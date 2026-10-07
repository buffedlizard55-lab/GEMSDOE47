"""Tests for the H50 additions: the lidar-scarp instrument, the peak detector, the
acquisition-block rank and the read-back contract of the published artifact.

The geometric and algebraic claims are checkable on synthetic arrays; the ones that need the
500 MB competition rasters are marked ``needs_data`` and are skipped in a clean checkout.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import ndimage as ndi

from gems47 import grid as G
from gems47 import h50
from gems47s3.metric import dti

ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------- peaks
def test_lidar_peaks_finds_the_plateau_centre() -> None:
    valid = np.ones((21, 21), bool)
    channel = np.zeros((21, 21), np.float32)
    channel[10, 10] = 255.0
    channel[10, 11] = 255.0          # a 2 px plateau: both are local maxima of the max filter
    peaks = h50.lidar_peaks(channel, valid, 200, 3)
    ys, xs = np.nonzero(peaks)
    assert set(zip(ys.tolist(), xs.tolist())) <= {(10, 10), (10, 11)}


def test_lidar_peaks_respects_the_minimum_separation() -> None:
    valid = np.ones((41, 41), bool)
    channel = np.zeros((41, 41), np.float32)
    for c in (5, 6, 7, 8, 20, 21):
        channel[20, c] = 250.0
    peaks = h50.lidar_peaks(channel, valid, 200, 3)
    ys, xs = np.nonzero(peaks)
    assert len(ys) <= 2, "a 7 px Chebyshev neighbourhood must hold at most one peak"
    if len(ys) == 2:
        d = max(abs(int(ys[0] - ys[1])), abs(int(xs[0] - xs[1])))
        assert d >= 3, "peaks must be at least min_distance apart"


def test_lidar_peaks_ignores_invalid_cells_and_threshold() -> None:
    valid = np.zeros((11, 11), bool)
    channel = np.full((11, 11), 255.0, np.float32)
    assert h50.lidar_peaks(channel, valid, 200, 3).sum() == 0
    valid = np.ones((11, 11), bool)
    lone = np.zeros((11, 11), np.float32)
    lone[5, 5] = 255.0
    assert h50.lidar_peaks(lone, valid, 200, 3).sum() == 1
    assert h50.lidar_peaks(lone, valid, 300, 3).sum() == 0


def test_lidar_peaks_matches_skimage_when_available() -> None:
    """Documented difference against the reference implementation, not an equality claim."""
    pytest.importorskip("skimage")
    from skimage.feature import peak_local_max

    rng = np.random.default_rng(0)
    a = ndi.gaussian_filter(rng.random((80, 80)).astype(np.float32), 1.5) * 255
    valid = np.ones(a.shape, bool)
    mine = h50.lidar_peaks(a, valid, 100, 3)
    pts = peak_local_max(a, min_distance=3, threshold_abs=100, exclude_border=False)
    sk = np.zeros(a.shape, bool)
    sk[pts[:, 0], pts[:, 1]] = True
    assert 0.5 <= mine.sum() / max(sk.sum(), 1) <= 1.0
    assert (mine & sk).sum() >= 0.8 * mine.sum()


# --------------------------------------------------------------- block rank
def test_block_rank_is_bounded_and_monotone() -> None:
    values = np.zeros((6, 6), np.float32)
    values[:, 3:] = 1.0
    blocks = np.zeros((6, 6), np.int32)
    blocks[:3] = 1
    blocks[3:] = 2
    mask = np.ones((6, 6), bool)
    r = h50.block_rank(values, blocks, mask)
    assert r.min() > 0.0 and r.max() == 1.0
    # ranks are distinct inside each block (ties are broken by raster index)
    for block_id in (1, 2):
        sub = np.sort(r[blocks == block_id])
        assert np.all(np.diff(sub) > 0), f"ties inside block {block_id}"
    # within a block the rank must be monotone in the value
    assert (r[:, 3:] > r[:, :3]).all()


def test_block_rank_normalises_within_each_block() -> None:
    """A steep block must not monopolise the top of the ranking."""
    values = np.array([[1.0, 2.0], [3.0, 4.0]], np.float32)
    blocks = np.array([[1, 1], [2, 2]], np.int32)
    mask = np.ones((2, 2), bool)
    r = h50.block_rank(values, blocks, mask)
    # block 1 holds {1, 2} and block 2 holds {3, 4}: each block's own top pixel gets rank 1.0
    assert r[0, 0] == 0.5 and r[0, 1] == 1.0
    assert r[1, 0] == 0.5 and r[1, 1] == 1.0
    assert r[0, 0] == r[1, 0], "each block contributes its own top rank"


def test_block_rank_zero_outside_the_mask() -> None:
    values = np.arange(12, dtype=np.float32).reshape(3, 4)
    blocks = np.ones((3, 4), np.int32)
    mask = np.zeros((3, 4), bool)
    mask[1, 1] = True
    r = h50.block_rank(values, blocks, mask)
    assert r[1, 1] == 1.0 and (r[~mask] == 0).all()


def test_block_rank_rejects_mismatched_shapes() -> None:
    with pytest.raises(ValueError):
        h50.block_rank(np.zeros((3, 3), np.float32), np.ones((2, 2), np.int32),
                       np.ones((3, 3), bool))


# ------------------------------------------------------------------- emission
def test_emit_respects_spacing_and_domain() -> None:
    rng = np.random.default_rng(3)
    field = rng.random((120, 120)).astype(np.float32)
    mask = np.ones((120, 120), bool)
    p = h50.emit(field, mask, 2.8, 500)
    assert p.sum() == 500
    ys, xs = np.nonzero(p)
    d2 = (ys[:, None] - ys[None, :]).astype(np.float64) ** 2
    d2 = d2 + (xs[:, None] - xs[None, :]).astype(np.float64) ** 2
    np.fill_diagonal(d2, np.inf)
    assert d2.min() >= (2.8 ** 2) - 1e-6, "every pair must respect the spacing"


def test_emit_rejects_an_unreachable_budget() -> None:
    field = np.zeros((20, 20), np.float32)
    field[0, 0] = 1.0
    mask = np.ones((20, 20), bool)
    with pytest.raises(ValueError):
        h50.emit(field, mask, 2.8, 50)


def test_emit_keeps_zero_outside_the_mask() -> None:
    rng = np.random.default_rng(4)
    field = rng.random((40, 40)).astype(np.float32)
    mask = np.zeros((40, 40), bool)
    mask[10:30, 10:30] = True
    p = h50.emit(field, mask, 2.8, 30)
    assert (p[~mask] == 0).all() and p.sum() == 30


# ------------------------------------------------------- credit-bar profile
def test_expected_kernel_profile_reports_the_credit_bar() -> None:
    rng = np.random.default_rng(5)
    field = rng.random((200, 200)).astype(np.float32)
    mask = np.ones((200, 200), bool)
    truth = np.zeros((200, 200), bool)
    truth[50:60, 50:60] = True
    rows = h50.expected_kernel_profile(field, mask, truth, (100, 400))
    assert [r["budget"] for r in rows] == [100, 400]
    for r in rows:
        assert r["n_truth"] == 100
        assert r["credit_bar"] == pytest.approx(0.2 * r["dti"])
        assert 0.0 <= r["mean_kernel_weight"] <= 1.0


def test_credit_bar_matches_the_metric_derivation() -> None:
    """A dot with kernel weight above alpha*DTI must raise DTI when added."""
    from gems47s3.metric import credit_bar

    truth = np.zeros((60, 60), bool)
    truth[20:30, 20:30] = True
    base = np.zeros((60, 60), np.float32)
    base[25, 25] = 1.0          # sits inside the truth block, so the DTI is nonzero
    r0 = dti(base, truth.astype(np.int8), valid=np.ones((60, 60), bool))
    bar = credit_bar(r0["dti"])
    # a dot whose kernel weight is above the bar must help
    better = base.copy()
    better[26, 26] = 1.0
    r1 = dti(better, truth.astype(np.int8), valid=np.ones((60, 60), bool))
    assert r1["dti"] > r0["dti"]
    assert 0.0 < bar < 1.0


# ---------------------------------------------------------------- the artifact
@pytest.mark.needs_data
def test_published_h50_nan_outside_artifact_meets_the_local_format_contract() -> None:
    """Read the primary review artifact back and check the mirrored footprint contract."""
    template = G.load_template()
    matches = sorted((ROOT / "docs" / "downloads").glob("gems47-h50-slopeanom-*-nanoutside.tif"))
    if not matches:
        pytest.skip("H50 NaN-outside artifact not built in this checkout")
    path = matches[-1]
    receipt = json.loads((ROOT / "docs" / "data" / "h50-artifact.json").read_text())
    import rasterio
    with rasterio.open(path) as src:
        v = src.read(1)
        assert src.count == 1 and str(src.dtypes[0]) == "float32"
        assert str(src.crs) == "EPSG:32611"
        assert list(src.transform)[:6] == list(template.transform)[:6]
        assert src.nodata is not None and np.isnan(src.nodata)
        assert np.isfinite(v[template.footprint]).all()
        assert np.isnan(v[~template.footprint]).all()
        assert np.all((v[template.footprint] >= 0) & (v[template.footprint] <= 1))
        assert (v[template.catalogue] == 0).all()
        dots = int((v > 0).sum())
    assert dots == receipt["budget"]
    import hashlib
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    assert h == receipt["sha256_tif"], "the published receipt must pin the primary review bytes"


@pytest.mark.needs_data
def test_published_h50_artifact_is_unique_among_prior_rasters() -> None:
    import rasterio
    path = max((ROOT / "docs" / "downloads").glob("gems47-h50-slopeanom-*-nanoutside.tif"))
    with rasterio.open(path) as src:
        pred = np.nan_to_num(src.read(1).astype(np.float32), nan=0.0) > 0
    receipt = json.loads((ROOT / "docs" / "data" / "h50-artifact.json").read_text())
    assert int(pred.sum()) == receipt["budget"]
    assert receipt["uniqueness"]["exact_matches"] == 0
    assert receipt["uniqueness"]["max_jaccard"] < 0.5


def test_h50_historical_publisher_and_page_rewriter_fail_closed() -> None:
    """Retired H50 generators must not overwrite the reviewed status or primary TIFF."""
    for script, expected in (
        ("build_submission_h50.py", "all-finite zero-outside"),
        ("update_site_h50.py", "submission-ready wording"),
    ):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        assert result.returncode == 2, result.stdout + result.stderr
        assert "DISABLED:" in result.stdout
        assert expected in result.stdout
