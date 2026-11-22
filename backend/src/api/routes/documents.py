from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4
import logging
import os
import re
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, Field
from src.core.auth import AuthUser, get_current_user
from src.core.config import effective_ingestion_mode, get_settings
from src.core.rate_limit import rate_limited_user
from src.core.errors import DocumentNotFoundError, InvalidPDFError
from src.domain.models import Document
from src.infrastructure.supabase_client import SupabaseClient
from src.services.ingestion import DocumentIngestionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])


def safe_filename(name: str) -> str:
    """Strip any path and unsafe characters; the name goes into storage paths and headers."""
    base = os.path.basename((name or "").replace("\\", "/"))
    base = re.sub(r"[^A-Za-z0-9._ -]", "_", base).strip(" .")
    return (base or "document.pdf")[:150]

settings = get_settings()
supabase = SupabaseClient()
ingestion_service = DocumentIngestionService(supabase)


async def _sweep_inline_stale() -> None:
    """Serverless-only recovery for uploads/processing killed by a platform timeout.
    Never breaks the request it rides on; queue mode keeps its own worker sweep."""
    if effective_ingestion_mode() != "inline":
        return
    try:
        swept = await supabase.fail_stale_inline(settings.JOB_STALE_SECONDS, settings.UPLOAD_ABANDON_SECONDS)
        if swept:
            logger.info("Inline stale sweep reclaimed %s document(s)", swept)
    except Exception:
        logger.warning("Inline stale sweep failed", exc_info=True)


class UploadUrlRequest(BaseModel):
    filename: str = Field(..., max_length=300)
    size: int = Field(..., ge=0)

@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_document(response: Response, file: UploadFile = File(...), user: AuthUser = Depends(rate_limited_user)):
    await _sweep_inline_stale()
    filename = safe_filename(file.filename or "")
    if not any(filename.lower().endswith(ext) for ext in settings.ALLOWED_EXTENSIONS):
        supported = ", ".join(ext.lstrip(".").upper() for ext in settings.ALLOWED_EXTENSIONS)
        raise InvalidPDFError(f"Only {supported} documents are supported.")

    pdf_bytes = await file.read(settings.MAX_UPLOAD_SIZE_BYTES + 1)
    if len(pdf_bytes) == 0:
        raise InvalidPDFError("Uploaded PDF file is empty.")

    if len(pdf_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise InvalidPDFError(f"File size exceeds maximum allowable {max_mb}MB limit.")

    if not pdf_bytes.startswith(b"%PDF"):
        raise InvalidPDFError("File content is not a PDF.")

    queued = effective_ingestion_mode() == "queue"
    try:
        if queued:
            doc = await ingestion_service.enqueue_document(
                filename=filename, pdf_bytes=pdf_bytes, owner_id=user.id
            )
        else:
            doc = await ingestion_service.ingest_document(
                filename=filename,
                pdf_bytes=pdf_bytes,
                owner_id=user.id,
            )
        if queued:
            response.status_code = status.HTTP_202_ACCEPTED
        return {
            "success": True,
            "data": doc.model_dump(),
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": "/api/v1/documents",
            }
        }
    except InvalidPDFError:
        raise
    except Exception:
        logger.warning("Document ingestion failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest document.",
        )

@router.post("/upload-url", status_code=status.HTTP_201_CREATED)
async def create_upload_url(payload: UploadUrlRequest, user: AuthUser = Depends(rate_limited_user)):
    """Step 1 of the serverless upload: validate, create the owner-scoped row and
    mint a one-object signed upload URL. The browser then PUTs the PDF straight
    to private Supabase storage, so big request bodies never hit this host."""
    await _sweep_inline_stale()
    filename = safe_filename(payload.filename)
    if not any(filename.lower().endswith(ext) for ext in settings.ALLOWED_EXTENSIONS):
        supported = ", ".join(ext.lstrip(".").upper() for ext in settings.ALLOWED_EXTENSIONS)
        raise InvalidPDFError(f"Only {supported} documents are supported.")
    if payload.size <= 0:
        raise InvalidPDFError("Uploaded PDF file is empty.")
    if payload.size > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise InvalidPDFError(f"File size exceeds maximum allowable {max_mb}MB limit.")
    doc = Document(id=uuid4(), filename=filename, status="uploaded", owner_id=user.id)
    await supabase.create_document(doc)
    signed = await supabase.create_signed_upload_url(doc.id, filename)
    return {
        "success": True,
        "data": {
            "document_id": str(doc.id),
            "bucket": signed["bucket"],
            "path": signed["path"],
            "token": signed["token"],
            "max_upload_size_bytes": settings.MAX_UPLOAD_SIZE_BYTES,
        },
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": "/api/v1/documents/upload-url",
        },
    }


