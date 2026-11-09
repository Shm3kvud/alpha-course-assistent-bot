from aiogram import Router, types
from aiogram.filters import CommandStart
from bot.keyboards import button


router = Router()


# Команда /start
@router.message(CommandStart())
async def start_command(message: types.Message):
    name = message.from_user.first_name
    
    await message.answer(
        f"👋 Добро пожаловать в AlfaAI, {name}!",
        reply_markup=button
    )