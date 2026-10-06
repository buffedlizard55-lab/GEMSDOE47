"""Tests for the exact DTI implementation.

Every assertion here is checkable against the official page:
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gems47s3 import metric as M
from gems47s3.metric import credit_bar, dti
from gems47s3.spec import ALPHA, BETA


def test_kernel_values_on_the_100m_lattice():
    assert M.kernel(0.0) == 1.0
    assert M.kernel(1.0) == pytest.approx(2 / 3)
    assert M.kernel(3.0) == 0.0
    assert M.kernel(4.0) == 0.0
    assert M.kernel(np.sqrt(2.0)) == pytest.approx(1 - np.sqrt(2) / 3)
    assert M.kernel(2 * np.sqrt(2.0)) == pytest.approx(1 - 2 * np.sqrt(2) / 3)


def test_official_worked_example_gives_060():
    """The published example: TP_w 3.00, FP_w 1.89, FN_w 2.00 -> TI_w = 0.60.

    The official page prints "0.60" (two decimals).  The exact value of the published
    expression 3.00 / (3.00 + 0.2*1.89 + 0.8*2.00) is 3.00/4.978 = 0.602651..., which
    ROUNDS to the printed 0.60.  Verified 2026-10-06 against the live page text.
    """
    ex = M.official_worked_example()
    assert round(ex["dti"], 2) == 0.60
    assert ex["dti"] == pytest.approx(3.00 / 4.978, abs=1e-12)
    # and the same number straight from the published formula
    assert 3.00 / (3.00 + ALPHA * 1.89 + BETA * 2.00) == pytest.approx(ex["dti"], abs=1e-12)


def _tiny_case(seed=0):
    rng = np.random.default_rng(seed)
    truth = rng.random((24, 24)) < 0.06
    pred = np.where(rng.random((24, 24)) < 0.25, rng.random((24, 24)), 0.0)
    return pred, truth


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_exact_matches_literal_bruteforce(seed):
    pred, truth = _tiny_case(seed)
    fast = M.dti(pred, truth)
    slow = M.dti_bruteforce(pred, truth)
    assert fast["tp"] == pytest.approx(slow["tp"], abs=1e-9)
    assert fast["fp"] == pytest.approx(slow["fp"], abs=1e-9)
    assert fast["fn"] == pytest.approx(slow["fn"], abs=1e-9)
    assert fast["dti"] == pytest.approx(slow["dti"], abs=1e-9)


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_fn_equals_ntruth_minus_tp(seed):
    pred, truth = _tiny_case(seed)
    r = M.dti(pred, truth)
    assert r["fn"] == pytest.approx(r["n_truth"] - r["tp"], abs=1e-12)


@pytest.mark.parametrize("seed", [0, 1, 2, 3])
def test_algebraic_identity_holds(seed):
    """DTI == T / (0.2*(T + S - M) + 0.8*|G|) — the form every emitter here reasons with."""
    pred, truth = _tiny_case(seed)
    r = M.dti(pred, truth)
    assert r["dti"] == pytest.approx(r["dti_identity"], abs=1e-12)


def test_binary_path_matches_soft_path():
    pred, truth = _tiny_case(7)
    b = (pred > 0)
    soft = M.dti(b.astype(float), truth)
    fast = M.dti_binary(b, truth)
    assert fast["dti"] == pytest.approx(soft["dti"], abs=1e-12)
    assert fast["tp"] == pytest.approx(soft["tp"], abs=1e-12)
    assert fast["fp"] == pytest.approx(soft["fp"], abs=1e-12)


def test_known_fault_masking_removes_pixels_from_both_sums():
    """Official staff: known USGS/INGENIOUS pixels are masked out of evaluation."""
    truth = np.zeros((12, 12), bool)
    truth[6, 6] = True
    pred = np.zeros((12, 12))
    pred[6, 6] = 1.0
    assert M.dti(pred, truth)["dti"] == pytest.approx(1.0, abs=1e-9)
    known = np.zeros((12, 12), bool)
    known[6, 6] = True
    r = M.dti(pred, truth, known=known)
    assert r["n_truth"] == 0 and r["tp"] == 0.0 and r["S"] == 0.0 and r["dti"] == 0.0


def test_a_prediction_near_a_known_fault_but_far_from_truth_is_fully_penalised():
    """Official staff post #4: there is NO buffer around known faults."""
    truth = np.zeros((20, 20), bool)
    truth[2, 2] = True                    # the only hidden new fault
    known = np.zeros((20, 20), bool)
    known[10, 10] = True                  # a known catalogue pixel
    pred = np.zeros((20, 20))
    pred[10, 11] = 1.0                    # adjacent to the known fault, 11 px from truth
    r = M.dti(pred, truth, known=known)
    # not masked -> it is a full false positive
    assert r["fp"] == pytest.approx(1.0, abs=1e-12)
    assert r["tp"] == 0.0
    assert r["dti"] == pytest.approx(0.0, abs=1e-12)


