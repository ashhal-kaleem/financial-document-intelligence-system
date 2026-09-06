import traceback
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.api.routes import ask, documents, health, notify
from src.core.config import get_settings
from src.core.errors import (
    FDISException,
    fdis_exception_handler,
    validation_exception_handler,
)

settings = get_settings()

app = FastAPI(
    title="Financial Document Intelligence System (FDIS) API",
    description="Enterprise API for sub-second, strictly grounded financial document Q&A",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom exception handlers (RFC 9457 & Unified Error Envelopes)
app.add_exception_handler(FDISException, fdis_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "internal_error",
                "message": str(exc),
                "traceback": tb,
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
app.include_router(notify.router, prefix="/api/v1")

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(ask.router)
app.include_router(notify.router)

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
