from functools import lru_cache
from typing import List
from sentence_transformers import SentenceTransformer
from src.core.config import get_settings


class EmbeddingClient:
    def __init__(self, model_name: str = None):
        settings = get_settings()
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.model = SentenceTransformer(self.model_name)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        embedding = self.model.encode(query, normalize_embeddings=True, show_progress_bar=False)
        return embedding.tolist()


@lru_cache()
def get_embedding_client() -> EmbeddingClient:
    return EmbeddingClient()
