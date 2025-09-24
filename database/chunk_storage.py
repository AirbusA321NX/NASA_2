import asyncpg
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChunkStorage:
    """
    Storage of canonical section chunks with token offsets in database
    """
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.pool = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        # Create connection pool
        self.pool = await asyncpg.create_pool(
            host=self.db_config['host'],
            port=self.db_config['port'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            database=self.db_config['database'],
            min_size=1,
            max_size=10
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.pool:
            await self.pool.close()

    async def store_document_chunks(self, 
                                  paper_id: str, 
                                  sections: List[Dict[str, Any]]) -> List[str]:
        """
        Store document sections as chunks in the database
        
        Args:
            paper_id: ID of the parent publication
            sections: List of section dictionaries with content and metadata
            
        Returns:
            List of inserted section IDs
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        section_ids = []
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for section in sections:
                    try:
                        # Extract section data
                        section_type = section.get('type', 'unknown')
                        content = section.get('content', '')
                        byte_start = section.get('byte_start', 0)
                        byte_end = section.get('byte_end', len(content.encode('utf-8')))
                        token_start = section.get('token_start', 0)
                        token_end = section.get('token_end', section.get('token_count', 0))
                        tokens = section.get('tokens', [])
                        
                        # Insert section
                        section_id = await conn.fetchval('''
                            INSERT INTO document_sections (
                                paper_id, section_type, content, 
                                byte_start, byte_end, token_start, token_end
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                            RETURNING section_id
                        ''', 
                        paper_id, section_type, content,
                        byte_start, byte_end, token_start, token_end)
                        
                        section_ids.append(str(section_id))
                        
                        # Store token information if available
                        if tokens:
                            await self._store_tokens(conn, str(section_id), tokens)
                        
                        logger.debug(f"Stored section {section_type} for paper {paper_id}")
                        
                    except Exception as e:
                        logger.error(f"Error storing section for paper {paper_id}: {e}")
                        # Continue with other sections rather than failing completely
                        continue
        
        logger.info(f"Successfully stored {len(section_ids)} sections for paper {paper_id}")
        return section_ids

    async def _store_tokens(self, conn: asyncpg.Connection, 
                          section_id: str, 
                          tokens: List[Dict[str, Any]]):
        """
        Store token information for a section
        
        Args:
            conn: Database connection
            section_id: ID of the parent section
            tokens: List of token dictionaries
        """
        # For now, we store tokens as JSON in the document_sections table
        # In a more advanced implementation, we might have a separate tokens table
        try:
            await conn.execute('''
                UPDATE document_sections 
                SET tokens = $1 
                WHERE section_id = $2
            ''', json.dumps(tokens), section_id)
        except Exception as e:
            logger.warning(f"Could not store tokens for section {section_id}: {e}")

    async def get_document_chunks(self, paper_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all chunks for a document
        
        Args:
            paper_id: ID of the publication
            
        Returns:
            List of section dictionaries
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT section_id, section_type, content, 
                       byte_start, byte_end, token_start, token_end, tokens,
                       created_at
                FROM document_sections 
                WHERE paper_id = $1 
                ORDER BY section_type
            ''', paper_id)
            
            sections = []
            for row in rows:
                section = {
                    'section_id': str(row['section_id']),
                    'section_type': row['section_type'],
                    'content': row['content'],
                    'byte_start': row['byte_start'],
                    'byte_end': row['byte_end'],
                    'token_start': row['token_start'],
                    'token_end': row['token_end'],
                    'tokens': json.loads(row['tokens']) if row['tokens'] else [],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None
                }
                sections.append(section)
                
            return sections

    async def get_chunk_by_id(self, section_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific chunk by ID
        
        Args:
            section_id: ID of the section
            
        Returns:
            Section dictionary or None if not found
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT section_id, paper_id, section_type, content, 
                       byte_start, byte_end, token_start, token_end, tokens,
                       created_at
                FROM document_sections 
                WHERE section_id = $1
            ''', section_id)
            
            if row:
                return {
                    'section_id': str(row['section_id']),
                    'paper_id': str(row['paper_id']),
                    'section_type': row['section_type'],
                    'content': row['content'],
                    'byte_start': row['byte_start'],
                    'byte_end': row['byte_end'],
                    'token_start': row['token_start'],
                    'token_end': row['token_end'],
                    'tokens': json.loads(row['tokens']) if row['tokens'] else [],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None
                }
            else:
                return None

    async def get_chunks_by_type(self, paper_id: str, section_type: str) -> List[Dict[str, Any]]:
        """
        Retrieve chunks of a specific type for a document
        
        Args:
            paper_id: ID of the publication
            section_type: Type of section to retrieve
            
        Returns:
            List of section dictionaries
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT section_id, section_type, content, 
                       byte_start, byte_end, token_start, token_end, tokens,
                       created_at
                FROM document_sections 
                WHERE paper_id = $1 AND section_type = $2
                ORDER BY created_at
            ''', paper_id, section_type)
            
            sections = []
            for row in rows:
                section = {
                    'section_id': str(row['section_id']),
                    'section_type': row['section_type'],
                    'content': row['content'],
                    'byte_start': row['byte_start'],
                    'byte_end': row['byte_end'],
                    'token_start': row['token_start'],
                    'token_end': row['token_end'],
                    'tokens': json.loads(row['tokens']) if row['tokens'] else [],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None
                }
                sections.append(section)
                
            return sections

    async def search_chunks(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for chunks containing specific text
        
        Args:
            query: Text to search for
            limit: Maximum number of results
            
        Returns:
            List of matching section dictionaries
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT section_id, paper_id, section_type, content, 
                       byte_start, byte_end, token_start, token_end,
                       ts_rank(to_tsvector('english', content), plainto_tsquery('english', $1)) as rank
                FROM document_sections 
                WHERE to_tsvector('english', content) @@ plainto_tsquery('english', $1)
                ORDER BY rank DESC
                LIMIT $2
            ''', query, limit)
            
            sections = []
            for row in rows:
                section = {
                    'section_id': str(row['section_id']),
                    'paper_id': str(row['paper_id']),
                    'section_type': row['section_type'],
                    'content': row['content'],
                    'byte_start': row['byte_start'],
                    'byte_end': row['byte_end'],
                    'token_start': row['token_start'],
                    'token_end': row['token_end'],
                    'rank': row['rank']
                }
                sections.append(section)
                
            return sections

    async def get_document_structure(self, paper_id: str) -> Dict[str, Any]:
        """
        Get the structure of a document (what sections it contains)
        
        Args:
            paper_id: ID of the publication
            
        Returns:
            Dictionary with document structure information
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT section_type, COUNT(*) as count,
                       MIN(created_at) as first_created,
                       MAX(created_at) as last_created
                FROM document_sections 
                WHERE paper_id = $1
                GROUP BY section_type
                ORDER BY section_type
            ''', paper_id)
            
            structure = {
                'paper_id': paper_id,
                'sections': [],
                'total_sections': 0
            }
            
            for row in rows:
                section_info = {
                    'type': row['section_type'],
                    'count': row['count'],
                    'first_created': row['first_created'].isoformat() if row['first_created'] else None,
                    'last_created': row['last_created'].isoformat() if row['last_created'] else None
                }
                structure['sections'].append(section_info)
                structure['total_sections'] += row['count']
                
            return structure

    async def delete_document_chunks(self, paper_id: str) -> int:
        """
        Delete all chunks for a document
        
        Args:
            paper_id: ID of the publication
            
        Returns:
            Number of deleted sections
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        async with self.pool.acquire() as conn:
            result = await conn.execute('''
                DELETE FROM document_sections 
                WHERE paper_id = $1
            ''', paper_id)
            
            # Extract the number of deleted rows
            deleted_count = int(result.split()[1]) if result.startswith('DELETE') else 0
            logger.info(f"Deleted {deleted_count} sections for paper {paper_id}")
            return deleted_count

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored chunks
        
        Returns:
            Dictionary with statistics
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        async with self.pool.acquire() as conn:
            # Total chunks
            total_chunks = await conn.fetchval('SELECT COUNT(*) FROM document_sections')
            
            # Chunks by section type
            type_counts = await conn.fetch('''
                SELECT section_type, COUNT(*) as count
                FROM document_sections
                GROUP BY section_type
                ORDER BY count DESC
            ''')
            
            # Average content length
            avg_length = await conn.fetchval('''
                SELECT AVG(LENGTH(content)) FROM document_sections
            ''')
            
            return {
                'total_chunks': total_chunks,
                'chunks_by_type': [{'type': row['section_type'], 'count': row['count']} for row in type_counts],
                'average_content_length': float(avg_length) if avg_length else 0
            }

async def main():
    """
    Main function to demonstrate chunk storage functionality
    """
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': '5432',
        'user': 'postgres',
        'password': 'password',
        'database': 'nasa_space_biology'
    }
    
    async with ChunkStorage(db_config) as storage:
        # Example usage
        print("Chunk storage initialized successfully")
        
        # Example statistics
        try:
            stats = await storage.get_statistics()
            print(f"Storage statistics: {stats}")
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())