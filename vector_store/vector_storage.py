import numpy as np
import logging
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Try to import FAISS
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False
    logging.warning("FAISS not available. Install with: pip install faiss-cpu")

# Try to import asyncpg
try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    asyncpg = None
    ASYNCPG_AVAILABLE = False
    logging.warning("asyncpg not available. Install with: pip install asyncpg")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStorage:
    """
    Vector storage solution using FAISS for semantic retrieval
    """
    
    def __init__(self, dimension: int = 768, index_path: str = "vector_index.faiss"):
        self.dimension = dimension
        self.index_path = index_path
        self.index = None
        self.id_mapping = {}  # Maps FAISS IDs to database IDs
        self.metadata = {}    # Stores metadata for each vector
        
        # Check if required dependencies are available
        if not FAISS_AVAILABLE:
            logging.warning("FAISS is not available. Vector storage functionality will be limited.")
        if not ASYNCPG_AVAILABLE:
            logging.warning("asyncpg is not available. Database sync functionality will be limited.")
        
    def initialize_index(self):
        """
        Initialize the FAISS index
        """
        if not FAISS_AVAILABLE:
            raise RuntimeError("FAISS is not available. Install with: pip install faiss-cpu")
            
        try:
            # Check if index file exists
            if os.path.exists(self.index_path):
                logger.info(f"Loading existing FAISS index from {self.index_path}")
                self.index = faiss.read_index(self.index_path)
                
                # Load metadata if it exists
                metadata_path = self.index_path.replace('.faiss', '_metadata.json')
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        self.id_mapping = metadata.get('id_mapping', {})
                        self.metadata = metadata.get('metadata', {})
                        
                logger.info(f"Loaded index with {self.index.ntotal} vectors")
            else:
                # Create new index
                logger.info("Creating new FAISS index")
                # Use IndexFlatIP for cosine similarity (vectors should be normalized)
                self.index = faiss.IndexFlatIP(self.dimension)
                
            logger.info("FAISS index initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing FAISS index: {e}")
            raise

    def add_vectors(self, 
                   vectors: List[List[float]], 
                   ids: List[str],
                   metadata: Optional[List[Dict[str, Any]]] = None) -> int:
        """
        Add vectors to the index
        
        Args:
            vectors: List of embedding vectors
            ids: List of corresponding IDs
            metadata: Optional list of metadata dictionaries
            
        Returns:
            Number of vectors added
        """
        if self.index is None:
            raise RuntimeError("Index not initialized. Call initialize_index() first.")
            
        try:
            # Convert to numpy array
            vectors_np = np.array(vectors).astype('float32')
            
            # Normalize vectors for cosine similarity
            faiss.normalize_L2(vectors_np)
            
            # Get current number of vectors
            current_count = self.index.ntotal
            
            # Add vectors to index
            self.index.add(vectors_np)
            
            # Update ID mapping
            for i, id_val in enumerate(ids):
                faiss_id = current_count + i
                self.id_mapping[faiss_id] = id_val
                
                # Store metadata if provided
                if metadata and i < len(metadata):
                    self.metadata[id_val] = metadata[i]
                    
            logger.info(f"Added {len(vectors)} vectors to index")
            return len(vectors)
            
        except Exception as e:
            logger.error(f"Error adding vectors to index: {e}")
            raise

    def search_vectors(self, 
                      query_vector: List[float], 
                      k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for similar vectors
        
        Args:
            query_vector: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of search results with IDs, scores, and metadata
        """
        if self.index is None:
            raise RuntimeError("Index not initialized. Call initialize_index() first.")
            
        if self.index.ntotal == 0:
            logger.warning("Index is empty")
            return []
            
        try:
            # Convert query to numpy array
            query_np = np.array([query_vector]).astype('float32')
            
            # Normalize query vector
            faiss.normalize_L2(query_np)
            
            # Search
            scores, indices = self.index.search(query_np, k)
            
            # Format results
            results = []
            for i in range(len(indices[0])):
                faiss_id = indices[0][i]
                score = float(scores[0][i])
                
                # Skip invalid results
                if faiss_id == -1:
                    continue
                    
                # Get database ID
                db_id = self.id_mapping.get(faiss_id)
                if db_id:
                    result = {
                        'id': db_id,
                        'score': score,
                        'faiss_id': int(faiss_id)
                    }
                    
                    # Add metadata if available
                    if db_id in self.metadata:
                        result.update(self.metadata[db_id])
                        
                    results.append(result)
                    
            return results
            
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            raise

    async def sync_with_database(self, db_config: Dict[str, str], batch_size: int = 1000) -> int:
        """
        Sync vector store with database embeddings
        
        Args:
            db_config: Database configuration
            batch_size: Number of records to process in each batch
            
        Returns:
            Number of vectors synced
        """
        # Create connection pool
        pool = await asyncpg.create_pool(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            min_size=1,
            max_size=5
        )
        
        try:
            synced_count = 0
            
            async with pool.acquire() as conn:
                # Get embeddings that are not yet in the vector store
                # (This is a simplified approach - in practice, you'd want a more robust sync mechanism)
                rows = await conn.fetch('''
                    SELECT e.embedding_id, e.section_id, e.vector_data,
                           ds.section_type, ds.content, ds.paper_id
                    FROM embeddings e
                    JOIN document_sections ds ON e.section_id = ds.section_id
                    ORDER BY e.created_at
                ''')
                
                logger.info(f"Found {len(rows)} embeddings to sync")
                
                # Process in batches
                for i in range(0, len(rows), batch_size):
                    batch = rows[i:i + batch_size]
                    vectors = []
                    ids = []
                    metadata = []
                    
                    for row in batch:
                        vector_data = row['vector_data']
                        if vector_data:
                            vectors.append(vector_data)
                            ids.append(str(row['embedding_id']))
                            metadata.append({
                                'section_id': str(row['section_id']),
                                'paper_id': str(row['paper_id']),
                                'section_type': row['section_type'],
                                'content_preview': row['content'][:100] + '...' if len(row['content']) > 100 else row['content']
                            })
                    
                    # Add to index
                    if vectors:
                        self.add_vectors(vectors, ids, metadata)
                        synced_count += len(vectors)
                        logger.info(f"Synced {synced_count}/{len(rows)} embeddings")
                        
            return synced_count
            
        finally:
            await pool.close()

    def save_index(self):
        """
        Save the index and metadata to disk
        """
        if self.index is None:
            raise RuntimeError("Index not initialized.")
            
        try:
            # Save index
            faiss.write_index(self.index, self.index_path)
            
            # Save metadata
            metadata_path = self.index_path.replace('.faiss', '_metadata.json')
            metadata = {
                'id_mapping': self.id_mapping,
                'metadata': self.metadata,
                'dimension': self.dimension,
                'created_at': datetime.now().isoformat()
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            logger.info(f"Saved index with {self.index.ntotal} vectors to {self.index_path}")
            
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            raise

    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the index
        
        Returns:
            Dictionary with index statistics
        """
        if self.index is None:
            return {'initialized': False}
            
        return {
            'initialized': True,
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'index_type': str(type(self.index)),
            'metadata_entries': len(self.metadata)
        }

    async def get_vector_statistics(self, db_config: Dict[str, str]) -> Dict[str, Any]:
        """
        Get statistics about vectors in both database and FAISS index
        
        Args:
            db_config: Database configuration
            
        Returns:
            Dictionary with vector statistics
        """
        # Create connection pool
        pool = await asyncpg.create_pool(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            min_size=1,
            max_size=5
        )
        
        try:
            async with pool.acquire() as conn:
                # Database statistics
                db_stats = await conn.fetchrow('''
                    SELECT 
                        COUNT(*) as total_embeddings,
                        COUNT(DISTINCT paper_id) as papers_with_embeddings
                    FROM embeddings e
                    JOIN document_sections ds ON e.section_id = ds.section_id
                ''')
                
                # Section type distribution
                type_distribution = await conn.fetch('''
                    SELECT ds.section_type, COUNT(*) as count
                    FROM embeddings e
                    JOIN document_sections ds ON e.section_id = ds.section_id
                    GROUP BY ds.section_type
                    ORDER BY count DESC
                ''')
                
                # FAISS index statistics
                index_stats = self.get_index_stats()
                
                return {
                    'database': {
                        'total_embeddings': db_stats['total_embeddings'] if db_stats else 0,
                        'papers_with_embeddings': db_stats['papers_with_embeddings'] if db_stats else 0,
                        'type_distribution': [{'type': row['section_type'], 'count': row['count']} for row in type_distribution]
                    },
                    'faiss_index': index_stats
                }
                
        finally:
            await pool.close()

    def delete_vectors(self, ids: List[str]) -> int:
        """
        Delete vectors by IDs (simplified implementation)
        Note: FAISS doesn't support direct deletion, so we rebuild the index
        
        Args:
            ids: List of IDs to delete
            
        Returns:
            Number of vectors deleted
        """
        if self.index is None:
            raise RuntimeError("Index not initialized.")
            
        # In a real implementation, you would rebuild the index without the deleted vectors
        # For now, we'll just log the request
        logger.info(f"Delete request for {len(ids)} vectors (not implemented in this simplified version)")
        return 0

def main():
    """
    Main function to demonstrate vector storage functionality
    """
    # Initialize vector storage
    vector_store = VectorStorage(dimension=768, index_path="test_vector_index.faiss")
    
    try:
        # Initialize index
        vector_store.initialize_index()
        
        # Get initial stats
        stats = vector_store.get_index_stats()
        print(f"Initial index stats: {stats}")
        
        # Example vectors (in practice, these would come from sentence transformers)
        example_vectors = [
            [0.1, 0.2, 0.3] + [0.0] * 765,  # Pad to 768 dimensions
            [0.4, 0.5, 0.6] + [0.0] * 765,
            [0.7, 0.8, 0.9] + [0.0] * 765,
            [0.1, 0.9, 0.2] + [0.0] * 765
        ]
        
        example_ids = ['vec_1', 'vec_2', 'vec_3', 'vec_4']
        example_metadata = [
            {'type': 'introduction', 'paper_id': 'paper_1'},
            {'type': 'methods', 'paper_id': 'paper_1'},
            {'type': 'results', 'paper_id': 'paper_1'},
            {'type': 'conclusions', 'paper_id': 'paper_2'}
        ]
        
        # Add vectors
        added_count = vector_store.add_vectors(example_vectors, example_ids, example_metadata)
        print(f"Added {added_count} vectors")
        
        # Search
        query_vector = [0.15, 0.25, 0.35] + [0.0] * 765
        results = vector_store.search_vectors(query_vector, k=3)
        print(f"Search results: {results}")
        
        # Save index
        vector_store.save_index()
        print("Index saved successfully")
        
        # Get final stats
        final_stats = vector_store.get_index_stats()
        print(f"Final index stats: {final_stats}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()