import logging
from rag.retriever import retrieve
from llm.client import generate
from llm.prompts import system_prompt
from memory.session import get_history, add_to_history

log = logging.getLogger(__name__)

async def answer(query: str, user_id: int) -> str:
    history = get_history(user_id)

    try:
        docs = await retrieve(query, k=5)
    except Exception:
        log.exception("Ошибка при поиске в БД")
        return "Извините, у меня проблемы с базой знаний. Попробуйте позже."

    if not docs:
        log.exception("Контекст не найден")
        return "К сожалению, я не нашёл ответа на этот вопрос. Уточните у оператора."

    context_blocks = [doc.page_content for doc in docs]
    context = "\n\n".join(context_blocks)

    try:
        answer_text = await generate(
            system_prompt=system_prompt,
            context=context,
            question=query,
            history=history,
        )
        add_to_history(user_id, query, answer_text)
        return answer_text
    
    except Exception:
        log.exception("Ошибка при генерации ответа LLM")
        return "Извините, произошла ошибка. Попробуйте ещё раз."