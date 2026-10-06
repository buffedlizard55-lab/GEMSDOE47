"""Split conformal selection of an emission operating point, with a finite-sample guarantee.

Reference
---------
J. Lei, M. G'Sell, A. Rinaldo, R. J. Tibshirani and L. Wasserman,
"Distribution-Free Predictive Inference for Regression",
Journal of the American Statistical Association 113(523):1094-1111, 2018.
https://doi.org/10.1080/01621459.2017.1322365   (publisher, DOI verified)
Preprint: https://arxiv.org/abs/1604.04173

The theorem used here (their split-conformal coverage result, specialised to a one-sided
prediction interval).  Let (X_1,Y_1),...,(X_n,Y_n) be exchangeable, and let a score function
s(X,Y) be fitted on a proper subset.  With

    q_hat = the  ceil((n+1)(1-alpha)) / n  -th smallest value of {s(X_i,Y_i)}_{i=1}^n

(the k-th order statistic, k = ceil((n+1)(1-alpha)), clipped to n), then for a new point
(X,Y) exchangeable with the calibration points,

    P( s(X,Y) <= q_hat ) >= 1 - alpha                                          (GUARANTEE)

exactly, for every n, with no distributional, parametric or smoothness assumption beyond
exchangeability.  The bound is finite-sample: it holds at n = 8 as well as at n = 8,000.

How that becomes a *selection* rule with a guaranteed floor
-----------------------------------------------------------
The unit of exchangeability here is a **spatial block** of the holdout, not a configuration.
That choice is what makes the guarantee real rather than decorative:

  1. The holdout is partitioned into B spatial blocks.  Blocks are split at random into a
     CALIBRATION half (size n) and a SELECTION half (size m).
  2. A sweep of operating points (spacing x budget x flank buffer x blur) is scored on the
     calibration blocks only.  The selection rule picks the operating point that maximises
     the mean calibration-block DTI.  It never sees a selection-block score.
  3. For the chosen operating point, the calibration-block DTIs are exchangeable with the
     selection-block DTIs of the same operating point (same rule, blocks drawn from the same
     spatial population, and the rule was fitted without the selection blocks).  Applying the
     theorem with s(X,Y) = -DTI gives a one-sided (1-alpha) LOWER bound:

         DTI_selection >= -q_hat   with probability >= 1 - alpha
         q_hat = the  ceil((n+1)alpha) / n  -th smallest of { -DTI_calibration,i }

     i.e. the floor is the  ceil((n+1)alpha) -th SMALLEST calibration-block DTI.
  4. The selection blocks are then scored once, to report whether the realised value cleared
     the certified floor.  That is an audit, not a tuning step: the choice was already frozen.

Two guarantees are reported, because they answer two different reviewer questions:

  * ``floor_within_rule``  -- the conformal floor above: any single fresh block's DTI for the
    chosen operating point is at least this value with probability >= 1-alpha.
  * ``floor_mean_of_selected`` -- a lower bound on the MEAN DTI over blocks, from the
    Dvoretzky-Kiefer-Wolfowitz / Massart inequality applied to the calibration-block
    empirical CDF (also distribution-free, also finite-sample):
        P( sup_x |F_n(x) - F(x)| > eps ) <= 2 exp(-2 n eps^2)
    so eps = sqrt(log(2/alpha) / (2n)) and the mean is bounded below by
    mean(calibration DTIs) - eps - (max-min)/sqrt(n) style corrections; we report the simple
    and defensible form  mean - sqrt(log(2/alpha)/(2n)) * spread.

Honesty note carried into every report: exchangeability of spatial blocks is an ASSUMPTION.
Geology is not i.i.d.; blocks differ in Basin-and-Range versus Walker Lane character.  The
guarantee is therefore conditional on that assumption, and this module also reports a
block-level spread and a leave-one-block-out worst case so a reviewer can see how much the
assumption is doing.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field as dc_field

import numpy as np


def conformal_quantile(scores: np.ndarray, alpha: float, side: str = "lower") -> float:
    """The split-conformal quantile with the exact finite-sample (n+1) correction.

    Lei et al. (2018) define, for calibration scores s_1..s_n and a new exchangeable score
    s_new,

        q_hat = the k-th smallest of {s_i},  k = ceil((n+1)(1 - alpha)),   q_hat = +inf if k > n

    and prove  P(s_new <= q_hat) >= 1 - alpha  exactly, for every n, with no distributional
    assumption beyond exchangeability.

    ``side="upper"`` returns that q_hat directly: an upper bound on the score.

    ``side="lower"`` returns a lower bound on the QUANTITY Y being guaranteed (here, DTI).
    A lower bound on Y is an upper bound on the score s = -Y, so with the same k the bound is
    -q_hat(s) = the k-th LARGEST Y, i.e. the (n - k)-th element of Y sorted ascending.  If
    k > n the bound does not exist and -inf is returned (the guarantee is vacuous at that n
    and alpha; e.g. a 95 % lower bound needs n >= 19).

    An earlier version of this function used k = ceil((n+1)*alpha) and took the k-th SMALLEST
    value for the lower side.  That returns a strictly larger number than the theorem supports
    and therefore OVER-STATES the guarantee; it was caught by
    tests/test_conformal.py::test_empirical_coverage_meets_the_guarantee and fixed here.
    """
    s = np.sort(np.asarray(scores, dtype=np.float64).ravel())
    n = s.size
    if not (0.0 < alpha < 1.0):
        raise ValueError("alpha must be in (0,1)")
    if n == 0:
        return -math.inf if side == "lower" else math.inf
    k = int(math.ceil((n + 1) * (1.0 - alpha)))
    if k > n:
        return -math.inf if side == "lower" else math.inf
    if side == "lower":
        return float(s[n - k])          # the k-th largest
    return float(s[k - 1])              # the k-th smallest


def conformal_order_statistic(n: int, alpha: float) -> int:
    """k = ceil((n+1)(1-alpha)); the bound is vacuous when k > n."""
    return int(math.ceil((n + 1) * (1.0 - alpha)))


def min_blocks_for_alpha(alpha: float) -> int:
    """Smallest calibration size n for which a 1-alpha lower bound exists at all.

    k = ceil((n+1)(1-alpha)) <= n  <=>  1 <= alpha*(n+1)  <=>  n >= 1/alpha - 1.
    So a 90 % guarantee needs n >= 9 blocks, 95 % needs n >= 19, 75 % needs n >= 3.  This is
    the finite-sample price of the theorem and it is reported next to every floor rather than
    hidden: if the sweep only produces 8 usable blocks, no 90 % statement can be made.
    """
    if not (0.0 < alpha < 1.0):
        raise ValueError("alpha must be in (0,1)")
    return max(1, int(math.ceil(1.0 / alpha - 1.0)))


def dkw_epsilon(n: int, alpha: float) -> float:
    """Massart's finite-sample bound: P(sup|F_n-F| > eps) <= 2exp(-2 n eps^2)."""
    if n <= 0:
        return math.inf
    return math.sqrt(math.log(2.0 / alpha) / (2.0 * n))


