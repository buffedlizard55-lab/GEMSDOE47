"""Deterministic guarded spatial units and label-isolated training targets.

All blocks with feature support are assigned before scoring, regardless of
truth count. A shuffled geographic grid is NOT proof of exchangeability, and
all public labels have been available to prior sessions: this is a new frozen
screen, not a never-inspected geological region or organizer private test.
"""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage

ROLES = ("train", "selection", "calibration", "test")


def spatial_blocks(support: np.ndarray, *, nrows: int = 16, ncols: int = 16,
                   guard_px: int = 20, seed: int = 470610) -> tuple[list[dict], np.ndarray]:
    valid = np.asarray(support, bool)
    if valid.ndim != 2 or min(valid.shape) < 1:
        raise ValueError("support must be nonempty 2D")
    for v in (nrows, ncols):
        if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
            raise ValueError("grid counts must be positive integers")
    if isinstance(guard_px, bool) or not isinstance(guard_px, int) or guard_px < 3:
        raise ValueError("guard must be an integer >=3 pixels")
    yr = np.linspace(0, valid.shape[0], nrows + 1).astype(int)
    xr = np.linspace(0, valid.shape[1], ncols + 1).astype(int)
    ids = np.full(valid.shape, -1, np.int16)
    blocks = []
    for row in range(nrows):
        for col in range(ncols):
            y0, y1, x0, x1 = yr[row] + guard_px, yr[row + 1] - guard_px, xr[col] + guard_px, xr[col + 1] - guard_px
            if y1 <= y0 or x1 <= x0:
                raise ValueError("guard leaves an empty geometric core")
            core = valid[y0:y1, x0:x1]
            count = int(core.sum())
            if count == 0:
                continue
            block_id = row * ncols + col
            ids[y0:y1, x0:x1] = np.where(core, block_id, -1)
            blocks.append({"block_id": block_id, "bounds_rc": [int(y0), int(y1), int(x0), int(x1)],
                           "support_pixels": count, "guard_px": guard_px})
    if len(blocks) < 12:
        raise ValueError("too few feature-supported blocks for four disjoint roles")
    permutation = np.random.default_rng(seed).permutation(len(blocks))
    n_train = len(blocks) // 2
    n_other = len(blocks) - n_train
    n_selection = n_other // 3
    n_cal = n_other // 3
    edges = (0, n_train, n_train + n_selection, n_train + n_selection + n_cal, len(blocks))
    for role, start, end in zip(ROLES, edges[:-1], edges[1:]):
        for i in permutation[start:end]:
            blocks[int(i)]["role"] = role
    return blocks, ids


def training_target(labels: np.ndarray, training_mask: np.ndarray) -> np.ndarray:
    """Kernel proximity formed from training-core labels ONLY (300 m support)."""
    g = np.asarray(labels) == 1
    mask = np.asarray(training_mask, bool)
    if g.ndim != 2 or g.shape != mask.shape:
        raise ValueError("labels/training_mask must have the same 2D shape")
    g &= mask
    if not g.any():
        return np.zeros(mask.shape, np.float32)
    distances = ndimage.distance_transform_edt(~g)
    return np.where(mask, np.maximum(1 - distances / 3, 0), 0).astype(np.float32)


def sample_training_rows(target: np.ndarray, train_rows: np.ndarray, *, seed: int = 470610,
                         max_rows: int = 180_000, max_positive: int = 90_000) -> tuple[np.ndarray, np.ndarray]:
    """Stratified subsampling with inverse-probability weights, not class weights."""
    t = np.asarray(target, float)
    rows = np.asarray(train_rows, np.int64)
    if t.ndim != 1 or rows.ndim != 1 or not rows.size or np.unique(rows).size != rows.size:
        raise ValueError("target and nonempty unique row indices must be 1D")
    if (rows < 0).any() or (rows >= t.size).any() or not np.isfinite(t[rows]).all():
        raise ValueError("invalid training rows/targets")
    if not 0 < max_positive < max_rows:
        raise ValueError("invalid training caps")
    pos = rows[t[rows] > 0]
    neg = rows[t[rows] == 0]
    if not pos.size or not neg.size:
        raise ValueError("training needs both nonzero-kernel and background rows")
    rng = np.random.default_rng(seed)
    p = rng.choice(pos, min(pos.size, max_positive), replace=False)
    n = rng.choice(neg, min(neg.size, max_rows - p.size), replace=False)
    out = np.concatenate((p, n))
    weights = np.concatenate((np.full(p.size, pos.size / p.size), np.full(n.size, neg.size / n.size)))
    # Normalized weights preserve L2 regularization scale across sample counts.
    weights /= weights.mean()
    return out, weights


