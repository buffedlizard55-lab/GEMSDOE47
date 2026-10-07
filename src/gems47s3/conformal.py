"""Split-conformal operating-point selection with disjoint selection and calibration blocks.

Reference
---------
J. Lei, M. G'Sell, A. Rinaldo, R. J. Tibshirani and L. Wasserman,
"Distribution-Free Predictive Inference for Regression",
Journal of the American Statistical Association 113(523):1094-1111, 2018.
https://doi.org/10.1080/01621459.2017.1322365
Preprint: https://arxiv.org/abs/1604.04173

Safe selection protocol
-----------------------
1. Freeze the candidate grid and ranking rule before examining calibration scores.
2. Use the disjoint selection blocks to choose a candidate (this implementation ranks by mean DTI).
3. Only after the choice is fixed, use that candidate's calibration-block DTIs to compute a
   one-sided split-conformal lower prediction bound for ONE future exchangeable block.

For n calibration scores, the lower bound is the ``k``-th largest calibration DTI, where
``k = ceil((n + 1) * (1 - alpha))``. The finite-sample statement is conditional on exchangeability
of calibration and future block scores and on candidate selection being independent of calibration
outcomes. Spatial/geological exchangeability is an assumption; this module cannot establish it.
The result is not a guarantee for a block mean, pooled map DTI, a geographic subregion, private
labels, or a leaderboard score.

Do not select the candidate by maximizing a conformal floor computed on the same calibration data
unless a valid simultaneous/multiple-selection construction is used. Repeated random partitions of
the same blocks are sensitivity diagnostics, not new independent calibration samples.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from dataclasses import field as dc_field
from fractions import Fraction
from typing import Any

import numpy as np


def _alpha_fraction(alpha: float) -> Fraction:
    if isinstance(alpha, (bool, np.bool_)):
        raise TypeError("alpha must be numeric, not bool")
    try:
        value = float(alpha)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("alpha must be finite and strictly between 0 and 1") from exc
    if not math.isfinite(value) or not 0.0 < value < 1.0:
        raise ValueError("alpha must be finite and strictly between 0 and 1")
    # Decimal-string arithmetic avoids ceil errors at exact finite-sample ranks.
    return Fraction(str(alpha))


def _validated_dti(values: Any, name: str, *, allow_empty: bool = False) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64).reshape(-1)
    if not allow_empty and arr.size == 0:
        raise ValueError(f"{name} must contain at least one block score")
    if not np.isfinite(arr).all() or ((arr < 0.0) | (arr > 1.0)).any():
        raise ValueError(f"{name} must contain finite DTI scores in [0,1]")
    return arr


def conformal_order_statistic(n: int, alpha: float) -> int:
    """Return ``ceil((n+1)(1-alpha))`` using exact decimal-rational arithmetic."""
    if isinstance(n, (bool, np.bool_)) or int(n) != n or n < 0:
        raise ValueError("n must be a non-negative integer")
    level = _alpha_fraction(alpha)
    numerator = (int(n) + 1) * (level.denominator - level.numerator)
    return (numerator + level.denominator - 1) // level.denominator


def conformal_quantile(scores: np.ndarray, alpha: float, side: str = "lower") -> float:
    """Compute an exact finite-sample one-sided conformal order statistic.

    ``side="upper"`` returns the ``k``-th smallest score, an upper bound on an exchangeable
    future score. ``side="lower"`` treats the supplied values as the quantity being bounded
    (here, DTI) and returns the ``k``-th largest value. If ``k > n``, the requested bound is
    vacuous and returns +infinity (upper) or -infinity (lower).
    """
    if side not in {"lower", "upper"}:
        raise ValueError("side must be 'lower' or 'upper'")
    values = np.asarray(scores, dtype=np.float64).reshape(-1)
    if not np.isfinite(values).all():
        raise ValueError("conformal scores must be finite")
    n = values.size
    k = conformal_order_statistic(n, alpha)
    if n == 0 or k > n:
        return -math.inf if side == "lower" else math.inf
    ordered = np.sort(values)
    if side == "lower":
        return float(ordered[n - k])
    return float(ordered[k - 1])


def min_blocks_for_alpha(alpha: float) -> int:
    """Smallest calibration size for a finite ``1-alpha`` one-sided bound."""
    level = _alpha_fraction(alpha)
    return max(1, (level.denominator + level.numerator - 1) // level.numerator - 1)


def dkw_epsilon(n: int, alpha: float) -> float:
    """Massart's two-sided DKW radius for n iid draws at failure probability ``alpha``."""
    _alpha_fraction(alpha)
    if isinstance(n, (bool, np.bool_)) or int(n) != n or n < 0:
        raise ValueError("n must be a non-negative integer")
    if n == 0:
        return math.inf
    return math.sqrt(math.log(2.0 / float(alpha)) / (2.0 * int(n)))


