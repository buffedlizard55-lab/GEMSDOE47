"""Verification of the DTI implementation.

Three independent checks, in increasing order of strength:
 1. the organisers' own published worked example (page 967) -> 0.60
 2. an analytic single-truth-pixel / single-dot case with a hand-computed answer
 3. the fast path vs a literal O(N^2) transcription of the four published formulas
 4. the two exact reductions (FN_w = K - T, FP_w = S - Phi) and the lambda-scaling identity
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gems47 import metric as M  # noqa: E402


def test_kernel_offsets_and_levels():
    # 25 integer offsets have k > 0: s = dy^2+dx^2 in {0,1,2,4,5,8}
    assert M.N_OFFSETS == 25
    counts = {0: 1, 1: 4, 2: 4, 4: 4, 5: 8, 8: 4}
    got: dict[int, int] = {}
    for dy, dx in zip(M.OFF_DY, M.OFF_DX):
        got[int(dy * dy + dx * dx)] = got.get(int(dy * dy + dx * dx), 0) + 1
    assert got == counts
    assert M.KERNEL_SUM == pytest.approx(9.3802978105, abs=1e-9)
    assert M.kernel_value(0.0) == 1.0
    assert M.kernel_value(1.0) == pytest.approx(2 / 3)
    assert M.kernel_value(3.0) == 0.0
    assert M.kernel_value(4.0) == 0.0
    # distinct levels descending, all in (0, 1]
    assert M.LEVELS[0] == 1.0 and all(a > b for a, b in zip(M.LEVELS, M.LEVELS[1:]))


def test_published_worked_example():
    w = M.worked_example()
    assert w["DTI"] == pytest.approx(w["published"], abs=5e-3)
    # exact arithmetic from the published components
    assert 3.00 / (3.00 + 0.2 * 1.89 + 0.8 * 2.00) == pytest.approx(0.6026516, abs=1e-7)


def test_analytic_single_truth_single_dot():
    """One truth pixel, one dot at pixel distance d, no masking.

    T = k(d), F = 1 - k(d), K = 1  =>  DTI = k / (0.2*1 + 0.8*1) = k.
    (because alpha*(T+F) = alpha*1 exactly: the dot either covers the truth or not)
    """
    for dy, dx in [(0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2), (3, 0)]:
        p = np.zeros((9, 9)); g = np.zeros((9, 9), bool)
        p[4, 4] = 1.0
        g[4 + dy, 4 + dx] = True
        s = M.score(p, g)
        k = M.kernel_value(float(np.hypot(dy, dx)))
        assert s.T == pytest.approx(k, abs=1e-12)
        assert s.F == pytest.approx(1.0 - k, abs=1e-12)
        assert s.K == 1
        assert s.DTI == pytest.approx(k / (0.2 * 1.0 + 0.8 * 1.0), abs=1e-12)


def test_reduction_FN_equals_K_minus_T_and_FP_equals_S_minus_Phi():
    rng = np.random.default_rng(7)
    for _ in range(6):
        p = (rng.random((40, 40)) * rng.random((40, 40)) * 1.4).clip(0, 1)
        g = rng.random((40, 40)) < 0.05
        s = M.score(p, g)
        assert s.FN == pytest.approx(s.K - s.T, abs=1e-9)
        assert s.F == pytest.approx(s.S - s.Phi, abs=1e-9)
        assert s.DTI == pytest.approx(M.dti_from_TFK(s.T, s.F, s.K), abs=1e-12)


def test_fast_path_matches_bruteforce():
    rng = np.random.default_rng(11)
    for trial in range(8):
        n = 26
        p = np.zeros((n, n))
        g = np.zeros((n, n), bool)
        # sparse binary-ish predictions and truths, plus some continuous mass
        idx = rng.integers(0, n, size=(trial + 3) * 4)
        idy = rng.integers(0, n, size=(trial + 3) * 4)
        p[idy, idx] = rng.choice([1.0, 0.5, 0.25], size=len(idx))
        g[rng.integers(0, n, size=trial + 4), rng.integers(0, n, size=trial + 4)] = True
        ev = np.ones((n, n), bool)
        ev[rng.integers(0, n, size=5), rng.integers(0, n, size=5)] = False  # masked pixels
        fast = M.score(p, g, ev)
        slow = M.dti_bruteforce(p, g, ev)
        assert fast.T == pytest.approx(slow["TP_w"], abs=1e-9), (trial, fast.T, slow["TP_w"])
        assert fast.F == pytest.approx(slow["FP_w"], abs=1e-9), (trial, fast.F, slow["FP_w"])
        assert fast.FN == pytest.approx(slow["FN_w"], abs=1e-9)
        assert fast.DTI == pytest.approx(slow["DTI"], abs=1e-9)


def test_lambda_scaling_identity_is_exact():
    rng = np.random.default_rng(3)
    p = (rng.random((30, 30)) < 0.15).astype(float)
    g = rng.random((30, 30)) < 0.04
    for lam in (1.0, 0.75, 0.5, 0.25, 0.1):
        direct, closed = M.scale_identity(p, lam, g)
        assert direct == pytest.approx(closed, abs=1e-12)


def test_masked_pixels_are_neutral():
    """DrivenData staff (thread 11516): catalogue pixels are excluded from evaluation.

    Adding unit mass on masked pixels must change neither T nor F nor DTI.
    """
    rng = np.random.default_rng(5)
    g = rng.random((30, 30)) < 0.05
    p = (rng.random((30, 30)) < 0.1).astype(float)
    ev = np.ones((30, 30), bool)
    mask_out = np.zeros((30, 30), bool)
    mask_out[2:6, 2:6] = True
    ev &= ~mask_out
    s1 = M.score(p, g, ev)
    p2 = p.copy()
    p2[mask_out] = 1.0  # pile mass onto masked pixels
    s2 = M.score(p2, g, ev)
    assert s2.T == pytest.approx(s1.T, abs=1e-12)
    assert s2.F == pytest.approx(s1.F, abs=1e-12)
    assert s2.DTI == pytest.approx(s1.DTI, abs=1e-12)


def test_marginal_rule_reduces_to_k_gt_alpha_dti():
    dti = 0.26
    for k in np.linspace(0.001, 0.2, 40):
        g = M.marginal_gain(k, 1.0 - k, dti)
        assert (g > 0) == (k > M.ALPHA * dti), (k, g)
    assert M.breakeven_k(0.26) == pytest.approx(0.052)
    assert M.breakeven_k(0.3262) == pytest.approx(0.06524)


def test_required_recall_table():
    # 1/DTI = alpha + alpha*(F/T) + beta*(K/T);  x = T/K = (a*rho+b)/(1/DTI-a)
    assert M.required_recall(0.3262, 0.0) == pytest.approx(0.2791733, abs=1e-6)
    assert M.required_recall(0.3195, 0.0) == pytest.approx(0.2730476, abs=1e-6)
    assert M.required_recall(0.2600, 0.0) == pytest.approx(0.2194092, abs=1e-6)


def test_dti_is_monotone_in_credit_and_decreasing_in_waste():
    K = 10_000.0
    base = M.dti_from_TFK(4000, 30_000, K)
    assert M.dti_from_TFK(4400, 30_000, K) > base
    assert M.dti_from_TFK(4000, 26_000, K) > base
    assert M.dti_from_TFK(4000, 34_000, K) < base


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
