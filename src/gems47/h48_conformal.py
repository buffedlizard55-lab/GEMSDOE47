"""Split conformal selection and certification for the GEMS emission sweep.

Why this module exists
----------------------
Every operating point this project has ever chosen was chosen by *eyeballing a
sweep*: "d2.8 beat d1.5, so pick d2.8".  An observed maximum of a finite sweep is
not a guarantee; it is the largest of a set of noisy numbers, and its optimism is
exactly the quantity that has burned this family before (the measured
optimizer's curse in ``evidence/crossfit_validation.json`` is ~0.30 DTI).

This module implements the honest alternative requested in the standing brief:
**split conformal prediction** in the sense of Lei, G'Sell, Rinaldo, Tibshirani &
Wasserman (JASA 2018), *"Distribution-Free Predictive Inference for Regression"*,
https://doi.org/10.1080/01621459.2017.1307116 (open copy:
https://arxiv.org/abs/1604.04173), applied to the leaderboard-return sweep.

The construction
----------------
1.  A *belief model* q maps a candidate emission field to a predicted public-test
    DTI, ``DTI_hat`` (see ``gems47.lati`` for the estimator: ``T = <q, w>``
    exactly, ``F = S - Phi``, ``K = <q, 1>``).
2.  The same model is evaluated against the **measured** DTIs of the previously
    submitted rasters.  The absolute residuals ``r_i = |DTI_i - DTI_hat_i|`` are
    the calibration scores.
3.  The observations are split into a **calibration half** and a **selection
    half**.  The calibration half yields the conformal quantile
    ``q_hat = r_(k)`` with ``k = ceil((n+1)(1-alpha))`` (Lei et al. 2018, eq. 2.6;
    Vovk et al. 2005, ch. 2.2).  The selection half never enters the quantile.
4.  The assumption-conditional lower bound for any new candidate is
    ``LCB = DTI_hat(candidate) - q_hat``, and ``LCB <= DTI_true`` with probability
    at least ``1 - alpha`` **if** the calibration scores and the new candidate's
    score are exchangeable.
5.  Selecting the best member of a *fixed, pre-declared* family of ``m``
    candidates inflates the error probability by at most a factor ``m``: using
    ``alpha' = alpha / m`` (Bonferroni) keeps ``P(for all i, LCB_i <= DTI_i) >= 1 -
    alpha``, so the selected candidate's bound is still valid.  This is what makes
    "pick the best spacing, then report its assumption-conditional lower bound" legitimate.

What is **not** claimed
-----------------------
*   Exchangeability is an assumption, not a theorem.  The thirteen observations
    are largely *nested thinnings of one field*, so they are not independent
    draws from the same distribution as a brand-new candidate.  Every number this
    module produces is therefore reported as an **assumption-conditional**
    bound, per the standing hard requirement #3 ("Never call an
    assumption-conditional result a distribution-free guarantee for private
    labels or a leaderboard score").
*   The bound is a bound on the *public-test* DTI of the probe raster, which is
    the only quantity the leaderboard reports.  It is **not** a bound on the
    private-test score, and it is not a claim about the Final Prize Round label
    set.
*   ``q_hat = +inf`` whenever the requested level needs a rank beyond the
    calibration set (``k > n``): with ``n`` calibration points the maximum
    reliable level is ``1 - 1/(n+1)``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

__all__ = [
    "CertifiedCandidate",
    "SplitConformal",
    "conformal_coverage_report",
    "conformal_quantile",
    "conformal_rank",
    "jackknife_plus_residuals",
    "lower_quantile",
    "max_level",
    "min_alpha",
    "min_alpha_family",
    "select_by_certified_floor",
    "select_by_conditional_lower_bound",
]


def lower_quantile(residuals, alpha: float) -> float:
    """One-sided split-conformal quantile of the **signed** residuals.

    With ``R_i = Y_i - Yhat_i`` and ``k = ceil((n+1)(1-alpha))``, the lower bound
    ``Yhat_new - R_(k)`` covers ``Y_new`` from below with probability at least
    ``1 - alpha`` (Vovk et al. 2005 ch. 2.2; Lei et al. 2018 eq. 2.6).  Written
    in terms of the signed residual of the *prediction* (``Y - Yhat``) the same
    statement is

        LCB = Yhat_new + E_(n-k+1)   where E = (Y - Yhat) sorted ascending.

    A one-sided bound is strictly sharper than subtracting the absolute-residual
    quantile, and it is the correct object here: the belief model is known to be
    one-signed (it under-predicts the strong fields, see
    ``evidence/h48_build.json``), and a two-sided absolute bound would charge the
    candidate for a bias that runs in the safe direction.

    Returns ``-inf`` when the level is not attainable with ``n`` points.
    """
    e = np.sort(np.asarray(residuals, dtype=np.float64).ravel())
    n = e.size
    k = conformal_rank(n, alpha)
    if n == 0 or k < 1 or k > n:
        return -math.inf            # alpha >= 1 or level beyond 1-1/(n+1): vacuous
    return float(e[n - k])          # the (n-k+1)-th smallest, 1-based


def min_alpha_family(n: int, n_candidates: int) -> float:
    """Smallest family error rate a calibration set of ``n`` can certify.

    Each candidate needs ``alpha' >= 1/(n+1)``; Bonferroni over ``m`` candidates
    therefore costs ``alpha >= m/(n+1)``.  This is the price of *choosing* an
    operating point from a sweep, and it is reported rather than hidden.
    """
    if n <= 0:
        return 1.0
    return min(1.0, max(n_candidates, 1) / (n + 1.0))


# ---------------------------------------------------------------------------
# elementary split-conformal machinery
# ---------------------------------------------------------------------------


def conformal_rank(n: int, alpha: float) -> int:
    """``k = ceil((n+1)(1-alpha))`` — the order statistic split conformal uses.

    Lei et al. (2018) eq. 2.6: the split-conformal interval
    ``C_hat(x) = [mu_hat(x) - R_(k), mu_hat(x) + R_(k)]`` with ``k =
    ceil((n+1)(1-alpha))`` and ``R_(1) <= ... <= R_(n)`` the sorted absolute
    residuals satisfies ``P(Y in C_hat(X)) >= 1 - alpha`` under exchangeability.
    """
    if n <= 0:
        return math.inf
    return math.ceil((n + 1) * (1.0 - alpha))


def max_level(n: int) -> float:
    """Largest level ``1-alpha`` a calibration set of size ``n`` can certify.

    ``k = n`` requires ``ceil((n+1)(1-alpha)) <= n``, i.e. ``alpha >= 1/(n+1)``.
    """
    if n <= 0:
        return 0.0
    return 1.0 - 1.0 / (n + 1)


def min_alpha(n: int) -> float:
    """Smallest ``alpha`` (== most confident level) attainable with ``n`` points."""
    if n <= 0:
        return 1.0
    return 1.0 / (n + 1)


def conformal_quantile(residuals, alpha: float) -> float:
    """``q_hat`` = the ``ceil((n+1)(1-alpha))``-th smallest absolute residual.

    Returns ``+inf`` when the requested level is not attainable with the given
    calibration size (the honest answer: no finite guarantee).
    """
    r = np.sort(np.abs(np.asarray(residuals, dtype=np.float64).ravel()))
    n = r.size
    k = conformal_rank(n, alpha)
    if n == 0 or k < 1 or k > n:
        return math.inf
    return float(r[k - 1])


# ---------------------------------------------------------------------------
# the split itself, plus the guarantee bookkeeping
# ---------------------------------------------------------------------------


@dataclass
class SplitConformal:
    """A calibrated split-conformal lower-bound machine for one metric.

    ``cal`` / ``sel`` are index arrays into the observation list.  ``alpha`` is
    the *family* error rate (before the Bonferroni division by the number of
    candidates), so ``level_used = 1 - alpha`` is the number a reviewer can
    check.
    """

    residuals: np.ndarray            # signed (observed - predicted) on the calibration half
    sel_residuals: np.ndarray        # same quantity on the selection half (diagnostic only)
    n_candidates: int = 1            # size of the swept family the selection ran over
    alpha: float = 0.125             # family error rate; divided by n_candidates for the bound
    cal_ids: list = field(default_factory=list)
    sel_ids: list = field(default_factory=list)
    one_sided: bool = True
    alpha_used_override: float | None = None

    @property
    def residuals_abs(self) -> np.ndarray:
        return np.abs(np.asarray(self.residuals, dtype=np.float64))

    @property
    def alpha_used(self) -> float:
        """Per-candidate error rate actually certified (clipped to [0, 1]).

        ``alpha_used_override`` is used when the caller has already applied the
        Bonferroni family correction (see ``min_alpha_family``), which is the
        honest way to spend confidence across a sweep: with ``n`` calibration
        scores no member of an ``m``-candidate family can be certified at a level
        above ``1 - m/(n+1)``.
        """
        if self.alpha_used_override is not None:
            return min(1.0, max(float(self.alpha_used_override), 0.0))
        return min(1.0, max(self.alpha, 0.0) / max(self.n_candidates, 1))

    @property
    def level_used(self) -> float:
        """Confidence level actually certified, after the family correction."""
        return 1.0 - self.alpha_used

    @property
    def n_cal(self) -> int:
        return int(np.size(self.residuals))

    @property
    def quantile(self) -> float:
        """Signed residual quantile (one-sided) or absolute residual quantile."""
        if self.one_sided:
            return lower_quantile(self.residuals, self.alpha_used)
        return conformal_quantile(self.residuals, self.alpha_used)

    @property
    def certified(self) -> bool:
        """False when the requested level needs more calibration points than exist."""
        return math.isfinite(self.quantile)

    def lcb(self, predicted: float) -> float:
        """Assumption-conditional lower bound on public-test DTI under exchangeability."""
        if self.one_sided:
            return float(predicted) + self.quantile
        return float(predicted) - self.quantile

    def empirical_coverage(self, predicted, observed) -> float:
        """Fraction of points whose observed value lies above the certified bound.

        Reported for the *selection* half only.  It is a diagnostic, not the
        guarantee: the guarantee is the finite-sample statement ``P >= 1-alpha``.
        """
        pred = np.asarray(predicted, dtype=np.float64)
        obs = np.asarray(observed, dtype=np.float64)
        if pred.size == 0:
            return float("nan")
        return float(np.mean(obs >= pred + self.quantile))

    def to_dict(self) -> dict:
        q = self.quantile
        return {
            "alpha_family": self.alpha,
            "n_candidates": int(self.n_candidates),
            "alpha_used": self.alpha_used,
            "level_used": self.level_used,
            "level_used_pct": round(100.0 * self.level_used, 3),
            "one_sided": bool(self.one_sided),
            "n_calibration": self.n_cal,
            "n_selection": int(np.size(self.sel_residuals)),
            "max_attainable_level": max_level(self.n_cal),
            "min_alpha_for_this_family": min_alpha_family(self.n_cal, self.n_candidates),
            "conformal_rank_k": conformal_rank(self.n_cal, self.alpha_used),
            "quantile": (None if not math.isfinite(q) else q),
            "certified": self.certified,
            "calibration_ids": list(self.cal_ids),
            "selection_ids": list(self.sel_ids),
            "calibration_residuals": [float(v) for v in np.ravel(self.residuals)],
            "selection_residuals": [float(v) for v in np.ravel(self.sel_residuals)],
            "assumption": (
                "Exchangeability of the calibration scores and the candidate's score. "
                "The calibration observations are previous submissions, several of them "
                "nested thinnings of one field, so this is an ASSUMPTION-CONDITIONAL "
                "bound on the public-test DTI of a probe raster - not a distribution-free "
                "guarantee for the private test set, the Final Prize Round label set, or a "
                "leaderboard rank."
            ),
            "method_citation": (
                "Lei, G'Sell, Rinaldo, Tibshirani & Wasserman (2018), 'Distribution-Free "
                "Predictive Inference for Regression', JASA 113(523):1094-1111, "
                "doi:10.1080/01621459.2017.1307116 (arXiv:1604.04173), eq. (2.6)."
            ),
        }


# ---------------------------------------------------------------------------
# selection over a fixed candidate family
# ---------------------------------------------------------------------------


@dataclass
class CertifiedCandidate:
    name: str
    predicted: float
    lcb: float
    payload: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"name": self.name, "predicted_dti": self.predicted,
                "assumption_conditional_lower_bound": self.lcb, **self.payload}


def select_by_conditional_lower_bound(candidates, sc: SplitConformal) -> CertifiedCandidate:
    """Select the greatest assumption-conditional lower bound from a fixed family.

    The finite-sample statement applies only under the exchangeability and
    calibration assumptions recorded in ``sc``; it is not a distribution-free
    private-score floor or an upload gate.
    """
    if not candidates:
        raise ValueError("no candidates")
    return max(candidates, key=lambda c: c.lcb)


def select_by_certified_floor(candidates, sc: SplitConformal) -> CertifiedCandidate:
    """Deprecated compatibility alias; the output is assumption-conditional."""
    return select_by_conditional_lower_bound(candidates, sc)


def conformal_coverage_report(sc: SplitConformal, predicted, observed, ids=None) -> dict:
    """Coverage diagnostics on the selection half (never used to set the bound)."""
    pred = np.asarray(predicted, np.float64)
    obs = np.asarray(observed, np.float64)
    above = obs >= pred - sc.quantile
    return {
        "n": int(pred.size),
        "covered": int(above.sum()),
        "fraction": float(above.mean()) if pred.size else float("nan"),
        "nominal_level": 1.0 - sc.alpha_used,
        "ids": list(ids) if ids is not None else [],
        "note": (
            "Selection-half coverage is a diagnostic only. The guarantee is the "
            "finite-sample statement P(covered) >= 1 - alpha_used under exchangeability."
        ),
    }


def jackknife_plus_residuals(predict_loo, observed) -> np.ndarray:
    """Leave-one-out residuals for the cross-conformal (jackknife+) bound.

    ``predict_loo[i]`` must be the prediction for observation ``i`` produced by a
    model fitted **without** observation ``i``.  With ``n`` observations this
    yields ``n`` calibration scores instead of the ``n/2`` a single split
    provides, at the price of a factor two in the guarantee: the jackknife+
    interval of Barber, Candes, Ramdas & Tibshirani (2019),
    https://arxiv.org/abs/1905.02928, covers with probability at least
    ``1 - 2*alpha`` rather than ``1 - alpha``.  Both numbers are reported.
    """
    pred = np.asarray(predict_loo, dtype=np.float64)
    obs = np.asarray(observed, dtype=np.float64)
    return obs - pred
