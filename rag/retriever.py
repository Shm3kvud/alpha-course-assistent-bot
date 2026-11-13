import asyncio
import logging

from langchain_core.documents import Document

from config import get_settings
from vector_db.vectorstore import search

log = logging.getLogger(__name__)

def retrieve(query: str, k: int | None = None) -> list[Document]:
    settings = get_settings()
    results = search(query=query, k=k)
    log.debug("Search вернул %d объектов", len(results))

    return [doc for doc, score in results if score >= settings.score_threshold]


async def aretrieve(query: str, k: int | None = None) -> list[Document]:
    return await asyncio.to_thread(retrieve, query, k)
