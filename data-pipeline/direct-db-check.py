#!/usr/bin/env python3
"""
Direct database connection test to check if data was inserted
"""
import psycopg2
import os

def check_database():
    """Check database directly with psycopg2"""
    try:
        # Database connection parameters (matching backend service)
        conn_params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'nasa_biology',
            'user': 'postgres',
            'password': '1234'
        }
        
        print("Connecting to database...")
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Count publications
        cursor.execute('SELECT COUNT(*) FROM publications')
        count = cursor.fetchone()[0]
        print(f"Total publications in database: {count}")
        
        # Show first few publications if any exist
        if count > 0:
            cursor.execute('SELECT paper_id, title, doi FROM publications LIMIT 5')
            rows = cursor.fetchall()
            print("\nFirst 5 publications:")
            for row in rows:
                print(f"  ID: {row[0]}")
                print(f"  Title: {row[1]}")
                print(f"  DOI: {row[2]}")
                print()
        
        cursor.close()
        conn.close()
        print("Database connection closed.")
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    check_database()