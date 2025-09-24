import asyncio
import asyncpg
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
from urllib.parse import urlparse
import hashlib

# Import our custom modules
from osdr_crawler import OSDRCrawler
from nslsl_harvester import NSLSLHarvester

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataPipeline:
    """
    Data extraction and normalization pipeline for OSDR and NSLSL data into PostgreSQL
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

    async def initialize_database(self):
        """
        Initialize database tables if they don't exist
        """
        # This would typically run the schema.sql file
        # For now, we'll assume the database is already set up
        logger.info("Database initialization skipped - assuming schema is already set up")
        
    async def extract_and_normalize_osdr_data(self) -> List[Dict[str, Any]]:
        """
        Extract and normalize OSDR data
        """
        logger.info("Starting OSDR data extraction and normalization")
        
        async with OSDRCrawler() as crawler:
            try:
                studies = await crawler.fetch_study_records()
                logger.info(f"Extracted {len(studies)} OSDR studies")
                
                # Normalize studies to publication format
                normalized_publications = []
                for study in studies:
                    normalized = self._normalize_osdr_study(study)
                    normalized_publications.append(normalized)
                
                return normalized_publications
                
            except Exception as e:
                logger.error(f"Error extracting OSDR data: {e}")
                raise

    def _normalize_osdr_study(self, study: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize OSDR study to publication format
        """
        # Extract year from submission date
        year = None
        if 'submission_date' in study:
            try:
                submission_date = datetime.fromisoformat(study['submission_date'].replace('Z', '+00:00'))
                year = submission_date.year
            except Exception as e:
                logger.warning(f"Error parsing submission date: {e}")
        
        # Extract authors
        authors = study.get('authors', [])
        if isinstance(authors, str):
            authors = [authors]
        
        # Extract file URLs
        file_urls = []
        if 'datafiles' in study:
            for datafile in study['datafiles']:
                if isinstance(datafile, dict) and 'file_url' in datafile:
                    file_urls.append(datafile['file_url'])
        
        return {
            'title': study.get('title', ''),
            'authors': authors,
            'year': year,
            'doi': study.get('doi', ''),
            'osd_id': study.get('osd_id', ''),
            'nslsl_id': None,  # OSDR data doesn't have NSLSL ID
            'pdf_url': self._extract_pdf_url(file_urls),
            'licences': [],  # OSDR doesn't provide explicit license info
            'abstract': study.get('description', ''),
            'keywords': study.get('keywords', []),
            'publication_date': study.get('submission_date'),
            'file_urls': file_urls,
            'source': 'osdr'
        }

    def _extract_pdf_url(self, file_urls: List[str]) -> Optional[str]:
        """
        Extract PDF URL from list of file URLs
        """
        for url in file_urls:
            if url.lower().endswith('.pdf'):
                return url
        return None

    async def extract_and_normalize_nslsl_data(self, query: str = "space biology", 
                                             max_records: int = 1000) -> List[Dict[str, Any]]:
        """
        Extract and normalize NSLSL data
        """
        logger.info("Starting NSLSL data extraction and normalization")
        
        harvester = NSLSLHarvester()
        try:
            publications = harvester.harvest_publications(query, max_records)
            logger.info(f"Extracted {len(publications)} NSLSL publications")
            
            # Normalize publications
            normalized_publications = []
            for pub in publications:
                normalized = self._normalize_nslsl_publication(pub)
                normalized_publications.append(normalized)
            
            return normalized_publications
            
        except Exception as e:
            logger.error(f"Error extracting NSLSL data: {e}")
            raise

    def _normalize_nslsl_publication(self, publication: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize NSLSL publication to standard format
        """
        # Extract year from publication date
        year = None
        if 'publication_date' in publication:
            try:
                # Handle different date formats
                pub_date_str = publication['publication_date']
                if isinstance(pub_date_str, str):
                    # Try different date formats
                    for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%fZ']:
                        try:
                            pub_date = datetime.strptime(pub_date_str, fmt)
                            year = pub_date.year
                            break
                        except ValueError:
                            continue
            except Exception as e:
                logger.warning(f"Error parsing publication date: {e}")
        
        return {
            'title': publication.get('title', ''),
            'authors': publication.get('authors', []),
            'year': year,
            'doi': publication.get('doi', ''),
            'osd_id': None,  # NSLSL data doesn't have OSD ID
            'nslsl_id': publication.get('nslsl_id', ''),
            'pdf_url': publication.get('file_urls', [None])[0] if publication.get('file_urls') else None,
            'licences': [],  # NSLSL doesn't provide explicit license info in this format
            'abstract': publication.get('abstract', ''),
            'keywords': publication.get('keywords', []),
            'publication_date': publication.get('publication_date'),
            'file_urls': publication.get('file_urls', []),
            'source': 'nslsl'
        }

    async def save_publications(self, publications: List[Dict[str, Any]]) -> List[str]:
        """
        Save normalized publications to PostgreSQL database
        
        Returns:
            List of inserted paper_ids
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        paper_ids = []
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for pub in publications:
                    try:
                        # Insert publication and get paper_id
                        paper_id = await conn.fetchval('''
                            INSERT INTO publications (
                                title, authors, year, doi, osd_id, nslsl_id, 
                                pdf_url, licences, abstract, keywords, publication_date
                            ) VALUES (
                                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
                            )
                            ON CONFLICT (doi) DO UPDATE SET
                                title = EXCLUDED.title,
                                updated_at = CURRENT_TIMESTAMP
                            RETURNING paper_id
                        ''', 
                        pub.get('title', ''),
                        json.dumps(pub.get('authors', [])),
                        pub.get('year'),
                        pub.get('doi'),
                        pub.get('osd_id'),
                        pub.get('nslsl_id'),
                        pub.get('pdf_url'),
                        json.dumps(pub.get('licences', [])),
                        pub.get('abstract', ''),
                        json.dumps(pub.get('keywords', [])),
                        pub.get('publication_date'))
                        
                        paper_ids.append(str(paper_id))
                        
                        # Insert file metadata
                        file_urls = pub.get('file_urls', [])
                        for file_url in file_urls:
                            if file_url:  # Only insert non-empty URLs
                                # Generate a checksum for the URL
                                checksum = hashlib.sha256(file_url.encode()).hexdigest()
                                
                                await conn.execute('''
                                    INSERT INTO file_metadata (
                                        paper_id, file_url, checksum
                                    ) VALUES ($1, $2, $3)
                                    ON CONFLICT (file_url) DO NOTHING
                                ''', paper_id, file_url, checksum)
                        
                        logger.debug(f"Saved publication: {pub.get('title', '')[:50]}...")
                        
                    except Exception as e:
                        logger.error(f"Error saving publication '{pub.get('title', '')[:50]}...': {e}")
                        # Continue with other publications rather than failing completely
                        continue
        
        logger.info(f"Successfully saved {len(paper_ids)} publications to database")
        return paper_ids

    async def update_ingestion_tracker(self, source: str, record_count: int):
        """
        Update the ingestion tracker with the latest information
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO ingestion_tracker (source, last_ingested, record_count)
                VALUES ($1, $2, $3)
                ON CONFLICT (source) DO UPDATE SET
                    last_ingested = EXCLUDED.last_ingested,
                    record_count = EXCLUDED.record_count,
                    updated_at = CURRENT_TIMESTAMP
            ''', source, datetime.now(), record_count)
        
        logger.info(f"Updated ingestion tracker for {source} with {record_count} records")

    async def run_pipeline(self, nslsl_query: str = "space biology", nslsl_max_records: int = 1000):
        """
        Run the complete data pipeline
        """
        logger.info("Starting data pipeline execution")
        
        # Initialize database
        await self.initialize_database()
        
        # Extract and normalize OSDR data
        osdr_publications = await self.extract_and_normalize_osdr_data()
        osdr_paper_ids = await self.save_publications(osdr_publications)
        await self.update_ingestion_tracker('osdr', len(osdr_paper_ids))
        
        # Extract and normalize NSLSL data
        nslsl_publications = await self.extract_and_normalize_nslsl_data(
            nslsl_query, nslsl_max_records)
        nslsl_paper_ids = await self.save_publications(nslsl_publications)
        await self.update_ingestion_tracker('nslsl', len(nslsl_paper_ids))
        
        # Summary
        total_papers = len(osdr_paper_ids) + len(nslsl_paper_ids)
        logger.info(f"Pipeline completed successfully. Total papers processed: {total_papers}")
        logger.info(f"  OSDR papers: {len(osdr_paper_ids)}")
        logger.info(f"  NSLSL papers: {len(nslsl_paper_ids)}")
        
        return {
            'total_papers': total_papers,
            'osdr_papers': len(osdr_paper_ids),
            'nslsl_papers': len(nslsl_paper_ids),
            'osdr_paper_ids': osdr_paper_ids,
            'nslsl_paper_ids': nslsl_paper_ids
        }

async def main():
    """
    Main function to run the data pipeline
    """
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password'),
        'database': os.getenv('DB_NAME', 'nasa_space_biology')
    }
    
    async with DataPipeline(db_config) as pipeline:
        try:
            results = await pipeline.run_pipeline(
                nslsl_query="space biology",
                nslsl_max_records=100  # Limit for demonstration
            )
            
            print(f"Pipeline completed with results: {results}")
            
        except Exception as e:
            logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())