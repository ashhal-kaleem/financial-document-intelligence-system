"""Direct-to-storage (serverless) upload flow: upload-url + ingest endpoints."""
import uuid

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.core.auth import AuthUser, get_current_user
from src.api.routes import documents as documents_route
from src.domain.models import Document

client = TestClient(app)
USER = AuthUser(id="11111111-1111-1111-1111-111111111111")


@pytest.fixture(autouse=True)
def signed_in():
    app.dependency_overrides[get_current_user] = lambda: USER
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def no_network_extras(monkeypatch):
    """Upload pre-checks (limits/sweeps) stay mocked; each test opts into the real paths."""
    async def zero(*a, **k):
        return 0
    monkeypatch.setattr(documents_route.supabase, "count_owner_documents", zero)
    monkeypatch.setattr(documents_route.supabase, "sweep_expired_guest_documents", zero)
    monkeypatch.setattr(documents_route.supabase, "fail_stale_inline", zero)


def make_doc(status="uploaded", owner=USER.id):
    return Document(id=uuid.uuid4(), filename="report.pdf", status=status, owner_id=owner)


def patch_doc(monkeypatch, doc):
    async def get_by_id(doc_id, owner_id):
        if doc and str(doc.id) == str(doc_id) and doc.owner_id == owner_id:
            return doc
        return None
    monkeypatch.setattr(documents_route.supabase, "get_document_by_id", get_by_id)


def test_upload_url_rejects_non_pdf():
    res = client.post("/api/v1/documents/upload-url", json={"filename": "notes.txt", "size": 100})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "invalid_pdf"


def test_upload_url_rejects_empty():
    res = client.post("/api/v1/documents/upload-url", json={"filename": "a.pdf", "size": 0})
    assert res.status_code == 422


def test_upload_url_rejects_oversize():
    res = client.post(
        "/api/v1/documents/upload-url",
        json={"filename": "big.pdf", "size": 26 * 1024 * 1024},
    )
    assert res.status_code == 422
    assert "25MB" in res.json()["error"]["message"]


def test_upload_url_success_owner_scoped(monkeypatch):
    created = {}

    async def create_document(doc):
        created["doc"] = doc
        return doc

    async def signed(doc_id, filename):
        return {"bucket": "documents", "path": f"{doc_id}/{filename}", "token": "tok123"}

    monkeypatch.setattr(documents_route.supabase, "create_document", create_document)
    monkeypatch.setattr(documents_route.supabase, "create_signed_upload_url", signed)

    res = client.post("/api/v1/documents/upload-url", json={"filename": "report.pdf", "size": 1024})
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["token"] == "tok123"
    assert data["path"].endswith("/report.pdf")
    assert data["document_id"] in data["path"]
    assert created["doc"].owner_id == USER.id
    assert created["doc"].status == "uploaded"


def test_ingest_unknown_document(monkeypatch):
    patch_doc(monkeypatch, None)
    res = client.post(f"/api/v1/documents/{uuid.uuid4()}/ingest")
    assert res.status_code == 404


def test_ingest_rejects_other_users_document(monkeypatch):
    patch_doc(monkeypatch, make_doc(owner="22222222-2222-2222-2222-222222222222"))
    res = client.post(f"/api/v1/documents/{uuid.uuid4()}/ingest")
    assert res.status_code == 404


def test_ingest_conflict_when_not_awaiting_upload(monkeypatch):
    doc = make_doc(status="ready")
    patch_doc(monkeypatch, doc)
    res = client.post(f"/api/v1/documents/{doc.id}/ingest")
    assert res.status_code == 409


def test_ingest_file_not_uploaded_yet(monkeypatch):
    doc = make_doc()
    patch_doc(monkeypatch, doc)

    async def no_size(doc_id, filename):
        return None

    monkeypatch.setattr(documents_route.supabase, "get_pdf_size", no_size)
    res = client.post(f"/api/v1/documents/{doc.id}/ingest")
    assert res.status_code == 422
    assert "not uploaded" in res.json()["error"]["message"].lower() or "not uploaded" in res.json().get("detail", "").lower()


