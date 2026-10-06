"""CI reopens the ACTUAL new research TIFF without downloading training inputs."""
import csv
import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import rasterio

from gems47 import grid as G
from gems47 import spatial_screen as B
from gems47.conformal import choose_operating_point, simultaneous_lower_bounds

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / "evidence" / name).read_text())


def test_actual_research_tiff_matches_grid_range_mask_and_byte_receipts():
    receipt = read("current-submission.json")
    path = ROOT / "docs" / "downloads" / receipt["filename"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == receipt["format_validation"]["sha256"]
    assert not receipt["slot_authorized"] and receipt["organizer_score"] is None
    with rasterio.open(path) as source:
        assert source.count == 1 and source.dtypes == ("float32",)
        assert source.shape == G.SHAPE and source.transform == G.TRANSFORM
        assert source.crs == rasterio.crs.CRS.from_string(G.CRS)
        assert tuple(source.bounds) == G.BOUNDS
        assert source.nodata is None and len(source.files) == 1
        p = source.read(1); mask = source.read_masks(1) > 0
    assert np.isfinite(p).all() and np.isin(p, (0, 1)).all()
    assert int((p > 0).sum()) == 37_654
    assert int(mask.sum()) == G.FOOTPRINT_PIXELS
    assert not (p[~mask] > 0).any()
    assert hashlib.sha256(np.packbits(p.ravel() > 0).tobytes()).hexdigest() == receipt["prediction_mask_sha256"]
    with zipfile.ZipFile(path.with_suffix(".zip")) as archive:
        assert archive.namelist() == [path.name]
        assert hashlib.sha256(archive.read(path.name)).hexdigest() == receipt["format_validation"]["sha256"]


def test_raw_spacing_history_recomputes_the_locked_band_and_failed_gate():
    screen = read("profile-screen.json")
    with (ROOT / "evidence" / "profile-spacing-history.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        for key in ["DTI", "TP_w", "FP_w", "FN_w", "S", "Phi", "|G|", "spacing_px"]:
            row[key] = float(row[key])
        row["block_id"] = int(row["block_id"])
    def matrix(role):
        rr = [r for r in rows if r["role"] == role and r["model"] == "profile"]
        ids = sorted({r["block_id"] for r in rr})
        return np.array([[next(r["DTI"] for r in rr if r["block_id"] == i and r["spacing_px"] == d)
                          for d in screen["spacings_px"]] for i in ids])
    band = simultaneous_lower_bounds(matrix("selection"), matrix("calibration"), coverage=.9)
    assert band["lower_bounds"] == screen["conformal"]["lower_bounds"] == [0] * 5
    assert band["quantile"] == screen["conformal"]["quantile"]
    idx = choose_operating_point(band, screen["spacings_px"])
    assert screen["spacings_px"][idx] == screen["selected_spacing_px"] == 2.8
    def selected(model, spacing):
        return [r for r in rows if r["role"] == "test" and r["model"] == model and r["spacing_px"] == spacing]
    gate = B.gate(selected("profile", 2.8), selected(screen["incumbent_model"], screen["incumbent_spacing_px"]),
                  selected("random", 2.8), lower_floor=band["lower_bounds"][idx])
    for key in ["candidate_pooled_dti", "incumbent_pooled_dti", "random_pooled_dti", "candidate_block_wins",
                "screen_passed", "slot_authorized"]:
        assert gate[key] == screen["screen_gate"][key]
    assert not gate["screen_passed"] and not gate["slot_authorized"]


def test_deployed_receipts_are_exact_copies_not_broken_parent_links():
    for name in ["current-submission.json", "profile-screen.json", "profile-spacing-history.csv", "profile-uniqueness.json"]:
        assert (ROOT / "docs" / "data" / name).read_bytes() == (ROOT / "evidence" / name).read_bytes()
    audit = read("profile-uniqueness.json")
    assert audit["comparisons"] >= 500 and audit["exact_matches"] == 0
    assert audit["bounded_unique"] and not audit["global_unique_proven"]
