"""Deterministic mock embedder for unit tests and CI environments."""

import numpy as np
from financial_rag.embeddings.base import BaseEmbedder


class MockEmbedder(BaseEmbedder):
    """Returns deterministic normalized random vectors.

    Uses the text hash as a random seed so the same text always produces
    the same vector — tests are reproducible without downloading any model.

    Args:
        dim: Embedding dimensionality (default 16 keeps tests fast).
    """

    def __init__(self, dim: int = 16) -> None:
        self._dim = dim

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = np.stack([self._text_to_vector(t) for t in texts])
        return self.normalize(vectors)

    def embed_query(self, text: str) -> np.ndarray:
        return self._text_to_vector(text)

    @property
    def dimension(self) -> int:
        return self._dim

    def _text_to_vector(self, text: str) -> np.ndarray:
        seed = hash(text) % (2**31)
        rng = np.random.default_rng(seed)
        v = rng.standard_normal(self._dim).astype(np.float32)
        norm = np.linalg.norm(v)
        return v / norm if norm > 0 else v
