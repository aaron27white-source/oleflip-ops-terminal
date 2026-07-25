"""inventory_suggestions_service.py — Tier 1 gap-fill.

Read/act on the aging-stock suggestions the E-Inventory agent writes. The agent
produces the rows (see agents/impl/e_inventory.py); this service is the read +
"mark handled" seam the /inventory screen uses.
"""

from app.errors import ApiError

# Deterministic platform hint from the item's own words — never an LLM call, so
# a suggestion can be produced without spending tokens or inventing a price.
_PLATFORM_HINTS = (
    ("ebay", ("server", "poweredge", "xeon", "cpu", "gpu", "rtx", "ram", "ssd", "nvme")),
    ("facebook", ("monitor", "desktop", "pc", "tower", "optiplex", "elitedesk")),
    ("offerup", ("phone", "iphone", "tablet", "laptop")),
)


def platform_for(text: str) -> str:
    t = (text or "").lower()
    for platform, needles in _PLATFORM_HINTS:
        if any(n in t for n in needles):
            return platform
    return "ebay"


def list_open(conn, limit: int = 50) -> dict:
    rows = conn.execute(
        "SELECT s.*, i.title, i.buy_price, i.status "
        "FROM inventory_suggestions s JOIN inventory i ON i.id = s.inventory_id "
        "WHERE s.applied = 0 ORDER BY s.days_held DESC, s.id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


def mark_applied(conn, suggestion_id: int) -> dict:
    row = conn.execute(
        "SELECT id FROM inventory_suggestions WHERE id = ?", (suggestion_id,)
    ).fetchone()
    if not row:
        raise ApiError(404, "suggestion_not_found", f"No suggestion {suggestion_id}.")
    conn.execute(
        "UPDATE inventory_suggestions SET applied = 1 WHERE id = ?", (suggestion_id,)
    )
    conn.commit()
    return {"applied": suggestion_id}
