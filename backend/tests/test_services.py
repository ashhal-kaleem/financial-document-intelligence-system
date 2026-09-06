import pytest
import pymupdf
from uuid import uuid4
from src.domain.models import DocumentChunk
from src.services.ingestion import DocumentIngestionService
from src.services.inference import InferenceService


def create_sample_financial_pdf_bytes() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "APPLE INC. CONSOLIDATED STATEMENTS OF OPERATIONS\n"
        "Total net sales for fiscal 2024 were $391,035 million.\n"
        "Gross margin was $180,683 million.\n"
        "Operating income was $123,216 million.",
        fontsize=12,
    )
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_document_ingestion_service_extract_pdf():
    pdf_bytes = create_sample_financial_pdf_bytes()
    service = DocumentIngestionService(supabase_client=None)
    page_count, pages_data = service.extract_pdf_content(pdf_bytes, "test_report.pdf")

    assert page_count == 1
    assert len(pages_data) == 1
    page_num, text, tables = pages_data[0]
    assert page_num == 1
    assert "APPLE INC. CONSOLIDATED STATEMENTS" in text
    assert "$391,035 million" in text


def test_inference_service_rag_prompt_construction():
    service = InferenceService()
    doc_id = uuid4()
    chunks = [
        DocumentChunk(
            document_id=doc_id,
            content="Gross margin was $180,683 million in fiscal 2024.",
            source="apple_10k.pdf",
            page=32,
            chunk_index=1,
            total_chunks=5,
            similarity=0.88,
        )
    ]
    citations = service.retrieval.build_citations(chunks)
    messages = service.build_rag_prompt("What was gross margin?", chunks, citations)

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "ZERO-HALLUCINATION RULES" in messages[0]["content"]
    assert "[1] Document: apple_10k.pdf, Page: 32" in messages[1]["content"]
    assert "$180,683 million" in messages[1]["content"]
