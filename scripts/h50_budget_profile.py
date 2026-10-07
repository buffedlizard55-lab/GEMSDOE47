#!/usr/bin/env python3
"""H50 evidence, part 4 -- budget chosen from the metric's own credit bar.

``gems47s3.metric.credit_bar`` shows that a unit of mass pays for itself exactly when its
realised kernel weight exceeds ``alpha * DTI``.  ``gems47.h50.expected_kernel_profile``
therefore reports, for each budget, the mean realised kernel weight of the emitted dots and
the credit bar at that budget, which locates the budget at which the marginal dot stops
paying without reference to any leaderboard observation.  Writes
``evidence/h50/budget-profile.json``.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "2")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import rasterio  # noqa: E402
from scipy import ndimage as ndi  # noqa: E402

from gems47 import grid as G  # noqa: E402
from gems47 import h50  # noqa: E402
from gems47s3.geomorph import rank_scale  # noqa: E402

SPACING_PX = 2.8
REGIONAL_SIGMA_PX = 25.0
BUDGETS = (10_000, 20_000, 30_000, 37_654, 44_090, 50_000, 60_000, 80_000, 120_000)


def main() -> int:
    started = time.time()
    data = G.data_dir()
    grids = h50.read_grid(data)
    mask = grids["evaluated"]
    with rasterio.open(data / "training_features.tif") as src:
        slope = src.read(h50.SLOPE_BAND).astype(np.float32)
    slope[~np.isfinite(slope)] = 0.0
    slope[slope < -1e30] = 0.0
    regional = ndi.gaussian_filter(slope, REGIONAL_SIGMA_PX, mode="nearest")
    field = rank_scale(np.where(mask, slope - regional, np.nan))
    field = np.where(mask & np.isfinite(field), field, 0.0).astype(np.float32)
    truth = h50.instrument_l(data)["mask"] & mask
    profile = h50.expected_kernel_profile(field, mask, truth, BUDGETS)
    out = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "question": "at which budget does the marginal emitted dot stop paying alpha*DTI?",
        "spacing_px": SPACING_PX,
        "truth": "off-catalogue local maxima of the 1 m lidar scarp stack (Instrument L)",
        "n_truth": int(truth.sum()),
        "field": "rank of det_elev_slope above its 25 px Gaussian regional level",
        "credit_bar_rule": "a unit of mass pays for itself when its realised kernel weight "
                           "exceeds alpha*DTI (gems47s3.metric.credit_bar)",
        "rows": profile,
        "leaderboard_mass_anchor": "the owner-reported score history clusters at 37,654-44,090 "
                                   "dots at d2.8; the profile is reported so the choice is "
                                   "made on the credit bar, not on that anchor",
        "elapsed_seconds": round(time.time() - started, 2),
    }
    path = ROOT / "evidence" / "h50" / "budget-profile.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    for r in profile:
        print(f"budget={r['budget']:7d} dti={r['dti']:.4f} tp={r['tp']:9.1f} fp={r['fp']:9.1f} "
              f"mean_w={r['mean_kernel_weight']:.4f} bar={r['credit_bar']:.4f} "
              f"pays={r['marginal_pays']}", flush=True)
    print(f"-> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
