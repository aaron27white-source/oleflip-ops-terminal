"""channels.py — notification delivery mediums.

Each channel: `available()` reports whether it's configured, `send()` delivers one
message (raising on failure so the engine can log it). DB access (push
subscriptions) is passed in as a connection; channels hold no state beyond creds.
"""

import json
from datetime import datetime, timezone

import requests

# Embed colours per severity (Discord expects an int).
COLOR_GOOD = 0x3DDC97
COLOR_WARN = 0xFFCD80
COLOR_BAD = 0xFF6B6B
COLOR_INFO = 0x4F8CFF


class NotificationChannel:
    name = "base"

    def available(self) -> bool:
        return False

    def send(self, conn, title: str, body: str, data: dict | None = None) -> None:
        raise NotImplementedError


class DiscordChannel(NotificationChannel):
    name = "discord"

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def available(self) -> bool:
        return bool(self.webhook_url)

    def send(self, conn, title: str, body: str, data: dict | None = None) -> None:
        color = (data or {}).get("color", COLOR_INFO)
        resp = requests.post(
            self.webhook_url,
            json={
                "embeds": [{
                    "title": title[:256],
                    "description": body[:4000],
                    "color": color,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }]
            },
            timeout=10,
        )
        if resp.status_code >= 300:
            raise RuntimeError(f"discord {resp.status_code}: {resp.text[:200]}")


class SlackChannel(NotificationChannel):
    """Slack via an Incoming Webhook URL. Simple mrkdwn text message."""

    name = "slack"

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def available(self) -> bool:
        return bool(self.webhook_url)

    def send(self, conn, title: str, body: str, data: dict | None = None) -> None:
        resp = requests.post(
            self.webhook_url,
            json={"text": f"*{title}*\n{body}"[:3000]},
            timeout=10,
        )
        if resp.status_code >= 300:
            raise RuntimeError(f"slack {resp.status_code}: {resp.text[:200]}")


class PushChannel(NotificationChannel):
    """Web Push (VAPID). Fans out to every stored subscription; prunes dead ones."""

    name = "push"

    def __init__(self, public_key: str, private_key: str, email: str):
        self.public_key = public_key
        self.private_key = private_key
        self.email = email

    def available(self) -> bool:
        if not (self.public_key and self.private_key):
            return False
        try:
            import pywebpush  # noqa: F401
        except ImportError:
            return False
        return True

    def send(self, conn, title: str, body: str, data: dict | None = None) -> None:
        from pywebpush import WebPushException, webpush

        subs = conn.execute("SELECT * FROM push_subscriptions").fetchall()
        if not subs:
            raise RuntimeError("no push subscriptions registered")
        payload = json.dumps({"title": title, "body": body, "url": (data or {}).get("url", "/")})
        sent = 0
        for s in subs:
            try:
                webpush(
                    subscription_info={
                        "endpoint": s["endpoint"],
                        "keys": {"p256dh": s["p256dh_key"], "auth": s["auth_key"]},
                    },
                    data=payload,
                    vapid_private_key=self.private_key,
                    vapid_claims={"sub": f"mailto:{self.email}"},
                )
                sent += 1
            except WebPushException as e:
                status = getattr(getattr(e, "response", None), "status_code", None)
                if status in (404, 410):  # gone — drop the dead subscription
                    conn.execute("DELETE FROM push_subscriptions WHERE id = ?", (s["id"],))
        conn.commit()
        if sent == 0:
            raise RuntimeError("push delivered to 0 subscriptions")