def test_credit_bar_is_alpha_times_dti():
    """dDTI > 0 for a unit of mass with realised weight w  <=>  w > 0.2*DTI."""
    assert M.credit_bar(0.2778) == pytest.approx(0.2 * 0.2778)
    assert M.credit_bar(0.3345) == pytest.approx(0.2 * 0.3345)


def test_credit_bar_is_a_true_threshold_numerically():
    """Adding a dot with weight above the bar raises DTI; below it lowers DTI."""
    n_truth, T, S, Mg = 7905.0, 4075.0, 37654.0, 4075.0
    base = M.dti_from_TSM(T, S, Mg, n_truth)
    bar = M.credit_bar(base)
    w_hi = bar + 1e-3
    # a dot that becomes the sole best cover of one truth pixel: dT = w, dS = 1, dM = w
    up = M.dti_from_TSM(T + w_hi, S + 1, Mg + w_hi, n_truth)
    assert up > base
    w_lo = max(bar - 1e-3, 0.0)
    down = M.dti_from_TSM(T + w_lo, S + 1, Mg + w_lo, n_truth)
    assert down < base


def test_redundant_mass_hurts_unless_it_sits_exactly_on_truth():
    """A dot whose truth pixel is already better covered: dT = 0, dS = 1, dM = w.

    d(denominator) = alpha*(1 - w) >= 0, so DTI is non-increasing, and strictly
    decreasing for every w < 1.  Only w == 1 (the dot lands exactly on a truth pixel
    that is already perfectly covered) is score-neutral -- which is why duplicate mass
    on a 1-px-wide trace is pure waste and thinning is free.
    """
    n_truth, T, S, Mg = 7905.0, 4075.0, 37654.0, 4075.0
    base = M.dti_from_TSM(T, S, Mg, n_truth)
    for w in (2 / 3, 1 - np.sqrt(2) / 3, 1 / 3, 1 - 2 * np.sqrt(2) / 3, 0.0):
        assert M.dti_from_TSM(T, S + 1, Mg + w, n_truth) < base
    # w == 1 is exactly neutral
    assert M.dti_from_TSM(T, S + 1, Mg + 1.0, n_truth) == pytest.approx(base, abs=1e-15)


def test_score_budget_dataclass():
    b = M.ScoreBudget(T=4075.0, S=37654.0, M=4075.0, n_truth=7905.0)
    assert b.dti == pytest.approx(M.dti_from_TSM(4075.0, 37654.0, 4075.0, 7905.0))
    assert b.wasted == pytest.approx(37654.0 - 4075.0)
    assert b.to_dict()["credit_per_pixel"] == pytest.approx(4075.0 / 37654.0)


def test_out_of_range_prediction_inside_domain_is_rejected():
    truth = np.zeros((8, 8), bool)
    pred = np.zeros((8, 8))
    pred[3, 3] = 1.5
    with pytest.raises(ValueError):
        M.dti(pred, truth)
    pred2 = np.zeros((8, 8))
    pred2[3, 3] = -3.4028234663852886e38   # the feature sentinel must never leak through
    with pytest.raises(ValueError):
        M.dti(pred2, truth)


