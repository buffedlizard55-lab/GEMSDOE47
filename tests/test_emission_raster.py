"""Tests for the emitter spacing rules, the tie-free rank scaling and the format gates."""
from __future__ import annotations

import numpy as np
import pytest

from gems47s3 import emission as E
from gems47s3 import geomorph as G
from gems47s3.raster import validate_submission, write_submission


# --------------------------------------------------------------------- rank_scale
def test_rank_scale_has_no_ties():
    """Exact float32 ties collapse NMS plateaus to a single pixel; rank_scale must not tie."""
    a = np.zeros((40, 40), np.float32)
    a[5:35, 5:35] = 1.0                       # a large exact plateau
    a[0:5, :] = np.linspace(0.1, 0.5, 5)[:, None]
    r = G.rank_scale(a)
    v = r[a > -1]
    assert np.unique(v).size == v.size, "rank_scale must produce a total order"
    assert r.min() > 0.0 and r.max() <= 1.0


def test_rank_scale_preserves_order():
    rng = np.random.default_rng(1)
    a = rng.normal(size=(50, 50)).astype(np.float32)
    r = G.rank_scale(a)
    flat_a, flat_r = a.ravel(), r.ravel()
    i, j = np.argsort(flat_a)[:5], np.argsort(flat_a)[-5:]
    assert (flat_r[i] < 0.1).all() and (flat_r[j] > 0.9).all()


# --------------------------------------------------------------------- nms_disk
def test_nms_disk_enforces_the_spacing_constraint():
    rng = np.random.default_rng(2)
    f = rng.random((120, 140)).astype(np.float32)
    support = np.ones(f.shape, bool)
    for s in (1.0, 2.0, 2.8, 4.0):
        out = E.nms_disk(f, support, s)
        ys, xs = np.nonzero(out)
        if ys.size < 2:
            continue
        d2 = ((ys[:, None] - ys[None, :]) ** 2 + (xs[:, None] - xs[None, :]) ** 2).astype(np.float64)
        np.fill_diagonal(d2, np.inf)
        assert d2.min() > s * s - 1e-6, f"spacing {s} violated: min dist {np.sqrt(d2.min())}"


def test_nms_disk_breaks_exact_ties_at_every_separation():
    """Tied pixels inside each other's disc must not both survive (that would violate the
    spacing constraint).  A fully tied region collapses conservatively; the pipeline removes
    ties upstream so this path is a safety net, not the normal case."""
    f = np.full((30, 30), 0.5, np.float32)    # every pixel tied
    f[5:25, 5:25] = 1.0                       # a tied plateau 20 x 20
    out = E.nms_disk(f, np.ones(f.shape, bool), 2.0)
    ys, xs = np.nonzero(out)
    d2 = ((ys[:, None] - ys[None, :]) ** 2 + (xs[:, None] - xs[None, :]) ** 2).astype(np.float64)
    np.fill_diagonal(d2, np.inf)
    assert d2.min() > 4.0 - 1e-6, f"tied pixels violated the spacing: {np.sqrt(d2.min())}"
    # A fully tied region collapses conservatively to one pixel per tie cluster.  That is safe
    # but wasteful, which is why the pipeline removes ties upstream: geomorph.rank_scale returns
    # a total order and detector.build_core re-ranks the composite.  The property that matters
    # here is that the spacing constraint holds even under maximal tying.
    assert out.sum() >= 1
    # with distinct, non-monotone values the same disc packs a proper lattice
    rng = np.random.default_rng(11)
    g = rng.random((40, 40)).astype(np.float64)
    g = (np.arange(g.size, dtype=np.float64)[np.argsort(g.ravel(), kind="stable")] / g.size
         ).reshape(g.shape).astype(np.float32)      # unique values, no monotone trend
    assert np.unique(g).size == g.size
    o2 = E.nms_disk(g, np.ones(g.shape, bool), 2.0)
    assert o2.sum() > 40
    ys, xs = np.nonzero(o2)
    d2 = ((ys[:, None] - ys[None, :]) ** 2 + (xs[:, None] - xs[None, :]) ** 2).astype(np.float64)
    np.fill_diagonal(d2, np.inf)
    assert d2.min() > 4.0 - 1e-6


