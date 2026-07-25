"""dashboard.py — home-screen aggregate stats."""

from fastapi import APIRouter, Depends

from app.db import get_conn
from app.services import dashboard_service as svc

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
def dashboard(period: str = "month", conn=Depends(get_conn)):
    return svc.dashboard(conn, period)
