#!/usr/bin/env python3
"""Build the H1 research candidate: radiometric alteration-halo emission.

Per notes/HYPOTHESES.md H1, a speculative rank-grid affinity from Th/K, U/K,
and U/Th is transformed with a Laplacian of Gaussian and emitted only outside
the 300 m catalogue-kernel reach. The ratios are uint8 rank proxies, not
physical geochemical units; this is an unvalidated mechanism hypothesis.

This is a RESEARCH screen using a public group-hosted mirror, not authenticated
organizer downloads. A previous matched-mass catalogue-alignment screen was
negative (0.0156 vs 0.0369 seeded random), while the annulus-restricted blocked
score is vacuous by construction. It is not promoted and this script refuses
to write into docs/downloads/. A sidecar receipt records input hashes.

Inputs (public mirror bytes, SHA-256 pinned against GEMSDOE24 manifests):
  work/external/geodawn_rad_u8.tif        K, Th, U, TC rank grids
  work/external/geodawn_extensions_u8.tif ThK, UK, UTh, TMI_up150 rank grids
  work/bridge/labels.tif                  mirrored public catalogue labels + footprint

Usage:  python3 scripts/build_h1_candidate.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import numpy as np
import rasterio
from scipy import ndimage
from scipy.spatial import cKDTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

WORK = os.path.join(ROOT, "work")
OUTDIR = os.path.join(WORK, "candidates")
RAD = os.path.join(WORK, "external", "geodawn_rad_u8.tif")
EXT = os.path.join(WORK, "external", "geodawn_extensions_u8.tif")
LABELS = os.path.join(WORK, "bridge", "labels.tif")
TEMPLATE = os.path.join(WORK, "bridge", "sample_submission.tif")

PINNED_SHA256 = {  # from GEMSDOE24/data/external/*.json manifests (fetched 2026-10-06)
    "rad": "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682",
    "ext": "a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b",
}
RAD_BANDS = ["K", "Th", "U", "TC"]              # per geodawn_rad.json
EXT_BANDS = ["ThK", "UK", "UTh", "TMI_up150"]   # per geodawn_extensions.json

ANNULUS_D_CAT_MIN = 3       # px; strictly beyond the 300 m kernel reach of a catalogue pixel
BUDGET = 18524              # matched-mass with H47-B research raster, not a spatial holdout best
SEP_PX = 3.0                # non-overlap: one dot per kernel footprint
LOG_SIGMA = 3.0             # curvature scale, px (H1: "3-5 px scale")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def require_inputs() -> None:
    for p in (RAD, EXT, LABELS, TEMPLATE):
        if not os.path.exists(p):
            raise SystemExit(f"missing input {p} — fetch it via the GitHub contents API "
                             f"(see docs/review-log.md addendum for the exact paths)")
    for key, p in (("rad", RAD), ("ext", EXT)):
        h = sha256_file(p)
        if h != PINNED_SHA256[key]:
            raise SystemExit(f"{p}: sha256 {h} != pinned {PINNED_SHA256[key]} — REFUSING to proceed")
    with rasterio.open(RAD) as ds:
        if list(ds.descriptions) != RAD_BANDS and len(ds.descriptions) != 4:
            print(f"note: rad band descriptions read as {list(ds.descriptions)!r}; "
                  f"assuming order {RAD_BANDS} per geodawn_rad.json")
        if ds.shape != (3730, 3292) or str(ds.crs) != "EPSG:32611":
            raise SystemExit("rad grid does not match the competition grid")
    with rasterio.open(EXT) as ds:
        if ds.shape != (3730, 3292) or str(ds.crs) != "EPSG:32611":
            raise SystemExit("extensions grid does not match the competition grid")


def rank01(band: np.ndarray) -> np.ndarray:
    """uint8 rank grid (nodata 0) -> float32 in [0,1]; NaN where nodata."""
    out = np.full(band.shape, np.nan, np.float32)
    m = band > 0
    out[m] = ((band[m].astype(np.float32) - 1.0) / 254.0)
    return out


def build_field() -> np.ndarray:
    with rasterio.open(EXT) as ds:
        ext = ds.read()
    thk = rank01(ext[0])          # Th/K
    uk = rank01(ext[1])           # U/K
    uth = rank01(ext[2])          # U/Th
    # Alteration affinity: high U/K, high U/Th, low Th/K (K-feldspathisation + Th
    # leaching + U mobility — the classic geothermal-halo ratio pattern).
    aff = (uk + uth + (1.0 - np.nan_to_num(thk, nan=0.5))) / 3.0
    valid = ~(np.isnan(uk) | np.isnan(uth) | np.isnan(thk))
    # curvature transform: negative LoG marks local halo maxima (blob centres)
    lof = ndimage.gaussian_laplace(np.where(valid, aff, np.nan_to_num(aff)), sigma=LOG_SIGMA)
    s = np.where(valid, -lof, -np.inf).astype(np.float32)
    return s


def greedy_independent(order_idx: np.ndarray, ys: np.ndarray, xs: np.ndarray,
                      sep: float, limit: int) -> np.ndarray:
    """Greedy max-spacing selection over candidate points already ordered best-first."""
    pts = np.c_[ys[order_idx], xs[order_idx]].astype(np.float64)
    t = cKDTree(pts)
    pairs = t.query_pairs(sep, output_type="ndarray")
    adj = {i: [] for i in range(len(pts))}
    if len(pairs):
        for a, b in pairs.astype(int):
            adj[int(a)].append(int(b))
            adj[int(b)].append(int(a))
    blocked = np.zeros(len(pts), bool)
    chosen = []
    for i in range(len(pts)):
        if blocked[i]:
            continue
        chosen.append(i)
        if len(chosen) >= limit:
            break
        for j in adj[i]:
            blocked[j] = True
    return order_idx[np.asarray(chosen, dtype=np.int64)]


def main() -> int:
    require_inputs()
    os.makedirs(OUTDIR, exist_ok=True)
    with rasterio.open(LABELS) as ds:
        lab = ds.read(1)
    foot = lab >= 0
    d_cat = ndimage.distance_transform_edt(lab != 1)
    s = build_field()
    allowed = np.isfinite(s) & foot & (d_cat > ANNULUS_D_CAT_MIN) & (s > -np.inf)
    n_allowed = int(allowed.sum())
    if n_allowed < 20 * BUDGET:
        raise SystemExit(f"not enough allowed candidates ({n_allowed}) for matched-mass selection")

    # over-select by score, then enforce non-overlap, then trim to budget
    k = min(n_allowed, 20 * BUDGET)
    flat = np.flatnonzero(allowed.ravel())
    scores = s.ravel()[flat]
    top = flat[np.argpartition(-scores, k - 1)[:k]]
    top = top[np.argsort(-s.ravel()[top], kind="stable")]
    ys, xs = np.divmod(top, s.shape[1])
    chosen = greedy_independent(np.arange(len(top)), ys, xs, SEP_PX, BUDGET)
    if len(chosen) < BUDGET:
        print(f"warning: spacing rule yielded {len(chosen)} < budget {BUDGET}; using all of them")
    sel = top[chosen]
    emit = np.zeros(lab.shape, bool)
    np.put(emit.ravel(), sel, True)
    n = int(emit.sum())

    out = np.full(lab.shape, np.nan, np.float32)
    out[foot] = 0.0
    out[emit] = 1.0

    # ---------------- exploratory diagnostics (not a promotion gate) ------------
    # An annulus-restricted mask is beyond the catalogue's 300 m kernel reach by
    # construction. Its blocked DTI against that same catalogue is therefore
    # vacuous: candidate and controls can all score zero without distinguishing
    # their geological value. The separate full-domain, matched-mass comparison
    # is a local catalogue-alignment screen only; it is not the private target
    # score and cannot establish discovery of uncatalogued faults.
    from src.gems47_blocks import blocked_scores
    truth = (lab == 1)
    rows = {"candidate": blocked_scores(out, truth, 2, 2),
            "random_control": None, "owner_reported_d2_8_reference": None}
    rng = np.random.default_rng(47)
    ctrl = np.zeros(lab.shape, np.float32)
    pick = rng.choice(flat, size=n, replace=False)
    ctrl.ravel()[pick] = 1.0
    ctrl[~foot] = np.nan
    rows["random_control"] = blocked_scores(ctrl, truth, 2, 2)
    base_p = os.path.join(WORK, "anchors", "gemsdoe33-d28-reference-20261004-426073b6b4ab-nan.tif")
    if os.path.exists(base_p):
        with rasterio.open(base_p) as ds:
            b = ds.read(1)
        inc = np.isfinite(b) & (b > 0) & (d_cat > ANNULUS_D_CAT_MIN)
        rows["owner_reported_d2_8_reference"] = blocked_scores(np.where(inc, 1.0, np.nan).astype(np.float32),
                                               truth, 2, 2)
    def _pooled(rs):
        tp = sum(r["TPw"] for r in rs); ng = sum(r["Ng"] for r in rs)
        fp = sum(r["FPw"] for r in rs)
        return 5 * tp / (tp + fp + 4 * ng) if ng else 0.0
    heldout = {k2: round(_pooled(v), 5) for k2, v in rows.items() if v is not None}

    # full-domain alignment test (same budget, no annulus restriction)
    s_full = np.where(np.isfinite(s) & foot, s, -np.inf)
    flat_all = np.flatnonzero(np.isfinite(s) & foot)
    sc_all = s_full.ravel()[flat_all]
    top_all = flat_all[np.argpartition(-sc_all, n - 1)[:n]]
    emit_all = np.zeros(lab.shape, bool)
    np.put(emit_all.ravel(), top_all, True)
    r_cand = blocked_scores(np.where(emit_all, 1.0, np.nan).astype(np.float32), truth, 2, 2)
    ctrl2 = np.zeros(lab.shape, np.float32)
    pick2 = rng.choice(flat_all, size=n, replace=False)
    ctrl2.ravel()[pick2] = 1.0
    ctrl2[~foot] = np.nan
    r_rand = blocked_scores(ctrl2, truth, 2, 2)
    alignment = {"halo_top_mass_full_domain_dti": round(_pooled(r_cand), 6),
                 "random_control_dti": round(_pooled(r_rand), 6),
                 "ratio": round(_pooled(r_cand) / max(_pooled(r_rand), 1e-9), 2)}

    # catalogue-hugging diagnostics
    d_emit = d_cat[emit]
    jac = []
    for p in sorted(os.listdir(os.path.join(WORK, "anchors"))) + sorted(os.listdir(os.path.join(ROOT, "docs", "downloads"))):
        if not p.endswith(".tif"):
            continue
        ap = os.path.join(WORK, "anchors", p)
        if not os.path.exists(ap):
            ap = os.path.join(ROOT, "docs", "downloads", p)
        with rasterio.open(ap) as ds:
            m = ds.read(1)
        m = np.isfinite(m) & (m > 0)
        j = (emit & m).sum() / (emit | m).sum()
        jac.append((round(float(j), 4), p))
    jac.sort(reverse=True)

    fn = f"gems47-h1-radhalo-matchedmass-{n}px-20261006.tif"
    dest = os.path.join(OUTDIR, fn)
    with rasterio.open(TEMPLATE) as ds:
        prof = ds.profile.copy()
    prof.update(dtype="float32", count=1, nodata=float("nan"), compress="lzw", tiled=False)
    with rasterio.open(dest, "w", **prof) as dst:
        dst.write(out, 1)
    sha = sha256_file(dest)

    receipt = {
        "artifact": fn, "kind": "RESEARCH ONLY — MIRROR-LABEL SCREEN, NOT PROMOTED, DO NOT SUBMIT",
        "hypothesis": "H1 radiometric alteration halos (ratio field → LoG curvature) in the outer annulus",
        "built_utc": "2026-10-06", "positives": n, "sha256": sha,
        "rule": {"annulus": f"d_cat > {ANNULUS_D_CAT_MIN} px", "budget": BUDGET,
                 "log_sigma_px": LOG_SIGMA, "min_separation_px": SEP_PX,
                 "affinity": "(U/K + U/Th + (1 - Th/K))/3, uint8 rank-scaled, -LoG"},
        "inputs": {"rad_sha256": sha256_file(RAD), "ext_sha256": sha256_file(EXT),
                   "labels_sha256": sha256_file(LABELS), "rad_bands": RAD_BANDS,
                   "ext_bands": EXT_BANDS},
        "diagnostics": {
            "allowed_px": n_allowed,
            "blocked_catalogue_holdout_dti_pooled_2x2_annulus_restricted": heldout,
            "annulus_holdout_note": "vacuous by construction (0.0 for every annulus-restricted mask); "
                                    "not evidence for or against private-label performance",
            "full_domain_alignment_dti_vs_catalogue": alignment,
            "median_d_cat_of_emission_px": round(float(np.median(d_emit)), 2),
            "frac_emission_within_3px_of_catalogue": round(float((d_emit <= 3).mean()), 4),
            "max_jaccard_vs_siblings": jac[:5],
        },
        "promotion_state": "NOT_PROMOTED — full-domain matched-mass catalogue DTI was 0.0156 "
                           "versus 0.0369 for seeded random in the recorded screen; the "
                           "annulus-restricted holdout is vacuous; labels are from a public mirror; "
                           "no official or private score is inferred.",
    }
    with open(dest + ".receipt.json", "w") as fh:
        json.dump(receipt, fh, indent=1)
    print(json.dumps(receipt["diagnostics"], indent=1))
    print(f"wrote {dest}\n  positives {n}  sha256 {sha[:16]}…")
    print("  receipt at " + dest + ".receipt.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
