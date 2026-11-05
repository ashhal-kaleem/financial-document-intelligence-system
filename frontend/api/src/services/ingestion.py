import asyncio
import io
import logging
from typing import List, Optional, Tuple
from uuid import UUID, uuid4
import pymupdf
from src.core.config import get_settings
from src.core.errors import InvalidPDFError
from src.domain.chunker import RecursiveFinancialChunker
from src.domain.models import Document, DocumentChunk
from src.infrastructure.embedding_client import get_embedding_client
from src.infrastructure.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class DocumentIngestionService:
    def __init__(self, supabase_client: SupabaseClient = None):
        self.settings = get_settings()
        self.supabase = supabase_client or SupabaseClient()
        self.embedding_client = get_embedding_client()
        self.chunker = RecursiveFinancialChunker(
            target_chunk_size=self.settings.CHUNK_SIZE,
            overlap=self.settings.CHUNK_OVERLAP,
        )

    def extract_pdf_content(self, pdf_bytes: bytes, filename: str) -> Tuple[int, List[Tuple[int, str, List[str]]]]:
        """
        Extracts text and structured tables per page.
        Guarantees doc.close() and store_shrink(100) memory cleanup.
        """
        doc = None
        pages_data = []
        try:
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            page_count = len(doc)
            if page_count == 0:
                raise InvalidPDFError("The PDF document contains 0 pages.")

            if page_count > self.settings.MAX_PDF_PAGES:
                raise InvalidPDFError(f"PDF has {page_count} pages; the limit is {self.settings.MAX_PDF_PAGES}.")

            for page_idx in range(page_count):
                page = doc[page_idx]
                page_num = page_idx + 1

                # 1. Extract plain text
                page_text = page.get_text("text")

                # 2. Extract tables natively if present
                page_tables = []
                try:
                    tabs = page.find_tables()
                    for tab in tabs:
                        df_rows = tab.extract()
                        if df_rows:
                            # Format as readable markdown table
                            header = " | ".join(str(cell or "").strip() for cell in df_rows[0])
                            separator = " | ".join(["---"] * len(df_rows[0]))
                            rows = [" | ".join(str(cell or "").strip() for cell in row) for row in df_rows[1:]]
                            table_md = f"| {header} |\n| {separator} |\n" + "\n".join(f"| {r} |" for r in rows)
                            page_tables.append(table_md)
                except Exception as e:
                    logger.debug(f"Table detection skipped on page {page_num}: {e}")

                pages_data.append((page_num, page_text, page_tables))
            return page_count, pages_data
        except Exception as e:
            if isinstance(e, InvalidPDFError):
                raise
            raise InvalidPDFError(f"Failed to parse PDF document '{filename}': {str(e)}")
        finally:
            if doc:
                doc.close()
            # Crucial invariant: release MuPDF internal cache
            pymupdf.TOOLS.store_shrink(100)

    async def enqueue_document(self, filename: str, pdf_bytes: bytes, owner_id: Optional[str] = None) -> Document:
        """Queue mode: store the PDF and a 'queued' row. A worker does the heavy work later.
        If the PDF cannot be stored the row is removed and the error propagates (nothing to retry from)."""
        doc = Document(id=uuid4(), filename=filename, status="queued", owner_id=owner_id)
        created = await self.supabase.create_document(doc)
        try:
            await self.supabase.upload_pdf(doc.id, filename, pdf_bytes)
        except Exception:
            await self.supabase.update_document_status(
                doc.id, "error", error_message="Could not store the uploaded file."
            )
            raise
        return created

    async def ingest_document(self, filename: str, pdf_bytes: bytes, owner_id: Optional[str] = None, is_sample: bool = False) -> Document:
        """Inline mode: create the row and process it inside the request."""
        doc = Document(id=uuid4(), filename=filename, status="processing", is_sample=is_sample, owner_id=owner_id)
        created_doc = await self.supabase.create_document(doc)
        try:
            await self.supabase.upload_pdf(doc.id, filename, pdf_bytes)
        except Exception as e:
            logger.warning(f"Could not upload PDF bytes to storage: {e}")
        return await self._process(created_doc, pdf_bytes)

    async def process_claimed(self, doc: Document) -> Document:
        """Worker entry: fetch the stored PDF for a claimed job and process it."""
        pdf_bytes = await self.supabase.get_pdf_bytes(doc.id, doc.filename)
        if not pdf_bytes:
            await self.supabase.update_document_status(
                doc.id, "error", error_message="Stored file not found."
            )
            doc.status = "error"
            return doc
        return await self._process(doc, pdf_bytes, raise_on_error=False)

    async def _process(self, doc: Document, pdf_bytes: bytes, raise_on_error: bool = True) -> Document:
        doc_id = doc.id
        filename = doc.filename
        try:
            # Parsing and embedding are blocking calls: keep them off the event loop.
            page_count, pages_data = await asyncio.to_thread(self.extract_pdf_content, pdf_bytes, filename)

            all_chunks: List[DocumentChunk] = []
            for page_num, page_text, page_tables in pages_data:
                all_chunks.extend(
                    self.chunker.chunk_page(
                        document_id=doc_id,
                        source=filename,
                        page_number=page_num,
                        page_text=page_text,
                        page_tables=page_tables,
                    )
                )
            for idx, c in enumerate(all_chunks):
                c.chunk_index = idx
                c.total_chunks = len(all_chunks)

            if all_chunks:
                embeddings = await asyncio.to_thread(
                    self.embedding_client.embed_texts, [c.content for c in all_chunks]
                )
                for c, emb in zip(all_chunks, embeddings):
                    c.embedding = emb
                # A retried job must not leave duplicate chunks behind.
                await self.supabase.delete_chunks(doc_id)
                await self.supabase.insert_chunks_batch(all_chunks)

            await self.supabase.update_document_status(
                document_id=doc_id, status="ready", page_count=page_count, chunk_count=len(all_chunks)
            )
            doc.status, doc.page_count, doc.chunk_count = "ready", page_count, len(all_chunks)
            return doc
        except Exception as exc:
            logger.error(f"Failed ingesting document {filename}: {exc}")
            message = (
                str(exc) if isinstance(exc, InvalidPDFError) else "Ingestion failed. Check the file and try again."
            )
            await self.supabase.update_document_status(document_id=doc_id, status="error", error_message=message)
            doc.status, doc.error_message = "error", message
            if raise_on_error:
                raise
            return doc
