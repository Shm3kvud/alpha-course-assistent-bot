import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()


async def create_chat(user_id, title):
        conn = await asyncpg.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        
        try:
            chat_id = await conn.fetchval(
                "INSERT INTO chats (telegram_user_id, title) VALUES ($1, $2) RETURNING id",
                user_id,
                title
            )
            
            return chat_id
        finally:
            await conn.close()
            

async def save_message(chat_id, role, content):
    conn = await asyncpg.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    
    try:
        await conn.execute(
            "INSERT INTO messages (chat_id, role, content) VALUES ($1, $2, $3)",
            chat_id,
            role,
            content
        )
    finally:
        await conn.close()

        
async def get_last_chat(user_id):
    conn = await asyncpg.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    
    try:
        return await conn.fetchval(
            "SELECT id FROM chats WHERE telegram_user_id = $1 ORDER BY id DESC LIMIT 1",
            user_id
        )
    finally:
        await conn.close()
        
        
async def get_user_chats(user_id):
    conn = await asyncpg.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    
    try:
        return await conn.fetch(
            "SELECT id, title FROM chats WHERE telegram_user_id = $1 ORDER BY id ASC",
            user_id
        )
    finally:
        await conn.close()