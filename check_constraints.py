import asyncio
import asyncpg
import os

async def check_constraints():
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '1234'),
        'database': os.getenv('DB_NAME', 'nasa_biology')
    }
    
    # Create connection
    conn = await asyncpg.connect(**db_config)
    
    try:
        # Check table information
        table_info = await conn.fetch('''
            SELECT column_name, is_nullable, data_type, column_default
            FROM information_schema.columns 
            WHERE table_name = 'publications' 
            ORDER BY ordinal_position
        ''')
        
        print("Publications table structure:")
        for row in table_info:
            print(f"  {row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']})")
        
        # Check constraints
        constraints = await conn.fetch('''
            SELECT constraint_name, constraint_type 
            FROM information_schema.table_constraints 
            WHERE table_name = 'publications'
        ''')
        
        print("\nTable constraints:")
        for row in constraints:
            print(f"  {row['constraint_name']}: {row['constraint_type']}")
            
        # Check indexes
        indexes = await conn.fetch('''
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'publications'
        ''')
        
        print("\nTable indexes:")
        for row in indexes:
            print(f"  {row['indexname']}: {row['indexdef']}")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_constraints())