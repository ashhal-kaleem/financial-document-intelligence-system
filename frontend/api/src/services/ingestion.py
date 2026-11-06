import asyncio
from contextlib import suppress
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

HEARTBEAT_SECONDS = 60


class LostLeaseError(Exception):
    """Another worker claimed this job (our lease expired). Stop without writing anything."""


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
            if doc.needs_pass:
                raise InvalidPDFError("Password-protected PDFs are not supported.")
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
                    logger.debug("Table detection skipped on page %s", page_num)

                pages_data.append((page_num, page_text, page_tables))
            if not any(text.strip() or tables for _, text, tables in pages_data):
                raise InvalidPDFError("No readable text found. Scanned PDFs need OCR, which is not supported yet.")
            return page_count, pages_data
        except Exception as e:
            if isinstance(e, InvalidPDFError):
                raise
            raise InvalidPDFError("The PDF could not be parsed. Check that it is valid and not encrypted.") from None
        finally:
            if doc:
                doc.close()
            # Crucial invariant: release MuPDF internal cache
            pymupdf.TOOLS.store_shrink(100)

    async def enqueue_document(self, filename: str, pdf_bytes: bytes, owner_id: Optional[str] = None) -> Document:
        """Queue mode: store the PDF and a 'queued' row. A worker does the heavy work later.
        If storage fails the row becomes error and cannot be claimed."""
        doc = Document(id=uuid4(), filename=filename, status="uploaded", owner_id=owner_id)
        created = await self.supabase.create_document(doc)
        try:
            await self.supabase.upload_pdf(doc.id, filename, pdf_bytes)
        except Exception:
            await self.supabase.update_document_status(
                doc.id, "error", error_message="Could not store the uploaded file."
            )
            raise
        await self.supabase.update_document_status(doc.id, "queued")
        created.status = "queued"
        return created

    async def ingest_document(self, filename: str, pdf_bytes: bytes, owner_id: Optional[str] = None, is_sample: bool = False) -> Document:
        """Inline mode: create the row and process it inside the request."""
        doc = Document(id=uuid4(), filename=filename, status="processing", is_sample=is_sample, owner_id=owner_id)
        created_doc = await self.supabase.create_document(doc)
        try:
            await self.supabase.upload_pdf(doc.id, filename, pdf_bytes)
        except Exception:
            await self.supabase.update_document_status(doc.id, "error", error_message="Could not store the uploaded file.")
            raise RuntimeError("Could not store the uploaded file") from None
        return await self._process(created_doc, pdf_bytes)

    async def process_claimed(self, doc: Document) -> Document:
        """Worker entry: fetch the stored PDF for a claimed job and process it."""
        pdf_bytes = await self.supabase.get_pdf_bytes(doc.id, doc.filename)
        if not pdf_bytes:
            if doc.attempts is not None:
                await self.supabase.finish_document(doc.id, doc.attempts, "error", "Stored file not found.")
            else:
                await self.supabase.update_document_status(doc.id, "error", error_message="Stored file not found.")
            doc.status = "error"
            return doc
        return await self._process(doc, pdf_bytes, raise_on_error=False, attempt=doc.attempts)

    async def _heartbeat(self, doc_id: UUID, attempt: int) -> None:
        while True:
            await asyncio.sleep(HEARTBEAT_SECONDS)
            try:
                if not await self.supabase.heartbeat_document(doc_id, attempt):
                    return  # lease lost; the next fenced write will stop the job
            except Exception:
                logger.warning("Heartbeat failed for %s", doc_id)

    async def _process(self, doc: Document, pdf_bytes: bytes, raise_on_error: bool = True,
                       attempt: Optional[int] = None) -> Document:
        """attempt is the queue fencing token; None means inline mode (no queue, no fencing)."""
        beat = asyncio.create_task(self._heartbeat(doc.id, attempt)) if attempt is not None else None
        try:
            return await self._process_inner(doc, pdf_bytes, raise_on_error, attempt)
        finally:
            if beat:
                beat.cancel()
                with suppress(asyncio.CancelledError):
                    await beat

    async def _process_inner(self, doc: Document, pdf_bytes: bytes, raise_on_error: bool,
                             attempt: Optional[int]) -> Document:
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
                if len(embeddings) != len(all_chunks):
                    raise RuntimeError("Embedding batch size mismatch")
                for c, emb in zip(all_chunks, embeddings):
                    c.embedding = emb
                if attempt is None:
                    await self.supabase.delete_chunks(doc_id)
                    await self.supabase.insert_chunks_batch(all_chunks)
                else:
                    # Fenced: rejected if another worker has claimed the job since we did.
                    if not await self.supabase.clear_chunks_fenced(doc_id, attempt):
                        raise LostLeaseError()
                    if not await self.supabase.insert_chunks_fenced(doc_id, attempt, all_chunks):
                        raise LostLeaseError()

            if attempt is None:
                await self.supabase.update_document_status(
                    document_id=doc_id, status="ready", page_count=page_count, chunk_count=len(all_chunks)
                )
            elif not await self.supabase.finish_document(doc_id, attempt, "ready", None, page_count, len(all_chunks)):
                raise LostLeaseError()
            doc.status, doc.page_count, doc.chunk_count = "ready", page_count, len(all_chunks)
            return doc
        except LostLeaseError:
            logger.warning("Lost lease on document %s; another worker owns it now", doc_id)
            return doc
        except Exception as exc:
            logger.error("Document ingestion failed (%s)", type(exc).__name__)
            message = (
                str(exc) if isinstance(exc, InvalidPDFError) else "Ingestion failed. Check the file and try again."
            )
            if attempt is None:
                await self.supabase.update_document_status(document_id=doc_id, status="error", error_message=message)
            else:
                await self.supabase.finish_document(doc_id, attempt, "error", message)  # no-op if lease lost
            doc.status, doc.error_message = "error", message
            if raise_on_error:
                raise
            return doc
