"""errors.py — unified error envelope: {"error": {code, message, detail}}."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(Exception):
    """Raise from services/routers for a controlled error response."""

    def __init__(self, status: int, code: str, message: str, detail=None):
        self.status = status
        self.code = code
        self.message = message
        self.detail = detail


def _envelope(code: str, message: str, detail=None) -> dict:
    return {"error": {"code": code, "message": message, "detail": detail}}


def install_error_handlers(app) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError):
        return JSONResponse(
            status_code=exc.status,
            content=_envelope(exc.code, exc.message, exc.detail),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope("http_error", str(exc.detail)),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=_envelope("validation_error", "Request failed validation", exc.errors()),
        )

    @app.exception_handler(ValueError)
    async def _value_error(_: Request, exc: ValueError):
        # Phase 1 raises ValueError for not-found/ambiguous lookups.
        return JSONResponse(status_code=422, content=_envelope("value_error", str(exc)))
