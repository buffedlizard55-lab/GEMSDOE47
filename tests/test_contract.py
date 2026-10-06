"""Finite values plus a self-contained internal null mask; no organizer claims."""
import hashlib
import zipfile

import numpy as np
import pytest
import rasterio
from rasterio.transform import Affine

from gems47 import contract as C
from gems47.grid import Template


@pytest.fixture
def template():
    foot = np.zeros((30, 25), bool); foot[3:27, 3:22] = True
    return Template(foot.shape, Affine(100, 0, 243350, 0, -100, 4508550),
                    "EPSG:32611", foot, np.zeros_like(foot))


def test_internal_mask_meets_both_raw_range_and_null_footprint_readings(tmp_path, template):
    values = np.zeros(template.shape, np.float32); values[10, 10] = 1
    path = tmp_path / "new.tif"
    audit = C.write(values, path, template)
    assert audit["format_valid"]
    assert len(audit["checks"]) == 15 and all(audit["checks"].values())
    assert not audit["organizer_acceptance_verified"]
    assert audit["stats"]["raw_nonfinite_pixels"] == 0
    with rasterio.open(path) as source:
        assert source.nodata is None and len(source.files) == 1
        assert np.all((source.read(1) >= 0) & (source.read(1) <= 1))
        assert np.array_equal(np.ma.getmaskarray(source.read(1, masked=True)), ~template.footprint)
        assert not np.ma.getmaskarray(source.read(1, masked=True))[8, 8]  # valid absence is not nodata
    assert not path.with_suffix(".tif.msk").exists()


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf, -.00001, 1.00000001])
def test_bad_interior_rejected_before_float32_rounding_or_repair(tmp_path, template, bad):
    values = np.zeros(template.shape, np.float64); values[10, 10] = bad
    with pytest.raises(ValueError, match="before float32"):
        C.write(values, tmp_path / "bad.tif", template)
    assert not (tmp_path / "bad.tif").exists()


def test_invalid_outside_samples_cannot_leak_into_output(tmp_path, template):
    values = np.zeros(template.shape); values[~template.footprint] = -3.4e38
    audit = C.write(values, tmp_path / "safe.tif", template)
    assert audit["format_valid"] and audit["stats"]["min"] == 0


def test_zip_contains_only_the_byte_identical_tiff_and_is_reproducible(tmp_path, template):
    tiff = tmp_path / "new.tif"
    C.write(np.zeros(template.shape), tiff, template)
    a = C.single_tiff_zip(tiff, tmp_path / "a.zip")
    b = C.single_tiff_zip(tiff, tmp_path / "b.zip")
    assert a["sha256"] == b["sha256"]
    with zipfile.ZipFile(tmp_path / "a.zip") as archive:
        assert archive.namelist() == ["new.tif"]
        assert hashlib.sha256(archive.read("new.tif")).hexdigest() == C.sha256(tiff)


def test_export_refuses_to_overwrite_a_previous_submission(tmp_path, template):
    path = tmp_path / "prior.tif"
    values = np.zeros(template.shape)
    C.write(values, path, template)
    first = C.sha256(path)
    with pytest.raises(FileExistsError):
        C.write(values, path, template)
    assert C.sha256(path) == first


def test_wrong_grid_validates_as_failure_without_indexing_crash(tmp_path, template):
    path = tmp_path / "wrong.tif"
    with rasterio.open(path, "w", driver="GTiff", height=8, width=9, count=1, dtype="float32",
                       crs=template.crs, transform=template.transform) as source:
        source.write(np.zeros((8, 9), np.float32), 1)
    result = C.validate(path, template)
    assert not result["format_valid"]
    assert "shape_matches_template" in result["failed_checks"]
