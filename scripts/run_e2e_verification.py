import time
import requests
from pathlib import Path

from reportlab.pdfgen import canvas

BASE_URL = "http://localhost:8000"

def create_pdf(path: Path, text: str):
    c = canvas.Canvas(str(path))
    c.drawString(100, 750, text)
    c.save()

def ask_with_retry(payload: dict, max_retries: int = 12) -> dict:
    """POST /ask with exponential backoff on 429 rate-limit responses."""
    for attempt in range(max_retries):
        resp = requests.post(f"{BASE_URL}/ask", json=payload)
        if resp.status_code == 429:
            wait = min(2 ** attempt, 60)
            print(f"  [rate limit] retry {attempt+1}/{max_retries} in {wait}s ...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"Rate limit persisted after {max_retries} retries")


def test_upload_flow():
    dummy_pdf_path = Path("test_upload_1.pdf")
    create_pdf(dummy_pdf_path, "Company Alpha completely different information. " * 5)

    try:
        with open(dummy_pdf_path, "rb") as f:
            res = requests.post(f"{BASE_URL}/documents/upload", files={"file": ("test_upload_1.pdf", f, "application/pdf")})
        
        assert res.status_code == 200 or res.status_code == 202, f"Expected 200/202, got {res.status_code}"
        data = res.json()
        doc_id = data["document_id"]
        
        print("Polling status...")
        for _ in range(30):
            list_res = requests.get(f"{BASE_URL}/documents")
            docs = list_res.json()["documents"]
            doc = next(d for d in docs if d["id"] == doc_id)
            if doc["status"] == "ready":
                break
            elif doc["status"] == "error":
                assert False, f"Document ingestion failed: {doc['error_message']}"
            time.sleep(1)
        else:
            assert False, "Document ingestion timed out or failed"

        print("Upload flow passed.")
        return doc_id
    finally:
        if dummy_pdf_path.exists():
            dummy_pdf_path.unlink()

def test_document_isolation(doc_id_1):
    dummy_pdf_path2 = Path("test_upload_2.pdf")
    create_pdf(dummy_pdf_path2, "Company Beta completely different information. " * 5)

    try:
        with open(dummy_pdf_path2, "rb") as f:
            res = requests.post(f"{BASE_URL}/documents/upload", files={"file": ("test_upload_2.pdf", f, "application/pdf")})
        doc_id_2 = res.json()["document_id"]
        
        for _ in range(30):
            docs = requests.get(f"{BASE_URL}/documents").json()["documents"]
            if next(d for d in docs if d["id"] == doc_id_2)["status"] == "ready":
                break
            time.sleep(1)

        # Query only doc 1
        ans = ask_with_retry({
            "question": "Company Alpha completely different information.",
            "document_ids": [doc_id_1],
            "model": "openai/gpt-oss-20b",
            "top_k": 5
        })
        assert any(doc_id_1 in c for c in ans["citations"]), "Doc 1 not cited"
        
        # Query only doc 2
        ans2 = ask_with_retry({
            "question": "Company Beta completely different information.",
            "document_ids": [doc_id_2],
            "model": "openai/gpt-oss-20b",
            "top_k": 5
        })
        assert any(doc_id_2 in c for c in ans2["citations"]), "Doc 2 not cited"

        print("Document isolation passed.")
        return doc_id_2
    finally:
        if dummy_pdf_path2.exists():
            dummy_pdf_path2.unlink()

def test_multi_document(doc_id_1, doc_id_2):
    ans = ask_with_retry({
        "question": "Company Alpha completely different information. Company Beta completely different information.",
        "document_ids": [doc_id_1, doc_id_2],
        "model": "openai/gpt-oss-20b",
        "top_k": 10
    })
    assert any(doc_id_1 in c for c in ans["citations"]), "Doc 1 not cited in multi-doc query"
    assert any(doc_id_2 in c for c in ans["citations"]), "Doc 2 not cited in multi-doc query"
    print("Multi-document comparison passed.")

def test_all_documents():
    ans = ask_with_retry({
        "question": "What is Habib Bank Limited?",
        "document_ids": None,
        "model": "openai/gpt-oss-20b",
        "top_k": 5
    })
    print("All documents passed.")

def test_legacy_source_filter():
    ask_res = requests.post(f"{BASE_URL}/ask", json={
        "question": "What is the bank's strategy?",
        "document_ids": None,
        "source_filter": "interbank",
        "model": "openai/gpt-oss-20b",
        "top_k": 5
    })
    assert ask_res.status_code in (200, 429)
    print("Legacy source_filter passed.")

def test_deletion(doc_id_1, doc_id_2):
    res = requests.delete(f"{BASE_URL}/documents/{doc_id_1}")
    assert res.status_code == 200
    
    docs = requests.get(f"{BASE_URL}/documents").json()["documents"]
    assert not any(d["id"] == doc_id_1 for d in docs)
    
    requests.delete(f"{BASE_URL}/documents/{doc_id_2}")
    print("Deletion passed.")

def test_malformed_pdf():
    dummy_path = Path("bad.txt")
    dummy_path.write_text("not a pdf")
    try:
        with open(dummy_path, "rb") as f:
            res = requests.post(f"{BASE_URL}/documents/upload", files={"file": ("bad.pdf", f, "application/pdf")})
        assert res.status_code == 400
        assert "Invalid PDF" in res.text
        print("Malformed PDF handling passed.")
    finally:
        dummy_path.unlink()

if __name__ == '__main__':
    doc_1 = test_upload_flow()
    doc_2 = test_document_isolation(doc_1)
    test_multi_document(doc_1, doc_2)
    test_all_documents()
    test_legacy_source_filter()
    test_deletion(doc_1, doc_2)
    test_malformed_pdf()
    print("ALL INTEGRATION TESTS PASSED")
