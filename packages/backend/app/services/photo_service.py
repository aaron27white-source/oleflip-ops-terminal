"""photo_service.py — Tier 4 inventory photos.

Processing on upload: auto-rotate from EXIF, strip metadata (re-encode drops it —
privacy: no GPS leak), cap to 1920px, save JPEG. Files live under
UPLOAD_DIR/{inventory_id}/; DB rows carry order + primary flag.
"""

import io
import re
import time

from PIL import Image, ImageOps, UnidentifiedImageError

from app.config import settings
from app.errors import ApiError
from app.storage import storage

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_PER_REQUEST = 6
MAX_DIMENSION = 1920


def _require_item(conn, item_id: int) -> None:
    if not conn.execute("SELECT 1 FROM inventory WHERE id = ?", (item_id,)).fetchone():
        raise ApiError(404, "inventory_not_found", f"No inventory item {item_id}.")


def _row_to_dict(item_id: int, r) -> dict:
    d = dict(r)
    d["url"] = storage.url(f"{item_id}/{d['filename']}")
    return d


def _process(data: bytes) -> tuple[bytes, int, int]:
    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)          # honor phone orientation
        img = img.convert("RGB")                      # normalize; drops alpha/EXIF
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION)) # cap longest side, keep aspect
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=85)      # re-encode => metadata stripped
        return out.getvalue(), img.width, img.height
    except (UnidentifiedImageError, OSError) as e:
        raise ApiError(400, "bad_image", f"Could not process image: {e}") from e


def list_photos(conn, item_id: int) -> dict:
    rows = conn.execute(
        "SELECT * FROM inventory_photos WHERE inventory_id = ? ORDER BY sort_order, id", (item_id,)
    ).fetchall()
    return {"items": [_row_to_dict(item_id, r) for r in rows], "total": len(rows)}


def upload(conn, item_id: int, files: list[dict]) -> dict:
    _require_item(conn, item_id)
    if not files:
        raise ApiError(422, "no_files", "No files uploaded.")
    if len(files) > MAX_PER_REQUEST:
        raise ApiError(422, "too_many_files", f"Max {MAX_PER_REQUEST} photos per upload.")

    existing = conn.execute(
        "SELECT COUNT(*) FROM inventory_photos WHERE inventory_id = ?", (item_id,)
    ).fetchone()[0]
    if existing + len(files) > settings.max_photos_per_item:
        raise ApiError(422, "photo_limit", f"Item can hold at most {settings.max_photos_per_item} photos.")

    max_bytes = settings.max_photo_size_mb * 1024 * 1024
    limit = conn.execute(
        "SELECT COALESCE(MAX(sort_order), -1) FROM inventory_photos WHERE inventory_id = ?", (item_id,)
    ).fetchone()[0]
    created = []
    for i, f in enumerate(files):
        ctype = (f.get("content_type") or "").split(";")[0].strip()
        if ctype not in ALLOWED_TYPES:
            raise ApiError(400, "bad_type", f"Unsupported type {ctype!r} (jpeg/png/webp only).")
        data = f["data"]
        if len(data) > max_bytes:
            raise ApiError(400, "too_large", f"Each photo must be under {settings.max_photo_size_mb}MB.")
        processed, w, h = _process(data)
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", (f.get("filename") or "photo"))[:60]
        filename = f"{int(time.time() * 1000)}_{i}_{safe}.jpg"
        storage.save(f"{item_id}/{filename}", processed)
        is_primary = 1 if (existing == 0 and i == 0) else 0
        cur = conn.execute(
            "INSERT INTO inventory_photos (inventory_id, filename, original_name, file_size, "
            "width, height, sort_order, is_primary) VALUES (?,?,?,?,?,?,?,?)",
            (item_id, filename, f.get("filename"), len(processed), w, h, limit + 1 + i, is_primary),
        )
        created.append(cur.lastrowid)
    conn.commit()
    rows = conn.execute(
        f"SELECT * FROM inventory_photos WHERE id IN ({','.join('?' * len(created))})", created
    ).fetchall()
    return {"items": [_row_to_dict(item_id, r) for r in rows], "total": len(rows)}


def delete_photo(conn, item_id: int, photo_id: int) -> None:
    row = conn.execute(
        "SELECT * FROM inventory_photos WHERE id = ? AND inventory_id = ?", (photo_id, item_id)
    ).fetchone()
    if not row:
        raise ApiError(404, "photo_not_found", f"No photo {photo_id} on item {item_id}.")
    storage.delete(f"{item_id}/{row['filename']}")
    conn.execute("DELETE FROM inventory_photos WHERE id = ?", (photo_id,))
    if row["is_primary"]:  # promote the next remaining photo
        nxt = conn.execute(
            "SELECT id FROM inventory_photos WHERE inventory_id = ? ORDER BY sort_order, id LIMIT 1",
            (item_id,),
        ).fetchone()
        if nxt:
            conn.execute("UPDATE inventory_photos SET is_primary = 1 WHERE id = ?", (nxt["id"],))
    conn.commit()


def set_primary(conn, item_id: int, photo_id: int) -> dict:
    if not conn.execute(
        "SELECT 1 FROM inventory_photos WHERE id = ? AND inventory_id = ?", (photo_id, item_id)
    ).fetchone():
        raise ApiError(404, "photo_not_found", f"No photo {photo_id} on item {item_id}.")
    conn.execute("UPDATE inventory_photos SET is_primary = 0 WHERE inventory_id = ?", (item_id,))
    conn.execute("UPDATE inventory_photos SET is_primary = 1 WHERE id = ?", (photo_id,))
    conn.commit()
    return list_photos(conn, item_id)


def reorder(conn, item_id: int, photo_ids: list[int]) -> dict:
    for order, pid in enumerate(photo_ids):
        conn.execute(
            "UPDATE inventory_photos SET sort_order = ? WHERE id = ? AND inventory_id = ?",
            (order, pid, item_id),
        )
    conn.commit()
    return list_photos(conn, item_id)
