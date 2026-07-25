"""dashboard_service.py — aggregates for the home screen."""

from app.services import inventory_service


def dashboard(conn, period: str = "month") -> dict:
    pnl = inventory_service.pnl_summary(conn, period)

    best_deals = [
        dict(r)
        for r in conn.execute(
            "SELECT * FROM flagged_deals WHERE dismissed = 0 AND margin_good = 1 "
            "ORDER BY headroom DESC LIMIT 5"
        ).fetchall()
    ]
    recent_sales = [
        dict(r)
        for r in conn.execute(
            "SELECT id, title, sell_price, sell_date, net_profit, roi_pct FROM inventory_pnl "
            "WHERE status = 'sold' ORDER BY sell_date DESC, id DESC LIMIT 5"
        ).fetchall()
    ]
    # Reuse Phase 1's staleness idea: parts with no comps in the 30-day window.
    stale = conn.execute(
        "SELECT COUNT(*) FROM parts p WHERE NOT EXISTS ("
        "  SELECT 1 FROM price_history ph WHERE ph.part_id = p.id "
        "  AND ph.date >= date('now','-30 days'))"
    ).fetchone()[0]

    return {
        "period": period,
        "profit_this_period": pnl["realized_profit"],
        "items_in_stock": pnl["by_status"].get("in_stock", 0),
        "items_listed": pnl["by_status"].get("listed", 0),
        "unrealized_cost": pnl["unrealized_cost"],
        "best_deals": best_deals,
        "recent_sales": recent_sales,
        "staleness_warnings": stale,
    }
