"""Grid, footprint, catalogue and spatial-fold primitives.

Every array this module returns is on the pinned competition grid
(3730 rows x 3292 cols, EPSG:32611, 100 m, transform (100, 0, 243350, 0, -100, 4508550)).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

from .spec import (BAND_INDEX, FEATURE_INVALID_BELOW, FEATURE_SENTINEL, HEIGHT,
                   LABEL_POSITIVE_PIXELS, PINS, WIDTH)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
STRUCT8 = np.ones((3, 3), bool)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def pin_check(path: Path) -> dict:
    """Verify a restored official file against its pinned byte count and sha256."""
    p = Path(path)
    pin = PINS.get(p.name)
    out = dict(path=str(p), exists=p.exists())
    if not p.exists():
        return out
    out["bytes"] = p.stat().st_size
    out["sha256"] = sha256_file(p)
    if pin:
        out["expected_bytes"] = pin["bytes"]
        out["expected_sha256"] = pin["sha256"]
        out["bytes_match"] = out["bytes"] == pin["bytes"]
        out["sha256_match"] = out["sha256"] == pin["sha256"]
        out["ok"] = bool(out["bytes_match"] and out["sha256_match"])
    return out


class Grid:
    """The competition footprint, the catalogue and the derived working masks."""

    def __init__(self, data_dir: Path = DATA):
        self.data_dir = Path(data_dir)
        sub = self.data_dir / "sample_submission.tif"
        lab = self.data_dir / "labels.tif"
        with rasterio.open(sub) as ds:
            self._assert_grid(ds)
            s = ds.read(1)
            self.submission_nodata = ds.nodata
        self.footprint = np.isfinite(s)                       # 5,167,373 px
        with rasterio.open(lab) as ds:
            self._assert_grid(ds)
            l = ds.read(1)
        self.catalogue = (l == 1)                             # 60,988 px
        assert int(self.catalogue.sum()) == LABEL_POSITIVE_PIXELS
        # The organiser masks catalogue pixels out of evaluation (forum 11516 #2).
        # A prediction may only earn credit on:  footprint AND NOT catalogue.
        self.scored = self.footprint & ~self.catalogue
        self.d_catalogue = ndi.distance_transform_edt(~self.catalogue).astype(np.float32)
        self.shape = (HEIGHT, WIDTH)

    @staticmethod
    def _assert_grid(ds) -> None:
        assert ds.width == WIDTH and ds.height == HEIGHT, f"grid mismatch: {ds.width}x{ds.height}"
        assert ds.crs is not None and ds.crs.to_epsg() == 32611, f"CRS mismatch: {ds.crs}"
        t = tuple(ds.transform)[:6]
        assert t == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0), f"transform mismatch: {t}"

    # ------------------------------------------------------------------ features
    def band(self, name: str) -> np.ndarray:
        """One official feature band as float32 with the sentinel replaced by NaN."""
        with rasterio.open(self.data_dir / "training_features.tif") as ds:
            a = ds.read(BAND_INDEX[name] + 1).astype(np.float32)
        a[~np.isfinite(a)] = np.nan
        a[a < FEATURE_INVALID_BELOW] = np.nan
        return a

    def all_bands_finite(self) -> np.ndarray:
        """Pixels finite in all 19 bands (5,165,840 px), intersected with the footprint."""
        ok = self.footprint.copy()
        with rasterio.open(self.data_dir / "training_features.tif") as ds:
            for i in range(1, ds.count + 1):
                a = ds.read(i)
                ok &= np.isfinite(a) & (a > FEATURE_INVALID_BELOW)
        return ok

    # ------------------------------------------------------------------ catalogue structure
    def catalogue_components(self) -> tuple[np.ndarray, int, np.ndarray]:
        """8-connected components of the catalogue: (labels, n, sizes)."""
        lab, n = ndi.label(self.catalogue, structure=STRUCT8)
        sizes = np.bincount(lab.ravel(), minlength=n + 1)
        return lab, n, sizes

    def spatial_folds(self, n_rows: int = 2, n_cols: int = 2) -> np.ndarray:
        """Contiguous rectangular spatial blocks (fold id per pixel, 0-based).

        Spatial blocking is mandatory here: fault traces are long and connected, so a
        random pixel split leaks the same trace into train and test.
        """
        fid = np.zeros(self.shape, np.int8)
        rh = HEIGHT // n_rows
        cw = WIDTH // n_cols
        k = 0
        for r in range(n_rows):
            for c in range(n_cols):
                y0, y1 = r * rh, (HEIGHT if r == n_rows - 1 else (r + 1) * rh)
                x0, x1 = c * cw, (WIDTH if c == n_cols - 1 else (c + 1) * cw)
                fid[y0:y1, x0:x1] = k
                k += 1
        return fid

    def component_fold_assignment(self, n_rows: int = 2, n_cols: int = 2) -> np.ndarray:
        """Assign each whole catalogue component to one spatial fold (majority block).

        Whole-component assignment is what makes the holdout honest: no part of a held-out
        trace is visible to the detector as "known".
        """
        lab, n, _ = self.catalogue_components()
        fid = self.spatial_folds(n_rows, n_cols)
        comp_fold = np.zeros(n + 1, np.int8)
        for c in range(1, n + 1):
            sel = lab == c
            vals, counts = np.unique(fid[sel], return_counts=True)
            comp_fold[c] = vals[np.argmax(counts)]
        return comp_fold[lab]


def robust_unit(a: np.ndarray, valid: np.ndarray, pct: float = 99.5, clip: float = 6.0) -> np.ndarray:
    """Robust footprint-normalised non-negative score in [0, 1].

    median/IQR z-score computed only on ``valid`` pixels, scaled by the ``pct`` percentile
    and clipped.  NaN outside ``valid``.  Using the IQR rather than the standard deviation
    matters because every geophysical band here is heavy-tailed (see scripts/explore_data.py).
    """
    a = np.asarray(a, np.float32)
    v = valid & np.isfinite(a)
    out = np.full(a.shape, np.nan, np.float32)
    if not v.any():
        return out
    vals = a[v]
    med = float(np.median(vals))
    q25, q75 = np.percentile(vals, [25.0, 75.0])
    scale = max(float(q75 - q25) / 1.349, 1e-9)
    z = (a - med) / scale
    hi = max(float(np.percentile(z[v], pct)), 1e-6)
    out[v] = np.clip(z[v] / hi, 0.0, clip) / clip
    return out
