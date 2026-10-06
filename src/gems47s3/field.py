"""H47 detector surfaces — five hypotheses, each a label-free physical surface.

Nothing in this module reads ``labels.tif`` except ``vacancy_residual``, which uses the
catalogue *geometry* only as a density to be subtracted (never as a prediction target),
so every surface is safe to evaluate on a spatially-blocked holdout without leakage from
the held-out traces.

The five hypotheses
-------------------
H47-A  **Catalogue-vacancy residual (mapping-gap targeting).**
       Layers: all 19 official bands (physics lineament density) + ``labels.tif`` geometry.
       Signature: a *density residual* -- locally smoothed physics-lineament evidence minus
       locally smoothed catalogue trace density, at matched scales and matched normalisation.
       Why it should catch a fault MISSING from the catalogue rather than one already in it:
       Hermant et al. (2025, Stanford Workshop on Geothermal Reservoir Engineering, Fig. 2)
       documents that USGS Quaternary-fault density varies with the *scale of the source map*
       rather than with geology, and that lidar-based expert labels can sit up to ~400 m from
       the USGS trace.  A cell with strong multi-physics lineament evidence and no catalogue
       trace is therefore a mapping gap, not an absence of structure.
       Differs from everything already implemented: the family used *external* catalogues
       (SGMC, QFaults v2) as an ADDITIVE prior (GEMSDOE32 H60-2) and the given catalogue only
       as a REMOVAL buffer (H33-2).  No prior surface computes a residual against the given
       catalogue's own density field.

H47-B  **Cross-strike magnetic "braid number" (damage-zone multimodality).**
       Layers: rtp, tmi_hg, tmi_vg, tc, mag_anom.
       Signature: a *counting* transform -- the number of distinct ridge maxima in the
       cross-strike profile within +/-5 px, at each of four orientations.  Not a magnitude.
       Why: a fault damage zone is an anastomosing braid of sub-parallel structures
       (Chester & Logan 1986; Faulkner et al. 2011, both cited in Hermant et al. 2025).
       One magnetic edge is a lithologic contact or a dyke; two or more sub-parallel edges
       within 200-500 m is a damage zone, which is what an expert maps as a fault.
       Differs from: the family used per-pixel ridge magnitude, Hessian line response and
       orientation consensus (H33-A/H33-6).  No prior surface counts parallel edges.

H47-C  **Two-sided drainage-azimuth asymmetry (half-graben tilt).**
       Layers: det_elev, det_elev_slope.
       Signature: the contrast, across a candidate line, of the vector-mean downslope azimuth
       and of the mean gradient magnitude on the two sides within 4 px.
       Why: a range-front normal fault separates a tilted, radially-drained footwall from a
       hanging-wall apron with longer, more parallel drainage; the asymmetry is two-sided and
       is the classic Basin-and-Range expression of the structures that host geothermal
       systems (Giddens & Faulds 2025: 91.9 % of step-overs associated with known geothermal
       systems lie on range-front faults).
       Differs from: H33-B/H33-C measured *collinearity* of valley or scarplet skeletons --
       a one-sided, orientation-free occupancy vote.  Nothing measured a two-sided contrast.

H47-D  **Strain-partitioning ratio edge.**
       Layers: geod_dilaterate, geod_shearrate, geod_2ndinv.
       Signature: the Laplacian of the partitioning ratio rho = |dilatation| / (shear + eps).
       A signed second derivative, so the smooth regional strain gradient -- which dominates
       every raw magnitude here (geod_2ndinv median 19.9, IQR-based sigma 15.2) -- cancels.
       Why: strain localises on structures, and the *partitioning* between volumetric and
       shear strain changes across a fault that is favourably oriented in the regional stress
       field; dilational segments are the open, fluid-permeable ones (the USGS Nevada
       Geothermal Machine Learning Project assigns slip/dilation tendency per fault segment,
       DeAngelo et al. 2022, DOI 10.5066/P9V5SQRD).
       Differs from: the family used these bands as scalars or plain gradient magnitudes;
       H61-4 proposed a principal-axis matched filter on the tensor but was never implemented.

H47-E  **Signed basement-step persistence.**
       Layers: depth_to_base_surf, cond_surf.
       Signature: the *signed* cross-strike step in basement depth, required to persist over
       a run of >= 10 px along the locally-estimated strike; sign reversals along strike are
       emitted separately as a segment-boundary / transfer-zone surface.
       Why: basin fill thickness steps abruptly across a range-front fault, and the sign
       (which side is deeper) distinguishes a fault from a symmetric fold or a lithologic
       edge.  Sign reversals locate accommodation zones, where transverse, unmapped
       structures live (Curewitz & Karson 1997; Faulds & Hinz 2015, cited in Hermant 2025).
       Differs from: H33-D used an UNSIGNED gradient magnitude plus orientation coherence.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from .grid import Grid, robust_unit
from .spec import HEIGHT, WIDTH

# Four orientations as (dy, dx) unit steps along the STRIKE.  The cross-strike normal is
# (-dx, dy).  Half-integer normals are handled by rounding the sample offsets.
ORIENTATIONS = [
    ("N-S",   (0.0, 1.0)),    # strike north-south   -> normal points east-west
    ("E-W",   (1.0, 0.0)),    # strike east-west     -> normal points north-south
    ("NE-SW", (0.7071, 0.7071)),
    ("NW-SE", (0.7071, -0.7071)),
]

# Physics families used for corroboration.  The two seismic bands (deq_n100a15,
# ieq_n100a15) are excluded by measurement, not assumption: see
# scripts/explore_data.py, which reproduces the family's earlier finding that ieq is
# ~0.99 autocorrelated at 3 km lag and therefore carries no information at the 300 m
# scale the metric resolves.
FAMILIES = {
    "mag":   ["rtp", "tmi_hg", "tmi_vg", "tc", "mag_anom", "tmi"],
    "grav":  ["iso_grav_anom", "iso_grav_anom_slope", "iso_grav_anom_hg", "iso_grav_anom_vg"],
    "topo":  ["det_elev", "det_elev_slope"],
    "strain": ["geod_2ndinv", "geod_shearrate", "geod_dilaterate"],
    "elec":  ["cond_surf", "depth_to_base_surf"],
}


# --------------------------------------------------------------------------- primitives
def _fill(a: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Replace invalid cells with the valid-median so filters do not propagate NaN."""
    v = valid & np.isfinite(a)
    med = float(np.median(a[v])) if v.any() else 0.0
    return np.where(v, a, med).astype(np.float32)


