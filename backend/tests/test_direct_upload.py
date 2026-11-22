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

    async def ingest(d):
        d.status = "ready"
        d.page_count = 3
        return d

    monkeypatch.setattr(documents_route.supabase, "get_pdf_size", ok_size)
    monkeypatch.setattr(documents_route.supabase, "update_document_status", set_status)
    monkeypatch.setattr(documents_route.ingestion_service, "ingest_stored_document", ingest)

    res = client.post(f"/api/v1/documents/{doc.id}/ingest")
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "ready"


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
