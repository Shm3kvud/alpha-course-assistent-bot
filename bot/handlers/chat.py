from db.history import create_chat, get_last_chat, save_message, get_user_chats
from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# from rag.pipeline import answer для раг!


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
    
    response = "Тут будет подключена RAG-система. В разработке"
    
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
async def show_history(callback: types.CallbackQuery):
    await callback.answer()
    
    chats = await get_user_chats(callback.from_user.id)
    
    if not chats:
        await callback.message.answer("История диалогов пуста")
        return
    
    text = "Твои диалоги:\n\n"
    
    for chat in chats:
        text += f"{chat['id']}. {chat['title']}\n"
        
    await callback.message.answer(text)