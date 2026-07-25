"""engine.py — routes an event to enabled channels, honoring per-preference
throttle + dedup, and logs every attempt. Never raises: a channel failure is
recorded, so an agent run or cron is never broken by a bad webhook.
"""

from app.config import settings
from app.notifications.channels import DiscordChannel, PushChannel, SlackChannel


class NotificationEngine:
    def __init__(self):
        self.channels = {
            c.name: c
            for c in (
                DiscordChannel(settings.discord_webhook_url),
                SlackChannel(settings.slack_webhook_url),
                PushChannel(
                    settings.push_vapid_public_key,
                    settings.push_vapid_private_key,
                    settings.push_vapid_email,
                ),
            )
        }

    def channel_status(self) -> dict:
        return {name: ch.available() for name, ch in self.channels.items()}

    def _log(self, conn, event, channel, title, body, dedup_key, success, error):
        conn.execute(
            "INSERT INTO notification_log (event_type, channel, title, body, dedup_key, success, error) "
            "VALUES (?,?,?,?,?,?,?)",
            (event, channel, title, body, dedup_key, 1 if success else 0, error),
        )
        conn.commit()

    def dispatch(self, conn, event, title, body, data=None, dedup_key=None, headroom=None) -> dict:
        prefs = conn.execute(
            "SELECT channel, min_headroom, throttle_hours FROM notification_preferences "
            "WHERE event_type = ? AND enabled = 1",
            (event,),
        ).fetchall()
        results: dict[str, bool] = {}
        for p in prefs:
            channel = p["channel"]
            ch = self.channels.get(channel)
            if not ch:
                continue
            # headroom threshold (deal events)
            if p["min_headroom"] is not None and headroom is not None and headroom < p["min_headroom"]:
                continue
            # dedup: never send the same keyed event twice on a channel
            if dedup_key and conn.execute(
                "SELECT 1 FROM notification_log WHERE channel = ? AND dedup_key = ? AND success = 1 LIMIT 1",
                (channel, dedup_key),
            ).fetchone():
                continue
            # throttle: at most one of this event_type per channel per N hours
            if p["throttle_hours"] and conn.execute(
                "SELECT 1 FROM notification_log WHERE event_type = ? AND channel = ? AND success = 1 "
                "AND created_at >= datetime('now', ?) LIMIT 1",
                (event, channel, f"-{p['throttle_hours']} hours"),
            ).fetchone():
                continue
            if not ch.available():
                self._log(conn, event, channel, title, body, dedup_key, False, "channel not configured")
                results[channel] = False
                continue
            try:
                ch.send(conn, title, body, data)
                self._log(conn, event, channel, title, body, dedup_key, True, None)
                results[channel] = True
            except Exception as e:  # noqa: BLE001 — a bad channel must not break the caller
                self._log(conn, event, channel, title, body, dedup_key, False, str(e)[:300])
                results[channel] = False
        return results

    def send_test(self, conn, channels: list[str]) -> dict:
        """Force a message to the named channels, ignoring prefs/throttle."""
        out = {"results": {}, "errors": {}}
        for channel in channels:
            ch = self.channels.get(channel)
            if not ch or not ch.available():
                out["results"][channel] = False
                out["errors"][channel] = "channel not configured"
                continue
            try:
                ch.send(conn, "✅ Test notification",
                        "If you can read this, Oleflip notifications are wired up.",
                        {"url": "/settings"})
                self._log(conn, "system", channel, "Test", "test", None, True, None)
                out["results"][channel] = True
            except Exception as e:  # noqa: BLE001
                self._log(conn, "system", channel, "Test", "test", None, False, str(e)[:300])
                out["results"][channel] = False
                out["errors"][channel] = str(e)[:200]
        return out


engine = NotificationEngine()