def block_budget(block: dict, total_support: int, budget: int = 37_654) -> int:
    if total_support <= 0 or budget <= 0 or block["support_pixels"] <= 0:
        raise ValueError("invalid support or budget")
    return max(1, int(np.rint(budget * block["support_pixels"] / total_support)))


def pool(rows: list[dict]) -> float:
    if not rows:
        raise ValueError("cannot pool an empty list")
    tp = sum(float(r["TP_w"]) for r in rows)
    fp = sum(float(r["FP_w"]) for r in rows)
    ng = sum(int(r["|G|"]) for r in rows)
    den = .2 * (tp + fp) + .8 * ng
    return tp / den if den > 0 else 0.0


def gate(candidate_rows: list[dict], incumbent_rows: list[dict], random_rows: list[dict],
         lower_floor: float) -> dict:
    """Fixed, fail-closed local screen; not competition-slot authorization."""
    if not (len(candidate_rows) == len(incumbent_rows) == len(random_rows)) or not candidate_rows:
        raise ValueError("comparator block counts differ or are empty")
    for rows in (candidate_rows, incumbent_rows, random_rows):
        if len({r["block_id"] for r in rows}) != len(rows):
            raise ValueError("duplicate block IDs cannot create extra fold wins")
        for row in rows:
            tp, fp, ng, mass, fn, value = (row[k] for k in ("TP_w", "FP_w", "|G|", "S", "FN_w", "DTI"))
            if any(isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, float, np.number))
                   or not np.isfinite(v) or v < 0 for v in (tp, fp, ng, mass, fn, value)):
                raise ValueError("invalid metric components")
            if int(ng) != ng or tp > ng + 1e-8 or fp > mass + 1e-8 or abs(fn - (ng - tp)) > 1e-8:
                raise ValueError("inconsistent metric components")
            den = .2 * (tp + fp) + .8 * ng
            exact = tp / den if den > 0 else 0.0
            if abs(exact - value) > 1e-9:
                raise ValueError("reported DTI differs from exact components")
    for triplet in zip(candidate_rows, incumbent_rows, random_rows):
        if len({r["block_id"] for r in triplet}) != 1:
            raise ValueError("paired block IDs differ")
        if len({r["|G|"] for r in triplet}) != 1:
            raise ValueError("paired truth counts differ")
        if max(r["S"] for r in triplet) - min(r["S"] for r in triplet) > 1e-8:
            raise ValueError("paired emission mass differs")
        if any(not np.isfinite(r["DTI"]) or not 0 <= r["DTI"] <= 1 for r in triplet):
            raise ValueError("invalid DTI")
    if not np.isfinite(lower_floor) or not 0 <= lower_floor <= 1:
        raise ValueError("invalid lower floor")
    truth_bearing = [i for i, row in enumerate(candidate_rows) if row["|G|"] > 0]
    wins = sum(candidate_rows[i]["DTI"] > incumbent_rows[i]["DTI"] for i in truth_bearing)
    c, b, r = pool(candidate_rows), pool(incumbent_rows), pool(random_rows)
    cm = float(np.mean([row["DTI"] for row in candidate_rows]))
    bm = float(np.mean([row["DTI"] for row in incumbent_rows]))
    rm = float(np.mean([row["DTI"] for row in random_rows]))
    checks = {
        "pooled_beats_incumbent": c > b, "pooled_beats_random": c > r,
        "mean_beats_incumbent": cm > bm, "mean_beats_random": cm > rm,
        "at_least_ten_truth_bearing_blocks": len(truth_bearing) >= 10,
        "wins_two_thirds_truth_bearing_blocks": wins >= math.ceil(2 * len(truth_bearing) / 3),
        "positive_proxy_floor": lower_floor > 0,
    }
    return {"screen_passed": all(checks.values()), "checks": checks,
            "failures": [key for key, ok in checks.items() if not ok],
            "candidate_pooled_dti": c, "incumbent_pooled_dti": b, "random_pooled_dti": r,
            "candidate_mean_dti": cm, "incumbent_mean_dti": bm, "random_mean_dti": rm,
            "truth_bearing_blocks": len(truth_bearing), "candidate_block_wins": wins,
            "required_block_wins": math.ceil(2 * len(truth_bearing) / 3),
            "lower_floor": lower_floor, "slot_authorized": False,
            "reason_slot_closed": "Mirror-only inputs; exchangeability unverified; no private new-fault labels."}
