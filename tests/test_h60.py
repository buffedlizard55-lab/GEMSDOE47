"""H60 round contracts: frozen definitions, emission invariants and the screen receipt.

The heavy pieces (the 41-block screen, the artifact build) have their own scripts;
these tests pin the invariants that must never silently change: the frozen channel
list, the noise-mask radii, the budget/spacing contracts of the trace emitter, the
largest-remainder allocation law, and the frozen verdicts in the published screen
receipt.  Tests that read the 500 MB rasters are marked ``needs_data``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from gems47 import h60


# ------------------------------------------------------------------ frozen definitions
def test_h60_channels_and_mask_radii_are_frozen() -> None:
    assert set(h60.H60_CHANNELS) == {"step_max", "lappos_max", "lapneg_max",
                                     "upface_max", "downface_max", "cross_max"}
    assert h60.ROAD_MASK_M == 250.0
    assert h60.CLAIM_MASK_M == 150.0


def test_preregistration_is_committed_and_covers_the_slate() -> None:
    path = ROOT / "docs" / "research" / "h60-hypotheses-preregistered.md"
    assert path.is_file(), "the preregistered slate must be published"
    text = path.read_text(encoding="utf-8")
    for token in ("H60", "H61", "H62", "H63", "H64", "250 m", "150 m", "37,654",
                  "gate", "lappos_t200_d3"):
        assert token in text, token


# ------------------------------------------------------------------ emitter invariants
def test_greedy_up_to_never_exceeds_the_requested_cap() -> None:
    """The feasibility cap must return a feasible selection, not raise, not exceed."""
    rng = np.random.default_rng(0)
    f = rng.random((40, 40)).astype(np.float32)
    order = np.argsort(f, axis=None)[::-1]
    for spacing, cap in ((2.0, 294), (2.8, 1400), (4.6, 50)):
        sel = h60._greedy_up_to(order, f.shape, spacing, cap)
        assert 0 < len(sel) <= cap
        if len(sel) < cap:
            # smaller caps must not return more dots than larger caps
            sel_small = h60._greedy_up_to(order, f.shape, spacing, max(len(sel) - 1, 1))
            assert len(sel_small) <= len(sel)


def test_greedy_up_to_respects_the_minimum_separation() -> None:
    rng = np.random.default_rng(1)
    f = rng.random((60, 60)).astype(np.float32)
    order = np.argsort(f, axis=None)[::-1]
    sel = h60._greedy_up_to(order, f.shape, 2.8, 200)
    pts = np.array(np.unravel_index(sel, f.shape)).T.astype(float)
    d = np.linalg.norm(pts[:, None, :] - pts[None, :, :], axis=-1)
    d[d == 0] = np.inf
    assert d.min() >= 2.8 - 1e-9


def test_emit_trace_meets_the_block_budget_exactly() -> None:
    """sum(alloc) == budget always; the emitted mask realises the budget.

    The domain must be able to hold the budget at the spacing (true for every real
    block; a starved synthetic domain would legitimately under-emit).
    """
    rng = np.random.default_rng(2)
    f = rng.random((300, 300)).astype(np.float32)
    valid = np.ones((300, 300), bool)
    thr = float(np.quantile(f, 0.9))
    for budget in (294, 1400):
        p = h60.emit_trace(f, valid, 2.8, budget, thr)
        assert int(p.sum()) == budget, "the trace emitter must meet the budget exactly"


def test_emit_trace_is_deterministic() -> None:
    rng = np.random.default_rng(3)
    f = rng.random((300, 300)).astype(np.float32)
    valid = np.ones((300, 300), bool)
    thr = float(np.quantile(f, 0.9))
    a = h60.emit_trace(f, valid, 2.0, 500, thr)
    b = h60.emit_trace(f, valid, 2.0, 500, thr)
    assert np.array_equal(a, b)


# ------------------------------------------------------------------ screen receipt
def test_screen_receipt_freezes_the_gate_verdicts() -> None:
    screen = json.loads((ROOT / "evidence" / "h60" / "screen.json").read_text())
    gate = screen["gate"]["per_arm"]
    assert gate["h60"]["passed"] is True
    assert gate["h62"]["passed"] is True      # passed, lost the sgmc tie-break
    assert gate["h61"]["passed"] is False     # per-trace reallocation refuted
    assert gate["h63"]["passed"] is False     # catalogue-adjacency gate refuted
    assert screen["gate"]["winner"] == "h60"
    assert screen["gate"]["passing_arms"] == ["h60", "h62"]
    # the anchor reproduced bit-for-bit: the frozen H50 design was re-instantiated
    assert screen["anchor_reproduction"]["matches"] is True
    assert screen["anchor_reproduction"]["measured"] == 0.16588059959214113
    # the promotion is over the preregistered 1.10x bar
    h50 = screen["arms"]["h50"]["pooled_primary_selection"]
    h60sel = screen["arms"]["h60"]["pooled_primary_selection"]
    assert h60sel >= 1.10 * h50
    # independent corroboration: the sgmc gain over random exceeds 2x
    assert screen["arms"]["h60"]["pooled_sgmc_selection"] >= \
        2 * screen["controls"]["h60"]["random"]["sgmc"]
    # the H61 min-1 deviation is recorded, not hidden
    assert any("emitted_mass_selection_half" in k or "correction" in str(k).lower()
               for k in screen.get("corrections", ["recorded"]))
    assert screen["arms"]["h60"]["emitted_mass_selection_half"] < 21198, \
        "the noise-masked domain caps capacity below the 21,198-dot selection budget"


def test_screen_receipt_carries_the_block_design() -> None:
    import csv
    rows = list(csv.DictReader((ROOT / "evidence" / "h60" / "spacing-history.csv").open()))
    assert rows, "the spacing history must be published"
    blocks = {(r["block_id"], r["role"]) for r in rows}
    assert len({b for b, _ in blocks}) == 41, "the frozen design has 41 blocks"
    assert {role for _, role in blocks} == {"selection", "calibration"}
    for r in rows:
        assert 0.0 <= float(r["DTI"]) <= 1.0
        assert int(float(r["emitted"])) >= 0


def test_instrument_refinement_supports_the_mask_design() -> None:
    ref = json.loads((ROOT / "evidence" / "h60" / "instrument-refinement.json").read_text())
    rows = ref["rows"]
    # far-from-catalogue peaks correlate better than near ones (why H63 failed)
    assert rows["lappos_t200_d3_far"]["spearman"] > rows["lappos_t200_d3_near"]["spearman"]
    # the noise masks do not destroy the instrument-leaderboard correlation
    for name in ("lappos_t200_d3", "lapneg_t200_d3", "step_t150_d3"):
        assert rows[f"{name}_roadok"]["spearman"] > 0.4, name
    # every scored row carries the permutation reference
    for name, row in rows.items():
        if row.get("skipped"):
            continue
        assert row["permutation_draws"] == 20000
        assert 0.0 <= row["permutation_p_two_sided"] <= 1.0


@pytest.mark.needs_data
def test_h60_emission_domain_respects_masks_and_catalogue() -> None:
    from gems47 import grid as G
    data = G.data_dir()
    grids = h60.read_grid(data)
    domain = h60.h60_emission_domain(data)
    assert int(domain.sum()) == 1_610_706, "the frozen emission domain is fixed"
    assert not (domain & grids["catalogue"]).any(), "no emission on the catalogue"
    assert (domain <= grids["evaluated"]).all(), "emission stays inside the evaluated domain"
    assert not (domain & ~h60.noise_ok(data)).any(), "masks are honoured"


@pytest.mark.needs_data
def test_h60_field_is_a_unit_interval_field_on_the_domain() -> None:
    from gems47 import grid as G
    data = G.data_dir()
    domain = h60.h60_emission_domain(data)
    field = h60.h60_field(data, domain)
    assert np.isfinite(field).all()
    assert float(field.min()) >= 0.0 and float(field.max()) <= 1.0
    assert (field[~domain] == 0.0).all(), "the field is zero off its domain"


@pytest.mark.needs_data
def test_published_h60_artifact_meets_the_format_contract() -> None:
    import hashlib

    import rasterio

    from gems47 import grid as G
    template = G.load_template()
    matches = sorted((ROOT / "docs" / "downloads").glob("gems47-h60-lidarscarp-*allfinite.tif"))
    if not matches:
        pytest.skip("H60 artifact not built in this checkout")
    path = matches[-1]
    receipt = json.loads((ROOT / "docs" / "data" / "h60-artifact.json").read_text())
    with rasterio.open(path) as src:
        v = src.read(1)
        assert src.count == 1 and str(src.dtypes[0]) == "float32"
        assert str(src.crs) == "EPSG:32611"
        assert list(src.transform)[:6] == list(template.transform)[:6]
        assert src.nodata is None
        assert np.all((v >= 0) & (v <= 1)), "Predicted values must be in range [0, 1]"
        assert np.isfinite(v).all()
        assert (v[~template.footprint] == 0).all()
        assert (v[template.catalogue] == 0).all()
        dots = int((v > 0).sum())
    assert dots == receipt["budget"] == 37_654
    assert hashlib.sha256(path.read_bytes()).hexdigest() == receipt["sha256_tif"]
    assert receipt["uniqueness"]["exact_matches"] == 0
    assert receipt["uniqueness"]["max_jaccard"] < 0.5


@pytest.mark.needs_data
def test_h60_artifact_zip_contents_match_the_published_bytes() -> None:
    import hashlib
    import zipfile

    matches = sorted((ROOT / "docs" / "downloads").glob("gems47-h60-lidarscarp-*.zip"))
    if not matches:
        pytest.skip("H60 artifact not built in this checkout")
    zpath = matches[-1]
    receipt = json.loads((ROOT / "docs" / "data" / "h60-artifact.json").read_text())
    with zipfile.ZipFile(zpath) as z:
        names = set(z.namelist())
        assert names == {Path(receipt["download_url"]).name,
                         f"{receipt['artifact']}-note.txt",
                         f"{receipt['artifact']}-receipt.json"}
        tif_bytes = z.read(Path(receipt["download_url"]).name)
        assert hashlib.sha256(tif_bytes).hexdigest() == receipt["sha256_tif"]
        note = z.read(f"{receipt['artifact']}-note.txt").decode()
        assert "h60 lidar-scarp d2p0 conformal90" in note
        assert "not a copy of any prior submission" in note