def dkw_mean_lower_bound(
    scores: Any,
    alpha: float,
    *,
    support: tuple[float, float] = (0.0, 1.0),
) -> float:
    """A DKW lower bound on the mean of a fixed score population.

    Under iid sampling from a fixed score population, if scores lie in a *predeclared* interval
    [a,b], the CDF sup-norm bound implies an absolute mean error at most ``(b-a) * epsilon``.
    The interval must be known from the metric contract; using the observed sample range is not
    valid because it can understate the true population range. DTI is bounded by [0,1], so that
    support is the default. The result is clipped at the known lower endpoint, which is itself a
    valid deterministic lower bound. DKW's iid sampling assumption is stronger than conformal
    exchangeability and is not established for heterogeneous spatial blocks here.
    """
    values = _validated_dti(scores, "scores")
    if len(support) != 2:
        raise ValueError("support must be a (lower, upper) pair")
    lower, upper = (float(support[0]), float(support[1]))
    if not math.isfinite(lower) or not math.isfinite(upper) or lower >= upper:
        raise ValueError("support must be finite and strictly increasing")
    if ((values < lower) | (values > upper)).any():
        raise ValueError("scores fall outside the declared support")
    eps = dkw_epsilon(values.size, alpha)
    return max(lower, float(values.mean()) - (upper - lower) * eps)


@dataclass
class SweepPoint:
    """One fixed operating point and its DTI scores on disjoint spatial-block roles."""

    name: str
    params: dict
    calib_dtis: list[float] = dc_field(default_factory=list)
    select_dtis: list[float] = dc_field(default_factory=list)
    offcat_enrichment: float | None = None
    emitted: int = 0
    calibration_block_ids: list[int] = dc_field(default_factory=list)
    selection_block_ids: list[int] = dc_field(default_factory=list)

    @property
    def calib_mean(self) -> float:
        return float(np.mean(self.calib_dtis)) if self.calib_dtis else float("-inf")

    @property
    def select_mean(self) -> float:
        return float(np.mean(self.select_dtis)) if self.select_dtis else float("nan")


@dataclass
class ConformalSelection:
    """Chosen operating point and the scope/assumptions a reviewer must see."""

    chosen: str
    params: dict
    alpha: float
    n_calibration_blocks: int
    n_selection_blocks: int
    certified_floor: float
    calibration_mean: float
    calibration_min: float
    calibration_max: float
    calibration_dtis: list[float]
    selection_mean: float
    selection_dtis: list[float]
    selection_half_min_above_floor: bool | None
    dkw_epsilon: float
    mean_floor_dkw: float
    leave_one_out_worst_floor: float
    vacuous: bool
    calibration_block_ids: list[int]
    selection_block_ids: list[int]
    runner_up: list[dict] = dc_field(default_factory=list)

    @property
    def certified_confidence(self) -> float:
        return 1.0 - self.alpha

    def to_dict(self) -> dict:
        finite_floor = self.certified_floor if math.isfinite(self.certified_floor) else None
        finite_loo = (self.leave_one_out_worst_floor
                      if math.isfinite(self.leave_one_out_worst_floor) else None)
        return dict(
            chosen=self.chosen,
            params=self.params,
            alpha=self.alpha,
            certified_confidence_pct=round(100.0 * self.certified_confidence, 3),
            n_calibration_blocks=self.n_calibration_blocks,
            n_selection_blocks=self.n_selection_blocks,
            calibration_block_ids=self.calibration_block_ids,
            selection_block_ids=self.selection_block_ids,
            block_roles_disjoint=True,
            selected_by="selection-half mean DTI; calibration scores do not choose the candidate",
            certified_floor=finite_floor,
            vacuous=self.vacuous,
            calibration_mean=self.calibration_mean,
            calibration_min=self.calibration_min,
            calibration_max=self.calibration_max,
            calibration_dtis=self.calibration_dtis,
            selection_mean=self.selection_mean,
            selection_dtis=self.selection_dtis,
            selection_half_min_above_floor=self.selection_half_min_above_floor,
            selection_half_min_check_is_descriptive=True,
            dkw_epsilon=self.dkw_epsilon,
            mean_floor_dkw=self.mean_floor_dkw,
            dkw_support=[0.0, 1.0],
            dkw_support_was_predeclared=True,
            dkw_mean_floor_scope=(
                "calibration-population mean for the selected point under iid calibration sampling, "
                "selection-only choice, and a fixed candidate grid; not a one-block floor"
            ),
            dkw_mean_floor_valid_under_declared_assumptions=True,
            dkw_iid_sampling_verified=False,
            leave_one_out_worst_floor=finite_loo,
            candidate_grid_must_be_fixed_independently_of_calibration=True,
            exchangeability_verified=False,
            private_or_leaderboard_floor_certified=False,
            coverage_scope=(
                "one future exchangeable block's DTI for the selected operating point; not a block "
                "mean, pooled map DTI, geographic-conditional score, private label, or leaderboard score"
            ),
            exchangeability_note=(
                "Finite-sample coverage is conditional on exchangeability of calibration and future "
                "spatial blocks and on the candidate grid/selection rule being fixed independently "
                "of calibration outcomes. Geological exchangeability and prospective protocol "
                "fixation are assumptions, not verified by this calculation."
            ),
            runner_up=self.runner_up,
        )


