"""Marketing 📣 — weekly pricing-psychology recommendations over the current
catalog prices (BIN vs auction, price endings, seasonal timing, bundles). Writes
the recommendation as the run record; the owner acts on it."""

from app.agents.base import BaseAgent


class MarketingAgent(BaseAgent):
    def build_context(self, conn) -> str:
        rows = conn.execute(
            "SELECT p.name, cp.avg_price_30d, cp.sample_count FROM current_prices cp "
            "JOIN parts p ON p.id = cp.part_id WHERE cp.sample_count > 0 "
            "ORDER BY cp.avg_price_30d DESC LIMIT 20"
        ).fetchall()
        self._n = len(rows)
        lines = [f"- {r['name']}: ~${(r['avg_price_30d'] or 0):.2f} (n={r['sample_count']})"
                 for r in rows]
        return (
            "You advise pricing psychology for a used IT-parts reseller on eBay / Facebook.\n"
            + ("Current catalog prices:\n" + "\n".join(lines)
               if lines else "No priced parts yet — give general tactics.")
            + "\n\nRecommend: Buy-It-Now vs auction, price endings (.99 vs round), seasonal timing "
              "(back-to-school, tax season, GPU launches), and any bundle ideas. Concise, actionable."
        )

    def apply(self, conn, result, context) -> str:
        return f"Pricing tactics ({self._n} parts). {result.text.strip().replace(chr(10), ' ')}"[:500]
