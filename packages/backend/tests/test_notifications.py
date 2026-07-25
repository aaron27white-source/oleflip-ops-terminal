"""Tier 3 — notifications. No live network: channels are unconfigured in the test
env (Discord/push report unavailable), and dispatch logic is exercised with a
fake channel injected into the engine."""

from app.notifications import events
from app.notifications.engine import engine


class FakeChannel:
    name = "discord"

    def __init__(self):
        self.sent = []

    def available(self):
        return True

    def send(self, conn, title, body, data=None):
        self.sent.append((title, body))


def test_prefs_seeded_and_channels_reported(client):
    body = client.get("/api/notifications/prefs").json()
    ets = {p["event_type"] for p in body["items"]}
    assert {"deal_found", "daily_brief", "agent_failure"} <= ets
    assert set(body["channels"]) == {"discord", "slack", "push"}
    assert body["channels"]["discord"] is False  # no webhook in test env
    assert body["channels"]["slack"] is False


def test_update_pref_toggles(client):
    client.patch("/api/notifications/prefs",
                 json={"event_type": "deal_found", "channel": "discord", "enabled": False})
    body = client.get("/api/notifications/prefs").json()
    df = next(p for p in body["items"] if p["event_type"] == "deal_found" and p["channel"] == "discord")
    assert df["enabled"] == 0


def test_dispatch_sends_then_dedups(conn, monkeypatch):
    fake = FakeChannel()
    monkeypatch.setitem(engine.channels, "discord", fake)
    deal = {"id": 1, "lot_key": "LOT1", "matched_model": "OptiPlex 7080", "title": "t",
            "current_bid": 40, "headroom": 90, "agent_verdict": "BUY"}
    events.deal_found(conn, deal)
    assert len(fake.sent) == 1
    events.deal_found(conn, deal)          # same lot_key → deduped
    assert len(fake.sent) == 1


def test_dispatch_respects_headroom_threshold(conn, monkeypatch):
    fake = FakeChannel()
    monkeypatch.setitem(engine.channels, "discord", fake)
    events.deal_found(conn, {"id": 2, "lot_key": "LOW", "headroom": 10, "agent_verdict": "BUY",
                             "title": "x", "current_bid": 5, "matched_model": "m"})
    assert len(fake.sent) == 0  # below the 40 min_headroom for deal_found


def test_push_register(client):
    r = client.post("/api/notifications/push/register",
                    json={"endpoint": "https://push/ep1", "keys": {"p256dh": "a", "auth": "b"}})
    assert r.status_code == 200 and r.json()["registered"] is True


def test_test_endpoint_reports_unconfigured(client):
    body = client.post("/api/notifications/test", json={"channels": ["discord", "push"]}).json()
    assert body["results"]["discord"] is False
    assert "discord" in body["errors"]
