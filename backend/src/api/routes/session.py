"""Guest session lifecycle: explicit self-service deletion and the scheduled expiry sweep."""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from src.core.auth import AuthUser, UnauthorizedError, get_current_user
from src.core.config import get_settings
from src.infrastructure.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Session"])
supabase = SupabaseClient()


@router.delete("/session")
async def end_session(user: AuthUser = Depends(get_current_user)):
    """Delete everything the caller owns: documents (rows, chunks, stored PDFs),
    usage counters and the auth identity itself. Self-scoped: only the caller's
    data is touched. Old named accounts are never affected unless they call this."""
    documents = await supabase.get_documents(user.id)
    deleted, failed = 0, 0
    for doc in documents:
        try:
            if doc.status == "uploaded":
                ok = await supabase.cancel_uploaded_document(doc.id, user.id)
            else:
                ok = await supabase.delete_document(doc.id, user.id)
            deleted += 1 if ok else 0
            failed += 0 if ok else 1
        except Exception:
            failed += 1
            logger.warning("Session cleanup failed for one document", exc_info=True)
    try:
        await supabase.delete_owner_usage(user.id)
    except Exception:
        logger.warning("Session usage cleanup failed", exc_info=True)
    identity_removed = await supabase.admin_delete_auth_user(user.id)
    return {
        "success": True,
        "data": {
            "documents_deleted": deleted,
            "documents_failed": failed,
            "identity_removed": identity_removed,
        },
        "meta": {"timestamp": datetime.now(timezone.utc).isoformat(), "path": "/api/v1/session"},
    }


@router.get("/internal/sweep")
async def scheduled_sweep(request: Request):
    """Daily Vercel Cron target: removes expired guest uploads even with no traffic.
    Vercel sends Authorization: Bearer $CRON_SECRET; fail closed when unset."""
    settings = get_settings()
    if not settings.CRON_SECRET:
        raise UnauthorizedError("Sweep is not configured.")
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or token.strip() != settings.CRON_SECRET:
        raise UnauthorizedError()
    stale = await supabase.fail_stale_inline(settings.JOB_STALE_SECONDS, settings.UPLOAD_ABANDON_SECONDS)
    expired = await supabase.sweep_expired_guest_documents(limit=100)
    orphans = await supabase.sweep_orphaned_guest_users()
    return {
        "success": True,
        "data": {
            "stale_reclaimed": stale,
            "expired_guest_documents_deleted": expired,
            "orphaned_guest_identities_deleted": orphans,
        },
        "meta": {"timestamp": datetime.now(timezone.utc).isoformat(), "path": "/api/v1/internal/sweep"},
    }
