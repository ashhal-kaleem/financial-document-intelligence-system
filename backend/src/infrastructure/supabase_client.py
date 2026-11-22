import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID
import httpx
from src.core.config import get_settings
from src.domain.models import Document, DocumentChunk
from src.infrastructure.interfaces import BaseVectorStore
from src.infrastructure.embedding_assets import PROFILE
from src.core.errors import FDISException

logger = logging.getLogger(__name__)


class SupabaseClient(BaseVectorStore):
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.SUPABASE_URL.rstrip("/")
        self.service_key = self.settings.SUPABASE_SERVICE_ROLE_KEY
        self.bucket = self.settings.SUPABASE_STORAGE_BUCKET
        self.headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    async def create_document(self, doc: Document) -> Document:
        async with httpx.AsyncClient(timeout=15.0) as client:
            payload = {
                "id": str(doc.id),
                "filename": doc.filename,
                "page_count": doc.page_count,
                "chunk_count": doc.chunk_count,
                "status": doc.status,
                "is_sample": doc.is_sample,
                "owner_id": doc.owner_id,
                "created_at": doc.created_at.isoformat(),
            }
            if doc.session_expires_at is not None:
                payload["session_expires_at"] = doc.session_expires_at.isoformat()
            res = await client.post(
                f"{self.base_url}/rest/v1/documents",
                headers=self.headers,
                json=payload,
            )
            res.raise_for_status()
            data = res.json()
            if data:
                return Document(**data[0])
            return doc

    async def update_document_status(
        self,
        document_id: UUID,
        status: str,
        error_message: Optional[str] = None,
        page_count: Optional[int] = None,
        chunk_count: Optional[int] = None,
    ) -> bool:
        async with httpx.AsyncClient(timeout=15.0) as client:
            payload: Dict[str, Any] = {"status": status}
            if error_message is not None:
                payload["error_message"] = error_message
            if page_count is not None:
                payload["page_count"] = page_count
            if chunk_count is not None:
                payload["chunk_count"] = chunk_count

            res = await client.patch(
                f"{self.base_url}/rest/v1/documents?id=eq.{document_id}",
                headers=self.headers,
                json=payload,
            )
            res.raise_for_status()
            return True

    @staticmethod
    def _visible_filter(owner_id: str) -> str:
        """PostgREST filter: non-sample documents owned by this user only."""
        return f"owner_id=eq.{owner_id}&is_sample=eq.false"

    async def get_documents(self, owner_id: str) -> List[Document]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(
                f"{self.base_url}/rest/v1/documents?order=created_at.desc&{self._visible_filter(owner_id)}",
                headers=self.headers,
            )
            res.raise_for_status()
            data = res.json()
            return [Document(**item) for item in data]

    async def get_document_by_id(self, doc_id: UUID, owner_id: str) -> Optional[Document]:
        """Returns the document only if the user owns it and it is not a sample."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(
                f"{self.base_url}/rest/v1/documents?id=eq.{doc_id}&status=neq.deleting&{self._visible_filter(owner_id)}",
                headers=self.headers,
            )
            res.raise_for_status()
            data = res.json()
            if data:
                return Document(**data[0])
            return None

    CANCELED_UPLOAD_MESSAGE = "Upload canceled."

    async def cancel_uploaded_document(self, doc_id: UUID, owner_id: str) -> bool:
        """Cancel an upload that never started processing (status 'uploaded').

        Code-only path: begin_document_delete refuses uploaded rows as busy, so
        without this an abandoned direct-to-storage upload could never be
        removed. The row is NOT deleted: it flips to a fenced 'error' marker
        (conditional on status=eq.uploaded, so a concurrent ingest claim gets
        no match and the caller gets a conflict instead of a race). Keeping the
        row keeps the object tracked: a browser still holding the signed URL
        (valid up to 2h) can re-PUT the object after cancellation, and the
        inline sweep reclaims canceled rows' objects once the grant is expired
        (abandon threshold 6h > grant lifetime). While the row exists, ingest
        can never pick the object up (409 for non-uploaded rows).
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.patch(
                f"{self.base_url}/rest/v1/documents?id=eq.{doc_id}&owner_id=eq.{owner_id}&status=eq.uploaded",
                headers={**self.headers, "Prefer": "return=representation"},
                json={"status": "error", "error_message": self.CANCELED_UPLOAD_MESSAGE},
            )
            res.raise_for_status()
            rows = res.json()
        if not rows:
            return False
        try:
            await self.delete_pdf(doc_id, rows[0]["filename"])
        except Exception:
            pass
        return True

    async def delete_document(self, doc_id: UUID, owner_id: str) -> bool:
        """Deletes only a document owned by the user (shared samples are never deletable)."""
        from src.core.errors import FDISException
        async with httpx.AsyncClient(timeout=30.0) as client:
            begin = await client.post(
                f"{self.base_url}/rest/v1/rpc/begin_document_delete",
                headers=self.headers, json={"p_id": str(doc_id), "p_owner": owner_id},
            )
            if begin.status_code == 400 and begin.json().get("code") == "55000":
                raise FDISException("Document is busy", "Wait for processing to finish before deleting.", 409, "document_busy")
            begin.raise_for_status()
            rows = begin.json()
            if not rows:
                return False
            # Keep the deleting row until Storage confirms removal. Retry is safe after either failure.
            path = f"{doc_id}/{rows[0]['filename']}"
            removed = await client.request(
                "DELETE", f"{self.base_url}/storage/v1/object/{self.bucket}",
                headers=self.headers, json={"prefixes": [path]},
            )
            removed.raise_for_status()
            # FK cascade clears chunks atomically with the final document removal.
            res = await client.delete(
                f"{self.base_url}/rest/v1/documents?id=eq.{doc_id}&owner_id=eq.{owner_id}&status=eq.deleting",
                headers=self.headers,
            )
            res.raise_for_status()
            return True

    async def get_visible_document_ids(self, owner_id: str) -> List[UUID]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(
                f"{self.base_url}/rest/v1/documents?select=id&status=eq.ready&{self._visible_filter(owner_id)}",
                headers=self.headers,
            )
            res.raise_for_status()
            return [UUID(r["id"]) for r in res.json()]

    async def delete_chunks(self, doc_id: UUID) -> None:
        """Clears a document's chunks so a retried job never duplicates them."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.delete(
                f"{self.base_url}/rest/v1/chunks?document_id=eq.{doc_id}",
                headers=self.headers,
            )
            res.raise_for_status()

    async def claim_next_document(self, stale_seconds: int, max_attempts: int) -> Optional[Document]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                f"{self.base_url}/rest/v1/rpc/claim_next_document",
                headers=self.headers,
                json={"p_stale_seconds": stale_seconds, "p_max_attempts": max_attempts},
            )
            res.raise_for_status()
            rows = res.json()
            return Document(**rows[0]) if rows else None

    async def fail_stale_documents(self, stale_seconds: int, max_attempts: int) -> int:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                f"{self.base_url}/rest/v1/rpc/fail_stale_documents",
                headers=self.headers,
                json={"p_stale_seconds": stale_seconds, "p_max_attempts": max_attempts},
            )
            res.raise_for_status()
            return int(res.json() or 0)

    async def _rpc_bool(self, fn: str, payload: Dict[str, Any], timeout: float = 30.0) -> bool:
        async with httpx.AsyncClient(timeout=timeout) as client:
            res = await client.post(f"{self.base_url}/rest/v1/rpc/{fn}", headers=self.headers, json=payload)
            res.raise_for_status()
            return bool(res.json())

    # Fenced worker writes: each returns False if the worker no longer holds `attempt`.
    async def heartbeat_document(self, doc_id: UUID, attempt: int) -> bool:
        return await self._rpc_bool("heartbeat_document", {"p_id": str(doc_id), "p_attempt": attempt})

    async def clear_chunks_fenced(self, doc_id: UUID, attempt: int) -> bool:
        return await self._rpc_bool("clear_chunks_fenced", {"p_id": str(doc_id), "p_attempt": attempt})

    async def insert_chunks_fenced(self, doc_id: UUID, attempt: int, chunks: List[DocumentChunk], batch_size: int = 100) -> bool:
        for i in range(0, len(chunks), batch_size):
            rows = [
                {
                    "content": c.content, "source": c.source, "page": c.page,
                    "chunk_index": c.chunk_index, "total_chunks": c.total_chunks,
                    "metadata": c.metadata,
                    "embedding": "[" + ",".join(repr(float(x)) for x in c.embedding) + "]",
                }
                for c in chunks[i : i + batch_size]
            ]
            ok = await self._rpc_bool(
                "insert_chunks_fenced", {"p_id": str(doc_id), "p_attempt": attempt, "p_rows": rows}, timeout=60.0
            )
            if not ok:
                return False
        return True

    async def finish_document(self, doc_id: UUID, attempt: int, status: str, error: Optional[str] = None,
                              page_count: Optional[int] = None, chunk_count: Optional[int] = None) -> bool:
        return await self._rpc_bool("finish_document", {
            "p_id": str(doc_id), "p_attempt": attempt, "p_status": status, "p_error": error,
            "p_pages": page_count, "p_chunks": chunk_count,
        })

    async def insert_chunks_batch(self, chunks: List[DocumentChunk], batch_size: int = 50) -> bool:
        if not chunks:
            return True

        async with httpx.AsyncClient(timeout=30.0) as client:
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i : i + batch_size]
                rows = []
                for c in batch:
                    rows.append(
                        {
                            "document_id": str(c.document_id),
                            "content": c.content,
                            "source": c.source,
                            "page": c.page,
                            "chunk_index": c.chunk_index,
                            "total_chunks": c.total_chunks,
                            "metadata": c.metadata,
                            "embedding": c.embedding,
                        }
                    )
                res = await client.post(
                    f"{self.base_url}/rest/v1/chunks",
                    headers=self.headers,
                    json=rows,
                )
                res.raise_for_status()
        return True

    async def match_chunks(
        self,
        query_embedding: List[float],
        match_threshold: float = 0.05,
        match_count: int = 5,
        document_ids: Optional[List[UUID]] = None,
    ) -> List[DocumentChunk]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            payload: Dict[str, Any] = {
                "query_embedding": query_embedding,
                "match_threshold": match_threshold,
                "match_count": match_count,
            }
            if document_ids:
                payload["p_document_ids"] = [str(d) for d in document_ids]

            res = await client.post(
                f"{self.base_url}/rest/v1/rpc/match_chunks",
                headers=self.headers,
                json=payload,
            )
            res.raise_for_status()
            rows = res.json()
            
            results = []
            for r in rows:
                if (r.get("metadata") or {}).get("embedding_profile") != PROFILE:
                    raise FDISException("Search index differs", "Stored search vectors use a different model profile. Reprocessing requires owner approval.", 409, "embedding_profile_mismatch")
                results.append(
                    DocumentChunk(
                        id=r.get("id"),
                        document_id=UUID(r["document_id"]),
                        content=r["content"],
                        source=r["source"],
                        page=r["page"],
                        chunk_index=r["chunk_index"],
                        total_chunks=r["total_chunks"],
                        metadata=r.get("metadata", {}),
                        similarity=float(r.get("similarity", 0.0)),
                    )
                )
            return results


    async def create_signed_upload_url(self, document_id: UUID, filename: str) -> Dict[str, str]:
        """Mints a short-lived signed upload URL for one owner-scoped object key.
        The bucket stays private; no storage policy change is needed because the
        browser only ever gets a per-object token minted here with the service key."""
        path = f"{document_id}/{filename}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                f"{self.base_url}/storage/v1/object/upload/sign/{self.bucket}/{path}",
                headers=self.headers,
                json={},
            )
            res.raise_for_status()
            signed = res.json().get("url", "")
        token = ""
        if "token=" in signed:
            token = signed.split("token=", 1)[1].split("&", 1)[0]
        if not token:
            raise RuntimeError("Storage did not return an upload token.")
        return {"bucket": self.bucket, "path": path, "token": token}

    async def get_pdf_size(self, document_id: UUID, filename: str) -> Optional[int]:
        """Byte size of the stored object via a 1-byte range probe; None if absent."""
        path = f"{document_id}/{filename}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(
                f"{self.base_url}/storage/v1/object/{self.bucket}/{path}",
                headers={"apikey": self.service_key, "Authorization": f"Bearer {self.service_key}", "Range": "bytes=0-0"},
            )
        if res.status_code not in (200, 206):
            return None
        content_range = res.headers.get("content-range", "")
        if "/" in content_range:
            total = content_range.rsplit("/", 1)[1]
            if total.isdigit():
                return int(total)
        return len(res.content)

    async def delete_pdf(self, document_id: UUID, filename: str) -> None:
        """Best-effort removal of one stored object (oversized or orphaned uploads)."""
        path = f"{document_id}/{filename}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            await client.request(
                "DELETE", f"{self.base_url}/storage/v1/object/{self.bucket}",
                headers=self.headers, json={"prefixes": [path]},
            )

    async def claim_inline_ingest(self, document_id: UUID, attempts: int) -> bool:
        """Atomically flip uploaded -> processing, fencing the inline sweep.

        Sets claimed_at to now: the sweep fences processing rows on claim time,
        never on document creation time, so a delayed ingest that just started
        on an old upload can never be swept while its function is alive. The
        status=eq.uploaded filter makes the claim atomic: a second ingest, or a
        sweep that already errored the row, gets no match instead of a race.
        """
        from datetime import datetime, timezone
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.patch(
                f"{self.base_url}/rest/v1/documents?id=eq.{document_id}&status=eq.uploaded",
                headers={**self.headers, "Prefer": "return=representation"},
                json={
                    "status": "processing",
                    "attempts": attempts + 1,
                    "claimed_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            res.raise_for_status()
            return bool(res.json())

    async def fail_stale_inline(self, stale_seconds: int, abandon_seconds: int) -> int:
        """Serverless (inline) recovery for uploads/processing a timeout killed.

        Two fences, both immune to live work:
        - processing rows are matched on claimed_at (processing start), not
          created_at. stale_seconds always exceeds the host's hard request cap
          (Vercel: 300s), so the invocation that set claimed_at is provably dead
          before the row matches. A delayed ingest starting on an old upload is
          safe: its claim refreshes claimed_at.
        - uploaded rows are matched on created_at against abandon_seconds,
          which exceeds the signed-upload URL's lifetime. No function runs for
          an uploaded row, so age alone is safe here; the fence exists only to
          reclaim orphaned storage objects.
        Runs only in inline mode; queue rows keep their own worker sweep.
        """
        from datetime import datetime, timedelta, timezone
        from urllib.parse import quote
        # Percent-encode: a raw ISO "+00:00" decodes as a space server-side and
        # PostgREST rejects the filter (400), which the caller swallows by design.
        now = datetime.now(timezone.utc)
        stale_cutoff = quote((now - timedelta(seconds=stale_seconds)).isoformat(), safe="")
        abandon_cutoff = quote((now - timedelta(seconds=abandon_seconds)).isoformat(), safe="")
        canceled_message = quote(f'"{self.CANCELED_UPLOAD_MESSAGE}"', safe="")
        # (filter, mark rows error?) - canceled rows are already fenced error
        # markers; only their (possibly re-PUT) storage object needs reclaim.
        filters = [
            (f"status=eq.processing&claimed_at=lt.{stale_cutoff}", True),
            (f"status=eq.uploaded&created_at=lt.{abandon_cutoff}", True),
            (f"status=eq.error&error_message=eq.{canceled_message}&created_at=lt.{abandon_cutoff}", False),
        ]
        swept = 0
        for filt, mark_error in filters:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    f"{self.base_url}/rest/v1/documents?select=id,filename&{filt}",
                    headers=self.headers,
                )
                res.raise_for_status()
                rows = res.json()
                if not rows:
                    continue
                if mark_error:
                    res = await client.patch(
                        f"{self.base_url}/rest/v1/documents?{filt}",
                        headers=self.headers,
                        json={"status": "error", "error_message": "Upload or processing was interrupted. Please delete this document and try again."},
                    )
                    res.raise_for_status()
            for row in rows:
                try:
                    await self.delete_pdf(UUID(row["id"]), row["filename"])
                except Exception:
                    pass  # storage cleanup is best-effort; the error row stays deletable
            swept += len(rows)
        return swept

    async def upload_pdf(self, document_id: UUID, filename: str, pdf_bytes: bytes) -> str:
        path = f"{document_id}/{filename}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                f"{self.base_url}/storage/v1/object/{self.bucket}/{path}",
                headers={
                    "apikey": self.service_key,
                    "Authorization": f"Bearer {self.service_key}",
                    "Content-Type": "application/pdf",
                    "x-upsert": "true",
                },
                content=pdf_bytes,
            )
            res.raise_for_status()
        return path  # private object key, never a public URL

    async def get_pdf_bytes(self, document_id: UUID, filename: str) -> Optional[bytes]:
        path = f"{document_id}/{filename}"
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(
                f"{self.base_url}/storage/v1/object/{self.bucket}/{path}",
                headers=self.headers,
            )
            if res.status_code == 200:
                return res.content
        return None

    async def get_document_chunks(self, document_id: UUID) -> List[DocumentChunk]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(
                f"{self.base_url}/rest/v1/chunks?select=id,document_id,content,source,page,chunk_index,total_chunks,metadata&document_id=eq.{document_id}&order=page.asc,chunk_index.asc",
                headers=self.headers,
            )
            res.raise_for_status()
            rows = res.json()
            return [
                DocumentChunk(
                    id=r.get("id"),
                    document_id=UUID(r["document_id"]),
                    content=r["content"],
                    source=r["source"],
                    page=r["page"],
                    chunk_index=r["chunk_index"],
                    total_chunks=r["total_chunks"],
                    metadata=r.get("metadata", {}),
                    similarity=0.0,
                )
                for r in rows
            ]

    async def take_question_quota(self, owner_id: str, user_limit: int, global_limit: int) -> str:
        """Atomically count one answer against the per-guest and global daily free quotas.
        Returns 'ok', 'user_exhausted' or 'global_exhausted' (migration 0006)."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                f"{self.base_url}/rest/v1/rpc/take_question_quota",
                headers=self.headers,
                json={"p_owner": owner_id, "p_user_limit": user_limit, "p_global_limit": global_limit},
            )
            res.raise_for_status()
            return res.json()

    async def count_owner_documents(self, owner_id: str) -> int:
        """Live (not being deleted) documents the owner currently holds."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(
                f"{self.base_url}/rest/v1/documents?select=id&owner_id=eq.{owner_id}&status=neq.deleting",
                headers={**self.headers, "Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"},
            )
            res.raise_for_status()
            content_range = res.headers.get("content-range", "*/0")
            try:
                return int(content_range.split("/")[-1])
            except ValueError:
                return 0

    async def sweep_expired_guest_documents(self, limit: int = 20) -> int:
        """Delete guest uploads whose session_expires_at has passed (rows, chunks, storage objects).

        Expired rows are force-deleted in any status: an expired 'processing' row is
        stale work, not a live upload. Bounded per call; ridden by traffic and the
        daily scheduled sweep."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.get(
                f"{self.base_url}/rest/v1/documents?select=id,filename&session_expires_at=lt.{datetime.now(timezone.utc).isoformat()}&order=session_expires_at.asc&limit={limit}",
                headers=self.headers,
            )
            res.raise_for_status()
            rows = res.json()
            swept = 0
            for row in rows:
                try:
                    await client.request(
                        "DELETE", f"{self.base_url}/storage/v1/object/{self.bucket}",
                        headers=self.headers, json={"prefixes": [f"{row['id']}/{row['filename']}"]},
                    )
                    dele = await client.delete(
                        f"{self.base_url}/rest/v1/documents?id=eq.{row['id']}&session_expires_at=lt.{datetime.now(timezone.utc).isoformat()}",
                        headers=self.headers,
                    )
                    dele.raise_for_status()
                    swept += 1
                except httpx.HTTPError:
                    logger.warning("Expired guest document sweep failed for one row", exc_info=True)
            return swept

    async def delete_owner_usage(self, owner_id: str) -> None:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.delete(
                f"{self.base_url}/rest/v1/ask_usage?owner_id=eq.{owner_id}",
                headers=self.headers,
            )
            res.raise_for_status()

    async def admin_delete_auth_user(self, user_id: str) -> bool:
        """GoTrue admin delete: removes the caller's own auth identity (docs cascade by FK)."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.delete(
                f"{self.base_url}/auth/v1/admin/users/{user_id}",
                headers=self.headers,
            )
            return res.status_code in (200, 204)

    async def ping(self) -> tuple[bool, float, Optional[str]]:
        import time
        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(
                    f"{self.base_url}/rest/v1/documents?limit=1",
                    headers=self.headers,
                )
                latency_ms = round((time.perf_counter() - t0) * 1000, 2)
                return (res.status_code == 200, latency_ms, None)
        except Exception as e:
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            return (False, latency_ms, str(e))
