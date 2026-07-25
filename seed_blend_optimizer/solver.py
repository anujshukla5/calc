"""Blend calculation and optimization logic."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping


@dataclass(frozen=True)
class ParameterResult:
    name: str
    specification: float | None
    low_value: float
    good_value: float
    foreign_value: float
    final_value: float | None
    required_good_kg: float
    meets_specification: bool
    impossible: bool
    detail: str
    difference_from_specification: float | None = None


@dataclass(frozen=True)
class BlendResult:
    required_good_kg: int
    controlling_parameter: str
    parameters: tuple[ParameterResult, ...]
    overall_pass: bool
    low_quantity_kg: float
    foreign_quantity_kg: float
    foreign_enabled: bool


@dataclass(frozen=True)
class ReverseBlendResult:
    allowed_low_kg: int
    controlling_parameter: str
    parameters: tuple[ParameterResult, ...]
    overall_pass: bool
    good_quantity_kg: float
    outside_fm_kg: int
    fm_target: float
    alternatives: tuple["CompositionAlternative", ...] = ()


@dataclass(frozen=True)
class CompositionValue:
    name: str
    specification: float | None
    final_percentage: float | None
    final_kg: float | None
    meets_specification: bool
    compensation_low_kg: float


@dataclass(frozen=True)
class CompositionAlternative:
    controlling_parameter: str
    low_quantity_kg: int
    values: tuple[CompositionValue, ...]


def _number(value: object, default: float = 0.0) -> float:
    if value is None or str(value).strip() == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _validated_number(value: object, label: str, *, allow_blank: bool = True) -> float:
    if value is None or str(value).strip() == "":
        if allow_blank:
            return 0.0
        raise ValueError(f"{label} is required")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not 0 <= number <= 100:
        raise ValueError(f"{label} must be between 0 and 100")
    return number


def solve_blend(
    low_quantity_kg: float,
    low_values: Mapping[str, object],
    good_values: Mapping[str, object],
    specifications: Mapping[str, object],
    foreign_quantity_kg: float = 0.0,
    foreign_values: Mapping[str, object] | None = None,
    foreign_enabled: bool = False,
) -> BlendResult:
    """Find the smallest good-lot quantity satisfying every maximum spec."""
    try:
        low_quantity = float(low_quantity_kg)
    except (TypeError, ValueError) as exc:
        raise ValueError("Low lot weight must be numeric") from exc
    if low_quantity <= 0:
        raise ValueError("Low lot weight must be greater than zero")
    try:
        foreign_quantity = float(foreign_quantity_kg)
    except (TypeError, ValueError) as exc:
        raise ValueError("Foreign material weight must be numeric") from exc
    if foreign_quantity < 0:
        raise ValueError("Foreign material weight cannot be negative")
    if foreign_enabled and foreign_quantity <= 0:
        raise ValueError("Foreign material weight must be greater than zero when enabled")
    foreign_values = foreign_values or {}
    low_values = low_values or {}
    good_values = good_values or {}

    required_good = 0.0
    controlling = "None"
    results: list[ParameterResult] = []
    total_fixed = low_quantity + foreign_quantity

    for name, raw_spec in specifications.items():
        spec = None if raw_spec is None or str(raw_spec).strip() == "" else _validated_number(raw_spec, f"{name} specification")
        low_value = _validated_number(low_values.get(name), f"{name} low lot percentage")
        good_value = _validated_number(good_values.get(name), f"{name} good lot percentage")
        foreign_value = _validated_number(foreign_values.get(name), f"{name} foreign material percentage") if foreign_enabled else 0.0
        impossible = False
        needed = 0.0
        detail = "Within specification at current blend"

        if spec is None:
            final_value = None
            meets = True
            detail = "No specification entered"
        elif low_value <= spec:
            final_value = low_value
            meets = True
        elif good_value >= low_value:
            impossible = True
            final_value = None
            meets = False
            detail = "Impossible: good lot is not lower than the low lot"
        else:
            denominator = spec - good_value
            if denominator <= 0:
                impossible = True
                final_value = None
                meets = False
                detail = "Impossible: no dilution path to the maximum"
            else:
                fixed_excess = low_quantity * (low_value - spec)
                if foreign_enabled:
                    fixed_excess += foreign_quantity * (foreign_value - spec)
                needed = max(0.0, fixed_excess / denominator)
                total_weight = low_quantity + (foreign_quantity if foreign_enabled else 0.0) + needed
                final_value = (low_quantity * low_value + (foreign_quantity * foreign_value if foreign_enabled else 0.0) + needed * good_value) / total_weight
                meets = final_value <= spec + 1e-9
                detail = f"Requires {round(needed):,} kg good seed"

        if impossible:
            results.append(ParameterResult(name, spec, low_value, good_value, foreign_value, final_value, 0.0, False, True, detail))
            continue
        if needed > required_good:
            required_good = needed
            controlling = name
        results.append(ParameterResult(name, spec, low_value, good_value, foreign_value, final_value, needed, meets, False, detail))

    rounded_required = round(required_good)
    evaluated = [item for item in results if item.specification is not None]
    overall_pass = bool(evaluated) and all(item.meets_specification and not item.impossible for item in evaluated)
    return BlendResult(rounded_required, controlling, tuple(results), overall_pass, low_quantity, foreign_quantity, foreign_enabled)


def solve_reverse_blend(
    good_quantity_kg: float,
    low_values: Mapping[str, object],
    good_values: Mapping[str, object],
    specifications: Mapping[str, object],
    fm_target: object = 0.0,
    fm_parameter: str = "Foreign Material",
) -> ReverseBlendResult:
    """Find the maximum low-lot quantity that can be added to a fixed good lot."""
    try:
        good_quantity = float(good_quantity_kg)
    except (TypeError, ValueError) as exc:
        raise ValueError("Good lot weight must be numeric") from exc
    if good_quantity <= 0:
        raise ValueError("Good lot weight must be greater than zero")
    target = _validated_number(fm_target, "Foreign Material target")
    low_values = low_values or {}
    good_values = good_values or {}

    allowed_low = float("inf")
    controlling = "None"
    results: list[ParameterResult] = []
    for name, raw_spec in specifications.items():
        spec = None if raw_spec is None or str(raw_spec).strip() == "" else _validated_number(raw_spec, f"{name} specification")
        low_value = _validated_number(low_values.get(name), f"{name} low lot percentage")
        good_value = _validated_number(good_values.get(name), f"{name} good lot percentage")
        needed = 0.0
        impossible = False
        detail = "No low-lot limit"
        if spec is None:
            final_value = None
            meets = True
        elif good_value > spec:
            impossible = True
            final_value = None
            meets = False
            detail = "Impossible: good lot is already above the maximum"
        elif low_value <= spec:
            final_value = good_value
            meets = True
        else:
            denominator = low_value - spec
            needed = max(0.0, good_quantity * (spec - good_value) / denominator)
            final_value = spec if needed else good_value
            meets = True
            detail = f"Maximum {round(needed):,} kg low seed"
            if needed < allowed_low:
                allowed_low = needed
                controlling = name
        results.append(ParameterResult(name, spec, low_value, good_value, 0.0, final_value, needed, meets, impossible, detail))

    if allowed_low == float("inf"):
        allowed_low = 0.0
    low_quantity = round(allowed_low)
    alternatives: list[CompositionAlternative] = []
    for candidate_item in results:
        if candidate_item.specification is None or candidate_item.low_value <= candidate_item.specification:
            candidate_low = 0.0
        elif candidate_item.good_value > candidate_item.specification:
            continue
        else:
            candidate_low = good_quantity * (candidate_item.specification - candidate_item.good_value) / (candidate_item.low_value - candidate_item.specification)
        candidate_values: list[CompositionValue] = []
        candidate_total = good_quantity + candidate_low
        for item in results:
            if item.specification is None:
                candidate_values.append(CompositionValue(item.name, None, None, None, True, 0.0))
                continue
            final_percentage = (good_quantity * item.good_value + candidate_low * item.low_value) / candidate_total if candidate_total else 0.0
            final_kg = final_percentage / 100 * candidate_total
            meets = final_percentage <= item.specification + 1e-9
            compensation = 0.0
            if not meets and item.low_value > item.specification and item.good_value < item.low_value:
                item_limit = good_quantity * (item.specification - item.good_value) / (item.low_value - item.specification)
                compensation = max(0.0, candidate_low - item_limit)
            candidate_values.append(CompositionValue(item.name, item.specification, final_percentage, final_kg, meets, compensation))
        alternatives.append(CompositionAlternative(candidate_item.name, round(candidate_low), tuple(candidate_values)))
    recalculated: list[ParameterResult] = []
    total_weight = good_quantity + low_quantity
    for item in results:
        if item.impossible or item.specification is None:
            recalculated.append(item)
            continue
        final_value = (good_quantity * item.good_value + low_quantity * item.low_value) / total_weight if total_weight else 0.0
        difference = item.specification - final_value
        detail = item.detail
        if item.name != controlling and item.low_value > item.specification:
            detail = f"{difference:.2f}% below maximum"
        elif item.low_value <= item.specification:
            detail = f"{difference:.2f}% below maximum"
        recalculated.append(replace(item, final_value=final_value, meets_specification=final_value <= item.specification + 1e-9, detail=detail, difference_from_specification=difference))
    results = recalculated
    fm_index = next((index for index, item in enumerate(results) if item.name == fm_parameter), None)
    outside_fm = 0.0
    if fm_index is not None and target > 0:
        fm_item = results[fm_index]
        current_weight = good_quantity + low_quantity
        current_fm_mass = good_quantity * fm_item.good_value + low_quantity * fm_item.low_value
        current_fm_percentage = current_fm_mass / current_weight if current_weight else 0.0
        fm_shortfall = target - current_fm_percentage
        target_mass = target * current_weight
        if current_fm_mass < target_mass and target < 100:
            outside_fm = (target_mass - current_fm_mass) / (100 - target)
            fm_item = results[fm_index]
            results[fm_index] = replace(fm_item, final_value=target, difference_from_specification=(fm_item.specification - target) if fm_item.specification is not None else None, detail=f"Current {current_fm_percentage:.2f}%; short by {fm_shortfall:.2f}%; add {round(outside_fm):,} kg outside FM")
    evaluated = [item for item in results if item.specification is not None]
    overall_pass = bool(evaluated) and all(item.meets_specification and not item.impossible for item in evaluated)
    return ReverseBlendResult(low_quantity, controlling, tuple(results), overall_pass, good_quantity, round(outside_fm), target, tuple(alternatives))
