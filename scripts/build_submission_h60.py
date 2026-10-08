#!/usr/bin/env python3
"""RETIRED H60 builder; execution is disabled.

The historical builder below promotes an all-finite, zero-outside TIFF and labels it submission-ready. The scientific gate passed locally, but the all-finite encoding fails the published outside-null/NaN wording, organizer acceptance is untested, and no portal action is authorized in this review. Preserve the original implementation for audit; do not run it.

The artefact is the H60 field -- the per-cell maximum of the emission-domain ranks of
six scarp channels of the owner-derived 1 m lidar stack (step_max, lappos_max,
lapneg_max, upface_max, downface_max, cross_max), restricted to valid-lidar cells that
are >= 250 m from a TIGER road and >= 150 m from a BLM closed mining claim -- emitted
as unit dots at the split-conformal-selected 2.0 px spacing over the off-catalogue
evaluated domain, budget 37,654.

Promotion basis (docs/research/h60-hypotheses-preregistered.md, frozen before any
score): the H60 arm passed the preregistered six-condition gate on the frozen 41-block
spatially blocked holdout -- pooled selection-half DTI 0.2879 on the primary lidar-peak
instrument (H50 anchor 0.1659, random 0.0463, d2.8 reference 0.0494, H47-C1 0.0483),
positive simultaneous split-conformal floor 0.0989 at >= 90.91% coverage, and
independent-population corroboration on the SGMC off-catalogue instrument (0.1938 vs
random 0.0698 and vs the H50 anchor's 0.1221) -- conditions 5 (uniqueness) and 6
(format) are what this builder enforces.

Format contract (identical to H50):
* single band, float32, EPSG:32611, 100 m, the official transform and bounds;
* every value finite and inside [0, 1]; 0.0 outside the competition footprint;
* no nodata tag; strict read-back validation over every cell before publication;
* bounded uniqueness audit against every prior raster reachable from this checkout.

Outputs (all under ``docs/downloads/``): the GeoTIFF, a ZIP containing the TIFF, the
submission note and the receipt, a JSON receipt, and a TXT note for the DrivenData
"Note" field.  ``docs/data/`` receives the receipts the site renders.
"""
from __future__ import annotations

if __name__ != "__main__":
    raise RuntimeError("DISABLED: retired H60 builder cannot be imported or executed.")
print("DISABLED: historical H60 builder writes zero outside the footprint and labels that encoding submission-ready. No files were read or written.")
raise SystemExit(2)

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

from gems47 import grid as G
from gems47 import h50, h60
from gems47 import submission as SUB

SPACING_PX = 2.0
BUDGET = 37_654
STAMP = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
STEM = f"gems47-h60-lidarscarp-s2p0-{STAMP[:8]}"
FALLBACK_STEM = f"gems47-h60-lidarscarp-s2p0-{STAMP[:8]}-nanoutside"
PORTAL_NOTE = "h60 lidar-scarp d2p0 conformal90"

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


