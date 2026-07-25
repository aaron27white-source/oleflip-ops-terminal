"""E-Listings 📦 — on-demand. Drafts a complete eBay listing for an item, taken
from params['inventory_id'] (an inventory row) or params['specs'] (free text).
Returns the draft; the owner posts it."""

from app.agents.base import BaseAgent


class EListingsAgent(BaseAgent):
    def build_context(self, conn) -> str:
        specs = str(self.params.get("specs") or "").strip()
        inv_id = self.params.get("inventory_id")
        if inv_id and not specs:
            row = conn.execute(
                "SELECT title, machine_model, condition, notes FROM inventory WHERE id = ?",
                (inv_id,),
            ).fetchone()
            if row:
                specs = (f"{row['title'] or row['machine_model'] or 'item'} | "
                         f"condition: {row['condition'] or 'used'} | {row['notes'] or ''}")
        self._specs = specs
        if not specs:
            return ("No item specs or inventory_id provided. Reply briefly that an item is needed "
                    "before a listing can be drafted.")
        return (
            "Write a complete eBay listing for this item:\n"
            f"{specs}\n\n"
            "Return: an 80-char keyword-rich title; a 3-5 sentence honest description; item "
            "specifics (brand / type / capacity / condition); and a suggested Buy-It-Now price. "
            "Plain, real-seller voice."
        )

    def apply(self, conn, result, context) -> str:
        if not self._specs:
            return "No item provided — nothing drafted."
        return f"Listing draft: {result.text.strip().replace(chr(10), ' ')}"[:500]
