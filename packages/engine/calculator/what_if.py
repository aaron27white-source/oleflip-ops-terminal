"""what_if.py — parameterized max-bid scenario formula."""


def calculate_max_bid_advanced(parts_value, sell_discount=0, fee_percent=13.25,
                               shipping_override=None, profit_margin=0.20):
    """Max bid that still hits `profit_margin` after a sell-price discount,
    marketplace fees, and shipping. Tunable — used by the what-if tool."""
    adjusted_value = parts_value * (1 - sell_discount / 100)
    fees = adjusted_value * (fee_percent / 100)
    shipping = shipping_override if shipping_override is not None else 0.0
    profit_target = adjusted_value * profit_margin
    return round(adjusted_value - fees - shipping - profit_target, 2)