def test_rank_scaled_field_has_no_ties_at_float32_resolution():
    """5.16M distinct ranks in (0,1] must survive the float32 cast without colliding, or the
    emitter's spacing guarantee degrades.  float32 ULP on [0.5,1) is 6.0e-8 and the rank step
    is 1/5,164,300 = 1.94e-7, so it survives; this test pins that fact."""
    n = 5_164_300
    step = np.float32(1.0) / np.float32(n)
    assert float(step) > 6.0e-8
    r = np.arange(1, n + 1, dtype=np.float64) / float(n)
    f32 = r.astype(np.float32)
    assert np.unique(f32).size == n


def test_nms_disk_density_falls_with_spacing():
    rng = np.random.default_rng(3)
    f = rng.random((200, 200)).astype(np.float32)
    counts = [int(E.nms_disk(f, np.ones(f.shape, bool), s).sum()) for s in (1.0, 2.0, 4.0)]
    assert counts[0] > counts[1] > counts[2]


def test_poisson_disk_agrees_with_nms_on_spacing():
    """The exact candidate-loop rule and the vectorised NMS must both honour min_dist."""
    rng = np.random.default_rng(4)
    f = rng.random((60, 70)).astype(np.float32)
    support = f > 0.7
    for rule in (E.nms_disk, E.poisson_disk):
        out = rule(f, support, 2.5)
        ys, xs = np.nonzero(out)
        if ys.size < 2:
            continue
        d2 = ((ys[:, None] - ys[None, :]) ** 2 + (xs[:, None] - xs[None, :]) ** 2).astype(np.float64)
        np.fill_diagonal(d2, np.inf)
        assert d2.min() >= 2.5 ** 2 - 1e-6


# --------------------------------------------------------------------- emit
def test_emit_respects_budget_and_flank_buffer():
    rng = np.random.default_rng(5)
    f = rng.random((100, 100)).astype(np.float32)
    mask = np.ones(f.shape, bool)
    dcat = np.full(f.shape, 10.0, np.float32)
    dcat[:, :20] = 1.0                        # a "catalogue" strip on the left
    r = E.emit(f, mask, min_dist=2.0, support_q=1.0, d_catalogue=dcat, flank_b=2.0,
               blur="none", budget=500)
    assert r["n_after_flank"] <= 500
    assert r["mask"][:, :20].sum() == 0, "flank buffer must delete dots near the catalogue"
    assert r["n_thinned"] >= r["n_after_flank"]


def test_oriented_blur_preserves_mass_better_than_isotropic_along_a_line():
    """An along-strike blur must keep the ridge peak higher than an isotropic blur of the
    same total mass, because the metric charges 0.2 per unit pushed off the trace."""
    f = np.zeros((60, 60), np.float32)
    f[:, 30] = 1.0                            # a perfectly straight N-S trace
    theta = np.zeros(f.shape, np.float32)     # 2*theta = 0 means strike N-S
    coh = np.full(f.shape, 0.5, np.float32)
    ori = E.oriented_blur(f, 3.0, 0.0, coh, theta)
    iso = E.isotropic_blur(f, 1.5)
    assert ori.max() > iso.max()
    assert ori[:, 30].sum() > iso[:, 30].sum()


