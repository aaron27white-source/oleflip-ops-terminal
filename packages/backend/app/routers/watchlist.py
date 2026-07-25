"""watchlist.py — watch list + bid tracking. Thin router; mutations guarded."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db import get_conn
from app.security import require_api_key
from app.services import watchlist_service as svc

router = APIRouter(prefix="/api", tags=["watchlist"])
guard = [Depends(require_api_key)]


class WatchIn(BaseModel):
    item_name: str | None = None
    url: str | None = None
    source: str | None = None
    target_price: float | None = None
    max_bid: float | None = None
    last_price_seen: float | None = None
    status: str | None = None
    notes: str | None = None


class BidIn(BaseModel):
    watched_listing_id: int | None = None
    item_name: str | None = None
    url: str | None = None
    bid_amount: float | None = None
    max_bid: float | None = None
    auction_end: str | None = None
    status: str | None = None
    result_price: float | None = None


@router.get("/watchlist")
def list_watchlist(status: str | None = None, conn=Depends(get_conn)):
    return svc.list_watchlist(conn, status)


@router.post("/watchlist", dependencies=guard)
def create_watch(body: WatchIn, conn=Depends(get_conn)):
    return svc.create_watch(conn, body.model_dump(exclude_unset=True))


@router.patch("/watchlist/{watch_id}", dependencies=guard)
def update_watch(watch_id: int, body: WatchIn, conn=Depends(get_conn)):
    return svc.update_watch(conn, watch_id, body.model_dump(exclude_unset=True))


@router.delete("/watchlist/{watch_id}", dependencies=guard)
def delete_watch(watch_id: int, conn=Depends(get_conn)):
    return svc.delete_watch(conn, watch_id)


@router.get("/bids")
def list_bids(status: str | None = None, conn=Depends(get_conn)):
    return svc.list_bids(conn, status)


@router.post("/bids", dependencies=guard)
def create_bid(body: BidIn, conn=Depends(get_conn)):
    return svc.create_bid(conn, body.model_dump(exclude_unset=True))


@router.patch("/bids/{bid_id}", dependencies=guard)
def update_bid(bid_id: int, body: BidIn, conn=Depends(get_conn)):
    return svc.update_bid(conn, bid_id, body.model_dump(exclude_unset=True))
