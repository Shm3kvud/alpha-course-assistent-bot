import logging
from rag.retriever import aretrieve
from llm.client import generate
from llm.prompts import system_prompt
from memory.session import get_history, add_to_history
from config import get_settings

log = logging.getLogger(__name__)

async def answer(query: str, user_id: int) -> str:
    settings = get_settings()
    k = settings.top_k
    history = get_history(user_id)

    try:
        docs = await aretrieve(query, k)
    except Exception:
        log.exception("Ошибка при поиске в БД")
        return "Извините, у меня проблемы с базой знаний. Попробуйте позже."

    if not docs:
        log.exception("Контекст не найден")
        return "К сожалению, я не нашёл ответа на этот вопрос. Уточните у оператора."

    context_blocks = []
    for doc in docs:
        block = doc.page_content
        meta = doc.metadata
        
        facts = []
        
        if "cost" in meta:
            cost_val = meta["cost"]

            if str(cost_val) == "0" or cost_val == 0:
                facts.append("Стоимость: Бесплатно")
            elif cost_val:
                facts.append(f"Стоимость: {cost_val} руб.")
                
        if meta.get("duration"):
            facts.append(f"Длительность: {meta['duration']}")
            
        if str(meta.get("certificate")).lower() == "true":
            facts.append("Выдается сертификат")
            
        if str(meta.get("trial")).lower() == "true":
            facts.append("Есть пробный период")
            
        if meta.get("authors"):
            facts.append(f"Авторы: {meta['authors']}")
            
        if meta.get("url"):
            facts.append(f"Ссылка: {meta['url']}")
            
        if meta.get("experts"):
            facts.append(f"Эксперты: {meta['experts']}")
            
        if meta.get("files"):
            facts.append(f"Прикрепленные файлы: {meta['files']}")

        if facts:
            block += "\n[Дополнительные факты]: " + ". ".join(facts) + "."
            
        context_blocks.append(block)

    context = "\n\n---\n\n".join(context_blocks)

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