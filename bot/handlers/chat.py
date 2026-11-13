from db.history import create_chat, get_last_chat, save_message, get_user_chats
from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from bot.keyboards.keyboards import button
from rag.pipeline import answer


router = Router()


class Questions(StatesGroup):
    waiting_question = State()


@router.callback_query(F.data == "ask_question")
async def ask_question(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(Questions.waiting_question)
    
    await callback.message.answer(
        "Расскажи, с какой задачей в бизнесе нужна помощь."
    )
    
    
@router.message(Questions.waiting_question, F.text)
async def get_question(message: types.Message):
    question = message.text.strip()
    
    if not question:
        await message.answer("Напиши свой вопрос")
        return
    
    
    chat_id = await get_last_chat(message.from_user.id)
    
    if chat_id is None:
        chat_id = await create_chat(message.from_user.id, question[:60])
        
    await save_message(chat_id, "user", question)
    
    response = await answer(question, message.from_user.id)
    
    await message.answer(response)
    
    await save_message(chat_id, "assistant", response)
    

@router.callback_query(F.data == "new_chat")
async def new_chat(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    
    await create_chat(callback.from_user.id, "Новый диалог")
    
    await state.clear()
    await state.set_state(Questions.waiting_question)
    
    await callback.message.answer("Новый диалог создан. Напишите свой вопрос")
    
    
@router.callback_query(F.data == "history")
@router.callback_query(F.data.startswith("history_page:"))
async def show_history(callback: types.CallbackQuery):
    await callback.answer()
    
    chats = await get_user_chats(callback.from_user.id)
    
    page = 0
    
    if callback.data.startswith("history_page:"):
        page = int(callback.data.split(":")[1])
        
    total_pages = max(1, (len(chats) + 7) // 8)
    page = max(0, min(page, total_pages - 1))
    
    keyboard = []
    
    for chat in chats[page * 8:(page + 1) * 8]:
        keyboard.append([
            types.InlineKeyboardButton(
                text=f"{chat['id']}. {chat['title'][:40]}",
                callback_data=f"open_chat:{chat['id']}:[{page}]"
            )
        ])
    
    if total_pages > 1:
        keyboard.append([
            types.InlineKeyboardButton(
                text = "❮",
                callback_data=f"history_page:{page - 1}" if page > 0 else "history_noop"
            ),
            types.InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}",
                callback_data="history_noop"
            ),
            types.InlineKeyboardButton(
                text="❯",
                callback_data=f"history_page:{page + 1}" if page < total_pages - 1 else "history_noop"
            )
        ])
        
    keyboard.append([
        types.InlineKeyboardButton(
            text="← Назад в главное меню",
            callback_data="back_menu"
        )
    ])
    
    text = "История диалогов\nВыбери диалог:" if chats else "История пока пустая"
    
    await callback.message.edit_text(
        text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    
@router.callback_query(F.data == "back_menu")
async def back_menu(callback: types.CallbackQuery):
    await callback.answer()
    
    name = callback.from_user.first_name
    
    await callback.message.edit_text(
        f"👋 Добро пожаловать в AlfaAI, {name}!",
        reply_markup=button
    )