"""notification_service.py — Tier 3 preferences, log, push-subscription CRUD +
the test hook. Delivery itself lives in app/notifications/."""

from app.config import settings
from app.errors import ApiError
from app.notifications.engine import engine

_PREF_FIELDS = ("enabled", "min_headroom", "throttle_hours")


def list_prefs(conn) -> dict:
    rows = conn.execute(
        "SELECT * FROM notification_preferences ORDER BY event_type, channel"
    ).fetchall()
    return {
        "items": [dict(r) for r in rows],
        "channels": engine.channel_status(),
        "vapid_public_key": settings.push_vapid_public_key,  # public by design
    }


def update_pref(conn, data: dict) -> dict:
    et, ch = data["event_type"], data["channel"]
    fields = {k: data[k] for k in _PREF_FIELDS if data.get(k) is not None}
    row = conn.execute(
        "SELECT id FROM notification_preferences WHERE event_type = ? AND channel = ?", (et, ch)
    ).fetchone()
    if row:
        if fields:
            sets = ", ".join(f"{k} = ?" for k in fields)
            conn.execute(
                f"UPDATE notification_preferences SET {sets}, updated_at = datetime('now') WHERE id = ?",
                [*[int(v) if isinstance(v, bool) else v for v in fields.values()], row["id"]],
            )
    else:
        conn.execute(
            "INSERT INTO notification_preferences (event_type, channel, enabled, min_headroom, throttle_hours) "
            "VALUES (?,?,?,?,?)",
            (et, ch, int(fields.get("enabled", 1)), fields.get("min_headroom"),
             fields.get("throttle_hours", 0)),
        )
    conn.commit()
    return list_prefs(conn)


def list_log(conn, limit: int = 50) -> dict:
    rows = conn.execute(
        "SELECT * FROM notification_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


def register_push(conn, sub: dict) -> dict:
    endpoint = sub.get("endpoint")
    keys = sub.get("keys") or {}
    p256dh, auth = keys.get("p256dh"), keys.get("auth")
    if not (endpoint and p256dh and auth):
        raise ApiError(422, "bad_subscription", "Subscription needs endpoint + p256dh + auth.")
    conn.execute(
        "INSERT INTO push_subscriptions (endpoint, p256dh_key, auth_key, user_agent) VALUES (?,?,?,?) "
        "ON CONFLICT(endpoint) DO UPDATE SET p256dh_key = excluded.p256dh_key, auth_key = excluded.auth_key",
        (endpoint, p256dh, auth, sub.get("user_agent")),
    )
    conn.commit()
    return {"registered": True}


def send_test(conn, channels: list[str]) -> dict:
    return engine.send_test(conn, channels or list(engine.channels.keys()))
