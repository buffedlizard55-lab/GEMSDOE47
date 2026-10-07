"""Tests for the H49 additions: the strike-aligned emitter (H49-A) and polarity coherence (H49-B).

These are unit tests on synthetic fields.  They exist because the two new operators make geometric
claims that must be checkable without the 500 MB rasters:

  * ``strike_classes`` must reproduce the ``geomorph.orientation`` convention, which was measured on
    synthetic straight ridges (N-S -> 2*theta ~ 0, E-W -> 2*theta ~ pi, diagonals -> +-pi/2);
  * ``nms_oriented`` must never keep two pixels inside the same exclusion ellipse, and must keep
    FEWER pixels than the isotropic rule on a wide ridge (that is the whole point of H49-A);
  * ``polarity_step`` must respond to a step and must reject a symmetric bump of the same amplitude.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from scipy import ndimage as ndi

from gems47s3 import emission as E
from gems47s3.conformal import conformal_quantile
from gems47s3.geomorph import orientation, polarity_step, rank_scale


def _ridge(shape=(240, 240), column=120, width=1, value=1.0) -> np.ndarray:
    z = np.zeros(shape, np.float32)
    z[:, column - width // 2: column + width // 2 + 1] = value
    return z


def test_strike_classes_match_the_documented_convention() -> None:
    z_ns = _ridge()
    z_ew = _ridge().T.copy()
    y, x = np.mgrid[0:240, 0:240]
    z_ne = np.zeros((240, 240), np.float32)
    z_ne[np.abs(y - x) <= 1] = 1.0                      # NE-SW trace: along = (1, 1)
    z_nw = np.zeros((240, 240), np.float32)
    z_nw[np.abs((y + x) - 240) <= 1] = 1.0                # NW-SE trace: along = (1, -1)
    mid = (120, 120)
    for z, expected in ((z_ns, 0), (z_ew, 1), (z_ne, 2), (z_nw, 3)):
        theta, coh = orientation(z, 2.0)
        cls = E.strike_classes(theta)
        assert coh[mid] > 0.3, "synthetic ridge must be coherent"
        assert int(cls[mid]) == expected, f"expected class {expected}, got {int(cls[mid])}"


def _wide_ridge_field(shape=(200, 200), column=100, halfwidth=3, noise=0.02, seed=7):
    rng = np.random.default_rng(seed)
    z = ndi.gaussian_filter((np.abs(np.arange(shape[1])[None, :] - column) < halfwidth
                             ).astype(np.float32) * np.ones((shape[0], 1), np.float32), 1.0)
    z = z + noise * rng.random(shape).astype(np.float32)
    return rank_scale(z)


def test_oriented_nms_enforces_the_ellipse_and_thins_a_wide_ridge() -> None:
    shape = (200, 200)
    field = _wide_ridge_field(shape)
    support = np.ones(shape, bool)
    theta = np.zeros(shape, np.float32)            # trace runs north-south everywhere
    along, across = 2.8, 4.0

    aniso = E.nms_oriented(field, support, along, across, theta)
    disk = E.nms_disk(field, support, 2.8)
    assert aniso.any() and disk.any()
    assert aniso.sum() < disk.sum(), "the ellipse strictly contains the disk, so it must keep fewer"

    # pairwise: no two survivors may lie inside each other's ellipse
    fp = E.ellipse_footprint(along, across, 1, 0)
    r = fp.shape[0] // 2
    pts = set(zip(*[a.tolist() for a in np.nonzero(aniso)]))
    violations = 0
    for (y, x) in pts:
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if (dy or dx) and fp[dy + r, dx + r] and (y + dy, x + dx) in pts:
                    violations += 1
    assert violations == 0, f"{violations} survivor pairs inside one exclusion ellipse"

    # and the across-strike axis is what does the thinning: the crest count is preserved
    crest = int(aniso[:, 97:104].sum())
    assert crest >= 30, "the ridge crest must still be sampled along its whole length"


def test_oriented_rule_reduces_to_the_disk_when_the_axes_are_equal() -> None:
    rng = np.random.default_rng(3)
    field = rank_scale(rng.random((120, 120)).astype(np.float32))
    support = np.ones((120, 120), bool)
    theta = np.zeros((120, 120), np.float32)
    for s in (2.0, 2.8):
        a = E.nms_oriented(field, support, s, s, theta)
        b = E.nms_disk(field, support, s)
        assert np.array_equal(a, b), f"oriented(along=across={s}) must equal nms_disk({s})"


def test_oriented_nms_respects_support() -> None:
    rng = np.random.default_rng(11)
    field = rank_scale(rng.random((120, 120)).astype(np.float32))
    support = np.zeros((120, 120), bool)
    support[10:40, 10:40] = True
    out = E.nms_oriented(field, support, 2.8, 4.0, np.zeros((120, 120), np.float32))
    assert out.any() and (out & ~support).sum() == 0


def test_polarity_responds_to_a_step_and_rejects_a_symmetric_bump() -> None:
    y, x = np.mgrid[0:200, 0:200]
    step = np.zeros((200, 200), np.float32)
    step[:, 100:] = 1.0                                   # a real step, up to the east
    ridge = 1.0 - np.abs(x - 100) / 25.0                  # a symmetric bump, same amplitude
    ridge = np.clip(ridge, 0, None).astype(np.float32)
    p_step = polarity_step(rank_scale(step.astype(np.float32)), 9)
    p_ridge = polarity_step(rank_scale(ridge), 9)
    on_trace = (slice(90, 110), slice(99, 102))
    assert p_step[on_trace].max() > 0.05, "a genuine step must produce a polarity response"
    assert p_step[on_trace].max() > 3.0 * p_ridge[on_trace].max(), (
        "a symmetric bump must be rejected relative to a step of the same amplitude")


def test_emit_oriented_matches_nms_oriented_and_honours_budget() -> None:
    rng = np.random.default_rng(3)
    field = rank_scale(rng.random((150, 150)).astype(np.float32))
    mask = np.ones((150, 150), bool)
    theta = np.zeros((150, 150), np.float32)
    direct = E.nms_oriented(field, mask, 2.8, 4.0, theta)
    rec = E.emit_oriented(field, mask, 2.8, 4.0, theta, budget=50)
    assert rec["engine"] == "oriented" and rec["across"] == 4.0
    assert int(rec["mask"].sum()) <= 50
    assert int(direct.sum()) == rec["n_thinned"]
    assert np.array_equal(rec["mask"], E.topk_mask(np.where(direct, field, -np.inf),
                                                   min(50, int(direct.sum())), direct))


def test_disk_and_oriented_keep_the_isolated_peak() -> None:
    field = np.zeros((60, 60), np.float32)
    field[30, 30] = 1.0
    theta = np.zeros((60, 60), np.float32)
    support = np.ones((60, 60), bool)
    a = E.nms_oriented(field, support, 2.8, 2.8, theta)
    b = E.nms_disk(field, support, 2.8)
    assert a[30, 30] and b[30, 30]
    assert np.array_equal(a, b), "with equal axes and one isolated peak the rules must agree exactly"


def test_oriented_nms_is_deterministic() -> None:
    rng = np.random.default_rng(5)
    field = rank_scale(ndi.gaussian_filter(rng.random((120, 120)).astype(np.float32), 2.0))
    theta = np.zeros((120, 120), np.float32)
    support = np.ones((120, 120), bool)
    a = E.nms_oriented(field, support, 2.8, 4.0, theta)
    b = E.nms_oriented(field, support, 2.8, 4.0, theta)
    assert np.array_equal(a, b)


@pytest.mark.needs_data
def test_published_h49_tiff_has_the_exact_null_footprint_mask():
    """The downloadable H49 TIFF must satisfy the strict read-back contract, not just value bounds."""
    from gems47 import contract as C
    from gems47 import grid as G

    root = Path(__file__).resolve().parents[1]
    metadata = json.loads((root / "docs" / "data" / "current-artifact.json").read_text())
    artifact = root / "docs" / "downloads" / metadata["filename"]
    result = C.validate(artifact, G.load_template())
    assert result["format_valid"], result["failed_checks"]
    assert result["stats"]["positive_pixels"] == metadata["format_validation"]["stats"][
        "positive_cells_in_footprint"
    ]
    assert metadata["status"] == "RESEARCH_ONLY_SLOT_GATE_CLOSED"
    assert metadata["slot_authorized"] is False
    assert metadata["slot_gate"]["authorized"] is False
    assert metadata["organizer_score"] is None
    assert metadata["conformal_result_status"] == (
        "NOMINAL_FIXED_ARM_DIAGNOSTIC_NOT_FULL_ADAPTIVE_PIPELINE_GUARANTEE"
    )
    assert "conformal_certified_floor_primary_instrument" not in metadata
    public = metadata["public_uniqueness"]
    assert public["bounded_unique"] is True
    assert public["global_unique_proven"] is False
    audit_copy = root / "docs" / public["report"]
    audit = json.loads(audit_copy.read_text())
    assert audit["candidate_sha256"] == result["sha256"]
    assert audit["exact_matches"] == 0
    assert audit["comparisons"] == public["comparisons"]
    for arm_result in metadata["paired_vs_incumbent"].values():
        for half_result in arm_result.values():
            assert half_result["paired_difference_split_conformal_lower_bound"] < 0


def test_h49b_polarity_contrast_lower_bound_uses_candidate_minus_reference_direction():
    """The H49-B reported contrast is R7 polarity minus the R2 topographic reference."""
    root = Path(__file__).resolve().parents[1]
    sweep = json.loads((root / "evidence" / "sweep" / "sweep_h49b.json").read_text())
    arms: dict[tuple[str, str], dict[int, float]] = {}
    for row in sweep["rows"]:
        if (row["instrument"] != "B_sgmc_offcat" or row["emitter"] != "disk"
                or row["op"] != "s2.8_d7.37_b3"
                or row["recipe"] not in ("R2_scarp9_topo", "R7_scarp9_polarity")):
            continue
        arms.setdefault((row["recipe"], row["half"]), {})[int(row["block_index"])] = float(row["dti"])

    expected = {
        "selection": (0.00642308816364304, -0.00941204134820045),
        "calibration": (0.0024829962966223126, -0.01620891452098952),
    }
    for half, (mean_expected, lower_expected) in expected.items():
        candidate = arms[("R7_scarp9_polarity", half)]
        reference = arms[("R2_scarp9_topo", half)]
        common = sorted(candidate.keys() & reference.keys())
        differences = np.asarray([candidate[i] - reference[i] for i in common])
        assert np.isclose(differences.mean(), mean_expected, atol=1e-12)
        lower = conformal_quantile(differences, 0.10, side="lower")
        assert np.isclose(lower, lower_expected, atol=1e-12)
        assert lower < 0.0, "the observed mean does not clear the paired-difference gate"