def _shift(a: np.ndarray, dy: float, dx: float) -> np.ndarray:
    """Integer-rounded shift with edge replication."""
    return ndi.shift(a, (dy, dx), order=1, mode="nearest", prefilter=False).astype(np.float32)


def line_response(a: np.ndarray, valid: np.ndarray, sigma: float) -> np.ndarray:
    """Frangi/Sato curvilinear response: -lambda_min of the Hessian, both polarities.

    A magnetic low and a magnetic high can equally well mark the same contact, so the
    response is made sign-symmetric by taking the eigenvalue of least magnitude with a
    positive sign convention.
    """
    f = _fill(a, valid)
    axx = ndi.gaussian_filter(f, sigma, order=(0, 2), mode="nearest")
    ayy = ndi.gaussian_filter(f, sigma, order=(2, 0), mode="nearest")
    axy = ndi.gaussian_filter(f, sigma, order=(1, 1), mode="nearest")
    disc = np.sqrt(np.maximum(((axx - ayy) * 0.5) ** 2 + axy ** 2, 0.0))
    l1 = (axx + ayy) * 0.5 + disc
    l2 = (axx + ayy) * 0.5 - disc
    small = np.where(np.abs(l1) >= np.abs(l2), l2, l1)
    return -small


def structure_tensor(a: np.ndarray, valid: np.ndarray, sigma: float):
    """Orientation (2*theta convention) and coherence of the local structure tensor."""
    f = _fill(a, valid)
    gx = ndi.gaussian_filter(f, sigma, order=(0, 1), mode="nearest")
    gy = ndi.gaussian_filter(f, sigma, order=(1, 0), mode="nearest")
    jxx = ndi.gaussian_filter(gx * gx, sigma, mode="nearest")
    jyy = ndi.gaussian_filter(gy * gy, sigma, mode="nearest")
    jxy = ndi.gaussian_filter(gx * gy, sigma, mode="nearest")
    tr = jxx + jyy + 1e-12
    coh = np.sqrt(np.maximum(((jxx - jyy) * 0.5) ** 2 + jxy ** 2, 0.0)) / tr
    theta = 0.5 * np.arctan2(2 * jxy, (jxx - jyy) + 1e-12)
    return theta.astype(np.float32), coh.astype(np.float32)


