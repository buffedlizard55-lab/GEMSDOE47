"""Candidate geological layers for the H47 hypothesis family.

The LATI screen (evidence/lati_fit.json, evidence/lati_controls.json) says the
single strongest public predictor of the hidden new-fault truth is the 0-1.5 px
halo of the given USGS/INGENIOUS catalogue - the zone the reported-0.2778
submission deliberately emptied.  But an *isotropic* halo is not a geological
model.  The organiser's own definition is directional:

  "'new fault' means 'any fault pixel not already captured by USGS/INGENIOUS'
   and can include newly mapped geometry of an existing fault system."
   - DrivenData staff (chrisk-dd), community thread 11536, 2026-09-23

Newly mapped geometry of an existing system is not a buffer.  It is
  * along-strike continuation past a mapped trace tip,
  * en-echelon / relay-ramp strands just off strike,
  * splay branches at a releasing or restraining bend.
So the halo must be **decomposed by its orientation relative to the local
catalogue strike**.  That is what this module computes.

Every layer is returned as a full-grid float32 array (higher == more fault-like)
plus, where useful, a supporting mask.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage

from . import grid as G
from . import metric as M


def local_strike(cat: np.ndarray, sigma_px: float = 3.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Local strike unit vector of the catalogue lineaments, via the structure tensor.

    Returns (tx, ty, coherence).  ``t`` is the *along-strike* direction; the
    structure tensor's dominant eigenvector is the gradient direction, i.e.
    normal to the lineament, so the strike is its perpendicular.
    ``coherence`` = (l1-l2)/(l1+l2) in [0,1]: 1 for a perfectly linear trace,
    0 for an isotropic blob.
    """
    I = ndimage.gaussian_filter(cat.astype(np.float32), 1.0)
    gy, gx = np.gradient(I)
    w = sigma_px
    Jxx = ndimage.gaussian_filter(gx * gx, w)
    Jyy = ndimage.gaussian_filter(gy * gy, w)
    Jxy = ndimage.gaussian_filter(gx * gy, w)
    tr = Jxx + Jyy
    det = Jxx * Jyy - Jxy * Jxy
    disc = np.sqrt(np.maximum(tr * tr / 4.0 - det, 0.0))
    l1 = tr / 2.0 + disc
    l2 = tr / 2.0 - disc
    coherence = np.where(l1 + l2 > 0, (l1 - l2) / np.maximum(l1 + l2, 1e-12), 0.0)
    # dominant eigenvector (gradient direction n); strike t is perpendicular
    nx = Jxx - Jyy
    ny = 2.0 * Jxy
    nrm = np.sqrt(nx * nx + ny * ny)
    nrm = np.where(nrm > 1e-12, nrm, 1.0)
    tx = -ny / nrm
    ty = nx / nrm
    return tx.astype(np.float32), ty.astype(np.float32), coherence.astype(np.float32)


def nearest_catalogue_geometry(cat: np.ndarray):
    """For every pixel: distance to the catalogue (px), and the offset vector to
    the nearest catalogue pixel."""
    d, (iy, ix) = ndimage.distance_transform_edt(~cat, return_indices=True)
    yy, xx = np.mgrid[0:cat.shape[0], 0:cat.shape[1]]
    dy = (yy - iy).astype(np.float32)
    dx = (xx - ix).astype(np.float32)
    return d.astype(np.float32), dy, dx, iy, ix


def trace_tips(cat: np.ndarray, k: int = 2) -> np.ndarray:
    """Catalogue pixels that look like trace endpoints.

    A tip has few catalogue pixels in its local neighbourhood *and* a strongly
    linear local structure tensor (so junctions, which also have few neighbours
    in some directions, are excluded by requiring high coherence AND a low
    neighbour count on only one side).  We use the simple, robust version:
    endpoints of the 8-connected skeleton proxy = catalogue pixels with <= k
    catalogue neighbours within a 3x3 window, restricted to pixels whose local
    coherence exceeds 0.6.
    """
    nb = ndimage.convolve(cat.astype(np.int32), np.ones((3, 3), np.int32)) - cat.astype(np.int32)
    _, _, coh = local_strike(cat, 3.0)
    return (cat & (nb <= k) & (coh > 0.6))