def test_ingest_oversized_object_is_deleted_and_errored(monkeypatch):
    doc = make_doc()
    patch_doc(monkeypatch, doc)
    calls = {"deleted": [], "status": []}

    async def big_size(doc_id, filename):
        return 26 * 1024 * 1024

    async def delete_pdf(doc_id, filename):
        calls["deleted"].append((doc_id, filename))

    async def set_status(doc_id, st, **kw):
        calls["status"].append(st)
        return True

    monkeypatch.setattr(documents_route.supabase, "get_pdf_size", big_size)
    monkeypatch.setattr(documents_route.supabase, "delete_pdf", delete_pdf)
    monkeypatch.setattr(documents_route.supabase, "update_document_status", set_status)

    res = client.post(f"/api/v1/documents/{doc.id}/ingest")
    assert res.status_code == 422
    assert calls["deleted"], "oversized orphan object must be removed"
    assert "error" in calls["status"]


def test_ingest_success(monkeypatch):
    doc = make_doc()
    patch_doc(monkeypatch, doc)

    async def ok_size(doc_id, filename):
        return 1024

    async def set_status(doc_id, st, **kw):
        return True

    async def claim(doc_id, attempts):
        return True

    async def ingest(d):
        d.status = "ready"
        d.page_count = 3
        return d

    monkeypatch.setattr(documents_route.supabase, "get_pdf_size", ok_size)
    monkeypatch.setattr(documents_route.supabase, "update_document_status", set_status)
    monkeypatch.setattr(documents_route.supabase, "claim_inline_ingest", claim)
    monkeypatch.setattr(documents_route.ingestion_service, "ingest_stored_document", ingest)

    res = client.post(f"/api/v1/documents/{doc.id}/ingest")
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "ready"


def test_ingest_conflict_when_claim_lost(monkeypatch):
    """A concurrent ingest or sweep already took the row: no double processing."""
    doc = make_doc()
    patch_doc(monkeypatch, doc)

    async def ok_size(doc_id, filename):
        return 1024

    async def claim_lost(doc_id, attempts):
        return False

    async def forbidden_ingest(d):
        raise AssertionError("processing must not start when the claim is lost")

    monkeypatch.setattr(documents_route.supabase, "get_pdf_size", ok_size)
    monkeypatch.setattr(documents_route.supabase, "claim_inline_ingest", claim_lost)
    monkeypatch.setattr(documents_route.ingestion_service, "ingest_stored_document", forbidden_ingest)

    res = client.post(f"/api/v1/documents/{doc.id}/ingest")
    assert res.status_code == 409


def test_inline_sweep_skipped_in_queue_mode(monkeypatch):
    monkeypatch.setattr(documents_route, "effective_ingestion_mode", lambda *a, **k: "queue")

    async def forbidden(*a, **k):
        raise AssertionError("fail_stale_inline must not run in queue mode")

    async def none(*a, **k):
        return None

    monkeypatch.setattr(documents_route.supabase, "fail_stale_inline", forbidden)
    monkeypatch.setattr(documents_route.supabase, "get_document_by_id", none)
    res = client.get(f"/api/v1/documents/{uuid.uuid4()}")
    assert res.status_code == 404


def test_inline_sweep_failure_does_not_break_requests(monkeypatch):
    monkeypatch.setattr(documents_route, "effective_ingestion_mode", lambda *a, **k: "inline")

    async def broken(*a, **k):
        raise RuntimeError("db down")

    async def none(*a, **k):
        return None

    monkeypatch.setattr(documents_route.supabase, "fail_stale_inline", broken)
    monkeypatch.setattr(documents_route.supabase, "get_document_by_id", none)
    res = client.get(f"/api/v1/documents/{uuid.uuid4()}")
    assert res.status_code == 404


class _FakeResponse:
    def __init__(self, json_data=None, status=200, headers=None):
        self._json = json_data if json_data is not None else []
        self.status_code = status
        self.headers = headers or {}
        self.content = b""

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")


