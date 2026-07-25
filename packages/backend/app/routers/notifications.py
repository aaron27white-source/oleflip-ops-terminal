"""notifications.py — Tier 3 preferences, log, push registration, test send."""

from fastapi import APIRouter, Depends

from app.db import get_conn
from app.schemas.notifications import PrefUpdate, PushRegister, TestRequest
from app.security import require_api_key
from app.services import notification_service as svc

router = APIRouter(prefix="/api/notifications", tags=["notifications"])
guard = [Depends(require_api_key)]


@router.get("/prefs")
def list_prefs(conn=Depends(get_conn)):
    return svc.list_prefs(conn)


@router.patch("/prefs", dependencies=guard)
def update_pref(body: PrefUpdate, conn=Depends(get_conn)):
    return svc.update_pref(conn, body.model_dump())


@router.get("/log")
def list_log(limit: int = 50, conn=Depends(get_conn)):
    return svc.list_log(conn, limit)


@router.post("/push/register", dependencies=guard)
def register_push(body: PushRegister, conn=Depends(get_conn)):
    return svc.register_push(conn, body.model_dump())


@router.post("/test", dependencies=guard)
def send_test(body: TestRequest, conn=Depends(get_conn)):
    return svc.send_test(conn, body.channels)
