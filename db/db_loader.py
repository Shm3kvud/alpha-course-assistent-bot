import psycopg
import asyncio
import sys
#import json
import re
import html
from langchain_core.documents import Document
from config import get_settings

BASE_URL = "https://kurs.alfabank.ru"
COURSES_URL = f"{BASE_URL}/courses"
ARTICLES_URL = f"{BASE_URL}/articles"
WEBINARS_URL = f"{BASE_URL}/webinars"
PODCASTS_URL = f"{BASE_URL}/podcasts"
DOCUMENTS_URL = f"{BASE_URL}/documents"
CALCULATORS_URL = f"{BASE_URL}/calculators"
FILES_URL = f"{BASE_URL}/files"

async def connection_to_db():
    settings = get_settings()
    db_url = str(settings.source_database_url)
    return await psycopg.AsyncConnection.connect(db_url)

def clean_html(raw_html: str) -> str:
    if not raw_html: return ""
    text = html.unescape(raw_html)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

async def load_courses(cur) -> list[Document]:
    course_docs = []
    
    await cur.execute('''
        SELECT c."Id", c."Title", c."Description", c."DescriptionAdditional", c."DescriptionTag", 
        c."Duration", c."Cost", c."Url", c."IsCertified", c."LessonQuantity", c."Rating", 
        c."Target", c."VideoUrl", c."HasTrial", c."Created", st."Title" as status,
        STRING_AGG(a."Title", ', ') as authors_list
        FROM "Courses" c
        LEFT JOIN "Statuses" st ON c."StatusId" = st."Id"
        LEFT JOIN "CourseAuthorBindings" cab ON c."Id" = cab."CourseId"
        LEFT JOIN "Authors" a ON cab."AuthorId" = a."Id"
        WHERE c."IsDeleted" = false AND c."Published" IS NOT NULL
        GROUP BY c."Id", st."Title";
    ''')
    rows = await cur.fetchall()
    
    for row in rows:
        (c_id, title, desc1, desc2, desc3, duration, cost, url, certificate, 
         lesson_cnt, rating, target, video_url, trial, created, status, authors_list) = row
        
        text = f"Курс: '{title}'. "

        if desc1: text += f"{clean_html(desc1)}. "
        if desc2: text += f"{clean_html(desc2)}. "
        if desc3: text += f"{clean_html(desc3)}. "
        if target: text += f"Цель курса: {clean_html(target)}. "
        
        course_docs.append(Document(
            page_content=text.strip(),
            metadata={
                "id": f"course:{c_id}",
                "url": f"{COURSES_URL}/{url}",
                "authors": str(authors_list) if authors_list else None,
                "duration": str(duration) if duration else None,
                "date_created": str(created)[0:10] if created else None,
                "cost": cost if cost else 0,
                "certificate": bool(certificate),
                "lessons": lesson_cnt if lesson_cnt else 0,
                "rating": str(rating) if rating else None,
                "video_url": str(video_url) if video_url else None,
                "trial": bool(trial),
                "status": str(status) if status else None
            }
        ))

    return course_docs


async def load_course_questions(cur) -> list[Document]:
    faq_docs = []
    
    await cur.execute('''
        SELECT q."CourseId", q."Question", q."Answer", c."Title" as course_title
        FROM "CourseQuestions" q
        LEFT JOIN "Courses" c ON q."CourseId" = c."Id"
    ''')
    rows = await cur.fetchall()

    for row in rows:
        c_id, question, answer, course_title = row
        
        text = f"{question} "
        if answer:
            text += f"Ответ: {answer.strip()}"
            
        faq_docs.append(Document(
            page_content=text,
            metadata={
                "id": f"faq:{c_id}",
                "course_title": course_title
            }
        ))
    return faq_docs

