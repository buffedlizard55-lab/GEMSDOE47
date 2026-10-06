#!/usr/bin/env python3
"""Emission construction for the DOE GEMS Prize (DrivenData #306).

Legacy emission operators retained for unit tests and historical learning.
The documented 3730 x 3292, EPSG:32611, 100 m grid came from mirrored/local
rasters; this module does not authenticate official inputs or submission lineage.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree


def octile_dot_spacing(px_mask):
    """Median nearest-neighbour distance between a dot set's pixels (px)."""
    from scipy.spatial import cKDTree
    ys, xs = np.nonzero(px_mask)
    if len(ys) < 3:
        return float('nan')
    t = cKDTree(np.c_[ys, xs])
    d, _ = t.query(np.c_[ys, xs], k=2)
    return float(np.median(d[:, 1]))


def flank_prune(dots, dist_to_catalogue, B):
    """Remove every dot whose Euclidean distance to the nearest catalogue pixel is <= B.

    This operator was used for a historical candidate whose score-to-file
    mappings were not organizer-authenticated. The function is retained for
    unit tests and analysis only; it must not be treated as a validated
    submission method or a live-scored performance ladder.
    """
    return dots & (dist_to_catalogue > B)


def greedy_min_separation(dots, min_sep_px):
    """Greedy maximal independent set on the 'too close' graph.

    Iterates pixels in raster-scan order and keeps a dot only when no already-kept
    dot lies within min_sep_px (Euclidean). The output mask is a subset of the
    input mask; this function does not validate raster metadata or performance.
    """
    ys, xs = np.nonzero(dots)
    order = np.lexsort((xs, ys))
    keep = np.zeros(dots.shape, dtype=bool)
    kept = []
    r2 = float(min_sep_px) ** 2
    for idx in order:
        y, x = int(ys[idx]), int(xs[idx])
        ok = True
        for (ky, kx) in kept:
            if (ky - y) ** 2 + (kx - x) ** 2 < r2:
                ok = False
                break
        if ok:
            keep[y, x] = True
            kept.append((y, x))
    return keep


def dilate_support(dots, r):
    if r <= 0:
        return dots
    return ndimage.binary_dilation(dots, structure=ndimage.generate_binary_structure(2, 2), iterations=int(r))


def to_raster(dots, footprint, dtype=np.float32, outside='nan'):
    """Build a float raster: 1.0 at dots, 0 elsewhere, with configurable outside cells."""
    a = np.zeros(dots.shape, dtype=dtype)
    a[dots] = dtype(1.0)
    if outside == 'nan' and footprint is not None:
        a[~footprint] = np.nan
    return a


def trace_chains(dots, link_px=4.5):
    """Group dots into traces: connected components of the 'within link_px' graph."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    ys, xs = np.nonzero(dots)
    n = len(ys)
    t = cKDTree(np.c_[ys, xs])
    pairs = t.query_pairs(link_px)
    if not pairs:
        return [np.array([i]) for i in range(n)], (ys, xs)
    r = np.fromiter((p[0] for p in pairs), dtype=np.int32, count=len(pairs))
    c = np.fromiter((p[1] for p in pairs), dtype=np.int32, count=len(pairs))
    g = coo_matrix((np.ones(len(r), bool), (r, c)), shape=(n, n))
    _, lab = connected_components(g, directed=False)
    comps = [np.nonzero(lab == k)[0] for k in range(lab.max() + 1)]
    return comps, (ys, xs)


def order_chain(idx, ys, xs):
    """Order the dots of one component along the trace by a greedy nearest-neighbour walk."""
    pts = np.c_[ys[idx], xs[idx]].astype(float)
    m = len(pts)
    if m <= 2:
        return pts
    used = np.zeros(m, bool)
    start = int(np.argmin(pts[:, 0] + pts[:, 1]))
    used[start] = True
    order = [start]
    cur = start
    for _ in range(m - 1):
        d = np.hypot(pts[:, 0] - pts[cur, 0], pts[:, 1] - pts[cur, 1])
        d[used] = np.inf
        nxt = int(np.argmin(d))
        if not np.isfinite(d[nxt]):
            break
        used[nxt] = True
        order.append(nxt)
        cur = nxt
    return pts[order]


def redot(dots, spacing_px, link_px=4.5, centroid_keep_px=4.5):
    """Re-emit the dot network at a target spacing along the traces it already traces.

    Dots are grouped into traces (connected components within `link_px`), each trace is
    ordered along its own path, and new dots are placed at exact arc-length multiples of
    `spacing_px`, linearly interpolated between the two original dots that bracket the
    position.  Positions therefore stay on the network to within one interpolation step,
    which is what the metric's 300 m kernel treats as the same trace.
    """
    comps, (ys, xs) = trace_chains(dots, link_px)
    out = np.zeros(dots.shape, dtype=bool)
    for idx in comps:
        pts = order_chain(idx, ys, xs)
        if len(pts) == 1:
            out[int(pts[0, 0]), int(pts[0, 1])] = True
            continue
        seg = np.hypot(np.diff(pts[:, 0]), np.diff(pts[:, 1]))
        arc = np.concatenate([[0.0], np.cumsum(seg)])
        L = arc[-1]
        if L <= 0:
            out[int(pts[0, 0]), int(pts[0, 1])] = True
            continue
        n_new = max(1, int(np.floor(L / spacing_px)) + 1)
        targets = np.arange(n_new) * spacing_px
        targets = np.clip(targets, 0.0, L)
        ry = np.interp(targets, arc, pts[:, 0])
        rx = np.interp(targets, arc, pts[:, 1])
        yy = np.rint(ry).astype(int)
        xx = np.rint(rx).astype(int)
        out[np.clip(yy, 0, dots.shape[0] - 1), np.clip(xx, 0, dots.shape[1] - 1)] = True
    return out
