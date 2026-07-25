"""photos.py — Tier 4 inventory photo endpoints (upload / list / delete / order)."""

from fastapi import APIRouter, Depends, File, UploadFile

from app.db import get_conn
from app.schemas.photos import ReorderRequest
from app.security import require_api_key
from app.services import photo_service

router = APIRouter(prefix="/api", tags=["photos"])
guard = [Depends(require_api_key)]


@router.get("/inventory/{item_id}/photos")
def list_photos(item_id: int, conn=Depends(get_conn)):
    return photo_service.list_photos(conn, item_id)


@router.post("/inventory/{item_id}/photos", dependencies=guard)
async def upload_photos(
    item_id: int,
    files: list[UploadFile] = File(...),
    conn=Depends(get_conn),
):
    payloads = [
        {"filename": f.filename, "content_type": f.content_type, "data": await f.read()}
        for f in files
    ]
    return photo_service.upload(conn, item_id, payloads)


@router.patch("/inventory/photos/reorder", dependencies=guard)
def reorder(body: ReorderRequest, conn=Depends(get_conn)):
    return photo_service.reorder(conn, body.item_id, body.photo_ids)


@router.patch("/inventory/{item_id}/photos/{photo_id}/primary", dependencies=guard)
def set_primary(item_id: int, photo_id: int, conn=Depends(get_conn)):
    return photo_service.set_primary(conn, item_id, photo_id)


@router.delete("/inventory/{item_id}/photos/{photo_id}", dependencies=guard)
def delete_photo(item_id: int, photo_id: int, conn=Depends(get_conn)):
    photo_service.delete_photo(conn, item_id, photo_id)
    return {"deleted": photo_id}
