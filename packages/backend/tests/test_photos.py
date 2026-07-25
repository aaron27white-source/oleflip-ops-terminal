"""Tier 4 — inventory photos. Uploads are redirected to a temp dir; real images
are generated with Pillow so processing (resize/re-encode) actually runs."""

import io

import pytest
from PIL import Image

from app.config import settings
from app.storage import storage


@pytest.fixture(autouse=True)
def _tmp_uploads(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "base", tmp_path / "uploads")
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))


def _png(color=(120, 120, 120), size=(60, 40)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def _item(client) -> int:
    return client.post("/api/inventory", json={"title": "cam item", "buy_price": 10}).json()["id"]


def test_upload_photo(client):
    iid = _item(client)
    r = client.post(f"/api/inventory/{iid}/photos", files=[("files", ("a.png", _png(), "image/png"))])
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    p = body["items"][0]
    assert p["is_primary"] == 1          # first photo becomes the cover
    assert p["url"].startswith(f"/uploads/{iid}/")
    assert p["width"] == 60 and p["height"] == 40


def test_upload_too_many_photos(client):
    iid = _item(client)
    files = [("files", (f"{i}.png", _png(), "image/png")) for i in range(7)]
    assert client.post(f"/api/inventory/{iid}/photos", files=files).status_code == 422


def test_upload_non_image(client):
    iid = _item(client)
    r = client.post(f"/api/inventory/{iid}/photos", files=[("files", ("a.txt", b"hi", "text/plain"))])
    assert r.status_code == 400


def test_delete_photo(client):
    iid = _item(client)
    up = client.post(f"/api/inventory/{iid}/photos", files=[("files", ("a.png", _png(), "image/png"))]).json()
    pid = up["items"][0]["id"]
    assert client.delete(f"/api/inventory/{iid}/photos/{pid}").status_code == 200
    assert client.get(f"/api/inventory/{iid}/photos").json()["total"] == 0


def test_set_primary_photo(client):
    iid = _item(client)
    up = client.post(
        f"/api/inventory/{iid}/photos",
        files=[("files", ("a.png", _png(), "image/png")),
               ("files", ("b.png", _png((10, 10, 10)), "image/png"))],
    ).json()
    second = up["items"][1]["id"]
    body = client.patch(f"/api/inventory/{iid}/photos/{second}/primary").json()
    primary = [p for p in body["items"] if p["is_primary"] == 1]
    assert len(primary) == 1 and primary[0]["id"] == second


def test_photos_cascade_on_item_delete(client):
    iid = _item(client)
    client.post(f"/api/inventory/{iid}/photos", files=[("files", ("a.png", _png(), "image/png"))])
    client.delete(f"/api/inventory/{iid}")
    assert client.get(f"/api/inventory/{iid}/photos").json()["total"] == 0
