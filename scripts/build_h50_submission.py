#!/usr/bin/env python3
"""Rebuild H50a model output and package two explicitly labelled research encodings.

The H50a prediction field is generated from the restored inputs every time; it is
not copied from a historical submission. Both exports remain research-only:
local file-format success does not authorize a competition slot.

* ``finite-mask`` keeps finite raw [0, 1] samples plus a self-contained GDAL
  null mask. It is a diagnostic for a NaN-intolerant range reader.
* ``template-nanoutside`` uses the mirrored sample template's NaN/no-data
  convention. It is checked against that exact template mask and is the closest
  local encoding to the published null-or-NaN wording.

Neither mode diagnoses the historical portal range rejection: the rejected bytes
and an organizer parser receipt were not supplied.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from gems47 import contract as C
from gems47 import grid as G
from gems47 import submission as S
from gems47s3 import emission as E
from gems47s3 import geomorph
from gems47s3.detector import Bands, Recipe, build_core
from gems47s3.grid import Grid
from gemsdoe47.validation import validate_submission as validate_template_nan


def zip_or_validate(tiff: Path) -> dict:
    """Create a deterministic one-TIFF ZIP, or verify the existing exact ZIP."""
    path = tiff.with_suffix(".zip")
    if not path.exists():
        return C.single_tiff_zip(tiff, path)
    with zipfile.ZipFile(path) as archive:
        members = archive.namelist()
        exact = members == [tiff.name] and hashlib.sha256(archive.read(tiff.name)).hexdigest() == C.sha256(tiff)
    if not exact:
        raise ValueError(f"existing ZIP does not contain the exact verified TIFF: {path}")
    return {
        "filename": path.name,
        "sha256": C.sha256(path),
        "bytes": path.stat().st_size,
        "members": members,
        "single_geotiff_verified": True,
    }


def read_positive_mask(path: Path) -> np.ndarray:
    with rasterio.open(path) as source:
        if source.count != 1:
            raise ValueError(f"{path} is not single-band")
        return source.read(1) > 0


def finite_or_validate(path: Path, dots: np.ndarray, template: G.Template) -> dict:
    """Write the finite internal-mask diagnostic once, then fail closed on drift."""
    if path.exists():
        audit = C.validate(path, template)
        if not audit["format_valid"] or not np.array_equal(read_positive_mask(path), dots):
            raise ValueError("existing finite-mask artifact differs from H50a model output or fails local contract")
        return audit
    return C.write(
        dots.astype("float32"),
        path,
        template,
        tags={"STATUS": "RESEARCH_ONLY_DO_NOT_UPLOAD", "METHOD": "H50a corridor; finite internal mask"},
    )


def template_nan_or_validate(path: Path, dots: np.ndarray, template: G.Template, template_path: Path) -> tuple[dict, dict]:
    """Write/verify the template-matching NaN export and its two local audits."""
    if path.exists():
        if not np.array_equal(read_positive_mask(path), dots):
            raise ValueError("existing template-NaN artifact differs from H50a model output")
    else:
        # The writer uses the template footprint and places NaN only outside it.
        S.write_submission(dots.astype("float32"), path, mode="nan", template=template)
        with rasterio.open(path, "r+") as destination:
            destination.update_tags(
                PROJECT="GEMSDOE47",
                METHOD="H50a corridor; sample-template NaN outside",
                STATUS="RESEARCH_ONLY_DO_NOT_UPLOAD",
            )

    generic_audit = S.validate_submission(path, template=template)
    if not generic_audit["required_local_checks_passed"]:
        raise ValueError(f"template-NaN generic local contract failed: {generic_audit['hard_failures']}")
    strict_audit = validate_template_nan(path, template_path, template_footprint=True)
    if strict_audit["status"] != "LOCAL_PASS":
        raise ValueError("template-NaN strict local contract did not pass")

    with rasterio.open(path) as source:
        raw = source.read(1)
        expected_nan = ~template.footprint
        exact_template_encoding = (
            source.nodata is not None
            and np.isnan(source.nodata)
            and source.count == 1
            and source.dtypes == ("float32",)
            and source.shape == template.shape
            and source.crs == rasterio.crs.CRS.from_string(template.crs)
            and source.transform == template.transform
            and np.array_equal(np.isnan(raw), expected_nan)
            and np.isfinite(raw[template.footprint]).all()
            and ((raw[template.footprint] >= 0) & (raw[template.footprint] <= 1)).all()
            and len(source.files) == 1
        )
    if not exact_template_encoding:
        raise ValueError("template-NaN artifact does not match the expected local template encoding")
    return generic_audit, strict_audit


def main() -> None:
    certificate = json.loads((ROOT / "evidence/h50/conformal_certificate_h50.json").read_text())
    choice = certificate["chosen"]
    if choice["arm"] != "H50a_corridor" or choice["emitter"] != "disk":
        raise ValueError("This research builder implements only the original selected H50a disk arm")

    data_dir = ROOT / ".cache/gems_data"
    g = Grid(data_dir)
    valid = g.all_bands_finite()
    template = G.load_template(data_dir)
    template_path = data_dir / "sample_submission.tif"

    spec = importlib.util.spec_from_file_location("h50", ROOT / "scripts/run_h50.py")
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError("could not load the H50 model module")
    spec.loader.exec_module(module)
    recipe = Recipe(
        name="R7_scarp9_polarity",
        terms=[
            ("det_elev_slope", "scarp", 9.0, 3.0),
            ("det_elev_slope", "polarity", 9.0, 2.0),
            ("det_elev_slope", "curv", 2.5, 1.0),
            ("det_elev_slope", "detrend", 2.5, 1.0),
            ("det_elev_slope", "slope_var", 5.0, 1.0),
        ],
    )
    core = build_core(recipe, Bands(data_dir / "training_features.tif"), valid)["core"]
    prior = module.reservoir_corridor_prior(data_dir, valid)["prior"]
    field = module.combine_terms([(core, 1.0)], valid) * (0.35 + 0.65 * prior)
    field = np.where(valid, geomorph.rank_scale(np.where(valid, field, np.nan)), 0).astype("float32")
    allowed = valid & template.footprint & (g.d_catalogue > choice["flank_b"])
    dots = E.nms_disk(field, allowed, choice["spacing_px"])
    budget = round(7.37 * int((valid & ~g.catalogue).sum()) / 1000)
    if dots.sum() > budget:
        dots = E.topk_mask(field, budget, dots)
    if int(dots.sum()) != budget:
        raise ValueError("H50 global emitter did not reach its declared budget")

    digest = hashlib.sha256(np.packbits(dots).tobytes()).hexdigest()
    stem = f"gems47-h50a-corridor-s1p5-b3-20261007-{digest[:12]}"
    out_dir = ROOT / "docs/downloads"
    finite_path = out_dir / f"{stem}-research-finite-mask.tif"
    template_nan_path = out_dir / f"{stem}-template-nanoutside.tif"

    comparisons = []
    prior_paths = sorted(out_dir.rglob("*.tif"))
    prior_paths += sorted(data_dir.glob("scored/*.tif")) + sorted(data_dir.glob("reference/*.tif"))
    prior_paths += sorted((ROOT / "submission").glob("*.tif"))
    for other in prior_paths:
        if other in {finite_path, template_nan_path}:
            continue
        with rasterio.open(other) as source:
            if source.count != 1 or source.shape != dots.shape or source.transform != template.transform:
                continue
            values = source.read(1)
            mask = np.isfinite(values) & (values > 0)
        union = (mask | dots).sum()
        comparisons.append(
            {
                "path": str(other.relative_to(ROOT)),
                "sha256": C.sha256(other),
                "exact": bool(np.array_equal(mask, dots)),
                "jaccard": float((mask & dots).sum() / union) if union else 1.0,
            }
        )
    if not comparisons or any(row["exact"] for row in comparisons):
        raise ValueError("Exact positive-mask match to a bounded prior inventory; no uniqueness claim permitted")

    finite_audit = finite_or_validate(finite_path, dots, template)
    finite_zip = zip_or_validate(finite_path)
    generic_nan_audit, strict_nan_audit = template_nan_or_validate(template_nan_path, dots, template, template_path)
    template_nan_zip = zip_or_validate(template_nan_path)

    template_note = (
        "H50a corridor; s=1.5px/150m; template NaN outside; nominal 90% proxy floor=0.0000; "
        "coverage unverified; UNSCORED; NOT PROMOTED; DO NOT UPLOAD"
    )
    finite_note = (
        "H50a corridor finite-mask diagnostic; s=1.5px/150m; nominal 90% proxy floor=0.0000; "
        "coverage unverified; UNSCORED; NOT PROMOTED; DO NOT UPLOAD"
    )
    if max(len(template_note), len(finite_note)) > 200:
        raise ValueError("submission note exceeds 200 characters")

    shared = {
        "status": "RESEARCH_ONLY_NOT_PROMOTED",
        "slot_authorized": False,
        "submission_eligible": False,
        "organizer_acceptance_verified": False,
        "name": f"GEMSDOE47-H50a-{digest[:12]}",
        "selection": choice,
        "conformal": certificate,
        "uniqueness": {
            "comparisons": comparisons,
            "exact_matches": 0,
            "max_jaccard": max(row["jaccard"] for row in comparisons),
            "scope": "Only listed local/restored rasters; not a global uniqueness proof.",
        },
        "emission": {
            "prediction_mask_sha256": digest,
            "n_dots": int(dots.sum()),
            "budget": budget,
            "global_emission_not_block_certificate": True,
        },
        "warning": "DO NOT UPLOAD: the spatial validation/promotion gate is closed.",
    }
    finite_receipt = {
        **shared,
        "note": finite_note,
        "artifact_role": "finite_internal_mask_range_diagnostic",
        "filename": finite_path.name,
        "format_validation": finite_audit,
        "zip": finite_zip,
        "format_encoding": "finite raw [0,1] plus internal GDAL null mask; not the sample's NaN-nodata encoding",
    }
    template_nan_receipt = {
        **shared,
        "note": template_note,
        "artifact_role": "template_nanoutside_format_checkpoint",
        "filename": template_nan_path.name,
        "format_validation": generic_nan_audit,
        "strict_template_validation": strict_nan_audit,
        "zip": template_nan_zip,
        "format_encoding": "float32 with NaN nodata and raw NaN exactly outside the mirrored sample template mask",
        "same_prediction_mask_as": finite_path.name,
        "format_status": "LOCAL_TEMPLATE_MATCH_PASS; ORGANIZER_ACCEPTANCE_UNVERIFIED",
    }

    destinations = {
        finite_path.with_suffix(".json"): finite_receipt,
        ROOT / "evidence/h50/submission_build_h50.json": finite_receipt,
        ROOT / "docs/data/h50-submission.json": finite_receipt,
        template_nan_path.with_suffix(".json"): template_nan_receipt,
        ROOT / "evidence/h50/template_nanoutside_build_h50.json": template_nan_receipt,
        ROOT / "docs/data/h50-template-nanoutside.json": template_nan_receipt,
    }
    for destination, receipt in destinations.items():
        C.save_receipt(destination, receipt)
    finite_path.with_suffix(".txt").write_text(
        "Finite-mask diagnostic. " + finite_note + "\n",
        encoding="utf-8",
    )
    template_nan_path.with_suffix(".txt").write_text(
        "Template-NaN format checkpoint. " + template_note + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "name": shared["name"],
                "prediction_mask_sha256": digest,
                "dots": int(dots.sum()),
                "finite_mask": finite_path.name,
                "template_nanoutside": template_nan_path.name,
                "template_strict_status": strict_nan_audit["status"],
                "slot_authorized": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
