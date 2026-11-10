import logging

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer

from config import get_settings

logger = logging.getLogger(__name__)


class E5Embeddings(Embeddings):
    def __init__(
        self,
        model_name: str | None = None,
        fallback_model_name: str | None = None,
        batch_size: int | None = None,
        device: str | None = None,
    ) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.fallback_model_name = (
            fallback_model_name or settings.embedding_fallback_model
        )
        self.batch_size = batch_size or settings.embedding_batch_size
        self.device = device or settings.embedding_device
        self.model = self._load_model()
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.use_prefixes = "e5" in self.model_name.lower()

    def _load_model(self) -> SentenceTransformer:
        try:
            return SentenceTransformer(self.model_name, device=self.device)
        except Exception:
            logger.warning(
                "Не удалось загрузить модель %s, переключаюсь на %s",
                self.model_name,
                self.fallback_model_name,
            )
            self.model_name = self.fallback_model_name
            return SentenceTransformer(self.model_name, device=self.device)

    def _prepare_documents(self, texts: list[str]) -> list[str]:
        if not self.use_prefixes:
            return texts
        return [f"passage: {text}" for text in texts]

    def _prepare_query(self, text: str) -> str:
        if not self.use_prefixes:
            return text
        return f"query: {text}"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(
            self._prepare_documents(texts),
            normalize_embeddings=True,
            batch_size=self.batch_size,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        vector = self.model.encode(
            self._prepare_query(text),
            normalize_embeddings=True,
        )
        return vector.tolist()
