"""Price-refresh endpoint: staleness, target validation, creds-missing error,
and a happy path with a stubbed rapidapi fetcher."""

import pytest

from app.config import settings


def test_staleness_endpoint(client):
    r = client.get("/api/parts/staleness")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 12  # one row per seeded part (bundled reference engine)
    assert "blind" in body
    assert "staleness" not in [i["id"] for i in body["items"]]  # not captured as a part id


def test_refresh_requires_a_target(client):
    r = client.post("/api/parts/refresh-comps", json={"all": False, "source": "rapidapi"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "target_required"


def test_refresh_rapidapi_without_creds_is_clear_error(client, monkeypatch):
    monkeypatch.setattr(settings, "ebay_rapidapi_key", "")
    monkeypatch.setattr(settings, "ebay_rapidapi_host", "")
    r = client.post("/api/parts/refresh-comps", json={"all": True, "source": "rapidapi"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "ebay_rapidapi_missing"


def test_refresh_happy_path_with_stubbed_post(conn, monkeypatch):
    # Stub the RapidAPI POST so no network is touched; supply creds.
    monkeypatch.setattr(settings, "ebay_rapidapi_key", "k")
    monkeypatch.setattr(settings, "ebay_rapidapi_host", "h.example.com")

    from app.services import price_service

    def fake_post(url, headers, body):
        assert url == "https://h.example.com/findCompletedItems"
        assert headers["X-RapidAPI-Key"] == "k"  # creds passed from settings
        assert body["keywords"]  # the part's query
        return {"products": [
            {"title": f"{body['keywords']} comp", "sale_price": 25.0,
             "link": "https://www.ebay.com/itm/999?x=1", "date_sold": "Jul 19, 2026"},
            {"title": "zero-price skip", "sale_price": 0, "link": "https://ebay.com/itm/0"},
        ]}

    # patch the module-level fetch so _fetcher's lambda picks it up
    orig = price_service._rapidapi_fetch
    monkeypatch.setattr(price_service, "_rapidapi_fetch",
                        lambda q: orig(q, post=fake_post))

    result = price_service.refresh_comps(conn, "DDR4 16GB", refresh_all=False, source="rapidapi")
    assert result["inserted"] >= 1
    assert result["parts"] >= 1


def test_ebay_date_parsing():
    from app.services.price_service import _parse_ebay_date
    assert _parse_ebay_date("Jul 20, 2026") == "2026-07-20"
    assert _parse_ebay_date("") is None
    assert _parse_ebay_date("not a date") is None
