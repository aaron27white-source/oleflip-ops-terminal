"""pricing.py — per-model token pricing for agent cost accounting.

Prices are USD per 1,000,000 tokens (input, output). These drift — edit here
when a provider changes pricing. Unknown models resolve to $0 + a logged
warning (see cost_for) so a new model never crashes a run; it just shows $0
on the dashboard until its row is added.

Anthropic figures are current as of 2026-07 (Opus 4.8 $5/$25, Sonnet 5 $3/$15,
Haiku 4.5 $1/$5). DeepSeek / OpenAI / Grok rows are best-effort and flagged —
verify against each provider's pricing page before trusting the cost display.
"""

import logging

logger = logging.getLogger(__name__)

# model_id -> (input_per_mtok, output_per_mtok) in USD.
PRICE_PER_MTOK: dict[str, tuple[float, float]] = {
    # Anthropic (verified 2026-07).
    "claude-opus-4-8": (5.00, 25.00),
    "claude-opus-4-7": (5.00, 25.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
    # DeepSeek (approximate — verify at platform.deepseek.com/pricing).
    "deepseek-chat": (0.27, 1.10),
    "deepseek-reasoner": (0.55, 2.19),
    # OpenAI / Grok fallbacks (approximate — verify with the provider).
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "grok-2": (2.00, 10.00),
}


def cost_for(model: str, tokens_in: int, tokens_out: int) -> float:
    """USD cost for a call. Unknown model -> 0.0 with a warning (never raises)."""
    price = PRICE_PER_MTOK.get(model)
    if price is None:
        logger.warning("No pricing row for model %r — cost recorded as $0.", model)
        return 0.0
    in_rate, out_rate = price
    return round((tokens_in / 1_000_000) * in_rate + (tokens_out / 1_000_000) * out_rate, 6)
