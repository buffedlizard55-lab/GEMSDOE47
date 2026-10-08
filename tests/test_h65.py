"""H65-H68 round contracts: frozen definitions, field invariants and the receipts.

The heavy pieces (the 41-block screen, the artifact build) have their own scripts;
these tests pin the invariants that must never silently change: the frozen slate
definitions (channels, thresholds, radii, mixture weight), the tie-free lexicographic
rank, the screen receipt's frozen verdicts (including the conformal operating-point
rule), the artifact receipt, and the h33-2-b2 reference measurement.  Tests that read
the 500 MB rasters are marked ``needs_data``.
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
from gems47.conformal import choose_operating_point

SCREEN = ROOT / "evidence" / "h65" / "screen.json"
HISTORY = ROOT / "evidence" / "h65" / "spacing-history.csv"
H33 = ROOT / "evidence" / "h33_reference_analysis.json"
PREREG = ROOT / "docs" / "research" / "h65-hypotheses-preregistered.md"


# ------------------------------------------------------------------ frozen definitions
def test_slate_constants_are_frozen() -> None:
    assert h65.H68_CHANNELS == h60_six() + ("ex_max", "relief")
    assert h65.H65_THRESHOLDS == {"step_max": 150.0, "lappos_max": 200.0,
                                  "lapneg_max": 200.0, "upface_max": 200.0,
                                  "downface_max": 200.0, "cross_max": 200.0}
    assert h65.H66_FAR_RADIUS_PX == 3.0
    assert h65.H67_LAMBDA == 0.5
    assert h65.H67_THK_BAND == "ThK"
    assert "coh100" not in h65.H68_CHANNELS          # H64: anti-correlates -0.532
    assert "strike" not in h65.H68_CHANNELS          # not a max-amplitude
    assert "ex_mean" not in h65.H68_CHANNELS


def h60_six() -> tuple[str, ...]:
    from gems47 import h60
    return h60.H60_CHANNELS


def test_preregistration_is_committed_and_covers_the_slate() -> None:
    assert PREREG.is_file(), "the preregistered slate must be published"
    text = PREREG.read_text(encoding="utf-8")
    for token in ("H65", "H66", "H67", "H68", "Th/K", "ex_max", "relief",
                  "choose_operating_point", "90.909", "beats_incumbent_h60",
                  "37,654", "500610", "lappos_t200_d3", "validated candidate"):
        assert token in text, token


# ------------------------------------------------------------------ field invariants
def _synthetic_channels(shape=(40, 50)) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(7)
    ch = {name: rng.integers(0, 256, size=shape).astype(np.uint8)
          for name in ("step_max", "lappos_max", "lapneg_max", "upface_max",
                       "downface_max", "cross_max", "ex_max", "relief", "valid")}
    ch["valid"][:] = 255
    return ch


def test_lexicographic_rank_is_tie_free_and_in_unit_interval() -> None:
    mask = np.zeros((20, 30), bool)
    mask[2:15, 3:20] = True
    counts = np.zeros((20, 30))
    counts[2:15, 3:20] = np.random.default_rng(1).integers(0, 7, size=(13, 17))
    amp = np.random.default_rng(2).random((20, 30))
    out = h65._lexicographic_rank((counts, amp), mask)
    assert out.dtype == np.float32
    assert (out[~mask] == 0).all()
    vals = np.sort(out[mask])
    assert np.all(np.diff(vals) > 0), "lexicographic rank must be tie-free"
    assert vals.min() > 0 and vals.max() <= 1.0
    # primary key dominates: a count-6 cell always outranks a count-0 cell
    hi = np.zeros((20, 30)); hi[5, 5] = 6.0
    lo = np.zeros((20, 30)); lo[6, 6] = 0.0
    a = np.zeros((20, 30)); a[7, 7] = 1.0
    ranked = h65._lexicographic_rank((hi, a), mask)
    assert ranked[5, 5] > ranked[6, 6]
    ranked2 = h65._lexicographic_rank((lo, a), mask)
    assert ranked2[7, 7] > ranked2[6, 6]   # amplitude breaks ties within a count


def test_consensus_counts_match_thresholds_on_synthetic_data() -> None:
    ch = _synthetic_channels()
    mask = np.ones(ch["step_max"].shape, bool)
    # patch the channels so the counts are exactly known
    for name in h65.H65_THRESHOLDS:
        ch[name][:] = 0
    ch["step_max"][0, 0] = 151      # above its t150 threshold
    ch["lappos_max"][0, 0] = 201    # above its t200 threshold
    ch["lappos_max"][1, 1] = 199    # below
    ch["cross_max"][1, 1] = 200     # not above (strict >)
    consensus = np.zeros(mask.shape, np.int32)
    for name, thr in h65.H65_THRESHOLDS.items():
        consensus += (ch[name] > float(thr)).astype(np.int32)
    assert consensus[0, 0] == 2
    assert consensus[1, 1] == 0
    assert consensus.sum() == 2


# ------------------------------------------------------------------ screen receipt
def test_screen_receipt_verdicts_are_frozen() -> None:
    s = json.loads(SCREEN.read_text())
    assert s["status"] == "RESEARCH_SCREEN_NOT_A_SUBMISSION"
    assert s["design"]["budget"] == 37_654
    assert s["design"]["spacings_px"] == [2.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.6]
    assert s["design"]["h66_far_radius_px"] == 3.0
    assert s["design"]["h67_lambda"] == 0.5
    assert s["design"]["h68_channels"] == list(h65.H68_CHANNELS)
    # anchors reproduced bit-for-bit against the frozen H60 receipt
    assert s["anchor_reproduction"]["matches"] is True
    assert abs(s["arms"]["h60"]["pooled_primary_selection"] - 0.287891) < 1e-6
    assert abs(s["arms"]["h50"]["pooled_primary_selection"] - 0.165881) < 1e-6
    # the frozen verdicts (corrected run — see evidence/h65/erratum-consensus-rank-20261008.md)
    assert s["gate"]["winner"] == "h68"                       # frozen SGMC tie-break
    assert s["gate"]["passing_arms"] == ["h65", "h66", "h67", "h68"]
    assert s["gate"]["promotable_arms"] == ["h65"]            # conditions 1-5 only
    for arm in ("h65", "h66", "h67", "h68"):
        assert s["gate"]["per_arm"][arm]["passed"] is True
    # H65 is the only arm beating the H60 incumbent on BOTH instruments
    assert s["gate"]["per_arm"]["h65"]["conditions"]["beats_incumbent_h60"] is True
    assert s["arms"]["h65"]["pooled_primary_selection"] > s["arms"]["h60"]["pooled_primary_selection"]
    assert s["arms"]["h65"]["pooled_sgmc_selection"] > s["arms"]["h60"]["pooled_sgmc_selection"]
    for arm in ("h66", "h67", "h68"):
        assert s["gate"]["per_arm"][arm]["conditions"]["beats_incumbent_h60"] is False
    # H68 beats H60 on the independent instrument but not on the primary
    assert s["arms"]["h68"]["pooled_sgmc_selection"] > s["arms"]["h60"]["pooled_sgmc_selection"]
    assert s["arms"]["h68"]["pooled_primary_selection"] < s["arms"]["h60"]["pooled_primary_selection"]


def test_conformal_operating_point_is_argmax_certified_floor() -> None:
    s = json.loads(SCREEN.read_text())
    spacings = s["design"]["spacings_px"]
    for arm in ("h50", "h60", "h65", "h66", "h67", "h68"):
        v = s["arms"][arm]
        band = v["conformal"]
        chosen = choose_operating_point(band, spacings)
        assert float(spacings[chosen]) == v["selected_spacing_px"], arm
        # the chosen spacing really is the argmax of the certified lower bound
        assert band["lower_bounds"][chosen] == max(band["lower_bounds"])
        # the finite-sample confidence level: rank 20 of 22 -> >= 90.909 %
        assert band["rank_1_based"] == 20
        assert band["n_calibration"] == 21
        assert band["n_selection"] == 20
        assert abs(band["coverage_at_least"] - 20 / 22) < 1e-12


def test_spacing_history_rows_cover_arms_spacings_and_controls() -> None:
    import csv
    with HISTORY.open() as fh:
        rows = list(csv.DictReader(fh))
    models = {r["model"] for r in rows}
    assert {"h50", "h60", "h65", "h66", "h67", "h68", "random",
            "h33_reference", "h47c1"} <= models
    for model in ("h50", "h60", "h65", "h66", "h67", "h68", "random"):
        spacings = sorted({float(r["spacing_px"]) for r in rows if r["model"] == model})
        assert spacings == [2.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.6], model
    roles = {r["role"] for r in rows}
    assert roles == {"selection", "calibration"}


# ------------------------------------------------------------------ artifact receipts
def test_h68_candidate_artifact_is_consistent_and_honestly_labelled() -> None:
    a = json.loads((ROOT / "docs" / "data" / "h68-artifact.json").read_text())
    assert a["hypothesis_id"] == "H68"
    assert a["kind"] == "validated_candidate_not_recommended_while_primary_stands"
    assert a["promoted_to_primary"] is False
    assert a["budget"] == 37_654
    assert a["spacing_px"] == 2.8
    assert a["screen_selected_spacing_px"] == 2.8
    assert all(v is True for k, v in a["readback_checks"].items()
               if isinstance(v, bool))
    assert a["uniqueness_pass"] is True
    assert a["uniqueness"]["exact_matches"] == 0
    assert a["uniqueness"]["max_jaccard"] < 0.5
    assert a["conformal"]["rank_1_based"] == 20
    assert abs(a["conformal"]["coverage_at_least"] - 20 / 22) < 1e-12
    assert a["conformal"]["confidence_level_pct"] == 90.909
    assert a["submission_note_field"] == "h68 lidar 8-channel d2p8 conformal90"
    assert len(a["submission_note_field"]) <= 60
    # the note reports the conformal confidence level next to the chosen spacing
    note = (ROOT / "docs" / "downloads" / f"{a['artifact']}-note.txt").read_text()
    assert "2.8 px (280 m)" in note
    assert "90.91%" in note and "rank 20 of 22" in note
    assert "certified holdout floor 0.0993 DTI" in note
    assert "does NOT beat the previous incumbent H60" in note
    # the deployed bytes match the receipt hash
    import hashlib
    tif = ROOT / "docs" / a["download_url"]
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == a["sha256_tif"]


def test_h65_research_artifact_is_published_with_the_uniqueness_failure_disclosed() -> None:
    """The round's best science is blocked by the frozen uniqueness bar — published,
    not hidden, and clearly NOT OK to submit."""
    a = json.loads((ROOT / "docs" / "data" / "h65-artifact.json").read_text())
    assert a["hypothesis_id"] == "H65"
    assert a["kind"] == "research_artifact_not_ok_to_submit_uniqueness_bar"
    assert a["promoted_to_primary"] is False
    assert a["submission_note_field"] is None          # no portal note offered
    assert a["budget"] == 37_654
    assert a["spacing_px"] == 2.0
    assert a["screen_selected_spacing_px"] == 2.0
    assert all(v is True for k, v in a["readback_checks"].items()
               if isinstance(v, bool))                 # format is fine
    assert a["uniqueness_pass"] is False
    assert a["uniqueness"]["exact_matches"] == 0
    assert a["uniqueness"]["max_jaccard"] >= 0.5      # 0.5119 vs the H60 incumbent
    # unique against every scored prior submission (machine-checkable)
    assert a["uniqueness"]["max_jaccard_vs_scored_priors"] < 0.05
    assert a["uniqueness"]["max_jaccard_vs_scored_priors"] == \
        round(a["uniqueness"]["max_jaccard_vs_scored_priors"], 6)
    assert "frozen condition 6" in a["not_ok_to_submit_reason"]
    assert a["conformal"]["rank_1_based"] == 20
    assert abs(a["conformal"]["coverage_at_least"] - 20 / 22) < 1e-12
    assert a["conformal"]["confidence_level_pct"] == 90.909
    # it beat the H60 incumbent on both instruments (the round's headline result)
    assert a["holdout"]["candidate_pooled_dti"] > a["holdout"]["h60_incumbent_pooled_dti"]
    assert a["holdout"]["candidate_sgmc_pooled_dti"] > \
        a["holdout"]["h60_incumbent_sgmc_pooled_dti"]
    # the note discloses the scientific pass AND the uniqueness fail
    note = (ROOT / "docs" / "downloads" / f"{a['artifact']}-note.txt").read_text()
    assert "SCIENTIFIC PASS, UNIQUENESS FAIL" in note
    assert "0.5119" in note and "NOT OK to submit" in note
    assert "90.91%" in note and "rank 20 of 22" in note
    # the deployed bytes match the receipt hash
    import hashlib
    tif = ROOT / "docs" / a["download_url"]
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == a["sha256_tif"]


def test_consensus_rank_erratum_is_published() -> None:
    path = ROOT / "evidence" / "h65" / "erratum-consensus-rank-20261008.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    for token in ("inverted", "0.015698", "0.291870", "r[::-1]", "IR-2026-10-08-D"):
        assert token in text, token


# ------------------------------------------------------------------ h33 measurement
def test_h33_reference_measurement_is_frozen() -> None:
    h = json.loads(H33.read_text())
    g = h["geometry"]
    assert g["dots_total"] == 37_654
    assert g["dots_on_evaluated"] == 37_654
    assert g["dots_on_catalogue"] == 0
    assert g["unique_values"] == [0.0, 1.0]
    # lineage: a strict subset of the scored d2.8 raster
    lin = h["lineage_jaccard"]
    assert lin["exact_matches"] == 0
    assert ".cache/gems_data/scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif" \
        in lin["reference_is_subset_of"]
    # the pruning invariant: the full-mass row reproduces the direct proxy DTI
    for inst, curve in h["pruning_mechanism"]["curves"].items():
        direct = h["proxy_dti_whole_evaluated_map"][inst]
        assert abs(curve[0]["dti"] - direct["dti"]) < 1e-6, inst
        assert curve[0]["kept_dots"] == g["dots_total"]
        # deleting low-credit dots never lowers the proxy DTI on this raster
        for row in curve[1:]:
            assert row["dti"] >= curve[0]["dti"] - 1e-9, (inst, row)


# ------------------------------------------------------------------ needs_data
@pytest.mark.needs_data
def test_fields_build_on_restored_data_with_frozen_domains() -> None:
    from gems47 import grid as G
    built = h65.build_all(G.data_dir())
    s = json.loads(SCREEN.read_text())
    doms = s["design"]["emission_domains"]
    assert int(built["h65"]["mask"].sum()) == doms["h60"] == doms["h65"] == doms["h68"]
    assert int(built["h66"]["mask"].sum()) == doms["h66"]
    assert int(built["h67"]["mask"].sum()) == doms["h67"]
    assert built["h65"]["counts"] == {int(k): v for k, v in s["h65_consensus_counts"].items()}
    for arm in ("h65", "h66", "h67", "h68"):
        f, m = built[arm]["field"], built[arm]["mask"]
        assert np.isfinite(f[m]).all()
        assert (f[m] > 0).all() and (f[m] <= 1).all()
        assert (f[~m] == 0).all()
