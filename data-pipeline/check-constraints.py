import asyncio
import asyncpg
import os

async def check_constraint_name():
    """Check the exact name of the DOI constraint"""
    
    # Database configuration from data_pipeline.py
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '1234'),
        'database': os.getenv('DB_NAME', 'nasa_biology')
    }
    
    print("Checking constraint names...")
    
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
            # Get constraint information
            constraints = await conn.fetch('''
                SELECT conname, contype 
                FROM pg_constraint 
                WHERE conrelid = 'publications'::regclass
                AND conkey = (
                    SELECT array_agg(attnum) 
                    FROM pg_attribute 
                    WHERE attrelid = 'publications'::regclass 
                    AND attname = 'doi'
                )
            ''')
            
            print("DOI-related constraints:")
            for constraint in constraints:
                print(f"  Name: {constraint['conname']}, Type: {constraint['contype']}")
                
            # Also check with a simpler query
            simple_constraints = await conn.fetch('''
                SELECT constraint_name, constraint_type 
                FROM information_schema.table_constraints 
                WHERE table_name = 'publications' 
                AND constraint_name LIKE '%doi%'
            ''')
            
            print("\nAll DOI-related constraints from information_schema:")
            for constraint in simple_constraints:
                print(f"  Name: {constraint['constraint_name']}, Type: {constraint['constraint_type']}")
        
        await pool.close()
        print("Constraint check completed successfully!")
        
    except Exception as e:
        print(f"Error checking constraints: {e}")

if __name__ == "__main__":
    asyncio.run(check_constraint_name())