#!/usr/bin/env python3
"""
Test script to insert an OSDR-like publication
"""
import asyncio
import asyncpg
import json
from datetime import datetime

async def test_osdr_insert():
    """Test inserting an OSDR-like publication"""
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
        
        # OSDR-like publication data (similar to what the crawler would produce)
        test_pub = {
            'title': 'NASA OSDR Study OSD-1',
            'authors': ['NASA Researcher'],
            'year': 2025,
            'doi': '',  # Empty DOI to test the constraint
            'osd_id': 'OSD-1',
            'nslsl_id': None,
            'pdf_url': 'https://example.com/osd1.pdf',
            'licences': [],
            'abstract': 'This is a test OSDR study.',
            'keywords': ['osdr', 'space biology'],
            'publication_date': datetime.now()
        }
        
        print("Inserting OSDR-like publication...")
        
        # Insert publication
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
        test_pub['title'],
        json.dumps(test_pub['authors']),
        test_pub['year'],
        test_pub['doi'],
        test_pub['osd_id'],
        test_pub['nslsl_id'],
        test_pub['pdf_url'],
        json.dumps(test_pub['licences']),
        test_pub['abstract'],
        json.dumps(test_pub['keywords']),
        test_pub['publication_date'])
        
        print(f"Successfully inserted publication with ID: {paper_id}")
        
        # Count publications
        count = await conn.fetchval('SELECT COUNT(*) FROM publications')
        print(f"Total publications in database: {count}")
        
        await conn.close()
        print("Database connection closed.")
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(test_osdr_insert())