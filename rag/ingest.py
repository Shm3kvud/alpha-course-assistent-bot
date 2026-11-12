from db.db_loader import get_all_documents
from langchain_core.documents import Document

from vector_db.vectorstore import add_documents, get_vectorstore

BATCH_SIZE = 200


def _validate_ids(ids: list[str]):
    if len(ids) != len(set(ids)):
        raise ValueError("Id неуникальны.")


def _to_list(all_docs: dict[str, list[Document]]) -> list[Document]:
    list_of_docs = []

    for docs in all_docs.values():
        for doc in docs:
            doc_id: str | None = doc.metadata.get("id")

            if doc_id:
                doc.metadata["source_type"] = doc_id[:doc_id.find(":")]

            list_of_docs.append(doc)

    return list_of_docs


def ingest() -> None:
    all_docs = get_all_documents()
    docs = _to_list(all_docs)
    ids = [doc.metadata["id"] for doc in docs]
    _validate_ids(ids)

    get_vectorstore(pre_delete=True)

    total = len(docs)
    for start in range(0, total, BATCH_SIZE):
        end = start + BATCH_SIZE
        add_documents(docs[start:end], ids[start:end])
        print(f"{min(end, total)}/{total}")


if __name__ == "__main__":
    ingest()
