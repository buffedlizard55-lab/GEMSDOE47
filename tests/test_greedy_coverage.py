#!/usr/bin/env python3
"""Regression tests for coverage optimiser arithmetic, not scientific eligibility."""
import numpy as np
import pytest

from gems47s3 import emission as E
from gems47s3 import metric as M


def brute(field, mask, n, radius):
    dy, dx, kw = M.kernel_offsets(radius)
    f = np.where(mask, field, 0.)
    coverage = np.zeros(f.shape)
    out = np.zeros(mask.shape, bool)
    for _ in range(n):
        gains = []
        for i in np.flatnonzero(mask & ~out):
            y, x = divmod(int(i), f.shape[1])
            yy, xx = y+dy, x+dx
            ok = (yy >= 0) & (xx >= 0) & (yy < f.shape[0]) & (xx < f.shape[1])
            yy, xx, weights = yy[ok], xx[ok], kw[ok]
            gain = float((f[yy, xx] * np.maximum(weights-coverage[yy, xx], 0)).sum())
            gains.append((-gain, i))
        if not gains:
            break
        neg, i = min(gains)
        if neg >= 0:
            break
        out.flat[i] = True
        y, x = divmod(int(i), f.shape[1])
        yy, xx = y+dy, x+dx
        ok = (yy >= 0) & (xx >= 0) & (yy < f.shape[0]) & (xx < f.shape[1])
        coverage[yy[ok], xx[ok]] = np.maximum(coverage[yy[ok], xx[ok]], kw[ok])
    return out


@pytest.mark.parametrize('seed', range(5))
def test_greedy_matches_brute_and_respects_mask(seed):
    rng = np.random.default_rng(seed)
    f = rng.random((9, 11))
    mask = rng.random(f.shape) > .4
    got = E.greedy_coverage(f, mask, 30, 3.)
    assert np.array_equal(got, brute(f, mask, 30, 3.))
    assert not got[~mask].any()


def test_greedy_empty_and_zero_budget():
    f = np.ones((10, 10))
    assert not E.greedy_coverage(f, np.zeros_like(f, bool), 10).any()
    assert not E.greedy_coverage(f, np.ones_like(f, bool), 0).any()
    assert not E.greedy_coverage(f*0, np.ones_like(f, bool), 10).any()


def test_greedy_budget_and_no_spacing_claim():
    f = np.ones((10, 10))
    out = E.greedy_coverage(f, np.ones_like(f, bool), 100)
    assert out.sum() == 100  # coverage greedy is not a spacing constraint
