from aiogram import types

button = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [types.InlineKeyboardButton(text="Задать вопрос", callback_data="ask_question")]
    ]
)