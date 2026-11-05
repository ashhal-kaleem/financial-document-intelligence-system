"""Integration-style tests with Supabase, embeddings and the LLM replaced by fakes.
They prove our code's behavior (scoping, filters, batching, fail-closed switches), not the
behavior of the real hosted services."""
import asyncio
import httpx
import pytest
from uuid import UUID, uuid4
from src.core import auth
from src.core.config import get_settings
from src.domain.citation import NOT_COVERED_ANSWER
from src.domain.models import DocumentChunk
from src.infrastructure import supabase_client as sc
from src.infrastructure.embedding_client import EmbeddingClient
from src.services.inference import InferenceService
from src.services.ingestion import DocumentIngestionService
from src.services.retrieval import RetrievalService
from tests.test_services import create_sample_financial_pdf_bytes

OWNER = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def mock_supabase(monkeypatch, handler):
    real = httpx.AsyncClient
    monkeypatch.setattr(
        sc.httpx, "AsyncClient",
        lambda **kw: real(transport=httpx.MockTransport(handler), **{k: v for k, v in kw.items() if k != "transport"}),
    )


@pytest.mark.asyncio
async def test_queries_are_scoped_to_owner_or_sample(monkeypatch):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json=[])
    mock_supabase(monkeypatch, handler)
    client = sc.SupabaseClient()
    await client.get_documents(OWNER)
    await client.get_document_by_id(uuid4(), OWNER)
    await client.get_visible_document_ids(OWNER)
    for r in seen:
        assert f"owner_id.eq.{OWNER}" in str(r.url) and "is_sample.eq.true" in str(r.url)


@pytest.mark.asyncio
async def test_delete_refuses_unowned_and_never_deletes_samples(monkeypatch):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json=[])  # ownership lookup finds nothing
    mock_supabase(monkeypatch, handler)
    assert await sc.SupabaseClient().delete_document(uuid4(), OWNER) is False
    assert [r.method for r in seen] == ["GET"]
    assert "is_sample=eq.false" in str(seen[0].url) and f"owner_id=eq.{OWNER}" in str(seen[0].url)


class FakeStore:
    def __init__(self, visible, matches):
        self.visible, self.matches, self.calls = visible, matches, []

    async def get_visible_document_ids(self, owner_id):
        return self.visible

    async def match_chunks(self, **kw):
        self.calls.append(kw)
        return self.matches


class FakeEmbedder:
    def embed_query(self, q):
        return [0.0] * 384


def make_retrieval(store):
    r = RetrievalService(supabase_client=store)
    r.embedding_client = FakeEmbedder()
    return r


@pytest.mark.asyncio
async def test_retrieval_ignores_foreign_ids_and_has_no_zero_threshold_fallback():
    mine, foreign = uuid4(), uuid4()
    store = FakeStore(visible=[mine], matches=[])
    out = await make_retrieval(store).retrieve_relevant_chunks("q", document_ids=[mine, foreign], owner_id=OWNER)
    assert out == []
    assert len(store.calls) == 1  # no second, looser call
    assert store.calls[0]["document_ids"] == [mine]
    assert store.calls[0]["match_threshold"] > 0


@pytest.mark.asyncio
async def test_retrieval_with_no_visible_documents_skips_search():
    store = FakeStore(visible=[], matches=[])
    assert await make_retrieval(store).retrieve_relevant_chunks("q", owner_id=OWNER) == []
    assert store.calls == []


class ExplodingLLM:
    async def stream_chat(self, *a, **k):
        raise AssertionError("LLM must not be called when nothing relevant was retrieved")
        yield


@pytest.mark.asyncio
async def test_no_context_returns_fixed_not_covered_answer_without_llm():
    svc = InferenceService(retrieval_service=make_retrieval(FakeStore(visible=[uuid4()], matches=[])), llm_client=ExplodingLLM())
    events = [e async for e in svc.stream_answer("what is the CEO's salary?", owner_id=OWNER)]
    tokens = "".join(e["token"] for e in events if e["event"] == "token")
    assert tokens == NOT_COVERED_ANSWER
    assert events[-1]["event"] == "done" and events[-1]["citations_count"] == 0


