"""Tests for the split-conformal selector and its finite-sample guarantee."""
from __future__ import annotations

import math

import numpy as np
import pytest

from gems47s3.conformal import (SweepPoint, conformal_quantile, conformal_order_statistic,
                              dkw_epsilon, min_blocks_for_alpha, select)


def test_quantile_uses_the_n_plus_one_correction():
    """Lei et al. (2018): q_hat is the ceil((n+1)(1-alpha))-th smallest calibration score and
    P(s_new <= q_hat) >= 1 - alpha.  For a LOWER bound on Y we score with s = -Y, so the bound
    is the k-th LARGEST Y with the same k -- i.e. the (n-k+1)-th smallest."""
    s = np.arange(1.0, 11.0)                       # n = 10
    # alpha = 0.10 -> k = ceil(11 * 0.90) = 10 -> the 10th largest = the MINIMUM
    assert conformal_quantile(s, 0.10, "lower") == 1.0
    # alpha = 0.25 -> k = ceil(11 * 0.75) = 9 -> the 9th largest = 2nd smallest
    assert conformal_quantile(s, 0.25, "lower") == 2.0
    # alpha = 0.50 -> k = ceil(11 * 0.50) = 6 -> the 6th largest = 5th smallest
    assert conformal_quantile(s, 0.50, "lower") == 5.0
    # alpha -> 1 gives the largest value
    assert conformal_quantile(s, 0.999, "lower") == 10.0
    # upper side: alpha = 0.10 -> the 10th smallest = the MAXIMUM
    assert conformal_quantile(s, 0.10, "upper") == 10.0


def test_quantile_is_vacuous_when_k_exceeds_n():
    # n = 5, alpha = 0.10 -> k = ceil(6 * 0.90) = 6 > n, so a 90% lower bound does NOT exist
    assert conformal_quantile(np.arange(1.0, 6.0), 0.10, "lower") == -math.inf
    # n = 20, alpha = 0.10 -> k = ceil(21 * 0.90) = 19 <= n -> the 19th largest = 2nd smallest
    assert conformal_quantile(np.arange(1.0, 21.0), 0.10, "lower") == 2.0
    # upper side with k > n is vacuous
    assert conformal_quantile(np.arange(1.0, 4.0), 0.05, "upper") == math.inf


def test_lower_bound_never_exceeds_the_minimum_for_small_n():
    """Guard against an over-optimistic bound: the 1-alpha lower bound can never be above the
    (n - ceil((n+1)(1-alpha)) + 1)-th smallest, and at 1-alpha <= n/(n+1) it is the minimum."""
    for n in range(2, 40):
        s = np.sort(np.random.default_rng(n).random(n))
        alpha = 1.0 / (n + 1.0)                   # the largest alpha with k = n
        assert conformal_quantile(s, alpha, "lower") == pytest.approx(s[0])


def test_quantile_monotone_in_alpha():
    s = np.array([0.01, 0.02, 0.05, 0.09, 0.20, 0.31, 0.44, 0.60])
    prev = -math.inf
    for a in (0.05, 0.10, 0.20, 0.30, 0.40):
        q = conformal_quantile(s, a, "lower")
        assert q >= prev
        prev = q


def test_empirical_coverage_meets_the_guarantee():
    """The theorem: P(s(X,Y) <= q_hat) >= 1 - alpha, exactly, for exchangeable data.

    Checked by Monte Carlo over 4,000 repetitions with n = 12 calibration points and a
    deliberately skewed distribution.  The empirical one-sided miss rate must not exceed
    alpha beyond Monte-Carlo error.
    """
    rng = np.random.default_rng(0)
    for alpha in (0.05, 0.10, 0.20):
        misses = 0
        reps = 4000
        n = 40                                    # large enough that k <= n at every alpha
        for _ in range(reps):
            draws = rng.lognormal(mean=0.0, sigma=1.2, size=n + 1)
            calib, new = draws[:n], draws[n]
            q = conformal_quantile(calib, alpha, "lower")
            assert math.isfinite(q), "the bound must be non-vacuous at this n and alpha"
            if new < q:                       # one-sided lower bound violated
                misses += 1
        rate = misses / reps
        assert rate <= alpha + 3.5 * math.sqrt(alpha * (1 - alpha) / reps), (alpha, rate)


