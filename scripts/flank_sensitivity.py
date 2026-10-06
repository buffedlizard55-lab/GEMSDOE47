#!/usr/bin/env python3
"""Sensitivity of the H47 flank hypothesis to the contested 0.2778 attribution.

evidence/flank_robustness_13obs.json showed that adding the reported-0.2778
raster ``h33-2-b2`` - which contains ZERO dots in the catalogue flank, because it
was *built* by deleting them - flips the flank coefficient from +6.18 to +1.42
and turns a +55.7% LOO gain into a -64.0% LOO loss.

But GEMSDOE42's own prior-results.csv flags that score:
  "attribution_conflict_site_says_unscored_official_board_has_unlinked_0.2778_row"

So the falsification rests on one contested number.  This script sweeps the
assumed DTI of that single observation from 0.1800 to 0.3000 and reports the
flank coefficient and the LOO gain at each value, giving the exact break-even.

    python3 scripts/flank_sensitivity.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems47 import features as FEAT   # noqa: E402
from gems47 import grid as G          # noqa: E402
from gems47 import hypotheses as HY   # noqa: E402
from gems47 import lati, metric as M  # noqa: E402
from gems47.scripts_common import rank_u8_inplace  # noqa: E402

H33 = Path("/home/user/refs/GEMSDOE32/docs/downloads/"
           "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif")
L2, BMAX, KLO, KHI = 1e-5, 12.0, 2_000.0, 120_000.0


def h33_obs(dti: float, t, ev, ev_idx, shape) -> lati.Obs:
    with rasterio.open(H33) as s:
        v = np.nan_to_num(s.read(1).astype(np.float32))
    pred = np.where(ev, v, 0.0)
    dm = pred > 0
    dflat = np.flatnonzero(dm.ravel())
    pos = np.full(shape[0] * shape[1], -1, np.int64)
    pos[ev_idx] = np.arange(ev_idx.size)
    w = M.max_kernel_filter(pred.astype(np.float64))
    a = np.zeros(shape)
    for dy, dx, k in zip(M.OFF_DY, M.OFF_DX, M.OFF_K):
        a += k * lati._shift_in(dm.astype(np.float64), dy, dx)
    return lati.Obs(id="h33-2-b2", dti=dti, site="GEMSDOE32",
                    family="flank-pruned (reported 0.2778, attribution CONFLICTED)",
                    sha256=hashlib.sha256(H33.read_bytes()).hexdigest(),
                    S=float(pred[dm].sum()), n_dots=int((v > 0).sum()),
                    n_on_catalogue=int((v > 0)[t.catalogue].sum()),
                    w=w.ravel()[ev_idx].astype(np.float32),
                    a=a.ravel()[ev_idx].astype(np.float32),
                    dot_pos=pos[dflat], dot_flat=dflat, extras={})


def fit(uset, obs):
    V = np.stack(uset)
    L = {1: 256, 2: 64}[len(uset)]
    bm = lati.BinnedSoftmax(V, list(range(len(uset))), obs, L)
    f = bm.fit(l2=L2, bmax=BMAX, k_lo=KLO, k_hi=KHI)
    f["ssr"] = float(np.sum((bm.predict(np.array(f["theta"])) - bm.dti_obs) ** 2))
    loo = 0.0
    for h in range(len(obs)):
        sub = [i for i in range(len(obs)) if i != h]
        g = bm.fit(l2=L2, subset=sub, theta0=np.array(f["theta"]), bmax=BMAX, k_lo=KLO, k_hi=KHI)
        loo += float(bm.predict(np.array(g["theta"]))[h] - obs[h].dti) ** 2
    f["loo"] = loo
    return f


def main() -> int:
    t0 = time.time()
    t = G.load_template()
    ev, shape = t.evaluated, t.shape
    obs12 = lati.load_observations(verbose=False)
    st = FEAT.build_stack(verbose=False)
    ev_idx, U, names = st["ev_idx"], st["U"], list(st["names"])
    HL = HY.build_layers(t)

    def prox(oid, cap=40.0):
        o = [x for x in obs12 if x.id == oid][0]
        m = np.zeros(shape[0] * shape[1], bool)
        m[o.dot_flat] = True
        return rank_u8_inplace((-FEAT.dist_px(m.reshape(shape), cap).ravel()[ev_idx]).astype(np.float32))

    PX = prox("d2.8")
    UF = rank_u8_inplace(HL["flank_halo_0_3"].ravel()[ev_idx].astype(np.float32))

    d_cat = HL["_diag_d_catalogue"]
    halo3 = ev & (d_cat > 0) & (d_cat <= M.RANGE_PX)
    with rasterio.open(H33) as s:
        h33dots = np.nan_to_num(s.read(1)) > 0
    rows = []
    grid = [None, 0.1800, 0.2000, 0.2200, 0.2400, 0.2477, 0.2550, 0.2600, 0.2700, 0.2708,
            0.2778, 0.2900, 0.3000]
    print("assumed   n  flank_beta   K_base     K_flank   LOO_base   LOO_flank   LOO_gain  verdict")
    print("h33 DTI      obs")
    for dti in grid:
        if dti is None:
            obs, tag = list(obs12), "excluded "
        else:
            obs = list(obs12) + [h33_obs(dti, t, ev, ev_idx, shape)]
            tag = f"{dti:.4f}  "
        fb = fit([PX], obs)
        ff = fit([PX, UF], obs)
        bf = ff["theta"][2]
        gain = 100.0 * (fb["loo"] - ff["loo"]) / fb["loo"]
        verdict = "flank SUPPORTED" if ff["loo"] < fb["loo"] - 1e-9 else "flank NOT supported"
        rows.append(dict(assumed_h33_dti=dti, n_obs=len(obs), flank_beta=float(bf),
                         K_base=fb["theta"][0], K_flank=ff["theta"][0],
                         loo_base=fb["loo"], loo_flank=ff["loo"], loo_gain_pct=gain,
                         verdict=verdict, theta_base=fb["theta"], theta_flank=ff["theta"]))
        print(f"{tag}  {len(obs):>3}   {bf:>+9.3f}  {fb['theta'][0]:>9,.0f}  {ff['theta'][0]:>9,.0f}"
              f"   {fb['loo']:.6f}   {ff['loo']:.6f}   {gain:>+7.1f}%  {verdict}")

    sup = [r for r in rows if r["assumed_h33_dti"] is not None and r["loo_gain_pct"] > 0]
    breakeven = None
    if sup:
        breakeven = max(r["assumed_h33_dti"] for r in sup)
    out = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        question="how much does the H47 flank falsification depend on the contested 0.2778?",
        h33_raster=dict(path=str(H33), sha256=None,
                        dots=int(h33dots.sum()),
                        dots_in_catalogue_flank_0_300m=int((h33dots & halo3).sum()),
                        note="built by DELETING every dot within 2 px of the catalogue, "
                             "so it is the only direct flank ablation in the whole family"),
        attribution_flag=("GEMSDOE42/docs/prior-results.csv: 'attribution_conflict_site_says_"
                          "unscored_official_board_has_unlinked_0.2778_row'"),
        sweep=rows,
        break_even_h33_dti=breakeven,
        conclusion=(
            "The flank layer is supported by the twelve flank-agnostic observations "
            "(LOO gain +55.7%, beta=+6.18) and refuted as soon as the flank-PRUNED "
            "h33-2-b2 raster is admitted at its reported 0.2778 (LOO gain -64.0%, "
            "beta collapses to +1.42). The break-even assumed score is "
            f"{breakeven if breakeven is not None else 'below every value tested'}: "
            "above it the flank is refuted, below it supported. Because the single "
            "observation that decides the question is itself attribution-conflicted, "
            "H47 flank re-occupation is NOT SHIPPED - the project rule is never to "
            "spend a submission slot on a candidate that a direct local ablation "
            "contradicts."),
        seconds=round(time.time() - t0, 1))
    out["h33_raster"]["sha256"] = hashlib.sha256(H33.read_bytes()).hexdigest()
    (ROOT / "evidence" / "flank_sensitivity.json").write_text(json.dumps(out, indent=1))
    print(f"\nbreak-even assumed h33-2-b2 DTI: {breakeven}")
    print(f"wrote evidence/flank_sensitivity.json ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
