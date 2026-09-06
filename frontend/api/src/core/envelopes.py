from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

class ResponseMeta(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    requestId: Optional[str] = None
    path: Optional[str] = None

class APIErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[List[Any]] = None

class UnifiedResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[APIErrorDetail] = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)
