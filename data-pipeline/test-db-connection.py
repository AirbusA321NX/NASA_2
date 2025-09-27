import asyncio
import asyncpg
import os

async def test_database_connection():
    """Test which database the data pipeline is connecting to"""
    
    # Database configuration from data_pipeline.py
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '1234'),
        'database': os.getenv('DB_NAME', 'nasa_biology')
    }
    
    print("Database configuration:")
    for key, value in db_config.items():
        print(f"  {key}: {value}")
    
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
            # Get database name
            db_name = await conn.fetchval('SELECT current_database()')
            print(f"Connected to database: {db_name}")
            
            # Get connection info
            conn_info = await conn.fetchrow('SELECT inet_server_addr(), inet_server_port()')
            print(f"Server address: {conn_info[0]}")
            print(f"Server port: {conn_info[1]}")
            
            # Check publications count
            count = await conn.fetchval('SELECT COUNT(*) FROM publications')
            print(f"Publications count: {count}")
            
            # List all databases
            databases = await conn.fetch('SELECT datname FROM pg_database WHERE datistemplate = false')
            print("Available databases:")
            for db in databases:
                print(f"  - {db['datname']}")
        
        await pool.close()
        
    except Exception as e:
        print(f"Error connecting to database: {e}")

if __name__ == "__main__":
    asyncio.run(test_database_connection())