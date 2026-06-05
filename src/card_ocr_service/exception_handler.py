import logging
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from card_ocr_service.exception import ErrorCode, OcrException
from card_ocr_service.schemas.error import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(OcrException, _handle_ocr_exception)
    app.add_exception_handler(RequestValidationError, _handle_validation_exception)
    app.add_exception_handler(Exception, _handle_internal_exception)


async def _handle_ocr_exception(request: Request, exception: OcrException) -> JSONResponse:
    if exception.error_code.status >= 500:
        logger.exception("Card OCR exception handled. code=%s", exception.error_code.code)
    return _error_response(request, exception.error_code, exception.details)


async def _handle_validation_exception(
    request: Request,
    exception: RequestValidationError,
) -> JSONResponse:
    details = [
        ErrorDetail(field=_field_name(error.get("loc")), message=str(error.get("msg", "")))
        for error in exception.errors()
    ]
    return _error_response(request, ErrorCode.INVALID_REQUEST, details)


async def _handle_internal_exception(request: Request, exception: Exception) -> JSONResponse:
    logger.exception("Unhandled card OCR exception.", exc_info=exception)
    return _error_response(request, ErrorCode.INTERNAL_SERVER_ERROR)


def _error_response(
    request: Request,
    error_code: ErrorCode,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        timestamp=datetime.now(UTC).isoformat(timespec="milliseconds"),
        status=error_code.status,
        error=HTTPStatus(error_code.status).name,
        code=error_code.code,
        reason=error_code.reason,
        message=error_code.message,
        details=details or [],
        correlation_id=request.headers.get("X-Correlation-Id"),
        path=request.url.path,
    )
    return JSONResponse(status_code=error_code.status, content=body.model_dump(by_alias=True))


def _field_name(location: Any) -> str | None:
    if not isinstance(location, list | tuple):
        return None

    meaningful_parts = [str(part) for part in location if part not in {"body", "query", "path"}]
    if not meaningful_parts:
        return None
    return ".".join(meaningful_parts)
