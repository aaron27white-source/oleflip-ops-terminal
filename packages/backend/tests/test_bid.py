"""M2 — bid calculator parity with the engine's worked example ($75.03 on the
bundled reference seed: parts value $136.42 × the 55% max-bid rule)."""


def test_bid_optiplex_7080_is_buy_at_75_03(client):
    r = client.post("/api/bid", json={"machine": "OptiPlex 7080", "price": 55, "shipping": 30})
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] == "BUY"
    assert body["max_bid"] == 75.03  # the canary: web layer must match the engine
    assert body["total_cost"] == 85.0
    assert body["projection"]["net"] is not None
    assert len(body["lines"]) > 0


def test_bid_pass_when_price_above_max(client):
    r = client.post("/api/bid", json={"machine": "OptiPlex 7080", "price": 200})
    assert r.status_code == 200
    assert r.json()["verdict"] == "PASS"


def test_bid_stub_profile_returns_amber_not_error(client):
    # OptiPlex 3020 is a seeded stub (estimated_total_value NULL).
    r = client.post("/api/bid", json={"machine": "OptiPlex 3020", "price": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] is None
    assert body["warning"]
    assert body["max_bid"] is None


def test_bid_ambiguous_machine_is_422_with_suggestions(client):
    r = client.post("/api/bid", json={"machine": "OptiPlex", "price": 50})
    assert r.status_code == 422
    assert "error" in r.json()


def test_bid_unknown_machine_is_422(client):
    r = client.post("/api/bid", json={"machine": "Nonexistent 9999", "price": 50})
    assert r.status_code == 422


def test_scrap_endpoint(client):
    r = client.post("/api/scrap", json={"count": 10, "price": 50, "shipping": 40})
    assert r.status_code == 200
    assert "max_bid" in r.json() and "verdict" in r.json()


def test_compare_ranks_by_total(client):
    r = client.post("/api/compare", json={"lots": [
        {"name": "a", "price": 120, "shipping": 50},
        {"name": "b", "price": 50, "shipping": 40},
        {"name": "c", "price": 80, "shipping": 30},
    ]})
    ranked = r.json()["ranked"]
    assert [l["name"] for l in ranked] == ["b", "c", "a"]
