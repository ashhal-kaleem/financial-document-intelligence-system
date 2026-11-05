import asyncio
import logging
from typing import Optional
from src.core.config import get_settings
from src.services.ingestion import DocumentIngestionService

logger = logging.getLogger(__name__)


class IngestionWorker:
    """Polls the Postgres-backed queue (claim_next_document) and processes one job at a time.
    State is in the database, so a crash or restart only delays jobs; stale ones are re-claimed."""

    def __init__(self, ingestion: DocumentIngestionService):
        self.ingestion = ingestion
        self.settings = get_settings()
        self._task: Optional[asyncio.Task] = None

    async def run_once(self) -> bool:
        """Returns True if a job was processed."""
        s, db = self.settings, self.ingestion.supabase
        await db.fail_stale_documents(s.JOB_STALE_SECONDS, s.JOB_MAX_ATTEMPTS)
        doc = await db.claim_next_document(s.JOB_STALE_SECONDS, s.JOB_MAX_ATTEMPTS)
        if doc is None:
            return False
        logger.info("Processing document %s (attempt claimed)", doc.id)
        await self.ingestion.process_claimed(doc)
        return True

    async def run_forever(self) -> None:
        while True:
            try:
                if await self.run_once():
                    continue  # drain the queue without sleeping
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Ingestion worker iteration failed")
            await asyncio.sleep(self.settings.WORKER_POLL_SECONDS)

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self.run_forever())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