def uniqueness_audit(pred: np.ndarray, exclude_stems: tuple[str, ...]) -> dict:
    rows = []
    for pattern in PRIOR_GLOBS:
        for q in sorted(ROOT.glob(pattern)):
            if any(q.stem.startswith(s) for s in exclude_stems):
                continue  # never compare an artefact with itself
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
    started = time.time()
    data = G.data_dir()
    template = G.load_template()
    domain = h60.h60_emission_domain(data)
    field = h60.h60_field(data, domain)
    dots = h50.emit(field, domain, SPACING_PX, BUDGET)

    outdir = ROOT / "docs" / "downloads"
    outdir.mkdir(parents=True, exist_ok=True)
    tif = outdir / f"{STEM}-allfinite.tif"
    SUB.write_submission(dots, tif, mode="allfinite", template=template)
    checks = readback(tif, template, BUDGET)
    if not all(v is True for k, v in checks.items() if isinstance(v, bool)):
        raise SystemExit(f"read-back validation failed: {checks}")
    audit = uniqueness_audit(dots > 0, (STEM, FALLBACK_STEM))
    if audit["exact_matches"] != 0 or audit["max_jaccard"] >= 0.5:
        raise SystemExit(f"uniqueness gate failed: {audit['exact_matches']} exact matches, "
                         f"max jaccard {audit['max_jaccard']}")

    fallback = outdir / f"{FALLBACK_STEM}.tif"
    SUB.write_submission(dots, fallback, mode="nan", template=template)

    screen = json.loads((ROOT / "evidence" / "h60" / "screen.json").read_text())
    arm = screen["arms"]["h60"]
    anchor = screen["arms"]["h50"]
    ctrl = screen["controls"]["h60"]
    floor = float(arm["conformal"]["floor"])
    rank = int(arm["conformal"]["rank_1_based"])
    n_conformal = int(arm["conformal"]["band"]["n_calibration"]) + 1
    cov = float(arm["conformal"]["coverage_at_least"])
    sel = float(arm["pooled_primary_selection"])
    anchor_sel = float(anchor["pooled_primary_selection"])
    sgmc = float(arm["pooled_sgmc_selection"])
    anchor_sgmc = float(anchor["pooled_sgmc_selection"])
    rnd_primary = float(ctrl["random"]["primary"])
    rnd_sgmc = float(ctrl["random"]["sgmc"])

    note = (
        f"{PORTAL_NOTE}\n"
        "\n"
        "New hypothesis, not a copy of any prior submission.  Field: the per-cell maximum "
        "of the ranks of six scarp channels (step height, crest convexity, base concavity, "
        "up/down-facing and across-slope band-passed gradients) of the owner-derived 1 m "
        "lidar scarp stack -- built from USGS 3DEP 1 m DEM tiles on the competition's own "
        "tile list -- restricted to cells at least 250 m from a mapped road and 150 m from a "
        "BLM closed mining claim, so the detector sees tectonic steps rather than road cuts "
        "and mine scars.  Emission: unit dots at 200 m spacing over the noise-masked "
        "off-catalogue domain (competition footprint minus the USGS/INGENIOUS catalogue, which "
        "is masked out of scoring, intersected with the valid-lidar road/claim-masked domain), "
        "37,654 dots.  Values are 0/1 only, float32, single band, EPSG:32611, "
        "100 m, official grid/transform, all finite, zeros outside the footprint.\n"
        "\n"
        f"Operating point: 2.0 px (200 m), chosen on a selection half of "
        f"{arm['conformal']['band']['n_selection']} spatially blocked holdout blocks and "
        "certified on the disjoint calibration half by split-conformal prediction (Lei, "
        "G'Sell, Rinaldo, Tibshirani, Wasserman, JASA 2018, Algorithm 2), max-residual rank "
        f"{rank} of {n_conformal}, finite-sample coverage at least {cov:.2%}, certified "
        f"holdout floor {floor:.4f} DTI.\n"
        "\n"
        "Validation: pooled selection-half DTI 0.2879 on the primary off-catalogue "
        "lidar-scarp-peak instrument against 0.1659 for the previous repository candidate "
        "(H50, slope anomaly), 0.0463 mass-matched spaced random, 0.0494 the owner-reported "
        "d2.8 reference and 0.0483 H47-C1; AND 0.1938 on the independent SGMC off-catalogue "
        "fault population against 0.0698 random and 0.1221 for H50 -- the field beats every "
        "control on an instrument it does not read.  The primary instrument is derived from "
        "the same lidar stack, so its numbers are optimistic for this field; the SGMC gain "
        "and the 13-artifact rank correlations are the independent evidence.  No private "
        "label, pooled-map or leaderboard guarantee is claimed.\n"
    )

    receipt = {
        "schema_version": 1,
        "hypothesis_id": "H60",
        "artifact": STEM,
        "kind": "primary_submission_candidate",
        "promoted": True,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "spacing_px": SPACING_PX,
        "budget": BUDGET,
        "channels": list(h60.H60_CHANNELS),
        "noise_masks": {"tiger_road_lt_m": h60.ROAD_MASK_M,
                        "blm_closed_claim_lt_m": h60.CLAIM_MASK_M},
        "emission_domain": "competition footprint AND NOT USGS/INGENIOUS catalogue AND "
                           "valid lidar AND road>=250 m AND closed-claim>=150 m "
                           f"({int(domain.sum())} cells)",
        "format": {
            "driver": "GTiff", "count": 1, "dtype": "float32", "crs": "EPSG:32611",
            "width": template.shape[1], "height": template.shape[0],
            "transform": list(template.transform)[:6], "nodata": None,
            "outside_footprint": "0.0 (all finite)", "values": "0.0 and 1.0 only",
        },
        "readback_checks": checks,
        "uniqueness": {k: audit[k] for k in ("compared", "exact_matches", "max_jaccard")},
        "screen": "evidence/h60/screen.json",
        "preregistration": "docs/research/h60-hypotheses-preregistered.md",
        "screen_selected_spacing_px": arm["selected_spacing_px"],
        "conformal": {
            "method": "max-residual one-sided split conformal, Lei et al. JASA 2018 Alg. 2",
            "reference": "https://doi.org/10.1080/01621459.2017.1307116",
            "selection_blocks": screen["arms"]["h50"]["conformal"]["band"]["n_selection"],
            "calibration_blocks": screen["arms"]["h50"]["conformal"]["band"]["n_calibration"],
            "rank_1_based": rank,
            "coverage_at_least": cov,
            "certified_floor_dti": floor,
            "assumption": "block-level exchangeability, not verified; conditional guarantee",
        },
        "holdout": {
            "primary_instrument": "off-catalogue local maxima of the owner-derived 1 m lidar "
                                  "scarp stack (lappos t200 d3)",
            "candidate_pooled_dti": sel,
            "h50_anchor_pooled_dti": anchor_sel,
            "spaced_random_pooled_dti_mass_matched": rnd_primary,
            "owner_reported_d28_reference_pooled_dti":
                float(ctrl["h33_reference"]["primary"]),
            "h47c1_pooled_dti": float(ctrl["h47c1"]["primary"]),
            "independent_instrument": "SGMC off-catalogue faults (>300 m from the catalogue)",
            "candidate_sgmc_pooled_dti": sgmc,
            "h50_anchor_sgmc_pooled_dti": anchor_sgmc,
            "random_sgmc_pooled_dti": rnd_sgmc,
            "gate": screen["gate"]["per_arm"]["h60"],
        },
        "sha256_tif": sha256(tif),
        "bytes": tif.stat().st_size,
        "files": [tif.name, f"{STEM}.zip", f"{STEM}-receipt.json", f"{STEM}-note.txt",
                  fallback.name],
        "provenance_limits": [
            "The lidar scarp stack is owner-derived from USGS 3DEP 1 m DEM tiles (706/716, "
            "tile list OCR-recovered from the competition PDF), not organiser-supplied.",
            "No organiser receipt links any participant score to a TIFF; the 0.2778 figure "
            "is owner-reported and the owner page marks that submission unscored.",
            "The restored data are hash-pinned owner mirrors, not organizer-authenticated "
            "bytes.",
            "The primary instrument is derived from the same lidar stack the field reads, "
            "so primary-instrument numbers are optimistic; the SGMC off-catalogue gain is "
            "the independent corroboration.",
        ],
    }
    save_json(outdir / f"{STEM}-receipt.json", receipt)
    (outdir / f"{STEM}-note.txt").write_text(note)

    zpath = outdir / f"{STEM}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(tif, tif.name)
        z.write(outdir / f"{STEM}-note.txt", f"{STEM}-note.txt")
        z.write(outdir / f"{STEM}-receipt.json", f"{STEM}-receipt.json")

    # deploy the evidence receipts the site renders
    deployed = {}
    for src, dst in (("screen.json", "h60-screen.json"),
                     ("instrument-refinement.json", "h60-instrument-refinement.json")):
        payload = json.loads((ROOT / "evidence" / "h60" / src).read_text())
        payload["deployed_from"] = f"evidence/h60/{src}"
        save_json(ROOT / "docs" / "data" / dst, payload)
        deployed[dst] = sha256(ROOT / "docs" / "data" / dst)
    shutil.copyfile(ROOT / "evidence" / "h60" / "spacing-history.csv",
                    ROOT / "docs" / "data" / "h60-spacing-history.csv")
    deployed["h60-spacing-history.csv"] = sha256(ROOT / "docs" / "data" / "h60-spacing-history.csv")

    save_json(ROOT / "docs" / "data" / "h60-artifact.json", {
        **receipt,
        "download_url": f"downloads/{STEM}-allfinite.tif",
        "zip_url": f"downloads/{STEM}.zip",
        "note_url": f"downloads/{STEM}-note.txt",
        "fallback_url": f"downloads/{fallback.name}",
        "submission_note_field": PORTAL_NOTE,
        "deployed_evidence_sha256": deployed,
    })

    print(json.dumps({"tif": str(tif.relative_to(ROOT)), "sha256": receipt["sha256_tif"],
                      "bytes": receipt["bytes"], "dots": BUDGET,
                      "checks": checks, "uniqueness": receipt["uniqueness"],
                      "elapsed_seconds": round(time.time() - started, 2)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
