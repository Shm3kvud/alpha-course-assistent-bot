from __future__ import annotations

import logging
from functools import lru_cache

from langchain_core.documents import Document
from langchain_postgres import PGVector

from config import get_settings
from rag.embeddings import E5Embeddings

logger = logging.getLogger(__name__)

_vector_store: PGVector | None = None


@lru_cache
def get_embeddings() -> E5Embeddings:
    return E5Embeddings()


def _build_vector_store(pre_delete: bool) -> PGVector:
    settings = get_settings()
    embeddings = get_embeddings()
    return PGVector(
        embeddings=embeddings,
        collection_name=settings.collection_name,
        connection=str(settings.vector_database_url),
        embedding_length=embeddings.dimension,
        pre_delete_collection=pre_delete,
        use_jsonb=True,
    )


def get_vectorstore(pre_delete: bool = False) -> PGVector:
    global _vector_store
    if pre_delete or _vector_store is None:
        _vector_store = _build_vector_store(pre_delete)
    return _vector_store


def add_documents(docs: list[Document], ids: list[str]) -> None:
    if len(docs) != len(ids):
        raise ValueError("docs и ids должны быть одинаковой длины")
    vector_store = get_vectorstore()
    vector_store.add_documents(documents=docs, ids=ids)
    logger.info("Записано/обновлено документов: %d", len(ids))


def search(query: str, k: int | None = None) -> list[tuple[Document, float]]:
    settings = get_settings()
    k = k or settings.top_k
    vector_store = get_vectorstore()
    results = vector_store.similarity_search_with_score(query=query, k=k)

    return [(doc, 1.0 - distance) for doc, distance in results]
