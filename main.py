import asyncio
import os 

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

from bot.handlers.start import router as start_router
from bot.handlers.chat import router as chat_router


load_dotenv()

token = Bot(token=os.getenv("BOT_TOKEN"))
dp=Dispatcher()

dp.include_router(start_router)
dp.include_router(chat_router)


# Запуск бота
async def main():
    await dp.start_polling(token)
    

asyncio.run(main())