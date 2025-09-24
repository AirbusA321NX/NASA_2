import torch
import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.preprocessing import normalize
import asyncio
import asyncpg
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """
    Sentence-transformer model (all-mpnet-base-v2) for local embedding generation
    """
    
    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        self.model_name = model_name
        self.model = None
        self.device = None
        self.dimension = 768  # Default for all-mpnet-base-v2
        
    def initialize_model(self):
        """
        Initialize the sentence transformer model
        """
        try:
            # Determine device
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(f"Using device: {self.device}")
            
            # Load model
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error initializing sentence transformer model: {e}")
            raise

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        if self.model is None:
            raise RuntimeError("Model not initialized. Call initialize_model() first.")
            
        try:
            # Generate embeddings
            embeddings = self.model.encode(
                texts, 
                convert_to_numpy=True, 
                normalize_embeddings=True,
                show_progress_bar=False
            )
            
            # Convert to list format
            if isinstance(embeddings, np.ndarray):
                embeddings = embeddings.tolist()
                
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text string
            
        Returns:
            Embedding vector
        """
        embeddings = self.generate_embeddings([text])
        return embeddings[0] if embeddings else []

    async def generate_and_store_embeddings(self, 
                                          db_config: Dict[str, str],
                                          batch_size: int = 32) -> int:
        """
        Generate embeddings for all document chunks and store in database
        
        Args:
            db_config: Database configuration
            batch_size: Number of chunks to process in each batch
            
        Returns:
            Number of embeddings generated and stored
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
            processed_count = 0
            
            async with pool.acquire() as conn:
                # Get chunks that don't have embeddings yet
                rows = await conn.fetch('''
                    SELECT ds.section_id, ds.content
                    FROM document_sections ds
                    LEFT JOIN embeddings e ON ds.section_id = e.section_id
                    WHERE e.section_id IS NULL
                    ORDER BY ds.created_at
                ''')
                
                logger.info(f"Found {len(rows)} chunks without embeddings")
                
                # Process in batches
                for i in range(0, len(rows), batch_size):
                    batch = rows[i:i + batch_size]
                    texts = [row['content'] for row in batch]
                    section_ids = [str(row['section_id']) for row in batch]
                    
                    # Generate embeddings
                    embeddings = self.generate_embeddings(texts)
                    
                    # Store embeddings
                    async with conn.transaction():
                        for section_id, embedding in zip(section_ids, embeddings):
                            await conn.execute('''
                                INSERT INTO embeddings (section_id, vector_data)
                                VALUES ($1, $2)
                            ''', section_id, embedding)
                    
                    processed_count += len(batch)
                    logger.info(f"Processed {processed_count}/{len(rows)} chunks")
                    
            return processed_count
            
        finally:
            await pool.close()

    async def search_similar_chunks(self, 
                                  db_config: Dict[str, str],
                                  query_text: str, 
                                  top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for chunks similar to a query text using cosine similarity
        
        Args:
            db_config: Database configuration
            query_text: Text to search for similar chunks
            top_k: Number of similar chunks to return
            
        Returns:
            List of similar chunks with similarity scores
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
            # Generate embedding for query
            query_embedding = self.generate_embedding(query_text)
            
            async with pool.acquire() as conn:
                # Get all embeddings (in a real implementation, we'd use approximate search)
                rows = await conn.fetch('''
                    SELECT e.embedding_id, e.section_id, e.vector_data,
                           ds.section_type, ds.content, ds.paper_id
                    FROM embeddings e
                    JOIN document_sections ds ON e.section_id = ds.section_id
                ''')
                
                # Calculate similarities
                similarities = []
                for row in rows:
                    db_embedding = row['vector_data']
                    if db_embedding:
                        # Calculate cosine similarity
                        similarity = np.dot(query_embedding, db_embedding) / (
                            np.linalg.norm(query_embedding) * np.linalg.norm(db_embedding)
                        )
                        similarities.append({
                            'embedding_id': str(row['embedding_id']),
                            'section_id': str(row['section_id']),
                            'paper_id': str(row['paper_id']),
                            'section_type': row['section_type'],
                            'content': row['content'][:200] + '...' if len(row['content']) > 200 else row['content'],
                            'similarity': float(similarity)
                        })
                
                # Sort by similarity and return top_k
                similarities.sort(key=lambda x: x['similarity'], reverse=True)
                return similarities[:top_k]
                
        finally:
            await pool.close()

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_name': self.model_name,
            'device': self.device,
            'dimension': self.dimension,
            'initialized': self.model is not None
        }

    async def get_embedding_statistics(self, db_config: Dict[str, str]) -> Dict[str, Any]:
        """
        Get statistics about stored embeddings
        
        Args:
            db_config: Database configuration
            
        Returns:
            Dictionary with embedding statistics
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
                # Total embeddings
                total_embeddings = await conn.fetchval('SELECT COUNT(*) FROM embeddings')
                
                # Embeddings by section type
                type_counts = await conn.fetch('''
                    SELECT ds.section_type, COUNT(*) as count
                    FROM embeddings e
                    JOIN document_sections ds ON e.section_id = ds.section_id
                    GROUP BY ds.section_type
                    ORDER BY count DESC
                ''')
                
                return {
                    'total_embeddings': total_embeddings,
                    'embeddings_by_type': [{'type': row['section_type'], 'count': row['count']} for row in type_counts]
                }
                
        finally:
            await pool.close()

def main():
    """
    Main function to demonstrate embedding generator functionality
    """
    # Initialize embedding generator
    generator = EmbeddingGenerator()
    
    try:
        # Initialize model
        generator.initialize_model()
        
        # Get model info
        model_info = generator.get_model_info()
        print(f"Model info: {model_info}")
        
        # Example texts
        example_texts = [
            "The effects of microgravity on plant growth are significant for space missions.",
            "Human physiology changes dramatically during long-duration spaceflight.",
            "Microbial communities in closed environments require careful monitoring.",
            "Radiation exposure poses risks to astronaut health during Mars missions."
        ]
        
        # Generate embeddings
        print("Generating embeddings for example texts...")
        embeddings = generator.generate_embeddings(example_texts)
        
        print(f"Generated {len(embeddings)} embeddings")
        print(f"Embedding dimension: {len(embeddings[0])}")
        
        # Example similarity search
        print("\nPerforming similarity search...")
        query = "How does microgravity affect biological systems?"
        query_embedding = generator.generate_embedding(query)
        
        # Calculate similarity with example embeddings
        for i, (text, embedding) in enumerate(zip(example_texts, embeddings)):
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            print(f"Text {i+1}: {similarity:.4f} - {text[:50]}...")
            
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()