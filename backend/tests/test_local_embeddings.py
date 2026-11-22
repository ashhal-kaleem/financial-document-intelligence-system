from pathlib import Path
import socket
import threading
from uuid import uuid4
import numpy as np
import pytest

from src.infrastructure import embedding_assets as assets
from src.infrastructure import embedding_client as enc
from src.services.ingestion import DocumentIngestionService
from src.core.errors import InvalidPDFError, FDISException
from src.domain.models import DocumentChunk


def test_local_encoder_offline_normalized_and_batch_invariant(monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("Runtime embeddings must not use network")
    monkeypatch.setattr(socket, "socket", no_network)
    client = enc.EmbeddingClient()
    text = "Operating cash flow was USD 118 billion in FY2024."
    single = np.array(client.embed_query(text))
    batch = np.array(client.embed_texts([text, "Shorter sentence."]))
    assert batch.shape == (2, 384)
    assert np.isfinite(batch).all()
    assert np.linalg.norm(batch, axis=1) == pytest.approx([1, 1], abs=1e-6)
    assert single @ batch[0] > .99999
    assert client.embed_texts([]) == []


def test_long_input_rejected_not_silently_truncated():
    client = enc.EmbeddingClient()
    with pytest.raises(FDISException, match="token search limit"):
        client.embed_query("financial revenue " * 500)
    with pytest.raises(FDISException, match="non-empty"):
        client.embed_query("  ")


def test_token_split_preserves_late_financial_fact_and_unicode():
    text = ("Revenue FY2023 USD 100 million. " * 80) + "FY2024 exact net income INR 987654 crore. अंतिम तथ्य"
    parts = assets.split_embedding_text(text)
    assert len(parts) > 1
    assert all(len(assets.get_tokenizer().encode(p).ids) <= 256 for p in parts)
    assert "987654" in parts[-1] and "अंतिम तथ्य" in parts[-1]
    assert parts[0].startswith("Revenue")
    # The suffix must survive indexing, not silently disappear at token256.
    assert text.endswith(parts[-1])


def test_missing_and_corrupt_artifact_fail_closed(tmp_path):
    with pytest.raises(RuntimeError, match="missing"):
        assets.verify_artifact(tmp_path / "absent", 3, "bad")
    p = tmp_path / "asset"
    p.write_bytes(b"bad")
    with pytest.raises(RuntimeError, match="integrity"):
        assets.verify_artifact(p, 3, "0" * 64)


def test_capacity_wait_is_bounded(monkeypatch):
    client = enc.EmbeddingClient()
    client.timeout_seconds = .001
    lock = threading.Lock()
    lock.acquire()
    monkeypatch.setattr(enc, "_INFERENCE_LOCK", lock)
    with pytest.raises(FDISException, match="busy"):
        client.embed_texts(["revenue"])
    lock.release()


def test_embedding_budget_stops_between_batches(monkeypatch):
    client = enc.EmbeddingClient()
    client.timeout_seconds = .001
    monkeypatch.setattr(enc.time, "monotonic", iter([0, 1]).__next__)
    with pytest.raises(FDISException, match="budget"):
        client.embed_texts(["revenue"])
    assert not enc._INFERENCE_LOCK.locked()


def test_chunks_keep_page_and_profile_and_work_limit(monkeypatch):
    service = DocumentIngestionService()
    chunk = DocumentChunk(document_id=uuid4(), source="report.pdf", page=17,
                          content="Revenue net income " * 400, chunk_index=0, total_chunks=1,
                          metadata={"has_table": True})
    bounded = service._bound_embedding_chunks([chunk])
    assert len(bounded) > 1
    assert all(c.page == 17 and c.metadata["embedding_profile"] == assets.PROFILE for c in bounded)
    assert all(c.metadata["has_table"] for c in bounded)
    monkeypatch.setattr(service.settings, "MAX_DOCUMENT_CHUNKS", 1)
    with pytest.raises(InvalidPDFError, match="too many"):
        service._bound_embedding_chunks([chunk])


def test_sessions_are_cached_and_cpu_only():
    session = enc._get_session()
    assert enc._get_session() is session
    assert session.get_providers() == ["CPUExecutionProvider"]


@pytest.mark.asyncio
@pytest.mark.parametrize("profile", [None, "old-provider-profile", assets.PROFILE])
async def test_vector_profile_guard(monkeypatch, profile):
    import httpx
    from src.infrastructure.supabase_client import SupabaseClient
    data = {"document_id": str(uuid4()), "content": "Revenue FY2025 USD 100 million",
            "source": "public-test.pdf", "page": 1, "chunk_index": 0, "total_chunks": 1,
            "similarity": .8, "metadata": {"embedding_profile": profile} if profile else {}}
    class FakeClient:
        def __init__(self, **kw): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, **kw):
            return httpx.Response(200, json=[data], request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    if profile != assets.PROFILE:
        with pytest.raises(FDISException) as exc:
            await SupabaseClient().match_chunks([0.0] * 384)
        assert exc.value.code == "embedding_profile_mismatch"
    else:
        result = await SupabaseClient().match_chunks([0.0] * 384)
        assert len(result) == 1 and result[0].metadata["embedding_profile"] == assets.PROFILE
