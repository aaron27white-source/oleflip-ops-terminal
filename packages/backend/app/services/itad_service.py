"""itad_service.py — ITAD supplier CRM: companies, call logs, purchases.

Reads go through the itad_company_summary view so per-company stats (call
count, spend, avg unit price, win rate) are always derived, never stale.
"""

from app.errors import ApiError

_BOOL_FIELDS = ("sells_singles",)
_COMPANY_FIELDS = (
    "name", "phone", "address", "city", "state", "website", "contact_person",
    "status", "reliability", "sells_singles", "typical_bare_price",
    "typical_loaded_price", "notes",
)


def _row_to_company(row) -> dict:
    c = dict(row)
    for f in _BOOL_FIELDS:
        if f in c and c[f] is not None:
            c[f] = bool(c[f])
    return c


# ── companies ────────────────────────────────────────────────────────────────

def list_companies(conn, search=None, city=None, status=None, min_reliability=None) -> dict:
    where, params = [], []
    if search:
        where.append("(name LIKE ? OR contact_person LIKE ? OR notes LIKE ?)")
        like = f"%{search}%"
        params += [like, like, like]
    if city:
        where.append("city = ? COLLATE NOCASE")
        params.append(city)
    if status:
        where.append("status = ?")
        params.append(status)
    if min_reliability:
        where.append("reliability >= ?")
        params.append(min_reliability)
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    rows = conn.execute(
        f"SELECT * FROM itad_company_summary {clause} "
        f"ORDER BY (status='active') DESC, reliability DESC, name",
        params,
    ).fetchall()
    return {"items": [_row_to_company(r) for r in rows], "total": len(rows)}


def _summary_row(conn, company_id):
    return conn.execute(
        "SELECT * FROM itad_company_summary WHERE id = ?", (company_id,)
    ).fetchone()


def get_company(conn, company_id: int) -> dict:
    """Full detail payload for the SupplierDetail screen: company + summary,
    its calls, its purchases, and a soft inventory match by model text."""
    row = _summary_row(conn, company_id)
    if not row:
        raise ApiError(404, "company_not_found", f"No ITAD company {company_id}.")
    company = _row_to_company(row)
    calls = [dict(r) for r in conn.execute(
        "SELECT * FROM itad_call_logs WHERE company_id = ? ORDER BY call_date DESC, id DESC",
        (company_id,),
    ).fetchall()]
    purchases = [dict(r) for r in conn.execute(
        "SELECT * FROM itad_purchases WHERE company_id = ? ORDER BY purchase_date DESC, id DESC",
        (company_id,),
    ).fetchall()]
    return {"company": company, "calls": calls, "purchases": purchases}


def create_company(conn, data: dict) -> dict:
    cols = [f for f in _COMPANY_FIELDS if data.get(f) is not None]
    placeholders = ",".join("?" * len(cols))
    values = [int(data[c]) if c in _BOOL_FIELDS else data[c] for c in cols]
    try:
        cur = conn.execute(
            f"INSERT INTO itad_companies ({','.join(cols)}) VALUES ({placeholders})", values
        )
    except Exception:
        raise ApiError(409, "company_exists", f"An ITAD company named '{data.get('name')}' already exists.")
    conn.commit()
    return get_company(conn, cur.lastrowid)


def update_company(conn, company_id: int, data: dict) -> dict:
    if not _summary_row(conn, company_id):
        raise ApiError(404, "company_not_found", f"No ITAD company {company_id}.")
    fields = {f: (int(data[f]) if f in _BOOL_FIELDS else data[f])
              for f in _COMPANY_FIELDS if f in data and data[f] is not None}
    if fields:
        sets = ", ".join(f"{k} = ?" for k in fields)
        conn.execute(
            f"UPDATE itad_companies SET {sets}, updated_at = datetime('now') WHERE id = ?",
            [*fields.values(), company_id],
        )
        conn.commit()
    return get_company(conn, company_id)


def delete_company(conn, company_id: int) -> None:
    if not _summary_row(conn, company_id):
        raise ApiError(404, "company_not_found", f"No ITAD company {company_id}.")
    conn.execute("DELETE FROM itad_companies WHERE id = ?", (company_id,))  # cascades calls+purchases
    conn.commit()


# ── call logs ────────────────────────────────────────────────────────────────

def log_call(conn, company_id: int, data: dict) -> dict:
    if not _summary_row(conn, company_id):
        raise ApiError(404, "company_not_found", f"No ITAD company {company_id}.")
    conn.execute(
        "INSERT INTO itad_call_logs (company_id, call_date, spoke_with, notes, "
        "has_inventory, pricing_text, follow_up) "
        "VALUES (?, COALESCE(?, date('now')), ?, ?, ?, ?, ?)",
        (company_id, data.get("call_date"), data.get("spoke_with"), data["notes"],
         1 if data.get("has_inventory") else 0, data.get("pricing_text"), data.get("follow_up")),
    )
    # First contact promotes not-contacted -> contacted; always touch updated_at.
    conn.execute(
        "UPDATE itad_companies SET updated_at = datetime('now'), "
        "status = CASE WHEN status = 'not-contacted' THEN 'contacted' ELSE status END WHERE id = ?",
        (company_id,),
    )
    conn.commit()
    return get_company(conn, company_id)


def delete_call(conn, call_id: int) -> None:
    row = conn.execute("SELECT company_id FROM itad_call_logs WHERE id = ?", (call_id,)).fetchone()
    if not row:
        raise ApiError(404, "call_not_found", f"No call log {call_id}.")
    conn.execute("DELETE FROM itad_call_logs WHERE id = ?", (call_id,))
    conn.commit()


# ── purchases ────────────────────────────────────────────────────────────────

def log_purchase(conn, company_id: int, data: dict) -> dict:
    if not _summary_row(conn, company_id):
        raise ApiError(404, "company_not_found", f"No ITAD company {company_id}.")
    qty = data["quantity"]
    unit_price = data["unit_price"]
    total_cost = data.get("total_cost")
    if total_cost is None:
        total_cost = round(qty * unit_price, 2)
    conn.execute(
        "INSERT INTO itad_purchases (company_id, purchase_date, model, quantity, unit_price, "
        "total_cost, had_ram, had_storage, working_count, notes) "
        "VALUES (?, COALESCE(?, date('now')), ?, ?, ?, ?, ?, ?, ?, ?)",
        (company_id, data.get("purchase_date"), data.get("model"), qty, unit_price, total_cost,
         1 if data.get("had_ram") else 0, 1 if data.get("had_storage") else 0,
         data.get("working_count"), data.get("notes")),
    )
    # A purchase means they're an active supplier.
    conn.execute("UPDATE itad_companies SET status = 'active', updated_at = datetime('now') WHERE id = ?",
                 (company_id,))
    conn.commit()
    return get_company(conn, company_id)


def delete_purchase(conn, purchase_id: int) -> None:
    row = conn.execute("SELECT id FROM itad_purchases WHERE id = ?", (purchase_id,)).fetchone()
    if not row:
        raise ApiError(404, "purchase_not_found", f"No purchase {purchase_id}.")
    conn.execute("DELETE FROM itad_purchases WHERE id = ?", (purchase_id,))
    conn.commit()
