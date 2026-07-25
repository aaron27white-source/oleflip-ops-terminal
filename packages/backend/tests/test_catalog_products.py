"""M3 — catalog (parts/machines/categories) + products."""


def test_list_parts_includes_price_summary(client):
    r = client.get("/api/parts?search=DDR4 16GB")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    assert "price" in body["items"][0]
    assert "sell_speed" in body["items"][0]


def test_part_search_is_order_independent(client):
    # Phase 1 search_parts matches tokens regardless of order.
    r = client.get("/api/parts?search=16GB DDR4")
    assert any("DDR4" in p["name"] for p in r.json()["items"])


def test_machines_autocomplete(client):
    r = client.get("/api/machines?search=OptiPlex")
    assert r.status_code == 200
    assert any("OptiPlex" in m for m in r.json()["items"])


def test_machine_profile_detail(client):
    r = client.get("/api/machines/OptiPlex 7080")
    assert r.status_code == 200
    assert r.json()["model"] == "OptiPlex 7080"
    assert "parts" in r.json()


def test_categories_seeded(client):
    r = client.get("/api/categories")
    names = {c["name"] for c in r.json()["items"]}
    assert "Phones" in names


def test_product_crud(client):
    cats = client.get("/api/categories").json()["items"]
    phones = next(c for c in cats if c["name"] == "Phones")
    created = client.post("/api/products", json={
        "category_id": phones["id"], "brand": "Apple", "model": "iPhone 12",
        "specs": {"storage": "128GB"}, "condition_tiers": ["Good", "Fair"],
    })
    assert created.status_code == 200
    pid = created.json()["id"]
    assert created.json()["specs"] == {"storage": "128GB"}

    got = client.get(f"/api/products/{pid}")
    assert got.json()["model"] == "iPhone 12"

    listed = client.get("/api/products?search=iPhone 12")
    assert listed.json()["total"] >= 1

    deleted = client.delete(f"/api/products/{pid}")
    assert deleted.status_code == 200
    assert client.get(f"/api/products/{pid}").status_code == 404
