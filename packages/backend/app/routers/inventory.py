"""inventory.py — inventory CRUD + P&L summary."""

from fastapi import APIRouter, Depends

from app.db import get_conn
from app.schemas.inventory import InventoryCreate, InventoryUpdate
from app.security import require_api_key
from app.services import inventory_service as svc
from app.services import inventory_suggestions_service as suggestions

router = APIRouter(prefix="/api", tags=["inventory"])
guard = [Depends(require_api_key)]


@router.get("/inventory")
def list_inventory(status: str | None = None, source: int | None = None, q: str | None = None,
                   limit: int = 200, offset: int = 0, conn=Depends(get_conn)):
    return svc.list_inventory(conn, status, source, q, limit, offset)


@router.get("/inventory/pnl")
def pnl(period: str = "all", conn=Depends(get_conn)):
    return svc.pnl_summary(conn, period)


@router.get("/inventory/suggestions")
def list_suggestions(conn=Depends(get_conn)):
    return suggestions.list_open(conn)


@router.patch("/inventory/suggestions/{suggestion_id}", dependencies=guard)
def apply_suggestion(suggestion_id: int, conn=Depends(get_conn)):
    return suggestions.mark_applied(conn, suggestion_id)


@router.get("/inventory/{item_id}")
def get_item(item_id: int, conn=Depends(get_conn)):
    return svc.get_item(conn, item_id)


@router.post("/inventory", dependencies=guard)
def create_item(body: InventoryCreate, conn=Depends(get_conn)):
    return svc.create_item(conn, body.model_dump())


@router.patch("/inventory/{item_id}", dependencies=guard)
def update_item(item_id: int, body: InventoryUpdate, conn=Depends(get_conn)):
    return svc.update_item(conn, item_id, body.model_dump(exclude_unset=True))


@router.delete("/inventory/{item_id}", dependencies=guard)
def delete_item(item_id: int, conn=Depends(get_conn)):
    svc.delete_item(conn, item_id)
    return {"deleted": item_id}
