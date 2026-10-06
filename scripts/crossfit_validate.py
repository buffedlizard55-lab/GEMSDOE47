#!/usr/bin/env python3
"""Cross-fitted validation: the only test that can honestly rank a NEW candidate.

Why this script exists
----------------------
``scripts/build_final.py`` forward-selected a belief model on all thirteen
observations and then emitted the dot set that maximises the predicted DTI
*under that same model*.  The result was F1 = 0.62 against the incumbent's
0.2653 - a 2.4x "improvement" that no independent frame corroborated
(F2 0.057, F3 0.014, F4 0.032, F5 0.015, all far below the incumbent).  Two
biases produce exactly that pattern:

  B1 optimizer's curse - a candidate chosen to maximise a fitted objective is
     scored by the same fitted objective, so its in-sample advantage is
     guaranteed and meaningless;
  B2 pool-selection bias - the candidate layers were themselves ranked by LOO on
     the same thirteen observations, so even the LOO number is optimistic.

Both are removed here:
  * the layer pool is fixed a priori from GEOLOGY (the twelve layers the GEMS
    problem statement implies for "faults indicative of geothermal resources"),
    never from the data;
  * forward selection runs INSIDE each fold;
  * the candidate built from fold A's model is scored by fold B's model, and
    vice versa, and the incumbent is scored by the same out-of-fold model so the
    comparison is paired.

Verdict rule (pre-registered): ship only if the candidate beats the incumbent on
the mean out-of-fold predicted DTI in BOTH folds.

    python3 scripts/crossfit_validate.py
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

from gems47 import emitter as E       # noqa: E402
from gems47 import features as FEAT   # noqa: E402
from gems47 import grid as G          # noqa: E402
from gems47 import hypotheses as HY   # noqa: E402
from gems47 import lati, metric as M  # noqa: E402
from gems47.scripts_common import rank_u8_inplace  # noqa: E402

L2, BMAX, KLO, KHI = 1e-5, 12.0, 2_000.0, 120_000.0
LEVELS = {1: 256, 2: 64, 3: 32, 4: 20, 5: 14, 6: 12}
H33 = Path("/home/user/refs/GEMSDOE32/docs/downloads/"
           "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif")

# A PRIORI POOL - fixed from geology before any fit was run on these data.
# "Faults indicative of geothermal resources" in the Basin and Range are, in the
# standard play (opportunity 2 / play element 2 of the GEMS problem statement):
#   * actively straining ground            -> geod_* (GNSS/InSAR strain rate)
#   * hydrothermally altered ground        -> rad_ThK / rad_UK (K-metasomatism
#                                             and silica sinter depress Th/K)
#   * fluid discharge at the surface       -> thermal_* (GDR springs and wells)
#   * seismically active                   -> ieq_/deq_n100a15
#   * shallow magnetic contrast across a   -> tmi_hg (high-pass TMI) with a weak
#     buried or covered structure             deep expression (tmi_vg)
#   * permeable, clay-poor, fractured rock -> cond_surf
POOL = ["geod_shearrate", "geod_2ndinv", "geod_dilaterate", "rad_ThK", "rad_UK",
        "thermal_hot_prox", "thermal_warm_prox", "ieq_n100a15", "deq_n100a15",
        "tmi_hg", "tmi_vg", "cond_surf"]


def add_h33(obs12, t, ev, ev_idx, shape):
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
    return list(obs12) + [lati.Obs(
        id="h33-2-b2", dti=0.2778, site="GEMSDOE32",
        family="flank-pruned (reported 0.2778, attribution CONFLICTED)",
        sha256=hashlib.sha256(H33.read_bytes()).hexdigest(), S=float(pred[dm].sum()),
        n_dots=int((v > 0).sum()), n_on_catalogue=int((v > 0)[t.catalogue].sum()),
        w=w.ravel()[ev_idx].astype(np.float32), a=a.ravel()[ev_idx].astype(np.float32),
        dot_pos=pos[dflat], dot_flat=dflat, extras={})]


def fit(rows_u8, obs):
    V = np.stack(rows_u8)
    bm = lati.BinnedSoftmax(V, list(range(len(rows_u8))), obs, LEVELS[len(rows_u8)])
    f = bm.fit(l2=L2, bmax=BMAX, k_lo=KLO, k_hi=KHI)
    f["ssr"] = float(np.sum((bm.predict(np.array(f["theta"])) - bm.dti_obs) ** 2))
    loo = 0.0
    for h in range(len(obs)):
        sub = [i for i in range(len(obs)) if i != h]
        g = bm.fit(l2=L2, subset=sub, theta0=np.array(f["theta"]), bmax=BMAX, k_lo=KLO, k_hi=KHI)
        loo += float(bm.predict(np.array(g["theta"]))[h] - obs[h].dti) ** 2
    f["loo"] = loo
    eta = np.zeros(V.shape[1])
    for j in range(len(rows_u8)):
        eta += f["theta"][1 + j] * (V[j].astype(np.float64) / 255.0 - 0.5)
    s = np.exp(eta - eta.max())
    return f, s / s.sum()


def forward_select(layers, obs, backbone, max_steps=4, pool=POOL):
    """Forward selection INSIDE a fold - the pool is a priori, never screened here."""
    chosen = [backbone]
    f0, w0 = fit([layers[backbone]], obs)
    cur = f0["loo"]
    hist = [dict(step=0, layers=list(chosen), K=f0["theta"][0], theta=f0["theta"],
                 ssr=f0["ssr"], loo=cur)]
    for step in range(1, max_steps + 1):
        best = None
        for nm in pool:
            if nm in chosen or nm not in layers:
                continue
            f, _ = fit([layers[c] for c in chosen] + [layers[nm]], obs)
            if best is None or f["loo"] < best["loo"]:
                best = dict(step=step, layers=chosen + [nm], K=f["theta"][0],
                            theta=[float(v) for v in f["theta"]], ssr=f["ssr"], loo=f["loo"])
        if best is None or best["loo"] >= cur - 1e-9:
            break
        chosen = best["layers"]
        cur = best["loo"]
        hist.append(best)
    f, wn = fit([layers[c] for c in chosen], obs)
    return chosen, f, wn, hist


def main() -> int:
    t0 = time.time()
    t = G.load_template()
    ev, shape = t.evaluated, t.shape
    obs12 = lati.load_observations(verbose=False)
    st = FEAT.build_stack(verbose=False)
    U, names, ev_idx = st["U"], list(st["names"]), st["ev_idx"]
    obs = add_h33(obs12, t, ev, ev_idx, shape)
    print(f"[xfit] {len(obs)} observations, a-priori pool of {len(POOL)} geological layers")

    def prox(oid, cap=40.0):
        o = [x for x in obs12 if x.id == oid][0]
        m = np.zeros(shape[0] * shape[1], bool)
        m[o.dot_flat] = True
        return rank_u8_inplace((-FEAT.dist_px(m.reshape(shape), cap).ravel()[ev_idx]).astype(np.float32))

    layers = {"prox_d2.8": prox("d2.8")}
    for nm in POOL:
        layers[nm] = U[names.index(nm)]

    # two observation folds, stratified by reported DTI so each fold spans the range
    order = sorted(range(len(obs)), key=lambda i: obs[i].dti)
    foldA = sorted(order[0::2])
    foldB = sorted(order[1::2])
    print(f"[xfit] fold A ({len(foldA)}): {[obs[i].id for i in foldA]}")
    print(f"[xfit] fold B ({len(foldB)}): {[obs[i].id for i in foldB]}")

    incumbent = np.zeros(shape, bool)
    incumbent.ravel()[[o.dot_flat for o in obs if o.id == "d2.8"][0]] = True
    incumbent &= ev

    out = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "method": "2-fold cross-fitted LATI: a-priori geological pool, forward "
                     "selection inside each fold, candidate scored by the OTHER fold's model",
           "biases_removed": ["optimizer's curse (B1)", "pool-selection bias (B2)"],
           "pool": POOL, "folds": {}, "budget": 37_654}

    verdicts = []
    for tag, tr_idx, te_idx in (("A_train_B_test", foldA, foldB), ("B_train_A_test", foldB, foldA)):
        obs_tr = [obs[i] for i in tr_idx]
        obs_te = [obs[i] for i in te_idx]
        chosen, f_tr, wn_tr, hist = forward_select(layers, obs_tr, "prox_d2.8")
        q_tr = np.zeros(shape[0] * shape[1]); q_tr[ev_idx] = f_tr["theta"][0] * wn_tr
        q_tr = q_tr.reshape(shape)
        print(f"\n[xfit:{tag}] in-fold selected layers={chosen} K={f_tr['theta'][0]:,.0f} "
              f"LOO(in-fold)={f_tr['loo']:.6f}")
        cand = E.emit_greedy(q_tr, ev.copy(), budget=37_654, dti_start=0.0, batch=4000)
        cand_dots = cand.dots & ev
        print(f"[xfit:{tag}] candidate: {int(cand_dots.sum()):,} dots, stopped={cand.stopped_by}")
        # score the candidate under the OTHER fold's independently selected model
        chosen_te, f_te, wn_te, hist_te = forward_select(layers, obs_te, "prox_d2.8")
        q_te = np.zeros(shape[0] * shape[1]); q_te[ev_idx] = f_te["theta"][0] * wn_te
        q_te = q_te.reshape(shape)
        print(f"[xfit:{tag}] out-of-fold model layers={chosen_te} K={f_te['theta'][0]:,.0f}")
        sc_cand = E.predicted_score(q_te, cand_dots)
        sc_inc = E.predicted_score(q_te, incumbent)
        sc_in = E.predicted_score(q_tr, cand_dots)
        delta = sc_cand["DTI"] - sc_inc["DTI"]
        verdicts.append(delta)
        out["folds"][tag] = dict(
            train_ids=[obs[i].id for i in tr_idx], test_ids=[obs[i].id for i in te_idx],
            in_fold=dict(layers=chosen, theta=f_tr["theta"], K=f_tr["theta"][0],
                         ssr=f_tr["ssr"], loo=f_tr["loo"], history=hist),
            out_of_fold=dict(layers=chosen_te, theta=f_te["theta"], K=f_te["theta"][0],
                             ssr=f_te["ssr"], loo=f_te["loo"], history=hist_te),
            candidate=dict(n_dots=int(cand_dots.sum()), stopped_by=cand.stopped_by,
                           in_fold_predicted=sc_in, out_of_fold_predicted=sc_cand),
            incumbent_out_of_fold_predicted=sc_inc,
            paired_delta_out_of_fold=delta,
            in_fold_advantage=sc_in["DTI"] - sc_cand["DTI"])
        print(f"[xfit:{tag}] IN-fold  predicted DTI: candidate {sc_in['DTI']:.4f}")
        print(f"[xfit:{tag}] OUT-fold predicted DTI: candidate {sc_cand['DTI']:.4f}  "
              f"incumbent {sc_inc['DTI']:.4f}  -> paired delta {delta:+.4f}")
        print(f"[xfit:{tag}] in-fold advantage evaporates by {sc_in['DTI']-sc_cand['DTI']:.4f} "
              f"(= the optimizer's-curse + pool-selection premium)")
        np.save(ROOT / ".cache" / f"xfit_cand_{tag}.npy", cand_dots)

    ok = all(d > 0 for d in verdicts)
    out["verdict"] = dict(
        paired_deltas=verdicts, mean_delta=float(np.mean(verdicts)),
        ship=bool(ok),
        rule="ship only if the candidate beats the incumbent on the mean out-of-fold "
             "predicted DTI in BOTH folds",
        statement=("CROSS-FIT VALIDATION PASSED - the candidate beats the incumbent out of fold"
                   if ok else
                   "CROSS-FIT VALIDATION FAILED - the apparent in-fold advantage does not survive "
                   "out-of-fold scoring, so the a-priori geological pool does NOT support a "
                   "candidate that beats the incumbent. Under the project rule ('never spend a "
                   "weekly submission slot on an idea that hasn't beaten the current holdout "
                   "best') the honest deliverable is the incumbent-matched re-emission with the "
                   "smallest out-of-fold deficit, plus the negative result."))
    out["seconds"] = round(time.time() - t0, 1)
    (ROOT / "evidence" / "crossfit_validation.json").write_text(json.dumps(out, indent=1, default=float))
    print(f"\n[verdict] deltas={[round(d,5) for d in verdicts]}  SHIP={ok}")
    print(out["verdict"]["statement"])
    print(f"wrote evidence/crossfit_validation.json ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
