"""security.py — single-user API-key gate for mutating endpoints.

If settings.api_key is empty (dev default) the gate is open. In any deployed
environment, set API_KEY; the Next.js server proxy attaches it as X-API-Key so
the key never ships to the browser bundle.
"""

from fastapi import Header

from app.config import settings
from app.errors import ApiError


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not settings.api_key:
        return  # gate disabled in dev
    if x_api_key != settings.api_key:
        raise ApiError(401, "unauthorized", "Missing or invalid API key.")
