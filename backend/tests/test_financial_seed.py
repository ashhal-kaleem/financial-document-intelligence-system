"""Seed integrity / extraction / evidence plumbing, NOT measured model answer quality."""
import json
from pathlib import Path
from uuid import uuid4
import pymupdf
import pytest
from src.domain.chunker import RecursiveFinancialChunker
from src.domain.citation import create_citations_from_chunks
from src.services.ingestion import DocumentIngestionService
from src.services.inference import InferenceService
CASES=json.loads((Path(__file__).parent/'fixtures/financial_seed.json').read_text())

@pytest.mark.parametrize('case',CASES,ids=lambda c:c['id'])
def test_financial_seed_preserves_text_page_and_evidence(case):
    if not case['passage']:
        assert case['expected_fact'] is None
        return
    # Generated digital PDFs are synthetic data, no external reports or provider calls.
    pdf=pymupdf.open();page=pdf.new_page();page.insert_textbox(pymupdf.Rect(40,40,550,700),case['passage'],fontsize=12)
    data=pdf.tobytes();pdf.close()
    count,pages=DocumentIngestionService().extract_pdf_content(data,case['filename'])
    text=pages[0][1]
    assert count==1 and case['passage'].split()[0] in text
    chunks=RecursiveFinancialChunker().chunk_page(uuid4(),case['filename'],case['page'],text)
    for index,c in enumerate(chunks):c.chunk_index=index;c.total_chunks=len(chunks)
    citations=create_citations_from_chunks(chunks)
    assert citations and all(c.page==case['page'] and c.filename==case['filename'] for c in citations)
    prompt=InferenceService().build_rag_prompt(case['question'],chunks,citations)
    assert case['question'] in prompt[-1]['content']
    if case['expected_fact']:assert case['expected_fact'] in text

def test_seed_has_required_distinct_categories_and_explicit_review_status():
    assert len(CASES)>=30 and len({c['id'] for c in CASES})==len(CASES)
    assert {'currency-scale-year','basis','negative','missing-fact','hostile-passage','hostile-link','hostile-filename','hinglish','no-context'} <= {c['tag'] for c in CASES}
    assert all('not independently labeled' in c['review_status'] for c in CASES)
