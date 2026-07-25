"""price.py — current price / net profit lookups and price updates.

Current price is always derived from recent price_history via the current_prices
view; there is no mutable "current price" column.
"""

from datetime import date


def get_current_price_summary(conn, part_id):
    """Row from the current_prices view for a part, or None if no recent sales."""
    row = conn.execute(
        "SELECT * FROM current_prices WHERE part_id = ?", (part_id,)
    ).fetchone()
    return dict(row) if row else None


def get_net_profit(conn, part_id):
    """Row from the net_profit view for a part, or None if no recent sales."""
    row = conn.execute(
        "SELECT * FROM net_profit WHERE part_id = ?", (part_id,)
    ).fetchone()
    return dict(row) if row else None


def sell_speed_label(sample_count):
    """Rough sell-speed heuristic from the 30-day sample count."""
    if not sample_count:
        return "UNKNOWN – no sales data"
    if sample_count >= 20:
        return "⚡ FAST (1-5 days)"
    if sample_count >= 5:
        return "MEDIUM (1-2 weeks)"
    return "SLOW (2+ weeks)"


def update_price(conn, part_id, price, source="manual", sale_date=None, condition="used", url=None):
    """Append a sold price to price_history."""
    sale_date = sale_date or date.today().isoformat()
    conn.execute(
        "INSERT INTO price_history (part_id, price, source, date, condition, url) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (part_id, price, source, sale_date, condition, url),
    )
    conn.commit()
