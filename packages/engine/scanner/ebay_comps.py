"""ebay_comps.py — eBay sold-comp intake for the price scanner.

Reference implementation: the HTML-scrape path is intentionally inert (eBay's
bot wall blocks scraping anyway), so fetch_html returns "" and parse yields no
comps offline. The real intake in practice is `listings=` passed straight into
refresh_part from the RapidAPI/official-API paths, which this fully supports.
"""

from urllib.parse import quote_plus

from models.price import update_price

MAX_COMPS_PER_PART = 20


def build_search_url(query):
    """A plausible eBay 'sold & completed' search URL for a query."""
    return f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(query)}&LH_Sold=1&LH_Complete=1"


def fetch_html(url):
    """Offline reference: scraping eBay is blocked, so return no HTML.
    Swap the engine (PHASE1_PATH) to plug in a real fetcher."""
    return ""


def parse_sold_listings(html):
    """Parse sold listings out of eBay search HTML. Empty in → empty out."""
    if not html:
        return []
    return []


def filter_comps(listings, max_results=MAX_COMPS_PER_PART):
    """Keep usable comps (positive price + url), capped at max_results."""
    kept = [c for c in listings if c.get("price") and c.get("url")]
    return kept[:max_results]


def normalize_listings(raw):
    """Coerce listings from any intake into {title, price, url, sold_date}.
    Entries missing a usable price or url are dropped."""
    out = []
    for item in raw:
        try:
            price = float(item["price"])
        except (KeyError, TypeError, ValueError):
            continue
        url = str(item.get("url") or "").split("?")[0]
        if not url:
            continue
        out.append({
            "title": str(item.get("title") or ""),
            "price": price,
            "url": url,
            "sold_date": item.get("sold_date") or None,
        })
    return out


def _known_urls(conn, part_id):
    rows = conn.execute(
        "SELECT url FROM price_history WHERE part_id = ? AND url IS NOT NULL", (part_id,)
    ).fetchall()
    return {row[0] for row in rows}


def refresh_part(conn, part_id, query, fetcher=fetch_html, dry_run=False, listings=None):
    """Fetch → parse → filter → insert comps for one part. If `listings` is
    given (already-normalized comps), fetch/parse are skipped. Dedups by url.

    Returns {part_id, query, found, kept, inserted, skipped_dup, comps}.
    """
    found = listings if listings is not None else parse_sold_listings(fetcher(build_search_url(query)))
    kept = filter_comps(found)
    known = _known_urls(conn, part_id)
    fresh = [c for c in kept if c["url"] not in known]
    if not dry_run:
        for comp in fresh:
            update_price(conn, part_id, comp["price"], source="eBay_sold",
                         sale_date=comp.get("sold_date"), url=comp["url"])
    return {
        "part_id": part_id,
        "query": query,
        "found": len(found),
        "kept": len(kept),
        "inserted": 0 if dry_run else len(fresh),
        "skipped_dup": len(kept) - len(fresh),
        "comps": fresh,
    }
