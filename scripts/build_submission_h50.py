#!/usr/bin/env python3
"""RETIRED historical H50 publisher — intentionally disabled.

This implementation previously published an all-finite zero-outside GeoTIFF as primary and
used stale submission-ready/score-attribution language. It must not regenerate deployed files.
The reviewed NaN-outside H50 artifact is a locally promoted public-proxy candidate only; it is
not organizer-accepted or authorized for a competition slot. A replacement builder requires
separate review and a regression-tested serialized read-back contract.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
import zipfile
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "2")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import numpy as np
import rasterio
from scipy import ndimage as ndi

from gems47 import grid as G
from gems47 import h50
from gems47 import submission as SUB
from gems47s3.geomorph import rank_scale

SPACING_PX = 2.8
BUDGET = 37_654
REGIONAL_SIGMA_PX = 25.0
STAMP = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
STEM = f"gems47-h50-slopeanom-s2p8-{STAMP[:8]}"
FALLBACK_STEM = f"gems47-h50-slopeanom-s2p8-{STAMP[:8]}-nanoutside"

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


def save_json(path: Path, values) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(values, indent=2, allow_nan=False) + "\n")


def build_field(data: Path, mask: np.ndarray) -> np.ndarray:
    with rasterio.open(data / "training_features.tif") as src:
        slope = src.read(h50.SLOPE_BAND).astype(np.float32)
    slope[~np.isfinite(slope)] = 0.0
    slope[slope < -1e30] = 0.0
    regional = ndi.gaussian_filter(slope, REGIONAL_SIGMA_PX, mode="nearest")
    field = rank_scale(np.where(mask, slope - regional, np.nan))
    return np.where(mask & np.isfinite(field), field, 0.0).astype(np.float32)


def uniqueness_audit(pred: np.ndarray, exclude_stems: tuple[str, ...]) -> dict:
    rows = []
    for pattern in PRIOR_GLOBS:
        for q in sorted(ROOT.glob(pattern)):
            if any(q.stem.startswith(s) for s in exclude_stems):
                continue  # never compare an artifact with itself
            try:
                with rasterio.open(q) as src:
                    a = np.nan_to_num(src.read(1).astype(np.float32), nan=0.0) > 0
            except Exception as exc:
                rows.append(dict(path=str(q.relative_to(ROOT)), error=repr(exc)))
                continue
            inter = int((a & pred).sum())
            union = int((a | pred).sum())
            rows.append(dict(path=str(q.relative_to(ROOT)), dots=int(a.sum()),
                             intersection=inter, union=union,
                             jaccard=round(inter / max(union, 1), 6),
                             exact_match=bool(inter == union and inter > 0)))
    rows.sort(key=lambda r: -r.get("jaccard", 0.0))
    return dict(compared=len(rows), exact_matches=sum(1 for r in rows if r.get("exact_match")),
                max_jaccard=round(max((r.get("jaccard", 0.0) for r in rows), default=0.0), 6),
                rows=rows)


def readback(path: Path, template: G.Template, dots: int) -> dict:
    with rasterio.open(path) as src:
        v = src.read(1)
        checks = {
            "single_band": src.count == 1,
            "dtype_float32": str(src.dtypes[0]) == "float32",
            "crs_epsg32611": str(src.crs) == "EPSG:32611",
            "width_matches": src.width == template.shape[1],
            "height_matches": src.height == template.shape[0],
            "transform_matches": list(src.transform)[:6] == list(template.transform)[:6],
            "nodata_unset": src.nodata is None,
            "no_nan": not bool(np.isnan(v).any()),
            "no_inf": not bool(np.isinf(v).any()),
            "all_in_unit_interval": bool(np.all((v >= 0.0) & (v <= 1.0))),
            "nan_intolerant_range_check": bool(np.all((v >= 0) & (v <= 1))),
            "zero_outside_footprint": bool((v[~template.footprint] == 0).all()),
            "dot_count": int((v > 0).sum()) == dots,
            "dots_on_footprint": bool((v > 0)[template.footprint].sum() == dots),
            "dots_off_catalogue": bool((v[template.catalogue] == 0).all()),
            "values_are_unit": bool(np.all(np.unique(v) == np.array([0.0, 1.0]))),
            "compression": str(src.compression),
        }
    return checks


def main() -> int:
    print(
        "DISABLED: historical H50 publisher labels an all-finite zero-outside TIFF as primary "
        "and emits stale submission-ready claims. The reviewed NaN-outside artifact is locally "
        "promoted but not organizer-accepted or slot-authorized. Do not regenerate published "
        "files until a separate replacement builder and read-back suite are reviewed."
    )
    return 2
    started = time.time()
    data = G.data_dir()
    template = G.load_template()
    grids = h50.read_grid(data)
    mask = grids["evaluated"]
    field = build_field(data, mask)
    dots = h50.emit(field, mask, SPACING_PX, BUDGET)

    outdir = ROOT / "docs" / "downloads"
    outdir.mkdir(parents=True, exist_ok=True)
    tif = outdir / f"{STEM}-allfinite.tif"
    SUB.write_submission(dots, tif, mode="allfinite", template=template)
    checks = readback(tif, template, BUDGET)
    if not all(v is True for k, v in checks.items() if isinstance(v, bool)):
        raise SystemExit(f"read-back validation failed: {checks}")
    audit = uniqueness_audit(dots > 0, (STEM, FALLBACK_STEM))

    fallback = outdir / f"{FALLBACK_STEM}.tif"
    SUB.write_submission(dots, fallback, mode="nan", template=template)

    screen = json.loads((ROOT / "evidence" / "h50" / "screen.json").read_text())
    cand = screen["candidate"]
    ctrl = screen["controls"]
    floor = float(cand["conformal_floor"])
    # the conformal band's rank is out of (n_calibration + 1) residual slots
    n_conformal = int(screen["conformal"]["n_calibration"]) + 1
    cov = float(cand["conformal_coverage"])
    rank = int(cand["conformal_rank"])
    sel = float(cand["selection_mean"])
    ref = float(ctrl["h33_reference"]["selection_mean"])
    c1 = float(ctrl["h47c1"]["selection_mean"])
    rnd = float(ctrl["random"]["selection_mean"])

    note = (
        "h50 slope-anomaly d2p8 conformal90\n"
        "\n"
        "New hypothesis, not a copy of any prior submission.  Field: the rank of official "
        "band 19 (detrended elevation slope) above its own 25 px (2.5 km) Gaussian regional "
        "level, so a fault scarp -- a locally steep step on a gentle surface -- ranks above a "
        "uniformly steep mountain front.  Emission: unit dots at 280 m spacing over the "
        "evaluated domain (competition footprint minus the USGS/INGENIOUS catalogue, which is "
        "masked out of scoring), 37,654 dots.  Values are 0/1 only, float32, single band, "
        "EPSG:32611, 100 m, official grid/transform, all finite, zeros outside the footprint.\n"
        "\n"
        f"Operating point: 2.8 px (280 m), chosen on a selection half of {screen['block_counts']['selection']} "
        f"spatially blocked holdout blocks and certified on the disjoint calibration half of "
        f"{screen['block_counts']['calibration']} blocks by split-conformal prediction (Lei, G'Sell, "
        f"Rinaldo, Tibshirani, Wasserman, JASA 2018, Algorithm 2), max-residual rank {rank} of "
        f"{n_conformal}, finite-sample coverage at least {cov:.2%}, certified holdout floor "
        f"{floor:.4f} DTI.  Budget 37,654 is the point where the marginal dot's realised "
        "kernel weight is still 4x the metric's own credit bar (alpha*DTI).\n"
        "\n"
        f"Validation instrument: the off-catalogue local maxima of the organiser-supplied 1 m "
        "lidar scarp stack ("
        f"{screen['instrument_truth_pixels'][screen['design']['primary_instrument']]} points).  "
        f"On the blocked holdout the candidate reaches {sel:.4f} pooled DTI against {ref:.4f} for the "
        f"owner-reported d2.8 reference, {c1:.4f} for the previous holdout best (H47-C1) and "
        f"{rnd:.4f} for mass-matched spaced random.  The instrument is a proxy: it shares the "
        "slope quantity with the field's input band and it is not a private-label guarantee.\n"
    )

    receipt = {
        "schema_version": 1,
        "hypothesis_id": "H50",
        "artifact": STEM,
        "kind": "primary_submission_candidate",
        "promoted": True,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "spacing_px": SPACING_PX,
        "budget": BUDGET,
        "regional_sigma_px": REGIONAL_SIGMA_PX,
        "slope_band": h50.SLOPE_BAND,
        "emission_domain": "competition footprint AND NOT USGS/INGENIOUS catalogue",
        "format": {
            "driver": "GTiff", "count": 1, "dtype": "float32", "crs": "EPSG:32611",
            "width": template.shape[1], "height": template.shape[0],
            "transform": list(template.transform)[:6], "nodata": None,
            "outside_footprint": "0.0 (all finite)", "values": "0.0 and 1.0 only",
        },
        "readback_checks": checks,
        "uniqueness": {k: audit[k] for k in ("compared", "exact_matches", "max_jaccard")},
        "screen": "evidence/h50/screen.json",
        "screen_selected_spacing_px": screen["selected_spacing_px"],
        "conformal": {
            "method": "max-residual one-sided split conformal, Lei et al. JASA 2018 Alg. 2",
            "reference": "https://doi.org/10.1080/01621459.2017.1307116",
            "selection_blocks": screen["block_counts"]["selection"],
            "calibration_blocks": screen["block_counts"]["calibration"],
            "rank_1_based": rank,
            "coverage_at_least": cov,
            "certified_floor_dti": floor,
            "assumption": "block-level exchangeability, not verified; conditional guarantee",
        },
        "holdout": {
            "instrument": "off-catalogue local maxima of the 1 m lidar scarp stack",
            "candidate_pooled_dti": sel,
            "owner_reported_d28_reference_pooled_dti": ref,
            "h47c1_previous_holdout_best_pooled_dti": c1,
            "spaced_random_pooled_dti_mass_matched": rnd,
            "gate": screen["gate"],
        },
        "sha256_tif": sha256(tif),
        "bytes": tif.stat().st_size,
        "files": [tif.name, f"{STEM}.zip", f"{STEM}-receipt.json", f"{STEM}-note.txt",
                  fallback.name],
        "provenance_limits": [
            "No organiser receipt links any participant score to a TIFF; the 0.2778 figure is "
            "owner-reported and the owner page marks that submission unscored.",
            "The restored data are hash-pinned owner mirrors, not organizer-authenticated "
            "bytes.",
            "Instrument L shares the slope quantity with the field's input band, so the "
            "holdout numbers are an optimistic proxy, not a certified leaderboard score.",
        ],
    }
    save_json(outdir / f"{STEM}-receipt.json", receipt)
    (outdir / f"{STEM}-note.txt").write_text(note)

    zpath = outdir / f"{STEM}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(tif, tif.name)
        z.write(outdir / f"{STEM}-note.txt", f"{STEM}-note.txt")
        z.write(outdir / f"{STEM}-receipt.json", f"{STEM}-receipt.json")

    # deploy the evidence receipts the site renders, so the published numbers and the
    # published evidence cannot drift apart
    deployed = {}
    for src, dst in (("instrument-ranking.json", "h50-instrument-ranking.json"),
                     ("field-scan.json", "h50-field-scan.json"),
                     ("field-refine.json", "h50-field-refine.json"),
                     ("screen.json", "h50-screen.json"),
                     ("budget-profile.json", "h50-budget-profile.json")):
        payload = json.loads((ROOT / "evidence" / "h50" / src).read_text())
        payload["deployed_from"] = f"evidence/h50/{src}"
        save_json(ROOT / "docs" / "data" / dst, payload)
        deployed[dst] = sha256(ROOT / "docs" / "data" / dst)
    shutil.copyfile(ROOT / "evidence" / "h50" / "spacing-history.csv",
                    ROOT / "docs" / "data" / "h50-spacing-history.csv")
    deployed["h50-spacing-history.csv"] = sha256(ROOT / "docs" / "data" / "h50-spacing-history.csv")

    save_json(ROOT / "docs" / "data" / "h50-artifact.json", {
        **receipt,
        "download_url": f"downloads/{STEM}-allfinite.tif",
        "zip_url": f"downloads/{STEM}.zip",
        "note_url": f"downloads/{STEM}-note.txt",
        "fallback_url": f"downloads/{fallback.name}",
        "submission_note_field": "h50 slope-anomaly d2p8 conformal90",
        "deployed_evidence_sha256": deployed,
    })

    print(json.dumps({"tif": str(tif.relative_to(ROOT)), "sha256": receipt["sha256_tif"],
                      "bytes": receipt["bytes"], "dots": BUDGET,
                      "checks": checks, "uniqueness": receipt["uniqueness"],
                      "elapsed_seconds": round(time.time() - started, 2)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
