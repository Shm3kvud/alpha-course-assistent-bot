import logging
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat

from config import get_settings

log = logging.getLogger(__name__)

_llm: GigaChat | None = None


def _get_llm() -> GigaChat:
    global _llm
    settings = get_settings()
    if _llm is None:
        _llm = GigaChat(
            credentials=settings.gigachat_api_key,
            verify_ssl_certs=False,
            model=settings.gigachat_model,
            temperature=0.2,
            max_tokens=500,
            timeout=30,
        )
    return _llm


async def generate(
    system_prompt: str,
    context: str,
    question: str,
    history: list[dict] | None = None,
) -> str:
    messages = [SystemMessage(content=system_prompt)]

    if history:
        for turn in history[-5:]:
            messages.append(HumanMessage(content=turn["user"]))
            messages.append(AIMessage(content=turn["assistant"]))

    messages.append(HumanMessage(
        content=f"Контекст:\n{context}\n\nВопрос пользователя: {question}"
    ))

    try:
        resp = await _get_llm().ainvoke(messages)
        return resp.content.strip()
    except Exception:
        log.exception("GigaChat generation failed")
        return "Извините, произошла ошибка. Попробуйте ещё раз."