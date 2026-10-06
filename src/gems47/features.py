"""Feature stack for the hidden-new-fault intensity model.

Every layer is reduced to a *rank percentile* (uint8, 0..255) over the evaluated
pixel set, which makes the inversion scale-free and immune to the float32-min
nodata sentinel (-3.4028234663852886e+38) that ``np.isfinite`` does NOT catch
(flagged as IR-47-001).

Features are produced by a *streaming* generator and rank-quantised one at a
time, so peak memory stays at roughly one full-grid float32 layer (~49 MB)
instead of one per feature.

Provenance of every input layer is recorded in ``registry/sources.json``.
"""

from __future__ import annotations

import csv
import json
import time
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

from . import grid as G

SENTINEL = -1e30  # anything below this is the float32-min nodata sentinel

# 19 official GeoDAWN bands, in file order (read back from the TIFF descriptions)
TRAINING_BANDS = [
    "mag_anom", "rtp", "tmi_hg", "geod_2ndinv", "iso_grav_anom_slope", "tc",
    "geod_shearrate", "geod_dilaterate", "tmi_vg", "deq_n100a15", "iso_grav_anom_vg",
    "det_elev", "iso_grav_anom", "tmi", "depth_to_base_surf", "ieq_n100a15",
    "cond_surf", "iso_grav_anom_hg", "det_elev_slope",
]
LIDAR_BANDS = ["ex_max", "ex_mean", "step_max", "lapneg_max", "lappos_max",
               "downface_max", "upface_max", "cross_max", "relief", "coh100",
               "strike", "valid"]
RAD_BANDS = ["rad_K", "rad_Th", "rad_U", "rad_TC"]
EXT_BANDS = ["rad_ThK", "rad_UK", "rad_UTh", "tmi_up150"]
GRAD_OF = ("det_elev", "iso_grav_anom", "tmi", "rtp", "cond_surf", "depth_to_base_surf")


def dist_px(mask: np.ndarray, cap: float = 80.0) -> np.ndarray:
    """Euclidean distance in pixels to the nearest True pixel of ``mask`` (capped)."""
    if not mask.any():
        return np.full(mask.shape, cap, np.float32)
    return np.clip(ndimage.distance_transform_edt(~mask), 0, cap).astype(np.float32)


