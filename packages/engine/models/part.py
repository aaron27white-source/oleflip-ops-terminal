"""part.py — parts catalog lookups."""


def get_part(conn, part_id):
    """Full row for a part id, or None."""
    row = conn.execute("SELECT * FROM parts WHERE id = ?", (part_id,)).fetchone()
    return dict(row) if row else None


def search_parts(conn, keyword):
    """Token-based match, order-independent: every whitespace-separated token must
    appear (case-insensitively) somewhere across id/name/category/subcategory.
    Returns a list of dicts."""
    tokens = (keyword or "").split()
    if not tokens:
        return []
    clauses, params = [], []
    for tok in tokens:
        like = f"%{tok}%"
        clauses.append(
            "(id LIKE ? COLLATE NOCASE OR name LIKE ? COLLATE NOCASE "
            "OR category LIKE ? COLLATE NOCASE OR subcategory LIKE ? COLLATE NOCASE)"
        )
        params += [like, like, like, like]
    where = " AND ".join(clauses)
    rows = conn.execute(
        f"SELECT * FROM parts WHERE {where} ORDER BY name", params  # nosec B608 — clauses are literal ?-placeholder groups; values bound
    ).fetchall()
    return [dict(r) for r in rows]