@router.post("/{document_id}/ingest")
async def ingest_uploaded_document(document_id: UUID, user: AuthUser = Depends(rate_limited_user)):
    """Step 2: after the browser's direct storage upload finishes, process the
    stored object inline. The object is re-validated server-side: the signed
    URL, the browser and stored metadata are never trusted for size."""
    await _sweep_inline_stale()
    doc = await supabase.get_document_by_id(document_id, user.id)
    if not doc:
        raise DocumentNotFoundError(str(document_id))
    if doc.status != "uploaded":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is not awaiting an upload.",
        )
    size = await supabase.get_pdf_size(document_id, doc.filename)
    if size is None:
        raise InvalidPDFError("File not uploaded yet. Finish the upload, then retry.")
    if size > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        await supabase.delete_pdf(document_id, doc.filename)
        await supabase.update_document_status(
            document_id, "error",
            error_message=f"File size exceeds maximum allowable {max_mb}MB limit.",
        )
        raise InvalidPDFError(f"File size exceeds maximum allowable {max_mb}MB limit.")
    # Atomic claim fences the stale sweep: claimed_at is refreshed now, so a
    # delayed ingest on an old upload can never be swept mid-flight, and a
    # concurrent ingest/sweep gets no match instead of racing.
    claimed = await supabase.claim_inline_ingest(document_id, doc.attempts or 0)
    if not claimed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is not awaiting an upload.",
        )
    doc.status = "processing"
    try:
        result = await ingestion_service.ingest_stored_document(doc)
    except Exception:
        logger.warning("Document ingestion failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest document.",
        )
    return {
        "success": True,
        "data": result.model_dump(),
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": f"/api/v1/documents/{document_id}/ingest",
        },
    }


@router.get("")
async def list_documents(user: AuthUser = Depends(get_current_user)):
    await _sweep_inline_stale()
    docs = await supabase.get_documents(user.id)
    return {
        "success": True,
        "data": [d.model_dump() for d in docs],
        "meta": {
            "total": len(docs),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": "/api/v1/documents",
        }
    }

@router.get("/{document_id}")
async def get_document(document_id: UUID, user: AuthUser = Depends(get_current_user)):
    doc = await supabase.get_document_by_id(document_id, user.id)
    if not doc:
        raise DocumentNotFoundError(str(document_id))
    return {
        "success": True,
        "data": doc.model_dump(),
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": f"/api/v1/documents/{document_id}",
        }
    }

@router.delete("/{document_id}")
async def delete_document(document_id: UUID, user: AuthUser = Depends(get_current_user)):
    # Owner check first: a missing or foreign document is a 404 even if the
    # delete RPC is unavailable, while a real owner delete failure must surface.
    doc = await supabase.get_document_by_id(document_id, user.id)
    if not doc:
        raise DocumentNotFoundError(str(document_id))
    if doc.status == "uploaded":
        # Never-ingested upload: cancel it in code (the delete RPC refuses
        # uploaded rows as busy). The row stays as a fenced 'error' marker so
        # the storage object remains tracked until the signed grant expires.
        cancelled = await supabase.cancel_uploaded_document(document_id, user.id)
        if not cancelled:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document started processing. Wait for it to finish before deleting.",
            )
        return {
            "success": True,
            "data": {"id": str(document_id), "status": "canceled"},
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": f"/api/v1/documents/{document_id}",
            },
        }
    success = await supabase.delete_document(document_id, user.id)
    if not success:
        raise DocumentNotFoundError(str(document_id))
    return {
        "success": True,
        "data": {"id": str(document_id), "status": "deleted"},
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": f"/api/v1/documents/{document_id}",
        }
    }



@router.get("/{document_id}/chunks")
async def get_document_chunks_endpoint(document_id: UUID, user: AuthUser = Depends(get_current_user)):
    doc = await supabase.get_document_by_id(document_id, user.id)
    if not doc:
        raise DocumentNotFoundError(str(document_id))
    chunks = await supabase.get_document_chunks(document_id)
    return {
        "success": True,
        "data": [c.model_dump() for c in chunks],
        "meta": {
            "total": len(chunks),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": f"/api/v1/documents/{document_id}/chunks",
        }
    }

@router.get("/{document_id}/pdf")
async def get_document_pdf(document_id: UUID, user: AuthUser = Depends(get_current_user)):
    doc = await supabase.get_document_by_id(document_id, user.id)
    if not doc:
        raise DocumentNotFoundError(str(document_id))
    
    # Try fetching from Supabase storage
    pdf_bytes = await supabase.get_pdf_bytes(document_id, doc.filename)
    
    if not pdf_bytes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF file content not found for document {document_id}"
        )
        
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{safe_filename(doc.filename)}"',
            "Cache-Control": "private, no-store",
        }
    )
