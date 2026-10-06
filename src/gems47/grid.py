"""Grid / template constants for the GEMS Prize Challenge submission raster.

Every constant here was read back from hash-pinned, owner-supplied mirror copies
of ``sample_submission.tif`` / ``labels.tif``, not from documentation. The
mirror is not organizer authentication. The verification command is
``scripts/verify_grid.py``.

Official format requirements (competition page 967, "Submission format"):
  * same projected CRS as the training data -> UTM zone 11N, EPSG:32611
  * same resolution as the training data     -> 100 m
  * same bounds as the training data, data outside the bounds null or nan
  * single layer, float32, values in [0, 1]
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

# --- read back from sample_submission.tif / labels.tif (both identical) -----
WIDTH = 3292
HEIGHT = 3730
SHAPE = (HEIGHT, WIDTH)
CRS = "EPSG:32611"
RESOLUTION_M = 100.0
TRANSFORM = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
BOUNDS = (243350.0, 4135550.0, 572550.0, 4508550.0)  # left, bottom, right, top
N_PIXELS = HEIGHT * WIDTH  # 12,279,160

# --- label semantics (labels.tif is int8 with nodata = -1) ------------------
LABEL_NODATA = -1
CATALOGUE_PIXELS = 60_988  # labels == 1  (USGS Quaternary + INGENIOUS)
FOOTPRINT_PIXELS = 5_167_373  # labels != -1, identical to isfinite(sample_submission)


def data_dir() -> Path:
    """Local (git-ignored) directory holding the restored competition bytes."""
    import os
    env = os.environ.get("GEMS_DATA_DIR", "").strip()
    if env:
        return Path(env)
    root = Path(__file__).resolve().parents[2]
    return root / ".cache" / "gems_data"


@dataclass(frozen=True)
class Template:
    """The submission grid plus the two masks every score depends on."""

    shape: tuple[int, int]
    transform: Affine
    crs: str
    footprint: np.ndarray  # bool, True where a value is expected (finite)
    catalogue: np.ndarray  # bool, True on labels == 1 (masked out of evaluation)

    @property
    def evaluated(self) -> np.ndarray:
        """Pixels that take part in the FP sum: in-footprint and NOT catalogue.

        DrivenData staff (community thread 11516, chrisk-dd, 2026-09-16):
        "Pixels corresponding to known USGS/INGENIOUS faults are masked /
        excluded from evaluation, so they do not count towards penalty terms."
        """
        return self.footprint & ~self.catalogue


def dataset_matches_template_grid(dataset, template: Template, *, atol: float = 1e-9) -> bool:
    """Compare raster dimensions, projected CRS, and affine transform to a template.

    Transform coefficients use an absolute tolerance with zero relative tolerance:
    grid origin/spacing comparisons should not scale with coordinate magnitude.
    """
    if dataset.shape != template.shape or dataset.crs is None:
        return False
    if dataset.crs.to_string() != template.crs:
        return False
    actual = np.asarray(tuple(dataset.transform)[:6], dtype=np.float64)
    expected = np.asarray(tuple(template.transform)[:6], dtype=np.float64)
    return bool(np.allclose(actual, expected, rtol=0.0, atol=atol))


def load_template(data: Path | None = None) -> Template:
    data = Path(data) if data else data_dir()
    with rasterio.open(data / "labels.tif") as src:
        lab = src.read(1)
        tr, crs = src.transform, src.crs
    with rasterio.open(data / "sample_submission.tif") as src:
        ss = src.read(1)
        assert src.transform == tr and str(src.crs) == str(crs), "template mismatch"
    footprint = lab != LABEL_NODATA
    if not np.array_equal(footprint, np.isfinite(ss)):
        raise AssertionError("labels footprint != sample_submission finite mask")
    return Template(shape=lab.shape, transform=tr, crs=str(crs),
                    footprint=footprint, catalogue=lab == 1)


def receipt(data: Path | None = None) -> dict:
    """Machine-readable statement of the grid, for the site and the tests."""
    t = load_template(data)
    return {
        "shape": list(t.shape), "crs": t.crs,
        "transform": list(t.transform)[:6], "bounds_m": list(BOUNDS),
        "resolution_m": RESOLUTION_M, "n_pixels": int(N_PIXELS),
        "footprint_pixels": int(t.footprint.sum()),
        "catalogue_pixels": int(t.catalogue.sum()),
        "evaluated_pixels": int(t.evaluated.sum()),
        "declared_constants_match_bytes": bool(
            t.shape == SHAPE and t.crs == CRS
            and tuple(t.transform)[:6] == tuple(TRANSFORM)[:6]
            and int(t.footprint.sum()) == FOOTPRINT_PIXELS
            and int(t.catalogue.sum()) == CATALOGUE_PIXELS),
    }


if __name__ == "__main__":
    print(json.dumps(receipt(), indent=1))
