"""price_service.py — refresh part prices from eBay sold comps, and report
staleness. Reuses Phase 1's refresh_part for insert/dedup, and feeds eBay
creds from settings rather than process env vars — so the same .env that
configures the backend also configures the fetchers.

Sources:
  - rapidapi: works today (RapidAPI 'ebay-average-selling-price' by ecommet).
    POST /findCompletedItems with a JSON body; response has a `products` array.
    Needs EBAY_RAPIDAPI_KEY/HOST. Free tier is rate-limited (429s on rapid
    calls) — refresh_comps sleeps between parts.
  - api: official Marketplace Insights, pending eBay approval. Needs
    EBAY_CLIENT_ID/SECRET.
  - scrape: eBay's bot wall blocks this (kept for parity; will usually error).
"""

import time
from datetime import datetime

from app.config import settings
from app.errors import ApiError
from models.part import search_parts

REQUEST_TIMEOUT = 30
RAPIDAPI_DELAY_SECONDS = 1.5  # spacing between parts to respect the free-tier rate limit


def _parse_ebay_date(text: str | None) -> str | None:
    """'Jul 20, 2026' -> '2026-07-20'; None/unparseable -> None."""
    if not text:
        return None
    try:
        return datetime.strptime(text.strip(), "%b %d, %Y").date().isoformat()
    except ValueError:
        return None


def _rapidapi_fetch(query: str, *, post=None) -> list[dict]:
    """Fetch sold comps from the ebay-average-selling-price RapidAPI (POST) and
    map its `products` into the internal {title, price, url, sold_date} shape.
    `post` is injectable so tests run offline."""
    host = settings.ebay_rapidapi_host
    url = f"https://{host}/findCompletedItems"
    headers = {
        "Content-Type": "application/json",
        "X-RapidAPI-Key": settings.ebay_rapidapi_key,
        "X-RapidAPI-Host": host,
    }
    body = {"keywords": query, "max_search_results": "60", "site_id": "0", "remove_outliers": True}

    if post is None:
        import requests

        def post(u, h, b):
            r = requests.post(u, headers=h, json=b, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            return r.json()

    data = post(url, headers, body)
    out = []
    for p in (data.get("products") or []):
        price = p.get("sale_price")
        link = (p.get("link") or "").split("?")[0]
        if not price or price <= 0 or not link:
            continue
        out.append({
            "title": p.get("title") or "",
            "price": float(price),
            "url": link,
            "sold_date": _parse_ebay_date(p.get("date_sold")),
        })
    return out


def _targets(conn, keyword: str | None, refresh_all: bool, limit: int):
    if refresh_all:
        rows = conn.execute(
            "SELECT part_id, query FROM part_queries ORDER BY part_id LIMIT ?", (limit,)
        ).fetchall()
        return [(r["part_id"], r["query"]) for r in rows]
    matches = search_parts(conn, keyword or "")
    if not matches:
        return []
    ids = [p["id"] for p in matches[:limit]]
    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"SELECT part_id, query FROM part_queries WHERE part_id IN ({placeholders})", ids
    ).fetchall()
    return [(r["part_id"], r["query"]) for r in rows]


def _fetcher(source: str):
    """Return a function query -> normalized listings, with creds from settings."""
    from scanner.ebay_comps import normalize_listings

    if source == "rapidapi":
        if not settings.ebay_rapidapi_key or not settings.ebay_rapidapi_host:
            raise ApiError(
                400, "ebay_rapidapi_missing",
                "eBay RapidAPI price refresh needs EBAY_RAPIDAPI_KEY and "
                "EBAY_RAPIDAPI_HOST set on the server (see README).",
            )
        return lambda q: _rapidapi_fetch(q)

    if source == "api":
        from scanner.ebay_api import fetch_comps_via_api

        if not settings.ebay_client_id or not settings.ebay_client_secret:
            raise ApiError(
                400, "ebay_api_missing",
                "Official eBay API refresh needs EBAY_CLIENT_ID and "
                "EBAY_CLIENT_SECRET (Marketplace Insights approval required).",
            )
        return lambda q: normalize_listings(
            fetch_comps_via_api(q, token_kwargs={
                "client_id": settings.ebay_client_id,
                "client_secret": settings.ebay_client_secret,
            })
        )

    # scrape fallback (eBay bot wall usually blocks this)
    from scanner.ebay_comps import fetch_html, parse_sold_listings

    return lambda q: parse_sold_listings(fetch_html(_scrape_url(q)))


def _scrape_url(query: str) -> str:
    from scanner.ebay_comps import build_search_url

    return build_search_url(query)


def refresh_comps(conn, keyword: str | None, refresh_all: bool,
                  source: str = "rapidapi", dry_run: bool = False, limit: int = 25) -> dict:
    from scanner.ebay_comps import refresh_part

    targets = _targets(conn, keyword, refresh_all, limit)
    if not targets:
        return {"results": [], "inserted": 0, "warning": f"No parts matched '{keyword}'."}

    fetch = _fetcher(source)  # raises ApiError early if creds missing
    results, warnings = [], []
    for i, (part_id, query) in enumerate(targets):
        if i and source in ("rapidapi", "api"):
            time.sleep(RAPIDAPI_DELAY_SECONDS)  # respect the free-tier rate limit
        try:
            listings = fetch(query)
            results.append(refresh_part(conn, part_id, query, listings=listings, dry_run=dry_run))
        except Exception as e:  # noqa: BLE001 — isolate per-part failures
            warnings.append(f"{part_id}: {type(e).__name__}: {e}")

    return {
        "source": source,
        "parts": len(targets),
        "inserted": sum(r["inserted"] for r in results),
        "results": results,
        "warnings": warnings,
    }


def staleness(conn) -> dict:
    """Per-part newest price date + 30-day sample count; flags parts the bid
    calculator is blind on (mirrors Phase 1's `staleness` command)."""
    rows = conn.execute(
        """
        SELECT p.id, p.name, MAX(ph.date) AS newest,
               COUNT(*) FILTER (WHERE ph.date >= date('now','-30 days')) AS samples_30d
        FROM parts p LEFT JOIN price_history ph ON ph.part_id = p.id
        GROUP BY p.id
        ORDER BY (newest IS NOT NULL), newest, p.id
        """
    ).fetchall()
    items = [dict(r) for r in rows]
    blind = sum(1 for r in items if not r["samples_30d"])
    return {"items": items, "total": len(items), "blind": blind}
