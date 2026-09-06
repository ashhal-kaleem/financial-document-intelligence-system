from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    filename: str
    page_count: int = 0
    chunk_count: int = 0
    status: str = "uploaded"  # uploaded, processing, ready, error
    error_message: Optional[str] = None
    is_sample: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentChunk(BaseModel):
    id: Optional[int] = None
    document_id: UUID
    content: str
    source: str
    page: int
    chunk_index: int
    total_chunks: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    similarity: Optional[float] = None


class Citation(BaseModel):
    citation_id: int
    document_id: UUID
    filename: str
    page: int
    chunk_index: int
    total_chunks: int
    similarity: float
    snippet: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, description="User question on financial reports")
    document_ids: Optional[List[UUID]] = Field(default=None, description="Optional document filter")
    model: Optional[str] = Field(default=None, description="Optional model override")


class NotificationRequest(BaseModel):
    recipient: str
    document_name: str
    summary: str
