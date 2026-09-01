"""Loader for PDF files using pypdf."""

from __future__ import annotations

import re
from pathlib import Path

from financial_rag.ingestion.base import BaseLoader
from financial_rag.ingestion.models import Document

# ---------------------------------------------------------------------------
# Boilerplate removal — strips repetitive PDF header/footer lines that pollute
# BM25 retrieval without adding any financial information.
# Conservative patterns only: pure page numbers, bare annual-report title
# lines, and bare bank-name lines.
# ---------------------------------------------------------------------------
_RE_PAGE_NUM   = re.compile(r'^\d{1,3}$')
_RE_AR_TITLE   = re.compile(
    r'^(?:.*?\s+)?Annual\s+Report\s+20\d{2}$',
    re.IGNORECASE,
)
_RE_FILENAME   = re.compile(
    r'^.*_Annual_Report_\d{4}(?:\.pdf)?$',
    re.IGNORECASE,
)


def _clean_page_text(text: str) -> str:
    """Remove repetitive PDF header/footer boilerplate lines."""
    cleaned: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if _RE_PAGE_NUM.match(s):
            continue
        if _RE_AR_TITLE.match(s):
            continue
        if _RE_FILENAME.match(s):
            continue
        cleaned.append(line)
    return '\n'.join(cleaned).strip()


class PDFLoader(BaseLoader):
    """Loads a PDF file, producing one Document per page.

    One-document-per-page is a deliberate choice: it preserves page-level
    provenance so citations can reference exact page numbers, and it keeps
    individual documents small enough for chunking to work predictably.
    """

    def load(self) -> list[Document]:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ImportError("Install pypdf: pip install pypdf") from exc

        reader = PdfReader(str(self.path))
        documents: list[Document] = []

        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text = _clean_page_text(text)

            if not text:
                # Scanned page or image-only — skip with a warning
                print(f"  [warning] Page {page_num + 1} of {self.path.name} has no extractable text (may be scanned).")
                continue

            documents.append(
                Document(
                    content=text,
                    source=self.path.name,
                    page=page_num,
                    metadata={
                        "filename": self.path.name,
                        "extension": ".pdf",
                        "total_pages": len(reader.pages),
                        "size_bytes": self.path.stat().st_size,
                    },
                )
            )

        if not documents:
            raise ValueError(
                f"No extractable text found in {self.path.name}. "
                "The PDF may be scanned. Consider an OCR pre-processing step."
            )

        return documents
