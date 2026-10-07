"""Mechanism and isolation tests; synthetic rasters are not competition claims."""
import numpy as np
import pytest
from scipy.special import erf

from gems47 import metric as M
from gems47 import profile as P
from gems47 import spatial_screen as B
from gems47.hypotheses import local_strike
from src.gems47_metric import dti


def test_templates_are_orthogonal_to_constant_and_linear_slope():
    u = np.arange(-6, 7, dtype=float)
    for width in P.WIDTHS_PX:
        for kind in ("step", "channel"):
            t = P.residualized_template(u, width, kind)
            assert t.sum() == pytest.approx(0, abs=1e-12)
            assert t @ u == pytest.approx(0, abs=1e-12)


def test_planar_terrain_has_no_scarp_profile_response():
    y, x = np.mgrid[:90, :90]
    support = np.zeros((90, 90), bool); support[20:-20, 20:-20] = True
    elevation = (100 + 2 * x + 3 * y).astype(np.float32)
    fields = P.scarp_profiles(elevation, elevation, support)
    assert np.max(fields["odd_step_r2"]) < 1e-6
    assert np.max(fields["even_channel_r2"]) < 1e-6
    assert all(np.all(value[~support] == 0) for value in fields.values())


def test_odd_step_beats_even_channel_and_is_polarity_invariant():
    y, x = np.mgrid[:100, :100]
    support = np.zeros((100, 100), bool); support[20:-20, 20:-20] = True
    z = 10 * erf((x - 50) / np.sqrt(2)) + .7 * x + .1 * y
    a = P.scarp_profiles(z, x.astype(float), support)
    b = P.scarp_profiles(-z, x.astype(float), support)
    assert a["odd_step_r2"][50, 50] > .99
    assert a["step_minus_channel_r2"][50, 50] > .9
    assert a["step_height_abs"][50, 50] == pytest.approx(20, rel=.005)
    assert a["step_alongstrike_consistency"][50, 50] > .99
    assert a["gravity_normal_agreement"][50, 50] > .99
    for name in P.PROFILE_NAMES:
        assert np.allclose(a[name], b[name], atol=1e-5), name


def test_channel_model_beats_odd_step_at_valley_center():
    y, x = np.mgrid[:100, :100]
    support = np.zeros((100, 100), bool); support[20:-20, 20:-20] = True
    z = -10 * np.exp(-.5 * (x - 50) ** 2) + .7 * x + .1 * y
    fields = P.scarp_profiles(z, x.astype(float), support)
    assert fields["even_channel_r2"][50, 50] > .99
    assert fields["odd_step_r2"][50, 50] < 1e-4


def test_training_target_is_invariant_to_every_held_out_label():
    mask = np.zeros((80, 80), bool); mask[10:30, 10:30] = True
    a = np.zeros((80, 80), np.uint8); a[20, 20] = 1
    b = a.copy(); b[~mask] = 1
    assert np.array_equal(B.training_target(a, mask), B.training_target(b, mask))
    assert not B.training_target(a, mask)[~mask].any()


def test_blocks_disjoint_deterministic_and_not_filtered_on_truth():
    support = np.ones((320, 320), bool)
    blocks, ids = B.spatial_blocks(support, nrows=4, ncols=4, guard_px=20)
    again, ids2 = B.spatial_blocks(support, nrows=4, ncols=4, guard_px=20)
    assert blocks == again and np.array_equal(ids, ids2)
    assert len(blocks) == 16
    assert {b["role"] for b in blocks} == set(B.ROLES)
    assert sum(b["support_pixels"] for b in blocks) == int((ids >= 0).sum())
    assert len({b["block_id"] for b in blocks}) == len(blocks)
    for b in blocks:
        y0, y1, x0, x1 = b["bounds_rc"]
        assert (ids[y0:y1, x0:x1] == b["block_id"]).all()


def test_inverse_probability_sampling_is_reproducible():
    target = np.concatenate((np.ones(300), np.zeros(700)))
    a, w = B.sample_training_rows(target, np.arange(1000), max_rows=180, max_positive=90)
    b, w2 = B.sample_training_rows(target, np.arange(1000), max_rows=180, max_positive=90)
    assert np.array_equal(a, b) and np.array_equal(w, w2)
    assert len(a) == len(np.unique(a)) == 180
    assert w.mean() == pytest.approx(1)
    assert (target[a] > 0).sum() == 90


def test_strike_tensor_uses_half_angle_and_correct_xy_components():
    horizontal = np.zeros((80, 80), bool); horizontal[40, 15:65] = True
    vertical = horizontal.T
    tx, ty, coherence = local_strike(horizontal)
    assert abs(tx[40, 40]) > .999 and abs(ty[40, 40]) < .001
    assert coherence[40, 40] > .99
    tx, ty, _ = local_strike(vertical)
    assert abs(tx[40, 40]) < .001 and abs(ty[40, 40]) > .999


def test_empty_truth_has_no_phantom_edt_corner_credit():
    p = np.ones((9, 9), np.float32)
    result = dti(p, np.zeros((9, 9), bool))
    assert result["FPw"] == 81
    assert result["TPw"] == 0 and result["dti"] == 0


def test_sparse_binary_dti_does_not_generally_equal_T_over_point_two_N_plus_point_eight_G():
    p = np.zeros((15, 15)); p[7, 7] = 1
    g = np.zeros((15, 15), bool); g[7, 4:11] = True
    s = M.score(p, g)
    assert s.T == pytest.approx(3)
    assert s.Phi == pytest.approx(1)
    assert s.F == pytest.approx(0)
    assert s.DTI == pytest.approx(3 / (.2 * 3 + .8 * 7))
    assert s.DTI != pytest.approx(3 / (.2 * s.S + .8 * s.K))


def test_any_positive_credit_improves_a_zero_score():
    assert M.accept(.001, 100, 0)
    assert not M.accept(0, 100, 0)


def test_gate_rejects_zero_floor_and_mass_mismatch():
    def rows(score):
        tp = score * (.2 * 5 + .8 * 100) / (1 - .2 * score)
        return [{"block_id": i, "DTI": score, "|G|": 100, "S": 10,
                 "TP_w": tp, "FP_w": 5, "FN_w": 100-tp} for i in range(12)]
    c, b, r = rows(.4), rows(.3), rows(.1)
    result = B.gate(c, b, r, 0)
    assert result["screen_passed"] is False
    assert "positive_proxy_floor" in result["failures"]
    assert result["slot_authorized"] is False
    b[0]["S"] = 11
    with pytest.raises(ValueError, match="mass"):
        B.gate(c, b, r, .2)
