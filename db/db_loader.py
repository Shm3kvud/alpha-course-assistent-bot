import psycopg
import asyncio
<<<<<<< HEAD
=======
import sys
#import json
>>>>>>> c9ec92b (подправила прототип чтения из бд)
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

<<<<<<< HEAD
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
=======
async def get_all_documents() -> list[Document]:
    global docs
    
    conn = await connection_to_db()
    async with conn.cursor() as cursor:
        docs.extend(await load_courses(cursor))
        docs.extend(await load_articles(cursor))
        docs.extend(await load_webinars(cursor))
        docs.extend(await load_podcasts(cursor))
        docs.extend(await load_documents(cursor))
        docs.extend(await load_calculators(cursor))

    await conn.close()

    print(f"Успешно загружено документов: {len(docs)}")
    if docs:
        print("\nПример первого документа:")
        print(docs[0].page_content)

    output_data = []
    for doc in docs:
        safe_metadata = {k: str(v) for k, v in doc.metadata.items()}
        output_data.append({
            "text": doc.page_content,
            "metadata": safe_metadata
        })

    '''Для тестирования, что считывается в итоге:
    output_data = []
    for doc in docs:
        safe_metadata = {k: str(v) for k, v in doc.metadata.items()}
        output_data.append({
            "text": doc.page_content,
            "metadata": safe_metadata
        })
        
    with open("data_extracted.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print("Данные успешно сохранены в файл data_extracted.json")
    '''

    return docs

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) # noqa
        
    docs = asyncio.run(get_all_documents())
>>>>>>> c9ec92b (подправила прототип чтения из бд)
