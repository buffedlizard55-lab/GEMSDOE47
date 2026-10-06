"""The composite detector field: an explicit, reproducible recipe over the official bands.

A ``Recipe`` is a list of ``(band, transform, radius, weight)`` terms plus two optional
multiplicative gates.  Nothing is tuned implicitly: the recipe that produced the submission
is serialised into the submission bundle, so a reviewer can rebuild the exact field from the
exact numbers.

Why this form
-------------
Each term is rank-scaled to a uniform [0,1] marginal before combination, then the terms are
combined as a weighted geometric mean.  Two properties matter for this metric:

  * rank scaling makes the combination invariant to each transform's amplitude, which differs
    by orders of magnitude across bands (deq_n100a15 spans 0 to 4.96e6);
  * a geometric mean is an AND, not an OR.  A term that is near zero anywhere suppresses the
    field there.  For a metric that charges 0.2 per unit of prediction mass and pays only for
    the best-covering pixel, an AND of independent physical evidence is the correct way to
    buy precision -- and precision is the binding constraint here (see
    evidence/inversion/live_anchor_inversion.json: at the incumbent's 37,654 px the
    false-positive tax exceeds the earned credit).

The two gates
-------------
``vacancy`` (H47-A) multiplies by the rank of the physics-lineament density times
(1 - rank of the catalogue trace density), at a matched 800 m scale.  It is the term that
aims the field at MAPPING GAPS rather than at already-mapped traces, which are masked out of
evaluation and therefore worth zero.

``regional`` multiplies by a smooth (>= 2.5 km) prior built from the bands that carry no
300 m structure (geodetic strain rate, gravity, depth-to-basement, conductivity).  Those
bands cannot localise a fault, but they can veto one: a lineament-like topographic response
in a basin floor with no strain-rate or gravity expression is far more likely to be a stream
bank or a fan edge than a fault.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

from . import geomorph as G
from .spec import BAND_INDEX, FEATURE_INVALID_BELOW, HEIGHT, WIDTH

TRANSFORM_BY_NAME = G.TRANSFORMS


@dataclass
class Recipe:
    name: str
    terms: list[tuple[str, str, float, float]]        # (band, transform, radius, weight)
    use_vacancy: bool = False                         # H47-A gate
    vacancy_scale_px: float = 8.0
    vacancy_power: float = 1.0
    regional_bands: tuple[str, ...] = ()              # H47 regional veto prior
    regional_sigma_px: float = 25.0
    regional_power: float = 0.5
    notes: str = ""

    def to_dict(self) -> dict:
        return dict(name=self.name,
                    terms=[[b, t, float(r), float(w)] for b, t, r, w in self.terms],
                    use_vacancy=bool(self.use_vacancy),
                    vacancy_scale_px=float(self.vacancy_scale_px),
                    vacancy_power=float(self.vacancy_power),
                    regional_bands=list(self.regional_bands),
                    regional_sigma_px=float(self.regional_sigma_px),
                    regional_power=float(self.regional_power), notes=self.notes)

    @staticmethod
    def from_dict(d: dict) -> Recipe:
        return Recipe(name=d["name"], terms=[(b, t, float(r), float(w)) for b, t, r, w in d["terms"]],
                      use_vacancy=d.get("use_vacancy", False),
                      vacancy_scale_px=d.get("vacancy_scale_px", 8.0),
                      vacancy_power=d.get("vacancy_power", 1.0),
                      regional_bands=tuple(d.get("regional_bands", ())),
                      regional_sigma_px=d.get("regional_sigma_px", 25.0),
                      regional_power=d.get("regional_power", 0.5),
                      notes=d.get("notes", ""))


class Bands:
    """Lazy, cached access to the official 19-band stack on the pinned grid."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._cache: dict[str, np.ndarray] = {}

    def __call__(self, name: str) -> np.ndarray:
        """The band as float32 with the float32 nodata sentinel replaced by NaN.

        float32 is used deliberately: the sentinel -3.4028234663852886e38 is exactly the
        float32 minimum and so survives the cast, and caching 19 float64 bands would need
        1.9 GB against the 3 GB available in this environment.
        """
        if name not in self._cache:
            import rasterio
            with rasterio.open(self.path) as ds:
                a = ds.read(BAND_INDEX[name] + 1).astype(np.float32)
            a[~np.isfinite(a)] = np.nan
            a[a < np.float32(FEATURE_INVALID_BELOW)] = np.nan
            self._cache[name] = a
        return self._cache[name]

    def filled(self, name: str, valid: np.ndarray) -> np.ndarray:
        a = self(name)
        sel = valid & np.isfinite(a)
        med = float(np.median(a[sel])) if sel.any() else 0.0
        return np.where(sel, a, med).astype(np.float32)