async def load_course_info(cur) -> list[Document]:
    info_docs = []
    
    await cur.execute('''
        SELECT cib."CourseId", cit."Title" as block_title, cib."Title" as info_text, 
        cib."Description" as info_desc, c."Title" as course_title
        FROM "CourseInfoBindings" cib
        JOIN "CourseInfoTypes" cit ON cib."CourseInfoTypeId" = cit."Id"
        JOIN "Courses" c ON cib."CourseId" = c."Id"
        WHERE c."IsDeleted" = false AND c."Published" IS NOT NULL
    ''')
    rows = await cur.fetchall()

    grouped = {}
    for row in rows:
        c_id, block_title, info_text, info_desc, course_title = row
        
        if not info_text and not info_desc: 
            continue
        
        key = (c_id, course_title)
        if key not in grouped:
            grouped[key] = {}
        if block_title not in grouped[key]:
            grouped[key][block_title] = []
            
        if info_text and info_desc:
            grouped[key][block_title].append(f"{info_text} ({info_desc})")
        elif info_text:
            grouped[key][block_title].append(info_text)
        elif info_desc:
            grouped[key][block_title].append(info_desc)

    for (c_id, course_title), blocks in grouped.items():
        text = ""
        for b_title, items in blocks.items():
            text += f"{b_title}: {', '.join(items)}. \n"
            
        info_docs.append(Document(
            page_content=text.strip(),
            metadata={
                "id": f"course_info:{c_id}",
                "course_title": course_title
            }
        ))
    return info_docs

async def load_lessons(cur) -> list[Document]:
    lesson_docs = []
    
    await cur.execute('''
        SELECT l."Id", l."Title", l."Description", l."Duration", 
               c."Title" as course_title, lt."Title" as type_title
        FROM "Lessons" l
        JOIN "CourseLessonBindings" clb ON l."Id" = clb."LessonId"
        JOIN "Courses" c ON clb."CourseId" = c."Id"
        LEFT JOIN "LessonTypes" lt ON l."TypeId" = lt."Id"
        WHERE c."IsDeleted" = false AND c."Published" IS NOT NULL
    ''')
    rows = await cur.fetchall()

    for row in rows:
        l_id, title, desc, duration, course_title, type_title = row
        
        text = f"Урок: {title}. "
        if desc: text += f"{clean_html(desc)}. "
            
        lesson_docs.append(Document(
            page_content=text.strip(),
            metadata={
                "id": f"lesson:{l_id}",
                "course_title": course_title,
                "type": str(type_title) if type_title else None,
                "duration": str(duration) if duration else None
            }
        ))
    return lesson_docs

async def load_articles(cur) -> list[Document]:
    articles_docs = []
    
    await cur.execute('''
        SELECT a."Id", a."Title", a."Description", a."DescriptionTag", a."Duration", a."Url", a."Published", aut."Title" as author_name
        FROM "Articles" a
        LEFT JOIN "Authors" aut ON a."AuthorId" = aut."Id"
        WHERE a."IsDeleted" = false AND a."Published" IS NOT NULL;
    ''')
    rows = await cur.fetchall()

    for row in rows:
        a_id, title, desc1, desc2, duration, url, published, authors_list = row
        
        text = f"Статья: '{title}'. "
        if desc1: text += f"{desc1.strip()}. "
        if desc2: text += f"{desc2.strip()}. "
            
        articles_docs.append(Document(
            page_content=text,
            metadata={
                "id": f"article:{a_id}",
                "url": f"{ARTICLES_URL}/{url}",
                "authors": str(authors_list) if authors_list else None,
                "duration": str(duration) if duration else None,
                "date_created": str(published)[0:10] if published else None,
            }
        ))
    return articles_docs

