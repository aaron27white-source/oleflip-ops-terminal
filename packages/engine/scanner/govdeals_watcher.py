"""govdeals_watcher.py — GovDeals-style auction scanner (reference engine).

Finds auction lots, matches each to a known machine profile, and runs the match
through the bid calculator to flag good-margin lots. The live actor call needs an
Apify token + network; a `transport(url, params, body) -> [raw_lot, ...]` seam is
injectable so this runs offline (tests, or a self-hosted source). Without a token
or a transport it raises before any network call, and the backend returns a clean
400. Swap the engine (PHASE1_PATH) to plug in a live source.
"""

import os
import re
import time

from calculator.bid_calculator import calculate_max_bid_simple, compute_parts_yield
from models.machine import get_machine_profile, list_machines

APIFY_RUN_URL = (
    "https://api.apify.com/v2/acts/parseforge~govdeals-scraper/run-sync-get-dataset-items"
)
REQUEST_TIMEOUT = 60
RATE_LIMIT_SECONDS = 3


def _default_transport(url, params, json_body):
    import requests

    resp = requests.post(url, params=params, json=json_body, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def run_apify_search(search_text, *, token=None, category_ids=None, location_state=None,
                     max_items=50, transport=None):
    """Run the auction source for one saved search. Returns the raw list of lot
    dicts; map_lot() normalizes each. `transport` is injectable for offline use;
    a missing token raises before any network call."""
    token = token or os.environ.get("APIFY_API_TOKEN")
    if not token and transport is None:
        raise ValueError("auction scan needs APIFY_API_TOKEN set (or an injected transport).")
    transport = transport or _default_transport
    body = {"searchText": search_text, "maxItems": max_items}
    if category_ids:
        body["categoryIds"] = category_ids
    if location_state:
        body["locationState"] = location_state
    return transport(APIFY_RUN_URL, {"token": token}, body)


def _first_present(item, keys):
    for key in keys:
        val = item.get(key)
        if val not in (None, ""):
            return val
    return None


_QTY_PATTERNS = [
    (r"lot of\s*\(?(\d+)", lambda m: int(m.group(1))),
    (r"\bpallets?\s+of\s+(\d+)", lambda m: int(m.group(1))),
    (r"qty[:.\s]+(\d+)", lambda m: int(m.group(1))),
    (r"\b(\d+)\s*(?:units|pcs|pieces|ct)\b", lambda m: int(m.group(1))),
    (r"\((\d+)\)", lambda m: int(m.group(1))),
    (r"^(\d+)\s+(?:dell|hp|lenovo|apple|assorted|mixed|used|refurb)", lambda m: int(m.group(1))),
]


def parse_quantity(title):
    """(quantity, confident) from explicit quantity phrases only; (1, False) otherwise.
    Conservative by design — a model number like '5090' must not read as a count."""
    if not title:
        return 1, False
    t = title.lower()
    for pattern, extract in _QTY_PATTERNS:
        m = re.search(pattern, t)
        if m:
            try:
                qty = extract(m)
                if qty >= 1:
                    return qty, True
            except (ValueError, IndexError):
                continue
    return 1, False


def map_lot(raw):
    """Normalize one raw lot dict, or None if it lacks a title/price."""
    title = raw.get("title")
    if title is None:
        return None
    current_bid = _first_present(raw, ["finalPrice", "currentBid"])
    if current_bid in (None, 0, "0"):
        current_bid = _first_present(raw, ["startingBid"])
    if current_bid is None:
        return None
    try:
        current_bid = float(current_bid)
    except (TypeError, ValueError):
        return None
    auction_end = _first_present(raw, ["auctionEnd", "auctionEndUtc"])
    url = _first_present(raw, ["url", "itemUrl", "link", "assetUrl", "listingUrl"])
    lot_id = _first_present(raw, ["assetId", "id", "itemId", "lotId", "inventoryId"])
    lot_key = str(lot_id) if lot_id is not None else f"{title}|{auction_end}"
    quantity, qty_confident = parse_quantity(title)
    return {
        "title": title,
        "current_bid": current_bid,
        "bid_count": raw.get("bidCount"),
        "auction_end": auction_end,
        "location_state": raw.get("locationState"),
        "url": url,
        "lot_key": lot_key,
        "quantity": quantity,
        "quantity_confident": qty_confident,
        "is_sold": raw.get("isSold") is True,
    }


def match_machine(conn, title):
    """The known model that appears in `title` (longest match wins), or None."""
    if not title:
        return None
    low = title.lower()
    candidates = [m for m in list_machines(conn) if m.lower() in low]
    return max(candidates, key=len) if candidates else None


def evaluate_lot(conn, lot):
    """Attach a machine match + quantity-aware bid evaluation to a mapped lot."""
    qty = lot.get("quantity") or 1
    total_cost = lot["current_bid"]
    result = dict(lot, matched_model=None, priced=False, quantity=qty,
                  total_cost=total_cost, per_unit_cost=round(total_cost / qty, 2))
    model = match_machine(conn, lot["title"])
    if not model:
        return result
    result["matched_model"] = model
    profile = get_machine_profile(conn, model)
    if not profile or profile["estimated_total_value"] is None:
        return result
    parts_value = round(sum(p["line_total"] for p in compute_parts_yield(conn, profile)), 2)
    max_bid_per_unit = calculate_max_bid_simple(parts_value)
    total_max_bid = round(max_bid_per_unit * qty, 2)
    result.update(priced=True, max_bid_per_unit=max_bid_per_unit, max_bid=total_max_bid,
                  headroom=round(total_max_bid - total_cost, 2),
                  margin_good=total_cost < total_max_bid)
    return result


def _seen_key_exists(conn, source, lot_key):
    return conn.execute(
        "SELECT 1 FROM seen_lots WHERE source = ? AND lot_key = ?", (source, lot_key)
    ).fetchone() is not None


def _mark_seen(conn, source, lot_key):
    conn.execute(
        "INSERT OR IGNORE INTO seen_lots (source, lot_key, first_seen) VALUES (?, ?, date('now'))",
        (source, lot_key),
    )
    conn.commit()


def scan_watches(conn, watches, *, token=None, dry_run=False, rate_limit=RATE_LIMIT_SECONDS,
                 transport=None, source="govdeals", report=print, active_only=False):
    """Run each saved watch, map + evaluate every lot, tag is_new via seen_lots.
    Per-watch failures are reported and skipped. Returns a flat list of lots."""
    all_lots = []
    for i, watch in enumerate(watches):
        if i and rate_limit:
            time.sleep(rate_limit)
        try:
            raw_lots = run_apify_search(
                watch["search_text"], token=token,
                category_ids=watch.get("category_ids"),
                location_state=watch.get("location_state"),
                transport=transport,
            )
        except Exception as e:  # noqa: BLE001 — isolate per-watch failures
            report(f"'{watch['search_text']}': {type(e).__name__}: {e}")
            continue
        for raw in raw_lots:
            mapped = map_lot(raw)
            if mapped is None:
                continue
            if active_only and mapped.get("is_sold"):
                continue
            evaluated = evaluate_lot(conn, mapped)
            evaluated["is_new"] = not _seen_key_exists(conn, source, mapped["lot_key"])
            evaluated["watch"] = watch["search_text"]
            if not dry_run:
                _mark_seen(conn, source, mapped["lot_key"])
            all_lots.append(evaluated)
    return all_lots
