"""H65 paired-scape field and full-domain scoring regressions."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from gems47 import h50, h65
from scripts.run_h65_screen import metric


def _channels(shape=(24, 24)):
    y, x = np.indices(shape)
    return {
        "step_max": (x + y).astype(np.float32),
        "lapneg_max": (x * 2 + y).astype(np.float32),
        "lappos_max": (x + y * 3).astype(np.float32),
        "valid": np.ones(shape, dtype=np.float32),
    }


def test_h65_rank_consensus_preserves_the_callers_mask_and_arrays():
    channels = _channels()
    mask = np.ones((24, 24), dtype=bool)
    mask[0, :] = False
    mask_before = mask.copy()
    before = [channels[k].copy() for k in h65.H65_CHANNELS]
    field = h65.paired_morphology_score(*(channels[k] for k in h65.H65_CHANNELS), mask)
    assert np.array_equal(mask, mask_before)
    assert all(np.array_equal(channels[k], v) for k, v in zip(h65.H65_CHANNELS, before))
    assert field.dtype == np.float32
    assert np.isfinite(field).all()
    assert 0.0 <= float(field.min()) <= float(field.max()) <= 1.0
    assert (field[~mask] == 0.0).all()


def test_h65_score_excludes_nonfinite_values_without_mutating_validity():
    channels = _channels()
    channels["step_max"][5, 5] = np.nan
    valid = np.ones((24, 24), dtype=bool)
    original = valid.copy()
    field = h65.paired_morphology_score(*(channels[k] for k in h65.H65_CHANNELS), valid)
    assert np.array_equal(valid, original)
    assert field[5, 5] == 0.0
    assert np.isfinite(field).all()


def test_h65_field_intersects_lidar_validity_on_a_copy(monkeypatch):
    channels = _channels()
    channels["valid"][4:8, 4:8] = 0
    monkeypatch.setattr(h50, "lidar_scarp_channels", lambda _path: channels)
    domain = np.ones((24, 24), dtype=bool)
    original = domain.copy()
    field = h65.paired_morphology_field(Path("unused"), domain)
    assert np.array_equal(domain, original), "the caller's domain must not be mutated"
    assert (field[4:8, 4:8] == 0.0).all()
    assert np.isfinite(field).all()


def test_full_scoring_domain_counts_truth_outside_emission_domain():
    """A detector's candidate mask cannot become the metric's valid mask."""
    scoring = np.ones((24, 24), dtype=bool)
    emission = np.zeros_like(scoring)
    emission[:12, :12] = True
    truth = np.zeros_like(scoring)
    truth[18, 18] = True
    pred = np.zeros(scoring.shape, dtype=np.float32)
    r = metric(pred, truth, scoring, crosscheck=True)
    assert int(emission.sum()) < int(scoring.sum())
    assert r["n_truth"] == 1
    assert r["FN_w"] == 1.0
    assert r["DTI"] == 0.0