def multiscale_line(a: np.ndarray, valid: np.ndarray, sigmas=(1.0, 2.0, 3.0)) -> np.ndarray:
    """Scale-normalised maximum of the line response over several smoothing scales."""
    best = None
    for s in sigmas:
        r = line_response(a, valid, s) * (s ** 1.0)   # scale normalisation
        best = r if best is None else np.maximum(best, r)
    return best


# --------------------------------------------------------------------------- H47 surfaces
def corroboration(g: Grid, valid: np.ndarray, pct: float = 99.0,
                  sigmas=(1.0, 2.0, 3.0)) -> dict:
    """Per-family normalised lineament response and the count of families that fire."""
    fam = {}
    for name, bands in FAMILIES.items():
        acc = None
        for b in bands:
            r = robust_unit(multiscale_line(g.band(b), valid, sigmas), valid, pct=pct)
            acc = r if acc is None else np.fmax(acc, r)
        fam[name] = np.nan_to_num(acc, nan=0.0).astype(np.float32)
    stack = np.stack([fam[k] for k in FAMILIES])
    thr = np.quantile(stack[:, valid], 0.99, axis=1).reshape(-1, 1, 1)
    firing = (stack >= np.maximum(thr, 1e-6)).astype(np.float32)
    count = firing.sum(axis=0)
    return dict(families=fam, count=count.astype(np.float32),
                mean=stack.mean(axis=0).astype(np.float32),
                max=stack.max(axis=0).astype(np.float32))


def h47a_vacancy_residual(g: Grid, valid: np.ndarray, corr: dict,
                          scale: float = 8.0) -> dict:
    """H47-A: physics lineament density minus catalogue trace density, matched scales."""
    phys = corr["mean"]
    d_phys = ndi.gaussian_filter(np.where(valid, phys, 0.0), scale, mode="nearest")
    n_valid = ndi.gaussian_filter(valid.astype(np.float32), scale, mode="nearest")
    d_phys = d_phys / np.maximum(n_valid, 1e-6)
    d_cat = ndi.gaussian_filter(g.catalogue.astype(np.float32), scale, mode="nearest") / np.maximum(
        ndi.gaussian_filter(g.footprint.astype(np.float32), scale, mode="nearest"), 1e-6)
    # normalise both densities to the same [0,1] robust scale before differencing
    a = robust_unit(d_phys, valid, pct=99.5)
    b = robust_unit(d_cat, valid, pct=99.5)
    resid = np.nan_to_num(a - b, nan=0.0)
    return dict(residual=np.clip(resid, 0.0, 1.0).astype(np.float32),
                signed=resid.astype(np.float32),
                physics_density=a, catalogue_density=b)


