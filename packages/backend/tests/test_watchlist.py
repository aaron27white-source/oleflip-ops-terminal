"""Sprint 2 — watch list + bid tracking CRUD."""


def test_watchlist_crud(client):
    created = client.post("/api/watchlist", json={
        "item_name": "Dell R740 lot", "url": "https://govdeals.com/x",
        "target_price": 300, "max_bid": 350, "source": "GovDeals",
    }).json()
    wid = created["id"]
    assert created["status"] == "active" and created["item_name"] == "Dell R740 lot"

    listed = client.get("/api/watchlist").json()
    assert listed["total"] == 1

    updated = client.patch(f"/api/watchlist/{wid}", json={"status": "won", "last_price_seen": 320}).json()
    assert updated["status"] == "won" and updated["last_price_seen"] == 320

    assert client.get("/api/watchlist?status=active").json()["total"] == 0

    assert client.request("DELETE", f"/api/watchlist/{wid}").json() == {"deleted": wid}
    assert client.get("/api/watchlist").json()["total"] == 0


def test_watchlist_requires_item_name(client):
    assert client.post("/api/watchlist", json={"target_price": 10}).status_code == 422


def test_bids_and_win_rate(client):
    b = client.post("/api/bids", json={"item_name": "OptiPlex 7080 x5", "bid_amount": 120,
                                       "max_bid": 150}).json()
    assert b["status"] == "active"

    bids = client.get("/api/bids").json()
    assert bids["total"] == 1 and bids["win_rate"] is None  # nothing decided yet

    client.patch(f"/api/bids/{b['id']}", json={"status": "won", "result_price": 120})
    assert client.get("/api/bids").json()["win_rate"] == 1.0


def test_bid_requires_amount(client):
    assert client.post("/api/bids", json={"item_name": "x"}).status_code == 422