def rank_u8(v: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """Rank percentile (0..255, ties averaged) of ``v.ravel()[idx]``."""
    x = v.ravel()[idx]
    order = np.argsort(x, kind="stable")
    r = np.empty(x.size, np.float64)
    r[order] = np.arange(x.size, dtype=np.float64)
    sx = x[order]
    i = 0
    n = sx.size
    while i < n:
        j = i + 1
        while j < n and sx[j] == sx[i]:
            j += 1
        if j - i > 1:
            r[order[i:j]] = 0.5 * (i + j - 1)
        i = j
    return np.clip(np.rint(r / max(n - 1, 1) * 255.0), 0, 255).astype(np.uint8)


def _layers(data: Path, ev: np.ndarray, shape: tuple[int, int]) -> Iterator[tuple[str, np.ndarray]]:
    """Yield (name, full-grid float32 layer).  Higher value == more fault-like."""
    H, W = shape
    with rasterio.open(data / "training_features.tif") as src:
        for b, name in enumerate(TRAINING_BANDS, start=1):
            v = src.read(b).astype(np.float32)
            v[~(ev & (v > SENTINEL))] = 0.0
            yield name, v
            if name in GRAD_OF:
                gy, gx = np.gradient(v.astype(np.float32))
                yield name + "_grad", np.hypot(gy, gx).astype(np.float32)

    with rasterio.open(data / "external" / "lidar_scarp_features_u8.tif") as src:
        lid = src.read().astype(np.float32)
    for i, name in enumerate(LIDAR_BANDS):
        yield "lidar_" + name, lid[i]
    keys = ("ex_max", "step_max", "lapneg_max", "downface_max", "cross_max", "relief")
    morph = np.stack([lid[LIDAR_BANDS.index(k)] for k in keys])
    yield "lidar_scarp_composite", morph.mean(axis=0).astype(np.float32)
    yield "lidar_scarp_max", morph.max(axis=0).astype(np.float32)
    del lid, morph

    with rasterio.open(data / "external" / "geodawn_rad_u8.tif") as src:
        rad = src.read().astype(np.float32)
    for i, name in enumerate(RAD_BANDS):
        yield name, rad[i]
    del rad
    with rasterio.open(data / "external" / "geodawn_extensions_u8.tif") as src:
        ext = src.read().astype(np.float32)
    for i, name in enumerate(EXT_BANDS):
        yield name, ext[i]
    del ext

    with rasterio.open(data / "external" / "derived_sgmc_faults_100m_u8.tif") as src:
        sgmc = (src.read(1) > 0) & ev
    yield "sgmc_offcat", sgmc.astype(np.float32)
    yield "sgmc_offcat_prox", -dist_px(sgmc, 40.0)
    del sgmc

    cat = np.zeros((H, W), bool)  # filled by caller? no - recompute from labels
    with rasterio.open(data / "labels.tif") as src:
        cat = src.read(1) == 1
    d_cat = dist_px(cat, 80.0)
    yield "d_catalogue_prox", -d_cat
    for lo, hi in [(0.0, 1.5), (1.5, 3.0), (3.0, 6.0), (6.0, 12.0), (12.0, 25.0), (25.0, 1e9)]:
        yield (f"dcat_band_{lo:g}_{hi:g}",
               ((d_cat > lo) & (d_cat <= hi)).astype(np.float32))
    del cat, d_cat

    hot = np.zeros((H, W), bool)
    warm = np.zeros((H, W), bool)
    with open(data / "external" / "gdr_wellspring_in_footprint.csv") as fh:
        for row in csv.DictReader(fh):
            try:
                r, c = int(row["row"]), int(row["col"])
            except (ValueError, KeyError, TypeError):
                continue
            if 0 <= r < H and 0 <= c < W:
                warm[r, c] = True
                if (row.get("thermalclass") or "") == "Hot":
                    hot[r, c] = True
    vents = np.zeros((H, W), bool)
    with open(data / "external" / "gdr_volcanic_vents_in_footprint.csv") as fh:
        for row in csv.DictReader(fh):
            try:
                r, c = int(row["row"]), int(row["col"])
            except (ValueError, KeyError, TypeError):
                continue
            if 0 <= r < H and 0 <= c < W:
                vents[r, c] = True
    yield "thermal_hot_prox", -dist_px(hot & ev, 60.0)
    yield "thermal_warm_prox", -dist_px(warm & ev, 60.0)
    yield "vent_prox", -dist_px(vents & ev, 60.0)


def build_stack(data: Path | None = None, out: Path | None = None,
                verbose: bool = True) -> dict:
    """Build (and optionally cache) the rank-quantised feature matrix.

    Returns ``{"names": [...], "U": (n_feat, n_eval) uint8, "ev_idx": int64[...],
               "shape": (H, W), "meta": {...}}``.
    """
    data = Path(data) if data else G.data_dir()
    out = Path(out) if out else (Path(__file__).resolve().parents[2] / ".cache" / "featstack.npz")
    t = G.load_template(data)
    ev = t.evaluated
    ev_idx = np.flatnonzero(ev.ravel())

    side = out.with_suffix(".json")
    if out.exists() and side.exists():
        z = np.load(out, allow_pickle=False)
        m = json.loads(side.read_text())
        if z["ev_idx"].size == ev_idx.size and np.array_equal(z["ev_idx"], ev_idx):
            if verbose:
                print(f"[features] cache hit {out} ({z['U'].shape})")
            return {"names": m["names"], "U": z["U"], "ev_idx": ev_idx,
                    "shape": t.shape, "meta": m}

    t0 = time.time()
    names: list[str] = []
    rows: list[np.ndarray] = []
    for name, layer in _layers(data, ev, t.shape):
        names.append(name)
        rows.append(rank_u8(layer, ev_idx))
        if verbose:
            print(f"[features] {len(names):>3} {name:<26} {time.time()-t0:6.1f}s", flush=True)
        del layer
    U = np.stack(rows)
    del rows
    meta = {"n_eval": int(ev_idx.size), "shape": list(t.shape), "n_features": len(names),
            "names": names, "seconds": round(time.time() - t0, 1), "bytes": int(U.nbytes),
            "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, U=U, ev_idx=ev_idx)
    side.write_text(json.dumps(meta, indent=1))
    return {"names": names, "U": U, "ev_idx": ev_idx, "shape": t.shape, "meta": meta}


if __name__ == "__main__":
    st = build_stack()
    print(json.dumps(st["meta"], indent=1))
    print("U MB:", round(st["U"].nbytes / 1e6, 1))
