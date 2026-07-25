"""E-Inventory 📋 — ages inventory, computes the Inventory Signal + buying mode
(deterministic), and writes the inventory_kpis snapshot that E-Scanner reads next
run. The LLM adds markdown/action recommendations; the mode itself is NOT an LLM
call (the feedback loop stays deterministic)."""

from app.agents.base import BaseAgent
from app.notifications import events as notify
from app.services.inventory_suggestions_service import platform_for

STALE_DAYS = 60  # flag stock held at least this long


def _mode_for(signal_pct: float) -> str:
    # Inventory Signal thresholds (build spec Hole 2).
    if signal_pct > 80:
        return "conservative"
    if signal_pct >= 40:
        return "normal"
    return "aggressive"


def compute_stats(conn) -> dict:
    # "Held" = capital still tied up in sellable stock (not sold, not scrapped).
    held = conn.execute(
        "SELECT COALESCE(SUM(buy_price + COALESCE(buy_shipping, 0)), 0) AS value, "
        "COUNT(*) AS count FROM inventory WHERE status IN ('in_stock','listed')"
    ).fetchone()
    prev = conn.execute(
        "SELECT max_desired_value FROM inventory_kpis ORDER BY snapshot_date DESC LIMIT 1"
    ).fetchone()
    max_desired = (prev["max_desired_value"] if prev else 2000.0) or 2000.0
    value = held["value"] or 0.0
    signal = round(value / max_desired * 100, 1) if max_desired else 0.0
    sold_30 = conn.execute(
        "SELECT COUNT(*) FROM inventory WHERE status = 'sold' "
        "AND sell_date >= date('now', '-30 days')"
    ).fetchone()[0]
    denom = sold_30 + held["count"]
    return {
        "value": value,
        "count": held["count"],
        "max_desired": max_desired,
        "signal": signal,
        "mode": _mode_for(signal),
        "sell_through": round(sold_30 / denom, 3) if denom else 0.0,
    }


class EInventoryAgent(BaseAgent):
    def build_context(self, conn) -> str:
        self._stats = compute_stats(conn)
        rows = conn.execute(
            "SELECT id, COALESCE(title, machine_model, 'item') AS name, buy_price, status, "
            "CAST(julianday('now') - julianday(buy_date) AS INTEGER) AS days_held "
            "FROM inventory WHERE status IN ('in_stock','listed') ORDER BY days_held DESC LIMIT 40"
        ).fetchall()
        self._held = [dict(r) for r in rows]  # reused in apply() for suggestions
        lines = [
            f"- {r['name']}: held {r['days_held']}d, cost ${(r['buy_price'] or 0):.2f}, {r['status']}"
            for r in rows
        ]
        s = self._stats
        return (
            f"Inventory snapshot: ${s['value']:.2f} held across {s['count']} items; "
            f"signal {s['signal']}% of the ${s['max_desired']:.0f} target -> buying mode "
            f"'{s['mode']}'. 30-day sell-through {s['sell_through']}.\n"
            + ("Held items (oldest first):\n" + "\n".join(lines)
               if lines else "No items currently in stock.")
            + "\n\nFlag anything held 60+ days with a specific markdown, then give 2-3 concrete "
              "actions for the week. Be concise."
        )

    def apply(self, conn, result, context) -> str:
        s = self._stats
        conn.execute(
            "INSERT INTO inventory_kpis (snapshot_date, inventory_value, max_desired_value, "
            "signal_pct, mode, sell_through_rate) VALUES (date('now'), ?, ?, ?, ?, ?) "
            "ON CONFLICT(snapshot_date) DO UPDATE SET inventory_value = excluded.inventory_value, "
            "max_desired_value = excluded.max_desired_value, signal_pct = excluded.signal_pct, "
            "mode = excluded.mode, sell_through_rate = excluded.sell_through_rate",
            (s["value"], s["max_desired"], s["signal"], s["mode"], s["sell_through"]),
        )
        self._write_suggestions(conn)
        rec = result.text.strip().replace("\n", " ")
        return (f"Mode {s['mode']} (signal {s['signal']}%, ${s['value']:.0f} / {s['count']} held). "
                f"{rec}")[:500]

    def _write_suggestions(self, conn) -> None:
        """Persist one structured suggestion per item held STALE_DAYS+ so the
        /inventory screen can surface them. Deterministic: platform from the item's
        own words, price left NULL (never fabricated). Idempotent — clears prior
        un-applied rows and rewrites the current stale set."""
        conn.execute("DELETE FROM inventory_suggestions WHERE applied = 0")
        mode = self._stats["mode"]
        for it in getattr(self, "_held", []):
            days = it.get("days_held") or 0
            if days < STALE_DAYS:
                continue
            reasoning = (
                f"Held {days}d in '{mode}' buying mode — consider a markdown or relisting "
                f"on {platform_for(it['name'])}."
            )
            conn.execute(
                "INSERT INTO inventory_suggestions "
                "(inventory_id, suggested_price, suggested_platform, reasoning, days_held) "
                "VALUES (?, NULL, ?, ?, ?)",
                (it["id"], platform_for(it["name"]), reasoning, days),
            )
            notify.inventory_stale(
                conn,
                {"id": it["id"], "title": it["name"], "buy_price": it["buy_price"],
                 "status": it["status"]},
                days,
            )
