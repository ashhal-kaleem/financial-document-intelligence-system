"""Server-side Groq answer flow: quota gates, citation enforcement, fail-closed errors.
Provider and Supabase are fakes; no key, network or spend."""
import httpx
import pytest
from uuid import uuid4
from src.core import auth
from src.core.errors import FDISException
from src.domain.models import AskRequest, Citation, DocumentChunk
from src.infrastructure import groq_client as gc
from src.services.inference import InferenceService
from src.services.retrieval import RetrievalService

OWNER = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def _chunk():
    return DocumentChunk(
        document_id=uuid4(), content="Revenue $100 million, FY2024.", source="report.pdf",
        page=2, chunk_index=0, total_chunks=1, similarity=0.9,
    )


class FakeStore:
    async def get_visible_document_ids(self, owner_id):
        return [uuid4()]

    async def match_chunks(self, **kw):
        return [_chunk()]


class FakeEmbedder:
    def embed_query(self, q):
        return [0.0] * 384


def make_inference():
    r = RetrievalService(supabase_client=FakeStore())
    r.embedding_client = FakeEmbedder()
    return InferenceService(retrieval_service=r)


class FakeQuota:
    def __init__(self, result="ok"):
        self.result, self.calls, self.refunds = result, [], []

    async def take_question_quota(self, owner_id, user_limit, global_limit):
        self.calls.append((owner_id, user_limit, global_limit))
        return self.result

    async def refund_question_quota(self, owner_id):
        self.refunds.append(owner_id)


class FakeGroq:
    def __init__(self, answers):
        self.answers, self.calls = list(answers), []

    async def complete(self, messages):
        self.calls.append(messages)
        return self.answers.pop(0)


def make_route(monkeypatch, quota="ok", answers=None):
    from src.api.routes import ask as ask_routes
    monkeypatch.setattr(ask_routes, "inference_service", make_inference())
    q = FakeQuota(quota)
    g = FakeGroq(answers or ["Revenue was $100 million [1]."])
    monkeypatch.setattr(ask_routes, "supabase", q)
    monkeypatch.setattr(ask_routes, "groq", g)
    return ask_routes, q, g


@pytest.mark.asyncio
async def test_answer_flow_returns_grounded_answer_and_citations(monkeypatch):
    ask_routes, q, g = make_route(monkeypatch)
    result = await ask_routes.ask_answer(AskRequest(question="Revenue?"), auth.AuthUser(OWNER))
    assert result["data"]["answer"] == "Revenue was $100 million [1]."
    assert result["data"]["citations"][0]["filename"] == "report.pdf"
    assert result["data"]["model"]
    assert len(q.calls) == 1 and len(g.calls) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("quota,code", [("user_exhausted", "daily_question_limit"), ("global_exhausted", "free_quota_exhausted")])
async def test_quota_exhaustion_blocks_before_any_model_call(monkeypatch, quota, code):
    ask_routes, q, g = make_route(monkeypatch, quota=quota)
    with pytest.raises(FDISException) as err:
        await ask_routes.ask_answer(AskRequest(question="Revenue?"), auth.AuthUser(OWNER))
    assert err.value.status_code == 429 and err.value.code == code
    assert g.calls == []


@pytest.mark.asyncio
async def test_answer_without_valid_citations_is_retried_once_then_refused(monkeypatch):
    ask_routes, q, g = make_route(monkeypatch, answers=["no markers here", "still none"])
    with pytest.raises(FDISException) as err:
        await ask_routes.ask_answer(AskRequest(question="Revenue?"), auth.AuthUser(OWNER))
    assert err.value.status_code == 422 and err.value.code == "invalid_citations"
    assert len(g.calls) == 2


@pytest.mark.asyncio
async def test_citation_retry_succeeds_when_second_answer_is_grounded(monkeypatch):
    ask_routes, q, g = make_route(monkeypatch, answers=["no markers", "Revenue $100 million [1]."])
    result = await ask_routes.ask_answer(AskRequest(question="Revenue?"), auth.AuthUser(OWNER))
    assert result["data"]["answer"].endswith("[1].")
    assert len(g.calls) == 2


def _mock_groq_http(monkeypatch, handler):
    real = httpx.AsyncClient
    monkeypatch.setattr(
        gc.httpx, "AsyncClient",
        lambda **kw: real(transport=httpx.MockTransport(handler), **{k: v for k, v in kw.items() if k != "transport"}),
    )


@pytest.mark.asyncio
async def test_missing_key_fails_closed_without_network(monkeypatch):
    monkeypatch.setattr(gc.get_settings(), "GROQ_API_KEY", "")
    def forbidden(request):
        raise AssertionError("No provider call without a key")
    _mock_groq_http(monkeypatch, forbidden)
    with pytest.raises(FDISException) as err:
        await gc.GroqClient().complete([{"role": "user", "content": "hi"}])
    assert err.value.status_code == 503 and err.value.code == "ai_not_configured"


