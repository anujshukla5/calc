"""Optimization service."""

from collections.abc import Mapping

from .blend_engine import BlendResult, ReverseBlendResult, solve_blend, solve_reverse_blend


def optimize(low_weight_kg: float, low_values: Mapping[str, object], good_values: Mapping[str, object], specifications: Mapping[str, object], foreign_weight_kg: float = 0.0, foreign_values: Mapping[str, object] | None = None, foreign_enabled: bool = False) -> BlendResult:
    return solve_blend(low_weight_kg, low_values, good_values, specifications, foreign_weight_kg, foreign_values, foreign_enabled)


def optimize_reverse(good_weight_kg: float, low_values: Mapping[str, object], good_values: Mapping[str, object], specifications: Mapping[str, object], fm_target: object = 0.0) -> ReverseBlendResult:
    return solve_reverse_blend(good_weight_kg, low_values, good_values, specifications, fm_target)
