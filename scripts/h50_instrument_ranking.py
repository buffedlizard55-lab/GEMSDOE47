#!/usr/bin/env python3
"""H50 evidence, part 1 -- which local proxy truth reproduces the leaderboard ORDERING?

For every owner-reported public-score raster restored in this checkout, compute the exact
competition DTI against each candidate truth population and rank-correlate with the
reported score.  Writes ``evidence/h50/instrument-ranking.json``.

The DTI values use the same algebraic reductions as ``gems47.metric.score``
(``FN = |G| - TP`` and ``FP = S - Phi``), evaluated through that module's kernel offsets,
so they are the verified metric rather than a re-implementation.

Everything here is computed from hash-pinned owner mirrors.  No organiser receipt links a
participant score to a TIFF, so the rows are *owner-reported pairs*, and the correlation is
evidence about the proxy, not about a certified score.  With 13 pairs the standard error of
a Spearman rho is about 0.29, so every row also carries a permutation reference.
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
from scipy.stats import kendalltau, spearmanr  # noqa: E402

from gems47 import grid as G  # noqa: E402
from gems47 import h50  # noqa: E402
from gems47.metric import ALPHA, BETA, max_kernel_filter  # noqa: E402

# (mirror-relative path, owner-reported public DTI).  Labels are preserved verbatim from
# the user-supplied score history in the README standing brief.
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
SEED = 20261007


def dti_from_parts(w_sum: float, k: int, s: float, phi: float) -> float:
    """DTI from the verified reductions: TP=T, FN=K-T, FP=S-Phi."""
    t = float(w_sum)
    den = t + ALPHA * (s - phi) + BETA * (k - t)
    return float(t / den) if den > 0 else 0.0


def build_candidates(data: Path, grids: dict, ch: dict) -> dict:
    foot, cat, ev = grids["footprint"], grids["catalogue"], grids["evaluated"]
    valid = ch["valid"] > 0
    cands: dict[str, tuple[np.ndarray, np.ndarray, str]] = {}
    cands["catalogue"] = (cat, foot, "given USGS/INGENIOUS catalogue (masked out by the organiser)")
    sgmc = h50.instrument_sgmc_offcatalogue(data)
    cands["sgmc_offcat"] = (sgmc, ev, "SGMC faults off the catalogue and >300 m from it")
    cc, n = ndi.label(cat, structure=np.ones((3, 3), bool))
    sizes = ndi.sum(np.ones_like(cc), cc, index=range(1, n + 1)) if n else []
    iso = np.isin(cc, [i + 1 for i, s in enumerate(sizes) if s <= 12]) if n else np.zeros_like(cat)
    cands["iso_catalogue"] = (iso, foot, "catalogue components of <=12 px (isolated traces)")
    cands["flank_catalogue"] = (cat & ~iso, foot, "catalogue components of >12 px (clustered traces)")
    cands["cat_plus_sgmc_offcat"] = (cat | sgmc, foot, "catalogue union SGMC off-catalogue")

    for name in h50.LIDAR_SCARP_CHANNELS:
        for thr, md in ((200, 3), (200, 5), (150, 3), (250, 3)):
            m = h50.lidar_peaks(ch[name], valid, thr, md)
            m &= foot & ~cat
            cands[f"lidpeak_{name}_t{thr}_d{md}"] = (m, ev, f"off-catalogue peaks of lidar {name}")
    union = np.zeros(foot.shape, bool)
    for name in h50.LIDAR_SCARP_CHANNELS:
        union |= h50.lidar_peaks(ch[name], valid, 200, 3)
    cands["lidpeak_union_t200_d3"] = (union & foot & ~cat, ev,
                                      "union of the six scarp-channel peak sets")
    return cands


def main() -> int:
    started = time.time()
    data = G.data_dir()
    grids = h50.read_grid(data)
    ch = h50.lidar_scarp_channels(data)

    preds, reported = [], []
    for rel, score in ARTIFACTS:
        with rasterio.open(Path(data) / rel) as src:
            p = np.nan_to_num(src.read(1).astype(np.float32), nan=0.0)
        preds.append(np.where(grids["evaluated"], p, 0.0))
        reported.append(float(score))
    reported = np.asarray(reported)
    # w_i(x) = credit a truth pixel at x would receive from prediction i
    w = [max_kernel_filter(p) for p in preds]
    s = [float(p.sum()) for p in preds]
    print(f"[setup] {len(preds)} predictions, {time.time() - started:.0f}s", flush=True)

    cands = build_candidates(data, grids, ch)
    rows = {}
    for name, (truth, dom, note) in cands.items():
        if int(truth.sum()) < 50:
            rows[name] = dict(skipped=True, n_truth=int(truth.sum()), note=note)
            continue
        g = truth & dom
        k = int(g.sum())
        kappa = max_kernel_filter(g.astype(np.float64))
        vals = np.asarray([dti_from_parts(float(ww[g].sum()), k, si,
                                          float((pi * kappa).sum()))
                           for ww, pi, si in zip(w, preds, s)])
        rho = float(spearmanr(vals, reported).statistic)
        tau = float(kendalltau(vals, reported).statistic)
        rows[name] = dict(n_truth=k, note=note, spearman=round(rho, 4),
                          kendall=round(tau, 4), dti=[round(float(v), 5) for v in vals],
                          positive_rank_correlation=bool(rho > 0))
        print(f"{name:30s} n={k:7d} spearman={rho:+.3f} kendall={tau:+.3f}", flush=True)

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

    positive = [k for k, v in rows.items() if v.get("positive_rank_correlation")]
    out = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "question": "which local proxy truth reproduces the ordering of owner-reported public DTI?",
        "n_artifacts": len(ARTIFACTS),
        "artifacts": [Path(p).name for p, _ in ARTIFACTS],
        "reported_scores": [float(v) for _, v in ARTIFACTS],
        "score_provenance": "owner-reported public-leaderboard values preserved in the README "
                            "brief; no organiser receipt links any participant score to a TIFF",
        "metric": "gems47.metric.score reductions (FN=|G|-TP, FP=S-Phi), alpha=0.2 beta=0.8",
        "permutation_reference": "two-sided permutation p over 20000 relabellings of the "
                                 "reported scores; with 13 pairs a Spearman rho of 0.55 is "
                                 "about p=0.05",
        "positive_correlations": positive,
        "rows": rows,
        "elapsed_seconds": round(time.time() - started, 2),
    }
    path = ROOT / "evidence" / "h50" / "instrument-ranking.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(f"-> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
