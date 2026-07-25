"""leads.py — Source Finder CRUD."""

from fastapi import APIRouter, Depends

from app.db import get_conn
from app.schemas.sources import LeadIn
from app.security import require_api_key
from app.services import leads_service as svc

router = APIRouter(prefix="/api", tags=["leads"])
guard = [Depends(require_api_key)]


@router.get("/leads")
def list_leads(kind: str | None = None, conn=Depends(get_conn)):
    return svc.list_leads(conn, kind)


@router.get("/leads/{lead_id}")
def get_lead(lead_id: int, conn=Depends(get_conn)):
    return svc.get_lead(conn, lead_id)


@router.post("/leads", dependencies=guard)
def create_lead(body: LeadIn, conn=Depends(get_conn)):
    return svc.create_lead(conn, body.model_dump())


@router.put("/leads/{lead_id}", dependencies=guard)
def update_lead(lead_id: int, body: LeadIn, conn=Depends(get_conn)):
    return svc.update_lead(conn, lead_id, body.model_dump(exclude_unset=True))


@router.delete("/leads/{lead_id}", dependencies=guard)
def delete_lead(lead_id: int, conn=Depends(get_conn)):
    svc.delete_lead(conn, lead_id)
    return {"deleted": lead_id}
