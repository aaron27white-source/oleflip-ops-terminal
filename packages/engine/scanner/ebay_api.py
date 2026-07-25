"""ebay_api.py — official eBay Marketplace Insights intake (reference stub).

The real integration needs approved production credentials. Offline, this
returns no comps so the price-refresh endpoint degrades cleanly rather than
crashing. Swap the engine (PHASE1_PATH) to plug in a live client.
"""


def fetch_comps_via_api(query, *, limit=25, token=None, token_kwargs=None, search_transport=None):
    """Return raw sold-comp items for a query. Reference stub: no live creds → []."""
    return []


def map_item_sales(data):
    """Map an API response payload to raw {title, price, url, sold_date} items."""
    items = (data or {}).get("itemSales") or []
    out = []
    for it in items:
        price = (it.get("lastSoldPrice") or {}).get("value")
        if price is None:
            continue
        out.append({
            "title": it.get("title") or "",
            "price": price,
            "url": it.get("itemWebUrl") or "",
            "sold_date": it.get("lastSoldDate"),
        })
    return out
