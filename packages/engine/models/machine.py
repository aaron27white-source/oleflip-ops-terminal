"""machine.py — machine profile lookups (machines + machine_parts)."""


def get_machine_profile(conn, model):
    """Full profile for an exact model name (plus a `parts` list of
    {part_id, qty}), or None."""
    row = conn.execute("SELECT * FROM machines WHERE model = ?", (model,)).fetchone()
    if not row:
        return None
    profile = dict(row)
    parts = conn.execute(
        "SELECT part_id, qty FROM machine_parts WHERE model = ? ORDER BY part_id",
        (model,),
    ).fetchall()
    profile["parts"] = [dict(p) for p in parts]
    return profile


def fuzzy_match_machine(conn, query):
    """Case-insensitive partial match on model name. Returns a list of model names."""
    rows = conn.execute(
        "SELECT model FROM machines WHERE model LIKE ? COLLATE NOCASE ORDER BY model",
        (f"%{query}%",),
    ).fetchall()
    return [r["model"] for r in rows]


def list_machines(conn):
    """All machine model names, sorted."""
    rows = conn.execute("SELECT model FROM machines ORDER BY model").fetchall()
    return [r["model"] for r in rows]
