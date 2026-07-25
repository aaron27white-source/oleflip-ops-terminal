"""scrap_calculator.py — bid estimator for untested / scrap lots."""

from calculator.bid_calculator import calculate_max_bid_simple


def estimate_scrap_value(machine_count, value_per_working=40.00):
    """Expected resale value of `machine_count` working units."""
    return machine_count * value_per_working


def calculate_scrap_bid(machine_count, bid_price, shipping, expected_working_pct=40, value_per_working=40.00):
    """Max safe bid for a scrap lot given an expected working percentage."""
    expected_working = machine_count * (expected_working_pct / 100)
    expected_value = expected_working * value_per_working
    if expected_value <= 0:
        return 0
    return calculate_max_bid_simple(expected_value)
