#!/usr/bin/env python3
"""Measure the owner-reported d2.8 reference raster (reference/h33-2-b2-zeros.tif).

Answers, with measurements only, the standing question "why did the GEMSDOE32
h33-2-b2 submission report the family-high 0.2778":

1.  **Geometry.** How many unit dots, at what nearest-neighbour spacing, how is the
    mass distributed by distance to the USGS/INGENIOUS catalogue, and how much sits
    inside the TIGER-road / BLM-closed-claim noise masks that H60 excludes.
2.  **Lineage.** Mask Jaccard against every restored scored sibling raster and every
    published download in this checkout: is h33-2-b2 the same emission as the scored
    d1.5 (0.2477) or d2.8 (0.2600) rasters, a pruned subset of one of them, or a
    distinct emission?
3.  **Proxy DTI.** Whole-map DTI against the frozen instrument set (the same
    instruments the H50/H60 screens use), so the reference can be compared with the
    candidates on identical ground.
4.  **Pruning mechanism (algebra, not attribution).** DTI as a function of retained
    top-mass fraction against each instrument, showing the exact mechanism by which
    deleting low-credit dots raises DTI at fixed truth — the mechanism the withdrawn
    causal claim was about. This is a property of the metric, not evidence about which
    file earned any leaderboard row.

Attribution caveat (carried everywhere): the public leaderboard is participant-level.
No organiser receipt maps the 0.2778 row to this TIFF, and the owner page marks the
raster unscored; the 0.2778 figure is owner-reported. See knowledge/05 and
docs/why-02778.md.

Run:  python3 scripts/analyze_h33_reference.py     (needs the restored data group)
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from gems47 import grid as G
from gems47 import h50, h60
from gems47s3.metric import dti, kernel

DATA = G.data_dir()
EV = ROOT / "evidence"

INSTRUMENTS = {
    "lappos_t200_d3": ("lappos_max", 200, 3),
    "lapneg_t200_d3": ("lapneg_max", 200, 3),
    "step_t150_d3": ("step_max", 150, 3),
    "cross_t200_d3": ("cross_max", 200, 3),
    "upface_t200_d3": ("upface_max", 200, 3),
    "union_t200_d3": ("union", 200, 3),
}

PRIOR_GLOBS = (
    ".cache/gems_data/scored/*.tif",
    ".cache/gems_data/reference/*.tif",
    "docs/downloads/**/*.tif",
    "submission/*.tif",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def nearest_neighbour_spacing(dots: np.ndarray) -> dict:
    """Nearest-neighbour distance (px) from every dot to its closest other dot."""
    ys, xs = np.nonzero(dots)
    pts = np.column_stack([ys, xs]).astype(np.float64)
    # blockwise exact NN over a 12.3M-cell grid: use a KD-tree via scipy cKDTree
    from scipy.spatial import cKDTree
    tree = cKDTree(pts)
    d, _ = tree.query(pts, k=2)
    nn = d[:, 1]
    qs = np.quantile(nn, [0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99])
    return dict(n_dots=int(dots.sum()), min=float(nn.min()), mean=float(nn.mean()),
                median=float(np.median(nn)),
                quantiles={f"p{int(q*100)}": round(float(v), 4) for q, v in
                           zip([0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99], qs)},
                hist_1px={str(k): int(v) for k, v in zip(*np.histogram(
                    nn, bins=[0, 1, 1.5, 2, 2.5, 3, 3.5, 4, 5, 7, 10, 1e9]))})


def dist_hist(dcat: np.ndarray, dots: np.ndarray) -> dict:
    v = dcat[dots]
    edges = [0, 1, 2, 3, 5, 10, 30, 1e9]
    hist, _ = np.histogram(v, bins=edges)
    keys = ["0-1", "1-2", "2-3", "3-5", "5-10", "10-30", "30+"]
    return {k: int(h) for k, h in zip(keys, hist)}


def pruning_curve(dots: np.ndarray, truth: np.ndarray, valid: np.ndarray,
                  fractions=(1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1)) -> list[dict]:
    """DTI after keeping only the top-`f` DOTS by realised kernel weight vs `truth`.

    The realised kernel weight of a dot is k(d(dot, nearest truth pixel)).  Ranking
    is over the dots only (never over the empty cells, whose weight is undefined as
    a *dot* credit), so kept_fraction=1.0 reproduces the input emission exactly —
    asserted below against a direct dti() call.  Deleting the lowest-credit dots
    first is the best possible pruning order for DTI against this instrument; the
    curve therefore shows the maximum DTI gain any mass deletion can achieve
    against this proxy, and where it saturates.
    """
    g = np.asarray(truth, bool) & valid
    k_near = kernel(ndi.distance_transform_edt(~g))
    cand = np.asarray(dots, bool) & valid
    ys, xs = np.nonzero(cand)
    w = k_near[ys, xs]
    order = np.argsort(-w, kind="stable")
    n = int(ys.size)
    direct = dti(cand.astype(np.float32), g.astype(np.int8), valid=valid)
    out = []
    for f in fractions:
        keep = round(f * n)
        sel = np.zeros(cand.shape, bool)
        sel[ys[order[:keep]], xs[order[:keep]]] = True
        r = dti(sel.astype(np.float32), g.astype(np.int8), valid=valid)
        out.append(dict(kept_fraction=f, kept_dots=keep,
                        dti=round(float(r["dti"]), 6),
                        tp=round(float(r["tp"]), 3), fp=round(float(r["fp"]), 3),
                        fn=round(float(r["fn"]), 3)))
    # invariant: the full-mass row must reproduce the direct whole-set DTI exactly
    assert out[0]["kept_dots"] == n
    assert abs(out[0]["dti"] - round(float(direct["dti"]), 6)) < 1e-9, \
        "pruning curve at f=1.0 must reproduce the direct DTI"
    return out


def main() -> int:
    t0 = time.time()
    EV.mkdir(parents=True, exist_ok=True)
    grids = h50.read_grid(DATA)
    evaluated = grids["evaluated"]
    dcat = ndi.distance_transform_edt(~grids["catalogue"]).astype(np.float32)

    ref_path = DATA / "reference" / "h33-2-b2-zeros.tif"
    with rasterio.open(ref_path) as src:
        ref = np.nan_to_num(src.read(1).astype(np.float32), nan=0.0)
    dots = ref > 0

    # ---- instruments (frozen H50/H60 set)
    ch = h50.lidar_scarp_channels(DATA)
    valid_lidar = ch["valid"] > 0
    instruments = {}
    for iname, (chan, thr, md) in INSTRUMENTS.items():
        if chan == "union":
            m = np.zeros(evaluated.shape, bool)
            for nm in h50.LIDAR_SCARP_CHANNELS:
                m |= h50.lidar_peaks(ch[nm], valid_lidar, thr, md)
        else:
            m = h50.lidar_peaks(ch[chan], valid_lidar, thr, md)
        instruments[iname] = m & grids["footprint"] & ~grids["catalogue"] & evaluated
    sgmc = h50.instrument_sgmc_offcatalogue(DATA) & evaluated
    instruments["sgmc_offcat"] = sgmc
    del ch, valid_lidar

    noise = h60.noise_ok(DATA)

    # ---- geometry
    geom = nearest_neighbour_spacing(dots)
    geom["unique_values"] = sorted(float(v) for v in np.unique(ref))
    geom["dots_total"] = int(dots.sum())
    geom["dots_on_evaluated"] = int((dots & evaluated).sum())
    geom["dots_on_catalogue"] = int((dots & grids["catalogue"]).sum())
    geom["dots_outside_footprint"] = int((dots & ~grids["footprint"]).sum())
    geom["dots_in_noise_masks"] = int((dots & ~noise).sum())
    geom["dist_to_catalogue_hist_px"] = dist_hist(dcat, dots & evaluated)
    geom["sha256"] = sha256(ref_path)

    # ---- proxy DTI, whole evaluated map
    proxy = {}
    for iname, truth in instruments.items():
        r = dti(ref, truth.astype(np.int8), valid=evaluated)
        proxy[iname] = dict(dti=round(float(r["dti"]), 6), tp=round(float(r["tp"]), 3),
                            fp=round(float(r["fp"]), 3), fn=round(float(r["fn"]), 3),
                            n_truth=int(r["n_truth"]))

    # ---- pruning mechanism against the primary instrument and SGMC
    pruning = {
        "lappos_t200_d3": pruning_curve(dots & evaluated, instruments["lappos_t200_d3"],
                                        evaluated),
        "sgmc_offcat": pruning_curve(dots & evaluated, instruments["sgmc_offcat"],
                                     evaluated),
    }

    # ---- lineage: mask Jaccard vs every prior raster reachable from this checkout
    rows = []
    for pattern in PRIOR_GLOBS:
        for q in sorted(ROOT.glob(pattern)):
            if q.resolve() == ref_path.resolve():
                continue
            try:
                with rasterio.open(q) as src:
                    a = np.nan_to_num(src.read(1).astype(np.float32), nan=0.0) > 0
            except Exception as exc:  # audit must survive a bad file
                rows.append(dict(path=str(q.relative_to(ROOT)), error=repr(exc)))
                continue
            inter = int((a & dots).sum())
            union = int((a | dots).sum())
            subset_of = bool(inter == int(dots.sum())) and inter > 0
            rows.append(dict(path=str(q.relative_to(ROOT)), dots=int(a.sum()),
                             intersection=inter, union=union,
                             jaccard=round(inter / max(union, 1), 6),
                             reference_is_subset_of_this=subset_of,
                             exact_match=bool(inter == union and inter > 0)))
    rows.sort(key=lambda r: -r.get("jaccard", 0.0))

    out = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "question": "why did the GEMSDOE32 h33-2-b2 submission report the family-high "
                    "0.2778 — geometry, lineage and proxy DTI of the owner-reported "
                    "d2.8 reference raster",
        "attribution_caveat": "The public leaderboard is participant-level. No organiser "
                              "receipt maps the 0.2778 row to this TIFF and the owner page "
                              "marks the raster unscored; 0.2778 is owner-reported. "
                              "Nothing here authenticates a score-to-file mapping.",
        "raster": "reference/h33-2-b2-zeros.tif (hash-pinned owner mirror from "
                  "buffedlizard55-lab/GEMSDOE32; not organiser-authenticated bytes)",
        "geometry": geom,
        "proxy_dti_whole_evaluated_map": proxy,
        "pruning_mechanism": {
            "definition": "keep only the top-f dots by realised kernel weight against the "
                          "named instrument; the best possible deletion order for DTI "
                          "against that proxy",
            "curves": pruning,
        },
        "lineage_jaccard": dict(compared=len(rows),
                                exact_matches=sum(1 for r in rows if r.get("exact_match")),
                                max_jaccard=round(max((r.get("jaccard", 0.0) for r in rows),
                                                      default=0.0), 6),
                                reference_is_subset_of=[
                                    r["path"] for r in rows
                                    if r.get("reference_is_subset_of_this")],
                                rows=rows),
        "elapsed_seconds": round(time.time() - t0, 2),
    }
    (EV / "h33_reference_analysis.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"geometry": {k: geom[k] for k in
                                   ("dots_total", "dots_on_evaluated", "median",
                                    "dots_in_noise_masks")},
                      "proxy": proxy,
                      "lineage": out["lineage_jaccard"]}, indent=2)[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
