#!/usr/bin/env python3
"""RESEARCH-ONLY H48 exploratory sweep; not a submission or promotion pipeline.

The historical exploratory pipeline, in order
--------------------------------------------
  0  bytes         restore-free: read the hash-pinned competition rasters
  1  MSCL          multi-scale curvature lineament consensus (``gems47.h48``)
  2  observations  owner-reported participant-score/raster pairs, not organizer-authenticated
  3  split         calibration half / selection half of those observations
  4  fit           belief model q, fitted on the calibration half ONLY
  5  sweep         spacing sweep of emissions under q (min-separation rule)
  6  conformal     assumption-conditional split-conformal lower-bound estimate per spacing
  7  holdout       local proxy frames: candidate vs owner-reported reference geometry
  8  emit          write a research-only diagnostic GeoTIFF (values in [0, 1])
  9  audit         read the bytes back, verify the format, check uniqueness

Every score-dependent number is conditional on unverified owner-reported mappings. H33-2-B2 is
not authenticated to participant DTI 0.2778; the d2.8 TIFF is the owner-reported d2.8 reference.
All outputs are research-only, never slot-eligible, and cannot establish organizer acceptance.

Historical command (do not run without separate authorization):
    PYTHONPATH=src python3 scripts/build_h48.py --stage all
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems47 import features as FEAT
from gems47 import grid as G
from gems47 import (
    h48,
    h49,
    lati,
)
from gems47 import h48_conformal as CF
from gems47 import metric as M

CACHE = ROOT / ".cache"
EVID = ROOT / "evidence"
UTC = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

# ---------------------------------------------------------------------------
# a priori constants (declared before any score was inspected)
# ---------------------------------------------------------------------------

#: spacing sweep, pixels at 100 m - the operating point this build must choose
SPACINGS: tuple[float, ...] = (1.5, 2.0, 2.5, 3.0, 3.5, 4.5, 6.0)

#: top fraction of the belief field that may receive dots (support confinement)
SUPPORT_FRAC = 0.03

#: absolute mass ceiling; the marginal rule normally stops long before this
BUDGET = 60_000

#: Novelty bar: the project's best previous max-equal-mass-Jaccard against every
#: prior GEMSDOE artefact (H47-GSA, recorded in evidence/shipped.json).  A field
#: that overlaps a prior submission more than this is a re-issue, not a submission.
UNIQUE_BAR = 0.0457

#: Unverified owner-reported score used only in an illustrative sensitivity comparison; never a slot gate.
DTI_OWNER_SCORE_ASSUMED = 0.2600

#: The conditional marginal rule uses an assumed owner-reported DTI of 0.2778 for H33-2-B2.
#: No organizer receipt links that participant-level row to the TIFF; the 0.2600 observation
#: also has no authenticated raster mapping. All dependent fits and comparisons are hypothetical.
DTI_BAR = 0.2778
DTI_BAR_RESTORED_ONLY = 0.2600

#: belief-model family, declared before fitting.  Row 0 is always the owner-reported reference
#: proximity prior (the strongest single predictor in the project's own screen);
#: "mscl" is the new H48 lineament-consensus signature.
MODEL_FAMILY: dict[str, list[str]] = {
    "M0_prox": ["control_prox_d2.8"],
    "M1_prox_mscl": ["control_prox_d2.8", "h48_mscl"],
    "M2_prox_mscl_shear": ["control_prox_d2.8", "h48_mscl", "geod_shearrate"],
    "M3_screen_survivors": ["control_prox_d2.8", "geod_shearrate", "rad_ThK_low", "tmi_hg",
                            "geod_dilaterate"],
    "M4_prox_mscl_wide": ["control_prox_d2.8", "h48_mscl", "geod_shearrate", "rad_ThK_low",
                          "thermal_warm_prox"],
}

L_BY_R = {1: 256, 2: 64, 3: 32, 4: 20, 5: 14}


# ---------------------------------------------------------------------------
# stage 0/1 - grids and the new detector
# ---------------------------------------------------------------------------


def template():
    return G.load_template(G.data_dir())


def band_reader(data: Path):
    path = data / "training_features.tif"
    with rasterio.open(path) as src:
        names = [d.split(" - ")[0].strip() for d in (src.descriptions or [])]
    idx = {n: i + 1 for i, n in enumerate(names)}

    def reader(name: str) -> np.ndarray:
        if name in idx:
            with rasterio.open(path) as src:
                return src.read(idx[name]).astype(np.float32)
        if name == "rad_TC":  # external radiometric total count, 8-bit quantised
            with rasterio.open(data / "external" / "geodawn_rad_u8.tif") as src:
                return src.read(4).astype(np.float32)
        raise KeyError(name)

    return reader, names


def mscl_rows(data: Path, ev: np.ndarray) -> dict:
    """Compute (or load) the three H48 consensus rows, rank-quantised to uint8.

    The rows live on the **evaluated pixel set** (footprint and not catalogue),
    in the same order as ``features.build_stack``'s ``ev_idx``, so they can be
    concatenated onto the 59-layer stack.
    """
    cache = CACHE / "h48_mscl.npz"
    if cache.exists():
        z = np.load(cache, allow_pickle=False)
        if z["consensus"].size == int(ev.sum()):
            return {k: z[k] for k in ("topo", "geophys", "consensus")}
    reader, _ = band_reader(data)
    t0 = time.time()
    res = h48.multi_scale_consensus(reader, ev, verbose=True)
    out = {"topo": res.topo_u8, "geophys": res.geophys_u8, "consensus": res.consensus_u8}
    CACHE.mkdir(exist_ok=True)
    np.savez_compressed(cache, **out)
    print(f"[h48] MSCL built in {time.time()-t0:.0f}s", flush=True)
    return out


# ---------------------------------------------------------------------------
# stage 2/3 - observations and the split
# ---------------------------------------------------------------------------


def prox_row(obs: lati.Obs, shape, ev_idx) -> np.ndarray:
    """``control_prox_<id>`` exactly as ``scripts/lati_fit.py`` defines it."""
    H, W = shape
    m = np.zeros(H * W, bool)
    m[obs.dot_flat] = True
    d = FEAT.dist_px(m.reshape(H, W), 40.0)
    row = FEAT.rank_u8(-d.ravel(), ev_idx)
    del m, d
    return row


def build_feature_matrix(data: Path, st: dict, obs: list[lati.Obs], ev: np.ndarray,
                         verbose=True) -> tuple:
    U, names = st["U"], list(st["names"])
    ev_idx, shape = st["ev_idx"], tuple(st["meta"]["shape"])
    rows, labels = [], []
    for o in obs:
        if o.id == "d2.8":
            rows.append(prox_row(o, shape, ev_idx))
            labels.append("control_prox_d2.8")
    if not any(lab == "control_prox_d2.8" for lab in labels):
        raise RuntimeError("the d2.8 observation is required for control_prox_d2.8")
    mr = mscl_rows(data, ev)
    j = names.index("rad_ThK")
    for lab, row in (("h48_mscl", mr["consensus"]), ("h48_mscl_topo", mr["topo"]),
                     ("h48_mscl_geophys", mr["geophys"]),
                     ("rad_ThK_low", (255 - U[j]).astype(np.uint8))):
        rows.append(row)
        labels.append(lab)
    Ue = np.concatenate([U, np.stack(rows)])
    names = names + labels
    del rows
    if verbose:
        print(f"[h48] feature matrix {Ue.shape} ({Ue.nbytes/1e6:.0f} MB)", flush=True)
    return Ue, names, ev_idx, shape


def split_observations(obs: list[lati.Obs], half: str) -> tuple[list[int], list[int]]:
    """Deterministic complementary halves of the 13 returns.

    The split is by **emitted mass** (ascending, alternating), which is the one
    ordering that is (a) fixed before any score is looked at and (b) guaranteed to
    put both the dense fields and the sparse fields in both halves.  ``half``
    selects which parity is the selection half (the other one is calibration).
    """
    order = sorted(range(len(obs)), key=lambda i: (obs[i].S, obs[i].id))
    sel = order[0::2] if half == "A" else order[1::2]
    cal = [i for i in range(len(obs)) if i not in set(sel)]
    return cal, sel


# ---------------------------------------------------------------------------
# stage 4 - belief model fitted on the calibration half only
# ---------------------------------------------------------------------------


def fit_model(Ue: np.ndarray, names: list[str], obs: list[lati.Obs],
              layers: list[str], idx_fit: list[int], verbose=False) -> dict:
    """Fit ``q = K * softmax(sum_m beta_m u_m)`` on the given observations only.

    ``lati.BinnedSoftmax`` is used because it parameterises the hidden mass ``K``
    directly (bounded in [2000, 60000] by the model-free probes: 12,348 px from
    the r13-lattice diffuse probe, 7,931 from the placeholder; both are quoted in
    ``evidence/lati_fit.json``), so the concentrated and diffuse observations are
    not confounded, and it is the model the project's own screen selected.
    """
    rows = [names.index(n) for n in layers]
    L = L_BY_R.get(len(rows), 14)
    bm = lati.BinnedSoftmax(Ue, rows, obs, L)
    res = bm.fit(l2=1e-3, subset=idx_fit, k_lo=2000.0, k_hi=60000.0)
    pred = bm.predict(np.asarray(res["theta"]))
    out = {"layers": layers, "rows": rows, "theta": [float(v) for v in res["theta"]],
           "L": L, "K": float(res["K"]), "ssr_fit": float(res["ssr"]),
           "max_abs_resid_fit": float(np.max(np.abs(
               pred[np.asarray(idx_fit)] - np.array([obs[i].dti for i in idx_fit])))),
           "at_bound": bool(res["at_bound"]),
           "pred_all": [float(v) for v in pred],
           "ids_all": [o.id for o in obs]}
    if verbose:
        print(f"[h48] fit {layers} -> SSR {res['ssr']:.5f} K={res['K']:.0f}", flush=True)
    return out


def q_field(Ue: np.ndarray, rows: list[int], theta, ev_idx, shape) -> np.ndarray:
    """Scatter ``q = K * exp(sum_m beta_m u_m) / Z`` onto the full grid."""
    K = float(theta[0])
    n = Ue.shape[1]
    eta = np.zeros(n, np.float32)
    for j, r in enumerate(rows):
        eta += np.float32(theta[j + 1]) * (Ue[r].astype(np.float32) * np.float32(1.0 / 255.0)
                                           - np.float32(0.5))
    eta -= eta.max()
    e = np.exp(eta, dtype=np.float32)
    Z = float(e.sum())
    q_ev = (K / Z) * e.astype(np.float64)
    q = np.zeros(int(np.prod(shape)), np.float64)
    q[ev_idx] = q_ev
    return q.reshape(shape)


# ---------------------------------------------------------------------------
# stage 5/6 - sweep and split conformal
# ---------------------------------------------------------------------------


def base_field(data: Path, shape) -> tuple[np.ndarray, np.ndarray]:
    """The base dot set the emission repacks, and the catalogue-exclusion mask.

    The base is the owner-reported d2.8 reference raster (its participant-score
    association is not authenticated). The H33-2-B2 raster is also an owner-supplied
    reference; the alleged 0.2778 mapping is unverified. Any apparent subset relation
    is byte geometry only and does not establish a score effect. The 1.5 px catalogue
    exclusion is an exploratory modeling choice, not evidence that pruning caused a
    gain or that adjacent evaluated pixels have low truth credit.
    """
    with rasterio.open(data / "scored" / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif") as src:
        base = src.read(1) > 0
    with rasterio.open(data / "labels.tif") as src:
        cat = src.read(1) == 1
    dcat = FEAT.dist_px(cat, 40.0)
    return base, (dcat > 1.5)


def certify(sweep, residuals, n_candidates, alpha) -> tuple:
    sc = CF.SplitConformal(residuals=np.asarray(residuals, np.float64),
                           sel_residuals=np.asarray([], np.float64),
                           n_candidates=n_candidates, alpha=alpha)
    cands = []
    for sp in sweep:
        lcb = sc.lcb(sp.predicted_dti)
        cands.append(CF.CertifiedCandidate(
            name=f"r={sp.spacing_px}", predicted=sp.predicted_dti, lcb=lcb,
            payload={"n_dots": sp.n_dots, "S": sp.S, "covered_kernel_integral": sp.Phi,
                     "T_hat": sp.T, "F_hat": sp.F, "K_hat": sp.K}))
    return sc, cands


# ---------------------------------------------------------------------------
# stage 7 - spatially blocked holdout
# ---------------------------------------------------------------------------


def block_frames(data: Path, shape) -> dict:
    """Two real-label spatial frames used as the pre-registered holdout.

    ``cat``   the given USGS/INGENIOUS catalogue itself (60,988 px).  It is the
              *known* population, so it is a weak proxy for the target - used as
              a sanity frame, not as the selector (IR-47-005).
    ``sgmc``  state-geologic-map faults that are more than one cell off the
              catalogue (independent public mapping, external layer).  This is
              the closest thing to a real "faults missing from the competition
              catalogue" population that exists locally.
    """
    with rasterio.open(data / "labels.tif") as src:
        lab = src.read(1)
    cat = lab == 1
    foot = lab != -1
    with rasterio.open(data / "external" / "derived_sgmc_faults_100m_u8.tif") as src:
        sgmc = src.read(1) > 0
    d_cat = FEAT.dist_px(cat, 40.0)
    sgmc_off = sgmc & foot & (d_cat > 1.5)
    return {"catalogue": cat, "sgmc_offcatalogue": sgmc_off,
            "footprint": foot, "catalogue_geom": cat}


def blocked_holdout(pred: np.ndarray, truth: np.ndarray, footprint: np.ndarray,
                    nrows=4, ncols=4, buffer_px=3) -> dict:
    """DTI pooled over spatially disjoint blocks, truth restricted to each core."""
    H, W = pred.shape
    re_ = np.linspace(0, H, nrows + 1).astype(int)
    ce = np.linspace(0, W, ncols + 1).astype(int)
    per, T = [], {"T": 0.0, "F": 0.0, "K": 0.0, "S": 0.0, "Phi": 0.0}
    for i in range(nrows):
        for j in range(ncols):
            r0, r1, c0, c1 = re_[i], re_[i + 1], ce[j], ce[j + 1]
            R0, R1 = max(0, r0 - buffer_px), min(H, r1 + buffer_px)
            C0, C1 = max(0, c0 - buffer_px), min(W, c1 + buffer_px)
            g = np.zeros((R1 - R0, C1 - C0), bool)
            g[r0 - R0:r1 - R0, c0 - C0:c1 - C0] = truth[r0:r1, c0:c1]
            p = pred[R0:R1, C0:C1]
            if g.sum() == 0 and not (p > 0).any():
                continue
            s = M.score(p, g, evaluated=footprint[R0:R1, C0:C1] | g, mask_mode="fp_only")
            per.append({"row": i, "col": j, "K": s.K, "T": s.T, "F": s.F, "DTI": s.DTI})
            for k in T:
                T[k] += {"T": s.T, "F": s.F, "K": s.K, "S": s.S, "Phi": s.Phi}[k]
    pooled = M.dti_from_TFK(T["T"], T["F"], T["K"]) if T["K"] else 0.0
    vals = [b["DTI"] for b in per]
    return {"pooled_DTI": pooled, "per_block": per,
            "mean_block_DTI": float(np.mean(vals)) if vals else 0.0,
            "min_block_DTI": float(np.min(vals)) if vals else 0.0,
            "n_blocks_scored": len(per)}


# ---------------------------------------------------------------------------
# stage 8/9 - emit and audit
# ---------------------------------------------------------------------------


def write_tif(path: Path, dots: np.ndarray, footprint: np.ndarray) -> dict:
    """Write research-only predictions with NaN outside the supplied footprint.

    The NaN-outside encoding follows the available owner-supplied mirror
    convention; it does not establish organizer acceptance. All finite
    predictions are 0/1 and the file remains research-only.
    """
    p = (dots & footprint).astype(np.float32)
    p[~footprint] = np.float32("nan")
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", driver="GTiff", height=G.HEIGHT, width=G.WIDTH,
                       count=1, dtype="float32", crs=G.CRS, transform=G.TRANSFORM,
                       nodata=np.nan, compress="deflate", predictor=3, tiled=True,
                       blockxsize=256, blockysize=256) as dst:
        dst.write(p, 1)
        dst.set_band_description(1, "GEMS fault probability (H48-MSCL research-only emission)")
    return {"path": str(path.relative_to(ROOT)), "n_positive": int((p > 0).sum()),
            "outside_encoding": "NaN; owner-supplied mirror convention only"}


def audit_tif(path: Path, footprint: np.ndarray, labels: np.ndarray) -> dict:
    with rasterio.open(path) as src:
        a = src.read(1)
        masked = src.read(1, masked=True)
        read_mask = np.ma.getmaskarray(masked)
        meta = {"count": src.count, "dtype": src.dtypes[0], "crs": str(src.crs),
                "shape": [src.height, src.width], "nodata": src.nodata,
                "transform": [float(v) for v in src.transform[:6]]}
    fin = np.isfinite(a)
    finite_values = a[fin]
    inside = a[footprint]
    finite_inside = np.isfinite(inside)
    outside_null = (np.isnan(a) | read_mask)[~footprint]
    checks = {
        "single_band": meta["count"] == 1,
        "float32": meta["dtype"] == "float32",
        "crs_epsg32611": meta["crs"] in ("EPSG:32611", "epsg:32611"),
        "shape_3730x3292": meta["shape"] == [G.HEIGHT, G.WIDTH],
        "transform_matches": all(abs(x - y) < 1e-6 for x, y in
                                 zip(meta["transform"], [100.0, 0.0, 243350.0, 0.0, -100.0,
                                                         4508550.0])),
        "finite_predictions_within_0_1": bool(finite_inside.all() and
                                               np.all((inside[finite_inside] >= 0.0) &
                                                      (inside[finite_inside] <= 1.0))),
        "no_nan_or_inf_inside_footprint": bool(finite_inside.all()),
        "outside_is_null_or_nan": bool(outside_null.all()),
        "nodata_tag_is_nan_diagnostic": bool(meta["nodata"] is not None and np.isnan(meta["nodata"])),
        "zero_on_catalogue": bool((a[labels == 1] == 0).all()),
        "finite_values_binary_0_1": bool(set(np.unique(finite_values)).issubset({0.0, 1.0})),
    }
    required = ("single_band", "float32", "crs_epsg32611", "shape_3730x3292",
                "transform_matches", "finite_predictions_within_0_1",
                "no_nan_or_inf_inside_footprint", "outside_is_null_or_nan")
    local_pass = all(checks[k] for k in required)
    return {"meta": meta, "checks": checks,
            "required_local_checks_passed": local_pass,
            "all_pass": local_pass,  # historical alias; local only, not portal acceptance
            "organizer_acceptance_established": False,
            "outside_requirement_scope": "local check against supplied footprint only",
            "n_finite": int(fin.sum()), "n_nan": int(np.isnan(a).sum()),
            "n_positive": int((a > 0).sum()),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def uniqueness(dots: np.ndarray, data: Path, reference: Path) -> dict:
    files = sorted((data / "scored").glob("*.tif"))
    if reference.exists():
        files.append(reference)
    exact, jac, rows = 0, 0.0, []
    mine = dots.astype(bool)
    nm = int(mine.sum())
    for f in files:
        with rasterio.open(f) as src:
            o = src.read(1) > 0
        if o.shape != mine.shape:
            continue
        if o.sum() == nm and np.array_equal(o, mine):
            exact += 1
        inter = int((o & mine).sum())
        union = int((o | mine).sum())
        j = inter / union if union else 0.0
        jac = max(jac, j)
        rows.append({"file": f.name, "n_pos": int(o.sum()), "jaccard": round(j, 6),
                     "equal_mass_exact": bool(o.sum() == nm and np.array_equal(o, mine))})
    return {"n_compared": len(rows), "exact_matches": exact, "max_jaccard": round(jac, 6),
            "rows": sorted(rows, key=lambda r: -r["jaccard"])[:6]}


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all", choices=["all", "fit", "sweep", "emit"])
    ap.add_argument("--alpha", type=float, default=0.125,
                    help="family error rate target for the conformal bound (default 1/8)")
    ap.add_argument("--half", default="A", choices=["A", "B"])
    ap.add_argument("--spacings", default=",".join(str(s) for s in SPACINGS))
    ap.add_argument("--source", default="prior", choices=["prior", "apex"],
                    help="emission source: an owner-reported reference field used in a conditional research experiment "
                         "(prior) or H48-APEX, the detector's own consensus apex set")
    args = ap.parse_args()
    spacings = tuple(float(s) for s in args.spacings.split(","))

    t_start = time.time()
    EVID.mkdir(exist_ok=True)
    data = G.data_dir()
    t = template()
    ev = t.evaluated
    st = FEAT.build_stack(verbose=True)
    obs = lati.load_observations(verbose=True)
    Ue, names, ev_idx, shape = build_feature_matrix(data, st, obs, ev)
    mscl_ext = np.load(CACHE / "h48_mscl.npz", allow_pickle=False)
    del st

    cal, sel = split_observations(obs, args.half)
    y_all = np.array([o.dti for o in obs])
    print(f"[h48] split {args.half}: fit half={[obs[i].id for i in cal]}")
    print(f"[h48]                  holdout ={[obs[i].id for i in sel]}")

    # ---- 1. belief-model selection, scored by LOO **inside the fit half only**
    fits, loo = {}, {}
    for tag, layers in MODEL_FAMILY.items():
        f = fit_model(Ue, names, obs, layers, cal)
        lg = lati.BinnedSoftmax(Ue, f["rows"], obs, f["L"])
        errs = []
        for k in cal:
            sub = [i for i in cal if i != k]
            rk = lg.fit(l2=1e-3, subset=sub, k_lo=2000.0, k_hi=60000.0)
            errs.append(float(lg.predict(np.asarray(rk["theta"]))[k]) - float(y_all[k]))
        e = np.array(errs)
        fits[tag] = f
        loo[tag] = {"loo_ssr_fit_half": float(e @ e), "loo_max_abs": float(np.abs(e).max()),
                    "signed_loo_residuals_obs_minus_pred": [float(v) for v in e],
                    "ids": [obs[i].id for i in cal]}
        print(f"[h48] {tag:<22} in-half SSR {f['ssr_fit']:.5f}  LOO SSR {loo[tag]['loo_ssr_fit_half']:.5f}"
              f"  maxabs {loo[tag]['loo_max_abs']:.4f}")
    best_tag = min(loo, key=lambda k: loo[k]["loo_ssr_fit_half"])
    layers = MODEL_FAMILY[best_tag]
    print(f"[h48] chosen belief model {best_tag} = {layers}")

    rows = fits[best_tag]["rows"]
    theta = np.asarray(fits[best_tag]["theta"])
    bm = lati.BinnedSoftmax(Ue, rows, obs, fits[best_tag]["L"])

    # ---- 2. the two calibration channels ------------------------------------
    #    (a) SPLIT: the fit half is the model half; the other half is untouched
    pred = bm.predict(theta)
    r_split = y_all[sel] - pred[sel]                     # signed, obs - pred
    #    (b) CROSS: leave-one-out over all returns (the model never sees the
    #        observation it is asked to predict)
    r_x = np.empty(len(obs))
    for k in range(len(obs)):
        sub = [i for i in range(len(obs)) if i != k]
        rk = bm.fit(l2=1e-3, subset=sub, k_lo=2000.0, k_hi=60000.0)
        r_x[k] = y_all[k] - float(bm.predict(np.asarray(rk["theta"]))[k])
    print(f"[h48] split-half signed residuals (n={r_split.size}): {np.round(r_split,5)}")
    print(f"[h48] cross-conformal LOO residuals (n={r_x.size}): {np.round(r_x,5)}")

    q = q_field(Ue, rows, theta, ev_idx, shape)
    K_hat = float(q.sum())
    print(f"[h48] K_hat = {K_hat:,.0f} px   model DTI on the fit half "
          f"{np.round(pred[cal],4)} vs observed {np.round(y_all[cal],4)}")

    # ---- 3. base field, support, sweep --------------------------------------
    base, cat_free = base_field(data, shape)
    print(f"[h48] base field {int(base.sum()):,} dots; "
          f"{int((base & ~cat_free).sum()):,} inside the 1.5 px catalogue margin")
    thr = float(np.quantile(q[ev], 1.0 - SUPPORT_FRAC))
    allowed = ev & cat_free & (q >= thr)
    cons_full = np.zeros(shape, np.uint8)
    cons_full.ravel()[ev_idx] = mscl_ext["consensus"]
    add_cand = ev & cat_free & (cons_full >= np.quantile(cons_full[ev], 0.90))
    print(f"[h48] support {int(allowed.sum()):,} px; add-candidates {int(add_cand.sum()):,} px")
    dti_bar = DTI_BAR
    selected_by = ("the rank threshold is the detector's own confidence axis; "
                   "the spacing is held at a predeclared research value of 2.5 px")
    if args.source == "apex":
        # H48-APEX: emit the detector's OWN geometry.  No prior submission's dots
        # are used as a base, so the artefact cannot be a re-issue of d2.8/h33-2-b2.
        allowed_src = ev & cat_free
        sweep, sweep_names = [], []
        for th in h49.APEX_THRESHOLDS:
            dots = h49.consensus_apex(cons_full, allowed_src, th, h49.APEX_SPACING, BUDGET)
            sp = h48.sweep_point_from_dots(dots, q, h49.APEX_SPACING, dti_bar)
            sweep.append(sp)
            sweep_names.append(f"rank>={th}")
            print(f"[h48] apex {sweep_names[-1]:<10} dots={sp.n_dots:<7} "
                  f"surrogate={sp.predicted_dti:.4f}", flush=True)
    else:
        sweep = h48.run_snap_sweep(base & cat_free, cons_full, q, allowed, spacings, dti_bar,
                                   add_candidates=add_cand)
        sweep_names = [f"r={s_.spacing_px}" for s_ in sweep]

    # ---- 4. certification ----------------------------------------------------
    m = len(spacings)
    certs = {}
    for tag, resid, n in (("split_half", r_split, r_split.size),
                          ("cross_conformal_all_returns", r_x, r_x.size)):
        for mm, label in ((m, f"family_{m}"), (1, "single_predeclared")):
            alpha_needed = CF.min_alpha_family(n, mm)
            sc = CF.SplitConformal(residuals=resid, sel_residuals=r_split,
                                   n_candidates=mm, alpha=alpha_needed, one_sided=True,
                                   alpha_used_override=alpha_needed)
            certs[f"{tag}|{label}"] = sc
            print(f"[h48] cert {tag:<30} m={mm:<2} n={n:<3} level={sc.level_used:.4f} "
                  f"q={sc.quantile:+.5f} certified={sc.certified}")
    # ---- 3b. score the candidates with the SAME estimator as the residuals ----
    # The sweep's `predicted_dti` is a field-overlap surrogate on the belief field
    # q; the certificate's residuals are `observed - bm.predict`.  Adding a quantile
    # of one to the other mixes two different scales, so the candidates are pushed
    # through `bm` itself: an emission is a (S, w, a) triple, which is exactly what
    # a lati.Obs is.
    cand_obs = [h49.candidate_obs(nm, sp.dots, t, ev_idx)
                for nm, sp in zip(sweep_names, sweep)]
    bm_ext = lati.BinnedSoftmax(Ue, rows, obs + cand_obs, fits[best_tag]["L"])
    pred_ext = np.asarray(bm_ext.predict(theta))
    pred_cand = [float(v) for v in pred_ext[len(obs):]]
    for nm, pc in zip(sweep_names, pred_cand):
        print(f"[h48] model prediction {nm:<10} {pc:.4f}", flush=True)

    sc_fam = certs[f"cross_conformal_all_returns|family_{m}"]
    sc_pre = certs["cross_conformal_all_returns|single_predeclared"]
    sc_split = certs["split_half|single_predeclared"]
    for tag, scx in (("split_half|single_predeclared", sc_split),
                     ("cross|family_%d" % m, sc_fam),
                     ("cross|single_predeclared", sc_pre)):
        scx.cal_ids = [obs[i].id for i in sel]
        scx.sel_ids = [obs[i].id for i in cal]
    # The emitted operating point IS selected out of a family of m candidates, so
    # the certificate that matches the procedure is the family channel (Bonferroni
    # alpha/m, Lei et al. 2018 eq. 2.6).  The single-predeclared channel is kept
    # and reported as the m=1 reference: it is the number to quote if a reviewer
    # rejects the sweep and accepts only a pre-registered operating point.
    sc_fam = certs[f"cross_conformal_all_returns|family_{m}"]
    sc_pre = certs["cross_conformal_all_returns|single_predeclared"]
    sc_split = certs["split_half|single_predeclared"]
    for scx in (sc_fam, sc_pre, sc_split):
        scx.cal_ids = [obs[i].id for i in sel]
        scx.sel_ids = [obs[i].id for i in cal]
    sc_sel = sc_fam if sc_fam.certified else sc_pre
    k_sel = CF.conformal_rank(int(sc_sel.residuals.size), sc_sel.alpha_used)
    cands = []
    for nm, sp, pc in zip(sweep_names, sweep, pred_cand):
        cands.append(CF.CertifiedCandidate(
            name=nm, predicted=pc, lcb=sc_sel.lcb(pc),
            payload={"n_dots": sp.n_dots, "n_kept": sp.n_kept, "n_added": sp.n_added,
                     "S": sp.S, "T_hat": sp.T, "F_hat": sp.F, "Phi_hat": sp.Phi,
                     "K_hat": sp.K, "marginal_bar": sp.marginal_bar,
                     "surrogate_dti": sp.predicted_dti,
                     "lcb_single_predeclared": (sc_pre.lcb(pc) if sc_pre.certified else None),
                     "lcb_split_half": (sc_split.lcb(pc) if sc_split.certified else None)}))
    ref_pred = float(pred_ext[[o.id for o in obs].index("d2.8")])
    ref_lcb = sc_sel.lcb(ref_pred)
    for c in cands:
        print(f"[h48]   {c.name:<10} dots={c.payload['n_dots']:<7} predicted={c.predicted:.4f} "
              f"LCB={c.lcb:.4f}", flush=True)
    chosen = CF.select_by_conditional_lower_bound(cands, sc_sel)
    print(f"[h48] CHOSEN {chosen.name}  assumption-conditional lower bound {chosen.lcb:.4f} at level "
          f"{sc_sel.level_used:.4f} (channel: cross-conformal family-of-{m}, "
          f"conformal rank {k_sel} of n={sc_sel.residuals.size}, m=1 reference level "
          f"{sc_pre.level_used:.4f})")
    print(f"[h48] owner-reported d2.8 reference scenario: predicted {ref_pred:.4f}, assumption-conditional lower bound {ref_lcb:.4f}")

    result = {
        "generated_utc": UTC,
        "pipeline": "H48-MSCL split-conformal emission sweep",
        "hypothesis": "H48 multi-scale curvature lineament consensus (MSCL)",
        "alpha_target": args.alpha,
        "spacings_px": list(spacings),
        "split": {"fit_half": [obs[i].id for i in cal],
                  "holdout_half": [obs[i].id for i in sel],
                  "rule": "alternating by ascending emitted mass S, fixed before scoring"},
        "model_family": MODEL_FAMILY,
        "fits": {k: {kk: vv for kk, vv in v.items() if kk != "pred_all"} for k, v in fits.items()},
        "model_selection": loo,
        "chosen_model": best_tag,
        "theta": [float(v) for v in theta],
        "K_hat": K_hat,
        "score_provenance": {"classification": "owner-reported / unverified TIFF attribution",
                             "h33_2_b2_dti_0_2778": "hypothetical assumption, not authenticated",
                             "all_dependent_fits": "conditional research only; no slot eligibility"},
        "observations": [{"id": o.id, "dti": o.dti, "S": o.S, "site": o.site} for o in obs],
        "residuals": {"split_half": [float(v) for v in r_split],
                      "split_half_ids": [obs[i].id for i in sel],
                      "cross_conformal": [float(v) for v in r_x],
                      "cross_conformal_ids": [o.id for o in obs]},
        "certificates": {k: v.to_dict() for k, v in certs.items()},
        "sweep": [{"spacing_px": s.spacing_px, "n_dots": s.n_dots, "n_kept": s.n_kept,
                   "n_added": s.n_added, "S": s.S, "T_hat": s.T, "F_hat": s.F,
                   "Phi_hat": s.Phi, "K_hat": s.K, "predicted_dti": s.predicted_dti}
                  for s in sweep],
        "candidates": [c.to_dict() for c in cands],
        "chosen": chosen.to_dict(),
        "owner_reported_d2_8_reference_assumption": {"id": "d2.8", "assumed_participant_dti": 0.26,
                                "predicted_dti": ref_pred,
                                "assumption_conditional_lower_bound": ref_lcb,
                                "note": "conditional scenario only; owner-reported d2.8 raster/score mapping is not organizer-authenticated"},
        "mscl": {"sigmas_px": list(h48.SIGMAS), "topo_bands": list(h48.TOPO_BANDS),
                 "geophys_bands": list(h48.GEOPHYS_BANDS), "topk_geophys": h48.TOPK_GEOPHYS},
        "seconds": round(time.time() - t_start, 1),
    }
    dots_best = dict(zip(sweep_names, [s_.dots for s_ in sweep]))[chosen.name]

    # ---- 5. spatially blocked holdout ---------------------------------------
    frames = block_frames(data, shape)
    labels = np.where(t.catalogue, 1, 0).astype(np.int8)
    with rasterio.open(data / "reference" / "h33-2-b2-zeros.tif") as src:
        owner_reference_mask = src.read(1) > 0
    hold = {}
    for fname, truth in (("catalogue", frames["catalogue"]),
                         ("sgmc_offcatalogue", frames["sgmc_offcatalogue"])):
        hold[fname] = {"candidate": blocked_holdout(dots_best, truth, frames["footprint"]),
                       "owner_reported_h33_2_b2_raster_unverified": blocked_holdout(owner_reference_mask, truth,
                                                                                   frames["footprint"])}
        c = hold[fname]["candidate"]["pooled_DTI"]
        i = hold[fname]["owner_reported_h33_2_b2_raster_unverified"]["pooled_DTI"]
        print(f"[h48] local holdout[{fname}] candidate {c:.4f} vs owner-reported reference geometry {i:.4f}")
    result["spatially_blocked_holdout"] = hold
    result["holdout_note"] = (
        "Proxy populations only. Neither frame is the private expert label set. Owner-reported H33-2-B2 "
        "geometry is compared locally; its association with participant DTI 0.2778 is unverified. "
        "All score-dependent model conclusions are conditional research results."
    )

    # ---- 6. emit + audit -----------------------------------------------------
    tag = (f"apex-{chosen.name.split('>=')[1]}" if args.source == "apex"
           else f"repack-r{chosen.name.split('=')[1].replace('.', 'p')}")
    name = f"gems47-h48-mscl-{tag}-{chosen.payload['n_dots']}px-{UTC}-research-only-nan-outside.tif"
    out = ROOT / "docs" / "downloads" / name
    written = write_tif(out, dots_best, frames["footprint"])
    audit = audit_tif(out, frames["footprint"], labels)
    uniq = uniqueness(dots_best, data, data / "reference" / "h33-2-b2-zeros.tif")
    result["artifact"] = {**written, "filename": name, "audit": audit, "uniqueness": uniq, "status": "RESEARCH_ONLY_NOT_PROMOTED"}
    result["certificate_channel_used_for_selection"] = {
        "name": ("cross_conformal_all_returns|family_%d" % m) if sc_sel is sc_fam
                else "cross_conformal_all_returns|single_predeclared",
        "level": sc_sel.level_used, "level_pct": round(100 * sc_sel.level_used, 3),
        "n_calibration": int(sc_sel.residuals.size),
        "conformal_rank_k": int(k_sel),
        "quantile": None if sc_sel.quantile in (float("inf"), float("-inf")) else sc_sel.quantile,
        "m_candidates": sc_sel.n_candidates,
        "assumption": sc_sel.to_dict().get("assumption"),
        "m1_reference_level": sc_pre.level_used,
        "m1_reference_quantile": sc_pre.quantile,
        "split_half_family_level": sc_split.level_used,
    }
    result["emission_source"] = args.source
    result["selected_by"] = selected_by
    result["prediction_channel"] = ("lati.BinnedSoftmax M2 extended with the candidate emissions as "
                                    "observations, so candidate predictions and calibration "
                                    "residuals share one estimator and one scale")
    hold_c = result["spatially_blocked_holdout"]
    reasons = []
    if uniq["max_jaccard"] > UNIQUE_BAR:
        reasons.append(f"max equal-mass Jaccard {uniq['max_jaccard']:.4f} > novelty bar "
                       f"{UNIQUE_BAR} (the field overlaps a prior submission)")
    for frame in ("catalogue", "sgmc_offcatalogue"):
        c = hold_c[frame]["candidate"]["pooled_DTI"]
        i = hold_c[frame]["owner_reported_h33_2_b2_raster_unverified"]["pooled_DTI"]
        if not (c > i):
            reasons.append(f"local proxy frame {frame}: candidate {c:.4f} <= owner-reported reference geometry {i:.4f}")
    if chosen.lcb < DTI_OWNER_SCORE_ASSUMED:
        reasons.append(f"assumption-conditional lower bound {chosen.lcb:.4f} < assumed owner-reported score {DTI_OWNER_SCORE_ASSUMED}")
    result["promotion"] = {
        "unique_against_inspected_artifacts": bool(uniq["max_jaccard"] <= UNIQUE_BAR),
        "beats_owner_reported_reference_on_both_local_frames": not any(r.startswith("local proxy") for r in reasons),
        "conditional_lower_bound_above_owner_reported_score_assumption": bool(chosen.lcb >= DTI_OWNER_SCORE_ASSUMED),
        "shippable": False,
        "eligible_for_slot": False,
        "status": "RESEARCH_ONLY_UNVERIFIED_ATTRIBUTION",
        "reasons": ["H33-2-B2 / participant-DTI 0.2778 association is unverified; dependent results are conditional",
                    "no artifact in this pipeline is authorized for upload"] + reasons,
        "note": "Exploratory local proxy results only. No organizer-authenticated score-to-raster mapping or private-label performance is established.",
    }
    print(f"[h48] promotion shippable={result['promotion']['shippable']} reasons={reasons}")
    print(f"[h48] wrote {out.name}: {written['n_positive']} px, local_format_pass={audit['required_local_checks_passed']}, "
          f"max Jaccard {uniq['max_jaccard']}")
    receipt = EVID / ("h48_apex_build.json" if args.source == "apex" else "h48_build.json")
    receipt.write_text(json.dumps(result, indent=1))
    print(f"[h48] receipt {receipt.name}")
    print(f"[h48] total {time.time() - t_start:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
