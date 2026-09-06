from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional
from uuid import UUID
from src.domain.models import Document, DocumentChunk


class BaseLLMClient(ABC):
    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> AsyncGenerator[str, None]:
        pass


class BaseVectorStore(ABC):
    @abstractmethod
    async def insert_chunks_batch(self, chunks: List[DocumentChunk]) -> bool:
        pass

    @abstractmethod
    async def match_chunks(
        self,
        query_embedding: List[float],
        match_threshold: float,
        match_count: int,
        document_ids: Optional[List[UUID]] = None,
    ) -> List[DocumentChunk]:
        pass
