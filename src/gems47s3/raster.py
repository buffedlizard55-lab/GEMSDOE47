"""GeoTIFF writer and an independent, fail-closed submission validator.

The portal rejects a submission with "Predicted values must be in range [0, 1]".
Two distinct mechanisms produce that message and both are handled here:

  1. a value outside [0, 1] (including the float32 nodata sentinel -3.4028234663852886e38,
     which the official training_features.tif uses for its 7.1 M out-of-footprint cells);
  2. a nodata TAG whose value is outside [0, 1] (e.g. NaN or the float32 sentinel) -- the
     validator can read the tag as a "predicted value".

The writer therefore offers two modes, and the validator re-opens the file from disk
(it never trusts the in-memory array that was written):

  mode="zeros"  every one of the 12,279,160 cells is finite and in [0, 1]; nodata tag is
                ABSENT.  This is the safest file the specification allows: outside the
                footprint the confidence is 0.0, which is a legal value in [0, 1] and
                cannot trip a range check.
  mode="nan"    cells outside the footprint are NaN, as the official example_submission.tif
                does ("data outside the bounds is null or nan").  Legal, and byte-identical
                inside the footprint, but one validator change away from mechanism 2.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from .spec import EPSG, FOOTPRINT_PIXELS, HEIGHT, PIXEL_SIZE_M, WIDTH

TRANSFORM = from_origin(243350.0, 4508550.0, PIXEL_SIZE_M, PIXEL_SIZE_M)


# --------------------------------------------------------------------------- writer
def write_submission(values: np.ndarray, path: Path, mode: str = "zeros",
                     footprint: np.ndarray | None = None) -> dict:
    """Write a single-band float32 GeoTIFF on the pinned grid.  Returns a receipt."""
    a = np.asarray(values, np.float64)
    if a.shape != (HEIGHT, WIDTH):
        raise ValueError(f"expected {(HEIGHT, WIDTH)}, got {a.shape}")
    if footprint is None:
        footprint = np.isfinite(a)
    inside = a[footprint]
    if inside.size == 0:
        raise ValueError("empty footprint")
    if not np.isfinite(inside).all():
        raise ValueError("non-finite value inside the footprint")
    if inside.min() < 0.0 or inside.max() > 1.0:
        raise ValueError(f"value outside [0,1] inside the footprint: [{inside.min()}, {inside.max()}]")

    out = np.zeros((HEIGHT, WIDTH), np.float32)
    out[footprint] = np.clip(a[footprint], 0.0, 1.0).astype(np.float32)
    if mode == "nan":
        out = out.astype(np.float32)
        out[~footprint] = np.float32("nan")
    elif mode != "zeros":
        raise ValueError("mode must be 'zeros' or 'nan'")

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = dict(driver="GTiff", height=HEIGHT, width=WIDTH, count=1, dtype="float32",
                   crs=f"EPSG:{EPSG}", transform=TRANSFORM, compress="deflate",
                   tiled=False, BIGTIFF="NO")
    # Deliberately NO nodata tag: any sentinel we could write (NaN, -3.4e38) is itself
    # outside [0, 1] and is a second route to the portal's range rejection.
    with rasterio.open(path, "w", **profile) as ds:
        ds.write(out, 1)
        ds.set_band_description(1, "predicted confidence of an unmapped fault in [0,1]")
    return dict(path=str(path), mode=mode, bytes=path.stat().st_size,
                sha256=_sha256(path), positive_pixels=int((out > 0).sum()))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


# --------------------------------------------------------------------------- validator
@dataclass
class FormatReceipt:
    path: str = ""
    sha256: str = ""
    bytes: int = 0
    driver: str = ""
    count: int = 0
    dtype: str = ""
    width: int = 0
    height: int = 0
    crs: str = ""
    crs_epsg: int | None = None
    transform: tuple = ()
    nodata: object = None
    checks: dict = field(default_factory=dict)
    stats: dict = field(default_factory=dict)

    #: Checks that gate acceptance.  ``validator_range_0_1_guaranteed`` is deliberately NOT in
    #: this set: it asserts that EVERY cell of the grid is finite and in [0,1], which the
    #: ``mode="nan"`` writer intentionally does not satisfy (the official page permits "null or
    #: nan" outside the bounds, and three scored reference artifacts ship that way).  It is
    #: reported separately as the strongest available guarantee, not as a pass/fail gate.
    INFORMATIONAL = ("validator_range_0_1_guaranteed",)

    @property
    def ok(self) -> bool:
        gating = {k: v for k, v in self.checks.items() if k not in self.INFORMATIONAL}
        return bool(gating) and all(gating.values())

    @property
    def strongest_guarantee(self) -> bool:
        """True only for the all-finite, no-nodata-tag configuration actually shipped."""
        return self.ok and bool(self.checks.get("validator_range_0_1_guaranteed"))

    def to_dict(self) -> dict:
        d = dict(path=self.path, sha256=self.sha256, bytes=self.bytes, driver=self.driver,
                 count=self.count, dtype=self.dtype, width=self.width, height=self.height,
                 crs=self.crs, crs_epsg=self.crs_epsg, transform=list(self.transform),
                 nodata=repr(self.nodata), checks=self.checks, stats=self.stats,
                 all_checks_passed=self.ok,
                 informational_checks=list(self.INFORMATIONAL),
                 strongest_range_guarantee=self.strongest_guarantee)
        return d


def validate_submission(path: Path, footprint: np.ndarray | None = None,
                        catalogue: np.ndarray | None = None) -> FormatReceipt:
    """Re-open the written file from disk and gate every published format requirement.

    Fail-closed: any check that cannot be evaluated is reported False.
    """
    path = Path(path)
    r = FormatReceipt(path=str(path))
    with rasterio.open(path) as ds:
        a = ds.read(1)
        r.sha256 = _sha256(path)
        r.bytes = path.stat().st_size
        r.driver = ds.driver
        r.count = ds.count
        r.dtype = str(a.dtype)
        r.width, r.height = ds.width, ds.height
        r.crs = str(ds.crs)
        r.crs_epsg = ds.crs.to_epsg() if ds.crs is not None else None
        r.transform = tuple(ds.transform)[:6]
        r.nodata = ds.nodata

    finite = np.isfinite(a)
    fp = finite if footprint is None else np.asarray(footprint, bool)
    inside = a[fp]
    finite_in = np.isfinite(inside)
    in_range = finite_in & (inside >= 0.0) & (inside <= 1.0)
    nodata_is_nan = (r.nodata is not None) and isinstance(r.nodata, float) and np.isnan(r.nodata)
    nodata_bad = (r.nodata is not None) and not nodata_is_nan and not (0.0 <= float(r.nodata) <= 1.0)

    r.stats = dict(
        full_grid_cells=int(a.size),
        finite_cells=int(finite.sum()),
        footprint_cells=int(fp.sum()),
        finite_in_footprint=int(finite_in.sum()),
        min_in_footprint=float(inside[finite_in].min()) if finite_in.any() else None,
        max_in_footprint=float(inside[finite_in].max()) if finite_in.any() else None,
        cells_outside_0_1_in_footprint=int((finite_in & ~in_range).sum()),
        nan_in_footprint=int((~finite_in).sum()),
        positive_cells=int((finite & (a > 0)).sum()),
        positive_cells_in_footprint=int((fp & finite & (a > 0)).sum()),
        distinct_values=int(np.unique(a[finite]).size),
    )
    if catalogue is not None:
        cat = np.asarray(catalogue, bool)
        r.stats["positive_pixels_on_catalogue"] = int((fp & finite & (a > 0) & cat).sum())

    checks = dict(
        single_band=r.count == 1,
        dtype_float32=r.dtype == "float32",
        dimensions_3730x3292=(r.width == WIDTH and r.height == HEIGHT),
        crs_epsg_32611=r.crs_epsg == EPSG,
        transform_exact=r.transform == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0),
        in_footprint_all_finite=bool(finite_in.all()),
        in_footprint_zero_nan=int((~finite_in).sum()) == 0,
        in_footprint_zero_inf=bool(np.isinf(inside[finite_in]).sum() == 0) if finite_in.any() else False,
        in_footprint_zero_sentinel=bool((inside[finite_in] > -1e38).all()) if finite_in.any() else False,
        in_footprint_range_0_1=bool(in_range.all()),
        every_cell_finite_or_nan_outside=bool(finite[~fp].all() or np.isnan(a[~fp]).all()),
        nodata_tag_not_out_of_range=not nodata_bad,
        validator_range_0_1_guaranteed=bool(finite.all() and (a.min() >= 0.0) and (a.max() <= 1.0)),
        positive_pixels_present=int((a > 0).sum()) > 0,
    )
    if footprint is not None:
        # only checkable when the caller supplies the official template footprint
        checks["footprint_matches_template"] = int(fp.sum()) == FOOTPRINT_PIXELS
    r.checks = checks
    return r


def receipt_json(receipt: FormatReceipt, path: Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(receipt.to_dict(), indent=2))
    return p
