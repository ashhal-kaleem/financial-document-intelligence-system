from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

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
