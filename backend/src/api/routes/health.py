from datetime import datetime, timezone
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from src.core.config import get_settings
from src.infrastructure.supabase_client import SupabaseClient

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    settings = get_settings()
    supabase = SupabaseClient()
    
    # Real live probe to Supabase PostgREST endpoint
    db_ok, latency_ms, db_error = await supabase.ping()

    overall_status = "healthy" if db_ok else "unhealthy"
    http_status = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE

    checks = {
        "database": {
            "status": "connected" if db_ok else "degraded",
            "latency_ms": latency_ms,
        },
        "groq": {
            "status": "available" if settings.GROQ_API_KEY else "unconfigured",
        },
        "openrouter": {
            "status": "available" if settings.OPENROUTER_API_KEY else "unconfigured",
        },
        "resend": {
            "status": "available" if settings.RESEND_API_KEY else "unconfigured",
        }
    }
    if db_error:
        checks["database"]["error"] = db_error

    return JSONResponse(
        status_code=http_status,
        content={
            "success": db_ok,
            "status": overall_status,
            "checks": checks,
            "version": "1.0.0",
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": "/api/v1/health",
            }
        }
    )
