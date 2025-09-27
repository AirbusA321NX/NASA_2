import asyncio
import asyncpg
import json
import os
from datetime import datetime

async def test_single_insert():
    """Test inserting a single publication to see what happens"""
    
    # Database configuration from data_pipeline.py
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '1234'),
        'database': os.getenv('DB_NAME', 'nasa_biology')
    }
    
    print("Testing single publication insert...")
    
    try:
        # Create connection pool
        pool = await asyncpg.create_pool(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            min_size=1,
            max_size=10
        )
        
        async with pool.acquire() as conn:
            # Test inserting a single publication
            test_publication = {
                'title': 'Test Publication',
                'authors': ['Test Author'],
                'year': 2025,
                'doi': '10.1234/test.2025.001',
                'osd_id': 'OSD-TEST-001',
                'nslsl_id': None,
                'pdf_url': None,
                'licences': [],
                'abstract': 'This is a test publication for debugging purposes.',
                'keywords': ['test', 'debug'],
                'publication_date': '2025-09-26T00:00:00',
                'file_urls': []
            }
            
            print("Inserting test publication...")
            
            async with conn.transaction():
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
                    test_publication['title'],
                    json.dumps(test_publication['authors']),
                    test_publication['year'],
                    test_publication['doi'],
                    test_publication['osd_id'],
                    test_publication['nslsl_id'],
                    test_publication['pdf_url'],
                    json.dumps(test_publication['licences']),
                    test_publication['abstract'],
                    json.dumps(test_publication['keywords']),
                    datetime.fromisoformat(test_publication['publication_date']))
                    
                    print(f"Successfully inserted publication with ID: {paper_id}")
                    
                    # Check if it's in the database
                    count = await conn.fetchval('SELECT COUNT(*) FROM publications')
                    print(f"Total publications in database: {count}")
                    
                except Exception as e:
                    print(f"Error inserting publication: {e}")
                    raise
        
        await pool.close()
        print("Test completed successfully!")
        
    except Exception as e:
        print(f"Error in test: {e}")

if __name__ == "__main__":
    asyncio.run(test_single_insert())