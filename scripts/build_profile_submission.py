#!/usr/bin/env python3
"""Package the new H47-C1 research raster; never authorize a competition slot.

Requires the frozen screen's exact prediction fingerprint and code/data hashes.
The file is new model inference, not a renamed or copied historical submission.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems47 import contract as C
from gems47 import grid as G
from gems47.conformal import choose_operating_point


def main() -> int:
    screen_path = ROOT / "evidence" / "profile-screen.json"
    screen = json.loads(screen_path.read_text())
    if screen["hypothesis_id"] != "H47-C1" or screen["status"] != "RESEARCH_ONLY_NOT_PROMOTED":
        raise ValueError("only the frozen research-only H47-C1 screen can be packaged")
    for relative, sha in screen["code_sha256"].items():
        if C.sha256(ROOT / relative) != sha:
            raise ValueError(f"code changed after the screen: {relative}; do not mislabel this artifact")
    if C.sha256(ROOT / "docs" / "research" / "h47c-hypotheses-preregistered.md") != screen["protocol_sha256"]:
        raise ValueError("protocol changed after scoring")
    template = G.load_template()
    prediction = np.load(ROOT / ".cache" / "profile_screen" / "candidate.npy")
    packed_sha = hashlib.sha256(np.packbits(prediction.ravel() > 0).tobytes()).hexdigest()
    if packed_sha != screen["candidate_mask_sha256"]:
        raise ValueError("candidate prediction fingerprint does not match the scored build")
    if prediction.shape != template.shape or not np.isin(prediction, (0, 1)).all():
        raise ValueError("expected a binary, normalized unit-dot raster on the exact template grid")
    if int(prediction.sum()) != screen["candidate_prediction_pixels"] or prediction[~template.evaluated].any():
        raise ValueError("prediction mass/domain mismatch")
    spacing = screen["selected_spacing_px"]
    i = choose_operating_point(screen["conformal"], screen["spacings_px"])
    if screen["spacings_px"][i] != spacing:
        raise ValueError("final spacing differs from the conformal selection rule")
    floor = screen["conformal"]["lower_bounds"][i]
    slug_spacing = str(spacing).replace(".", "p")
    name = f"gems47-c1-oddstep-channel-d{slug_spacing}-20261006-{packed_sha[:12]}-finite-mask"
    out_dir = ROOT / "docs" / "downloads"
    path = out_dir / f"{name}.tif"
    note = (f"H47C1 odd-step/channel; d={spacing:g}px/{spacing*100:g}m; "
            f"90% marginal proxy L={floor:.4f} (assumed exch.), not private; "
            "37654 dots; finite+mask; UNSCORED; NOT PROMOTED")
    if len(note) > 200:
        raise ValueError("submission note exceeds 200 characters")
    if path.exists():
        audit = C.validate(path, template)
        if not audit["format_valid"]:
            raise ValueError("existing artifact failed re-verification")
        import rasterio
        with rasterio.open(path) as source:
            if not np.array_equal(source.read(1), prediction):
                raise ValueError("existing artifact has different prediction samples")
    else:
        audit = C.write(prediction, path, template, tags={
            "PROJECT": "GEMSDOE47", "HYPOTHESIS": "H47-C1_ODD_STEP_VS_EVEN_CHANNEL",
            "STATUS": "RESEARCH_ONLY_NOT_PROMOTED_DO_NOT_UPLOAD", "SPACING_PX": str(spacing),
            "CONFORMAL_TARGET": "public-catalogue block only; no private/global guarantee",
            "CONFORMAL_NOMINAL_COVERAGE": "0.90", "CONFORMAL_PROXY_FLOOR": str(floor),
            "PREDICTION_MASK_SHA256": packed_sha,
        })
    zip_path = path.with_suffix(".zip")
    if zip_path.exists():
        import zipfile
        with zipfile.ZipFile(zip_path) as archive:
            if archive.namelist() != [path.name] or hashlib.sha256(archive.read(path.name)).hexdigest() != audit["sha256"]:
                raise ValueError("existing zip differs from the TIFF")
        zip_receipt = {"filename": zip_path.name, "sha256": C.sha256(zip_path), "bytes": zip_path.stat().st_size,
                       "members": [path.name], "single_geotiff_verified": True}
    else:
        zip_receipt = C.single_tiff_zip(path, zip_path)
    receipt = {
        "schema_version": 1, "status": "RESEARCH_ONLY_NOT_PROMOTED", "slot_authorized": False,
        "hypothesis_id": "H47-C1", "filename": path.name, "download_relative_to_docs": f"downloads/{path.name}",
        "submission_name": f"GEMSDOE47-C1-D{slug_spacing}-{packed_sha[:12]}", "portal_note": note,
        "portal_note_characters": len(note), "format_validation": audit, "zip": zip_receipt,
        "prediction_mask_sha256": packed_sha, "screen_sha256": C.sha256(screen_path),
        "chosen_spacing_px": spacing, "chosen_spacing_m": spacing * 100,
        "conformal_nominal_coverage": .90, "conditional_public_block_floor": floor,
        "private_or_global_floor_certified": False, "organizer_score": None,
        "screen_gate": screen["screen_gate"],
        "no_historical_submission_used_to_construct_prediction": True,
        "data_authentication": "SHA-256 pinned repository mirrors, not authenticated DrivenData downloads",
        "warning": "DO NOT UPLOAD: no eligible submission. Format success is not scientific promotion.",
    }
    audit["path"] = receipt["download_relative_to_docs"]
    C.save_receipt(ROOT / "evidence" / "current-submission.json", receipt)
    C.save_receipt(out_dir / f"{name}.json", receipt)
    (out_dir / f"{name}.txt").write_text(note + "\n")
    print(json.dumps(receipt, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
