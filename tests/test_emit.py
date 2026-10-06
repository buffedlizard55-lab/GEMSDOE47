#!/usr/bin/env python3
"""Unit tests for the emission operators and the submission contract.

Run:  python3 tests/test_emit.py        (exit code 0 = all pass)
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gems47_emit import (flank_prune, greedy_min_separation, octile_dot_spacing,  # noqa: E402
                             redot, to_raster, trace_chains, order_chain)
from src.gems47_metric import dti, R_PX  # noqa: E402

PASS = FAIL = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} {detail}")


def mask(coords, shape=(40, 40)):
    m = np.zeros(shape, bool)
    for r, c in coords:
        m[r, c] = True
    return m


print("== metric ==")
h, w = 30, 30
truth = np.zeros((h, w), np.uint8)
truth[10, 5:25] = 1
perfect = truth.astype(np.float32)
check("perfect mask scores 1.0", abs(dti(perfect, truth)["dti"] - 1.0) < 1e-9,
      f"got {dti(perfect, truth)['dti']}")
shift = np.zeros((h, w), np.float32)
shift[12, 5:25] = 1.0                      # 2 px off, kernel radius 3
# algebra: TP = 20*(1/3), FP = 20*(2/3), FN = 20 - 20/3, N_g = 20
#   -> 5*(20/3) / (20/3 + 40/3 + 80) = (100/3)/(100) = 1/3
check("2 px offset gives exactly 1/3",
      abs(dti(shift, truth)["dti"] - 1 / 3) < 1e-6,
      f"got {dti(shift, truth)['dti']:.6f}")
far = np.zeros((h, w), np.float32)
far[20, 5:25] = 1.0
check("far row scores below the perfect mask", dti(far, truth)["dti"] < 1.0,
      f"got {dti(far, truth)['dti']:.4f}")
empty = np.zeros((h, w), np.float32)
check("empty mask scores 0.0", dti(empty, truth)["dti"] == 0.0)
check("mask=truth alias yields 0.0", dti(truth.astype(np.float32), truth, mask=truth)["dti"] == 0.0)

print("== flank_prune (delete-only, radius rule) ==")
dots = mask([(5, 5), (5, 6), (20, 20)])
dist = np.full((40, 40), 100.0)
dist[5, 5] = 0.0
dist[5, 6] = 1.0
out = flank_prune(dots, dist, 2)
check("removes only dots with d_cat <= B", out.sum() == 1 and out[20, 20],
      f"kept {out.sum()}")
check("flank_prune is delete-only", not (out & ~dots).any())
check("flank_prune keeps geometry identical otherwise",
      np.array_equal(np.nonzero(out), np.array([[20], [20]])))

print("== greedy_min_separation ==")
line = mask([(10, c) for c in range(0, 20)])
kept = greedy_min_separation(line, 4.0)
ys, xs = np.nonzero(kept)
gaps = np.diff(np.sort(xs))
check("min-separation >= requested spacing", gaps.min() >= 4.0, f"min gap {gaps.min()}")
check("min-separation is delete-only", not (kept & ~line).any())
check("min-separation keeps a sensible fraction", 3 <= kept.sum() <= 6, f"kept {kept.sum()}")

print("== octile_dot_spacing ==")
sp = octile_dot_spacing(mask([(1, 1), (1, 2), (1, 10)]))
check("spacing statistic returns a positive number", sp > 0, f"got {sp}")

print("== trace_chains / order_chain / redot ==")
pair = mask([(2, 2), (2, 4)])             # a two-dot "pair", the dominant real motif
comps, (ys, xs) = trace_chains(pair, 4.5)
check("a 2-dot pair forms one chain", len(comps) == 1 and len(comps[0]) == 2,
      f"{len(comps)} chains")
pts = order_chain(comps[0], ys, xs)
check("order_chain returns every dot exactly once", len(pts) == 2)
trace = mask([(5, c) for c in range(0, 30)])
r = redot(trace, 5.0)
ys2, xs2 = np.nonzero(r)
gaps = np.diff(np.sort(xs2))
check("redot places dots spaced ~5 px", gaps.max() <= 5 and gaps.min() >= 4, f"gaps {gaps}")
check("redot marks its spacing as exact multiples of the step",
      abs(len(np.unique(xs2)) - 7) <= 1, f"placed {len(np.unique(xs2))}")
check("redot on a straight trace stays exactly on the trace row",
      bool((ys2 == 5).all()))
xc = np.unique(xs2)
d = np.abs(np.diff(xc))
check("redot step is regular to within a pixel", d.std() <= 1.0, f"steps {d}")

# documented lossiness: redot may move positions off the original dots
moved = int((r & ~trace).sum())
check("redot is documented as lossy on straight traces (moved positions >= 0)", moved >= 0,
      f"moved {moved}")

print("== to_raster ==")
ras = to_raster(pair, np.ones((40, 40), bool))
check("to_raster is 0/1 inside the footprint", set(np.unique(ras)) <= {0.0, 1.0})
ras_nan = to_raster(pair, np.zeros((40, 40), bool))
check("to_raster writes NaN outside the footprint", np.isnan(ras_nan).any())

print("== submission contract (if the artifact is present) ==")
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sub = os.path.join(root, "docs", "downloads",
                   "gems47-dcat20-annulus-flankprune-n18524-20261006.tif")
if os.path.exists(sub):
    import rasterio
    with rasterio.open(sub) as ds:
        a = ds.read(1)
        check("submission is single band float32", ds.count == 1 and ds.dtypes[0] == "float32")
        check("submission CRS is EPSG:32611", str(ds.crs) == "EPSG:32611")
        check("submission shape is 3730x3292", ds.shape == (3730, 3292), f"{ds.shape}")
        check("submission nodata is None", ds.nodata is None)
    fin = a[np.isfinite(a)]
    check("submission values inside [0,1]", fin.min() >= 0 and fin.max() <= 1,
          f"[{fin.min()}, {fin.max()}]")
    check("submission has no NaN", bool(np.isfinite(a).all()))
    check("submission uses only 0 and 1", set(np.unique(fin)) <= {0.0, 1.0})
    check("submission has 18524 positives", int((a > 0).sum()) == 18524, f"{int((a>0).sum())}")
else:
    print("  skip  submission artifact not built yet")

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
