from sentence_transformers import SentenceTransformer

from app.core.config import get_settings
from app.core.exceptions import ServiceException


class EmbeddingService:
    """
    Create embeddings for document chunks and user queries.

    Phase 1 uses local SentenceTransformers embeddings so the project
    works without paid API keys.

    Later, this can be swapped for OpenAI, Gemini, or Azure embeddings.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.model_name = settings.embedding_model_name
        self.batch_size = settings.embedding_batch_size
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            try:
                self._model = SentenceTransformer(self.model_name)
            except Exception as exc:
                raise ServiceException(
                    f"Failed to load embedding model: {self.model_name}"
                ) from exc

        return self._model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        clean_texts = [text.strip() for text in texts if text and text.strip()]

        if not clean_texts:
            return []

        try:
            embeddings = self.model.encode(
                clean_texts,
                batch_size=self.batch_size,
                normalize_embeddings=True,
                show_progress_bar=False,
            )

            return embeddings.tolist()

        except Exception as exc:
            raise ServiceException("Failed to create text embeddings.") from exc

    def embed_query(self, query: str) -> list[float]:
        query = query.strip()

        if not query:
            raise ServiceException("Search query cannot be empty.")

        embeddings = self.embed_texts([query])

        if not embeddings:
            raise ServiceException("Failed to create query embedding.")

        return embeddings[0]