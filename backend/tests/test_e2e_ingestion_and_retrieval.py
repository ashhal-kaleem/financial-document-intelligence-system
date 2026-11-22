import pytest
from src.services.ingestion import DocumentIngestionService
from src.services.inference import InferenceService
from src.infrastructure.supabase_client import SupabaseClient

TEST_OWNER = "00000000-0000-0000-0000-0000000000aa"

pytestmark = pytest.mark.live  # needs real Supabase/HF keys; skipped unless RUN_LIVE_TESTS=1


@pytest.mark.asyncio
async def test_live_ingestion_and_retrieval_roundtrip():
    supabase = SupabaseClient()
    ingestion_service = DocumentIngestionService(supabase)
    inference_service = InferenceService()

    with open("tests/sample_apple_10k.pdf", "rb") as f:
        pdf_bytes = f.read()

    # 1. Ingest document
    doc = await ingestion_service.ingest_document(
        filename="sample_apple_10k.pdf",
        pdf_bytes=pdf_bytes,
        owner_id=TEST_OWNER,
    )

    assert doc.status == "ready"
    assert doc.page_count == 2
    assert doc.chunk_count > 0

    try:
        # 2. Retrieve grounded context for a financial question (answers are produced by the browser AI flow)
        question = "What was Apple's total net sales and operating income in fiscal 2024?"
        chunks = await inference_service.retrieval.retrieve_relevant_chunks(
            query=question,
            document_ids=[doc.id],
            owner_id=TEST_OWNER,
        )
        citations = inference_service.retrieval.build_citations(chunks)

        assert len(chunks) > 0
        assert len(citations) > 0
        assert citations[0].filename == "sample_apple_10k.pdf"

        # 3. Prompt assembly embeds the retrieved passages for the browser model
        messages = inference_service.build_rag_prompt(question, chunks, citations)
        assert messages[0]["role"] == "system"
        assert "CONTEXT PASSAGES" in messages[-1]["content"]
        assert any(c.content in messages[-1]["content"] for c in chunks)
    finally:
        # Cleanup test document from database
        await supabase.delete_document(doc.id, TEST_OWNER)
