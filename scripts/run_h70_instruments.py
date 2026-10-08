#!/usr/bin/env python3
"""H70 -- instrument refinement, part 2: which off-catalogue proxy population reproduces
the leaderboard ORDERING of the 13 owner-reported scored artifacts best?

The frozen population list (docs/research/h65-hypotheses-preregistered.md):
* ``downface_max`` peaks at t200 d3, stratified by catalogue distance (near <= 3 px
  vs far > 3 px) and filtered by the H60 noise masks (the one H60 channel H64 left out);
* SGMC off-catalogue at finer and coarser catalogue-distance thresholds (>100 m, >200 m,
  >500 m, vs the frozen >300 m) and SGMC near (off-catalogue, <= 3 px);
* the 21 INGENIOUS volcanic-vent pixels as an explicitly exploratory diagnostic
  (n reported; no conclusion may rest on it).

Method: identical to H64 (exact DTI through the verified ``gems47.metric``
reductions, Spearman/Kendall against the owner-reported scores, two-sided
permutation p over 20,000 relabellings, seed 20261008 -- the seed differs from
H64's because the population list differs; the method is identical).  The 13
(raster, score) pairs are owner-reported, not organiser receipts; with 13 pairs
the standard error of a Spearman rho is about 0.29, so every row carries the
permutation reference.  Populations with fewer than 50 truth pixels are skipped,
except the vent diagnostic which is always computed with its n reported.

Writes ``evidence/h65/instrument-refinement.json``.
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

import numpy as np
import rasterio
from scipy.stats import kendalltau, spearmanr

from gems47 import grid as G
from gems47 import h50, h60, h65
from gems47.metric import ALPHA, BETA, max_kernel_filter

ARTIFACTS = [
    ("scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif", 0.1922),
    ("scored/gems19-h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan.tif", 0.1894),
    ("scored/gems16-h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan.tif", 0.1855),
    ("scored/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif", 0.2477),
    ("scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif", 0.2600),
    ("scored/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif", 0.2449),
    ("scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif", 0.0904),
    ("scored/8GEMSDOE_Hedge-v2_submission.tif", 0.1563),
    ("scored/gems10-h25-ctx-ridge-20260927T232947704150Z-6452ae1d00.tif", 0.1280),
    ("scored/gems10-h28-dotted-ridge-20260928T020256236880Z-6452ae1d00.tif", 0.1839),
    ("scored/gemsdoe-ens12-adopted-7f00890a.tif", 0.1563),
    ("scored/gemsdoe9-PLACEHOLDER-2314b599.tif", 0.0107),
    ("reference/h33-2-b2-zeros.tif", 0.2778),
]

PERMUTATION_DRAWS = 20000
SEED = 20261008
MIN_TRUTH = 50


def dti_from_parts(w_sum: float, k: int, s: float, phi: float) -> float:
    t = float(w_sum)
    den = t + ALPHA * (s - phi) + BETA * (k - t)
    return float(t / den) if den > 0 else 0.0


def main() -> int:
    started = time.time()
    data = G.data_dir()
    grids = h50.read_grid(data)
    ch = h50.lidar_scarp_channels(data)
    valid = ch["valid"] > 0
    foot, cat, ev = grids["footprint"], grids["catalogue"], grids["evaluated"]
    dcat = h60.catalogue_distance(data)
    nmask = h60.noise_ok(data)

    preds, reported = [], []
    for rel, score in ARTIFACTS:
        with rasterio.open(Path(data) / rel) as src:
            p = np.nan_to_num(src.read(1).astype(np.float32), nan=0.0)
        preds.append(np.where(ev, p, 0.0))
        reported.append(float(score))
    reported = np.asarray(reported)
    w = [max_kernel_filter(p) for p in preds]
    s = [float(p.sum()) for p in preds]
    print(f"[setup] {len(preds)} predictions ({time.time()-started:.0f}s)", flush=True)

    down = h50.lidar_peaks(ch["downface_max"], valid, 200, 3) & foot & ~cat
    del ch
    vents = h65.volcanic_vent_pixels(data, foot.shape[0], foot.shape[1])
    cands: dict[str, tuple[np.ndarray, np.ndarray, str, bool]] = {
        "downface_t200_d3_near": (down & (dcat <= 3.0), ev,
                                 "downface_max peaks within 3 px of the catalogue", False),
        "downface_t200_d3_far": (down & (dcat > 3.0), ev,
                                "downface_max peaks farther than 3 px", False),
        "downface_t200_d3_roadok": (down & nmask, ev,
                                   "downface_max peaks on noise-ok cells", False),
        "sgmc_offcat_gt100m": (h65.instrument_sgmc_threshold(data, 1.0), ev,
                               "SGMC faults off-catalogue, >100 m from it", False),
        "sgmc_offcat_gt200m": (h65.instrument_sgmc_threshold(data, 2.0), ev,
                               "SGMC faults off-catalogue, >200 m from it", False),
        "sgmc_offcat_gt500m": (h65.instrument_sgmc_threshold(data, 5.0), ev,
                               "SGMC faults off-catalogue, >500 m from it", False),
        "sgmc_offcat_near": (h65.instrument_sgmc_near(data, 3.0), ev,
                             "SGMC faults off-catalogue but within 3 px of it", False),
        "volcanic_vents_exploratory": (vents, ev,
                                      "INGENIOUS volcanic-vent pixels; EXPLORATORY, n=21", True),
    }

    rows = {}
    for name, (truth, dom, note, exploratory) in cands.items():
        g = truth & dom
        k = int(g.sum())
        if k < MIN_TRUTH and not exploratory:
            rows[name] = dict(skipped=True, n_truth=k, note=note)
            continue
        kappa = max_kernel_filter(g.astype(np.float64))
        vals = np.asarray([dti_from_parts(float(ww[g].sum()), k, si,
                                          float((pi * kappa).sum()))
                           for ww, pi, si in zip(w, preds, s)])
        rho = float(spearmanr(vals, reported).statistic)
        tau = float(kendalltau(vals, reported).statistic)
        rows[name] = dict(n_truth=k, note=note, spearman=round(rho, 4),
                          kendall=round(tau, 4), dti=[round(float(v), 5) for v in vals],
                          positive_rank_correlation=bool(rho > 0),
                          exploratory=bool(exploratory))
        print(f"{name:28s} n={k:7d} spearman={rho:+.3f} kendall={tau:+.3f}", flush=True)

    rng = np.random.default_rng(SEED)
    for name, row in rows.items():
        if row.get("skipped"):
            continue
        vals = np.asarray(row["dti"])
        obs = float(spearmanr(vals, reported).statistic)
        draws = np.array([spearmanr(vals, rng.permutation(reported)).statistic
                          for _ in range(PERMUTATION_DRAWS)])
        row["permutation_p_two_sided"] = float((np.abs(draws) >= abs(obs)).mean())
        row["permutation_draws"] = PERMUTATION_DRAWS
        row["permutation_seed"] = SEED

    out = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "question": "do the remaining (downface, SGMC-variant, vent) populations reproduce "
                    "the owner-reported leaderboard ordering better than the H64 set?",
        "preregistration": "docs/research/h65-hypotheses-preregistered.md (H70)",
        "n_artifacts": len(ARTIFACTS),
        "artifacts": [a for a, _ in ARTIFACTS],
        "reported_scores": [float(x) for x in reported],
        "score_provenance": "owner-reported public-leaderboard values; no organiser receipt "
                            "links any participant score to a TIFF",
        "permutation_reference": "two-sided permutation p over 20000 relabellings; with 13 "
                                 "pairs a Spearman rho of 0.55 is about p=0.05",
        "rows": rows,
        "elapsed_seconds": round(time.time() - started, 2),
    }
    out_path = ROOT / "evidence" / "h65" / "instrument-refinement.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
