from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

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
    
    
    response = await answer(query=question)
    
    await messag.answer(response)