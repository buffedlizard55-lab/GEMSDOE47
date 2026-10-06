"""One-sided, simultaneous split conformal for a frozen operating-point sweep.

Source: Lei et al., JASA 2018, Algorithm 2 / Theorem 2.2,
https://doi.org/10.1080/01621459.2017.1307116 .

The unit is ONE block's vector of DTI scores over the fixed sweep, not a spacing
choice and not a leaderboard submission. Taking the maximum residual within a
block gives joint coverage over the sweep, allowing calibration-based selection.
The theorem needs exchangeability of calibration/future score vectors conditional
on the frozen fit/selection stage. This module cannot establish that assumption.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any

import numpy as np


def _scores(values: Any, name: str) -> np.ndarray:
    a = np.asarray(values, dtype=np.float64)
    if a.ndim != 2 or not all(a.shape):
        raise ValueError(f"{name} must be a nonempty blocks-by-settings matrix")
    if not np.isfinite(a).all() or ((a < 0) | (a > 1)).any():
        raise ValueError(f"{name} must contain finite DTI scores in [0,1]")
    return a


def simultaneous_lower_bounds(selection: Any, calibration: Any, *, coverage: float = 0.90) -> dict:
    """Compute a joint lower prediction band, not a confidence interval for a mean.

    Selection and calibration must be disjoint blocks, with the model/centers
    fixed before calibration. Return strict-JSON-compatible data, including a
    zero floor when the finite-sample rank needs the augmented +infinity score.
    Empty-truth blocks must NOT be dropped after looking at their scores.
    """
    s = _scores(selection, "selection")
    c = _scores(calibration, "calibration")
    if s.shape[1] != c.shape[1]:
        raise ValueError("selection/calibration settings differ")
    if isinstance(coverage, bool) or not np.isfinite(coverage) or not 0 < coverage < 1:
        raise ValueError("coverage must be finite and strictly between 0 and 1")
    n = c.shape[0]
    # Decimal rational arithmetic avoids a floating-point ceil at exact ranks.
    level = Fraction(str(coverage))
    k = ((n + 1) * level.numerator + level.denominator - 1) // level.denominator
    center = s.mean(axis=0)
    residuals = np.max(center[None, :] - c, axis=1)
    finite_rank = k <= n
    q = float(np.sort(residuals)[k - 1]) if finite_rank else None
    lower = np.clip(center - q, 0, 1) if finite_rank else np.zeros(s.shape[1])
    return {
        "method": "max-over-settings one-sided split conformal",
        "target": "one future exchangeable public-catalogue block score vector",
        "n_selection": int(s.shape[0]), "n_calibration": int(n),
        "n_settings": int(s.shape[1]), "nominal_coverage": float(coverage),
        "rank_1_based": int(k), "rank_exceeds_calibration_count": not finite_rank,
        "selection_centers": center.tolist(), "calibration_scores": c.tolist(),
        "max_residual_per_block": residuals.tolist(),
        "sorted_max_residuals": np.sort(residuals).tolist(),
        "quantile": q, "augmented_infinity_used": not finite_rank,
        "lower_bounds": lower.tolist(),
        "finite_sample_coverage_at_least_if_exchangeable": k / (n + 1),
        "exchangeability_verified": False,
        "private_leaderboard_floor_certified": False,
        "limitations": [
            "Marginal prediction coverage for one block, not all future blocks or a pooled nonlinear DTI.",
            "Spatial separation does not establish geological exchangeability.",
            "Public catalogue labels differ from expert-private new-fault labels.",
            "Adaptive leaderboard submissions are not exchangeable calibration units.",
        ],
    }


def choose_operating_point(bounds: dict, spacings: list[float] | tuple[float, ...]) -> int:
    """Pick maximal simultaneous floor; ties use selection mean, then spacing."""
    floor = np.asarray(bounds["lower_bounds"], float)
    center = np.asarray(bounds["selection_centers"], float)
    spacing = np.asarray(spacings, float)
    if floor.ndim != 1 or floor.size == 0 or not (floor.shape == center.shape == spacing.shape):
        raise ValueError("spacings and band dimensions differ")
    if not np.isfinite(np.concatenate((floor, center, spacing))).all() or (spacing <= 0).any():
        raise ValueError("invalid operating-point values")
    if ((floor < 0) | (floor > 1) | (center < 0) | (center > 1)).any():
        raise ValueError("DTI bounds/centers must be in [0,1]")
    if np.unique(spacing).size != spacing.size:
        raise ValueError("spacing settings must be unique")
    return max(range(floor.size), key=lambda i: (float(floor[i]), float(center[i]), float(spacing[i])))
