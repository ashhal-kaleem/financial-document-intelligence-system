import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.routes import documents as documents_route
from src.core import auth, rate_limit
from src.core.auth import AuthUser, get_current_user
from src.core.config import get_settings
from src.domain.models import Document

client = TestClient(app)
DOC_ID = "22222222-2222-2222-2222-222222222222"
ALICE = AuthUser(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
BOB = AuthUser(id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture(autouse=True)
def clean():
    app.dependency_overrides.clear()
    auth._token_cache.clear()
    rate_limit.reset_rate_limits()
    yield
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/v1/documents"),
        ("post", "/api/v1/documents"),
        ("get", f"/api/v1/documents/{DOC_ID}"),
        ("delete", f"/api/v1/documents/{DOC_ID}"),
        ("get", f"/api/v1/documents/{DOC_ID}/chunks"),
        ("get", f"/api/v1/documents/{DOC_ID}/pdf"),
        ("post", "/api/v1/ask/context"),
        ("post", "/api/v1/ask/stream"),
    ],
)
def test_data_endpoints_require_token(method, path):
    res = getattr(client, method)(path)
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "unauthorized"


def test_health_and_root_stay_public():
    assert client.get("/").status_code == 200
    assert client.get("/api/v1/health").status_code in (200, 503)


def test_notify_route_removed():
    assert client.post("/api/v1/notify", json={"recipient": "a@b.c", "document_name": "x", "summary": "y"}).status_code in (404, 405)


def test_invalid_token_rejected(monkeypatch):
    async def bad(token):
        return None
    monkeypatch.setattr(auth, "_verify_with_supabase", bad)
    res = client.get("/api/v1/documents", headers={"Authorization": "Bearer nope"})
    assert res.status_code == 401


def test_valid_token_resolves_user_and_is_cached(monkeypatch):
    calls = []

    async def good(token):
        calls.append(token)
        return ALICE
    monkeypatch.setattr(auth, "_verify_with_supabase", good)

    seen = {}

    async def fake_list(owner_id):
        seen["owner"] = owner_id
        return []
    monkeypatch.setattr(documents_route.supabase, "get_documents", fake_list)
    for _ in range(2):
        res = client.get("/api/v1/documents", headers={"Authorization": "Bearer abc"})
        assert res.status_code == 200
    assert seen["owner"] == ALICE.id
    assert calls == ["abc"]


def test_other_users_document_is_404(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: BOB

    async def scoped(doc_id, owner_id):
        # Mimics the owner filter: the doc belongs to Alice only.
        return Document(id=doc_id, filename="a.pdf", owner_id=ALICE.id) if owner_id == ALICE.id else None
    monkeypatch.setattr(documents_route.supabase, "get_document_by_id", scoped)
    for suffix in ("", "/chunks", "/pdf"):
        assert client.get(f"/api/v1/documents/{DOC_ID}{suffix}").status_code == 404


def test_delete_passes_owner(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: BOB
    seen = {}

    async def fake_delete(doc_id, owner_id):
        seen["owner"] = owner_id
        return False
    monkeypatch.setattr(documents_route.supabase, "delete_document", fake_delete)
    assert client.delete(f"/api/v1/documents/{DOC_ID}").status_code == 404
    assert seen["owner"] == BOB.id


def test_unhandled_error_hides_traceback(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: ALICE

    async def boom(owner_id):
        raise RuntimeError("secret internal detail SUPABASE_KEY")
    monkeypatch.setattr(documents_route.supabase, "get_documents", boom)
    res = TestClient(app, raise_server_exceptions=False).get("/api/v1/documents")
    assert res.status_code == 500
    body = res.text
    assert "traceback" not in body.lower()
    assert "secret internal detail" not in body


def test_upload_rejects_fake_pdf():
    app.dependency_overrides[get_current_user] = lambda: ALICE
    res = client.post("/api/v1/documents", files={"file": ("r.pdf", b"not really a pdf", "application/pdf")})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "invalid_pdf"


def test_safe_filename_strips_paths():
    f = documents_route.safe_filename
    assert f("../../etc/passwd.pdf") == "passwd.pdf"
    assert f('a"\r\nb.pdf') == "a___b.pdf"
    assert f("") == "document.pdf"


def test_rate_limit(monkeypatch):
    monkeypatch.setattr(get_settings(), "RATE_LIMIT_PER_MINUTE", 2)
    app.dependency_overrides[get_current_user] = lambda: ALICE
    codes = [
        client.post("/api/v1/documents", files={"file": ("r.txt", b"x", "text/plain")}).status_code
        for _ in range(3)
    ]
    assert codes == [422, 422, 429]


def test_cors_rejects_unlisted_origin():
    res = client.options(
        "/api/v1/documents",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in res.headers
