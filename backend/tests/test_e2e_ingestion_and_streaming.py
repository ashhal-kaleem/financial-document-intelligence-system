import pytest
from src.services.ingestion import DocumentIngestionService
from src.services.inference import InferenceService
from src.infrastructure.supabase_client import SupabaseClient


@pytest.mark.asyncio
async def test_live_ingestion_and_streaming_roundtrip():
    supabase = SupabaseClient()
    ingestion_service = DocumentIngestionService(supabase)
    inference_service = InferenceService()

    with open("tests/sample_apple_10k.pdf", "rb") as f:
        pdf_bytes = f.read()

    # 1. Ingest document
    doc = await ingestion_service.ingest_document(
        filename="sample_apple_10k.pdf",
        pdf_bytes=pdf_bytes,
        is_sample=True,
    )

    assert doc.status == "ready"
    assert doc.page_count == 2
    assert doc.chunk_count > 0

    try:
        # 2. Query grounded financial information
        question = "What was Apple's total net sales and operating income in fiscal 2024?"
        events = []
        async for event in inference_service.stream_answer(
            question=question,
            document_ids=[doc.id],
        ):
            events.append(event)

        # Verify event stream structure
        event_types = [e["event"] for e in events]
        assert "stage" in event_types
        assert "citations" in event_types
        assert "token" in event_types
        assert "done" in event_types

        # Verify citations
        citations_event = next(e for e in events if e["event"] == "citations")
        assert len(citations_event["citations"]) > 0
        assert citations_event["citations"][0]["filename"] == "sample_apple_10k.pdf"

        # Verify generated answer contains factual numbers
        tokens = [e["token"] for e in events if e["event"] == "token"]
        full_answer = "".join(tokens)
        print("\n--- Model Streamed Answer ---")
        print(full_answer)
        print("-----------------------------\n")
        assert "391,035" in full_answer or "391" in full_answer

        # 3. Test Zero-Hallucination on undisclosed fact
        undisclosed_q = "What is the CEO's personal home address?"
        undisclosed_events = []
        async for event in inference_service.stream_answer(
            question=undisclosed_q,
            document_ids=[doc.id],
        ):
            undisclosed_events.append(event)

        undisclosed_tokens = [e["token"] for e in undisclosed_events if e["event"] == "token"]
        undisclosed_answer = "".join(undisclosed_tokens)
        print("--- Undisclosed Query Response ---")
        print(undisclosed_answer)
        print("----------------------------------\n")
        assert "not disclose" in undisclosed_answer.lower() or "not contain" in undisclosed_answer.lower() or "not mentioned" in undisclosed_answer.lower()

    finally:
        # Cleanup test document from database
        await supabase.delete_document(doc.id)
