#!/usr/bin/env python3
"""
Test script to insert multiple OSDR-like publications
"""
import asyncio
import asyncpg
import json
from datetime import datetime

async def test_bulk_insert():
    """Test inserting multiple OSDR-like publications"""
    try:
        # Database connection parameters
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'nasa_biology',
            'user': 'postgres',
            'password': '1234'
        }
        
        print("Connecting to database...")
        conn = await asyncpg.connect(**db_config)
        
        # Sample OSDR-like publications
        test_pubs = [
            {
                'title': 'NASA OSDR Study OSD-1',
                'authors': ['NASA Researcher A'],
                'year': 2025,
                'doi': '10.1234/osdr.1',
                'osd_id': 'OSD-1',
                'nslsl_id': None,
                'pdf_url': 'https://example.com/osd1.pdf',
                'licences': [],
                'abstract': 'This is test OSDR study 1.',
                'keywords': ['osdr', 'space biology'],
                'publication_date': datetime.now()
            },
            {
                'title': 'NASA OSDR Study OSD-2',
                'authors': ['NASA Researcher B'],
                'year': 2025,
                'doi': '',  # Empty DOI
                'osd_id': 'OSD-2',
                'nslsl_id': None,
                'pdf_url': 'https://example.com/osd2.pdf',
                'licences': [],
                'abstract': 'This is test OSDR study 2.',
                'keywords': ['osdr', 'microgravity'],
                'publication_date': datetime.now()
            },
            {
                'title': 'NASA OSDR Study OSD-3',
                'authors': ['NASA Researcher C'],
                'year': 2025,
                'doi': '10.1234/osdr.3',
                'osd_id': 'OSD-3',
                'nslsl_id': None,
                'pdf_url': 'https://example.com/osd3.pdf',
                'licences': [],
                'abstract': 'This is test OSDR study 3.',
                'keywords': ['osdr', 'radiation'],
                'publication_date': datetime.now()
            }
        ]
        
        print("Inserting OSDR-like publications...")
        inserted_count = 0
        
        for pub in test_pubs:
            try:
                # Handle empty DOI values
                doi = pub.get('doi')
                if not doi or doi.strip() == '':
                    doi = None  # Set to None instead of empty string
                
                # Insert publication
                if doi is not None:
                    # Use ON CONFLICT for publications with DOI
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
                    doi,
                    pub.get('osd_id'),
                    pub.get('nslsl_id'),
                    pub.get('pdf_url'),
                    json.dumps(pub.get('licences', [])),
                    pub.get('abstract', ''),
                    json.dumps(pub.get('keywords', [])),
                    pub.get('publication_date'))
                else:
                    # For publications without DOI, insert without ON CONFLICT
                    paper_id = await conn.fetchval('''
                        INSERT INTO publications (
                            title, authors, year, doi, osd_id, nslsl_id, 
                            pdf_url, licences, abstract, keywords, publication_date
                        ) VALUES (
                            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
                        )
                        RETURNING paper_id
                    ''', 
                    pub.get('title', ''),
                    json.dumps(pub.get('authors', [])),
                    pub.get('year'),
                    doi,
                    pub.get('osd_id'),
                    pub.get('nslsl_id'),
                    pub.get('pdf_url'),
                    json.dumps(pub.get('licences', [])),
                    pub.get('abstract', ''),
                    json.dumps(pub.get('keywords', [])),
                    pub.get('publication_date'))
                
                print(f"Successfully inserted publication: {pub['title']} with ID: {paper_id}")
                inserted_count += 1
                
            except Exception as e:
                print(f"Error inserting publication '{pub['title']}': {e}")
                continue
        
        # Count publications
        count = await conn.fetchval('SELECT COUNT(*) FROM publications')
        print(f"Total publications in database: {count}")
        print(f"Successfully inserted {inserted_count} new publications")
        
        await conn.close()
        print("Database connection closed.")
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(test_bulk_insert())