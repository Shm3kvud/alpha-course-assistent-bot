import logging
from rag.retriever import retrieve
from llm.client import generate
from llm.prompts import SYSTEM_PROMPT

log = logging.getLogger(__name__)

async def answer(query: str, history: list[dict] | None = None) -> str:
    try:
        docs = await retrieve(query, k=5)
    except Exception:
        log.exception("Ошибка при поиске в БД")
        return "Извините, у меня проблемы с базой знаний. Попробуйте позже."

    if not docs:
        return "К сожалению, я не нашёл ответа на этот вопрос. Уточните у оператора."

    context_blocks = [doc.page_content for doc in docs]
    context = "\n\n".join(context_blocks)

    try:
        answer_text = await generate(
            system_prompt=SYSTEM_PROMPT,
            context=context,
            question=query,
            history=history,
        )
        return answer_text
    except Exception:
        log.exception("Ошибка при генерации ответа LLM")
        return "Извините, произошла ошибка. Попробуйте ещё раз."