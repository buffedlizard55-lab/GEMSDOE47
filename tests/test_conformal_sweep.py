"""Finite-sample rank / selection safety, independent of competition data."""
import json

import numpy as np
import pytest

from gems47.conformal import choose_operating_point, simultaneous_lower_bounds


def test_augmented_rank_yields_zero_not_a_fabricated_90_percent_floor():
    result = simultaneous_lower_bounds([[.8, .7]], [[.8, .7], [.75, .65], [.7, .6]])
    assert result["rank_1_based"] == 4
    assert result["augmented_infinity_used"] is True
    assert result["quantile"] is None
    assert result["lower_bounds"] == [0.0, 0.0]
    json.dumps(result, allow_nan=False)


def test_simultaneous_band_covers_nine_of_ten_exchangeable_leave_one_out_units():
    # Holding centers fixed, any of ten distinct units is equally likely to be
    # the next unit. Maximum residual joint band at 90% fails on at most one.
    scores = np.array([[.1 + .07 * i, .75 - .06 * i, .15 + .03 * i] for i in range(10)])
    selection = np.array([[.55, .5, .4], [.45, .6, .5]])
    jointly_covered = 0
    selected_covered = 0
    for i in range(10):
        band = simultaneous_lower_bounds(selection, np.delete(scores, i, axis=0), coverage=.9)
        assert band["rank_1_based"] == 9
        lower = np.array(band["lower_bounds"])
        jointly_covered += bool((scores[i] >= lower - 1e-12).all())
        index = choose_operating_point(band, (1.5, 2.8, 3.6))
        selected_covered += scores[i, index] >= lower[index] - 1e-12
    assert jointly_covered >= 9
    assert selected_covered >= 9


def test_max_over_settings_residual_and_exact_rank():
    selection = np.array([[.5, .9]])
    calibration = np.tile([.4, .6], (19, 1))
    result = simultaneous_lower_bounds(selection, calibration, coverage=.9)
    assert result["rank_1_based"] == 18
    assert result["quantile"] == pytest.approx(.3)
    assert result["lower_bounds"] == pytest.approx([.2, .6])
    assert choose_operating_point(result, (5.8, 1.5)) == 1
    assert result["exchangeability_verified"] is False
    assert result["private_leaderboard_floor_certified"] is False


def test_ties_use_selection_then_larger_spacing():
    band = {"lower_bounds": [0, 0, 0], "selection_centers": [.5, .6, .6]}
    assert choose_operating_point(band, (6, 2.8, 3.6)) == 2


@pytest.mark.parametrize("selection,calibration,coverage", [
    ([], [[.3]], .9), ([[.3]], [], .9), ([[.3]], [[np.nan]], .9),
    ([[1.1]], [[.3]], .9), ([[.3]], [[.3, .4]], .9),
    ([[.3]], [[.3]], 1), ([[.3]], [[.3]], True), ([[.3]], [[.3]], np.nan),
])
def test_invalid_inputs_fail_closed(selection, calibration, coverage):
    with pytest.raises(ValueError):
        simultaneous_lower_bounds(selection, calibration, coverage=coverage)