def _validated_block_ids(ids: list[int], n: int, name: str) -> list[int]:
    if len(ids) != n:
        raise ValueError(f"{name} must contain one ID per DTI score")
    if any(isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer))
           for value in ids):
        raise ValueError(f"{name} must contain integer block IDs")
    normalized = [int(value) for value in ids]
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicate block IDs")
    return normalized


def select(sweep: list[SweepPoint], alpha: float = 0.10) -> ConformalSelection:
    """Choose on the selection half, then certify using only disjoint calibration scores.

    The candidate list and this selection rule must be fixed independently of calibration outcomes.
    This implementation maximizes selection-half mean DTI (then uses larger spacing and name as
    deterministic tie breaks) and computes a lower prediction bound only for the chosen candidate.
    It deliberately does not rank candidates by floors computed on the same calibration sample.
    """
    _alpha_fraction(alpha)
    if not sweep:
        raise ValueError("sweep must contain at least one operating point")
    names = [point.name for point in sweep]
    if any(not name for name in names) or len(set(names)) != len(names):
        raise ValueError("operating-point names must be nonempty and unique")

    validated = []
    expected_calibration_ids: list[int] | None = None
    expected_selection_ids: list[int] | None = None
    for point in sweep:
        calibration = _validated_dti(point.calib_dtis, f"{point.name} calibration scores")
        selection = _validated_dti(point.select_dtis, f"{point.name} selection scores")
        calibration_ids = _validated_block_ids(
            point.calibration_block_ids, calibration.size, f"{point.name} calibration_block_ids"
        )
        selection_ids = _validated_block_ids(
            point.selection_block_ids, selection.size, f"{point.name} selection_block_ids"
        )
        if set(calibration_ids) & set(selection_ids):
            raise ValueError(f"{point.name} calibration and selection block IDs overlap")
        if expected_calibration_ids is None:
            expected_calibration_ids = calibration_ids
            expected_selection_ids = selection_ids
        elif calibration_ids != expected_calibration_ids or selection_ids != expected_selection_ids:
            raise ValueError("all operating points must use identical ordered block-role IDs")
        spacing = point.params.get("min_dist", point.params.get("spacing_px", 0.0))
        try:
            spacing = float(spacing)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{point.name} spacing tie-break must be numeric") from exc
        if not math.isfinite(spacing):
            raise ValueError(f"{point.name} spacing tie-break must be finite")
        validated.append((point, calibration, selection, spacing))

    # This ranking never reads calibration scores. Larger spacing is only a deterministic tie break.
    validated.sort(key=lambda row: (-float(row[2].mean()), -row[3], row[0].name))
    best, calibration, selection, _ = validated[0]
    floor = conformal_quantile(calibration, alpha, side="lower")
    eps = dkw_epsilon(calibration.size, alpha)
    mean_floor = dkw_mean_lower_bound(calibration, alpha, support=(0.0, 1.0))
    loo_floors = [
        conformal_quantile(np.delete(calibration, i), alpha, side="lower")
        for i in range(calibration.size)
    ]
    runner_up = [
        dict(name=point.name, selection_mean=float(values.mean()), emitted=point.emitted)
        for point, _, values, _ in validated[1:6]
    ]
    return ConformalSelection(
        chosen=best.name,
        params=best.params,
        alpha=float(alpha),
        n_calibration_blocks=int(calibration.size),
        n_selection_blocks=int(selection.size),
        certified_floor=floor,
        calibration_mean=float(calibration.mean()),
        calibration_min=float(calibration.min()),
        calibration_max=float(calibration.max()),
        calibration_dtis=[float(value) for value in calibration],
        selection_mean=float(selection.mean()),
        selection_dtis=[float(value) for value in selection],
        selection_half_min_above_floor=(
            bool(selection.min() >= floor) if math.isfinite(floor) else None
        ),
        dkw_epsilon=eps,
        mean_floor_dkw=mean_floor,
        leave_one_out_worst_floor=float(min(loo_floors)),
        vacuous=not math.isfinite(floor),
        calibration_block_ids=list(expected_calibration_ids or []),
        selection_block_ids=list(expected_selection_ids or []),
        runner_up=runner_up,
    )
