"""Unit tests for the embeddings layer."""

import numpy as np
import pytest

from financial_rag.embeddings.mock import MockEmbedder
from financial_rag.embeddings.base import BaseEmbedder


class TestMockEmbedder:
    def test_embed_returns_correct_shape(self):
        emb = MockEmbedder(dim=16)
        result = emb.embed(["hello", "world", "foo"])
        assert result.shape == (3, 16)

    def test_embed_query_returns_1d(self):
        emb = MockEmbedder(dim=16)
        result = emb.embed_query("test query")
        assert result.shape == (16,)

    def test_vectors_are_normalized(self):
        emb = MockEmbedder(dim=32)
        vectors = emb.embed(["text one", "text two", "text three"])
        norms = np.linalg.norm(vectors, axis=1)
        np.testing.assert_allclose(norms, 1.0, atol=1e-6)

    def test_deterministic_same_text(self):
        emb = MockEmbedder(dim=16)
        v1 = emb.embed_query("financial results 2025")
        v2 = emb.embed_query("financial results 2025")
        np.testing.assert_array_equal(v1, v2)

    def test_different_texts_produce_different_vectors(self):
        emb = MockEmbedder(dim=16)
        v1 = emb.embed_query("utilidad neta interbank")
        v2 = emb.embed_query("riesgo crediticio scotiabank")
        assert not np.allclose(v1, v2)

    def test_dimension_property(self):
        emb = MockEmbedder(dim=64)
        assert emb.dimension == 64

    def test_normalize_static_method(self):
        raw = np.array([[3.0, 4.0], [1.0, 0.0]], dtype=np.float32)
        normalized = BaseEmbedder.normalize(raw)
        norms = np.linalg.norm(normalized, axis=1)
        np.testing.assert_allclose(norms, 1.0, atol=1e-6)

    def test_normalize_handles_zero_vector(self):
        raw = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)
        result = BaseEmbedder.normalize(raw)
        assert not np.any(np.isnan(result))

    def test_output_is_float32(self):
        emb = MockEmbedder(dim=16)
        vectors = emb.embed(["test"])
        assert vectors.dtype == np.float32
