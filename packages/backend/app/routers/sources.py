"""sources.py — source tracker + performance rollup."""

from fastapi import APIRouter, Depends

from app.db import get_conn
from app.schemas.sources import SourceIn, SourceUpdate
from app.security import require_api_key
from app.services import sources_service as svc

router = APIRouter(prefix="/api", tags=["sources"])
guard = [Depends(require_api_key)]


@router.get("/sources")
def list_sources(conn=Depends(get_conn)):
    return svc.list_sources(conn)


@router.get("/sources/performance")
def performance(conn=Depends(get_conn)):
    return svc.performance(conn)


@router.post("/sources", dependencies=guard)
def create_source(body: SourceIn, conn=Depends(get_conn)):
    return svc.create_source(conn, body.name, body.type, body.reliability_score, body.notes)


@router.put("/sources/{source_id}", dependencies=guard)
def update_source(source_id: int, body: SourceUpdate, conn=Depends(get_conn)):
    return svc.update_source(conn, source_id, body.model_dump(exclude_unset=True))


@router.delete("/sources/{source_id}", dependencies=guard)
def delete_source(source_id: int, conn=Depends(get_conn)):
    svc.delete_source(conn, source_id)
    return {"deleted": source_id}
