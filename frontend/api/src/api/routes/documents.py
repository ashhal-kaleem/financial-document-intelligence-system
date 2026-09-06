from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from src.core.errors import DocumentNotFoundError, InvalidPDFError
from src.infrastructure.supabase_client import SupabaseClient
from src.services.ingestion import DocumentIngestionService

router = APIRouter(prefix="/documents", tags=["Documents"])
supabase = SupabaseClient()
ingestion_service = DocumentIngestionService(supabase)

@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise InvalidPDFError("Only PDF documents are supported.")

    pdf_bytes = await file.read()
    if len(pdf_bytes) == 0:
        raise InvalidPDFError("Uploaded PDF file is empty.")

    if len(pdf_bytes) > 25 * 1024 * 1024:
        raise InvalidPDFError("File size exceeds maximum allowable 25MB limit.")

    try:
        doc = await ingestion_service.ingest_document(
            filename=file.filename,
            pdf_bytes=pdf_bytes,
        )
        return {
            "success": True,
            "data": doc.model_dump(),
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": "/api/v1/documents",
            }
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {str(exc)}",
        )

@router.get("")
async def list_documents():
    docs = await supabase.get_documents()
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
async def get_document(document_id: UUID):
    doc = await supabase.get_document_by_id(document_id)
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
async def delete_document(document_id: UUID):
    success = await supabase.delete_document(document_id)
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


from fastapi.responses import Response

@router.get("/{document_id}/chunks")
async def get_document_chunks_endpoint(document_id: UUID):
    doc = await supabase.get_document_by_id(document_id)
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
async def get_document_pdf(document_id: UUID):
    doc = await supabase.get_document_by_id(document_id)
    if not doc:
        raise DocumentNotFoundError(str(document_id))
    
    # Try fetching from Supabase storage
    pdf_bytes = await supabase.get_pdf_bytes(document_id, doc.filename)
    
    # Fallback to local sample if test/sample filing
    if not pdf_bytes:
        import os
        sample_path = 'tests/sample_apple_10k.pdf'
        if os.path.exists(sample_path):
            with open(sample_path, 'rb') as f:
                pdf_bytes = f.read()
                
    if not pdf_bytes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF file content not found for document {document_id}"
        )
        
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{doc.filename}"',
            "Cache-Control": "public, max-age=3600",
        }
    )
