"""Embedding backend using sentence-transformers (local, no API key)."""

import numpy as np
from financial_rag.embeddings.base import BaseEmbedder


class SentenceTransformerEmbedder(BaseEmbedder):
    """Wraps sentence-transformers for local CPU embedding.

    First call downloads the model (~80 MB). Subsequent calls use cache.

    Args:
        model_name: HuggingFace model name.
            'all-MiniLM-L6-v2'  → 384 dims, fast, good quality (default)
            'all-mpnet-base-v2' → 768 dims, slower, better quality
        batch_size: How many texts to embed per forward pass.
        show_progress: Show tqdm bar during batch embedding.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        batch_size: int = 64,
        show_progress: bool = False,
    ) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self.show_progress = show_progress
        self._model = None  # lazy load

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise ImportError(
                    "Install sentence-transformers: pip install sentence-transformers"
                ) from exc
            print(f"  [embedder] Loading model '{self.model_name}' (first run downloads ~80MB)...")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: list[str]) -> np.ndarray:
        model = self._load_model()
        vectors = model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=self.show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True,  # L2-normalize built-in
        )
        return vectors.astype(np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return self.embed([text])[0]

    @property
    def dimension(self) -> int:
        model = self._load_model()
        return model.get_sentence_embedding_dimension()
