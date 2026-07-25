"""M5 — sources (+ inline create, performance) and leads."""


def test_sources_seeded(client):
    r = client.get("/api/sources")
    names = {s["name"] for s in r.json()["items"]}
    assert "GovDeals" in names


def test_inline_create_source_is_idempotent_on_name(client):
    a = client.post("/api/sources", json={"name": "Traders Village", "type": "flea"}).json()
    b = client.post("/api/sources", json={"name": "Traders Village", "type": "flea"}).json()
    assert a["id"] == b["id"]  # inline-create doesn't duplicate


def test_source_performance_rollup(client):
    src = client.post("/api/sources", json={"name": "TestSrc", "type": "flea"}).json()
    bought = client.post("/api/inventory", json={
        "title": "flip", "buy_price": 10, "source_id": src["id"],
    }).json()
    client.patch(f"/api/inventory/{bought['id']}", json={"status": "sold", "sell_price": 40})

    perf = client.get("/api/sources/performance").json()["items"]
    row = next(p for p in perf if p["id"] == src["id"])
    assert row["items_bought"] == 1
    assert row["realized_profit"] == 30.0
    assert row["total_spend"] == 10.0


def test_lead_crud(client):
    created = client.post("/api/leads", json={
        "kind": "itad", "name": "Houston ITAD Co", "contact": "713-555-0100",
        "location": "Houston, TX",
    })
    assert created.status_code == 200
    lid = created.json()["id"]
    listed = client.get("/api/leads?kind=itad").json()
    assert any(l["id"] == lid for l in listed["items"])
    assert client.delete(f"/api/leads/{lid}").status_code == 200