def h47b_braid_number(g: Grid, valid: np.ndarray, corr: dict, halfwidth: int = 5) -> dict:
    """H47-B: number of distinct magnetic ridge maxima in the cross-strike profile."""
    base = np.maximum(corr["families"]["mag"], 1e-6)
    best_count = np.zeros(base.shape, np.float32)
    per_orient = {}
    for name, (sy, sx) in ORIENTATIONS:
        ny, nx = -sx, sy                     # unit normal to the strike
        prof = np.stack([_shift(base, t * ny, t * nx) for t in range(-halfwidth, halfwidth + 1)])
        # local maxima along the profile axis (axis 0)
        lm = np.zeros(prof.shape, bool)
        lm[1:-1] = (prof[1:-1] > prof[:-2]) & (prof[1:-1] >= prof[2:])
        cnt = lm.sum(axis=0).astype(np.float32)
        per_orient[name] = cnt
        np.maximum(best_count, cnt, out=best_count)
    # a braid is >= 2 sub-parallel edges; scale to [0,1] with 4 as saturation
    return dict(braid=np.clip(best_count / 4.0, 0.0, 1.0).astype(np.float32),
                count=best_count, per_orientation=per_orient)


def h47c_drainage_asymmetry(g: Grid, valid: np.ndarray, width: int = 4) -> dict:
    """H47-C: two-sided contrast of flow azimuth and gradient magnitude across a line."""
    elev = _fill(g.band("det_elev"), valid)
    gy, gx = np.gradient(elev.astype(np.float64))
    gx = gx.astype(np.float32); gy = gy.astype(np.float32)
    mag = np.sqrt(gx * gx + gy * gy) + 1e-9
    # unit downslope direction
    ux, uy = -gx / mag, -gy / mag
    out = {}
    best_asym = np.zeros(elev.shape, np.float32)
    best_mag_asym = np.zeros(elev.shape, np.float32)
    for name, (sy, sx) in ORIENTATIONS:
        ny, nx = -sx, sy
        # accumulate the downslope unit vector and gradient magnitude on each side
        ax = ay = am = np.zeros(elev.shape, np.float32)
        bx = by = bm = np.zeros(elev.shape, np.float32)
        for t in range(1, width + 1):
            ax += _shift(ux, t * ny, t * nx); ay += _shift(uy, t * ny, t * nx)
            am += _shift(mag, t * ny, t * nx)
            bx += _shift(ux, -t * ny, -t * nx); by += _shift(uy, -t * ny, -t * nx)
            bm += _shift(mag, -t * ny, -t * nx)
        # azimuthal asymmetry = 1 - cosine similarity of the two side-mean directions
        dot = (ax * bx + ay * by) / np.maximum(np.sqrt((ax * ax + ay * ay) * (bx * bx + by * by)), 1e-9)
        asym = np.clip((1.0 - dot) * 0.5, 0.0, 1.0).astype(np.float32)
        mag_asym = np.clip(np.abs(am - bm) / np.maximum(am + bm, 1e-9), 0.0, 1.0).astype(np.float32)
        out[name] = dict(azimuth=asym, magnitude=mag_asym)
        np.maximum(best_asym, asym, out=best_asym)
        np.maximum(best_mag_asym, mag_asym, out=best_mag_asym)
    return dict(azimuth_asymmetry=best_asym, magnitude_asymmetry=best_mag_asym,
                per_orientation=out)


def h47d_strain_partitioning(g: Grid, valid: np.ndarray, sigma: float = 2.0) -> dict:
    """H47-D: Laplacian of the dilatation/shear partitioning ratio."""
    dil = _fill(g.band("geod_dilaterate"), valid)
    shr = _fill(g.band("geod_shearrate"), valid)
    inv = _fill(g.band("geod_2ndinv"), valid)
    eps = float(np.percentile(shr[valid], 5)) if valid.any() else 1e-6
    rho = np.abs(dil) / (shr + max(eps, 1e-6))
    rho_s = ndi.gaussian_filter(rho, sigma, mode="nearest").astype(np.float32)
    lap = ndi.laplace(rho_s).astype(np.float32)
    # both signs are informative: a dilatational ridge and a dilatational trough both mark
    # a partitioning boundary, so score |Laplacian| but keep the signed field for inspection
    abs_lap = np.abs(lap)
    return dict(ratio=rho_s, laplacian=lap,
                score=robust_unit(abs_lap, valid, pct=99.5),
                second_invariant=robust_unit(inv, valid, pct=99.5))


