"""E-Customer 🤝 — on-demand. Drafts a tone-matched reply to a buyer message
passed as params['message']. Never auto-sends — returns a draft for the owner."""

from app.agents.base import BaseAgent


class ECustomerAgent(BaseAgent):
    def build_context(self, conn) -> str:
        msg = str(self.params.get("message") or "").strip()
        self._has_msg = bool(msg)
        if not msg:
            return ("No customer message was provided. Reply briefly that the message text is "
                    "needed before a response can be drafted.")
        return (
            "A buyer sent this message about an eBay / Facebook Marketplace order:\n"
            f'"{msg}"\n\n'
            "Draft a professional, friendly reply that protects the seller's rating and resolves "
            "the issue fast. Follow eBay's 30-day return policy (buyer pays return shipping; refund "
            "on damaged/not-working, no argument). Do NOT auto-send — this is a draft for the owner."
        )

    def apply(self, conn, result, context) -> str:
        prefix = "" if self._has_msg else "(no message provided) "
        return f"{prefix}Draft reply: {result.text.strip().replace(chr(10), ' ')}"[:500]
