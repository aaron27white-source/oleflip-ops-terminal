"""inventory_service.py — log purchases, mark sold, derived P&L.

Reads go through the inventory_pnl view so net_profit / roi_pct are always
computed from the row, never stored stale.
"""

from app.errors import ApiError

_EDITABLE = (
    "product_id", "machine_model", "title", "condition", "buy_price", "buy_shipping",
    "buy_date", "source_id", "status", "sell_price", "sell_fees", "sell_shipping",
    "sell_date", "sold_on", "notes",
)


def _get_row(conn, item_id: int) -> dict:
    row = conn.execute("SELECT * FROM inventory_pnl WHERE id = ?", (item_id,)).fetchone()
    if not row:
        raise ApiError(404, "inventory_not_found", f"No inventory item {item_id}.")
    return dict(row)


def list_inventory(conn, status=None, source=None, q=None, limit=200, offset=0) -> dict:
    where, params = [], []
    if status:
        where.append("status = ?")
        params.append(status)
    if source:
        where.append("source_id = ?")
        params.append(source)
    if q:
        where.append("title LIKE ?")
        params.append(f"%{q}%")
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    total = conn.execute(f"SELECT COUNT(*) FROM inventory_pnl {clause}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT p.*, "
        f"(SELECT filename FROM inventory_photos ph WHERE ph.inventory_id = p.id AND ph.is_primary = 1 "
        f" LIMIT 1) AS primary_photo, "
        f"(SELECT COUNT(*) FROM inventory_photos ph WHERE ph.inventory_id = p.id) AS photo_count "
        f"FROM inventory_pnl p {clause} ORDER BY p.buy_date DESC, p.id DESC LIMIT ? OFFSET ?",
        [*params, limit, offset],
    ).fetchall()
    return {"items": [dict(r) for r in rows], "total": total}


def get_item(conn, item_id: int) -> dict:
    return _get_row(conn, item_id)


def create_item(conn, data: dict) -> dict:
    cur = conn.execute(
        "INSERT INTO inventory (product_id, machine_model, title, condition, buy_price, "
        "buy_shipping, buy_date, source_id, status, notes) "
        "VALUES (?,?,?,?,?,?,COALESCE(?, date('now')),?,'in_stock',?)",
        (data.get("product_id"), data.get("machine_model"), data["title"], data.get("condition"),
         data["buy_price"], data.get("buy_shipping", 0), data.get("buy_date"),
         data.get("source_id"), data.get("notes")),
    )
    conn.commit()
    return _get_row(conn, cur.lastrowid)


def update_item(conn, item_id: int, data: dict) -> dict:
    _get_row(conn, item_id)  # 404 if missing
    fields = {k: v for k, v in data.items() if k in _EDITABLE and v is not None}
    if not fields:
        return _get_row(conn, item_id)
    sets = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values())
    conn.execute(
        f"UPDATE inventory SET {sets}, updated_at = datetime('now') WHERE id = ?",
        [*params, item_id],
    )
    if fields.get("status") == "sold":
        conn.execute(
            "UPDATE inventory SET sell_date = COALESCE(sell_date, date('now')) WHERE id = ?",
            (item_id,),
        )
    conn.commit()
    return _get_row(conn, item_id)


def delete_item(conn, item_id: int) -> None:
    _get_row(conn, item_id)
    conn.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
    conn.commit()


def pnl_summary(conn, period: str = "all") -> dict:
    """Realized profit (sold items), unrealized cost (still held), counts."""
    period_clause = ""
    if period == "month":
        period_clause = "AND sell_date >= date('now','start of month')"
    realized = conn.execute(
        f"SELECT COALESCE(SUM(net_profit),0) FROM inventory_pnl "
        f"WHERE status = 'sold' {period_clause}"
    ).fetchone()[0]
    unrealized_cost = conn.execute(
        "SELECT COALESCE(SUM(buy_price + buy_shipping),0) FROM inventory "
        "WHERE status IN ('in_stock','listed')"
    ).fetchone()[0]
    by_status = {
        r["status"]: r["n"]
        for r in conn.execute("SELECT status, COUNT(*) n FROM inventory GROUP BY status").fetchall()
    }
    return {
        "period": period,
        "realized_profit": round(realized, 2),
        "unrealized_cost": round(unrealized_cost, 2),
        "item_count": sum(by_status.values()),
        "by_status": by_status,
    }
