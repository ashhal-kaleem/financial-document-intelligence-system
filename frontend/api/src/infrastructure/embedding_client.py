from functools import lru_cache
from typing import List
from huggingface_hub import InferenceClient
from src.core.config import get_settings


class EmbeddingClient:
    def __init__(self, model_name: str = None):
        settings = get_settings()
        self.model_name = model_name or f"sentence-transformers/{settings.EMBEDDING_MODEL_NAME}"
        self.hf_token = settings.HF_TOKEN
        self.client = InferenceClient(token=self.hf_token)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embs = self.client.feature_extraction(texts, model=self.model_name)
        if hasattr(embs, "tolist"):
            return embs.tolist()
        return [list(e) for e in embs]

    def embed_query(self, query: str) -> List[float]:
        emb = self.client.feature_extraction(query, model=self.model_name)
        if hasattr(emb, "tolist"):
            emb_list = emb.tolist()
            if emb_list and isinstance(emb_list[0], list):
                return emb_list[0]
            return emb_list
        return list(emb)


@lru_cache()
def get_embedding_client() -> EmbeddingClient:
    return EmbeddingClient()