def test_no_context_prompt_pins_the_exact_sentence():
    svc = InferenceService(retrieval_service=make_retrieval(FakeStore([], [])), llm_client=ExplodingLLM())
    msgs = svc.build_rag_prompt("q", [], [])
    assert NOT_COVERED_ANSWER in msgs[-1]["content"] and "exactly" in msgs[-1]["content"]


class FakeIngestStore:
    def __init__(self):
        self.chunks, self.status = [], None

    async def create_document(self, doc):
        self.doc = doc
        return doc

    async def upload_pdf(self, *a):
        return "x"

    async def insert_chunks_batch(self, chunks):
        self.chunks = chunks

    async def delete_chunks(self, doc_id):
        self.deleted = doc_id

    async def update_document_status(self, document_id, status, **kw):
        self.status = (status, kw)


@pytest.mark.asyncio
async def test_ingestion_pipeline_sets_owner_and_embeds():
    store = FakeIngestStore()
    svc = DocumentIngestionService(supabase_client=store)
    svc.embedding_client = type("E", (), {"embed_texts": lambda self, t: [[0.1] * 384 for _ in t]})()
    doc = await svc.ingest_document("r.pdf", create_sample_financial_pdf_bytes(), owner_id=OWNER)
    assert store.doc.owner_id == OWNER and doc.status == "ready"
    assert store.chunks and all(len(c.embedding) == 384 for c in store.chunks)
    assert store.chunks[0].page == 1 and "391,035" in "".join(c.content for c in store.chunks)


@pytest.mark.asyncio
async def test_ingestion_failure_stores_generic_message_only():
    store = FakeIngestStore()
    svc = DocumentIngestionService(supabase_client=store)

    def boom(texts):
        raise RuntimeError("hf token hf_SECRET leaked in message")
    svc.embedding_client = type("E", (), {"embed_texts": lambda self, t: boom(t)})()
    with pytest.raises(RuntimeError):
        await svc.ingest_document("r.pdf", create_sample_financial_pdf_bytes(), owner_id=OWNER)
    status, kw = store.status
    assert status == "error" and "hf_SECRET" not in kw["error_message"]


def test_embedding_batches_and_retries(monkeypatch):
    client = EmbeddingClient.__new__(EmbeddingClient)
    client.model_name, client.batch_size, client.max_retries, client.retry_delay = "m", 2, 3, 0
    attempts = {"n": 0}

    class Flaky:
        def feature_extraction(self, batch, model):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise RuntimeError("429")
            return [[1.0] * 3 for _ in batch]
    client.client = Flaky()
    out = client.embed_texts(["a", "b", "c", "d", "e"])
    assert len(out) == 5
    assert attempts["n"] == 4  # 3 batches + 1 retry


@pytest.mark.parametrize(
    "auth_required,debug,platform,expected",
    [(True, True, None, False), (False, False, None, False), (False, True, "RENDER", False),
     (False, True, "VERCEL", False), (False, True, None, True)],
)
def test_auth_bypass_fails_closed(monkeypatch, auth_required, debug, platform, expected):
    s = get_settings()
    monkeypatch.setattr(s, "AUTH_REQUIRED", auth_required)
    monkeypatch.setattr(s, "DEBUG", debug)
    for v in ("RENDER", "VERCEL", "VERCEL_ENV", "FLY_APP_NAME", "K_SERVICE"):
        monkeypatch.delenv(v, raising=False)
    if platform:
        monkeypatch.setenv(platform, "1")
    assert auth.auth_bypass_enabled() is expected


@pytest.mark.asyncio
async def test_token_with_non_uuid_user_id_is_rejected(monkeypatch):
    def handler(request):
        return httpx.Response(200, json={"id": "x),or=(is_sample.eq.true", "email": "a@b.c"})
    real = httpx.AsyncClient
    monkeypatch.setattr(auth.httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(handler)))
    assert await auth._verify_with_supabase("tok") is None