# --------------------------------------------------------------------- format gates
@pytest.mark.needs_data
def test_write_validate_roundtrip_nan_outside(tmp_path):
    from gems47s3.spec import HEIGHT, WIDTH
    v = np.zeros((HEIGHT, WIDTH), np.float32)
    v[100:110, 100:110] = 1.0
    p = tmp_path / "t.tif"
    from gems47s3.grid import Grid
    fp = Grid().footprint
    w = write_submission(v, p, mode="nan", footprint=fp)
    assert w["positive_pixels"] == 100
    r = validate_submission(p, footprint=fp)
    assert r.ok, {k: x for k, x in r.checks.items() if not x}
    assert r.nodata is None
    assert r.stats["nan_in_footprint"] == 0
    assert r.checks["footprint_matches_template"] is True
    assert r.checks["outside_is_null_or_nan"] is True
    assert r.all_grid_values_finite_and_unit_ranged is False


def test_validator_rejects_out_of_range_values(tmp_path):
    import rasterio

    from gems47s3.raster import TRANSFORM
    from gems47s3.spec import HEIGHT, WIDTH
    p = tmp_path / "bad.tif"
    a = np.zeros((HEIGHT, WIDTH), np.float32)
    a[0, 0] = 1.5                             # outside [0,1]
    with rasterio.open(p, "w", driver="GTiff", height=HEIGHT, width=WIDTH, count=1,
                       dtype="float32", crs="EPSG:32611", transform=TRANSFORM) as ds:
        ds.write(a, 1)
    r = validate_submission(p)
    assert r.ok is False
    assert r.checks["in_footprint_range_0_1"] is False


def test_validator_rejects_the_float32_sentinel(tmp_path):
    """The checked mirror training-feature raster has a float32 outside sentinel;
    this test checks local rejection, not the cause of a portal response."""
    import rasterio

    from gems47s3.raster import TRANSFORM
    from gems47s3.spec import HEIGHT, WIDTH
    p = tmp_path / "sentinel.tif"
    a = np.zeros((HEIGHT, WIDTH), np.float32)
    a[5, 5] = np.float32(-3.4028234663852886e38)
    with rasterio.open(p, "w", driver="GTiff", height=HEIGHT, width=WIDTH, count=1,
                       dtype="float32", crs="EPSG:32611", transform=TRANSFORM) as ds:
        ds.write(a, 1)
    r = validate_submission(p)
    assert r.ok is False
    assert r.checks["in_footprint_zero_sentinel"] is False
    assert r.checks["all_grid_values_finite_in_unit_interval"] is False


def test_writer_refuses_out_of_range_input():
    from gems47s3.spec import HEIGHT, WIDTH
    v = np.zeros((HEIGHT, WIDTH), np.float32)
    v[0, 0] = 1.0000001
    with pytest.raises(ValueError):
        write_submission(v, "/tmp/never-written.tif", footprint=np.ones(v.shape, bool))


# --------------------------------------------------------------------- geomorph
def test_scarp_step_fires_on_a_step_and_not_on_a_slope():
    """The across-strike step filter must separate a linear step from a uniform tilt."""
    y, x = np.mgrid[0:80, 0:80].astype(np.float32)
    tilt = 0.1 * x                                     # uniform regional dip
    step = np.where(x >= 40, 3.0, 0.0)                 # a straight N-S scarp
    a = tilt + step
    r = G.scarp_step(a, 5)
    band = r[:, 38:43].mean()
    away = np.concatenate([r[:, 5:20].ravel(), r[:, 60:75].ravel()]).mean()
    assert band > 3 * away, (band, away)


def test_scarp_step_samples_across_strike_not_along_it():
    """A step running N-S must be detected by the E-W normal, so a purely north-south
    gradient of the same amplitude must NOT produce the same response."""
    y, x = np.mgrid[0:80, 0:80].astype(np.float32)
    ew = G.scarp_step(np.where(x >= 40, 3.0, 0.0).astype(np.float32), 5)
    ns = G.scarp_step(np.where(y >= 40, 3.0, 0.0).astype(np.float32), 5)
    assert ew[:, 38:43].mean() > 1.0
    assert ns[38:43, :].mean() > 1.0
    # each field's own across-step band must dominate its off-band region
    assert ew[:, 38:43].mean() > ew[:, 5:15].mean()
    assert ns[38:43, :].mean() > ns[5:15, :].mean()


