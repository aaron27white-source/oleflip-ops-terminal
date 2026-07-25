"""scanner_service.py — wraps Phase 1's GovDeals watcher and persists results.

Reuses scanner.govdeals_watcher.scan_watches (which already matches lot titles
to machine profiles and runs the bid math). After a scan, matched lots are
upserted into flagged_deals so the UI can show them without re-scanning.

The Apify token comes from settings (server-side only, never the browser).
`transport` is injectable so tests run without hitting Apify.
"""

from app.config import settings
from app.errors import ApiError


def _load_watches(conn, watch: str | None):
    if watch:
        rows = conn.execute(
            "SELECT search_text, category_ids, location_state FROM auction_watches "
            "WHERE search_text LIKE ? COLLATE NOCASE ORDER BY id",
            (f"%{watch}%",),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT search_text, category_ids, location_state FROM auction_watches ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


def _upsert_flagged(conn, lots: list[dict]) -> None:
    for lot in lots:
        if not lot.get("matched_model"):
            continue  # only persist lots we could actually evaluate
        conn.execute(
            "INSERT INTO flagged_deals (source, lot_key, title, matched_model, current_bid, "
            "max_bid, headroom, margin_good, url, quantity, per_unit_cost, max_bid_per_unit) "
            "VALUES ('govdeals',?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(source, lot_key) DO UPDATE SET current_bid=excluded.current_bid, "
            "max_bid=excluded.max_bid, headroom=excluded.headroom, "
            "margin_good=excluded.margin_good, title=excluded.title, "
            "quantity=excluded.quantity, per_unit_cost=excluded.per_unit_cost, "
            "max_bid_per_unit=excluded.max_bid_per_unit",
            (lot.get("lot_key"), lot["title"], lot["matched_model"], lot.get("current_bid"),
             lot.get("max_bid"), lot.get("headroom"), 1 if lot.get("margin_good") else 0,
             lot.get("url"), lot.get("quantity"), lot.get("per_unit_cost"),
             lot.get("max_bid_per_unit")),
        )
    conn.commit()


def run_scan(conn, watch: str | None = None, dry_run: bool = False, transport=None,
             active_only: bool = False) -> dict:
    from scanner.govdeals_watcher import scan_watches

    token = settings.apify_api_token
    if not token and transport is None:
        raise ApiError(
            400, "apify_token_missing",
            "APIFY_API_TOKEN is not set on the server — the GovDeals scan can't run.",
        )
    watches = _load_watches(conn, watch)
    if not watches:
        return {"scanned": 0, "matched": 0, "good": 0, "lots": [], "warning": "No matching saved searches."}

    warnings: list[str] = []
    lots = scan_watches(conn, watches, token=token or "test", dry_run=dry_run,
                        rate_limit=0, transport=transport, report=warnings.append,
                        active_only=active_only)
    if not dry_run:
        _upsert_flagged(conn, lots)

    matched = [lot for lot in lots if lot.get("matched_model")]
    good = [lot for lot in matched if lot.get("margin_good")]
    sold = sum(1 for lot in lots if lot.get("is_sold"))
    # good-margin first, then priced matches, then the rest
    lots.sort(key=lambda x: (not x.get("margin_good"), not x.get("priced"), not x.get("matched_model")))
    return {
        "scanned": len(lots),
        "matched": len(matched),
        "good": len(good),
        "sold": sold,
        "lots": lots,
        "warnings": warnings,
    }


def list_deals(conn, open_only: bool = True) -> dict:
    clause = "WHERE dismissed = 0" if open_only else ""
    rows = conn.execute(
        f"SELECT * FROM flagged_deals {clause} ORDER BY margin_good DESC, headroom DESC, flagged_at DESC"
    ).fetchall()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


def dismiss_deal(conn, deal_id: int) -> dict:
    row = conn.execute("SELECT * FROM flagged_deals WHERE id = ?", (deal_id,)).fetchone()
    if not row:
        raise ApiError(404, "deal_not_found", f"No flagged deal {deal_id}.")
    conn.execute("UPDATE flagged_deals SET dismissed = 1 WHERE id = ?", (deal_id,))
    conn.commit()
    return {"dismissed": deal_id}


def list_watches(conn) -> dict:
    rows = conn.execute(
        "SELECT id, search_text, category_ids, location_state FROM auction_watches ORDER BY id"
    ).fetchall()
    return {"items": [dict(r) for r in rows], "total": len(rows)}
