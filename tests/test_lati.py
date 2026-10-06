"""The inversion's forward model, on synthetic data small enough to brute-force."""
from __future__ import annotations

import numpy as np
import pytest

from gems47 import emitter as E
from gems47 import lati
from gems47 import metric as M


def make_obs(seed=0, n=24, ndots=40):
    rng = np.random.default_rng(seed)
    shape = (n, n)
    obs = []
    for i in range(3):
        dots = np.zeros(shape, bool)
        dots[rng.integers(3, n - 3, ndots), rng.integers(3, n - 3, ndots)] = True
        p = dots.astype(np.float64)
        w = M.max_kernel_filter(p)
        a = np.zeros(shape)
        for dy, dx, k in zip(M.OFF_DY, M.OFF_DX, M.OFF_K):
            a += k * E._shift(p > 0, dy, dx)
        obs.append(lati.Obs(id=f"o{i}", dti=0.1 + 0.05 * i, site="synthetic", family="synthetic",
                            sha256="0" * 64, S=float(p.sum()), n_dots=int(dots.sum()),
                            n_on_catalogue=0, w=w.ravel().astype(np.float32),
                            a=a.ravel().astype(np.float32),
                            dot_pos=np.flatnonzero(dots.ravel()),
                            dot_flat=np.flatnonzero(dots.ravel()), extras={}))
    return obs, shape


def test_kernel_rings_partition_the_offsets():
    rings = E.kernel_rings()
    assert sum(len(o) for _, o in rings) == M.N_OFFSETS == 25
    ks = [k for k, _ in rings]
    assert ks == sorted(ks, reverse=True)
    assert ks[0] == 1.0


def test_expected_kappa_dense_is_in_unit_interval_and_matches_sparse():
    rng = np.random.default_rng(3)
    for scale in (0.002, 0.02, 0.2, 0.6):
        q = rng.random((50, 50)) * scale
        dots = rng.random((50, 50)) < 0.04
        kd = E.expected_kappa_dense(q)
        assert kd.min() >= 0.0 and kd.max() <= 1.0 + 1e-12
        assert abs(float(kd[dots].sum()) - E.expected_phi(q, dots)) < 1e-8


def test_expected_kappa_matches_monte_carlo():
    rng = np.random.default_rng(11)
    for scale in (0.002, 0.02, 0.2):
        q = rng.random((40, 40)) * scale
        dots = np.zeros((40, 40), bool)
        dots[rng.integers(5, 35, 60), rng.integers(5, 35, 60)] = True
        exact = E.expected_phi(q, dots)
        draws = [M.max_kernel_filter((rng.random(q.shape) < q).astype(float))[dots].sum()
                 for _ in range(600)]
        mc, se = float(np.mean(draws)), float(np.std(draws) / np.sqrt(len(draws)))
        assert abs(exact - mc) < 4 * max(se, 1e-6), (scale, exact, mc, se)


def test_first_order_phi_is_an_upper_bound_not_an_estimate():
    """Documents the bug that was fixed: <q, a> >= exact Phi, badly so as q grows."""
    rng = np.random.default_rng(5)
    for scale, expect in ((0.002, 0.002), (0.2, 0.5)):
        q = rng.random((40, 40)) * scale
        dots = np.zeros((40, 40), bool)
        dots[rng.integers(5, 35, 60), rng.integers(5, 35, 60)] = True
        a = np.zeros(q.shape)
        for dy, dx, k in zip(M.OFF_DY, M.OFF_DX, M.OFF_K):
            a += k * E._shift(q, dy, dx)
        first_order = float(a[dots].sum())
        exact = E.expected_phi(q, dots)
        assert first_order >= exact - 1e-12
        assert (first_order - exact) / max(exact, 1e-9) > expect


def test_predicted_score_never_reports_negative_fp():
    rng = np.random.default_rng(7)
    q = rng.random((60, 60)) * 0.4          # deliberately absurd density
    dots = rng.random((60, 60)) < 0.3       # and an absurdly dense emission
    ps = E.predicted_score(q, dots)
    assert ps["F"] >= 0.0
    assert ps["Phi"] <= ps["S"] + 1e-9
    assert 0.0 <= ps["DTI"] <= 1.25 + 1e-9  # the theoretical ceiling is T/(beta*K) = 1/0.8


def test_binned_softmax_matches_the_dense_path():
    obs, shape = make_obs()
    rng = np.random.default_rng(2)
    U = rng.integers(0, 256, size=(2, shape[0] * shape[1])).astype(np.uint8)
    rows = [0, 1]
    bm = lati.BinnedSoftmax(U, rows, obs, 32)
    theta = np.array([500.0, 3.0, -2.0])
    binned = bm.predict(theta)
    eta = np.zeros(U.shape[1])
    for j, r in enumerate(rows):
        eta += theta[1 + j] * (U[r].astype(np.float64) / 255.0 - 0.5)
    s = np.exp(eta - eta.max())
    q = theta[0] * s / s.sum()
    dense = lati.predict_dti(obs, q)
    assert np.max(np.abs(binned - dense)) < 5e-3


def test_dti_is_linear_functional_in_q_for_T():
    """T = <q, w_p> exactly, so doubling q doubles T at fixed K - the core of LATI."""
    obs, shape = make_obs()
    rng = np.random.default_rng(9)
    q = rng.random(shape[0] * shape[1]) * 1e-3
    c1 = lati.components(obs, q)
    c2 = lati.components(obs, 2 * q)
    for a, b in zip(c1, c2):
        assert b["T"] == pytest.approx(2 * a["T"], rel=1e-9)
        assert b["K"] == pytest.approx(2 * a["K"], rel=1e-9)


def test_observation_list_is_pinned_and_complete():
    assert len(lati.OBSERVATIONS) == 12
    ids = [r["id"] for r in lati.OBSERVATIONS]
    assert len(set(ids)) == 12
    for r in lati.OBSERVATIONS:
        assert 0.0 < r["dti"] <= 1.0
        assert r["file"].endswith(".tif")
        assert r["site"]
