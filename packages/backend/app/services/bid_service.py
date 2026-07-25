"""bid_service.py — composes Phase 1's PURE calculator functions into JSON.

Critically: this imports the pure functions (compute_parts_yield,
calculate_max_bid_simple, compute_profit_projection, resolve_machine, …) and
assembles a dict. It NEVER calls run_bid/run_what_if/run_scrap — those print
for the terminal and are not an API surface. This keeps the bid math as one
source of truth (Phase 1), so the web layer can't drift from the CLI.
"""

from calculator.bid_calculator import (
    calculate_max_bid_simple,
    compute_parts_yield,
    compute_profit_projection,
    resolve_machine,
    total_shipping,
)
from calculator.scrap_calculator import calculate_scrap_bid, estimate_scrap_value
from calculator.what_if import calculate_max_bid_advanced


def calculate_bid(conn, machine: str, price: float, shipping: float = 0.0, specs: str | None = None) -> dict:
    """Structured equivalent of run_bid(). resolve_machine raises ValueError
    for not-found/ambiguous — the error handler maps that to 422 with the
    'did you mean' text preserved."""
    profile = resolve_machine(conn, machine)
    lines = compute_parts_yield(conn, profile)

    if profile["estimated_total_value"] is None:
        # Stub profile: no pricing mapped. Not an error — the UI shows an
        # amber "needs pricing" state.
        return {
            "machine": profile["model"],
            "specs": specs,
            "verdict": None,
            "warning": profile.get("notes")
            or "This machine profile has no pricing data yet — add comps before bidding.",
            "parts_value": None,
            "max_bid": None,
            "total_cost": round(price + shipping, 2),
            "projection": None,
            "lines": lines,
        }

    parts_value = round(sum(line["line_total"] for line in lines), 2)
    shipping_total = total_shipping(lines)
    projection = compute_profit_projection(parts_value, shipping_total)
    max_bid = calculate_max_bid_simple(parts_value)

    return {
        "machine": profile["model"],
        "specs": specs,
        "verdict": "BUY" if price <= max_bid else "PASS",
        "warning": None,
        "parts_value": parts_value,
        "max_bid": max_bid,
        "total_cost": round(price + shipping, 2),
        "projection": projection,
        "lines": lines,
    }


def what_if(conn, machine: str, buy_price: float, sell_discount: float = 0.0,
            shipping_override: float | None = None) -> dict:
    profile = resolve_machine(conn, machine)
    lines = compute_parts_yield(conn, profile)
    if profile["estimated_total_value"] is None:
        return {"machine": profile["model"], "verdict": None,
                "warning": "No pricing data mapped for this machine yet."}
    parts_value = round(sum(line["line_total"] for line in lines), 2)
    baseline_shipping = total_shipping(lines)
    shipping_used = shipping_override if shipping_override is not None else baseline_shipping
    baseline_max_bid = calculate_max_bid_simple(parts_value)
    adjusted_max_bid = calculate_max_bid_advanced(parts_value, sell_discount, shipping_override=shipping_used)
    return {
        "machine": profile["model"],
        "parts_value": parts_value,
        "baseline_max_bid": baseline_max_bid,
        "adjusted_max_bid": adjusted_max_bid,
        "sell_discount": sell_discount,
        "shipping_used": round(shipping_used, 2),
        "verdict": "BUY" if buy_price <= adjusted_max_bid else "PASS",
        "warning": None,
    }


def scrap(conn, count: int, price: float, shipping: float,
          expected_working_pct: float = 40.0, value_per_working: float = 40.0) -> dict:
    max_bid = calculate_scrap_bid(count, price, shipping, expected_working_pct, value_per_working)
    expected_working = count * (expected_working_pct / 100)
    return {
        "count": count,
        "total_cost": round(price + shipping, 2),
        "expected_working": round(expected_working, 1),
        "expected_value": round(estimate_scrap_value(expected_working, value_per_working), 2),
        "value_per_working": value_per_working,
        "max_bid": max_bid,
        "verdict": "BUY" if price <= max_bid else "PASS",
    }


def compare(conn, lots: list[dict]) -> dict:
    """Rank lots by total cost (cheapest first). Each lot: {name, price, shipping}."""
    ranked = sorted(
        ({"name": lot["name"], "price": lot["price"], "shipping": lot.get("shipping", 0.0),
          "total": round(lot["price"] + lot.get("shipping", 0.0), 2)} for lot in lots),
        key=lambda x: x["total"],
    )
    return {"ranked": ranked}
