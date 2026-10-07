from __future__ import annotations

import hashlib
import shutil

import numpy as np
import rasterio
from affine import Affine

from scripts import audit_candidate_uniqueness as audit


def _write_raster(path, values: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=values.shape[0],
        width=values.shape[1],
        count=1,
        dtype="float32",
        crs="EPSG:32611",
        transform=Affine(100, 0, 243350, 0, -100, 4508550),
    ) as dataset:
        dataset.write(values.astype("float32"), 1)


def test_local_uniqueness_excludes_byte_identical_candidate_copies(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    candidate_path = tmp_path / "submission" / "candidate.tif"
    candidate_values = np.zeros((4, 4), dtype="float32")
    candidate_values[1, 1] = 1
    candidate_values[2, 2] = 1
    _write_raster(candidate_path, candidate_values)

    candidate_copy = tmp_path / "docs" / "downloads" / "candidate-copy.tif"
    candidate_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(candidate_path, candidate_copy)

    prior_path = tmp_path / ".cache" / "gems_data" / "reference" / "prior.tif"
    prior_values = np.zeros((4, 4), dtype="float32")
    prior_values[1, 1] = 1
    _write_raster(prior_path, prior_values)

    with rasterio.open(candidate_path) as dataset:
        grid = audit._grid(dataset)
    footprint = np.ones((4, 4), dtype=bool)
    candidate_mask = candidate_values > 0
    candidate_sha256 = hashlib.sha256(candidate_path.read_bytes()).hexdigest()

    result = audit._compare_local_prior_artifacts(
        candidate_path,
        grid,
        candidate_mask,
        footprint,
        int(candidate_mask.sum()),
        candidate_sha256,
    )

    assert result["artifacts_attempted"] == 1
    assert result["exact_grid_comparisons"] == 1
    assert result["exact_positive_mask_matches"] == 0
    assert result["maximum_positive_support_jaccard"] == 0.5
    assert result["same_candidate_copies_excluded"] == [
        {
            "path": "docs/downloads/candidate-copy.tif",
            "sha256": candidate_sha256,
            "reason": "byte-identical copy of the candidate; not an independent prior artifact",
        }
    ]
