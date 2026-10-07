from scripts.flank_sensitivity import find_grid_sign_change_bracket


def test_sign_change_reports_adjacent_tested_values_without_interpolation():
    rows = [
        {"assumed_h33_dti": None, "loo_improvement_pct": 55.7},
        {"assumed_h33_dti": 0.24, "loo_improvement_pct": -5.4},
        {"assumed_h33_dti": 0.20, "loo_improvement_pct": 41.0},
        {"assumed_h33_dti": 0.22, "loo_improvement_pct": 27.0},
    ]

    bracket = find_grid_sign_change_bracket(rows)

    assert bracket == {
        "last_tested_positive_dti": 0.22,
        "last_tested_positive_loo_improvement_pct": 27.0,
        "first_tested_nonpositive_dti": 0.24,
        "first_tested_nonpositive_loo_improvement_pct": -5.4,
        "interpretation": "coarse-grid sign-change bracket only; no exact root computed",
        "interpolation_performed": False,
    }


def test_sign_change_returns_none_without_positive_to_nonpositive_pair():
    rows = [
        {"assumed_h33_dti": 0.20, "loo_improvement_pct": 40.0},
        {"assumed_h33_dti": 0.22, "loo_improvement_pct": 10.0},
        {"assumed_h33_dti": 0.24, "loo_improvement_pct": 0.1},
    ]

    assert find_grid_sign_change_bracket(rows) is None
