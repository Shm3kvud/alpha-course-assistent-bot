import asyncio

from langchain_core.documents import Document

from config import get_settings
from vector_db.vectorstore import search


def retrieve(query: str, k: int | None = None) -> list[Document]:
    settings = get_settings()
    results = search(query=query, k=k)

    return [doc for doc, score in results if score >= settings.score_threshold]


async def aretrieve(query: str, k: int | None = None) -> list[Document]:
    return await asyncio.to_thread(retrieve, query, k)
