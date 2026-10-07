"""GeoTIFF writer and local format validator — not a portal oracle.

The published GEMS format page requires null or NaN outside the training-data
bounds, one float32 layer, EPSG:32611, 100 m resolution, matching bounds, and
predictions in [0, 1]. This module checks local bytes against those requirements;
it cannot establish organizer acceptance or explain the earlier rejection.

``mode="nan"`` writes NaN outside the supplied footprint, following the available
owner-supplied mirror convention. That mirror is not organizer authentication.
``mode="zeros"`` writes finite zeros outside the footprint; it is a diagnostic
only and fails the published outside-null/NaN check. Neither sibling-file
behavior nor a local range check proves portal acceptance. The cause of the
previous rejection remains unknown.
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
def write_submission(values: np.ndarray, path: Path, mode: str = "nan",
                     footprint: np.ndarray | None = None) -> dict:
    """Write a single-band float32 GeoTIFF on the pinned grid.  Returns a receipt."""
    a = np.asarray(values, np.float64)
    if a.shape != (HEIGHT, WIDTH):
        raise ValueError(f"expected {(HEIGHT, WIDTH)}, got {a.shape}")
    if footprint is None:
        raise ValueError("an explicit training-footprint mask is required; do not infer bounds from predictions")
    footprint = np.asarray(footprint, dtype=bool)
    if footprint.shape != a.shape:
        raise ValueError(f"footprint shape {footprint.shape} does not match raster {a.shape}")
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
    # Raw NaN outside follows an available mirror convention; this is no claim
    # about portal acceptance. No nodata tag is set.
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

    #: Full-grid finiteness and a nodata-tag heuristic are diagnostics, not published
    #: requirements. Local passes do not establish organizer acceptance.
    INFORMATIONAL = ("all_grid_values_finite_in_unit_interval",
                     "nodata_tag_in_unit_interval_diagnostic")

    @property
    def ok(self) -> bool:
        gating = {k: v for k, v in self.checks.items() if k not in self.INFORMATIONAL}
        return bool(gating) and all(gating.values())

    @property
    def all_grid_values_finite_and_unit_ranged(self) -> bool:
        """Report an optional all-finite diagnostic; not an acceptance guarantee."""
        return bool(self.checks.get("all_grid_values_finite_in_unit_interval"))

    def to_dict(self) -> dict:
        d = dict(path=self.path, sha256=self.sha256, bytes=self.bytes, driver=self.driver,
                 count=self.count, dtype=self.dtype, width=self.width, height=self.height,
                 crs=self.crs, crs_epsg=self.crs_epsg, transform=list(self.transform),
                 nodata=repr(self.nodata), checks=self.checks, stats=self.stats,
                 local_required_checks_passed=self.ok,
                 informational_checks=list(self.INFORMATIONAL),
                 all_grid_values_finite_and_unit_ranged=self.all_grid_values_finite_and_unit_ranged,
                 organizer_acceptance_established=False)
        return d


def validate_submission(path: Path, footprint: np.ndarray | None = None,
                        catalogue: np.ndarray | None = None) -> FormatReceipt:
    """Re-open bytes and check locally verifiable published format requirements.

    A passing receipt is not portal acceptance. Fail closed when an available
    format requirement cannot be verified.
    """
    path = Path(path)
    r = FormatReceipt(path=str(path))
    with rasterio.open(path) as ds:
        a = ds.read(1)
        read_mask = np.ma.getmaskarray(ds.read(1, masked=True))
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
    footprint_supplied = footprint is not None
    fp = finite if footprint is None else np.asarray(footprint, bool)
    if fp.shape != a.shape:
        raise ValueError(f"footprint shape {fp.shape} does not match raster {a.shape}")
    inside = a[fp]
    finite_in = np.isfinite(inside)
    in_range = finite_in & (inside >= 0.0) & (inside <= 1.0)
    try:
        nodata_is_nan = (r.nodata is not None) and bool(np.isnan(r.nodata))
    except TypeError:
        nodata_is_nan = False
    # Diagnostic only: the published page allows null/NaN outside the bounds;
    # it does not document how a portal treats a numeric nodata tag.
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
        in_footprint_zero_inf=bool(np.isinf(inside).sum() == 0),
        in_footprint_zero_sentinel=bool((inside[finite_in] > -1e38).all()) if finite_in.any() else False,
        in_footprint_range_0_1=bool(in_range.all()),
        footprint_supplied=footprint_supplied,
        outside_is_null_or_nan=(
            footprint_supplied and bool((np.isnan(a) | read_mask)[~fp].all())),
        nodata_tag_in_unit_interval_diagnostic=not nodata_bad,
        all_grid_values_finite_in_unit_interval=bool(
            finite.all() and a.size > 0 and (a.min() >= 0.0) and (a.max() <= 1.0)),
        positive_pixels_present=int((a > 0).sum()) > 0,
    )
    if footprint is not None:
        # only checkable when the caller supplies a trusted template footprint
        checks["footprint_matches_template"] = int(fp.sum()) == FOOTPRINT_PIXELS
    r.checks = checks
    return r


def receipt_json(receipt: FormatReceipt, path: Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(receipt.to_dict(), indent=2))
    return p
