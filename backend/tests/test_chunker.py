from uuid import uuid4
from src.domain.chunker import RecursiveFinancialChunker
from src.domain.citation import create_citations_from_chunks, format_citation_string
from src.domain.models import DocumentChunk


def test_recursive_financial_chunker_basic():
    chunker = RecursiveFinancialChunker(target_chunk_size=200, overlap=30)
    doc_id = uuid4()
    sample_text = (
        "Consolidated Statements of Operations for Apple Inc. "
        "Total net sales for the fiscal year ended September 28, 2024 were $391,035 million, "
        "compared to $383,285 million for the fiscal year ended September 30, 2023. "
        "Total cost of sales was $210,352 million and $214,137 million respectively. "
        "Operating income reached $123,216 million, representing an operating margin of 31.5%."
    )

    chunks = chunker.chunk_page(
        document_id=doc_id,
        source="apple_10k_2024.pdf",
        page_number=32,
        page_text=sample_text,
    )

    assert len(chunks) >= 1
    assert chunks[0].document_id == doc_id
    assert chunks[0].source == "apple_10k_2024.pdf"
    assert chunks[0].page == 32
    assert "Consolidated Statements of Operations" in chunks[0].content


def test_chunker_with_tables():
    chunker = RecursiveFinancialChunker(target_chunk_size=300, overlap=40)
    doc_id = uuid4()
    table_content = "| Metric | 2024 | 2023 |\n| Revenue | $391,035M | $383,285M |\n| Net Income | $93,736M | $96,995M |"
    narrative_text = "Management notes that service revenues grew 13% year over year to a new all-time high."

    chunks = chunker.chunk_page(
        document_id=doc_id,
        source="apple_10k_2024.pdf",
        page_number=33,
        page_text=narrative_text,
        page_tables=[table_content],
    )

    assert len(chunks) >= 1
    assert any("Table on Page 33" in c.content for c in chunks)
    assert any("service revenues grew 13%" in c.content for c in chunks)


def test_citations_formatting():
    doc_id = uuid4()
    chunks = [
        DocumentChunk(
            document_id=doc_id,
            content="Total net sales were $391,035 million in fiscal year 2024.",
            source="apple_10k_2024.pdf",
            page=32,
            chunk_index=0,
            total_chunks=3,
            similarity=0.8845,
        ),
        DocumentChunk(
            document_id=doc_id,
            content="Operating margin increased to 31.5% driven by services expansion.",
            source="apple_10k_2024.pdf",
            page=35,
            chunk_index=2,
            total_chunks=3,
            similarity=0.7912,
        ),
    ]

    citations = create_citations_from_chunks(chunks)
    assert len(citations) == 2
    assert citations[0].citation_id == 1
    assert citations[0].similarity == 0.8845
    formatted = format_citation_string(citations[0])
    assert formatted == "[1] apple_10k_2024.pdf, p.32 (chunk 1/3)"
