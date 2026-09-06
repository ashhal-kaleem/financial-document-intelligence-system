import io
import logging
from typing import List, Tuple
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

    async def ingest_document(self, filename: str, pdf_bytes: bytes, is_sample: bool = False) -> Document:
        doc_id = uuid4()
        doc = Document(
            id=doc_id,
            filename=filename,
            status="processing",
            is_sample=is_sample,
        )

        # 1. Create document entry in database
        created_doc = await self.supabase.create_document(doc)

        try:
            # 2. Extract text & tables
            page_count, pages_data = self.extract_pdf_content(pdf_bytes, filename)

            # 3. Recursive chunking
            all_chunks: List[DocumentChunk] = []
            for page_num, page_text, page_tables in pages_data:
                chunks = self.chunker.chunk_page(
                    document_id=doc_id,
                    source=filename,
                    page_number=page_num,
                    page_text=page_text,
                    page_tables=page_tables,
                )
                all_chunks.extend(chunks)

            # Update total_chunks count across document
            for idx, c in enumerate(all_chunks):
                c.chunk_index = idx
                c.total_chunks = len(all_chunks)

            # 4. Generate embeddings in batch
            if all_chunks:
                texts = [c.content for c in all_chunks]
                embeddings = self.embedding_client.embed_texts(texts)
                for c, emb in zip(all_chunks, embeddings):
                    c.embedding = emb

                # 5. Persist chunks to pgvector
                await self.supabase.insert_chunks_batch(all_chunks)

            # 6. Update document status to ready
            await self.supabase.update_document_status(
                document_id=doc_id,
                status="ready",
                page_count=page_count,
                chunk_count=len(all_chunks),
            )
            created_doc.status = "ready"
            created_doc.page_count = page_count
            created_doc.chunk_count = len(all_chunks)
            return created_doc

        except Exception as exc:
            logger.error(f"Failed ingesting document {filename}: {exc}")
            await self.supabase.update_document_status(
                document_id=doc_id,
                status="error",
                error_message=str(exc),
            )
            created_doc.status = "error"
            created_doc.error_message = str(exc)
            raise
