#!/usr/bin/env python3
"""H50 evidence, part 2 -- which 100 m-scale field ranks the off-catalogue scarps best?

Each candidate field is emitted with the real greedy spaced emission at a fixed budget and
spacing, then scored with the exact competition DTI against several instruments.  Writes
``evidence/h50/field-scan.json``.

Only the official 19-band raster, the acquisition-block raster and (for the controls) the
restored prior rasters are read.  No label enters any field: ``labels.tif`` is used only to
*remove* catalogue pixels, exactly as the organiser masks them.
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
from gems47.metric import ALPHA, BETA, max_kernel_filter  # noqa: E402
from gems47s3.geomorph import (  # noqa: E402
    curvature,
    detrend,
    line_response,
    lrm,
    rank_scale,
    scarp_step,
    slope_variability,
    tpi,
)

SPACING_PX = 2.8
BUDGET = 37_654

# name -> callable(bands, blocks, mask) -> field
FIELDS = {
    "slope_block_rank": lambda b, k, m: h50.block_rank(b["det_elev_slope"], k, m),
    "slope_global_rank": lambda b, k, m: rank_scale(np.where(m, b["det_elev_slope"], np.nan)),
    "slope_raw": lambda b, k, m: np.where(m, b["det_elev_slope"], 0.0),
    "scarp_elev_hw3": lambda b, k, m: scarp_step(b["det_elev"], 3),
    "scarp_elev_hw5": lambda b, k, m: scarp_step(b["det_elev"], 5),
    "scarp_elev_hw9": lambda b, k, m: scarp_step(b["det_elev"], 9),
    "scarp_elev_hw13": lambda b, k, m: scarp_step(b["det_elev"], 13),
    "lrm_elev_r9": lambda b, k, m: lrm(b["det_elev"], 9),
    "lrm_slope_r9": lambda b, k, m: lrm(b["det_elev_slope"], 9),
    "tpi_elev_r6": lambda b, k, m: np.abs(tpi(b["det_elev"], 6)),
    "curv_elev_s2": lambda b, k, m: curvature(b["det_elev"], 2.0),
    "detrend_elev_r9": lambda b, k, m: detrend(b["det_elev"], 9),
    "slopevar_elev_r9": lambda b, k, m: slope_variability(b["det_elev"], 9),
    "line_rtp_s2": lambda b, k, m: np.abs(line_response(b["rtp"], 2.0)),
    "tc_raw": lambda b, k, m: b["tc"],
    "slope_x_scarp9": lambda b, k, m: rank_scale(np.where(m, b["det_elev_slope"], np.nan))
                                    * rank_scale(np.where(m, scarp_step(b["det_elev"], 9), np.nan)),
    "slope_x_line_rtp": lambda b, k, m: rank_scale(np.where(m, b["det_elev_slope"], np.nan))
                                       * rank_scale(np.where(m, np.abs(line_response(b["rtp"], 2.0)), np.nan)),
    "slope_x_curv2": lambda b, k, m: rank_scale(np.where(m, b["det_elev_slope"], np.nan))
                                    * rank_scale(np.where(m, curvature(b["det_elev"], 2.0), np.nan)),
    "slope_x_lrm9": lambda b, k, m: rank_scale(np.where(m, b["det_elev_slope"], np.nan))
                                   * rank_scale(np.where(m, lrm(b["det_elev"], 9), np.nan)),
    "slope_x_tpi6": lambda b, k, m: rank_scale(np.where(m, b["det_elev_slope"], np.nan))
                                   * rank_scale(np.where(m, np.abs(tpi(b["det_elev"], 6)), np.nan)),
    "slope_x_tc": lambda b, k, m: rank_scale(np.where(m, b["det_elev_slope"], np.nan))
                                 * rank_scale(np.where(m, b["tc"], np.nan)),
    "slope_x_tmihg": lambda b, k, m: rank_scale(np.where(m, b["det_elev_slope"], np.nan))
                                    * rank_scale(np.where(m, b["tmi_hg"], np.nan)),
    "slope_x_grav_hg": lambda b, k, m: rank_scale(np.where(m, b["det_elev_slope"], np.nan))
                                      * rank_scale(np.where(m, b["iso_grav_anom_hg"], np.nan)),
    "slope_x_geod2inv": lambda b, k, m: rank_scale(np.where(m, b["det_elev_slope"], np.nan))
                                       * rank_scale(np.where(m, b["geod_2ndinv"], np.nan)),
    "slope_x_cond": lambda b, k, m: rank_scale(np.where(m, b["det_elev_slope"], np.nan))
                                   * rank_scale(np.where(m, b["cond_surf"], np.nan)),
    "slope_x_depth": lambda b, k, m: rank_scale(np.where(m, b["det_elev_slope"], np.nan))
                                    * rank_scale(np.where(m, b["depth_to_base_surf"], np.nan)),
    "slope_minus_regional": lambda b, k, m: rank_scale(np.where(
        m, b["det_elev_slope"] - ndi.gaussian_filter(b["det_elev_slope"], 25, mode="nearest"), np.nan)),
    "slope_smooth1": lambda b, k, m: rank_scale(np.where(
        m, ndi.gaussian_filter(b["det_elev_slope"], 1.0, mode="nearest"), np.nan)),
    "grad_from_elev": lambda b, k, m: rank_scale(np.where(
        m, np.hypot(ndi.gaussian_filter(b["det_elev"], 1.5, order=(0, 1), mode="nearest"),
                    ndi.gaussian_filter(b["det_elev"], 1.5, order=(1, 0), mode="nearest")), np.nan)),
}

BAND_INDEX = {"det_elev": 12, "det_elev_slope": 19, "rtp": 2, "tc": 6,
              "iso_grav_anom_hg": 18, "tmi_hg": 3, "geod_2ndinv": 4,
              "cond_surf": 17, "depth_to_base_surf": 15}

# instrument name -> (truth builder, domain key)
INSTRUMENTS = {
    "lappos_t200_d3": ("lappos_max", 200, 3),
    "lappos_t200_d5": ("lappos_max", 200, 5),
    "lapneg_t200_d3": ("lapneg_max", 200, 3),
    "step_t150_d3": ("step_max", 150, 3),
    "cross_t200_d3": ("cross_max", 200, 3),
    "upface_t200_d3": ("upface_max", 200, 3),
    "union_t200_d3": ("union", 200, 3),
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
        bands = {}
        for name, idx in BAND_INDEX.items():
            a = src.read(idx).astype(np.float32)
            a[~np.isfinite(a)] = 0.0
            a[a < -1e30] = 0.0
            bands[name] = a

    ch = h50.lidar_scarp_channels(data)
    valid = ch["valid"] > 0
    inst = {}
    for iname, (chan, thr, md) in INSTRUMENTS.items():
        if chan == "union":
            m = np.zeros(mask.shape, bool)
            for nm in h50.LIDAR_SCARP_CHANNELS:
                m |= h50.lidar_peaks(ch[nm], valid, thr, md)
        else:
            m = h50.lidar_peaks(ch[chan], valid, thr, md)
        m &= grids["footprint"] & ~grids["catalogue"]
        g = m & mask
        inst[iname] = dict(g=g, kappa=max_kernel_filter(g.astype(np.float64)), k=int(g.sum()))
    sgmc = h50.instrument_sgmc_offcatalogue(data) & mask
    inst["sgmc_offcat"] = dict(g=sgmc, kappa=max_kernel_filter(sgmc.astype(np.float64)),
                               k=int(sgmc.sum()))
    print("[setup] instruments", {k: v["k"] for k, v in inst.items()}, flush=True)

    rows = []
    for fname, fn in FIELDS.items():
        try:
            field = np.asarray(fn(bands, blocks, mask), np.float32)
            field = np.where(mask & np.isfinite(field), field, 0.0)
            pred = h50.emit(field, mask, SPACING_PX, BUDGET)
        except Exception as exc:  # a field that cannot be emitted is recorded, not hidden
            print(f"{fname:24s} ERROR {exc!r}", flush=True)
            rows.append(dict(field=fname, error=repr(exc)))
            continue
        w = max_kernel_filter(pred)
        s = float(pred.sum())
        rec = dict(field=fname, n_dots=int((pred > 0).sum()), emitted_mass=s)
        for iname, d in inst.items():
            rec[iname] = round(dti_parts(float(w[d["g"]].sum()), d["k"], s,
                                         float((pred * d["kappa"]).sum())), 5)
        rows.append(rec)
        print(f"{fname:24s} " + " ".join(f"{k}={rec[k]:.4f}" for k in inst),
              f"({time.time() - started:.0f}s)", flush=True)

    out = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "spacing_px": SPACING_PX, "budget": BUDGET,
        "emission": "greedy top-ranked selection at a minimum Euclidean spacing, unit dots, "
                    "catalogue pixels excluded from the emission domain",
        "metric": "exact competition DTI via gems47.metric reductions, alpha=0.2 beta=0.8",
        "instruments": {k: v["k"] for k, v in inst.items()},
        "instrument_note": "lappos/lapneg/step/cross/upface are off-catalogue local maxima of the "
                           "organiser-supplied 1 m lidar scarp stack; sgmc_offcat is the "
                           "independent SGMC off-catalogue compilation",
        "rows": rows,
        "elapsed_seconds": round(time.time() - started, 2),
    }
    path = ROOT / "evidence" / "h50" / "field-scan.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(f"-> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
