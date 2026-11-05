import pytest
from fastapi.testclient import TestClient
from src.api.main import app

from src.core.auth import AuthUser, get_current_user
from src.api.routes import documents as documents_route

client = TestClient(app)
USER = AuthUser(id="11111111-1111-1111-1111-111111111111")


@pytest.fixture(autouse=True)
def signed_in():
    """Most tests run as a signed-in user; security tests clear the override."""
    app.dependency_overrides[get_current_user] = lambda: USER
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def no_db(monkeypatch):
    async def none(*a, **k):
        return None
    monkeypatch.setattr(documents_route.supabase, "get_document_by_id", none)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "version" in data

def test_reject_non_pdf_upload():
    response = client.post(
        "/api/v1/documents",
        files={"file": ("report.txt", b"plain text report", "text/plain")},
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "invalid_pdf"
    assert "Only PDF documents are supported" in data["error"]["message"]

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Financial Document Intelligence System" in data["data"]["service"]

def test_document_chunks_not_found():
    import uuid
    random_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/documents/{random_id}/chunks")
    assert response.status_code == 404

def test_document_pdf_not_found():
    import uuid
    random_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/documents/{random_id}/pdf")
    assert response.status_code == 404