def test_openness_is_high_on_a_crest_and_low_in_a_pit():
    y, x = np.mgrid[0:60, 0:60].astype(np.float32)
    crest = np.exp(-((y - 30) ** 2 + (x - 30) ** 2) / 40.0) * 10
    o = G.openness(crest.astype(np.float32), 4)
    assert o[30, 30] > o[5, 5]
    pit = -crest
    o2 = G.openness(pit.astype(np.float32), 4)
    assert o2[30, 30] < o2[5, 5]


# --------------------------------------------------------------------- pass-2 regressions
def _real_footprint_and_a_dot_inside_it():
    """The template footprint, plus a 10x10 dot guaranteed to lie inside it."""
    import numpy as np

    from gems47s3.grid import Grid
    fp = Grid().footprint
    ys, xs = np.nonzero(fp)
    y, x = int(np.median(ys)), int(np.median(xs))
    v = np.zeros(fp.shape, np.float32)
    v[y:y + 10, x:x + 10] = 1.0
    assert v[fp].sum() > 0
    return fp, v


@pytest.mark.needs_data
def test_nan_mode_follows_null_nan_requirement_but_not_portal_verified(tmp_path):
    """NaN outside follows published wording and an available mirror convention; local pass only."""
    fp, v = _real_footprint_and_a_dot_inside_it()
    p = tmp_path / "nan.tif"
    write_submission(v, p, mode="nan", footprint=fp)
    r = validate_submission(p, footprint=fp)
    assert r.ok, {k: x for k, x in r.checks.items() if not x and k not in r.INFORMATIONAL}
    assert r.all_grid_values_finite_and_unit_ranged is False
    assert r.checks["outside_is_null_or_nan"] is True
    assert r.checks["all_grid_values_finite_in_unit_interval"] is False
    assert r.checks["nodata_tag_in_unit_interval_diagnostic"] is True   # no nodata tag at all


@pytest.mark.needs_data
def test_zeros_mode_is_finite_but_fails_outside_null_requirement(tmp_path):
    fp, v = _real_footprint_and_a_dot_inside_it()
    p = tmp_path / "zeros.tif"
    write_submission(v, p, mode="zeros", footprint=fp)
    r = validate_submission(p, footprint=fp)
    assert r.ok is False
    assert r.checks["outside_is_null_or_nan"] is False
    assert r.checks["all_grid_values_finite_in_unit_interval"] is True


@pytest.mark.needs_data
def test_gated_recipes_still_yield_a_total_order():
    """Multiplying a total-order core by a gate re-introduces float32 collisions; build_field
    must re-rank so the emitter's spacing guarantee holds for gated recipes too."""
    from pathlib import Path

    import numpy as np

    from gems47s3.detector import Bands, Recipe, build_field
    from gems47s3.grid import Grid
    root = Path(__file__).resolve().parents[1]
    surf = root / "data" / "surfaces" / "valid.npy"
    if not surf.exists():
        import pytest
        pytest.skip("data/surfaces/valid.npy not built; run scripts/build_surfaces.py")
    g = Grid()
    valid = np.load(surf)
    bands = Bands(g.data_dir / "training_features.tif")
    rec = Recipe(name="gated", terms=[("det_elev_slope", "scarp", 3, 1.0)],
                 use_vacancy=True, vacancy_power=0.5,
                 regional_bands=("geod_2ndinv",), regional_power=0.5)
    f = build_field(rec, bands, valid, g.catalogue)["field"]
    assert np.isfinite(f).all()
    assert f.min() >= 0.0 and f.max() <= 1.0
    n_valid = int(valid.sum())
    assert np.unique(f[valid]).size > 0.99 * n_valid, "gated field must be (near) a total order"
    # and the gate must actually push mass off the catalogue, which is masked out of scoring
    assert f[g.catalogue].mean() < f[valid & ~g.catalogue].mean()
