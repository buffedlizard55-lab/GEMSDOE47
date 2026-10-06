"""Canonical geomorphometric transforms, at the metric's own 300 m scale.

These are the transforms ``scripts/transform_search.py`` scored and ``src/gems47s3/detector.py``
composes.  They live in the package (not in the script) so that the field used for the
submission is byte-identical to the field that was scored -- a substitution in one place and
not the other is the single most likely way to ship something different from what was
validated.

Only transforms that respond to structure AT the metric's kernel support (3 px = 300 m) are
here.  ``scripts/diagnose_bands.py`` measured that 16 of the 19 official bands are >96.5 %
smooth above that scale, so a transform of them cannot localise a fault; they are kept in the
package as explicit regional-prior helpers instead (``regional_prior``).
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

# Four strikes as (along-strike dy, dx).  The across-strike normal is (-dx, dy).
STRIKES = ((0, 1), (1, 0), (1, 1), (1, -1))
DIRS8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def disk(radius: float) -> np.ndarray:
    ri = int(np.ceil(radius))
    dy, dx = np.mgrid[-ri:ri + 1, -ri:ri + 1]
    return (dy * dy + dx * dx) <= radius * radius + 1e-9


# --------------------------------------------------------------------- line / edge responses
def line_response(z: np.ndarray, sigma: float) -> np.ndarray:
    """Frangi/Sato line response: -lambda_min of the Hessian, sign-symmetric.

    A magnetic low and a magnetic high can mark the same contact, so polarity is discarded by
    taking the eigenvalue of least magnitude with a positive sign convention.
    """
    s = max(float(sigma), 0.7)
    axx = ndi.gaussian_filter(z, s, order=(0, 2), mode="nearest")
    ayy = ndi.gaussian_filter(z, s, order=(2, 0), mode="nearest")
    axy = ndi.gaussian_filter(z, s, order=(1, 1), mode="nearest")
    disc = np.sqrt(np.maximum(((axx - ayy) * 0.5) ** 2 + axy ** 2, 0.0))
    l1 = (axx + ayy) * 0.5 + disc
    l2 = (axx + ayy) * 0.5 - disc
    return (-np.where(np.abs(l1) >= np.abs(l2), l2, l1)).astype(np.float32)


def curvature(z: np.ndarray, sigma: float) -> np.ndarray:
    """Absolute mean curvature smoothed at ``sigma``."""
    s = max(float(sigma), 1.0)
    return np.abs(ndi.gaussian_filter(z, s, order=(2, 0), mode="nearest")
                  + ndi.gaussian_filter(z, s, order=(0, 2), mode="nearest")).astype(np.float32)


def scarp_step(z: np.ndarray, halfwidth: int) -> np.ndarray:
    """Across-strike elevation contrast, persisted along strike; max over four strikes.

    The physically correct detector for a normal-fault scarp: a straight, laterally persistent
    STEP.  Curvature and openness respond to any convex or concave feature (canyon rims,
    stream banks, fan edges) and cannot distinguish a step from a bend.
    """
    ri = max(1, int(np.ceil(halfwidth)))
    best = np.zeros(z.shape, np.float32)
    for sy, sx in STRIKES:
        ny, nx = -sx, sy
        a = np.zeros(z.shape, np.float32)
        b = np.zeros(z.shape, np.float32)
        for t in range(1, ri + 1):
            a += ndi.shift(z, (-t * ny, -t * nx), order=1, mode="nearest").astype(np.float32)
            b += ndi.shift(z, (t * ny, t * nx), order=1, mode="nearest").astype(np.float32)
        step = np.abs(a - b) / (2.0 * ri)
        L = 2 * ri + 1
        if (sy, sx) == (0, 1):
            step = ndi.uniform_filter1d(step, L, axis=1, mode="nearest")
        elif (sy, sx) == (1, 0):
            step = ndi.uniform_filter1d(step, L, axis=0, mode="nearest")
        else:
            acc = np.zeros_like(step)
            for t in range(-ri, ri + 1):
                acc += ndi.shift(step, (t * sy, t * sx), order=0, mode="nearest")
            step = acc / L
        np.maximum(best, step.astype(np.float32), out=best)
    return best


def signed_scarp_step(z: np.ndarray, halfwidth: int) -> np.ndarray:
    """``scarp_step`` keeping the sign of the dominant-orientation step (H47-E form).

    The sign distinguishes which side is up, so a fault is separable from a symmetric fold or
    a lithologic edge; sign reversals along a strike locate segment boundaries.
    """
    ri = max(1, int(np.ceil(halfwidth)))
    best_mag = np.zeros(z.shape, np.float32)
    best_signed = np.zeros(z.shape, np.float32)
    for sy, sx in STRIKES:
        ny, nx = -sx, sy
        a = np.zeros(z.shape, np.float32)
        b = np.zeros(z.shape, np.float32)
        for t in range(1, ri + 1):
            a += ndi.shift(z, (-t * ny, -t * nx), order=1, mode="nearest").astype(np.float32)
            b += ndi.shift(z, (t * ny, t * nx), order=1, mode="nearest").astype(np.float32)
        sgn = (a - b) / (2.0 * ri)
        mag = np.abs(sgn)
        hit = mag > best_mag
        best_signed = np.where(hit, sgn, best_signed).astype(np.float32)
        best_mag = np.maximum(best_mag, mag.astype(np.float32))
    return best_signed


def openness(z: np.ndarray, radius: int) -> np.ndarray:
    """Positive topographic openness (Yokoyama, Shirasawa & Pike 2002), 8-direction angular.

    psi_d = max_t arctan((z(x+t d) - z(x)) / (t * cell));  openness = pi/2 - max_d psi_d.
    """
    L = max(1, int(round(radius)))
    worst = np.full(z.shape, -np.inf, np.float32)
    for dy, dx in DIRS8:
        norm = float(np.hypot(dy, dx))
        for t in range(1, L + 1):
            d = (ndi.shift(z, (-t * dy, -t * dx), order=0, mode="nearest") - z) / (t * norm)
            np.maximum(worst, d.astype(np.float32), out=worst)
    return (np.pi / 2.0 - np.arctan(worst)).astype(np.float32)


def tpi(z: np.ndarray, radius: float) -> np.ndarray:
    """Topographic Position Index: z minus the mean of its neighbourhood."""
    s = 2 * int(np.ceil(radius)) + 1
    return (z - ndi.uniform_filter(z, size=s, mode="nearest")).astype(np.float32)


def lrm(z: np.ndarray, radius: float) -> np.ndarray:
    """Local Relief Model (Hesse 2010): max-min over a window, then lightly smoothed."""
    s = 2 * int(np.ceil(radius)) + 1
    return ndi.uniform_filter(ndi.maximum_filter(z, s) - ndi.minimum_filter(z, s),
                              size=max(3, s // 2), mode="nearest").astype(np.float32)


def linearity(z: np.ndarray, sigma: float) -> np.ndarray:
    """2*sqrt(det J)/tr J of the slope structure tensor: 1 for a perfect line, 0 for isotropic."""
    s = max(float(sigma), 1.0)
    gx = ndi.gaussian_filter(z, s, order=(0, 1), mode="nearest")
    gy = ndi.gaussian_filter(z, s, order=(1, 0), mode="nearest")
    jxx = ndi.gaussian_filter(gx * gx, s, mode="nearest")
    jyy = ndi.gaussian_filter(gy * gy, s, mode="nearest")
    jxy = ndi.gaussian_filter(gx * gy, s, mode="nearest")
    tr = jxx + jyy + 1e-12
    det = np.maximum(jxx * jyy - jxy * jxy, 0.0)
    return (2.0 * np.sqrt(det) / tr).astype(np.float32)


def orientation(z: np.ndarray, sigma: float) -> tuple[np.ndarray, np.ndarray]:
    """Local structure orientation (2*theta convention) and coherence in [0, 0.5]."""
    s = max(float(sigma), 1.0)
    gx = ndi.gaussian_filter(z, s, order=(0, 1), mode="nearest")
    gy = ndi.gaussian_filter(z, s, order=(1, 0), mode="nearest")
    jxx = ndi.gaussian_filter(gx * gx, s, mode="nearest")
    jyy = ndi.gaussian_filter(gy * gy, s, mode="nearest")
    jxy = ndi.gaussian_filter(gx * gy, s, mode="nearest")
    tr = jxx + jyy + 1e-12
    coh = np.sqrt(np.maximum(((jxx - jyy) * 0.5) ** 2 + jxy ** 2, 0.0)) / tr
    theta = 0.5 * np.arctan2(2 * jxy, (jxx - jyy) + 1e-12)
    return theta.astype(np.float32), coh.astype(np.float32)


def aspect_dispersion(z: np.ndarray, sigma: float) -> np.ndarray:
    """Dispersion of slope aspect: low on a planar facet, high in a dissected alluvial fan."""
    gx = ndi.gaussian_filter(z, 1.0, order=(0, 1), mode="nearest")
    gy = ndi.gaussian_filter(z, 1.0, order=(1, 0), mode="nearest")
    mag = np.sqrt(gx * gx + gy * gy) + 1e-9
    ux, uy = gx / mag, gy / mag
    s = max(float(sigma), 1.0)
    R = ndi.gaussian_filter(ux, s, mode="nearest") ** 2 + ndi.gaussian_filter(uy, s, mode="nearest") ** 2
    return (1.0 - np.sqrt(np.clip(R, 0, 1))).astype(np.float32)


def slope_variability(z: np.ndarray, radius: float) -> np.ndarray:
    """Standard deviation of slope magnitude over a window (a rugosity measure)."""
    s = 2 * int(np.ceil(radius)) + 1
    g = np.sqrt(ndi.sobel(z, 0, mode="nearest") ** 2 + ndi.sobel(z, 1, mode="nearest") ** 2)
    m = ndi.uniform_filter(g, s, mode="nearest")
    v = ndi.uniform_filter(g * g, s, mode="nearest") - m * m
    return np.sqrt(np.maximum(v, 0)).astype(np.float32)


def detrend(z: np.ndarray, radius: float) -> np.ndarray:
    """|z - mean_r(z)| weighted by the local tilt of the regional plane."""
    s = 2 * int(np.ceil(radius)) + 1
    m = ndi.uniform_filter(z, s, mode="nearest")
    gy = ndi.gaussian_filter(m, max(float(radius), 1.0), order=(1, 0), mode="nearest")
    gx = ndi.gaussian_filter(m, max(float(radius), 1.0), order=(0, 1), mode="nearest")
    return (np.abs(z - m) * (1.0 + np.sqrt(gx * gx + gy * gy))).astype(np.float32)


def regional(z: np.ndarray, sigma: float) -> np.ndarray:
    """Rank-scaled smooth (>= sigma*100 m) regional field.

    For the 16 official bands that carry no 300 m structure this is the ONLY admissible use:
    they cannot localise a fault, but they can say whether a location is in the right province
    for one.  Measured against Instrument A, ``regional(geod_2ndinv, 25)`` reaches
    precision-at-40k 0.287 against a 0.086 random baseline (3.3x) -- a strong regional prior
    from a band with essentially no fine-scale content.
    """
    return rank_scale(ndi.gaussian_filter(np.asarray(z, np.float32), max(float(sigma), 1.0),
                                          mode="nearest"))


def inv_regional(z: np.ndarray, sigma: float) -> np.ndarray:
    """Rank-scaled smooth regional field, inverted (low values score high).

    Measured: ``inv_regional(geod_2ndinv, 25)`` is the strongest single predictor of the
    ISOLATED catalogue traces (Instrument A1, precision-at-40k 0.033 vs 0.0099 random, 3.3x),
    while the non-inverted version is the strongest predictor of the FLANKING ones (A2, 3.8x).
    Clustered range-front fault sits in high strain rate; isolated buried trace sits in low
    strain rate.  Both directions are physically expected and both are kept as separate terms.
    """
    return rank_scale(-ndi.gaussian_filter(np.asarray(z, np.float32), max(float(sigma), 1.0),
                                           mode="nearest"))


def raw(z: np.ndarray, _radius: float = 0.0) -> np.ndarray:
    """Rank-scaled band, unfiltered."""
    return rank_scale(np.asarray(z, np.float32))


def inv_raw(z: np.ndarray, _radius: float = 0.0) -> np.ndarray:
    return rank_scale(-np.asarray(z, np.float32))


TRANSFORMS = dict(
    line=line_response, curv=curvature, scarp=scarp_step, openness=openness, tpi=tpi,
    lrm=lrm, aniso=linearity, aspect_var=aspect_dispersion, slope_var=slope_variability,
    detrend=detrend, regional=regional, inv_regional=inv_regional, raw=raw, inv_raw=inv_raw,
)


def multiscale(z: np.ndarray, fn, radii=(1.5, 2.5, 3.0, 5.0)) -> np.ndarray:
    """Max over several radii, each normalised to its own robust scale, so no single scale
    dominates by amplitude alone."""
    best = None
    for r in radii:
        t = np.asarray(fn(z, r), np.float32)
        t = rank_scale(t)
        best = t if best is None else np.maximum(best, t)
    return best


def rank_scale(a: np.ndarray) -> np.ndarray:
    """Map to a uniform [0,1] marginal over the finite pixels, with NO ties.

    Ties are removed deliberately.  A stable argsort gives every pixel a distinct rank, so
    the returned field is a total order.  This matters downstream: ``emission.nms_disk``
    keeps the pixels that are the maximum of their own disc, and if a large plateau shares
    one value the whole plateau is a single connected tie region and collapses to ONE emitted
    pixel.  That failure was measured (scripts/run_sweep_a.py emitted 283 px per block where
    ~2,000 were expected) and traced to exact float32 ties in the smoothed scarp field.
    Ties are broken by raster index, which is deterministic and reproducible.
    """
    a = np.asarray(a, np.float64)
    fin = np.isfinite(a)
    out = np.zeros(a.shape, np.float32)
    n = int(fin.sum())
    if n < 100:
        return out
    v = a[fin]
    order = np.argsort(v, kind="stable")
    r = np.empty(n, np.float32)
    r[order] = (np.arange(1, n + 1, dtype=np.float64) / float(n)).astype(np.float32)
    out[fin] = r
    return out


def regional_prior(a: np.ndarray, valid: np.ndarray, sigma: float = 25.0) -> np.ndarray:
    """Smooth (>= 2.5 km) regional field, for the 16 bands that carry no 300 m structure."""
    f = np.where(valid & np.isfinite(a), a, np.nanmedian(a[valid & np.isfinite(a)]))
    return rank_scale(ndi.gaussian_filter(f.astype(np.float32), sigma, mode="nearest"))
