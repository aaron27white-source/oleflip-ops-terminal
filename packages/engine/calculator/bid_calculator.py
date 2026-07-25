"""bid_calculator.py — pure functions for the "should I buy this lot?" report.

Given a machine profile + its parts' current prices, estimate resale parts value
and a safe max bid. These are generic reselling heuristics (a flat marketplace
fee, per-category shipping, a fixed max-bid factor) — swap the engine to plug in
your own model.
"""

from models.machine import fuzzy_match_machine, get_machine_profile
from models.part import get_part

# Per-category shipping — mirrors the net_profit view's CASE map in schema.sql.
SHIPPING_BY_CATEGORY = {
    "RAM": 5.00, "SSD": 5.50, "CPU": 4.50, "WIFI": 4.25,
    "NIC": 7.00, "GPU": 9.00, "PSU": 12.00,
}
DEFAULT_SHIPPING = 6.00
EBAY_FEE_PERCENT = 13.25
MAX_BID_FACTOR = 0.55  # bid at most 55% of estimated parts value


def estimate_shipping(category):
    """Per-part shipping cost by category, matching the net_profit view."""
    return SHIPPING_BY_CATEGORY.get(category, DEFAULT_SHIPPING)


def resolve_machine(conn, machine_query):
    """Resolve a machine name to an exact profile, or raise ValueError with
    suggestions (the API maps that to a 422 with the 'did you mean' text)."""
    profile = get_machine_profile(conn, machine_query)
    if profile:
        return profile
    matches = fuzzy_match_machine(conn, machine_query)
    if len(matches) == 1:
        return get_machine_profile(conn, matches[0])
    if matches:
        raise ValueError(
            f"No exact match for '{machine_query}'. Did you mean: {', '.join(matches)}?"
        )
    raise ValueError(f"No machine profile found for '{machine_query}'.")


def get_unit_price(conn, part_id):
    """30-day avg price, falling back to the most recent recorded sale."""
    row = conn.execute(
        "SELECT avg_price_30d FROM current_prices WHERE part_id = ?", (part_id,)
    ).fetchone()
    if row and row["avg_price_30d"] is not None:
        return row["avg_price_30d"]
    row = conn.execute(
        "SELECT price FROM price_history WHERE part_id = ? ORDER BY date DESC, id DESC LIMIT 1",
        (part_id,),
    ).fetchone()
    return row["price"] if row else None


def compute_parts_yield(conn, profile):
    """Per-part-line breakdown: part_id, name, category, qty, unit_price, line_total."""
    lines = []
    for mp in profile["parts"]:
        part = get_part(conn, mp["part_id"])
        unit_price = get_unit_price(conn, mp["part_id"])
        qty = mp["qty"]
        lines.append({
            "part_id": mp["part_id"],
            "name": part["name"] if part else mp["part_id"],
            "category": part["category"] if part else None,
            "qty": qty,
            "unit_price": unit_price,
            "line_total": round((unit_price or 0) * qty, 2),
        })
    return lines


def total_shipping(parts_yield_lines):
    """Sum of each part line's per-category shipping cost."""
    return round(sum(estimate_shipping(line["category"]) for line in parts_yield_lines), 2)


def calculate_max_bid_simple(parts_value):
    """Bid at most MAX_BID_FACTOR of estimated parts value."""
    return round(parts_value * MAX_BID_FACTOR, 2)


def compute_profit_projection(parts_value, shipping_total, fee_percent=EBAY_FEE_PERCENT):
    fees = round(parts_value * (fee_percent / 100), 2)
    net = round(parts_value - fees - shipping_total, 2)
    roi = round((net / parts_value) * 100, 0) if parts_value else 0
    return {"gross": parts_value, "fees": fees, "shipping": shipping_total, "net": net, "roi": roi}