def h47e_signed_basement_step(g: Grid, valid: np.ndarray, corr: dict,
                              halfwidth: int = 4, min_run: int = 10) -> dict:
    """H47-E: signed cross-strike basement step, persisted along strike."""
    base = _fill(g.band("depth_to_base_surf"), valid)
    best_signed = np.zeros(base.shape, np.float32)
    best_persist = np.zeros(base.shape, np.float32)
    flip = np.zeros(base.shape, np.float32)
    per = {}
    for name, (sy, sx) in ORIENTATIONS:
        ny, nx = -sx, sy
        deep = np.zeros(base.shape, np.float32)
        shallow = np.zeros(base.shape, np.float32)
        for t in range(1, halfwidth + 1):
            deep += _shift(base, t * ny, t * nx)
            shallow += _shift(base, -t * ny, -t * nx)
        step = (deep - shallow) / (2.0 * halfwidth)         # signed cross-strike gradient
        per[name] = step.astype(np.float32)
        # persistence along the strike: mean of |step| with consistent sign over a run
        sgn = np.sign(step).astype(np.float32)
        run = ndi.uniform_filter1d(sgn, min_run, axis=0 if abs(sy) < abs(sx) else 1)
        consist = np.abs(run).astype(np.float32)            # 1.0 = sign held for min_run px
        mag = np.abs(step).astype(np.float32)
        cand = (mag * consist).astype(np.float32)
        np.maximum(best_signed, cand, out=best_signed)
        np.maximum(best_persist, consist, out=best_persist)
        # sign-reversal (accommodation zone) locator
        np.maximum(flip, (mag * (1.0 - consist)).astype(np.float32), out=flip)
    return dict(step_score=robust_unit(best_signed, valid, pct=99.5),
                persistence=best_persist, sign_flip=robust_unit(flip, valid, pct=99.5),
                per_orientation=per)


# --------------------------------------------------------------------------- assembly
def build_all(g: Grid, valid: np.ndarray, scales=(1.0, 2.0, 3.0)) -> dict:
    """Compute every H47 surface.  Returns a dict of float32 arrays in [0,1] where scored."""
    corr = corroboration(g, valid, sigmas=scales)
    a = h47a_vacancy_residual(g, valid, corr)
    b = h47b_braid_number(g, valid, corr)
    c = h47c_drainage_asymmetry(g, valid)
    d = h47d_strain_partitioning(g, valid)
    e = h47e_signed_basement_step(g, valid, corr)
    unit = lambda x: np.nan_to_num(robust_unit(np.asarray(x, np.float32), valid, pct=99.5),
                                   nan=0.0).astype(np.float32)
    surfaces = dict(
        A_vacancy=a["residual"].astype(np.float32),
        A_vacancy_signed=unit(a["signed"]),
        B_braid=b["braid"].astype(np.float32),
        C_drain_asym=c["azimuth_asymmetry"].astype(np.float32),
        C_drain_mag=c["magnitude_asymmetry"].astype(np.float32),
        D_strain=unit(d["score"]),
        E_basement=unit(e["step_score"]),
        E_persistence=e["persistence"].astype(np.float32),
        E_signflip=unit(e["sign_flip"]),
        corr_count=unit(corr["count"]),
        corr_mean=corr["mean"].astype(np.float32),
        corr_max=unit(corr["max"]),
    )
    for k, v in surfaces.items():
        assert v.shape == (HEIGHT, WIDTH), k
    return dict(surfaces=surfaces, corroboration=corr, A=a, B=b, C=c, D=d, E=e)