class _FakeAsyncClient:
    """Records REST calls and serves canned rows per request."""

    def __init__(self, rows_by_marker=None):
        self.calls = []
        self.rows_by_marker = rows_by_marker or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, url, headers=None):
        self.calls.append(("GET", url))
        for marker, rows in self.rows_by_marker.items():
            if marker in url:
                return _FakeResponse(rows)
        return _FakeResponse([])

    async def patch(self, url, headers=None, json=None):
        self.calls.append(("PATCH", url, json))
        return _FakeResponse([{"id": "x", "filename": "f.pdf"}])

    async def request(self, method, url, headers=None, json=None):
        self.calls.append((method, url, json))
        return _FakeResponse({"ok": True})

    async def delete(self, url, headers=None):
        self.calls.append(("DELETE", url))
        return _FakeResponse([{"id": "x", "filename": "f.pdf"}])


def test_claim_inline_ingest_is_conditional_and_sets_claimed_at(monkeypatch):
    import asyncio
    from src.infrastructure import supabase_client as sc

    fake = _FakeAsyncClient()
    monkeypatch.setattr(sc.httpx, "AsyncClient", lambda timeout: fake)
    client = sc.SupabaseClient()
    doc_id = uuid.uuid4()

    ok = asyncio.run(client.claim_inline_ingest(doc_id, 0))
    assert ok is True
    method, url, body = fake.calls[0]
    assert f"id=eq.{doc_id}" in url and "status=eq.uploaded" in url
    assert body["status"] == "processing" and body["attempts"] == 1
    assert body["claimed_at"]  # fresh claim timestamp is the sweep fence


def test_sweep_fences_processing_on_claim_time_not_document_age(monkeypatch):
    import asyncio
    from src.infrastructure import supabase_client as sc

    stale_row = {"id": str(uuid.uuid4()), "filename": "old.pdf"}
    abandoned_row = {"id": str(uuid.uuid4()), "filename": "abandoned.pdf"}
    fake = _FakeAsyncClient({"status=eq.processing": [stale_row], "status=eq.uploaded": [abandoned_row]})
    monkeypatch.setattr(sc.httpx, "AsyncClient", lambda timeout: fake)
    client = sc.SupabaseClient()

    swept = asyncio.run(client.fail_stale_inline(stale_seconds=600, abandon_seconds=21600))
    assert swept == 2

    get_urls = [u for m, u, *_ in (c for c in fake.calls if c[0] == "GET")]
    processing_filt = next(u for u in get_urls if "status=eq.processing" in u)
    uploaded_filt = next(u for u in get_urls if "status=eq.uploaded" in u)
    # Processing rows fence on claim time: a delayed ingest on an old document
    # refreshes claimed_at, so a live function can never match this filter.
    assert "claimed_at=lt." in processing_filt
    assert "created_at" not in processing_filt
    # Uploaded rows fence on creation age (no live function possible), with a
    # threshold beyond the signed URL lifetime, and are reclaimed (orphan object deleted).
    assert "created_at=lt." in uploaded_filt
    deletes = [c for c in fake.calls if c[0] == "DELETE"]
    assert len(deletes) == 2


def test_sweep_skips_recent_claims_and_recent_uploads(monkeypatch):
    import asyncio
    from src.infrastructure import supabase_client as sc

    # No canned rows -> both filters return nothing, nothing is touched.
    fake = _FakeAsyncClient()
    monkeypatch.setattr(sc.httpx, "AsyncClient", lambda timeout: fake)
    client = sc.SupabaseClient()

    swept = asyncio.run(client.fail_stale_inline(stale_seconds=600, abandon_seconds=21600))
    assert swept == 0
    assert [c for c in fake.calls if c[0] in ("PATCH", "DELETE")] == []


def test_delete_cross_user_returns_404_even_if_rpc_fails(monkeypatch):
    """Owner check happens before the delete RPC: foreign docs are 404, never 500."""
    patch_doc(monkeypatch, None)

    async def rpc_would_fail(doc_id, owner_id):
        raise AssertionError("delete RPC must not run for a non-owned document")

    monkeypatch.setattr(documents_route.supabase, "delete_document", rpc_would_fail)
    res = client.delete(f"/api/v1/documents/{uuid.uuid4()}")
    assert res.status_code == 404


def test_delete_owner_rpc_failure_still_surfaces(monkeypatch):
    """A real owner's delete failure is not hidden by the guard."""
    doc = make_doc(status="ready")
    patch_doc(monkeypatch, doc)

    async def rpc_fails(doc_id, owner_id):
        raise RuntimeError("rpc unavailable")

    monkeypatch.setattr(documents_route.supabase, "delete_document", rpc_fails)
    with pytest.raises(RuntimeError):
        client.delete(f"/api/v1/documents/{doc.id}")


