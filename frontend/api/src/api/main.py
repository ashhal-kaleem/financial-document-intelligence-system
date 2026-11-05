import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.api.routes import ask, documents, health
from src.core.config import get_settings
from src.core.errors import (
    FDISException,
    fdis_exception_handler,
    validation_exception_handler,
)

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title="Financial Document Intelligence System (FDIS) API",
    description="Enterprise API for sub-second, strictly grounded financial document Q&A",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Register custom exception handlers (RFC 9457 & Unified Error Envelopes)
app.add_exception_handler(FDISException, fdis_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s", request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "internal_error",
                "message": "Something went wrong on the server.",
            },
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": request.url.path,
            },
        },
    )

# Dual-mount routes: both under /api/v1 and root for maximum proxy/serverless compatibility
app.include_router(health.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(ask.router, prefix="/api/v1")

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(ask.router)

@app.get("/")
async def root():
    return {
        "success": True,
        "data": {
            "service": "Financial Document Intelligence System",
            "docs_url": "/docs",
            "health_check": "/api/v1/health",
        },
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": "/",
        }
    }
