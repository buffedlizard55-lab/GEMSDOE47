#!/usr/bin/env python3
"""H50 evidence, part 3 -- refine the slope-anomaly field.  Writes
``evidence/h50/field-refine.json``."""
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
from gems47.metric import ALPHA, BETA, max_kernel_filter  # noqa: E402
from gems47s3.geomorph import rank_scale  # noqa: E402

SPACING_PX = 2.8
BUDGET = 37_654
SLOPE_BAND = 19
ELEV_BAND = 12

INSTRUMENTS = {
    "lappos_t200_d3": ("lappos_max", 200, 3),
    "lapneg_t200_d3": ("lapneg_max", 200, 3),
    "step_t150_d3": ("step_max", 150, 3),
    "cross_t200_d3": ("cross_max", 200, 3),
    "upface_t200_d3": ("upface_max", 200, 3),
}


def dti_parts(w_sum: float, k: int, s: float, phi: float) -> float:
    t = float(w_sum)
    den = t + ALPHA * (s - phi) + BETA * (k - t)
    return float(t / den) if den > 0 else 0.0


def main() -> int:
    started = time.time()
    data = G.data_dir()
    grids = h50.read_grid(data)
    mask = grids["evaluated"]
    blocks = h50.acquisition_blocks(data)
    with rasterio.open(data / "training_features.tif") as src:
        slope = src.read(SLOPE_BAND).astype(np.float32)
        slope[~np.isfinite(slope)] = 0.0
        slope[slope < -1e30] = 0.0
        elev = src.read(ELEV_BAND).astype(np.float32)
        elev[~np.isfinite(elev)] = 0.0
        elev[elev < -1e30] = 0.0

    ch = h50.lidar_scarp_channels(data)
    valid = ch["valid"] > 0
    inst = {}
    for iname, (chan, thr, md) in INSTRUMENTS.items():
        m = h50.lidar_peaks(ch[chan], valid, thr, md) & grids["footprint"] & ~grids["catalogue"]
        g = m & mask
        inst[iname] = dict(g=g, kappa=max_kernel_filter(g.astype(np.float64)), k=int(g.sum()))
    sgmc = h50.instrument_sgmc_offcatalogue(data) & mask
    inst["sgmc_offcat"] = dict(g=sgmc, kappa=max_kernel_filter(sgmc.astype(np.float64)),
                               k=int(sgmc.sum()))
    print("[setup]", {k: v["k"] for k, v in inst.items()}, flush=True)

    rs = lambda a: rank_scale(np.where(mask, a, np.nan))
    br = lambda a: h50.block_rank(a, blocks, mask)
    regional = lambda s: ndi.gaussian_filter(slope, s, mode="nearest")

    fields = {
        "block_rank_slope": br(slope),
        "global_rank_slope": rs(slope),
    }
    for sg in (8, 12, 16, 25, 40, 60):
        fields[f"anom_global_s{sg}"] = rs(slope - regional(sg))
        fields[f"anom_block_s{sg}"] = br(slope - regional(sg))
    # anomaly expressed as a ratio, and as a rank difference
    fields["ratio_global_s25"] = rs(slope / (regional(25) + 1.0))
    fields["ratio_block_s25"] = br(slope / (regional(25) + 1.0))
    fields["rankdiff_s25"] = np.maximum(rs(slope) - rs(regional(25)), 0.0)
    fields["rankdiff_block_s25"] = np.maximum(br(slope) - br(regional(25)), 0.0)
    # anomaly of the elevation gradient, for reference
    grad = np.hypot(ndi.gaussian_filter(elev, 1.5, order=(0, 1), mode="nearest"),
                    ndi.gaussian_filter(elev, 1.5, order=(1, 0), mode="nearest"))
    fields["anom_grad_s25"] = rs(grad - ndi.gaussian_filter(grad, 25, mode="nearest"))
    # max of the two best normalisations
    fields["max_block_anom25"] = np.maximum(br(slope), br(slope - regional(25)))

    rows = []
    for fname, field in fields.items():
        field = np.where(mask & np.isfinite(np.asarray(field, np.float32)),
                         np.asarray(field, np.float32), 0.0)
        try:
            pred = h50.emit(field, mask, SPACING_PX, BUDGET)
        except Exception as exc:
            print(f"{fname:22s} ERROR {exc!r}", flush=True)
            continue
        w = max_kernel_filter(pred)
        s = float(pred.sum())
        rec = dict(field=fname)
        for iname, d in inst.items():
            rec[iname] = round(dti_parts(float(w[d["g"]].sum()), d["k"], s,
                                         float((pred * d["kappa"]).sum())), 5)
        lid = [rec[k] for k in INSTRUMENTS]
        rec["mean_lidar"] = round(float(np.mean(lid)), 5)
        rows.append(rec)
        print(f"{fname:22s} " + " ".join(f"{k}={rec[k]:.4f}" for k in inst)
              + f" mean={rec['mean_lidar']:.4f} ({time.time()-started:.0f}s)", flush=True)

    out = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "spacing_px": SPACING_PX, "budget": BUDGET,
        "metric": "exact competition DTI via gems47.metric reductions, alpha=0.2 beta=0.8",
        "instruments": {k: v["k"] for k, v in inst.items()},
        "decision_rule": "pre-registered: maximise the mean DTI over the five off-catalogue "
                         "lidar scarp-peak instruments; sgmc_offcat is reported but is "
                         "negatively rank-correlated with the reported leaderboard scores",
        "rows": rows,
        "elapsed_seconds": round(time.time() - started, 2),
    }
    path = ROOT / "evidence" / "h50" / "field-refine.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(f"-> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
