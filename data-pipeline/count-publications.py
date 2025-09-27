#!/usr/bin/env python3
"""
Script to count publications in the database
"""
import asyncio
import asyncpg

async def count_publications():
    """Count publications in the database"""
    try:
        # Database connection parameters (matching data_pipeline.py)
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'nasa_biology',
            'user': 'postgres',
            'password': '1234'
        }
        
        print("Connecting to database...")
        conn = await asyncpg.connect(**db_config)
        
        # Count publications
        count = await conn.fetchval('SELECT COUNT(*) FROM publications')
        print(f"Total publications in database: {count}")
        
        # Show first few publications if any exist
        if count > 0:
            rows = await conn.fetch('SELECT paper_id, title, doi FROM publications LIMIT 5')
            print("\nFirst 5 publications:")
            for row in rows:
                print(f"  ID: {row['paper_id']}")
                print(f"  Title: {row['title']}")
                print(f"  DOI: {row['doi']}")
                print()
        
        await conn.close()
        print("Database connection closed.")
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(count_publications())