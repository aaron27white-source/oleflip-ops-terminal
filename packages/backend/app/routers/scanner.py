"""scanner.py — GovDeals market scanner + flagged deals."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db import get_conn
from app.security import require_api_key
from app.services import scanner_service as svc

router = APIRouter(prefix="/api", tags=["scanner"])
guard = [Depends(require_api_key)]


class ScanRequest(BaseModel):
    watch: str | None = None      # a saved-search keyword; None = all
    dry_run: bool = False
    active_only: bool = False      # drop sold/completed lots (often empty — actor returns sold data)


@router.get("/scan/govdeals/watches")
def watches(conn=Depends(get_conn)):
    return svc.list_watches(conn)


@router.post("/scan/govdeals", dependencies=guard)
def scan(body: ScanRequest, conn=Depends(get_conn)):
    return svc.run_scan(conn, body.watch, body.dry_run, active_only=body.active_only)


@router.get("/deals")
def deals(open: bool = True, conn=Depends(get_conn)):
    return svc.list_deals(conn, open)


@router.patch("/deals/{deal_id}", dependencies=guard)
def dismiss(deal_id: int, conn=Depends(get_conn)):
    return svc.dismiss_deal(conn, deal_id)
