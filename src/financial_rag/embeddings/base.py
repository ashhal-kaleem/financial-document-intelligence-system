"""Abstract base class for all embedding backends."""

from abc import ABC, abstractmethod
import numpy as np


class BaseEmbedder(ABC):
    """Contract for embedding models.

    Swap implementations freely: sentence-transformers locally,
    OpenAI in the cloud, or a mock in tests — all with the same interface.
    """

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of texts.

        Args:
            texts: List of strings to embed.

        Returns:
            Float32 array of shape (len(texts), embedding_dim),
            with each row L2-normalized to unit length.
        """
        ...

    @abstractmethod
    def embed_query(self, text: str) -> np.ndarray:
        """Embed a single query string.

        Returns:
            Float32 array of shape (embedding_dim,), L2-normalized.
        """
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensionality of the embedding vectors."""
        ...

    @staticmethod
    def normalize(vectors: np.ndarray) -> np.ndarray:
        """L2-normalize each row to unit length (required for cosine similarity)."""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)  # avoid division by zero
        return (vectors / norms).astype(np.float32)
