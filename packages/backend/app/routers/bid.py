"""bid.py — bid calculator endpoints (the flea-market core)."""

from fastapi import APIRouter, Depends

from app.db import get_conn
from app.schemas.bid import BidRequest, CompareRequest, ScrapRequest, WhatIfRequest
from app.security import require_api_key
from app.services import bid_service

router = APIRouter(prefix="/api", tags=["bid"], dependencies=[Depends(require_api_key)])


@router.post("/bid")
def post_bid(body: BidRequest, conn=Depends(get_conn)):
    return bid_service.calculate_bid(conn, body.machine, body.price, body.shipping, body.specs)


@router.post("/what-if")
def post_what_if(body: WhatIfRequest, conn=Depends(get_conn)):
    return bid_service.what_if(conn, body.machine, body.buy_price, body.sell_discount, body.shipping_override)


@router.post("/scrap")
def post_scrap(body: ScrapRequest, conn=Depends(get_conn)):
    return bid_service.scrap(conn, body.count, body.price, body.shipping,
                             body.expected_working_pct, body.value_per_working)


@router.post("/compare")
def post_compare(body: CompareRequest, conn=Depends(get_conn)):
    return bid_service.compare(conn, [lot.model_dump() for lot in body.lots])
