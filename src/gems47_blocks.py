#!/usr/bin/env python3
"""Spatially blocked DTI evaluation.

A block is a rectangular window of the 100 m grid.  Only ground-truth pixels
inside the block are scored; predicted pixels are taken from the window dilated
by the kernel radius so that predictions just outside the block can still earn
credit for truth inside it.  This is the standard "blocked holdout" so that a
ranking learned on some blocks cannot be scored by memorising neighbouring ones.
"""
from __future__ import annotations

import numpy as np

from .gems47_metric import R_PX, dti


def block_windows(shape, nrows, ncols, buffer_px=0):
    H, W = shape
    r_edges = np.linspace(0, H, nrows + 1).astype(int)
    c_edges = np.linspace(0, W, ncols + 1).astype(int)
    for i in range(nrows):
        for j in range(ncols):
            r0, r1 = r_edges[i], r_edges[i + 1]
            c0, c1 = c_edges[j], c_edges[j + 1]
            yield (i, j, (max(0, r0 - buffer_px), min(H, r1 + buffer_px),
                          max(0, c0 - buffer_px), min(W, c1 + buffer_px)),
                   (r0, r1, c0, c1))


def dti_in_block(pred, truth, win, core, mask=None):
    r0, r1, c0, c1 = win
    p = pred[r0:r1, c0:c1]
    g = np.zeros_like(p, dtype=bool)
    cr0, cr1, cc0, cc1 = core
    g[cr0 - r0:cr1 - r0, cc0 - c0:cc1 - c0] = truth[cr0:cr1, cc0:cc1] > 0
    m = None
    if mask is not None:
        m = mask[r0:r1, c0:c1].copy()
        # neutral only inside the block core; outside the core nothing is truth anyway
        m[cr0 - r0:cr1 - r0, cc0 - c0:cc1 - c0] = mask[cr0:cr1, cc0:cc1]
        m[:cr0 - r0, :] = False
        m[cr1 - r0:, :] = False
        m[:, :cc0 - c0] = False
        m[:, cc1 - c0:] = False
    return dti(p, g, mask=m)


def blocked_scores(pred, truth, nrows=2, ncols=2, mask=None):
    out = []
    for i, j, win, core in block_windows(pred.shape, nrows, ncols, int(np.ceil(R_PX))):
        r = dti_in_block(pred, truth, win, core, mask=mask)
        r.update(block=(i, j))
        out.append(r)
    return out
