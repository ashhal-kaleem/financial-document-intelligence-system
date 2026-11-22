import time
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from src.core.config import get_settings
from src.infrastructure.supabase_client import SupabaseClient
from src.infrastructure.embedding_assets import PROFILE, verify_model_assets

router = APIRouter(tags=["Health"])

_PING_TTL_SECONDS = 30
_ping_cache: dict = {"at": 0.0, "value": None}


async def _cached_ping(supabase: SupabaseClient):
    """Hosting probes hit /health often; reuse the DB result for a short time."""
    now = time.monotonic()
    if _ping_cache["value"] is not None and now - _ping_cache["at"] < _PING_TTL_SECONDS:
        return _ping_cache["value"]
    value = await supabase.ping()
    _ping_cache.update(at=now, value=value)
    return value

@router.get("/health")
async def health_check():
    settings = get_settings()
    supabase = SupabaseClient()
    
    # Real live probe to Supabase PostgREST endpoint
    db_ok, latency_ms, db_error = await _cached_ping(supabase)

    try:
        assets_ok = await asyncio.to_thread(verify_model_assets)
    except RuntimeError:
        assets_ok = False
    healthy = db_ok and assets_ok
    overall_status = "healthy" if healthy else "unhealthy"
    http_status = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    checks = {
        "embeddings": {
            "status": "local_assets_verified" if assets_ok else "assets_missing_or_invalid",
            "profile": PROFILE,
            "inference_probed": False,
        },
        "database": {
            "status": "connected" if db_ok else "degraded",
            "latency_ms": latency_ms,
        },
        "answers": {
            "status": "configured_unverified" if settings.GROQ_API_KEY else "unconfigured",
            "model": settings.GROQ_MODEL,
        },
        "resend": {
            "status": "configured_unverified" if settings.RESEND_API_KEY else "unconfigured",
        }
    }
    # Do not echo upstream error details or imply configured providers were probed.

    return JSONResponse(
        status_code=http_status,
        content={
            "success": healthy,
            "status": overall_status,
            "checks": checks,
            "version": "1.0.0",
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": "/api/v1/health",
            }
        }
    )
