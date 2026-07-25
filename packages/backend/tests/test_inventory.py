"""M4 — inventory lifecycle + derived P&L math."""


def test_log_purchase_then_mark_sold_computes_pnl(client):
    created = client.post("/api/inventory", json={
        "title": "OptiPlex 7080", "buy_price": 55, "buy_shipping": 30,
    })
    assert created.status_code == 200
    item = created.json()
    assert item["status"] == "in_stock"
    assert item["net_profit"] == -85.0  # cost only, nothing sold yet
    iid = item["id"]

    sold = client.patch(f"/api/inventory/{iid}", json={
        "status": "sold", "sell_price": 180, "sell_fees": 23.85, "sold_on": "eBay",
    })
    assert sold.status_code == 200
    s = sold.json()
    assert s["status"] == "sold"
    # 180 - 23.85 - 0 - 55 - 30 = 71.15
    assert s["net_profit"] == 71.15
    assert s["sell_date"] is not None  # auto-stamped


def test_pnl_summary_reflects_sold_and_stock(client):
    client.post("/api/inventory", json={"title": "held", "buy_price": 20})
    sold = client.post("/api/inventory", json={"title": "flip", "buy_price": 10}).json()
    client.patch(f"/api/inventory/{sold['id']}", json={"status": "sold", "sell_price": 40})

    pnl = client.get("/api/inventory/pnl?period=all").json()
    assert pnl["realized_profit"] == 30.0   # 40 - 10
    assert pnl["unrealized_cost"] == 20.0   # the held item
    assert pnl["by_status"]["sold"] == 1
    assert pnl["by_status"]["in_stock"] == 1


def test_inventory_filter_by_status(client):
    client.post("/api/inventory", json={"title": "x", "buy_price": 5})
    r = client.get("/api/inventory?status=in_stock")
    assert r.status_code == 200
    assert all(i["status"] == "in_stock" for i in r.json()["items"])


def test_delete_inventory(client):
    iid = client.post("/api/inventory", json={"title": "temp", "buy_price": 1}).json()["id"]
    assert client.delete(f"/api/inventory/{iid}").status_code == 200
    assert client.get(f"/api/inventory/{iid}").status_code == 404
