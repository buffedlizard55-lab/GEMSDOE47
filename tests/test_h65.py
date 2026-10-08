"""H65 round contracts: frozen definitions, tip/vent/mask logic, screen receipt.

The heavy pieces (the 41-block screen, the H70 instrument study) have their own
scripts; these tests pin the invariants that must never silently change: the frozen
mask radii, the tip-pixel definition, the vent CSV parsing, the emitted-mass
aggregation law (no division -- the H60 script's //7 is not repeated), and the
frozen verdicts in the published screen receipt.  Tests that read the restored
rasters are marked ``needs_data``.
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

from gems47 import h65


# ------------------------------------------------------------------ frozen definitions
def test_h65_mask_radii_are_frozen() -> None:
    assert (h65.H68_ROAD_M, h65.H68_CLAIM_M) == (150.0, 100.0)
    assert (h65.H69_ROAD_M, h65.H69_CLAIM_M) == (400.0, 250.0)


def test_preregistration_is_committed_and_covers_the_slate() -> None:
    path = ROOT / "docs" / "research" / "h65-hypotheses-preregistered.md"
    assert path.is_file(), "the preregistered slate must be published"
    text = path.read_text(encoding="utf-8")
    for token in ("H65", "H66", "H67", "H68", "H69", "H70", "150 m", "400 m", "37,654",
                  "gate", "lappos_t200_d3", "sgmc_offcat", "1.4"):
        assert token in text, token


# ------------------------------------------------------------------ tip logic
def test_tip_pixels_marks_exactly_endpoints() -> None:
    cat = np.zeros((7, 7), bool)
    cat[3, 1:6] = True  # a horizontal 5-pixel trace: tips at columns 1 and 5
    tips = h65.tip_pixels(cat)
    assert tips.sum() == 2
    assert tips[3, 1] and tips[3, 5]
    assert not tips[3, 2:5].any()


def test_tip_pixels_ignores_isolated_pixels() -> None:
    cat = np.zeros((5, 5), bool)
    cat[2, 2] = True
    assert not h65.tip_pixels(cat).any()


def test_tip_pixels_handles_branching() -> None:
    cat = np.zeros((7, 7), bool)
    cat[3, 1:6] = True
    cat[1:4, 3] = True  # a T: three tips, junction has 3 neighbours
    tips = h65.tip_pixels(cat)
    assert tips.sum() == 3
    assert not tips[3, 3]


# ------------------------------------------------------------------ emitted mass law
def test_emitted_mass_sums_primary_rows_with_no_division() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import run_h65_screen as S
    rows = []
    for block_id, dots in ((0, 100), (1, 200)):
        for instrument in ("lappos_t200_d3", "sgmc_offcat", "step_t150_d3"):
            rows.append(dict(role="selection", block_id=block_id, model="h65",
                             spacing_px=2.0, instrument=instrument, emitted=dots))
    assert S.emitted_mass(rows, "h65", "selection", 2.0) == 300


# ------------------------------------------------------------------ needs data
@pytest.mark.needs_data
def test_vent_pixels_match_the_pinned_csv() -> None:
    import csv as csv_mod

    from gems47.grid import SHAPE, data_dir
    mask = h65.volcanic_vent_pixels(data_dir(), SHAPE[0], SHAPE[1])
    with (data_dir() / "external" / "gdr_volcanic_vents_in_footprint.csv").open() as fh:
        n = sum(1 for _ in csv_mod.DictReader(fh))
    assert n == 21, "the pinned vent CSV carries 21 vents"
    assert int(mask.sum()) == 21, "every vent pixel lands on a distinct in-grid cell"


@pytest.mark.needs_data
def test_mask_domains_nest_and_shrink_with_radius() -> None:
    from gems47 import h60
    from gems47.grid import data_dir
    data = data_dir()
    d60 = h60.h60_emission_domain(data)
    d68 = h65.lidar_domain_rad(data, h65.H68_ROAD_M, h65.H68_CLAIM_M)
    d69 = h65.lidar_domain_rad(data, h65.H69_ROAD_M, h65.H69_CLAIM_M)
    assert not (d69 & ~d60).any(), "strict masks must nest inside the H60 domain"
    assert not (d60 & ~d68).any(), "the H60 domain must nest inside the relaxed domain"
    assert int(d69.sum()) < int(d60.sum()) < int(d68.sum())


@pytest.mark.needs_data
def test_fields_are_unit_interval_on_their_domains() -> None:
    from gems47 import h50, h60
    from gems47.grid import data_dir
    data = data_dir()
    grids = h50.read_grid(data)
    domain60 = h60.h60_emission_domain(data)
    for field, dom in ((h65.h65_field(data, domain60), domain60),
                       (h65.h66_field(data, domain60), domain60),
                       (h65.h67_field(data, grids["evaluated"]), grids["evaluated"])):
        assert np.isfinite(field[dom]).all()
        assert (field[dom] >= 0).all() and (field[dom] <= 1).all()
        assert (field[~dom] == 0).all()


# ------------------------------------------------------------------ screen receipt
def test_screen_receipt_gate_is_internally_consistent() -> None:
    path = ROOT / "evidence" / "h65" / "screen.json"
    if not path.is_file():
        pytest.skip("screen has not been run in this checkout")
    screen = json.loads(path.read_text())
    arms = screen["arms"]
    h60sel = arms["h60"]["pooled_primary_selection"]
    h60sgmc = arms["h60"]["pooled_sgmc_selection"]
    for arm, gate in screen["gate"]["per_arm"].items():
        a = arms[arm]
        rnd = screen["controls"][arm]["random"]
        expect = {
            "no_regression_on_primary": a["pooled_primary_selection"] >= h60sel,
            "positive_conformal_floor": a["conformal"]["floor"] > 0.0,
            "sgmc_beats_h60": a["pooled_sgmc_selection"] >= h60sgmc,
            "sgmc_beats_random": a["pooled_sgmc_selection"] >= rnd["sgmc"],
            "beats_random_3x_primary": a["pooled_primary_selection"] >= 3.0 * rnd["primary"],
        }
        assert gate["conditions"] == expect, arm
        assert gate["passed"] == all(expect.values()), arm
    passing = [a for a, g in screen["gate"]["per_arm"].items() if g["passed"]]
    assert screen["gate"]["passing_arms"] == passing
    if passing:
        best = max(passing, key=lambda a: (arms[a]["pooled_sgmc_selection"],
                                           arms[a]["conformal"]["floor"],
                                           arms[a]["pooled_primary_selection"]))
        assert screen["gate"]["winner"] == best
    else:
        assert screen["gate"]["winner"] is None
    assert screen["anchor_reproduction"]["matches"] is True
