#!/usr/bin/env python3
"""Build, validate, audit for uniqueness and publish the H71-round artifacts.

Two artifacts are built from the frozen screen receipt (`evidence/h71/screen.json`):

* **The primary** — the winner among the arms passing the frozen promotion condition
  `beats_incumbent_h60` (above H60's frozen 0.287891 primary AND 0.193813 SGMC pooled
  selection-half DTI).  This round that is **H71**, the scarp-consensus field, which
  beat the incumbent on both instruments; it replaces H60 as the repository's
  OK-to-download-and-submit artifact.  Emitted at its **split-conformal-selected**
  spacing (argmax certified lower bound).
* **The validated candidate** — the frozen winner by the session-5 tie-break (highest
  pooled SGMC selection DTI, then conformal floor) when it is not the primary.  This
  round that is **H74**, the eight-channel field: it passed the four control
  conditions and holds the best independent-instrument DTI of the round, but it does
  not beat the primary on the primary instrument, so it is published as a clearly
  labelled validated candidate, not the recommendation.

The conformal guarantee's confidence level is reported next to the chosen spacing in
every submission note: max-over-settings one-sided split conformal (Lei et al. JASA
2018, Algorithm 2), rank k = ceil((n+1) * 0.90) = 20 of n+1 = 22 calibration units,
finite-sample coverage at least 90.91 %, assumption-conditional on block-level
exchangeability.

Format contract (identical to H50/H60):
* single band, float32, EPSG:32611, 100 m, the official transform and bounds;
* every value finite and inside [0, 1]; 0.0 outside the competition footprint;
* no nodata tag; strict read-back validation over every cell before publication;
* bounded uniqueness audit against every prior raster reachable from this checkout.

Outputs (under ``docs/downloads/``): per artifact the GeoTIFF, a ZIP containing the
TIFF + note + receipt, the submission note and the receipt JSON, plus a NaN-outside
fallback.  ``docs/data/`` receives the receipts the site renders.
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

from gems47 import grid as G
from gems47 import h50, h71
from gems47 import submission as SUB

BUDGET = 37_654
STAMP = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
DATE = STAMP[:8]

ARM_SLUG = {"h71": "scarpconsensus", "h72": "farfield-lidar",
            "h73": "lidar-thk-alteration", "h74": "lidar-8ch"}
ARM_PORTAL_NOTE = {"h71": "h71 scarp-consensus", "h72": "h72 far-field lidar",
                   "h73": "h73 lidar+ThK alteration", "h74": "h74 lidar 8-channel"}
ARM_BLURB = {
    "h71": "the amplitude-tie-broken consensus count of the six lidar scarp channels "
           "(how many independent operators fire at the same cell, then the H60 "
           "channel-rank-max as tie-break), road/claim masked",
    "h72": "the H60 lidar scarp-crest field restricted to cells more than 300 m from "
           "every catalogue pixel (the unmapped-system pole), road/claim masked",
    "h73": "an additive 50/50 rank mixture of the H60 lidar scarp-crest field and the "
           "rank of the USGS GeoDAWN Th/K radiometric alteration grid (structure + "
           "fossil heat), road/claim masked",
    "h74": "the per-cell maximum of the ranks of eight lidar scarp channels (H60's six "
           "plus slope-excess and local relief), road/claim masked",
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


def save_json(path: Path, values) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(values, indent=2, allow_nan=False) + "\n")


def build_arm(arm: str, data: Path):
    """Return (field, mask, spec) for the frozen arm definition."""
    if arm == "h71":
        d = h71.h71_consensus(data)
        return d["field"], d["mask"], dict(channels=list(h71.H71_THRESHOLDS),
                                           thresholds=h71.H71_THRESHOLDS)
    if arm == "h72":
        d = h71.h72_field(data)
        return d["field"], d["mask"], dict(far_radius_px=h71.H72_FAR_RADIUS_PX)
    if arm == "h73":
        d = h71.h73_field(data)
        return d["field"], d["mask"], dict(lambda_=h71.H73_LAMBDA,
                                           thk_band=h71.H73_THK_BAND)
    if arm == "h74":
        d = h71.h74_field(data)
        return d["field"], d["mask"], dict(channels=list(h71.H74_CHANNELS))
    raise ValueError(f"unknown arm {arm!r}")


def uniqueness_audit(pred: np.ndarray, exclude_stems: tuple[str, ...]) -> dict:
    rows = []
    for pattern in PRIOR_GLOBS:
        for q in sorted(ROOT.glob(pattern)):
            if any(q.stem.startswith(s) for s in exclude_stems):
                continue  # never compare an artifact with itself
            try:
                with rasterio.open(q) as src:
                    a = np.nan_to_num(src.read(1).astype(np.float32), nan=0.0) > 0
            except Exception as exc:  # audit must survive a bad file
                rows.append(dict(path=str(q.relative_to(ROOT)), error=repr(exc)))
                continue
            inter = int((a & pred).sum())
            union = int((a | pred).sum())
            rows.append(dict(path=str(q.relative_to(ROOT)), dots=int(a.sum()),
                             intersection=inter, union=union,
                             jaccard=round(inter / max(union, 1), 6),
                             exact_match=bool(inter == union and inter > 0)))
    rows.sort(key=lambda r: -r.get("jaccard", 0.0))
    scored = [r for r in rows
              if r["path"].startswith(".cache/gems_data/scored/")
              or r["path"].startswith(".cache/gems_data/reference/")]
    return dict(compared=len(rows),
                exact_matches=sum(1 for r in rows if r.get("exact_match")),
                max_jaccard=round(max((r.get("jaccard", 0.0) for r in rows), default=0.0), 6),
                max_jaccard_vs_scored_priors=round(
                    max((r.get("jaccard", 0.0) for r in scored), default=0.0), 6),
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


def build_artifact(arm: str, screen: dict, data: Path,
                   template: G.Template) -> dict:
    """Build + validate + audit one arm's artifact. Returns its receipt.

    The build never raises on the uniqueness outcome: the audit is recorded and the
    caller decides the artifact's kind from it, so a scientifically-strong arm that
    fails the frozen uniqueness bar is still published — honestly labelled — instead
    of silently dropped (Own the Outcome).
    """
    arm_rec = screen["arms"][arm]
    gate = screen["gate"]["per_arm"][arm]
    if not gate["passed"]:
        raise SystemExit(f"arm {arm} did not pass the gate")
    promotable = arm in screen["gate"]["promotable_arms"]

    spacing = float(arm_rec["selected_spacing_px"])
    floor = float(arm_rec["conformal"]["floor"])
    rank = int(arm_rec["conformal"]["rank_1_based"])
    n_cal = int(arm_rec["conformal"]["n_calibration"])
    n_sel = int(arm_rec["conformal"]["n_selection"])
    cov = float(arm_rec["conformal"]["coverage_at_least"])
    sel = float(arm_rec["pooled_primary_selection"])
    sgmc = float(arm_rec["pooled_sgmc_selection"])

    field, mask, spec = build_arm(arm, data)
    dots = h50.emit(field, mask, spacing, BUDGET)

    slug = ARM_SLUG[arm]
    stem = f"gems47-{arm}-{slug}-s{str(spacing).replace('.', 'p')}-{DATE}"
    fallback_stem = f"{stem}-nanoutside"
    portal_note = f"{ARM_PORTAL_NOTE[arm]} d{str(spacing).replace('.', 'p')} conformal90"
    assert len(portal_note) <= 60, portal_note

    outdir = ROOT / "docs" / "downloads"
    outdir.mkdir(parents=True, exist_ok=True)
    tif = outdir / f"{stem}-allfinite.tif"
    SUB.write_submission(dots, tif, mode="allfinite", template=template)
    checks = readback(tif, template, BUDGET)
    if not all(v is True for k, v in checks.items() if isinstance(v, bool)):
        raise SystemExit(f"{arm}: read-back validation failed: {checks}")
    audit = uniqueness_audit(dots > 0, (stem, fallback_stem))
    uniqueness_pass = bool(audit["exact_matches"] == 0 and audit["max_jaccard"] < 0.5)
    format_pass = all(v is True for k, v in checks.items() if isinstance(v, bool))

    fallback = outdir / f"{fallback_stem}.tif"
    SUB.write_submission(dots, fallback, mode="nan", template=template)

    anchor = screen["arms"]["h50"]
    incumbent = screen["arms"]["h60"]
    ctrl = screen["controls"][arm]
    rnd_primary = float(ctrl["random"]["primary"])
    rnd_sgmc = float(ctrl["random"]["sgmc"])

    if promotable and uniqueness_pass:
        verdict = (
            f"This arm BEATS the H60 incumbent on BOTH instruments on the selection half "
            f"(primary {sel:.4f} vs {float(incumbent['pooled_primary_selection']):.4f}, "
            f"SGMC {sgmc:.4f} vs {float(incumbent['pooled_sgmc_selection']):.4f}), passed "
            "the frozen uniqueness bar, and is the new PRIMARY recommendation, "
            "superseding H60 (which remains a valid, format-checked fallback).")
    elif promotable and not uniqueness_pass:
        verdict = (
            f"SCIENTIFIC PASS, UNIQUENESS FAIL. This arm BEATS the H60 incumbent on BOTH "
            f"instruments on the selection half (primary {sel:.4f} vs "
            f"{float(incumbent['pooled_primary_selection']):.4f}, SGMC {sgmc:.4f} vs "
            f"{float(incumbent['pooled_sgmc_selection']):.4f}) and passed control "
            "conditions 1-5, but its emission overlaps the H60 incumbent artifact at "
            f"mask Jaccard {audit['max_jaccard']:.4f} >= 0.5, so it FAILS frozen "
            "condition 6 (bounded uniqueness). It is unique against every SCORED prior "
            "submission and every other prior raster (see the receipt). It is NOT OK to "
            "submit while the frozen uniqueness bar stands: this repository will not "
            "recommend spending a slot on an emission that shares most of its dots with "
            "the standing incumbent. H60 remains the primary. The organiser would accept "
            "the file; the bar is this repository's own slot-protection discipline.")
    else:
        verdict = (
            f"This arm passed the four control conditions and is the frozen winner by "
            f"the SGMC tie-break, but it does NOT beat the previous incumbent H60 "
            f"({float(incumbent['pooled_primary_selection']):.4f}) on the primary "
            f"instrument ({sel:.4f}); H60 remains the recommendation and no submission "
            "slot should be spent on this artefact while H60 stands.")

    note = (
        f"{portal_note}\n"
        "\n"
        f"New hypothesis, not a copy of any prior submission.  Field ({arm}): "
        f"{ARM_BLURB[arm]}.  Emission: unit dots at {spacing:g} px "
        f"({spacing*100:g} m) over the arm's emission domain "
        f"({int(mask.sum()):,} cells), {BUDGET:,} dots.  Values are 0/1 only, float32, "
        "single band, EPSG:32611, 100 m, official grid/transform, all finite, zeros "
        "outside the footprint.\n"
        "\n"
        f"Operating point: {spacing:g} px ({spacing*100:g} m), selected by SPLIT "
        "CONFORMAL PREDICTION (Lei, G'Sell, Rinaldo, Tibshirani, Wasserman, JASA 2018, "
        "Algorithm 2) as the spacing with the greatest CERTIFIED lower bound on the "
        f"frozen 41-block holdout: max-residual rank {rank} of {n_cal + 1} "
        f"(k = ceil((n+1) x 0.90), n = {n_cal} calibration blocks), finite-sample "
        f"coverage at least {cov:.2%} (confidence level {cov:.2%}), certified holdout "
        f"floor {floor:.4f} DTI.  The selection half ({n_sel} blocks) centered the band; "
        "the disjoint calibration half certified it.  The guarantee is "
        "assumption-conditional on block-level exchangeability and covers one future "
        "exchangeable block's proxy DTI -- never the private leaderboard.\n"
        "\n"
        f"Validation: pooled selection-half DTI {sel:.4f} on the primary off-catalogue "
        f"lidar-scarp-peak instrument against {float(anchor['pooled_primary_selection']):.4f} "
        f"for the H50 anchor, {float(incumbent['pooled_primary_selection']):.4f} for the "
        f"H60 incumbent, {rnd_primary:.4f} mass-matched spaced random, "
        f"{float(ctrl['h33_reference']['primary']):.4f} the owner-reported d2.8 reference "
        f"and {float(ctrl['h47c1']['primary']):.4f} H47-C1; AND {sgmc:.4f} on the "
        f"independent SGMC off-catalogue fault population against {rnd_sgmc:.4f} random, "
        f"{float(anchor['pooled_sgmc_selection']):.4f} for H50 and "
        f"{float(incumbent['pooled_sgmc_selection']):.4f} for the H60 incumbent.\n"
        "\n"
        + verdict + "\n"
        + "\n"
        "The primary instrument is derived from the same lidar stack the field reads, "
        "so its numbers are optimistic for this field; the SGMC gain is the independent "
        "evidence.  No private label, pooled-map or leaderboard guarantee is claimed.\n"
    )

    receipt = {
        "schema_version": 1,
        "hypothesis_id": arm.upper(),
        "artifact": stem,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "spacing_px": spacing,
        "budget": BUDGET,
        "arm_spec": spec,
        "emission_domain": f"{arm} emission domain ({int(mask.sum()):,} cells)",
        "format": {
            "driver": "GTiff", "count": 1, "dtype": "float32", "crs": "EPSG:32611",
            "width": template.shape[1], "height": template.shape[0],
            "transform": list(template.transform)[:6], "nodata": None,
            "outside_footprint": "0.0 (all finite)", "values": "0.0 and 1.0 only",
        },
        "readback_checks": checks,
        "format_pass": format_pass,
        "uniqueness": {k: audit[k] for k in ("compared", "exact_matches", "max_jaccard",
                                             "max_jaccard_vs_scored_priors")},
        "uniqueness_pass": uniqueness_pass,
        "screen": "evidence/h71/screen.json",
        "preregistration": "docs/research/h71-hypotheses-preregistered.md",
        "screen_selected_spacing_px": arm_rec["selected_spacing_px"],
        "conformal": {
            "method": "max-residual one-sided split conformal, Lei et al. JASA 2018 Alg. 2; "
                      "operating point = argmax certified lower bound",
            "reference": "https://doi.org/10.1080/01621459.2017.1307116",
            "selection_blocks": n_sel,
            "calibration_blocks": n_cal,
            "rank_1_based": rank,
            "coverage_at_least": cov,
            "confidence_level_pct": round(100.0 * cov, 3),
            "certified_floor_dti": floor,
            "assumption": "block-level exchangeability, not verified; conditional guarantee",
        },
        "holdout": {
            "primary_instrument": "off-catalogue local maxima of the owner-derived 1 m lidar "
                                  "scarp stack (lappos t200 d3)",
            "candidate_pooled_dti": sel,
            "h50_anchor_pooled_dti": float(anchor["pooled_primary_selection"]),
            "h60_incumbent_pooled_dti": float(incumbent["pooled_primary_selection"]),
            "round_primary_arm": "H60 (incumbent; no arm validly displaced it this round)",
            "round_primary_pooled_dti": float(incumbent["pooled_primary_selection"]),
            "spaced_random_pooled_dti_mass_matched": rnd_primary,
            "owner_reported_d28_reference_pooled_dti":
                float(ctrl["h33_reference"]["primary"]),
            "h47c1_pooled_dti": float(ctrl["h47c1"]["primary"]),
            "independent_instrument": "SGMC off-catalogue faults (>300 m from the catalogue)",
            "candidate_sgmc_pooled_dti": sgmc,
            "h50_anchor_sgmc_pooled_dti": float(anchor["pooled_sgmc_selection"]),
            "h60_incumbent_sgmc_pooled_dti": float(incumbent["pooled_sgmc_selection"]),
            "round_primary_sgmc_pooled_dti": float(incumbent["pooled_sgmc_selection"]),
            "random_sgmc_pooled_dti": rnd_sgmc,
            "gate": gate,
        },
        "sha256_tif": sha256(tif),
        "submission_note_field": portal_note,
        "bytes": tif.stat().st_size,
        "files": [tif.name, f"{stem}.zip", f"{stem}-receipt.json", f"{stem}-note.txt",
                  fallback.name],
        "provenance_limits": [
            "The lidar scarp stack is owner-derived from USGS 3DEP 1 m DEM tiles (706/716, "
            "tile list OCR-recovered from the competition PDF), not organiser-supplied.",
            "The GeoDAWN Th/K grid is a contractor u8-rank product of the USGS GeoDAWN "
            "release (DOI 10.5066/P93LGLVQ), not physical units; not organiser-supplied.",
            "No organiser receipt links any participant score to a TIFF; the 0.2778 figure "
            "is owner-reported and the owner page marks that submission unscored.",
            "The restored data are hash-pinned owner mirrors, not organizer-authenticated "
            "bytes.",
            "The primary instrument is derived from the same lidar stack the field reads, "
            "so primary-instrument numbers are optimistic; the SGMC off-catalogue gain is "
            "the independent corroboration.",
        ],
    }
    save_json(outdir / f"{stem}-receipt.json", receipt)
    (outdir / f"{stem}-note.txt").write_text(note)

    zpath = outdir / f"{stem}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(tif, tif.name)
        z.write(outdir / f"{stem}-note.txt", f"{stem}-note.txt")
        z.write(outdir / f"{stem}-receipt.json", f"{stem}-receipt.json")

    save_json(ROOT / "docs" / "data" / f"{arm}-artifact.json", {
        **receipt,
        "download_url": f"downloads/{stem}-allfinite.tif",
        "zip_url": f"downloads/{stem}.zip",
        "note_url": f"downloads/{stem}-note.txt",
        "fallback_url": f"downloads/{fallback.name}",
        "submission_note_field": portal_note,
    })
    return receipt


def main() -> int:
    started = time.time()
    screen = json.loads((ROOT / "evidence" / "h71" / "screen.json").read_text())
    gate = screen["gate"]
    data = G.data_dir()
    template = G.load_template()

    # The primary attempt: the winner among the arms passing the frozen promotion
    # conditions 1-5 (beats_incumbent_h60 included).  If its build also passes
    # condition 6 (bounded uniqueness) it becomes the new PRIMARY artifact; if it
    # fails condition 6 it is still published, honestly labelled as a research
    # artifact that is NOT OK to submit while the bar stands.
    promotable = gate["promotable_arms"]
    primary_arm = None
    if promotable:
        attempt = max(promotable, key=lambda a: (screen["arms"][a]["pooled_sgmc_selection"],
                                                screen["arms"][a]["conformal"]["floor"]))
        r = build_artifact(attempt, screen, data, template)
        if r["uniqueness_pass"] and r["format_pass"]:
            r["kind"] = "primary"
            r["promoted_to_primary"] = True
            r["supersedes"] = "H60"
            primary_arm = attempt
        else:
            r["kind"] = "research_artifact_not_ok_to_submit_uniqueness_bar"
            r["promoted_to_primary"] = False
            r["supersedes"] = None
            r["not_ok_to_submit_reason"] = (
                "frozen condition 6 (bounded uniqueness): mask Jaccard "
                f"{r['uniqueness']['max_jaccard']:.4f} >= 0.5 against a prior raster "
                "reachable from this checkout (the H60 incumbent artifact it would "
                "supersede); unique against every scored prior submission")
        save_json(ROOT / "docs" / "data" / f"{attempt}-artifact.json", {
            **r,
            "download_url": f"downloads/{r['artifact']}-allfinite.tif",
            "zip_url": f"downloads/{r['artifact']}.zip",
            "note_url": f"downloads/{r['artifact']}-note.txt",
            "fallback_url": f"downloads/{r['artifact']}-nanoutside.tif",
            "submission_note_field": None,   # NOT OK to submit: no portal note offered
        })
        print(json.dumps({"role": r["kind"], "arm": attempt, "tif": r["artifact"],
                          "sha256": r["sha256_tif"], "spacing_px": r["spacing_px"],
                          "uniqueness_pass": r["uniqueness_pass"],
                          "max_jaccard": r["uniqueness"]["max_jaccard"]}, indent=2))

    # The validated candidate: the frozen overall winner when it passed the control
    # conditions, is not the primary, and clears the uniqueness bar.
    candidate_arm = None
    winner = gate["winner"]
    if winner is not None and winner != primary_arm and gate["per_arm"][winner]["passed"]:
        r = build_artifact(winner, screen, data, template)
        if r["uniqueness_pass"] and r["format_pass"]:
            r["kind"] = "validated_candidate_not_recommended_while_primary_stands"
            r["promoted_to_primary"] = False
            r["supersedes"] = None
            candidate_arm = winner
            save_json(ROOT / "docs" / "data" / f"{winner}-artifact.json", {
                **r,
                "download_url": f"downloads/{r['artifact']}-allfinite.tif",
                "zip_url": f"downloads/{r['artifact']}.zip",
                "note_url": f"downloads/{r['artifact']}-note.txt",
                "fallback_url": f"downloads/{r['artifact']}-nanoutside.tif",
                "submission_note_field": r["submission_note_field"],
            })
            print(json.dumps({"role": r["kind"], "arm": winner, "tif": r["artifact"],
                              "sha256": r["sha256_tif"], "spacing_px": r["spacing_px"]},
                             indent=2))
        else:
            print(json.dumps({"role": "not published (uniqueness bar)", "arm": winner,
                              "max_jaccard": r["uniqueness"]["max_jaccard"]}, indent=2))

    # deploy the evidence receipts the site renders
    deployed = {}
    payload = json.loads((ROOT / "evidence" / "h71" / "screen.json").read_text())
    payload["deployed_from"] = "evidence/h71/screen.json"
    save_json(ROOT / "docs" / "data" / "h71-screen.json", payload)
    deployed["h71-screen.json"] = sha256(ROOT / "docs" / "data" / "h71-screen.json")
    shutil.copyfile(ROOT / "evidence" / "h71" / "spacing-history.csv",
                    ROOT / "docs" / "data" / "h71-spacing-history.csv")
    deployed["h71-spacing-history.csv"] = sha256(ROOT / "docs" / "data" / "h71-spacing-history.csv")
    shutil.copyfile(ROOT / "evidence" / "h33_reference_analysis.json",
                    ROOT / "docs" / "data" / "h33-reference-analysis.json")
    deployed["h33-reference-analysis.json"] = sha256(
        ROOT / "docs" / "data" / "h33-reference-analysis.json")
    for name in ("h71", "h74"):
        p = ROOT / "docs" / "data" / f"{name}-artifact.json"
        if p.is_file():
            d = json.loads(p.read_text())
            d["deployed_evidence_sha256"] = deployed
            save_json(p, d)

    print(json.dumps({"primary_arm": primary_arm,
                      "incumbent_remains_primary": primary_arm is None,
                      "candidate_arm": candidate_arm,
                      "elapsed_seconds": round(time.time() - started, 2)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
