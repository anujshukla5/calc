"""Report data helpers."""

from .blend_engine import BlendResult


def result_summary(result: BlendResult) -> dict:
    return {"required_good_kg": result.required_good_kg, "controlling_parameter": result.controlling_parameter, "overall_pass": result.overall_pass}
