"""catalog.py — parts, machine profiles, categories."""

from fastapi import APIRouter, Depends

from app.db import get_conn
from app.schemas.catalog import CategoryIn, MachineProfileIn, PriceRecord, RefreshCompsRequest
from app.security import require_api_key
from app.services import catalog_service as svc
from app.services import price_service

router = APIRouter(prefix="/api", tags=["catalog"])
guard = [Depends(require_api_key)]


@router.get("/parts")
def get_parts(search: str | None = None, category: str | None = None,
              limit: int = 200, conn=Depends(get_conn)):
    return svc.list_parts(conn, search, category, limit)


# NOTE: these two static paths must precede /parts/{part_id} so "staleness"
# and "refresh-comps" aren't captured as a part id.
@router.get("/parts/staleness")
def parts_staleness(conn=Depends(get_conn)):
    return price_service.staleness(conn)


@router.post("/parts/refresh-comps", dependencies=guard)
def refresh_comps(body: RefreshCompsRequest, conn=Depends(get_conn)):
    if not body.all and not body.part:
        from app.errors import ApiError
        raise ApiError(422, "target_required", "Provide `part` or set `all` to true.")
    return price_service.refresh_comps(conn, body.part, body.all, body.source,
                                       body.dry_run, body.limit)


@router.get("/parts/{part_id}")
def get_part_detail(part_id: str, conn=Depends(get_conn)):
    return svc.get_part_detail(conn, part_id)


@router.post("/parts/{part_id}/prices", dependencies=guard)
def post_price(part_id: str, body: PriceRecord, conn=Depends(get_conn)):
    return svc.record_price(conn, part_id, body.price, body.source, body.date,
                            body.condition, body.url)


@router.get("/machines")
def get_machines(search: str | None = None, conn=Depends(get_conn)):
    return svc.list_machine_profiles(conn, search)


@router.get("/machines/{model}")
def get_machine(model: str, conn=Depends(get_conn)):
    return svc.get_profile(conn, model)


@router.post("/machines", dependencies=guard)
def create_machine(body: MachineProfileIn, conn=Depends(get_conn)):
    return svc.upsert_profile(conn, body.model_dump())


@router.put("/machines/{model}", dependencies=guard)
def update_machine(model: str, body: MachineProfileIn, conn=Depends(get_conn)):
    return svc.upsert_profile(conn, body.model_dump(), existing_model=model)


@router.delete("/machines/{model}", dependencies=guard)
def remove_machine(model: str, conn=Depends(get_conn)):
    svc.delete_profile(conn, model)
    return {"deleted": model}


@router.get("/categories")
def get_categories(conn=Depends(get_conn)):
    return svc.list_categories(conn)


@router.post("/categories", dependencies=guard)
def create_category(body: CategoryIn, conn=Depends(get_conn)):
    return svc.create_category(conn, body.name, body.icon, body.parent_id, body.sort_order)


@router.delete("/categories/{cat_id}", dependencies=guard)
def delete_category(cat_id: int, conn=Depends(get_conn)):
    svc.delete_category(conn, cat_id)
    return {"deleted": cat_id}
