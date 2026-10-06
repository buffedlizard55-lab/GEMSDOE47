"""Verification of H48 (MSCL curvature consensus), H48-APEX emission, and the
split-conformal certificate.

Checks, in increasing order of strength:
 1. ``conformal_rank`` / ``min_alpha_family`` arithmetic against Lei et al. (2018)
 2. the vacuous-arm guard: no non-vacuous family guarantee exists at n = 6, m = 7,
    and the code must return -inf instead of raising (the bug fixed this session)
 3. ``consensus_apex`` on a synthetic field: local maxima only, threshold honoured,
    catalogue margin honoured, minimum separation honoured, budget honoured
 4. the certificate's monotonicity and the selection rule's validity statement
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gems47 import conformal as CF
from gems47 import h49

# ---------------------------------------------------------------------------
# 1/2 - the conformal arithmetic
# ---------------------------------------------------------------------------


def test_conformal_rank_matches_definition():
    # Lei et al. (2018) eq. (2.6): k = ceil((n + 1) * (1 - alpha))
    assert CF.conformal_rank(12, 0.07692307692307693) == 12
    assert CF.conformal_rank(12, 0.5384615384615385) == 6
    assert CF.conformal_rank(6, 1.0 / 7.0) == 6


def test_min_alpha_family_is_the_family_cost():
    # alpha_family = m / (n + 1) is exactly the Bonferroni-corrected rate at which
    # a family of m candidates is still certifiable from n calibration points.
    n, m = 12, 7
    a = CF.min_alpha_family(n, m)
    assert a == pytest.approx(m / (n + 1))
    # k = ceil((n+1) - m); for m >= 1 this is <= n, so the family is certifiable
    assert CF.conformal_rank(n, a) == n + 1 - m == 6
    assert 1 <= CF.conformal_rank(n, a) <= n
    # and the quantile is a real order statistic, not a vacuous +/-inf
    r = np.linspace(-0.05, 0.05, n)
    assert np.isfinite(CF.lower_quantile(r, a))


def test_family_of_seven_cannot_be_certified_from_six_returns():
    """The honest negative this session's build reports instead of a number."""
    n, m = 6, 7
    assert CF.min_alpha_family(n, m) >= 1.0
    assert CF.conformal_rank(n, CF.min_alpha_family(n, m)) < 1
    r = np.array([0.064, 0.048, 0.014, 0.011, 0.0004, 0.034])
    # must degrade to a vacuous bound, not raise IndexError
    assert CF.lower_quantile(r, CF.min_alpha_family(n, m)) == -np.inf
    sc = CF.SplitConformal(residuals=r, sel_residuals=np.array([0.0]),
                           n_candidates=m, alpha=CF.min_alpha_family(n, m),
                           alpha_used_override=CF.min_alpha_family(n, m))
    assert not sc.certified
    assert not np.isfinite(sc.lcb(0.3))


def test_single_predeclared_candidate_at_n6_is_certifiable():
    n = 6
    a = CF.min_alpha_family(n, 1)
    assert a == pytest.approx(1.0 / (n + 1))
    r = np.array([0.064, 0.048, 0.014, 0.011, 0.0004, 0.034])
    sc = CF.SplitConformal(residuals=r, sel_residuals=np.array([0.0]),
                           n_candidates=1, alpha=a, alpha_used_override=a)
    assert sc.certified
    assert sc.level_used == pytest.approx(n / (n + 1))
    # signed residuals -> the lower bound is predicted + the smallest residual
    assert sc.quantile == pytest.approx(0.0004)


# ---------------------------------------------------------------------------
# 3 - the H48-APEX emission (our own detector's geometry, not a prior's dots)
# ---------------------------------------------------------------------------


