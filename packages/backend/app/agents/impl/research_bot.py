"""Research Bot 🔬 — produces weekly market-intel signals into intel_board, which
E-Scanner reads before scanning and the Auditor reads before evaluating.

Sprint 3 uses the model's own market knowledge over the live catalog categories
(a deterministic fetch list can be added later — build spec §5). Re-running in the
same week replaces that week's still-unconsumed signals, so it's idempotent."""

from app.agents.base import BaseAgent
from app.agents.util import extract_json, week_start


class ResearchBotAgent(BaseAgent):
    def build_context(self, conn) -> str:
        self._week = week_start()
        cats = [r[0] for r in conn.execute(
            "SELECT DISTINCT category FROM parts WHERE category IS NOT NULL ORDER BY category")]
        return (
            "You track the used IT-parts / electronics resale market for a reseller.\n"
            f"Catalog categories in play: {', '.join(cats) or 'RAM, SSD, CPU, GPU'}.\n"
            "Produce 3-6 concrete current market signals a reseller should act on this week. "
            'Return ONLY a JSON array of {"category":"price_drop|new_gen|new_product|business",'
            '"subject":"<short>","signal":"<one line>","action":"<routed hint, '
            'e.g. e-pricer: refresh DDR4>","confidence":"high|med|low"}.'
        )

    def apply(self, conn, result, context) -> str:
        items = extract_json(result.text)
        if not isinstance(items, list):
            return "No parseable intel produced this run."
        # Idempotent within a week: drop this week's not-yet-consumed signals, re-write fresh.
        conn.execute("DELETE FROM intel_board WHERE week_start = ? AND consumed = 0", (self._week,))
        written = 0
        for it in items:
            if not isinstance(it, dict):
                continue
            subject = str(it.get("subject") or "")[:120]
            signal = str(it.get("signal") or "")[:300]
            if not subject or not signal:
                continue
            conn.execute(
                "INSERT INTO intel_board (category, subject, signal, action, confidence, week_start) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (str(it.get("category") or "business")[:20], subject, signal,
                 str(it.get("action") or "")[:200], str(it.get("confidence") or "")[:10],
                 self._week),
            )
            written += 1
        return f"Wrote {written} intel signal(s) for week {self._week}."