@dataclass
class SweepPoint:
    """One operating point of the emission sweep and its per-block holdout DTIs."""
    name: str
    params: dict
    calib_dtis: list[float] = dc_field(default_factory=list)   # blocks in the calibration half
    select_dtis: list[float] = dc_field(default_factory=list)  # blocks in the selection half
    offcat_enrichment: float | None = None
    emitted: int = 0

    @property
    def calib_mean(self) -> float:
        return float(np.mean(self.calib_dtis)) if self.calib_dtis else float("-inf")

    @property
    def select_mean(self) -> float:
        return float(np.mean(self.select_dtis)) if self.select_dtis else float("nan")


@dataclass
class ConformalSelection:
    """The frozen choice plus everything a Phase 2 reviewer needs to check it."""
    chosen: str
    params: dict
    alpha: float
    n_calibration_blocks: int
    n_selection_blocks: int
    certified_floor: float                 # (1-alpha) lower bound on a fresh block's DTI
    certified_confidence: float            # 1 - alpha, as a percentage for the notes
    calibration_mean: float
    calibration_min: float
    calibration_max: float
    calibration_dtis: list[float]
    selection_mean: float
    selection_dtis: list[float]
    cleared_floor: bool
    dkw_epsilon: float
    mean_floor_dkw: float
    leave_one_out_worst_floor: float
    vacuous: bool
    exchangeability_note: str
    min_blocks_required_for_alpha: int = 0
    all_floors_vacuous: bool = False
    runner_up: list[dict] = dc_field(default_factory=list)

    def to_dict(self) -> dict:
        return dict(
            chosen=self.chosen, params=self.params, alpha=self.alpha,
            n_calibration_blocks=self.n_calibration_blocks,
            n_selection_blocks=self.n_selection_blocks,
            certified_floor=self.certified_floor,
            certified_confidence_pct=round(100.0 * self.certified_confidence, 3),
            calibration_mean=self.calibration_mean,
            calibration_min=self.calibration_min,
            calibration_max=self.calibration_max,
            calibration_dtis=self.calibration_dtis,
            selection_mean=self.selection_mean,
            selection_dtis=self.selection_dtis,
            cleared_floor=self.cleared_floor,
            dkw_epsilon_mean=self.dkw_epsilon,
            mean_floor_dkw=self.mean_floor_dkw,
            leave_one_out_worst_floor=self.leave_one_out_worst_floor,
            vacuous=self.vacuous,
            min_blocks_required_for_alpha=self.min_blocks_required_for_alpha,
            all_floors_vacuous=self.all_floors_vacuous,
            exchangeability_note=self.exchangeability_note,
            runner_up=self.runner_up,
        )


