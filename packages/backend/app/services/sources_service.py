"""sources_service.py — where deals come from + per-source performance."""

from app.errors import ApiError


def list_sources(conn) -> dict:
    rows = conn.execute("SELECT * FROM sources ORDER BY name").fetchall()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


def get_source(conn, source_id: int) -> dict:
    row = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
    if not row:
        raise ApiError(404, "source_not_found", f"No source {source_id}.")
    return dict(row)


def create_source(conn, name: str, type_: str, reliability_score: int = 3, notes=None) -> dict:
    existing = conn.execute("SELECT * FROM sources WHERE name = ?", (name,)).fetchone()
    if existing:
        return dict(existing)  # inline-create is idempotent on name
    cur = conn.execute(
        "INSERT INTO sources (name, type, reliability_score, notes) VALUES (?,?,?,?)",
        (name, type_, reliability_score, notes),
    )
    conn.commit()
    return get_source(conn, cur.lastrowid)


def update_source(conn, source_id: int, data: dict) -> dict:
    get_source(conn, source_id)
    fields = {k: v for k, v in data.items()
              if k in ("name", "type", "reliability_score", "notes") and v is not None}
    if fields:
        sets = ", ".join(f"{k} = ?" for k in fields)
        conn.execute(f"UPDATE sources SET {sets} WHERE id = ?", [*fields.values(), source_id])
        conn.commit()
    return get_source(conn, source_id)


def delete_source(conn, source_id: int) -> None:
    get_source(conn, source_id)
    conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))
    conn.commit()


def performance(conn) -> dict:
    """Per-source rollup from inventory_pnl: spend, realized profit, ROI, counts."""
    rows = conn.execute(
        """
        SELECT s.id, s.name, s.type, s.reliability_score,
               COUNT(i.id)                                              AS items_bought,
               COALESCE(SUM(i.buy_price + i.buy_shipping), 0)           AS total_spend,
               COALESCE(SUM(CASE WHEN i.status='sold' THEN i.net_profit END), 0) AS realized_profit,
               SUM(CASE WHEN i.status='sold' THEN 1 ELSE 0 END)         AS sold_count
        FROM sources s
        LEFT JOIN inventory_pnl i ON i.source_id = s.id
        GROUP BY s.id
        ORDER BY realized_profit DESC
        """
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        spend = d["total_spend"] or 0
        d["avg_roi_pct"] = round(100.0 * d["realized_profit"] / spend, 0) if spend else None
        out.append(d)
    return {"items": out, "total": len(out)}
