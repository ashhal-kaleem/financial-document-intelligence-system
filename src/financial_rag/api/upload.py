"""Upload endpoints for PDF documents."""

import uuid
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, Request, BackgroundTasks

from financial_rag.api.schemas import DocumentItem, DocumentListResponse, UploadResponse
from financial_rag.ingestion.factory import load_document
from financial_rag.chunking.splitter import RecursiveCharacterSplitter

upload_router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = Path("data/uploads")

def process_uploaded_pdf(
    file_path: Path, 
    document_id: str, 
    pipeline, 
    supabase_client
):
    try:
        # Load and chunk
        docs = load_document(file_path)
        splitter = RecursiveCharacterSplitter()
        chunks = splitter.split_documents(docs)
        
        # Add document_id to chunks metadata so it's inserted into the db
        for chunk in chunks:
            chunk.metadata["document_id"] = document_id

        # Insert chunks
        pipeline._retriever._store.add_chunks(chunks, pipeline._retriever._embedder)
        
        page_count = len(docs)
        chunk_count = len(chunks)
        
        # Update documents row
        update_resp = supabase_client.table("documents").update({
            "status": "ready",
            "page_count": page_count,
            "chunk_count": chunk_count
        }).eq("id", document_id).execute()
        
        if not update_resp.data:
            raise Exception("Document row missing. Perhaps it was deleted during processing.")
        
    except Exception as e:
        # On failure, clean up any inserted chunks and mark as error
        if hasattr(pipeline._retriever._store, "delete_by_document_id"):
            pipeline._retriever._store.delete_by_document_id(document_id)
            
        supabase_client.table("documents").update({
            "status": "error",
            "error_message": str(e)
        }).eq("id", document_id).execute()
    finally:
        # Clean up temp file
        if file_path.exists():
            file_path.unlink()

@upload_router.post("/upload", response_model=UploadResponse)
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    pipeline = request.app.state.pipeline
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized.")
    
    supabase_client = getattr(pipeline._retriever._store, "_client", None)
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Supabase client not available.")

    if not file.filename.lower().endswith(".pdf") or file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    # Read magic bytes
    header = await file.read(5)
    if not header.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")
    await file.seek(0)
    
    # Generate UUID4
    document_id = str(uuid.uuid4())
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOAD_DIR / f"{document_id}.pdf"
    
    size = 0
    with open(file_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > 50 * 1024 * 1024:
                file_path.unlink()
                raise HTTPException(status_code=413, detail="File too large. Max 50MB.")
            f.write(chunk)
            
    # Insert row into documents table
    supabase_client.table("documents").insert({
        "id": document_id,
        "filename": file.filename,
        "status": "processing"
    }).execute()
    
    background_tasks.add_task(
        process_uploaded_pdf, 
        file_path, 
        document_id, 
        pipeline, 
        supabase_client
    )
    
    return UploadResponse(
        document_id=document_id,
        filename=file.filename,
        status="processing"
    )

@upload_router.get("", response_model=DocumentListResponse)
def list_documents(request: Request):
    pipeline = request.app.state.pipeline
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized.")
    
    supabase_client = getattr(pipeline._retriever._store, "_client", None)
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Supabase client not available.")
        
    response = supabase_client.table("documents").select("*").order("created_at", desc=True).execute()
    
    docs = []
    for row in response.data:
        docs.append(DocumentItem(**row))
        
    return DocumentListResponse(documents=docs)

@upload_router.delete("/{document_id}")
def delete_document(document_id: str, request: Request):
    try:
        uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format.")
        
    pipeline = request.app.state.pipeline
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized.")
    
    store = pipeline._retriever._store
    supabase_client = getattr(store, "_client", None)
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Supabase client not available.")
        
    # Check if sample
    doc_resp = supabase_client.table("documents").select("is_sample").eq("id", document_id).execute()
    if not doc_resp.data:
        raise HTTPException(status_code=404, detail="Document not found.")
        
    if doc_resp.data[0].get("is_sample"):
        raise HTTPException(status_code=403, detail="Cannot delete sample documents.")
        
    # Delete chunks
    if hasattr(store, "delete_by_document_id"):
        store.delete_by_document_id(document_id)
        
    # Delete from documents table
    supabase_client.table("documents").delete().eq("id", document_id).execute()
    
    return {"deleted": True}