def build_layers(template: G.Template, data=None) -> dict[str, np.ndarray]:
    cat = template.catalogue
    ev = template.evaluated
    d, dy, dx, iy, ix = nearest_catalogue_geometry(cat)
    tx, ty, coh = local_strike(cat, 3.0)
    # strike at the *nearest catalogue pixel*, pulled to this pixel
    stx = tx[iy, ix]
    sty = ty[iy, ix]
    dn = np.maximum(d, 1e-6)
    # |cos(angle between the offset to the catalogue and the local strike)|
    cos_along = np.abs((dy * stx + dx * sty) / dn).astype(np.float32)

    R = M.RANGE_PX
    halo = (d > 0) & (d <= R) & ev                       # 0 < d <= 3 px = 0..300 m
    halo_near = (d > 0) & (d <= 1.5) & ev
    tips = trace_tips(cat)
    d_tip, _, _, tiy, tix = nearest_catalogue_geometry(~tips if tips.any() else np.ones_like(cat))
    # distance from this pixel to the nearest trace tip
    dtip = ndimage.distance_transform_edt(~tips).astype(np.float32) if tips.any() else np.full(cat.shape, 99.0, np.float32)

    L: dict[str, np.ndarray] = {}
    z = np.zeros(cat.shape, np.float32)

    # 1. isotropic halo (the layer LATI ranked first among public layers)
    L["flank_halo_0_3"] = np.where(halo, 1.0 - d / (R + 1e-9), 0.0).astype(np.float32)
    L["flank_halo_0_1.5"] = np.where(halo_near, 1.0 - d / 1.5, 0.0).astype(np.float32)

    # 2. ALONG-STRIKE continuation: halo pixel offset parallel to the local strike.
    #    This is "newly mapped geometry of an existing fault system" in its most
    #    literal reading - the trace keeps going where the catalogue stops.
    L["flank_along_strike"] = (np.where(halo, 1.0 - d / (R + 1e-9), 0.0)
                               * cos_along * (0.35 + 0.65 * coh[iy, ix])).astype(np.float32)

    # 3. ACROSS-STRIKE splay / parallel strand: halo offset normal to strike.
    L["flank_across_strike"] = (np.where(halo, 1.0 - d / (R + 1e-9), 0.0)
                                * (1.0 - cos_along) * (0.35 + 0.65 * coh[iy, ix])).astype(np.float32)

    # 4. TIP EXTENSION: along-strike AND close to a mapped trace endpoint -
    #    the highest-confidence place for unmapped continuation.
    tip_w = np.exp(-dtip / 6.0).astype(np.float32)
    L["flank_tip_extension"] = (L["flank_along_strike"] * tip_w).astype(np.float32)

    # 5. relay-ramp / step-over: two catalogue pixels close together but this
    #    pixel between them and off both traces.  Proxy: moderate distance, low
    #    coherence at the nearest catalogue pixel (a bend), along-strike offset.
    bend_w = (1.0 - coh[iy, ix]).astype(np.float32)
    L["flank_bend_splay"] = (np.where(halo, 1.0 - d / (R + 1e-9), 0.0)
                             * bend_w * (0.5 + 0.5 * cos_along)).astype(np.float32)

    # diagnostics, not layers
    L["_diag_coherence"] = coh
    L["_diag_cos_along"] = cos_along
    L["_diag_d_catalogue"] = d
    L["_diag_tips"] = tips.astype(np.float32)
    L["_diag_halo_mask"] = halo.astype(np.float32)
    return L


if __name__ == "__main__":
    import json
    t = G.load_template()
    L = build_layers(t)
    for k, v in L.items():
        nz = int((v != 0).sum())
        print(f"{k:<24} nonzero={nz:>9,} max={float(v.max()):.4f} "
              f"mean_over_nonzero={float(v[v!=0].mean()) if nz else 0:.4f}")
