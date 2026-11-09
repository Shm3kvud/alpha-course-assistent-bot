from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


router = Router()


class Questions(statesGroup):
    waiting_question = State()


@router.callback_query(F.data == "ask_question")
async def ask_question(callback: types.CallbackQuery):
    await callback.answer()
    await state.set_state(Questions.waiting_question)
    
    await callback.message.answer(
        "Расскажи, с какой задачей в бизнесе нужна помощь."
    )
    
    
@router.message(Questions.waiting_question, F.text)
async def get_question(message: types.Message):
    question = message.text.strip()
    
    
    await message.answer(
        "ИИ в разработке"
    )