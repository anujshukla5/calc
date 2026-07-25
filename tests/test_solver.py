from seed_blend_optimizer.solver import solve_blend, solve_reverse_blend


def test_optimization_uses_controlling_parameter():
    result = solve_blend(
        1000,
        {"Dal": 4, "Damaged Seed": 3, "Foreign Material": 1},
        {"Dal": 1, "Damaged Seed": 0.5, "Foreign Material": 0.1},
        {"Dal": 2, "Damaged Seed": 1.5, "Foreign Material": 0.5},
    )
    assert result.required_good_kg == 2000
    assert result.controlling_parameter == "Dal"
    assert result.overall_pass is True


def test_impossible_good_lot_is_reported():
    result = solve_blend(1000, {"Dal": 4}, {"Dal": 4}, {"Dal": 2})
    parameter = result.parameters[0]
    assert parameter.impossible is True
    assert parameter.meets_specification is False
    assert "Impossible" in parameter.detail


def test_blank_values_are_zero():
    result = solve_blend(1000, {"Dal": ""}, {"Dal": ""}, {"Dal": 2})
    assert result.required_good_kg == 0
    assert result.parameters[0].final_value == 0


def test_invalid_weight_and_percentage_are_rejected():
    try:
        solve_blend(0, {"Dal": 4}, {"Dal": 1}, {"Dal": 2})
    except ValueError as error:
        assert "greater than zero" in str(error)
    else:
        raise AssertionError("zero low-lot weight should be rejected")

    try:
        solve_blend(1000, {"Dal": 101}, {"Dal": 1}, {"Dal": 2})
    except ValueError as error:
        assert "between 0 and 100" in str(error)
    else:
        raise AssertionError("out-of-range percentage should be rejected")


def test_reverse_blend_reports_low_seed_and_outside_fm():
    result = solve_reverse_blend(
        1000,
        {"Dal": 4, "Foreign Material": 1},
        {"Dal": 1, "Foreign Material": 0.1},
        {"Dal": 2, "Foreign Material": 5},
        2,
    )
    assert result.allowed_low_kg == 500
    assert result.controlling_parameter == "Dal"
    assert result.outside_fm_kg == 24


def test_reverse_blend_recalculates_non_controlling_parameters():
    result = solve_reverse_blend(
        1000,
        {"Dal": 4, "Damaged Seed": 3},
        {"Dal": 1, "Damaged Seed": 0.5},
        {"Dal": 2, "Damaged Seed": 2},
    )
    damaged = result.parameters[1]
    assert result.allowed_low_kg == 500
    assert round(damaged.final_value, 2) == 1.33
    assert round(damaged.difference_from_specification, 2) == 0.67


def test_fm_shortfall_is_reported_before_outside_fm():
    result = solve_reverse_blend(
        27000,
        {"Dal": 55, "Damaged Seed": 13, "Foreign Material": 1.5},
        {"Dal": 0, "Damaged Seed": 0, "Foreign Material": 0},
        {"Dal": 13, "Damaged Seed": 3.5, "Foreign Material": 3},
        3,
    )
    fm = result.parameters[2]
    assert result.allowed_low_kg == 8357
    assert result.outside_fm_kg == 964
    assert "Current 0.35%" in fm.detail
    assert "short by 2.65%" in fm.detail


def test_composition_alternatives_show_other_values_and_compensation():
    result = solve_reverse_blend(
        1000,
        {"Dal": 4, "Damaged Seed": 3},
        {"Dal": 1, "Damaged Seed": 0.5},
        {"Dal": 2, "Damaged Seed": 2},
    )
    assert [item.controlling_parameter for item in result.alternatives] == ["Dal", "Damaged Seed"]
    damaged_option = result.alternatives[1].values[0]
    assert round(damaged_option.final_percentage, 2) == 2.8
    assert round(damaged_option.final_kg, 1) == 70.0
    assert round(damaged_option.compensation_low_kg) == 1000
