import asyncio
import logging
import sys

from langchain_core.documents import Document

from db.db_loader import get_all_documents
from vector_db.vectorstore import add_documents, get_vectorstore

log = logging.getLogger(__name__)

BATCH_SIZE = 200


def _validate_ids(ids: list[str]):
    if len(ids) != len(set(ids)):
        raise ValueError("id неуникальны.")


def _to_list(all_docs: dict[str, list[Document]]) -> list[Document]:
    list_of_docs = []

    for docs in all_docs.values():
        for doc in docs:
            doc_id: str | None = doc.metadata.get("id")

            if doc_id:
                doc.metadata["source_type"] = doc_id[: doc_id.find(":")]

            list_of_docs.append(doc)

    return list_of_docs


def ingest() -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    all_docs = asyncio.run(get_all_documents())
    docs = _to_list(all_docs)
    ids = [doc.metadata["id"] for doc in docs]

    _validate_ids(ids)

    total = len(docs)
    if total == 0:
        raise ValueError("С бд пришло 0 документов. Перезапись отменена")

    log.warning("Векторная бд будет очищена и перезаписана")
    get_vectorstore(pre_delete=True)

    for start in range(0, total, BATCH_SIZE):
        end = start + BATCH_SIZE
        add_documents(docs[start:end], ids[start:end])
        log.info("Заполнено: %d/%d", min(end, total), total)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # заглушить логи библиотек, они лишние
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
    try:
        log.info("Заполнение векторной бд началось")
        ingest()
        log.info("Векторная бд успешно заполнена")
    except Exception:
        log.exception("Ошибка заполнения векторной бд")
        raise
