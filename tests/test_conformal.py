"""Finite-sample rank and selection-safety tests for the split-conformal utilities."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from gems47s3.conformal import (
    SweepPoint,
    conformal_order_statistic,
    conformal_quantile,
    dkw_epsilon,
    dkw_mean_lower_bound,
    min_blocks_for_alpha,
    select,
)


def test_quantile_uses_the_n_plus_one_correction():
    """For a lower DTI bound, use the k-th largest value, not the k-th smallest."""
    scores = np.arange(1.0, 11.0)                 # n = 10
    # alpha=.10 -> k=ceil(11*.90)=10 -> the 10th largest is the minimum.
    assert conformal_quantile(scores, 0.10, "lower") == 1.0
    # alpha=.25 -> k=ceil(11*.75)=9 -> the 9th largest is the 2nd smallest.
    assert conformal_quantile(scores, 0.25, "lower") == 2.0
    # alpha=.50 -> k=ceil(11*.50)=6 -> the 6th largest is the 5th smallest.
    assert conformal_quantile(scores, 0.50, "lower") == 5.0
    assert conformal_quantile(scores, 0.999, "lower") == 10.0
    assert conformal_quantile(scores, 0.10, "upper") == 10.0


def test_quantile_is_vacuous_when_the_finite_sample_rank_exceeds_n():
    assert conformal_quantile(np.arange(1.0, 6.0), 0.10, "lower") == -math.inf
    assert conformal_quantile(np.arange(1.0, 21.0), 0.10, "lower") == 2.0
    assert conformal_quantile(np.arange(1.0, 4.0), 0.05, "upper") == math.inf


def test_exact_rank_and_minimum_sample_size():
    assert conformal_order_statistic(19, 0.10) == 18
    assert conformal_order_statistic(9, 0.10) == 9
    assert min_blocks_for_alpha(0.10) == 9
    assert min_blocks_for_alpha(0.05) == 19
    assert min_blocks_for_alpha(0.25) == 3
    assert min_blocks_for_alpha(0.50) == 1
    for alpha in (0.05, 0.10, 0.25):
        n = min_blocks_for_alpha(alpha)
        assert conformal_order_statistic(n, alpha) <= n
        assert conformal_order_statistic(n - 1, alpha) > n - 1


def test_lower_bound_has_exchangeable_marginal_coverage_in_monte_carlo():
    rng = np.random.default_rng(0)
    for alpha in (0.05, 0.10, 0.20):
        misses = 0
        reps = 4000
        n = 40
        for _ in range(reps):
            draws = rng.lognormal(mean=0.0, sigma=1.2, size=n + 1)
            calibration, future = draws[:n], draws[n]
            bound = conformal_quantile(calibration, alpha, "lower")
            assert math.isfinite(bound)
            if future < bound:
                misses += 1
        rate = misses / reps
        tolerance = 3.5 * math.sqrt(alpha * (1 - alpha) / reps)
        assert rate <= alpha + tolerance


def test_dkw_epsilon_shrinks_as_inverse_sqrt_n():
    e8 = dkw_epsilon(8, 0.10)
    e32 = dkw_epsilon(32, 0.10)
    assert e32 == pytest.approx(e8 / 2.0, rel=1e-9)
    assert dkw_epsilon(0, 0.1) == math.inf


def test_dkw_mean_lower_bound_uses_declared_support_not_observed_range():
    scores = np.linspace(0.40, 0.50, 100)
    epsilon = dkw_epsilon(scores.size, 0.10)
    expected = float(scores.mean()) - epsilon
    assert dkw_mean_lower_bound(scores, 0.10) == pytest.approx(expected)
    # Multiplying by the observed 0.10 range would be an invalid, much tighter bound.
    assert dkw_mean_lower_bound(scores, 0.10) < float(scores.mean()) - 0.1 * epsilon
    assert dkw_mean_lower_bound(np.zeros(100), 0.10) == 0.0


def _point(
    name: str,
    calibration: list[float],
    selection: list[float],
    *,
    spacing: float = 2.8,
) -> SweepPoint:
    return SweepPoint(
        name=name,
        params={"min_dist": spacing},
        calib_dtis=calibration,
        select_dtis=selection,
        calibration_block_ids=list(range(10, 10 + len(calibration))),
        selection_block_ids=list(range(100, 100 + len(selection))),
    )


def test_candidate_is_chosen_from_selection_half_and_calibration_only_certifies():
    # A has a much higher calibration floor; B has a higher selection mean. The rule must choose B.
    a = _point("A", [0.8] * 10, [0.2] * 10)
    b = _point("B", [0.1] * 10, [0.4] * 10)
    result = select([a, b], alpha=0.10)
    assert result.chosen == "B"
    assert result.certified_floor == pytest.approx(0.1)
    assert result.selection_mean == pytest.approx(0.4)
    assert result.selection_half_min_above_floor is True
    evidence = result.to_dict()
    assert evidence["selected_by"].startswith("selection-half mean")
    assert evidence["block_roles_disjoint"] is True
    assert evidence["exchangeability_verified"] is False
    assert evidence["private_or_leaderboard_floor_certified"] is False


def test_changing_calibration_scores_cannot_change_selected_candidate():
    first = select([
        _point("A", [0.9] * 10, [0.2] * 10),
        _point("B", [0.1] * 10, [0.4] * 10),
    ])
    second = select([
        _point("A", [0.0] * 10, [0.2] * 10),
        _point("B", [0.8] * 10, [0.4] * 10),
    ])
    assert first.chosen == second.chosen == "B"
    assert first.certified_floor != second.certified_floor


def test_selector_rejects_overlapping_or_inconsistent_block_roles():
    overlapping = _point("overlap", [0.1] * 10, [0.2] * 10)
    overlapping.selection_block_ids[0] = overlapping.calibration_block_ids[0]
    with pytest.raises(ValueError, match="overlap"):
        select([overlapping])

    a = _point("A", [0.1] * 10, [0.2] * 10)
    b = _point("B", [0.2] * 10, [0.3] * 10)
    b.calibration_block_ids[0] = 999
    with pytest.raises(ValueError, match="identical ordered block-role IDs"):
        select([a, b])


def test_selector_rejects_missing_ids_bad_scores_and_duplicate_names():
    no_ids = SweepPoint(name="no_ids", params={}, calib_dtis=[0.1], select_dtis=[0.2])
    with pytest.raises(ValueError, match="one ID per DTI score"):
        select([no_ids])

    fractional_ids = _point("fractional", [0.1] * 10, [0.2] * 10)
    fractional_ids.calibration_block_ids[0] = 10.5
    with pytest.raises(ValueError, match="integer block IDs"):
        select([fractional_ids])

    bad = _point("bad", [0.1] * 10, [0.2] * 10)
    bad.calib_dtis[0] = float("nan")
    with pytest.raises(ValueError, match="finite DTI scores"):
        select([bad])

    a = _point("duplicate", [0.1] * 10, [0.2] * 10)
    b = _point("duplicate", [0.2] * 10, [0.3] * 10)
    with pytest.raises(ValueError, match="unique"):
        select([a, b])


def test_selector_does_not_accept_calibration_floor_as_ranking_rule():
    # The safe API has no calibration-floor tie-break option; using the same calibration data to
    # choose and certify would invalidate the advertised post-selection coverage.
    with pytest.raises(TypeError):
        select([_point("A", [0.1] * 10, [0.2] * 10)], tie_break="floor")


def test_invalid_alpha_side_and_nonfinite_conformal_scores_fail_closed():
    for alpha in (0.0, 1.0, float("nan")):
        with pytest.raises(ValueError):
            conformal_quantile([0.1, 0.2], alpha)
    with pytest.raises(TypeError, match="bool"):
        conformal_quantile([0.1, 0.2], True)
    with pytest.raises(ValueError, match="side"):
        conformal_quantile([0.1, 0.2], 0.1, side="middle")
    with pytest.raises(ValueError, match="finite"):
        conformal_quantile([0.1, float("nan")], 0.1)
    with pytest.raises(ValueError, match="support"):
        dkw_mean_lower_bound([0.1, 0.2], 0.1, support=(0.3, 1.0))


def test_historical_calibration_selected_certificate_is_retracted():
    root = Path(__file__).resolve().parents[1]
    selection = json.loads((root / "evidence" / "conformal" / "selection.json").read_text())
    retraction = json.loads(
        (root / "evidence" / "conformal" / "retraction-20261007.json").read_text()
    )
    guarantee = selection["guarantee"]
    assert selection["review_status"] == "RETRACTED_POST_SELECTION_SELECTOR_AND_DKW_FORMULA"
    assert guarantee["candidate_choice_used_calibration_outcomes"] is True
    assert guarantee["certified_floor"] is None
    assert guarantee["historical_certified_floor_reported_retracted"] == pytest.approx(0.04476930982739195)
    assert guarantee["mean_floor_dkw"] == 0.0
    assert guarantee["dkw_mean_floor_observed_range_scaled_retracted"] == pytest.approx(
        0.04552678479903236
    )
    assert guarantee["dkw_iid_sampling_verified"] is False
    assert retraction["support_fixed_dkw_calculation"]["clipped_lower_bound"] == 0.0