def _synthetic(n=60):
    y, x = np.mgrid[0:n, 0:n]
    cons = np.zeros((n, n), np.uint8)
    # a diagonal ridge at rank 255 and an off-ridge blob at rank 240
    for i in range(10, 50):
        cons[i, i] = 255
        cons[i, i + 1] = 254
    cons[5:9, 45:49] = 240
    allowed = np.ones((n, n), bool)
    allowed[:, 0] = False                      # stand-in for the catalogue margin
    return cons, allowed


def test_apex_takes_local_maxima_above_threshold_only():
    cons, allowed = _synthetic()
    dots = h49.consensus_apex(cons, allowed, 255, spacing_px=1.0, budget=10_000)
    assert dots.any()
    assert (cons[dots] == 255).all()
    assert not dots[:, 0].any()                # catalogue margin respected


def test_apex_threshold_is_nested_and_costs_nothing_extra():
    cons, allowed = _synthetic()
    tight = h49.consensus_apex(cons, allowed, 255, spacing_px=1.0, budget=10_000)
    loose = h49.consensus_apex(cons, allowed, 240, spacing_px=1.0, budget=10_000)
    assert (tight & ~loose).sum() == 0          # nested families
    assert loose.sum() > tight.sum()


def test_apex_honours_minimum_separation_and_budget():
    cons, allowed = _synthetic()
    dots = h49.consensus_apex(cons, allowed, 200, spacing_px=6.0, budget=10_000)
    ys, xs = np.nonzero(dots)
    if ys.size > 1:
        d = np.hypot(ys[:, None] - ys[None, :], xs[:, None] - xs[None, :])
        d[d == 0] = np.inf
        assert d.min() >= 6.0
    capped = h49.consensus_apex(cons, allowed, 200, spacing_px=1.0, budget=3)
    assert capped.sum() <= 3


def test_apex_is_deterministic():
    cons, allowed = _synthetic()
    a = h49.consensus_apex(cons, allowed, 248, spacing_px=2.5, budget=500)
    b = h49.consensus_apex(cons, allowed, 248, spacing_px=2.5, budget=500)
    assert np.array_equal(a, b)


# ---------------------------------------------------------------------------
# 4 - the certificate and the selection rule
# ---------------------------------------------------------------------------


def test_lcb_is_prediction_plus_quantile_and_monotone():
    r = np.linspace(-0.05, 0.05, 40)
    a = CF.min_alpha_family(40, 3)
    sc = CF.SplitConformal(residuals=r, sel_residuals=r[:5], n_candidates=3,
                           alpha=a, alpha_used_override=a)
    assert sc.certified
    lo, hi = sc.lcb(0.10), sc.lcb(0.20)
    assert hi - lo == pytest.approx(0.10)
    assert lo == pytest.approx(0.10 + sc.quantile)


def test_select_by_certified_floor_picks_the_argmax_bound():
    r = np.linspace(-0.05, 0.05, 40)
    a = CF.min_alpha_family(40, 2)
    sc = CF.SplitConformal(residuals=r, sel_residuals=r[:5], n_candidates=2,
                           alpha=a, alpha_used_override=a)
    cands = [CF.CertifiedCandidate(name="a", predicted=0.30, lcb=sc.lcb(0.30)),
             CF.CertifiedCandidate(name="b", predicted=0.10, lcb=sc.lcb(0.10))]
    assert CF.select_by_certified_floor(cands, sc).name == "a"


def test_certificate_level_is_reported_next_to_the_choice():
    """The submission note must quote a level a reviewer can recompute."""
    r = np.linspace(-0.05, 0.05, 12)
    m = 7
    a = CF.min_alpha_family(12, m)
    sc = CF.SplitConformal(residuals=r, sel_residuals=r[:6], n_candidates=m,
                           alpha=a, alpha_used_override=a)
    d = sc.to_dict()
    assert d["n_calibration"] == 12
    assert d["n_candidates"] == 7
    assert d["level_used"] == pytest.approx(1.0 - 7.0 / 13.0)
    assert d["conformal_rank_k"] == 6
    assert d.get("assumption")
