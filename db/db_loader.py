import psycopg
import asyncio
import sys
import json
from langchain_core.documents import Document
from config import get_settings

docs = []

async def connection_to_db():
    settings = get_settings()
    db_url = str(settings.source_database_url)
    return await psycopg.AsyncConnection.connect(db_url)

async def load_courses(cur) -> list[Document]:
    course_docs = []
    await cur.execute('SELECT "Id", "Title", "Description", "Duration", "Cost" ' \
                    ' FROM "Courses" ' \
                    ' WHERE "IsDeleted" = false AND "Published" IS NOT NULL;')
    rows = await cur.fetchall()
    
    for row in rows:
        c_id, title, desc, duration, cost = row
        text = f"Курс: {title}. Описание: {desc or ''}. Длительность: {duration or ''}. "
        text += f"Стоимость: {cost} руб." if cost else "Стоимость: Бесплатно."
        
        course_docs.append(Document(
            page_content=text,
            metadata={"source": "database_courses", "id": f"course:{c_id}"}
        ))
    return course_docs

async def load_articles(cur) -> list[Document]:
    articles_docs = []
    await cur.execute('SELECT "Id", "Title", "Description","Url", "Published", "IsDeleted"' \
                      'FROM "Articles"' \
                      'WHERE "IsDeleted" = false AND "Published" IS NOT NULL;')
    rows = await cur.fetchall()

    for row in rows:
        a_id, title, desc, url, published, is_deleted = row
        
        text = f"Статья: {title}. "
        if desc:
            text += f"Описание: {desc.strip()}. "
        if url:
            text += f"Ссылка: https://kurs.alfabank.ru/articles/{url}"
            
        articles_docs.append(Document(
            page_content=text,
            metadata={
                "source": "database_articles", 
                "id": f"article:{a_id}",
                "published_at": str(published)
            }
        ))
    return articles_docs

async def load_webinars(cur) -> list[Document]:
    webinars_docs = []
    await cur.execute('''
        SELECT "Id", "Title", "Description", "DescriptionExt", "Url", "StartsAt", "EndsAt", "Duration", "Rating", "StatusId"
        FROM "Webinars"
        WHERE "IsDeleted" = false;
    ''')
    rows = await cur.fetchall()

    for row in rows:
        w_id, title, desc, desc_ext, url, starts_at, ends_at, duration, rating, status_id = row
        
        text = f"Вебинар: {title}. "
        if desc: text += f"Описание: {desc.strip()}. "
        if desc_ext: text += f"Дополнительно: {desc_ext.strip()}. "
        if starts_at: text += f"Дата начала: {str(starts_at)[:16]}. "
        if ends_at: text += f"Дата окончания: {str(ends_at)[:16]}. "
        if duration: text += f"Длительность: {duration}. "
        if rating: text += f"Рейтинг: {rating}. "
        if url: text += f"Ссылка: https://kurs.alfabank.ru/webinars/{url}"
            
        webinars_docs.append(Document(
            page_content=text,
            metadata={
                "source": "database_webinars", 
                "id": f"webinar:{w_id}",
                "status_id": status_id
            }
        ))
    return webinars_docs

async def load_podcasts(cur) -> list[Document]:
    podcasts_docs = []
    await cur.execute('''
        SELECT "Id", "Title", "Description", "DescriptionExt", "Url", "Duration", "Published"
        FROM "Podcasts"
        WHERE "IsDeleted" = false AND "Published" IS NOT NULL;
    ''')
    rows = await cur.fetchall()

    for row in rows:
        p_id, title, desc, desc_ext, url, duration, published = row
        
        text = f"Подкаст: {title}. "
        if desc: text += f"Описание: {desc.strip()}. "
        if desc_ext: text += f"Дополнительно: {desc_ext.strip()}. "
        if duration: text += f"Длительность: {duration}. "
        if url: text += f"Ссылка: https://kurs.alfabank.ru/podcasts/{url}"
            
        podcasts_docs.append(Document(
            page_content=text,
            metadata={
                "source": "database_podcasts", 
                "id": f"podcast:{p_id}",
                "published_at": str(published) if published else None
            }
        ))
    return podcasts_docs

async def load_documents(cur) -> list[Document]:
    documents_docs = []
    await cur.execute('''
        SELECT "Id", "Title", "Description", "Url", "TypeId", "Extension", "Published"
        FROM "Documents"
        WHERE "IsDeleted" = false AND "Published" IS NOT NULL;
    ''')
    rows = await cur.fetchall()

    for row in rows:
        d_id, title, desc, url, type_id, ext, published = row
        
        text = f"Шаблон документа: {title}. "
        if desc: text += f"Текст: {desc.strip()}. "
        if ext: text += f"Формат: {ext}. "
        if url: text += f"Ссылка: https://kurs.alfabank.ru/documents/{url}"
            
        documents_docs.append(Document(
            page_content=text,
            metadata={
                "source": "database_documents", 
                "id": f"document:{d_id}",
                "published_at": str(published) if published else None
            }
        ))
    return documents_docs

async def load_calculators(cur) -> list[Document]:
    calculators_docs = []
    await cur.execute('''
        SELECT "Id", "Title", "Description", "Url"
        FROM "Calculators"
        WHERE "IsDeleted" = false;
    ''')
    rows = await cur.fetchall()

    for row in rows:
        c_id, title, desc, url = row
        
        text = f"Калькулятор: {title}. "
        if desc: text += f"Описание: {desc.strip()}. "
        if url: text += f"Ссылка: https://kurs.alfabank.ru/calculators/{url}"
            
        calculators_docs.append(Document(
            page_content=text,
            metadata={
                "source": "database_calculators", 
                "id": f"calculator:{c_id}"
            }
        ))
    return calculators_docs

async def main():
    global docs
    
    conn = await connection_to_db()
    async with conn.cursor() as cursor:
        docs.extend(await load_courses(cursor))
        docs.extend(await load_articles(cursor))

    await conn.close()

    print(f"Успешно загружено документов: {len(docs)}")
    if docs:
        print("\nПример первого документа:")
        print(docs[0].page_content)

    output_data = []
    for doc in docs:
        output_data.append({
            "text": doc.page_content,
            "metadata": doc.metadata
        })
        
    with open("data_extracted.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print("✅ Данные успешно сохранены в файл data_extracted.json")

if __name__ == "__main__":        
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) # noqa
    asyncio.run(main())
    