from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder

class FDISException(Exception):
    def __init__(
        self,
        title: str,
        detail: str,
        status_code: int = 500,
        code: str = "internal_error",
        invalid_params: Optional[list] = None,
    ):
        super().__init__(detail)
        self.title = title
        self.detail = detail
        self.status_code = status_code
        self.code = code
        self.invalid_params = invalid_params or []

class DocumentNotFoundError(FDISException):
    def __init__(self, doc_id: str):
        super().__init__(
            title="Document Not Found",
            detail=f"Document with ID '{doc_id}' does not exist.",
            status_code=404,
            code="not_found",
        )

class InvalidPDFError(FDISException):
    def __init__(self, detail: str = "Uploaded file is not a valid PDF document."):
        super().__init__(
            title="Invalid PDF Document",
            detail=detail,
            status_code=422,
            code="invalid_pdf",
        )

class RetrievalError(FDISException):
    def __init__(self, detail: str = "Vector similarity search failed."):
        super().__init__(
            title="Retrieval Failed",
            detail=detail,
            status_code=502,
            code="retrieval_error",
        )

class LLMInferenceError(FDISException):
    def __init__(self, detail: str = "LLM inference provider returned an error."):
        super().__init__(
            title="Inference Error",
            detail=detail,
            status_code=502,
            code="inference_error",
        )

def fdis_exception_handler(request: Request, exc: FDISException) -> JSONResponse:
    payload = {
        "success": False,
        "error": {
            "code": exc.code,
            "message": exc.detail,
            "title": exc.title,
            "details": exc.invalid_params if exc.invalid_params else None,
        },
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path,
        },
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(payload),
        headers={"Content-Type": "application/problem+json"},
    )

def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    invalid_params = []
    for err in exc.errors():
        field_path = ".".join(str(loc) for loc in err["loc"] if loc != "body")
        invalid_params.append({
            "field": field_path or "body",
            "issue": err["msg"],
            "type": err["type"],
        })

    payload = {
        "success": False,
        "error": {
            "code": "validation_error",
            "message": "Request payload failed contract schema validation.",
            "details": invalid_params,
        },
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path,
        },
    }
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(payload),
        headers={"Content-Type": "application/problem+json"},
    )