# ---- durable queue ----
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.routes import documents as documents_route
from src.core.auth import AuthUser, get_current_user
from src.domain.models import Document
from src.services.worker import IngestionWorker


class QueueStore(FakeIngestStore):
    def __init__(self, pdf=None, fail_upload=False):
        super().__init__()
        self.pdf, self.fail_upload, self.queue, self.statuses = pdf, fail_upload, [], []

    async def upload_pdf(self, *a):
        if self.fail_upload:
            raise RuntimeError("storage down")

    async def get_pdf_bytes(self, doc_id, filename):
        return self.pdf

    async def update_document_status(self, document_id, status, **kw):
        self.statuses.append((status, kw))

    async def fail_stale_documents(self, *a):
        return 0

    async def claim_next_document(self, *a):
        return self.queue.pop(0) if self.queue else None


@pytest.mark.asyncio
async def test_enqueue_creates_queued_row_and_stores_pdf():
    store = QueueStore()
    svc = DocumentIngestionService(supabase_client=store)
    doc = await svc.enqueue_document("r.pdf", b"%PDF-x", owner_id=OWNER)
    assert doc.status == "queued" and store.doc.owner_id == OWNER


@pytest.mark.asyncio
async def test_enqueue_marks_error_when_storage_fails():
    store = QueueStore(fail_upload=True)
    svc = DocumentIngestionService(supabase_client=store)
    with pytest.raises(RuntimeError):
        await svc.enqueue_document("r.pdf", b"%PDF-x", owner_id=OWNER)
    assert store.statuses[-1][0] == "error"


@pytest.mark.asyncio
async def test_worker_processes_claimed_job_and_idles_when_empty():
    store = QueueStore(pdf=create_sample_financial_pdf_bytes())
    svc = DocumentIngestionService(supabase_client=store)
    svc.embedding_client = type("E", (), {"embed_texts": lambda self, t: [[0.1] * 384 for _ in t]})()
    worker = IngestionWorker(svc)
    assert await worker.run_once() is False
    store.queue.append(Document(filename="r.pdf", status="processing", owner_id=OWNER))
    assert await worker.run_once() is True
    assert store.statuses[-1][0] == "ready" and store.chunks


@pytest.mark.asyncio
async def test_worker_marks_error_when_stored_pdf_missing():
    store = QueueStore(pdf=None)
    worker = IngestionWorker(DocumentIngestionService(supabase_client=store))
    store.queue.append(Document(filename="r.pdf", status="processing", owner_id=OWNER))
    await worker.run_once()
    assert store.statuses[-1][0] == "error"


@pytest.mark.asyncio
async def test_worker_survives_a_failing_iteration():
    store = QueueStore()

    async def boom(*a):
        raise RuntimeError("db down")
    store.fail_stale_documents = boom
    worker = IngestionWorker(DocumentIngestionService(supabase_client=store))
    worker.settings = type("S", (), {"WORKER_POLL_SECONDS": 0.01, "JOB_STALE_SECONDS": 1, "JOB_MAX_ATTEMPTS": 1})()
    worker.start()
    await asyncio.sleep(0.05)
    assert not worker._task.done()  # loop kept running after the error
    await worker.stop()


def test_queue_mode_upload_returns_202_and_serverless_falls_back_inline(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: AuthUser(id=OWNER)
    s = get_settings()
    monkeypatch.setattr(s, "INGESTION_MODE", "queue")
    monkeypatch.delenv("VERCEL", raising=False)

    async def fake_enqueue(**kw):
        return Document(filename=kw["filename"], status="queued", owner_id=kw["owner_id"])
    monkeypatch.setattr(documents_route.ingestion_service, "enqueue_document", fake_enqueue)
    res = TestClient(app).post("/api/v1/documents", files={"file": ("r.pdf", b"%PDF-1.4 x", "application/pdf")})
    assert res.status_code == 202 and res.json()["data"]["status"] == "queued"

    from src.core.config import effective_ingestion_mode
    monkeypatch.setenv("VERCEL", "1")
    assert effective_ingestion_mode() == "inline"
    app.dependency_overrides.clear()