def test_delete_abandoned_upload_cancels_in_code(monkeypatch):
    """An uploaded-but-never-ingested doc is deletable without the delete RPC."""
    doc = make_doc(status="uploaded")
    patch_doc(monkeypatch, doc)
    calls = {"cancel": 0}

    async def cancel(doc_id, owner_id):
        calls["cancel"] += 1
        assert owner_id == USER.id
        return True

    async def rpc_must_not_run(doc_id, owner_id):
        raise AssertionError("delete RPC refuses uploaded rows; must not be called")

    monkeypatch.setattr(documents_route.supabase, "cancel_uploaded_document", cancel)
    monkeypatch.setattr(documents_route.supabase, "delete_document", rpc_must_not_run)
    res = client.delete(f"/api/v1/documents/{doc.id}")
    assert res.status_code == 200
    assert calls["cancel"] == 1


def test_delete_upload_lost_to_concurrent_ingest_is_409(monkeypatch):
    doc = make_doc(status="uploaded")
    patch_doc(monkeypatch, doc)

    async def cancel_lost(doc_id, owner_id):
        return False

    monkeypatch.setattr(documents_route.supabase, "cancel_uploaded_document", cancel_lost)
    res = client.delete(f"/api/v1/documents/{doc.id}")
    assert res.status_code == 409


def test_delete_ready_doc_still_uses_rpc(monkeypatch):
    doc = make_doc(status="ready")
    patch_doc(monkeypatch, doc)
    calls = {"rpc": 0}

    async def rpc_delete(doc_id, owner_id):
        calls["rpc"] += 1
        return True

    async def cancel_must_not_run(doc_id, owner_id):
        raise AssertionError("cancel path is only for uploaded rows")

    monkeypatch.setattr(documents_route.supabase, "delete_document", rpc_delete)
    monkeypatch.setattr(documents_route.supabase, "cancel_uploaded_document", cancel_must_not_run)
    res = client.delete(f"/api/v1/documents/{doc.id}")
    assert res.status_code == 200
    assert calls["rpc"] == 1


def test_cancel_upload_is_conditional_and_keeps_fenced_marker_row(monkeypatch):
    import asyncio
    from src.infrastructure import supabase_client as sc

    fake = _FakeAsyncClient()
    monkeypatch.setattr(sc.httpx, "AsyncClient", lambda timeout: fake)
    client = sc.SupabaseClient()
    doc_id = uuid.uuid4()

    ok = asyncio.run(client.cancel_uploaded_document(doc_id, USER.id))
    assert ok is True
    method, url, body = fake.calls[0]
    assert method == "PATCH"  # row kept as tracking marker, not deleted
    assert f"id=eq.{doc_id}" in url
    assert f"owner_id=eq.{USER.id}" in url
    assert "status=eq.uploaded" in url  # fences a concurrent ingest claim
    assert body["status"] == "error"
    assert body["error_message"] == client.CANCELED_UPLOAD_MESSAGE
    # the current object is removed best-effort
    assert any(c[0] == "DELETE" for c in fake.calls)


def test_sweep_reclaims_canceled_rows_objects_after_grant_expiry(monkeypatch):
    import asyncio
    from src.infrastructure import supabase_client as sc

    canceled = {"id": str(uuid.uuid4()), "filename": "reput.pdf"}
    fake = _FakeAsyncClient({"status=eq.error": [canceled]})
    monkeypatch.setattr(sc.httpx, "AsyncClient", lambda timeout: fake)
    client = sc.SupabaseClient()

    swept = asyncio.run(client.fail_stale_inline(stale_seconds=600, abandon_seconds=21600))
    assert swept == 1
    get_urls = [u for m, u, *_ in (c for c in fake.calls if c[0] == "GET")]
    error_filt = next(u for u in get_urls if "status=eq.error" in u)
    assert "created_at=lt." in error_filt  # only after signed-grant expiry
    # the canceled row is NOT re-marked (no PATCH), only its object reclaimed
    assert [c for c in fake.calls if c[0] == "PATCH"] == []
    assert [c for c in fake.calls if c[0] == "DELETE"]
