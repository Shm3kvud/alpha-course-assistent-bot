import psycopg
import asyncio
from langchain_core.documents import Document
from config import get_settings

async def connection_to_db():
    settings = get_settings()
    db_url = str(settings.source_database_url)
    return await psycopg.AsyncConnection.connect(db_url)

async def load_courses():

    return

async def load_articles():
    return

async def load_webinars():
    return

async def load_podcasts():
    return

async def load_documents():
    return

async def load_calculators():
    return

async def main():
    conn = await connection_to_db()
    async with conn.cursor() as cursor:

        await cursor.execute('SELECT "Title", "Description", "Duration", "Cost" ' \
                             'FROM "Courses" ' \
                             'WHERE "IsDeleted" = false AND "Published" IS NOT NULL;')
        
        result = await cursor.fetchall()
        print("Результат из базы:", result)

    await conn.close()

if __name__ == "__main__":        
    asyncio.run(main())