# --------------------------------------------------------------------------- soft vs binary
def test_binary_is_optimal_over_soft_scaling():
    """The sign of dDTI for one added pixel does not depend on its value v.

    For a pixel of value v whose best-cover kernel weight is w: dT = v*w and
    d(denominator) = alpha*v, so v cancels out of the sign.  Down-weighting a pixel that clears
    the credit bar only shrinks its gain; up-weighting one that misses only enlarges the
    penalty.  A {0,1} mask is therefore the optimum of the whole soft family -- which is also
    what all eleven scored reference artifacts are.
    """
    n = 70
    truth = np.zeros((n, n), bool)
    truth[30, 8:58] = True                      # a straight 1-px-wide trace
    base = np.zeros((n, n), np.float64)
    base[30, 10:50:3] = 1.0                     # dots spaced 3 px along it, covering cols 8-51
    # col 55 is beyond every base dot (nearest is col 49, d = 6 > R), so its best cover is 0 and
    # ANY positive v placed there becomes the best cover with w = 1.0.  dT = v and
    # d(denominator) = 0.2*(v + v - v) = 0.2*v, so sign(dDTI) = sign(1 - 0.2*DTI) > 0 for every v.
    good = (30, 55)
    bad = (36, 25)                              # 6 px off the trace: w = 0, misses the bar

    base_dti = dti(base, truth)["dti"]
    for v in (0.05, 0.25, 0.5, 0.75, 1.0):
        a = base.copy(); a[good] = v
        b = base.copy(); b[bad] = v
        da = dti(a, truth)["dti"] - base_dti
        db = dti(b, truth)["dti"] - base_dti
        assert da > 0, f"a pixel that clears the bar must help at every v, failed at v={v}"
        assert db < 0, f"a pixel that misses the bar must hurt at every v, failed at v={v}"
    # the gain is monotone in v: a down-weighted good dot is strictly worse than a binary one
    scaled = []
    for v in (0.05, 0.25, 0.5, 0.75, 1.0):
        a = base.copy(); a[good] = v
        scaled.append(dti(a, truth)["dti"])
    assert scaled == sorted(scaled), "DTI must increase monotonically with the value of a good dot"


def test_soft_downweighting_of_a_good_dot_is_strictly_worse_than_binary():
    """Given a fixed support, scaling good dots down can only reduce DTI."""
    n = 60
    truth = np.zeros((n, n), bool)
    truth[30, 8:52] = True
    support = np.zeros((n, n), np.float64)
    support[30, 10:50:3] = 1.0
    best = dti(support, truth)["dti"]
    for v in (0.2, 0.5, 0.8, 0.999):
        assert dti(support * v, truth)["dti"] <= best + 1e-12


def test_credit_bar_agrees_with_the_lattice_weights():
    """At DTI 0.2778 the bar is 0.0556, so on the 100 m lattice a dot pays only within 2.83 px."""
    bar = credit_bar(0.2778)
    assert bar == pytest.approx(0.2 * 0.2778)
    k = lambda d: max(1.0 - d / 3.0, 0.0)
    assert k(2.0) > bar and k(np.sqrt(5)) > bar
    # 2*sqrt(2) = 2.8284 sits just INSIDE the break-even radius 2.8332, so it still pays
    assert k(2 * np.sqrt(2)) == pytest.approx(0.0572, abs=1e-3)
    assert k(2 * np.sqrt(2)) > bar
    assert k(2.9) < bar and k(3.0) == 0.0
    d_star = 3.0 * (1.0 - bar)
    assert d_star == pytest.approx(2.8332, abs=1e-3)
    assert 2 * np.sqrt(2) < d_star < 2.9


def test_credit_bar_is_alpha_times_dti_not_the_circulated_formula():
    """Guard against the alpha*s/(1-alpha*s) form that circulated in earlier repositories."""
    for d in (0.05, 0.1922, 0.2778, 0.3345, 0.60):
        assert credit_bar(d) == pytest.approx(0.2 * d)
        wrong = 0.2 * d / (1 - 0.2 * d)
        assert wrong != pytest.approx(credit_bar(d), abs=1e-6) or d < 1e-9
        # and the wrong form is always the more permissive one, i.e. it under-prunes
        assert wrong >= credit_bar(d)
