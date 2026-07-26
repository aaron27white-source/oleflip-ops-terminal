"""itad.py — ITAD supplier CRM endpoints."""

from fastapi import APIRouter, Depends

from app.db import get_conn
from app.schemas.itad import CallIn, CompanyIn, CompanyUpdate, PurchaseIn
from app.security import require_api_key
from app.services import itad_service as svc

router = APIRouter(prefix="/api/itad", tags=["itad"])
guard = [Depends(require_api_key)]


@router.get("/companies")
def list_companies(search: str | None = None, city: str | None = None,
                   status: str | None = None, min_reliability: int | None = None,
                   min_lat: float | None = None, min_lng: float | None = None,
                   max_lat: float | None = None, max_lng: float | None = None,
                   conn=Depends(get_conn)):
    # A full bounding box (map viewport) restricts results to that area.
    bbox = None
    if None not in (min_lat, min_lng, max_lat, max_lng):
        bbox = (min_lat, min_lng, max_lat, max_lng)
    return svc.list_companies(conn, search, city, status, min_reliability, bbox=bbox)


@router.post("/companies/geocode-missing", dependencies=guard)
def geocode_missing(conn=Depends(get_conn)):
    return svc.geocode_missing(conn)


@router.get("/companies/{company_id}")
def get_company(company_id: int, conn=Depends(get_conn)):
    return svc.get_company(conn, company_id)


@router.post("/companies", dependencies=guard)
def create_company(body: CompanyIn, conn=Depends(get_conn)):
    return svc.create_company(conn, body.model_dump())


@router.patch("/companies/{company_id}", dependencies=guard)
def update_company(company_id: int, body: CompanyUpdate, conn=Depends(get_conn)):
    return svc.update_company(conn, company_id, body.model_dump(exclude_unset=True))


@router.delete("/companies/{company_id}", dependencies=guard)
def delete_company(company_id: int, conn=Depends(get_conn)):
    svc.delete_company(conn, company_id)
    return {"deleted": company_id}


@router.post("/companies/{company_id}/calls", dependencies=guard)
def log_call(company_id: int, body: CallIn, conn=Depends(get_conn)):
    return svc.log_call(conn, company_id, body.model_dump())


@router.delete("/calls/{call_id}", dependencies=guard)
def delete_call(call_id: int, conn=Depends(get_conn)):
    svc.delete_call(conn, call_id)
    return {"deleted": call_id}


@router.post("/companies/{company_id}/purchases", dependencies=guard)
def log_purchase(company_id: int, body: PurchaseIn, conn=Depends(get_conn)):
    return svc.log_purchase(conn, company_id, body.model_dump())


@router.delete("/purchases/{purchase_id}", dependencies=guard)
def delete_purchase(purchase_id: int, conn=Depends(get_conn)):
    svc.delete_purchase(conn, purchase_id)
    return {"deleted": purchase_id}