async def load_webinars(cur) -> list[Document]:
    webinars_docs = []
    
    await cur.execute('''
        SELECT w."Id", w."Title", w."Description", w."DescriptionExt", w."Url", 
               w."StartsAt", w."EndsAt", w."Duration", w."Rating", 
               w."IsRegistrationRequired", st."Title" as status
        FROM "Webinars" w
        LEFT JOIN "Statuses" st ON w."StatusId" = st."Id"
        WHERE w."IsDeleted" = false AND st."Title" NOT IN ('Черновик', 'Снят с публикации', 'Архив', 'Работа не начата')
    ''')
    rows = await cur.fetchall()

    for row in rows:
        (w_id, title, desc, desc_ext, url, starts_at, ends_at, duration, 
         rating, is_reg_req, status) = row
        
        await cur.execute('''
            SELECT f."Title", f."Extension", f."Url"
            FROM "Files" f
            JOIN "WebinarFiles" wf ON f."Id" = wf."FileId"
            WHERE wf."WebinarId" = %s
        ''', (w_id,))
        files = await cur.fetchall()
        
        files_metadata = []
        if files:
            for f_title, f_ext, f_url in files:
                files_metadata.append({
                    "title": f_title,
                    "extension": f_ext,
                    "url": f"{FILES_URL}/{f_url}" if f_url else None
                })
        
        text = f"Вебинар: '{title}'. "
        if desc: text += f"{clean_html(desc)}. "
        if desc_ext: text += f"{clean_html(desc_ext)}. "
        
        webinars_docs.append(Document(
            page_content=text.strip(),
            metadata={
                "id": f"webinar:{w_id}",
                "url": f"{WEBINARS_URL}/{url}" if url else None,
                "status": str(status) if status else None,
                "starts_at": str(starts_at)[:16] if starts_at else None,
                "ends_at": str(ends_at)[:16] if ends_at else None,
                "duration": str(duration) if duration else None,
                "rating": str(rating) if rating else None,
                "registration_required": bool(is_reg_req),
                "files": files_metadata
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
        
        text = f"Подкаст: '{title}'. "
        if desc: text += f"{desc.strip()}. "
        if desc_ext: text += f"{desc_ext.strip()}. "
            
        podcasts_docs.append(Document(
            page_content=text,
            metadata={
                "id": f"podcast:{p_id}",
                "url": f"{PODCASTS_URL}/{url}" if url else None,
                "duration": str(duration) if duration else None,
                "published_at": str(published) if published else None
            }
        ))
    return podcasts_docs

async def load_documents(cur) -> list[Document]:
    documents_docs = []
    await cur.execute('''
        SELECT "Id", "Title", "Description", "Url"
        FROM "Documents"
        WHERE "IsDeleted" = false;
    ''')
    rows = await cur.fetchall()

    for row in rows:
        d_id, title, desc, url = row
        
        text = f"Шаблон документа: '{title}'. "
        if desc: text += f"{clean_html(desc).strip()}. "
            
        documents_docs.append(Document(
            page_content=text,
            metadata={
                "id": f"document:{d_id}",
                "url": f"{DOCUMENTS_URL}/{url}"
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
        
        text = f"Калькулятор: '{title}'. "
        if desc: text += f"{desc.strip()}. "
            
        calculators_docs.append(Document(
            page_content=text,
            metadata={
                "id": f"calculator:{c_id}",
                "url": f"{CALCULATORS_URL}/{url}"
            }
        ))
    return calculators_docs

async def get_all_documents() -> dict[str, list[Document]]:
    all_data = {}
    
    conn = await connection_to_db()
    async with conn.cursor() as cursor:
        all_data["Курсы"] = await load_courses(cursor)
        all_data["Уроки"] = await load_lessons(cursor)
        all_data["Частые вопросы о курсах"] = await load_course_questions(cursor)
        all_data["Доп информация о курсах"] = await load_course_info(cursor)
        all_data["Вебинары"] = await load_webinars(cursor)
        all_data["Подкасты"] = await load_podcasts(cursor)
        all_data["Статьи"] = await load_articles(cursor)
        all_data["Шаблоны"] = await load_documents(cursor)
        all_data["Калькуляторы"] = await load_calculators(cursor)

    await conn.close()

    total_docs = sum(len(docs_list) for docs_list in all_data.values())
    print(f"Успешно загружено документов: {total_docs}")

    if all_data:
        for category, docs_list in all_data.items():
            if docs_list:
                print(f"\nПример первого документа (из категории '{category}'):")
                print(docs_list[0].page_content)
                break 
    ''' Для тестов
    output_data = {}
    for category, docs_list in all_data.items():
        output_data[category] = [
            {
                "text": doc.page_content, 
                "metadata": {k: str(v) for k, v in doc.metadata.items()}
            }
            for doc in docs_list
        ]
        
    with open("data_extracted.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print("\nДанные успешно сохранены в файл data_extracted.json")
    '''
    return all_data

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) # noqa
        
    docs = asyncio.run(get_all_documents())