def vacancy_gate(bands: Bands, valid: np.ndarray, catalogue: np.ndarray,
                 physics_field: np.ndarray, scale_px: float = 8.0,
                 power: float = 1.0) -> dict:
    """H47-A: rank(physics lineament density) x (1 - rank(catalogue trace density))."""
    fp = np.maximum(ndi.gaussian_filter(valid.astype(np.float32), scale_px, mode="nearest"), 1e-6)
    phys = ndi.gaussian_filter(np.where(valid, physics_field, 0.0).astype(np.float32),
                               scale_px, mode="nearest") / fp
    catd = ndi.gaussian_filter(catalogue.astype(np.float32), scale_px, mode="nearest") / fp
    Rp = G.rank_scale(np.where(valid, phys, np.nan))
    Rc = G.rank_scale(np.where(valid, catd, np.nan))
    gate = (Rp * (1.0 - Rc)).astype(np.float32)
    return dict(gate=(gate ** power).astype(np.float32), physics_rank=Rp, catalogue_rank=Rc)


def regional_gate(bands: Bands, valid: np.ndarray, names: tuple[str, ...],
                  sigma_px: float = 25.0, power: float = 0.5) -> np.ndarray:
    """A >= 2.5 km veto prior built from the bands that carry no 300 m structure."""
    if not names:
        return None
    acc = None
    for n in names:
        p = G.regional_prior(bands(n), valid, sigma=sigma_px)
        acc = p if acc is None else np.maximum(acc, p)
    acc = np.clip(acc, 0.0, 1.0)
    # a floor of 0.15 so the prior can modulate but never fully veto
    return ((0.15 + 0.85 * acc) ** power).astype(np.float32)


def build_core(recipe: Recipe, bands: Bands, valid: np.ndarray,
               want_terms: bool = False) -> dict:
    """The label-free part of a recipe: the weighted geometric mean of rank-scaled terms.

    Cached across holdout blocks, because it does not depend on which catalogue pixels are
    visible.  Only the H47-A vacancy gate does.
    """
    terms = {}
    wsum = 0.0
    logacc = np.zeros((HEIGHT, WIDTH), np.float64)
    for band, tname, radius, w in recipe.terms:
        fn = TRANSFORM_BY_NAME[tname]
        z = bands.filled(band, valid)
        t = np.asarray(fn(z, radius), np.float32)
        t = G.rank_scale(np.where(valid & np.isfinite(t), t, np.nan))
        terms[f"{band}:{tname}:{radius:g}"] = t
        logacc += float(w) * np.log(np.clip(t, 1e-6, None))
        wsum += float(w)
    core = np.exp(logacc / max(wsum, 1e-9)).astype(np.float32)
    core = np.where(valid, core, 0.0).astype(np.float32)
    # A weighted geometric mean of float32 terms collides: distinct terms can round to the same
    # product.  Re-ranking makes the composite a total order, which the emitter's spacing
    # guarantee relies on (see emission.nms_disk).  Rank is a monotone transform, so this
    # changes nothing about which pixels are selected, only that ties are broken deterministically.
    core = np.where(valid, G.rank_scale(np.where(valid, core, np.nan)), 0.0).astype(np.float32)
    out = dict(core=core, recipe=recipe.to_dict())
    if want_terms:
        out["terms"] = terms
    return out


def build_field(recipe: Recipe, bands: Bands, valid: np.ndarray, catalogue: np.ndarray,
                core: np.ndarray | None = None, want_terms: bool = False) -> dict:
    """Full composite field: core x H47-A vacancy gate x regional veto prior."""
    if core is None:
        built = build_core(recipe, bands, valid, want_terms)
        core = built["core"]
    else:
        built = dict(core=core, recipe=recipe.to_dict())
    rg = regional_gate(bands, valid, recipe.regional_bands, recipe.regional_sigma_px,
                       recipe.regional_power)
    field = core.astype(np.float32) if rg is None else (core * rg).astype(np.float32)
    vg = None
    if recipe.use_vacancy:
        vg = vacancy_gate(bands, valid, catalogue, core, recipe.vacancy_scale_px,
                          recipe.vacancy_power)
        field = (field * vg["gate"]).astype(np.float32)
    field = np.where(valid, np.clip(field, 0.0, 1.0), 0.0).astype(np.float32)
    # Multiplying by a gate re-introduces float32 collisions even though `core` is a total order
    # (measured: 4,901,339 distinct values out of 5,164,300 valid pixels with both gates on).
    # Re-rank so every recipe, gated or not, hands the emitter a total order -- the emitter's
    # spacing guarantee depends on it.  Rank is monotone, so the selected pixel SET is unchanged;
    # only tie-breaking becomes deterministic.
    if recipe.use_vacancy or recipe.regional_bands:
        field = np.where(valid, G.rank_scale(np.where(valid, field, np.nan)),
                         0.0).astype(np.float32)
    out = dict(field=field, core=core, vacancy=vg, regional=rg, recipe=recipe.to_dict())
    if want_terms and "terms" in built:
        out["terms"] = built["terms"]
    return out


def save_recipe(recipe: Recipe, path: Path) -> Path:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(recipe.to_dict(), indent=2))
    return p
