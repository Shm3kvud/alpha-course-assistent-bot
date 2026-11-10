from sentence_transformers import SentenceTransformer

MODEL_NAME = "intfloat/multilingual-e5-large"


class E5Embeddings:
    def __init__(self, model_name: str = MODEL_NAME) -> None:
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        prepared = [f"passage: {text}" for text in texts]
        vectors = self.model.encode(
            prepared,
            normalize_embeddings=True,
            batch_size=16,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        vector = self.model.encode(
            f"query: {text}",
            normalize_embeddings=True,
        )
        return vector.tolist()


if __name__ == "__main__":
    import numpy as np

    embedder = E5Embeddings()
    print(embedder.dimension)

    docs = [
        "Курс по маркетплейсам: как запустить продажи на Ozon и Wildberries.",
        "Курс по финансовой грамотности: личный бюджет и налоги.",
        "Курс по открытию табачного магазина: лицензии и закупки.",
    ]
    doc_vectors = np.array(embedder.embed_documents(docs))
    query_vector = np.array(embedder.embed_query("хочу открыть табачный магазин"))
    scores = doc_vectors @ query_vector
    for text, score in sorted(zip(docs, scores), key=lambda item: item[1], reverse=True):
        print(f"{score:.4f}  {text}")
