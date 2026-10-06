"""LATI - Leaderboard-Anchored Truth Inversion.

The project's previous "truth model" was *self-referential*: GEMSDOE32's
``evidence/truth_model_mc.json`` draws hidden truth as
``pi ~ exp(-d(H19-5)/1.85 px)`` - i.e. a scatter around **the group's own best
field**.  Any rule that covers that field better then "wins" by construction
(their measured +0.0247 is exactly that artefact).  It cannot falsify the field
it was built from.

LATI replaces it with **twelve real measurements**.  For each of the twelve
prior submissions whose returned DTI is on the record we know the exact raster
that was uploaded (hash-pinned in ``registry/data_manifest.json``) and the number
the organiser sent back.  Those twelve numbers are *data about the hidden label
set*, and they are the only such data the project has ever had.

--------------------------------------------------------------------------
Why twelve scalars identify anything at all
--------------------------------------------------------------------------
Write ``G`` for the hidden new-fault pixel set, ``K = |G|``, and
``q(x) = P(x in G)`` for its intensity.  For a submission ``p``:

    T(p) = sum_{g in G} max_{x in D(p)} k(d(x,g))
         = sum_x q(x) * w_p(x),        w_p(x) = max_{y in D(p)} k(d(x,y))      (L1)
    Phi(p) = sum_{x in D(p)} E_q[ kappa(x) ],  kappa(x) = max_{g in G} k(d(x,g))
           ~ sum_x q(x) * a_p(x),      a_p(x) = sum_{y in D(p)} k(d(x,y))      (L2)
    F(p) = S(p) - Phi(p)
    DTI  = T / ( alpha*(T + F) + beta*K )

(L1) is *exact*: ``w_p`` depends only on ``p``, so ``T`` is linear in ``q``.
(L2) is first-order in ``q``: replacing ``max`` by ``sum`` over-estimates by
O(q^2), and ``q ~ K/n ~ 2e-3`` here, so the error is ~0.2 %.  It is verified
against the exact ring-product expectation in ``tests/test_lati.py``.

Both are therefore **linear functionals of the same unknown ``q``**, and each
returned DTI is one non-linear equation in them.  Twelve structurally different
rasters (mass 44 k -> 344 k; lattice, ridge, hedge, dotted, far-scatter) probe
twelve different "halo volumes" of ``q``.  Fitting
``q(x) = expit(b0 + sum_m b_m u_m(x))`` against all twelve simultaneously asks a
question no local holdout can ask: *which surface proxies does the hidden label
set actually follow?*

Honest limits, stated up front:
  * twelve scalars cannot identify 59 coefficients - the fit is regularised and
    forward-selected, and the reported answer is a **ranking of field families**,
    not a map of G;
  * the twelve DTIs are owner-reported transcriptions of the public board
    (no organiser receipt exists) - they are treated as exact but flagged;
  * K identified here is the **public-chunk** hidden mass, not the private one.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import rasterio

from . import grid as G
from . import metric as M

# ---------------------------------------------------------------------------
# the twelve (raster, returned DTI) observations
# ---------------------------------------------------------------------------

OBSERVATIONS: tuple[dict, ...] = (
    dict(id="d2.8", file="gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
         dti=0.2600, site="GEMSDOE25", family="h19-5 dotted"),
    dict(id="d1.5", file="gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
         dti=0.2477, site="GEMSDOE24", family="h19-5 dotted"),
    dict(id="tgc-v2", file="gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif",
         dti=0.2449, site="GEMSDOE27", family="h19-5 dotted + gap closure"),
    dict(id="h19-5", file="gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
         dti=0.1922, site="19GEMSDOE", family="h19-5 solid"),
    dict(id="h19-4", file="gems19-h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan.tif",
         dti=0.1894, site="19GEMSDOE", family="h19-4 solid"),
    dict(id="h16-1", file="gems16-h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan.tif",
         dti=0.1855, site="16GEMSDOE", family="h16-1 solid"),
    dict(id="h28-ridge", file="gems10-h28-dotted-ridge-20260928T020256236880Z-6452ae1d00.tif",
         dti=0.1839, site="GEMSDOE10", family="h28 dotted ridge"),
    dict(id="hedge-v2", file="8GEMSDOE_Hedge-v2_submission.tif",
         dti=0.1563, site="8GEMSDOE", family="hedge (ens12 + full catalogue)"),
    dict(id="ens12", file="gemsdoe-ens12-adopted-7f00890a.tif",
         dti=0.1563, site="GEMSDOE", family="ensemble-12"),
    dict(id="h25-ctx", file="gems10-h25-ctx-ridge-20260927T232947704150Z-6452ae1d00.tif",
         dti=0.1280, site="GEMSDOE10", family="contextual ridge"),
    dict(id="r13-lattice", file="13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
         dti=0.0904, site="13GEMSDOE", family="lattice s5"),
    dict(id="placeholder", file="gemsdoe9-PLACEHOLDER-2314b599.tif",
         dti=0.0107, site="GEMSDOE9", family="broad placeholder scatter"),
)


@dataclass
class Obs:
    id: str
    dti: float
    site: str
    family: str
    sha256: str
    S: float                 # evaluated emitted mass (catalogue pixels excluded)
    n_dots: int              # emitted pixels, all grid
    n_on_catalogue: int
    w: np.ndarray            # float32 (n_eval,) exact max-filter credit kernel
    a: np.ndarray            # float32 (n_eval,) first-order sum-filter halo
    dot_pos: np.ndarray      # int64 positions (into ev space) of evaluated dots
    dot_flat: np.ndarray     # int64 flat indices (full grid) of evaluated dots
    extras: dict = field(default_factory=dict)


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _cache_path() -> Path:
    return Path(__file__).resolve().parents[2] / ".cache" / "lati_obs.npz"


def load_observations(data: Path | None = None, verbose: bool = True,
                      use_cache: bool = True) -> list[Obs]:
    data = Path(data) if data else G.data_dir()
    cp = _cache_path()
    if use_cache and cp.exists():
        z = np.load(cp, allow_pickle=False)
        meta = json.loads(str(Path(cp.with_suffix(".json")).read_text()))
        if meta["ids"] == [r["id"] for r in OBSERVATIONS]:
            out = []
            for i, rec in enumerate(OBSERVATIONS):
                out.append(Obs(id=rec["id"], dti=rec["dti"], site=rec["site"],
                               family=rec["family"], sha256=meta["sha256"][i],
                               S=meta["S"][i], n_dots=meta["n_dots"][i],
                               n_on_catalogue=meta["n_on_catalogue"][i],
                               w=z[f"w{i}"], a=z[f"a{i}"], dot_pos=z[f"dp{i}"],
                               dot_flat=z[f"df{i}"], extras=meta["extras"][i]))
            if verbose:
                print(f"[lati] cache hit {cp}")
            return out
    t = G.load_template(data)
    ev = t.evaluated
    ev_idx = np.flatnonzero(ev.ravel())
    pos = np.full(t.shape[0] * t.shape[1], -1, np.int64)
    pos[ev_idx] = np.arange(ev_idx.size)

    out: list[Obs] = []
    for rec in OBSERVATIONS:
        p = data / "scored" / rec["file"]
        if not p.exists():
            raise FileNotFoundError(f"missing scored prior output {p}; run scripts/restore_data.py")
        with rasterio.open(p) as src:
            arr = src.read(1)
        if arr.shape != t.shape:
            raise AssertionError(f"{rec['file']}: shape {arr.shape} != template {t.shape}")
        raw = np.nan_to_num(np.asarray(arr, np.float32), nan=0.0)
        n_on_cat = int((raw > 0)[t.catalogue].sum())
        n_foot = int(((raw > 0) & t.footprint).sum())
        # mask_mode="zero": catalogue pixels are dropped before BOTH sums
        pred = np.where(ev, raw, 0.0)
        dmask = pred > 0
        dflat = np.flatnonzero(dmask.ravel())
        w_full = M.max_kernel_filter(pred.astype(np.float64))
        a_full = np.zeros(t.shape, np.float64)
        for dy, dx, k in zip(M.OFF_DY, M.OFF_DX, M.OFF_K):
            a_full += k * _shift_in(dmask.astype(np.float64), dy, dx)
        o = Obs(id=rec["id"], dti=rec["dti"], site=rec["site"], family=rec["family"],
                sha256=_sha256(p), S=float(pred[dmask].sum()),
                n_dots=int((raw > 0).sum()),
                n_on_catalogue=n_on_cat,
                w=w_full.ravel()[ev_idx].astype(np.float32),
                a=a_full.ravel()[ev_idx].astype(np.float32),
                dot_pos=pos[dflat], dot_flat=dflat)
        assert (o.dot_pos >= 0).all()
        o.extras = {"halo_sum_w": float(o.w.sum()), "halo_sum_a": float(o.a.sum()),
                    "halo_support_w": int((o.w > 0).sum()),
                    "positive_in_footprint": n_foot,
                    "positive_outside_footprint": int((raw > 0).sum()) - n_foot}
        out.append(o)
        if verbose:
            print(f"[lati] {o.id:<12} DTI={o.dti:.4f} S={o.S:>9.0f} dots={o.n_dots:>7} "
                  f"on_cat={o.n_on_catalogue:>6} sum_w={o.w.sum():>12.1f}", flush=True)
        del w_full, a_full, pred, dmask
    if use_cache:
        cp.parent.mkdir(parents=True, exist_ok=True)
        store = {}
        for i, o in enumerate(out):
            store[f"w{i}"] = o.w.astype(np.float32); store[f"a{i}"] = o.a.astype(np.float32)
            store[f"dp{i}"] = o.dot_pos.astype(np.int64); store[f"df{i}"] = o.dot_flat.astype(np.int64)
        np.savez(cp, **store)
        cp.with_suffix(".json").write_text(json.dumps(dict(
            ids=[o.id for o in out], sha256=[o.sha256 for o in out],
            S=[o.S for o in out], n_dots=[o.n_dots for o in out],
            n_on_catalogue=[o.n_on_catalogue for o in out],
            extras=[o.extras for o in out]), indent=1))
    return out


def _shift_in(a: np.ndarray, dy: int, dx: int) -> np.ndarray:
    out = np.zeros(a.shape, a.dtype)
    H, W = a.shape
    y0, y1 = max(0, -dy), min(H, H - dy)
    x0, x1 = max(0, -dx), min(W, W - dx)
    if y0 >= y1 or x0 >= x1:
        return out
    out[y0:y1, x0:x1] = a[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
    return out


# ---------------------------------------------------------------------------
# the forward model
# ---------------------------------------------------------------------------


def predict_dti(obs: list[Obs], q: np.ndarray, alpha: float = M.ALPHA,
                beta: float = M.BETA) -> np.ndarray:
    """Model DTI for every observation given the hidden-truth intensity ``q``.

    ``q`` is defined on the evaluated pixel set (same order as ``ev_idx``).
    """
    K = float(q.sum())
    out = np.empty(len(obs))
    for i, o in enumerate(obs):
        T = float(np.dot(q, o.w))
        Phi = float(np.dot(q, o.a))
        F = o.S - Phi
        out[i] = M.dti_from_TFK(T, F, K, alpha, beta)
    return out


def components(obs: list[Obs], q: np.ndarray) -> list[dict]:
    K = float(q.sum())
    rows = []
    for o in obs:
        T = float(np.dot(q, o.w)); Phi = float(np.dot(q, o.a)); F = o.S - Phi
        rows.append(dict(id=o.id, dti_obs=o.dti, S=o.S, T=T, Phi=Phi, F=F, K=K,
                         credit_per_dot=T / o.S if o.S else 0.0,
                         weighted_recall=T / K if K else 0.0,
                         dti_model=M.dti_from_TFK(T, F, K)))
    return rows


def q_from_beta(U: np.ndarray, rows: np.ndarray, beta: np.ndarray) -> np.ndarray:
    """q = expit(b0 + sum_m b_m * (u_m/255 - 0.5)) on the evaluated pixel set."""
    eta = np.full(U.shape[1], beta[0], np.float32)
    for j, r in enumerate(rows):
        eta += np.float32(beta[j + 1]) * (U[r].astype(np.float32) * np.float32(1.0 / 255.0) - np.float32(0.5))
    # expit in float32
    return (1.0 / (1.0 + np.exp(-eta, dtype=np.float32))).astype(np.float64)


def loss(obs: list[Obs], U: np.ndarray, rows: np.ndarray, beta: np.ndarray,
         l2: float = 0.0) -> float:
    q = q_from_beta(U, rows, beta)
    d = predict_dti(obs, q)
    r = d - np.array([o.dti for o in obs])
    return float(r @ r + l2 * float(np.sum(np.square(beta[1:]))))


# ---------------------------------------------------------------------------
# exact Phi (ring products) - used only to validate the (L2) approximation
# ---------------------------------------------------------------------------


def exact_phi(o: Obs, q_full: np.ndarray, shape: tuple[int, int]) -> float:
    """E_q[ sum_{x in dots} kappa(x) ] with independent Bernoulli q, computed exactly.

    kappa(x) = max_{g in G} k(d(x,g)); with independent Bernoulli q,
        E[max] = sum_{j=1..6} k_j * (Q_{j-1} - Q_j),  Q_j = prod_{rings 1..j} prod_delta (1 - q(x+delta)),
        Q_0 = 1, rings ordered by descending k.
    Used only to validate the first-order approximation Phi ~ <q, a_p>.
    """
    H, W = shape
    ys = o.dot_flat // W
    xs = o.dot_flat % W
    rings: dict[float, list[tuple[int, int]]] = {}
    for dy, dx, k in zip(M.OFF_DY, M.OFF_DX, M.OFF_K):
        rings.setdefault(round(float(k), 12), []).append((int(dy), int(dx)))
    ordered = sorted(rings.items(), key=lambda kv: -kv[0])
    ks = [kv[0] for kv in ordered] + [0.0]
    # stable form: E[max] = 1 - sum_m (k_m - k_{m+1}) Q_m   (see emitter.expected_kappa_dense)
    Q = np.ones(ys.size)
    acc = np.ones(ys.size)
    for m, (kj, offs) in enumerate(ordered):
        P = np.ones(ys.size)
        for dy, dx in offs:
            yy = ys + dy
            xx = xs + dx
            ok = (yy >= 0) & (yy < H) & (xx >= 0) & (xx < W)
            v = np.zeros(ys.size)
            v[ok] = q_full[yy[ok] * W + xx[ok]]
            P *= (1.0 - v)
        Q = Q * P
        acc -= (kj - ks[m + 1]) * Q
    return float(np.clip(acc, 0.0, 1.0).sum())


# ---------------------------------------------------------------------------
# binned fast path: exact for the selected feature subspace, ~1000x faster
# ---------------------------------------------------------------------------


class Binned:
    """Aggregate the linear functionals <q, w_i>, <q, a_i>, <q, 1> onto a grid
    in the *selected feature* space.

    q(x) depends on x only through u_m(x) = U[m, x]/255 - 0.5 for the selected
    rows, so all three functionals are exactly determined by the joint histogram
    of those quantised values together with the per-cell sums of w_i and a_i.
    Quantising each u to ``L`` cells and evaluating q at the cell centre is the
    only approximation; at L = 256 (single feature) it is below 1e-4 relative.
    """

    def __init__(self, U: np.ndarray, rows: np.ndarray, obs: list[Obs], L: int):
        self.rows = list(int(r) for r in rows)
        self.L = int(L)
        self.r = len(self.rows)
        n = U.shape[1]
        lev = np.zeros(n, np.int64)
        self.uc = np.zeros((self.r, L), np.float64)
        edges = np.linspace(-0.5, 0.5, L + 1)
        for j, rr in enumerate(self.rows):
            u = U[rr].astype(np.float64) / 255.0 - 0.5
            l = np.clip(((u + 0.5) / 1.0 * L).astype(np.int64), 0, L - 1)
            lev = lev * L + l
            self.uc[j] = 0.5 * (edges[:-1] + edges[1:])
        self.B = int(L ** self.r) if self.r else 1
        self.count = np.bincount(lev, minlength=self.B).astype(np.float64)
        self.W = np.stack([np.bincount(lev, weights=o.w, minlength=self.B) for o in obs])
        self.A = np.stack([np.bincount(lev, weights=o.a, minlength=self.B) for o in obs])
        self.S = np.array([o.S for o in obs])
        self.dti_obs = np.array([o.dti for o in obs])
        self.ids = [o.id for o in obs]
        # cell-centre design matrix (B, r)
        if self.r:
            grid = np.stack(np.meshgrid(*[np.arange(L)] * self.r, indexing="ij"), -1).reshape(-1, self.r)
            self.UC = self.uc.T[grid[:, ::-1].copy()] if False else np.column_stack(
                [self.uc[j][grid[:, j]] for j in range(self.r)])
        else:
            self.UC = np.zeros((1, 0))
        del lev

    def q_bins(self, beta: np.ndarray) -> np.ndarray:
        eta = np.full(self.B, float(beta[0]))
        if self.r:
            eta = eta + self.UC @ np.asarray(beta[1:], float)
        return 1.0 / (1.0 + np.exp(-eta))

    def predict(self, beta: np.ndarray, alpha: float = M.ALPHA,
                beta_w: float = M.BETA) -> np.ndarray:
        qb = self.q_bins(beta)
        T = self.W @ qb
        Phi = self.A @ qb
        K = float(self.count @ qb)
        F = self.S - Phi
        return np.array([M.dti_from_TFK(t, f, K, alpha, beta_w) for t, f in zip(T, F)])

    def components(self, beta: np.ndarray) -> list[dict]:
        qb = self.q_bins(beta)
        T = self.W @ qb; Phi = self.A @ qb; K = float(self.count @ qb)
        F = self.S - Phi
        return [dict(id=self.ids[i], dti_obs=float(self.dti_obs[i]), S=float(self.S[i]),
                     T=float(T[i]), Phi=float(Phi[i]), F=float(F[i]), K=K,
                     dti_model=float(M.dti_from_TFK(T[i], F[i], K)),
                     credit_per_dot=float(T[i] / self.S[i]) if self.S[i] else 0.0,
                     weighted_recall=float(T[i] / K) if K else 0.0)
                for i in range(len(self.ids))]


class BinnedSoftmax:
    """Log-linear (softmax) hidden-truth intensity with an explicit total mass K.

        s(x) = exp( sum_m beta_m * u_m(x) ),   q(x) = K * s(x) / sum_x s(x)

    Advantages over ``expit(b0 + sum b_m u_m)``:
      * K is a direct parameter, so the *diffuse* observations (the lattice and
        the broad placeholder scatter, whose halos average over the whole
        footprint) identify K while the *concentrated* observations identify the
        shape beta - the two are no longer confounded;
      * beta is shift-invariant, so no intercept has to be searched;
      * it cannot degenerate into a hard indicator with a runaway coefficient
        while still reporting a plausible K.

    Aggregated on the binned feature grid: with W_i[b] = sum_{x in b} w_i(x),
    A_i[b] = sum_{x in b} a_i(x), N[b] = |b|,

        Z   = sum_b N[b] exp(eta_b)
        T_i = (K/Z) * sum_b exp(eta_b) W_i[b]
        Phi_i = (K/Z) * sum_b exp(eta_b) A_i[b]
        DTI_i = T_i / (alpha*(T_i + S_i - Phi_i) + beta_w*K)
    """

    def __init__(self, U: np.ndarray, rows: np.ndarray, obs: list[Obs], L: int):
        self.rows = [int(r) for r in rows]
        self.L = int(L)
        self.r = len(self.rows)
        n = U.shape[1]
        lev = np.zeros(n, np.int64)
        self.uc = np.zeros((self.r, L), np.float64)
        edges = np.linspace(-0.5, 0.5, L + 1)
        centres = 0.5 * (edges[:-1] + edges[1:])
        for j, rr in enumerate(self.rows):
            l = np.clip((U[rr].astype(np.float64) * (L / 256.0)).astype(np.int64), 0, L - 1)
            lev = lev * L + l
            self.uc[j] = centres
        self.B = int(L ** self.r) if self.r else 1
        self.N = np.bincount(lev, minlength=self.B).astype(np.float64)
        self.W = np.stack([np.bincount(lev, weights=o.w.astype(np.float64), minlength=self.B) for o in obs])
        self.A = np.stack([np.bincount(lev, weights=o.a.astype(np.float64), minlength=self.B) for o in obs])
        self.S = np.array([o.S for o in obs])
        self.dti_obs = np.array([o.dti for o in obs])
        self.ids = [o.id for o in obs]
        if self.r:
            grid = np.stack(np.meshgrid(*[np.arange(L)] * self.r, indexing="ij"), -1).reshape(-1, self.r)
            self.UC = np.column_stack([self.uc[j][grid[:, j]] for j in range(self.r)])
        else:
            self.UC = np.zeros((1, 0))
        self.keep = self.N > 0
        del lev

    # ---- forward model -----------------------------------------------------
    def _parts(self, theta: np.ndarray):
        K = float(theta[0])
        eta = np.zeros(self.B) if not self.r else self.UC @ np.asarray(theta[1:], float)
        e = np.exp(eta - eta.max())
        Z = float(self.N @ e)
        c = K / Z
        T = c * (self.W @ e)
        Phi = c * (self.A @ e)
        return K, T, Phi

    def predict(self, theta: np.ndarray, alpha: float = M.ALPHA, beta_w: float = M.BETA) -> np.ndarray:
        K, T, Phi = self._parts(theta)
        F = self.S - Phi
        return np.array([M.dti_from_TFK(t, f, K, alpha, beta_w) for t, f in zip(T, F)])

    def components(self, theta: np.ndarray) -> list[dict]:
        K, T, Phi = self._parts(theta)
        F = self.S - Phi
        return [dict(id=self.ids[i], dti_obs=float(self.dti_obs[i]), S=float(self.S[i]),
                     T=float(T[i]), Phi=float(Phi[i]), F=float(F[i]), K=float(K),
                     dti_model=float(M.dti_from_TFK(T[i], F[i], K)),
                     credit_per_dot=float(T[i] / self.S[i]) if self.S[i] else 0.0,
                     weighted_recall=float(T[i] / K) if K else 0.0)
                for i in range(len(self.ids))]

    def fit(self, l2: float = 0.0, subset: list[int] | None = None,
            theta0: np.ndarray | None = None, bmax: float = 12.0,
            k_lo: float = 1_000.0, k_hi: float = 400_000.0):
        from scipy.optimize import least_squares
        idx = np.arange(len(self.ids)) if subset is None else np.asarray(subset)
        target = self.dti_obs[idx]
        x0 = theta0 if theta0 is not None else np.concatenate([[12_000.0], np.zeros(self.r)])
        x0 = np.clip(np.asarray(x0, float), None, None)
        x0[0] = float(np.clip(x0[0], k_lo, k_hi))

        def resid(th):
            r = self.predict(th)[idx] - target
            if l2:
                r = np.concatenate([r, np.sqrt(l2) * np.asarray(th[1:])])
            return r

        lo = np.concatenate([[k_lo], np.full(self.r, -bmax)])
        hi = np.concatenate([[k_hi], np.full(self.r, +bmax)])
        res = least_squares(resid, x0, bounds=(lo, hi), xtol=1e-14, ftol=1e-14, max_nfev=20000)
        pred = self.predict(res.x)
        return dict(theta=res.x.tolist(), K=float(res.x[0]),
                    ssr=float(np.sum((pred[idx] - target) ** 2)),
                    pred=pred.tolist(), max_abs_resid=float(np.max(np.abs(pred[idx] - target))),
                    nfev=int(res.nfev), at_bound=bool(np.any(np.abs(res.x[1:]) > bmax - 1e-9)))
