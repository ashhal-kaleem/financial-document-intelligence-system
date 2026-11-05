import time
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
        self.batch_size = 64
        self.max_retries = 3
        self.retry_delay = 1.0

    def _embed_batch(self, batch: List[str]) -> List[List[float]]:
        last_exc: Exception = RuntimeError("embedding failed")
        for attempt in range(self.max_retries):
            try:
                embs = self.client.feature_extraction(batch, model=self.model_name)
                return embs.tolist() if hasattr(embs, "tolist") else [list(e) for e in embs]
            except Exception as exc:  # network/rate-limit errors from the HF client
                last_exc = exc
                time.sleep(self.retry_delay * (2 ** attempt))
        raise last_exc

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embeds in batches so one huge filing is not a single oversized request."""
        out: List[List[float]] = []
        for i in range(0, len(texts), self.batch_size):
            out.extend(self._embed_batch(texts[i : i + self.batch_size]))
        return out

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
