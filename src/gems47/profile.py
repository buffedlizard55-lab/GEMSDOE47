"""H47-C1: odd scarp profiles competing with even channel/ridge profiles.

A coarse 100 m screening descriptor, NOT a reproduction of metre-scale scarp
age inversion. No labels, catalogue geometry or historic prediction enters this
module. Templates are projected off a constant and a linear regional slope,
so a planar hillside is not evidence for a scarp. All stencils are finite.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage, special

DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))  # (row, column) cross-profile direction
WIDTHS_PX = (1.0, 2.0)
HALF_PROFILE = 6
PROFILE_NAMES = (
    "odd_step_r2", "even_channel_r2", "step_minus_channel_r2",
    "step_height_abs", "step_alongstrike_consistency", "step_width_px",
    "gravity_normal_agreement",
)
STANDARD_NAMES = (
    "elevation_gradient", "elevation_laplacian", "hessian_determinant",
    "hessian_anisotropy", "tensor_coherence", "tensor_cos2normal",
    "tensor_sin2normal",
)


def residualized_template(u: np.ndarray, width: float, kind: str) -> np.ndarray:
    """Unitless template orthogonal to intercept and linear background slope."""
    u = np.asarray(u, dtype=np.float64)
    if u.ndim != 1 or u.size < 5 or not np.isfinite(u).all():
        raise ValueError("u must be a finite profile with at least five samples")
    if not np.isfinite(width) or width <= 0 or kind not in ("step", "channel"):
        raise ValueError("invalid template width or kind")
    b = np.column_stack((np.ones(u.size), u))
    if np.linalg.matrix_rank(b) != 2:
        raise ValueError("profile positions must span a nonzero distance")
    t = special.erf(u / (np.sqrt(2.0) * width)) if kind == "step" else np.exp(-0.5 * (u / width) ** 2)
    out = t - b @ np.linalg.lstsq(b, t, rcond=None)[0]
    if np.dot(out, out) < 1e-12:
        raise ValueError("degenerate residualized template")
    return out


def _line_kernel(weights: np.ndarray, dr: int, dc: int) -> np.ndarray:
    n = (len(weights) - 1) // 2
    k = np.zeros((2 * n + 1, 2 * n + 1), np.float32)
    for j, weight in zip(range(-n, n + 1), weights):
        k[n + j * dr, n + j * dc] = weight
    return k


def _translated(a: np.ndarray, dr: int, dc: int) -> np.ndarray:
    """out[r,c] = a[r+dr,c+dc], without circular wrap."""
    out = np.zeros_like(a)
    h, w = a.shape
    y0, y1 = max(0, -dr), min(h, h - dr)
    x0, x1 = max(0, -dc), min(w, w - dc)
    if y1 > y0 and x1 > x0:
        out[y0:y1, x0:x1] = a[y0 + dr:y1 + dr, x0 + dc:x1 + dc]
    return out


def ordinary_terrain(elevation: np.ndarray, support: np.ndarray) -> dict[str, np.ndarray]:
    """Shared generic-gradient/Hessian baseline; no signed-profile descriptors."""
    z = np.asarray(elevation, np.float32)
    valid = np.asarray(support, bool)
    if z.ndim != 2 or z.shape != valid.shape or not np.isfinite(z[valid]).all():
        raise ValueError("invalid elevation/support")
    z = np.where(np.isfinite(z), z, 0).astype(np.float32)
    gy = ndimage.gaussian_filter(z, 1.5, order=(1, 0), mode="constant", truncate=4)
    gx = ndimage.gaussian_filter(z, 1.5, order=(0, 1), mode="constant", truncate=4)
    xx = ndimage.gaussian_filter(z, 1.5, order=(0, 2), mode="constant", truncate=4)
    yy = ndimage.gaussian_filter(z, 1.5, order=(2, 0), mode="constant", truncate=4)
    xy = ndimage.gaussian_filter(z, 1.5, order=(1, 1), mode="constant", truncate=4)
    jxx = ndimage.gaussian_filter(gx * gx, 3, mode="constant", truncate=4)
    jyy = ndimage.gaussian_filter(gy * gy, 3, mode="constant", truncate=4)
    jxy = ndimage.gaussian_filter(gx * gy, 3, mode="constant", truncate=4)
    gap = np.hypot(jxx - jyy, 2 * jxy)
    eps = np.float32(1e-8)
    layers = dict(zip(STANDARD_NAMES, (
        np.hypot(gx, gy), xx + yy, xx * yy - xy * xy,
        np.hypot(xx - yy, 2 * xy), gap / np.maximum(jxx + jyy, eps),
        (jxx - jyy) / np.maximum(gap, eps), 2 * jxy / np.maximum(gap, eps),
    )))
    return {name: np.where(valid, value, 0).astype(np.float32) for name, value in layers.items()}


def scarp_profiles(elevation: np.ndarray, gravity: np.ndarray, support: np.ndarray) -> dict[str, np.ndarray]:
    """Return slope-orthogonal odd/even profile descriptors on common support.

    Caller must erode *raw measurement validity* by >=20 px. Zero fills are only
    allowed outside emission support; otherwise boundary profiles would be fake.
    Correlations are normalized by the affine-detrended residual sum of squares.
    """
    z, g, valid = np.asarray(elevation, np.float32), np.asarray(gravity, np.float32), np.asarray(support, bool)
    if z.ndim != 2 or z.shape != g.shape or z.shape != valid.shape:
        raise ValueError("elevation, gravity and support must be same-shape 2D")
    if not np.isfinite(z[valid]).all() or not np.isfinite(g[valid]).all():
        raise ValueError("valid measurements must be finite")
    z = np.where(np.isfinite(z), z, 0).astype(np.float32)
    g = np.where(np.isfinite(g), g, 0).astype(np.float32)
    step_best = np.zeros(z.shape, np.float32)
    channel_best = np.zeros_like(step_best)
    height_best = np.zeros_like(step_best)
    consistency_best = np.zeros_like(step_best)
    width_best = np.zeros_like(step_best)
    normal_best = np.zeros(z.shape, np.uint8)
    offsets = np.arange(-HALF_PROFILE, HALF_PROFILE + 1, dtype=np.float64)
    for direction_id, (dr, dc) in enumerate(DIRECTIONS):
        u = offsets * np.hypot(dr, dc)
        total = ndimage.correlate(z, _line_kernel(np.ones(u.size), dr, dc), mode="constant")
        total2 = ndimage.correlate(z * z, _line_kernel(np.ones(u.size), dr, dc), mode="constant")
        linear = ndimage.correlate(z, _line_kernel(u, dr, dc), mode="constant")
        rss = np.maximum(total2 - total * total / u.size - linear * linear / float(u @ u), 0)
        # An approximately planar profile has only float32 cancellation noise.
        usable = valid & (rss > np.maximum(1.0, total2 * 2e-6))
        for width in WIDTHS_PX:
            ts = residualized_template(u, width, "step")
            tv = residualized_template(u, width, "channel")
            dot = ndimage.correlate(z, _line_kernel(ts, dr, dc), mode="constant")
            vd = ndimage.correlate(z, _line_kernel(tv, dr, dc), mode="constant")
            coefficient = dot / float(ts @ ts)
            step = np.where(usable, dot * dot / np.maximum(rss * float(ts @ ts), 1e-6), 0)
            channel = np.where(usable, vd * vd / np.maximum(rss * float(tv @ tv), 1e-6), 0)
            np.clip(step, 0, 1, out=step)
            np.clip(channel, 0, 1, out=channel)
            np.maximum(channel_best, channel, out=channel_best)
            better = step > step_best
            # Compare signed step coefficients 300 m along the perpendicular strike.
            before = _translated(coefficient, -3 * dc, 3 * dr)
            after = _translated(coefficient, 3 * dc, -3 * dr)
            same_sign = (coefficient * before > 0) & (coefficient * after > 0)
            small = np.minimum(np.abs(coefficient), np.minimum(np.abs(before), np.abs(after)))
            large = np.maximum(np.abs(coefficient), np.maximum(np.abs(before), np.abs(after)))
            consistency = np.where(same_sign, small / np.maximum(large, 1e-6), 0)
            step_best[better] = step[better]
            height_best[better] = 2 * np.abs(coefficient[better])
            consistency_best[better] = consistency[better]
            width_best[better] = width
            normal_best[better] = direction_id
    g_y = ndimage.gaussian_filter(g, 1.5, order=(1, 0), mode="constant", truncate=4)
    g_x = ndimage.gaussian_filter(g, 1.5, order=(0, 1), mode="constant", truncate=4)
    normal_y = np.asarray([dr / np.hypot(dr, dc) for dr, dc in DIRECTIONS])[normal_best]
    normal_x = np.asarray([dc / np.hypot(dr, dc) for dr, dc in DIRECTIONS])[normal_best]
    agreement = np.abs(g_y * normal_y + g_x * normal_x) / np.maximum(np.hypot(g_y, g_x), 1e-8)
    layers = dict(zip(PROFILE_NAMES, (
        step_best, channel_best, step_best - channel_best, height_best,
        consistency_best, width_best, agreement,
    )))
    return {name: np.where(valid, value, 0).astype(np.float32) for name, value in layers.items()}
