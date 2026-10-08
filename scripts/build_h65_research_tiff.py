#!/usr/bin/env python3
"""Build a fresh H65 research-only GeoTIFF; this is not a submission-ready gate."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
import numpy as np
import rasterio

from gems47 import grid as G
from gems47 import h60, h65
from gems47 import submission as SUB
from gemsdoe47.magnetic import ranked_pixels

NAME = "gemsdoe47-h65-paired-scarp-consensus-s2p8-20261008-research-only-nanoutside"
OUT = ROOT / "docs/downloads" / f"{NAME}.tif"
RECEIPT = ROOT / "docs/data/h65-research-tiff.json"
NOTE = ROOT / "docs/downloads" / f"{NAME}-note.txt"
BUDGET = 37_654
PORTAL_NAME = "GEMSDOE47-H65-paired-scarp-s2p8-20261008"
PORTAL_NOTE = "H65 paired scarp consensus d2p8"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def local_uniqueness(pred: np.ndarray, template: G.Template, candidate: Path) -> dict:
    footprint = template.footprint
    paths = set((ROOT / "docs/downloads").glob("*.tif"))
    paths |= set((ROOT / ".cache/gems_data/scored").glob("*.tif"))
    paths |= set((ROOT / ".cache/gems_data/reference").glob("*.tif"))
    paths |= set((ROOT / "submission").glob("*.tif"))
    rows = []
    for path in sorted(paths):
        if path.resolve() == candidate.resolve():
            continue
        try:
            with rasterio.open(path) as src:
                if (src.count != 1 or src.shape != pred.shape or src.crs is None
                        or src.crs.to_string() != template.crs
                        or src.transform != template.transform):
                    rows.append({"path": str(path.relative_to(ROOT)), "comparable": False})
                    continue
                other = src.read(1)
            mask = np.isfinite(other) & (other > 0) & footprint
            inter, union = int((pred & mask).sum()), int((pred | mask).sum())
            rows.append({"path": str(path.relative_to(ROOT)), "comparable": True,
                         "positive_pixels": int(mask.sum()), "intersection": inter,
                         "union": union, "jaccard": inter / max(union, 1),
                         "exact_positive_mask_match": bool(np.array_equal(pred, mask))})
        except (OSError, rasterio.errors.RasterioError) as exc:
            rows.append({"path": str(path.relative_to(ROOT)), "comparable": False,
                         "error": str(exc)})
    comparable = [r for r in rows if r.get("comparable")]
    return {"scope": "local TIFFs reachable in docs/downloads, submission, and restored scored/reference cache; not global",
            "compared": len(rows), "comparable": len(comparable),
            "exact_matches": sum(r["exact_positive_mask_match"] for r in comparable),
            "max_jaccard": max((r["jaccard"] for r in comparable), default=0.0),
            "rows": rows}


def main() -> int:
    if OUT.exists() or RECEIPT.exists() or NOTE.exists():
        raise SystemExit("H65 output already exists; refusing to overwrite a research artifact")
    screen = json.loads((ROOT / "evidence/h65/screen.json").read_text())
    sgmc = screen["models"]["h65"]["sgmc_offcat"]
    spacing = float(sgmc["selected_spacing_px"])
    if spacing != 2.8:
        raise SystemExit(f"expected frozen output stem s2p8, selected spacing changed to {spacing}")
    paired_floor = float(screen["paired_h65_minus_h60_sgmc"]["lower_prediction_bound"])
    if screen["promotion_gate"]["all_passed"] or paired_floor > 0:
        raise SystemExit("screen no longer records a failed H65 promotion gate; review before building")

    data = G.data_dir()
    for key, pin in screen["input_pins"].items():
        path = data / pin["path"]
        if sha256(path) != pin["sha256"]:
            raise SystemExit(f"input hash changed since screening: {key}")
    template = G.load_template(data)
    emission = h60.h60_emission_domain(data)
    field = h65.paired_morphology_field(data, emission)
    order = ranked_pixels(field, emission)
    indices = h60._greedy_up_to(order, field.shape, spacing, BUDGET)
    dots = np.zeros(template.shape, dtype=np.float32)
    dots.ravel()[indices] = 1.0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    SUB.write_submission(dots, OUT, mode="nan", template=template)
    validation = SUB.validate_submission(OUT, template)
    if not validation["required_local_checks_passed"]:
        raise SystemExit(f"local required format checks failed: {validation['hard_failures']}")

    with rasterio.open(OUT) as src:
        values = src.read(1)
        assert src.count == 1 and src.dtypes == ("float32",)
        assert src.crs.to_string() == template.crs
        assert src.shape == template.shape and src.transform == template.transform
        assert src.nodata is not None and np.isnan(src.nodata)
        assert np.isnan(values[~template.footprint]).all()
        finite_in = values[template.footprint]
        assert np.isfinite(finite_in).all()
        assert ((finite_in >= 0) & (finite_in <= 1)).all()
        assert set(np.unique(finite_in).tolist()) <= {0.0, 1.0}
        assert not (dots.astype(bool) & template.catalogue).any()
    uniqueness = local_uniqueness(dots.astype(bool), template, OUT)
    if uniqueness["exact_matches"]:
        raise SystemExit("exact local positive-mask duplicate detected; do not publish")

    note_text = (
        f"{PORTAL_NOTE}\n"
        "Research artifact only — the H65 spatial screen failed its preregistered paired-bound gate. "
        "Do not upload or spend a competition slot. H65 uses a cube-root consensus of ranked "
        "step_max, lapneg_max, and lappos_max owner-derived LiDAR scarp descriptors; this is a "
        "testable morphology hypothesis, not confirmed fault truth. The selected spacing is "
        f"{spacing:g} px / {spacing*100:g} m.\n"
        "If a future, separately preregistered review authorizes a portal attempt, proposed name: "
        f"{PORTAL_NAME}; proposed short Note: {PORTAL_NOTE}. This text is not permission to submit.\n"
    )
    NOTE.write_text(note_text, encoding="utf-8")
    receipt = {
        "schema_version": 1, "status": "H65_RESEARCH_ONLY_NOT_PROMOTED_DO_NOT_SUBMIT",
        "hypothesis_id": "H65", "artifact_name": NAME,
        "filename": OUT.name, "download_path": f"docs/downloads/{OUT.name}",
        "sha256": sha256(OUT), "bytes": OUT.stat().st_size,
        "prediction_mask_sha256": hashlib.sha256(np.packbits(dots.ravel() > 0).tobytes()).hexdigest(),
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "selected_spacing_px": spacing, "selected_spacing_m": spacing * 100,
        "nominal_proxy_coverage": float(sgmc["nominal_coverage"]),
        "finite_sample_coverage_at_least_if_exchangeable": float(
            sgmc["finite_sample_coverage_at_least_if_exchangeable"]),
        "conformal_rank_1_based": int(sgmc["order_statistic_rank_1_based"]),
        "conformal_floor_sgmc_proxy": float(sgmc["selected_lower_prediction_bound"]),
        "paired_h65_minus_h60_sgmc_floor": paired_floor,
        "promotion_gate_passed": False, "organizer_acceptance_established": False,
        "slot_authorized": False, "slot_used": False,
        "unique_portal_name_if_future_authorized": PORTAL_NAME,
        "proposed_short_portal_note_if_future_authorized": PORTAL_NOTE,
        "predicted_pixels": int(dots.sum()), "target_budget": BUDGET,
        "emission_domain_pixels": int(emission.sum()),
        "format_validation": validation,
        "bounded_local_uniqueness": uniqueness,
        "uniqueness_global_proven": False,
        "source_report": "evidence/h65/screen.json",
        "official_source_context": {
            "problem_metric": "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/",
            "lidar_source": "https://www.usgs.gov/core-science-systems/ngp/3dep/about-3dep-products-services",
            "provenance": "Hash-pinned owner-derived LiDAR stack; not organizer-authenticated.",
        },
        "builder_sha256": sha256(Path(__file__)),
        "field_source": "src/gems47/h65.py::paired_morphology_field",
        "emitter_source": "gemsdoe47.magnetic.ranked_pixels + gems47.h60._greedy_up_to",
        "range_error_note": "Finite in-footprint predictions are exactly 0/1. NaN is used outside the template footprint per the published convention; the prior rejection cause remains unknown because rejected bytes and parser receipt are unavailable.",
        "no_leaderboard_claim": "No score was submitted or returned; this public-proxy screen cannot establish whether the file would beat 0.3774.",
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"file": str(OUT.relative_to(ROOT)), "sha256": receipt["sha256"],
                      "bytes": receipt["bytes"], "dots": receipt["predicted_pixels"],
                      "spacing_px": spacing, "format_pass": validation["required_local_checks_passed"],
                      "uniqueness": {k: uniqueness[k] for k in ("compared", "exact_matches", "max_jaccard")},
                      "status": receipt["status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
