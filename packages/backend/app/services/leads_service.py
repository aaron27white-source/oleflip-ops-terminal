"""leads_service.py — Source Finder: ITAD companies, university surplus
schedules, saved FB/GovDeals searches."""

from app.errors import ApiError

_FIELDS = ("kind", "name", "contact", "location", "schedule_note",
           "last_contacted", "url", "notes")


def list_leads(conn, kind: str | None) -> dict:
    if kind:
        rows = conn.execute("SELECT * FROM leads WHERE kind = ? ORDER BY name", (kind,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM leads ORDER BY kind, name").fetchall()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


def get_lead(conn, lead_id: int) -> dict:
    row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    if not row:
        raise ApiError(404, "lead_not_found", f"No lead {lead_id}.")
    return dict(row)


def create_lead(conn, data: dict) -> dict:
    cols = [f for f in _FIELDS if f in data]
    placeholders = ",".join("?" * len(cols))
    cur = conn.execute(
        f"INSERT INTO leads ({','.join(cols)}) VALUES ({placeholders})",
        [data[c] for c in cols],
    )
    conn.commit()
    return get_lead(conn, cur.lastrowid)


def update_lead(conn, lead_id: int, data: dict) -> dict:
    get_lead(conn, lead_id)
    fields = {k: v for k, v in data.items() if k in _FIELDS and v is not None}
    if fields:
        sets = ", ".join(f"{k} = ?" for k in fields)
        conn.execute(f"UPDATE leads SET {sets} WHERE id = ?", [*fields.values(), lead_id])
        conn.commit()
    return get_lead(conn, lead_id)


def delete_lead(conn, lead_id: int) -> None:
    get_lead(conn, lead_id)
    conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    conn.commit()
