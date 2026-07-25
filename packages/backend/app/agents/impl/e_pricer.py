"""E-Pricer 💰 — flags catalog parts whose 30-day average sold price diverges 10%+
from their 90-day average, and asks the LLM for a buy/hold/sell recommendation.

Deliberately does NOT auto-write price_history rows (that could pollute the bid
engine's source of truth) — it recommends; the owner acts. The recommendation is
the run record."""

from app.agents.base import BaseAgent

DIVERGENCE_PCT = 10.0


class EPricerAgent(BaseAgent):
    def build_context(self, conn) -> str:
        # Compute the 30d vs 90d windows directly from price_history — the Phase-1
        # current_prices view clamps to 30d, so its "90d" column can't show drift.
        rows = conn.execute(
            "SELECT p.name, "
            "  AVG(CASE WHEN ph.date >= date('now','-30 days') THEN ph.price END) AS avg_30d, "
            "  AVG(ph.price) AS avg_90d, "
            "  COUNT(CASE WHEN ph.date >= date('now','-30 days') THEN 1 END) AS n30 "
            "FROM price_history ph JOIN parts p ON p.id = ph.part_id "
            "WHERE ph.date >= date('now','-90 days') "
            "GROUP BY ph.part_id "
            "HAVING avg_30d IS NOT NULL AND avg_90d > 0 AND n30 > 0"
        ).fetchall()
        movers = []
        for r in rows:
            delta = (r["avg_30d"] - r["avg_90d"]) / r["avg_90d"] * 100
            if abs(delta) >= DIVERGENCE_PCT:
                movers.append((r["name"], round(r["avg_90d"], 2), round(r["avg_30d"], 2),
                               round(delta, 1), r["n30"]))
        movers.sort(key=lambda m: -abs(m[3]))
        self._movers = movers
        lines = [f"- {n}: 90d ${a90:.2f} -> 30d ${a30:.2f} ({d:+.0f}%, n={c})"
                 for n, a90, a30, d, c in movers]
        return (
            "Catalog parts whose 30-day sold price diverges 10%+ from the 90-day average:\n"
            + ("\n".join(lines) if lines else "No notable movers right now.")
            + "\n\nFor each, give a one-line buy / hold / sell call with the reason. Concise."
        )

    def apply(self, conn, result, context) -> str:
        rec = result.text.strip().replace("\n", " ")
        return f"{len(self._movers)} mover(s) flagged. {rec}"[:500]