@pytest.mark.asyncio
async def test_provider_429_maps_to_free_quota_error(monkeypatch):
    monkeypatch.setattr(gc.get_settings(), "GROQ_API_KEY", "test-key")
    def handler(request):
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(429, json={"error": {"message": "rate limited"}}, headers={"retry-after": "45"})
    _mock_groq_http(monkeypatch, handler)
    with pytest.raises(FDISException) as err:
        await gc.GroqClient().complete([{"role": "user", "content": "hi"}])
    assert err.value.status_code == 429 and err.value.code == "free_quota_exhausted"
    assert "45 seconds" in err.value.detail


@pytest.mark.asyncio
async def test_non_stop_finish_reason_is_rejected(monkeypatch):
    monkeypatch.setattr(gc.get_settings(), "GROQ_API_KEY", "test-key")
    def handler(request):
        return httpx.Response(200, json={"choices": [{"message": {"content": "cut off"}, "finish_reason": "length"}]})
    _mock_groq_http(monkeypatch, handler)
    with pytest.raises(FDISException) as err:
        await gc.GroqClient().complete([{"role": "user", "content": "hi"}])
    assert err.value.status_code == 502 and err.value.code == "incomplete_answer"


@pytest.mark.asyncio
async def test_complete_answer_is_returned(monkeypatch):
    monkeypatch.setattr(gc.get_settings(), "GROQ_API_KEY", "test-key")
    seen = []
    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"choices": [{"message": {"content": "Grounded [1]."}, "finish_reason": "stop"}]})
    _mock_groq_http(monkeypatch, handler)
    out = await gc.GroqClient().complete([{"role": "user", "content": "hi"}])
    assert out == "Grounded [1]."
    import json
    body = json.loads(seen[0].content)
    assert body["model"] == gc.get_settings().GROQ_MODEL and body["stream"] is False


def test_fullwidth_citation_markers_are_normalized(monkeypatch):
    """gpt-oss models emit 【1】; the answer must validate and ship as [1]."""
    from src.api.routes import ask as ask_route
    from src.domain.citation import normalize_citation_markers
    from src.domain.models import Citation

    cits = [Citation(citation_id=1, document_id="22222222-2222-2222-2222-222222222222", filename="e2e.pdf", page=1, chunk_index=0, total_chunks=1, similarity=0.9, snippet="x")]
    answer = normalize_citation_markers("Revenue was USD 100 million【1】.")
    assert answer == "Revenue was USD 100 million[1]."
    from src.domain.citation import validate_answer_citations
    assert validate_answer_citations(answer, cits)


@pytest.mark.asyncio
async def test_failed_answer_refunds_exactly_one_question_unit(monkeypatch):
    ask_routes, q, g = make_route(monkeypatch, answers=["no markers", "still none"])
    with pytest.raises(FDISException):
        await ask_routes.ask_answer(AskRequest(question="Revenue?"), auth.AuthUser(OWNER))
    assert q.refunds == [OWNER]


@pytest.mark.asyncio
async def test_incomplete_answer_also_refunds(monkeypatch):
    failing = FakeGroq([])
    async def boom(messages):
        raise FDISException("Incomplete answer", "nope", 502, "incomplete_answer")
    failing.complete = boom
    from src.api.routes import ask as ask_routes
    monkeypatch.setattr(ask_routes, "inference_service", make_inference())
    q = FakeQuota("ok")
    monkeypatch.setattr(ask_routes, "supabase", q)
    monkeypatch.setattr(ask_routes, "groq", failing)
    with pytest.raises(FDISException):
        await ask_routes.ask_answer(AskRequest(question="Revenue?"), auth.AuthUser(OWNER))
    assert q.refunds == [OWNER]


@pytest.mark.asyncio
async def test_successful_answer_is_never_refunded(monkeypatch):
    ask_routes, q, g = make_route(monkeypatch)
    await ask_routes.ask_answer(AskRequest(question="Revenue?"), auth.AuthUser(OWNER))
    assert q.refunds == []


@pytest.mark.asyncio
async def test_groq_payload_uses_low_reasoning_effort(monkeypatch):
    captured = {}
    def handler(request):
        import json as _json
        captured.update(_json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok [1]"}, "finish_reason": "stop"}]})
    _mock_groq_http(monkeypatch, handler)
    monkeypatch.setattr(gc.get_settings(), "GROQ_API_KEY", "test-key")
    await gc.GroqClient().complete([{"role": "user", "content": "hi"}])
    assert captured.get("reasoning_effort") == "low"


def test_system_prompt_enforces_concise_same_language_plain_answers():
    from src.domain.citation import GROUNDED_SYSTEM_PROMPT
    p = GROUNDED_SYSTEM_PROMPT
    assert "two to four sentences for a simple question" in p and "Write like a person explaining something directly" in p
    assert "same language AND the same script" in p
    assert "never Devanagari" in p
    assert "Never emit HTML tags" in p
    assert "[1], [2]" in p or "citation marker" in p  # citation guard stays


def test_system_prompt_script_matching_variants():
    from src.domain.citation import GROUNDED_SYSTEM_PROMPT as p
    # Roman-script question -> Roman-script answer (Roman Urdu/Hinglish case)
    assert "Roman (Latin) letters gets a Roman-script answer" in p
    # Devanagari only when the user wrote it
    assert "only use Devanagari when the user wrote in Devanagari" in p
    # Explicit user language/script request wins over defaults
    assert "explicitly asks for a specific language or script, use that" in p
    # English stays English
    assert "English questions get English answers" in p
