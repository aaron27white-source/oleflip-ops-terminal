"""M6 + M7 — dashboard aggregate, and scanner via an injected transport
(no network; reuses Phase 1's scan_watches transport seam)."""

from app.services import scanner_service


RAW_LOT = {
    "title": "Dell OptiPlex 7080 Desktop Computer - Used",
    "currentBid": 42.50,
    "bidCount": 3,
    "auctionEnd": "2026-07-25T18:00:00Z",
    "locationState": "TX",
    "itemId": "GD-TEST-1",
}


def _stub_transport(url, params, body):
    return [RAW_LOT]


def test_scan_persists_flagged_deal(conn):
    result = scanner_service.run_scan(conn, watch="Dell OptiPlex", transport=_stub_transport)
    assert result["scanned"] == 1
    assert result["matched"] == 1
    assert result["good"] == 1  # bid 42.50 < max 75.03
    lot = result["lots"][0]
    assert lot["matched_model"] == "OptiPlex 7080"
    assert lot["max_bid"] == 75.03

    deals = scanner_service.list_deals(conn)
    assert deals["total"] == 1
    assert deals["items"][0]["matched_model"] == "OptiPlex 7080"


def test_scan_dedups_flagged_deal_on_rerun(conn):
    scanner_service.run_scan(conn, watch="Dell OptiPlex", transport=_stub_transport)
    scanner_service.run_scan(conn, watch="Dell OptiPlex", transport=_stub_transport)
    deals = scanner_service.list_deals(conn)
    assert deals["total"] == 1  # ON CONFLICT(source, lot_key) upsert, not duplicate


def test_dashboard_endpoint(client):
    sold = client.post("/api/inventory", json={"title": "flip", "buy_price": 10}).json()
    client.patch(f"/api/inventory/{sold['id']}", json={"status": "sold", "sell_price": 40})
    r = client.get("/api/dashboard?period=all")
    assert r.status_code == 200
    body = r.json()
    assert body["profit_this_period"] == 30.0
    assert "best_deals" in body and "recent_sales" in body
    assert "staleness_warnings" in body


def test_watches_endpoint_lists_seeded_searches(client):
    r = client.get("/api/scan/govdeals/watches")
    assert r.status_code == 200
    texts = {w["search_text"] for w in r.json()["items"]}
    assert "Dell OptiPlex" in texts
