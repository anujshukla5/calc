"""Formula-level helpers for required good seed."""


def required_good_seed(low_weight_kg: float, low_percentage: float, good_percentage: float, specification: float) -> float:
    """Return L * (LP - S) / (S - GP), or zero when no dilution is needed."""
    if low_percentage <= specification:
        return 0.0
    if good_percentage >= low_percentage:
        raise ValueError("Good lot cannot dilute this parameter")
    denominator = specification - good_percentage
    if denominator <= 0:
        raise ValueError("No dilution path to the specification")
    return max(0.0, low_weight_kg * (low_percentage - specification) / denominator)
