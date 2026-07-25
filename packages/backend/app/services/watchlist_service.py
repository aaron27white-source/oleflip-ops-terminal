"""watchlist_service.py — CRUD for watched_listings + bids. Same shape as the
other services (whitelisted fields, parameterized queries, commit inside)."""

from app.errors import ApiError

_WATCH_FIELDS = ("item_name", "url", "source", "target_price", "max_bid",
                 "last_price_seen", "status", "notes")
_BID_FIELDS = ("watched_listing_id", "item_name", "url", "bid_amount", "max_bid",
               "auction_end", "status", "result_price")


def _row(conn, table, row_id):
    r = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()  # nosec B608 — table is a fixed literal
    if not r:
        raise ApiError(404, "not_found", f"No {table} row {row_id}.")
    return dict(r)


# ── watched listings ─────────────────────────────────────────────────────────
def list_watchlist(conn, status: str | None = None) -> dict:
    clause, params = ("WHERE status = ?", [status]) if status else ("", [])
    rows = conn.execute(
        f"SELECT * FROM watched_listings {clause} ORDER BY updated_at DESC, id DESC", params
    ).fetchall()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


def create_watch(conn, data: dict) -> dict:
    cols = [f for f in _WATCH_FIELDS if f in data and data[f] is not None]
    if "item_name" not in cols:
        raise ApiError(422, "item_name_required", "item_name is required.")
    placeholders = ",".join("?" * len(cols))
    cur = conn.execute(
        f"INSERT INTO watched_listings ({','.join(cols)}) VALUES ({placeholders})",  # nosec B608 — cols from _WATCH_FIELDS whitelist; values bound
        [data[c] for c in cols],
    )
    conn.commit()
    return _row(conn, "watched_listings", cur.lastrowid)


def update_watch(conn, watch_id: int, data: dict) -> dict:
    _row(conn, "watched_listings", watch_id)
    fields = {k: v for k, v in data.items() if k in _WATCH_FIELDS and v is not None}
    if fields:
        sets = ", ".join(f"{k} = ?" for k in fields)
        conn.execute(
            f"UPDATE watched_listings SET {sets}, updated_at = datetime('now') WHERE id = ?",  # nosec B608 — keys from whitelist; values bound
            [*fields.values(), watch_id],
        )
        conn.commit()
    return _row(conn, "watched_listings", watch_id)


def delete_watch(conn, watch_id: int) -> dict:
    _row(conn, "watched_listings", watch_id)
    conn.execute("DELETE FROM watched_listings WHERE id = ?", (watch_id,))
    conn.commit()
    return {"deleted": watch_id}


# ── bids ─────────────────────────────────────────────────────────────────────
def list_bids(conn, status: str | None = None) -> dict:
    clause, params = ("WHERE status = ?", [status]) if status else ("", [])
    rows = conn.execute(
        f"SELECT * FROM bids {clause} ORDER BY created_at DESC, id DESC", params
    ).fetchall()
    win = conn.execute("SELECT COUNT(*) FROM bids WHERE status = 'won'").fetchone()[0]
    decided = conn.execute(
        "SELECT COUNT(*) FROM bids WHERE status IN ('won','lost','outbid')"
    ).fetchone()[0]
    return {"items": [dict(r) for r in rows], "total": len(rows),
            "win_rate": round(win / decided, 3) if decided else None}


def create_bid(conn, data: dict) -> dict:
    cols = [f for f in _BID_FIELDS if f in data and data[f] is not None]
    if "item_name" not in cols or "bid_amount" not in cols:
        raise ApiError(422, "fields_required", "item_name and bid_amount are required.")
    placeholders = ",".join("?" * len(cols))
    cur = conn.execute(
        f"INSERT INTO bids ({','.join(cols)}) VALUES ({placeholders})",  # nosec B608 — cols from _BID_FIELDS whitelist; values bound
        [data[c] for c in cols],
    )
    conn.commit()
    return _row(conn, "bids", cur.lastrowid)


def update_bid(conn, bid_id: int, data: dict) -> dict:
    _row(conn, "bids", bid_id)
    fields = {k: v for k, v in data.items() if k in _BID_FIELDS and v is not None}
    if fields:
        sets = ", ".join(f"{k} = ?" for k in fields)
        conn.execute(
            f"UPDATE bids SET {sets} WHERE id = ?",  # nosec B608 — keys from whitelist; values bound
            [*fields.values(), bid_id],
        )
        conn.commit()
    return _row(conn, "bids", bid_id)
