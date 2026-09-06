from typing import List, Optional
from uuid import UUID
from src.core.config import get_settings
from src.domain.citation import create_citations_from_chunks
from src.domain.models import Citation, DocumentChunk
from src.infrastructure.embedding_client import get_embedding_client
from src.infrastructure.supabase_client import SupabaseClient


class RetrievalService:
    def __init__(self, supabase_client: SupabaseClient = None):
        self.settings = get_settings()
        self.supabase = supabase_client or SupabaseClient()
        self.embedding_client = get_embedding_client()

    async def retrieve_relevant_chunks(
        self,
        query: str,
        match_threshold: Optional[float] = None,
        top_k: Optional[int] = None,
        document_ids: Optional[List[UUID]] = None,
    ) -> List[DocumentChunk]:
        threshold = match_threshold if match_threshold is not None else self.settings.SIMILARITY_THRESHOLD
        k = top_k or self.settings.TOP_K_MATCHES

        query_embedding = self.embedding_client.embed_query(query)
        chunks = await self.supabase.match_chunks(
            query_embedding=query_embedding,
            match_threshold=threshold,
            match_count=k,
            document_ids=document_ids,
        )
        return chunks

    def build_citations(self, chunks: List[DocumentChunk]) -> List[Citation]:
        return create_citations_from_chunks(chunks)
