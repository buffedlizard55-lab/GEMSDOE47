#!/usr/bin/env python3
"""Exact re-implementation of the DOE GEMS distance-weighted Tversky index (DTI).

Transcribed line by line from the organizer's problem description
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/

    k(d)   = max(1 - d/R, 0),  R = 300 m = 3 px at 100 m resolution
    TP_w   = sum_{g in G} max_{x: d(x,g) <= R} p(x) k(d(x,g))
    FP_w   = sum_{x: p(x) > 0} p(x) [1 - max_{g in G} k(d(x,g))]
    FN_w   = sum_{g in G} [1 - max_{x: d(x,g) <= R} p(x) k(d(x,g))]
    DTI    = TP_w / (TP_w + alpha FP_w + beta FN_w + eps),  alpha = 0.2, beta = 0.8

Two consequences used throughout this repository:

  (1) Because p(x) k <= 1, the max is at most 1, so FN_w == N_g - TP_w exactly and
          DTI = TP_w / (0.2 TP_w + 0.2 FP_w + 0.8 N_g) = 5 TP_w / (TP_w + FP_w + 4 N_g).
      `identity_error` below reports max|FN_w - (N_g - TP_w)| as a numerical check.

  (2) Every predicted pixel with p(x) > 0 that is farther than R from every
      ground-truth pixel is a pure loss: it adds exactly alpha * p(x) to the
      denominator and 0 to the numerator.  Such pixels are called "dead dots".

This module does not validate any masking convention against an organizer
receipt. Callers must apply the current official footprint/label semantics and
record the exact source inputs separately.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage

R_PX = 3.0
ALPHA = 0.2
BETA = 0.8
EPS = 0.0


def kernel(d):
    return np.clip(1.0 - d / R_PX, 0.0, None)


def _offsets():
    """Every integer (dr, dc) whose Euclidean length is <= R_PX."""
    o = []
    r = int(np.floor(R_PX))
    for dr in range(-r, r + 1):
        for dc in range(-r, r + 1):
            if dr * dr + dc * dc <= R_PX * R_PX:
                o.append((dr, dc, float(np.hypot(dr, dc))))
    return o


OFFSETS = _offsets()
assert len(OFFSETS) == 29, len(OFFSETS)   # 3-px Euclidean disc


def _shift_field(a, dr, dc):
    out = np.zeros_like(a)
    H, W = a.shape
    sr = slice(max(0, dr), H + min(0, dr))
    dr_ = slice(max(0, -dr), H + min(0, -dr))
    sc = slice(max(0, dc), W + min(0, dc))
    dc_ = slice(max(0, -dc), W + min(0, -dc))
    out[dr_, dc_] = a[sr, sc]
    return out


def dti(pred, truth, mask=None, *, want_fields=False):
    p = np.nan_to_num(np.asarray(pred, dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    g = (np.asarray(truth) > 0).astype(np.float32)
    if mask is not None:
        m = np.asarray(mask, dtype=bool)
        p = np.where(m, np.float32(0.0), p)
        g = np.where(m, np.float32(0.0), g)
    p = np.clip(p, 0.0, 1.0)

    # scipy's EDT of an all-background image measures distance to an implicit
    # exterior pixel, not to an empty truth set. With G empty, kappa is exactly
    # zero and every prediction is pure FP; do not invent corner credit.
    if np.any(g):
        d_to_G = ndimage.distance_transform_edt(g == 0).astype(np.float32)
        FPw = float(np.sum(p * (1.0 - kernel(d_to_G)), dtype=np.float64))
    else:
        FPw = float(np.sum(p, dtype=np.float64))

    coverage = np.zeros_like(g)
    for dr, dc, dist in OFFSETS:
        k = np.float32(1.0 - dist / R_PX)
        shifted = _shift_field(p, dr, dc) * k          # contribution of x = g + (dr,dc) to g
        np.maximum(coverage, shifted, out=coverage)
    np.minimum(coverage, 1.0, out=coverage)
    truth_px = g > 0
    cov_g = coverage[truth_px]                     # coverage only AT ground-truth pixels
    TPw = float(cov_g.sum())
    Ng = float(truth_px.sum())
    FNw = float(np.sum(1.0 - cov_g))               # == N_g - TP_w exactly (max <= 1)
    denom = TPw + ALPHA * FPw + BETA * FNw + EPS
    val = float(TPw / denom) if denom > 0 else 0.0
    out = {
        "dti": val,
        "TPw": TPw,
        "FPw": FPw,
        "FNw": FNw,
        "Ng": Ng,
        "dti_identity": float(5.0 * TPw / (TPw + FPw + 4.0 * Ng)) if Ng > 0 else 0.0,
        "n_pred_pos": int((p > 0).sum()),
    }
    if want_fields:
        out['coverage'] = coverage
    return out


if __name__ == "__main__":                       # self-test: python3 src/gems47_metric.py
    import numpy as _np
    _pass = _fail = 0

    def _check(name, cond, extra=""):
        global _pass, _fail
        if cond:
            _pass += 1
            print(f"  ok   {name}")
        else:
            _fail += 1
            print(f"  FAIL {name} {extra}")

    _h = _w = 30
    _truth = _np.zeros((_h, _w), _np.uint8)
    _truth[10, 5:25] = 1

    _perfect = _np.zeros((_h, _w), _np.float32)
    _perfect[_truth == 1] = 1.0
    _check("perfect mask scores 1.0", abs(dti(_perfect, _truth)["dti"] - 1.0) < 1e-9)

    _off2 = _np.zeros((_h, _w), _np.float32)
    _off2[12, 5:25] = 1.0
    _check("2 px offset scores exactly 1/3", abs(dti(_off2, _truth)["dti"] - 1.0 / 3.0) < 1e-6,
           f"got {dti(_off2, _truth)['dti']:.6f}")

    _far = _np.zeros((_h, _w), _np.float32)
    _far[20, 5:25] = 1.0
    _check("far row scores below a perfect mask", dti(_far, _truth)["dti"] < 1.0)

    _empty = _np.zeros((_h, _w), _np.float32)
    _check("empty mask scores 0.0", dti(_empty, _truth)["dti"] == 0.0)
    _check("predicting the truth itself with mask=truth scores 0.0",
           dti(_truth.astype(_np.float32), _truth, mask=_truth)["dti"] == 0.0)

    # the algebraic reduction the whole project rests on, checked on random fields
    _rng = _np.random.default_rng(0)
    _ok = True
    for _ in range(5):
        _p = (_rng.random((40, 40)) < 0.05).astype(_np.float32)
        _g = (_rng.random((40, 40)) < 0.04).astype(_np.uint8)
        _r = dti(_p, _g)
        _ok &= abs(_r["dti"] - _r["dti_identity"]) < 1e-6
    _check("dti == 5*TPw/(TPw + FPw + 4*Ng) to machine precision", _ok)

    # organizer's worked example, transcribed from
    # https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ (fetched
    # 2026-10-06): TP_w = 3.00, FP_w = 1.89, FN_w = 2.00, page reports "0.60";
    # 3/(3+0.2*1.89+0.8*2) = 0.602651…, the "0.6027" quoted in this repo's notes.
    # The page's pixel rasters are images (gems_metric_1.png / gems_metric_2.png), not
    # machine-readable, so the check is at the formula level on the official components.
    _tp, _fp, _fn = 3.00, 1.89, 2.00
    _ti = _tp / (_tp + 0.2 * _fp + 0.8 * _fn)
    _check("organizer worked example = 0.602651… (page's 0.60)", abs(_ti - 0.602651) < 1e-5, f"{_ti:.6f}")
    _check("worked example under identity: N_g = TP+FN = 5 → 5*3/(3+1.89+20) identical",
           abs(5 * _tp / (_tp + _fp + 4 * (_tp + _fn)) - _ti) < 1e-12)

    print(f"\n{_pass} passed, {_fail} failed")
    raise SystemExit(1 if _fail else 0)
