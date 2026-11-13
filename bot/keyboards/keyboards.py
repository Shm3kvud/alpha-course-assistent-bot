from aiogram import types

button = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [types.InlineKeyboardButton(text="Задать вопрос", callback_data="ask_question")],
        [types.InlineKeyboardButton(text="Подобрать обучение", callback_data="find_course")],
        [
            types.InlineKeyboardButton(text="История", callback_data="history"),
            types.InlineKeyboardButton(text="Новый диалог", callback_data="new_chat")
        ]
    ]
)