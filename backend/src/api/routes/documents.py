from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
import logging
import os
import re
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from src.core.auth import AuthUser, get_current_user
from src.core.config import effective_ingestion_mode, get_settings
from src.core.rate_limit import rate_limited_user
from src.core.errors import DocumentNotFoundError, InvalidPDFError
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

@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_document(response: Response, file: UploadFile = File(...), user: AuthUser = Depends(rate_limited_user)):
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

@router.get("")
async def list_documents(user: AuthUser = Depends(get_current_user)):
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