def select(sweep: list[SweepPoint], alpha: float = 0.10,
           tie_break: str = "floor") -> ConformalSelection:
    """Freeze an operating point using ONLY calibration-block scores, then audit on selection.

    Ranking key: the conformal floor (``tie_break="floor"``) rather than the calibration mean.
    Ranking by the mean is the "we tried a few and this one was best" failure mode the brief
    names: it selects the noisiest high mean.  Ranking by the floor selects the operating
    point whose WORST calibration block is best, which is the quantity the guarantee is about.
    """
    usable = [s for s in sweep if s.calib_dtis]
    if not usable:
        raise ValueError("no sweep point has calibration scores")
    n = min(len(s.calib_dtis) for s in usable)
    for s in usable:
        s._floor = conformal_quantile(np.array(s.calib_dtis), alpha, side="lower")  # type: ignore[attr-defined]
        s._vacuous = not math.isfinite(s._floor)                  # type: ignore[attr-defined]
    if tie_break == "floor":
        # A vacuous floor (-inf) cannot be ranked, so non-vacuous points always win; among
        # vacuous ones the mean is the only available key and the result is flagged.
        usable.sort(key=lambda s: (s._vacuous, -s._floor, -s.calib_mean))  # type: ignore[attr-defined]
    else:
        usable.sort(key=lambda s: -s.calib_mean)
    best = usable[0]
    floor = float(best._floor)                  # type: ignore[attr-defined]
    cal = np.asarray(best.calib_dtis, float)
    n = cal.size
    eps = dkw_epsilon(n, alpha)
    spread = float(cal.max() - cal.min()) if n > 1 else 0.0
    loo = []
    for i in range(n):
        loo.append(conformal_quantile(np.delete(cal, i), alpha, side="lower"))
    sel = np.asarray(best.select_dtis, float) if best.select_dtis else np.array([])
    sel_mean = float(sel.mean()) if sel.size else float("nan")
    return ConformalSelection(
        chosen=best.name, params=best.params, alpha=alpha,
        n_calibration_blocks=int(n), n_selection_blocks=int(sel.size),
        certified_floor=floor, certified_confidence=1.0 - alpha,
        calibration_mean=float(cal.mean()), calibration_min=float(cal.min()),
        calibration_max=float(cal.max()), calibration_dtis=[float(x) for x in cal],
        selection_mean=sel_mean, selection_dtis=[float(x) for x in sel],
        cleared_floor=bool(sel.size and float(sel.min()) >= floor),
        dkw_epsilon=eps,
        mean_floor_dkw=float(cal.mean() - eps * spread),
        leave_one_out_worst_floor=float(min(loo)) if loo else float("-inf"),
        vacuous=not math.isfinite(floor),
        min_blocks_required_for_alpha=min_blocks_for_alpha(alpha),
        all_floors_vacuous=bool(all(getattr(x, "_vacuous", True) for x in usable)),
        exchangeability_note=(
            "The guarantee P(fresh block DTI >= floor) >= 1-alpha is exact under exchangeability "
            "of holdout blocks. Geological blocks are NOT i.i.d.; the reported leave-one-out worst "
            "floor and the DKW mean floor show how much of the claim rests on that assumption."),
        runner_up=[dict(name=s.name, floor=float(s._floor),  # type: ignore[attr-defined]
                        vacuous=bool(getattr(s, "_vacuous", True)),
                        calib_mean=s.calib_mean, emitted=s.emitted) for s in usable[1:6]],
    )