def test_dkw_epsilon_shrinks_as_inverse_sqrt_n():
    e8 = dkw_epsilon(8, 0.10)
    e32 = dkw_epsilon(32, 0.10)
    assert e32 == pytest.approx(e8 / 2.0, rel=1e-9)
    assert dkw_epsilon(0, 0.1) == math.inf


def test_min_blocks_for_alpha():
    assert min_blocks_for_alpha(0.10) == 9
    assert min_blocks_for_alpha(0.05) == 19
    assert min_blocks_for_alpha(0.25) == 3
    assert min_blocks_for_alpha(0.50) == 1
    for alpha in (0.05, 0.10, 0.25):
        n = min_blocks_for_alpha(alpha)
        assert conformal_order_statistic(n, alpha) <= n
        assert conformal_order_statistic(n - 1, alpha) > n - 1


def test_select_ranks_by_floor_not_by_mean():
    """A noisy high mean must lose to a stable lower mean.  n = 10 so that a 90 % lower bound
    exists at all (it needs n >= 9); with fewer blocks every floor is vacuous."""
    noisy = SweepPoint(name="noisy", params={},
                       calib_dtis=[0.40, 0.01, 0.28, 0.02, 0.29, 0.01, 0.27, 0.03, 0.26, 0.02],
                       select_dtis=[0.005, 0.03])
    stable = SweepPoint(name="stable", params={},
                        calib_dtis=[0.15, 0.16, 0.14, 0.15, 0.16, 0.15, 0.14, 0.15, 0.16, 0.15],
                        select_dtis=[0.15, 0.14])
    assert noisy.calib_mean > stable.calib_mean
    out = select([noisy, stable], alpha=0.10, tie_break="floor")
    assert out.chosen == "stable"
    # n = 10, alpha = 0.10 -> k = ceil(11 * 0.9) = 10 -> the 10th largest = the MINIMUM
    assert out.certified_floor == pytest.approx(0.14)
    assert out.vacuous is False
    assert out.min_blocks_required_for_alpha == 9
    assert out.cleared_floor is True
    # and the mean-ranked rule picks the noisy one, which is exactly the trap
    out2 = select([noisy, stable], alpha=0.10, tie_break="mean")
    assert out2.chosen == "noisy"
    assert out2.cleared_floor is False


def test_selection_is_flagged_vacuous_when_n_too_small():
    pt = SweepPoint(name="p", params={}, calib_dtis=[0.10, 0.20, 0.30, 0.40], select_dtis=[0.15])
    out = select([pt], alpha=0.10, tie_break="floor")
    # n = 4 but a 90 % lower bound needs n >= 9, so no finite bound exists
    assert out.vacuous is True
    assert out.certified_floor == -math.inf
    assert out.min_blocks_required_for_alpha == 9
    # a 75 % bound does exist at n = 4 (needs n >= 3): k = ceil(5 * 0.75) = 4 -> 4th largest
    out2 = select([pt], alpha=0.25, tie_break="floor")
    assert out2.vacuous is False
    assert out2.certified_floor == pytest.approx(0.10)


def test_select_prefers_a_non_vacuous_floor_over_a_higher_vacuous_one():
    small = SweepPoint(name="small_n", params={}, calib_dtis=[0.9, 0.9], select_dtis=[])
    big = SweepPoint(name="big_n", params={},
                     calib_dtis=[0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19],
                     select_dtis=[])
    out = select([small, big], alpha=0.10, tie_break="floor")
    assert out.chosen == "big_n"
    assert out.vacuous is False


def test_select_raises_without_calibration_scores():
    with pytest.raises(ValueError):
        select([SweepPoint(name="x", params={})], alpha=0.1)
