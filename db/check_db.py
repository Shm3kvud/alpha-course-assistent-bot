import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()


async def main():
    conn = await asyncpg.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    
    print("Подключение к PostgreSQL успешно!")
    
    tables = await conn.fetch(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
    )
    
    for table in tables:
        print(table["tablename"])
        
    await conn.close()
    

asyncio.run(main())