"""ITAD CRM — companies, call logs, purchases, summary view."""


def _make_company(client, name="Houston ITAD Co", **extra):
    return client.post("/api/itad/companies", json={"name": name, "city": "Houston", **extra}).json()


def test_create_and_get_company(client):
    created = _make_company(client, sells_singles=True, typical_bare_price=45)
    cid = created["company"]["id"]
    assert created["company"]["status"] == "not-contacted"
    assert created["company"]["sells_singles"] is True  # int -> bool round-trip

    got = client.get(f"/api/itad/companies/{cid}")
    assert got.status_code == 200
    body = got.json()
    assert body["company"]["name"] == "Houston ITAD Co"
    assert body["calls"] == [] and body["purchases"] == []
    assert body["company"]["call_count"] == 0  # from the summary view


def test_duplicate_name_is_conflict(client):
    _make_company(client, name="Dup ITAD")
    r = client.post("/api/itad/companies", json={"name": "Dup ITAD"})
    assert r.status_code == 409


def test_logging_a_call_promotes_status(client):
    cid = _make_company(client, name="CallMe ITAD")["company"]["id"]
    res = client.post(f"/api/itad/companies/{cid}/calls", json={
        "notes": "Spoke with warehouse, has ~40 OptiPlex", "spoke_with": "Mike",
        "has_inventory": True, "pricing_text": "$50 bare",
    })
    assert res.status_code == 200
    body = res.json()
    assert body["company"]["status"] == "contacted"      # not-contacted -> contacted
    assert body["company"]["call_count"] == 1
    assert body["calls"][0]["notes"].startswith("Spoke with")
    assert body["company"]["last_call_date"] is not None


def test_purchase_computes_total_and_summary(client):
    cid = _make_company(client, name="Buy ITAD")["company"]["id"]
    # total_cost omitted -> service computes qty*unit
    client.post(f"/api/itad/companies/{cid}/purchases", json={
        "model": "OptiPlex 3060", "quantity": 20, "unit_price": 45, "working_count": 18,
    })
    body = client.post(f"/api/itad/companies/{cid}/purchases", json={
        "model": "OptiPlex 7060", "quantity": 10, "unit_price": 60, "total_cost": 620, "working_count": 10,
    }).json()
    c = body["company"]
    assert c["status"] == "active"                        # a purchase => active supplier
    assert c["purchase_count"] == 2
    assert c["total_units"] == 30
    assert c["total_spent"] == 900 + 620                  # 20*45 + explicit 620
    assert c["avg_unit_price"] == 52.5                    # (45+60)/2
    assert c["win_rate_pct"] == 93                        # 28 working / 30 = 93%


def test_update_and_delete_cascades(client):
    cid = _make_company(client, name="Temp ITAD")["company"]["id"]
    client.post(f"/api/itad/companies/{cid}/calls", json={"notes": "x"})
    upd = client.patch(f"/api/itad/companies/{cid}", json={"reliability": 5, "status": "active"})
    assert upd.json()["company"]["reliability"] == 5

    assert client.delete(f"/api/itad/companies/{cid}").status_code == 200
    assert client.get(f"/api/itad/companies/{cid}").status_code == 404


def test_filters(client):
    _make_company(client, name="Dallas ITAD", city="Dallas")
    _make_company(client, name="Houston Two")
    houston = client.get("/api/itad/companies?city=Houston").json()
    assert all(c["city"] == "Houston" for c in houston["items"])
    assert any(c["name"] == "Houston Two" for c in houston["items"])


def test_bbox_filter_restricts_to_viewport(client):
    # Explicit coords bypass geocoding. Houston (TX) + Little Rock (AR) are in the
    # AR/LA/TX corridor box; NYC is far outside it.
    _make_company(client, name="Houston Geo", latitude=29.76, longitude=-95.36)
    _make_company(client, name="Little Rock Geo", city="Little Rock", latitude=34.74, longitude=-92.29)
    _make_company(client, name="NYC Geo", city="New York", latitude=40.71, longitude=-74.01)

    box = "min_lat=29&max_lat=36&min_lng=-97&max_lng=-90"
    names = {c["name"] for c in client.get(f"/api/itad/companies?{box}").json()["items"]}
    assert {"Houston Geo", "Little Rock Geo"} <= names
    assert "NYC Geo" not in names  # outside the viewport
    # Coordinates round-trip through the recreated summary view.
    hou = next(c for c in client.get(f"/api/itad/companies?{box}").json()["items"]
               if c["name"] == "Houston Geo")
    assert hou["latitude"] == 29.76 and hou["longitude"] == -95.36


def test_geocode_on_create(client, monkeypatch):
    from app.config import settings
    from app.services import itad_service

    monkeypatch.setattr(settings, "geocoding_enabled", True)
    monkeypatch.setattr(itad_service, "geocode", lambda q: (30.27, -97.74))  # pretend Austin

    body = _make_company(client, name="Geocoded ITAD", address="100 Congress Ave", city="Austin")
    assert body["company"]["latitude"] == 30.27
    assert body["company"]["longitude"] == -97.74


def test_geocode_missing_backfill(client, monkeypatch):
    from app.config import settings
    from app.services import itad_service

    # Created with geocoding off → no coords yet.
    cid = _make_company(client, name="Needs Coords", city="Shreveport")["company"]["id"]
    assert client.get(f"/api/itad/companies/{cid}").json()["company"]["latitude"] is None

    monkeypatch.setattr(settings, "geocoding_enabled", True)
    monkeypatch.setattr(itad_service, "geocode", lambda q: (32.52, -93.75))
    res = client.post("/api/itad/companies/geocode-missing")
    assert res.status_code == 200 and res.json()["geocoded"] >= 1
    assert client.get(f"/api/itad/companies/{cid}").json()["company"]["latitude"] == 32.52


def test_existing_itad_leads_are_copied(conn):
    # A kind='itad' lead seeded before migration 007 should appear as a company.
    # (Fresh test DB runs all migrations in order; simulate a pre-existing lead.)
    conn.execute("INSERT INTO leads (kind, name, contact, location) VALUES "
                 "('itad','Migrated ITAD','555-0100','Austin, TX')")
    conn.commit()
    # Re-run the copy statement (idempotent INSERT OR IGNORE) as migration 007 would:
    conn.execute("INSERT OR IGNORE INTO itad_companies (name, phone, city, notes, status) "
                 "SELECT name, contact, COALESCE(location,'Houston'), notes, 'not-contacted' "
                 "FROM leads WHERE kind='itad'")
    conn.commit()
    row = conn.execute("SELECT * FROM itad_companies WHERE name='Migrated ITAD'").fetchone()
    assert row is not None and row["phone"] == "555-0100"
