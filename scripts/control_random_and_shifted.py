#!/usr/bin/env python3
"""The control that decides whether the shipped candidate is a signal or an artefact.

Why this script exists
----------------------
`main` carries the record of two prior sessions on this same brief. Both built a detector, both
preregistered a gate, and **both closed it**:

* H47-B (cross-scale `TMI_up150` magnetic-edge persistence) scored pooled DTI **0.02755** on the
  locked test against a fixed-seed **random control of 0.03716** -- the candidate lost to random
  noise.  Its assumption-conditional split-conformal lower-bound estimate was **0.0**.
* H47-GSA (geodetic strain x hydrothermal alteration x thermal discharge) showed an in-fold
  advantage of **+0.30** that cross-fitting exposed as *optimizer's curse*: paired out-of-fold
  deltas were **-0.0611** and **-0.0450** against the owner-reported d2.8 reference; the comparison
  is conditional on the unverified H33-2-B2 / participant 0.2778 association and is not a spatial holdout.

The session that produced `docs/downloads/gemsdoe47-scarp9-persistence-s2.8-d7.37-b2.tif` swept
180 operating points and 5 recipes on a catalogue-derived holdout and reported the new field
beating an owner-reported H33-2-B2 raster on a local proxy by 15–24×; its participant-score mapping is unverified -- **but never ran a random or shuffled control at
matched mass on those folds.**  That is precisely the missing control.  This script supplies it.

Controls, all at MATCHED mass, MATCHED spacing and MATCHED flank buffer on IDENTICAL folds
    A  shipped      the dots actually in the historical research raster
    B  random       a uniform random field put through the identical emitter (20 seeds)
    C  shifted      the shipped dot pattern translated by a large offset: preserves the field's
                    density and clustering, destroys its alignment with the geology
    D  rankflip     the shipped field's support inverted: dots placed where the field is LOWEST

If A does not beat B and C by a margin far outside their spread, the candidate is not a signal and
must be marked RESEARCH ONLY, exactly as `main` marked its own two artifacts.

Needs only labels.tif and sample_submission.tif plus the historical research raster -- the 419 MB feature
stack is not required, because the controls replace the field rather than rebuild it.

Run:  python3 scripts/control_random_and_shifted.py
Out:  evidence/control/controls.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems47s3 import emission as E
from gems47s3 import metric as M
from gems47s3.spec import HEIGHT, WIDTH

DATA = ROOT / "data"
EV = ROOT / "evidence" / "control"
STRUCT8 = np.ones((3, 3), bool)
BLOCKS = 6
SEED = 20261006                     # the sweep's seed, so the folds are IDENTICAL
PM = {"PM0112": 0.00112, "PM0200": 0.00200, "PM0294": 0.00294}
# A1 = the 300 catalogue components that are ALONE in their own 300 m dilation.  On these folds
# the truth is by construction more than 3 px from the rest of the catalogue, so a full-catalogue
# flank prune does not delete dots near the truth and the comparison is fair without any further
# adjustment.  It is the cleanest frame available and is reported separately.
FRAMES = list(PM) + ["A1"]
N_RANDOM_SEEDS = 20
SPACING = 2.8
FLANK_B = 2.0


def dti_of(pred: np.ndarray, truth: np.ndarray, k_near: np.ndarray, n_truth: int) -> dict:
    s = float(pred.sum())
    if n_truth == 0 or s == 0.0:
        return dict(dti=0.0, tp=0.0, S=s, coverage=0.0)
    tp = float(M.kernel(ndi.distance_transform_edt(~pred))[truth].sum())
    m = float(k_near[pred].sum())
    fn = float(n_truth) - tp
    denom = tp + M.ALPHA * (s - m) + M.BETA * fn + M.EPS_METRIC
    return dict(dti=float(tp / denom), tp=tp, S=s, coverage=float(tp / n_truth))


def main() -> int:
    t0 = time.time()
    EV.mkdir(parents=True, exist_ok=True)
    with rasterio.open(DATA / "labels.tif") as ds:
        cat = ds.read(1) == 1
    with rasterio.open(DATA / "sample_submission.tif") as ds:
        fp = np.isfinite(ds.read(1))
    shipped_path = sorted((ROOT / "docs" / "downloads").glob("*.tif"))
    if not shipped_path:
        raise SystemExit("no shipped raster in docs/downloads/")
    with rasterio.open(shipped_path[0]) as ds:
        shipped = np.nan_to_num(ds.read(1).astype(np.float32)) > 0
    print(f"[load] shipped {shipped_path[0].name}: {int(shipped.sum())} positive px")
    assert shipped.sum() > 0

    dcat = ndi.distance_transform_edt(~cat).astype(np.float32)

    # ---- spatial blocks, identical construction to scripts/run_sweep_a.py
    fid = np.zeros((HEIGHT, WIDTH), np.int16)
    rh, cw = HEIGHT // BLOCKS, WIDTH // BLOCKS
    k = 0
    for r in range(BLOCKS):
        for c in range(BLOCKS):
            y0, y1 = r * rh, (HEIGHT if r == BLOCKS - 1 else (r + 1) * rh)
            x0, x1 = c * cw, (WIDTH if c == BLOCKS - 1 else (c + 1) * cw)
            fid[y0:y1, x0:x1] = k
            k += 1
    comp_lab, n_comp = ndi.label(cat, structure=STRUCT8)
    sizes = np.bincount(comp_lab.ravel(), minlength=n_comp + 1)
    objs = ndi.find_objects(comp_lab)
    comp_block = np.full(n_comp + 1, -1, np.int32)
    for c in range(1, n_comp + 1):
        sl = objs[c - 1]
        sel = comp_lab[sl] == c
        vals, counts = np.unique(fid[sl][sel], return_counts=True)
        comp_block[c] = int(vals[np.argmax(counts)])
    print(f"[folds] {n_comp} components over {BLOCKS}x{BLOCKS} blocks  ({time.time()-t0:.0f}s)")

    # isolated components (A1): alone in their own 300 m dilation
    dil = ndi.binary_dilation(cat, iterations=3, structure=STRUCT8)
    dil_lab, n_dil = ndi.label(dil, structure=STRUCT8)
    ys_c, xs_c = np.nonzero(cat)
    dl, cl = dil_lab[ys_c, xs_c], comp_lab[ys_c, xs_c]
    order = np.argsort(dl, kind="stable")
    dl_s, cl_s = dl[order], cl[order]
    bounds = np.searchsorted(dl_s, np.arange(n_dil + 2))
    flanking_comp = np.zeros(n_comp + 1, bool)
    for bb in range(1, n_dil + 1):
        seg = cl_s[bounds[bb]:bounds[bb + 1]]
        if seg.size:
            u = np.unique(seg)
            if u.size > 1:
                flanking_comp[u] = True
    isolated_comp = ~flanking_comp
    isolated_comp[0] = False
    print(f"[A1] isolated components {int(isolated_comp[1:].sum())} of {n_comp}")

    rng = np.random.default_rng(SEED)
    results = {}
    for pname in FRAMES:
        prev = PM.get(pname)
        rows = []
        for b in range(BLOCKS * BLOCKS):
            region = (fid == b) & fp
            if region.sum() < 5000:
                continue
            in_block = np.nonzero(comp_block == b)[0]
            if pname == "A1":
                in_block = in_block[isolated_comp[in_block]]
            if in_block.size == 0:
                continue
            if pname == "A1":
                keep = np.zeros(n_comp + 1, bool)
                keep[in_block] = True
            else:
                target = round(prev * float(region.sum()))
                keep, acc = np.zeros(n_comp + 1, bool), 0
                for j in rng.permutation(in_block.size):
                    if acc >= target:
                        break
                    c = in_block[j]
                    keep[c] = True
                    acc += int(sizes[c])
            truth = keep[comp_lab] & region
            if truth.sum() < 50:
                continue
            visible = cat & ~truth
            scored = region & ~visible
            # FAIRNESS: every arm must be restricted to the SAME emittable domain as the shipped
            # raster.  The shipped raster was pruned against the FULL catalogue (dcat > 2), so if
            # the controls are only pruned against the VISIBLE catalogue they may place dots
            # within 2 px of the fold truth while the historical research raster structurally may not -- an
            # asymmetry that makes the candidate look like noise whatever it is.  The first run of
            # this script had exactly that bug and reported A/B = 0.28-0.31; it is fixed here by
            # pruning all arms against the full catalogue, and by reporting the A1 frame where the
            # truth is isolated from the catalogue by construction.
            emask = scored & (dcat > FLANK_B)
            ys, xs = np.nonzero(region)
            crop = (int(ys.min()), int(ys.max()) + 1, int(xs.min()), int(xs.max()) + 1)
            y0, y1, x0, x1 = crop
            t_c = truth[y0:y1, x0:x1]
            em_c = emask[y0:y1, x0:x1]
            sh_c = shipped[y0:y1, x0:x1] & em_c
            n_truth = int(t_c.sum())
            k_near = M.kernel(ndi.distance_transform_edt(~t_c))
            n_shipped = int(sh_c.sum())
            if n_shipped == 0:
                continue

            entry = dict(block=int(b), n_truth=n_truth, n_scored=int(scored.sum()),
                         n_emittable=int(em_c.sum()), n_shipped=n_shipped)

            # A: the shipped dots
            entry["A_shipped"] = dti_of(sh_c, t_c, k_near, n_truth)

            # B: random field through the IDENTICAL emitter, matched mass, 20 seeds
            b_runs = []
            for s in range(N_RANDOM_SEEDS):
                r = np.random.default_rng(1000 + s)
                rf = r.random(em_c.shape).astype(np.float32)
                em = E.emit(rf, em_c, min_dist=SPACING, support_q=1.0, blur="none",
                            budget=n_shipped)
                b_runs.append(dti_of(em["mask"], t_c, k_near, n_truth)["dti"])
            entry["B_random"] = dict(dti=float(np.mean(b_runs)), dtis=[round(x, 6) for x in b_runs],
                                     sd=float(np.std(b_runs)), min=float(np.min(b_runs)),
                                     max=float(np.max(b_runs)), n_seeds=N_RANDOM_SEEDS)

            # C: the shipped pattern translated so it keeps density+clustering but loses alignment
            shifts = [(0, 60), (60, 0), (0, -60), (-60, 0), (45, 45), (-45, 45)]
            c_runs = []
            for dy, dx in shifts:
                mv = ndi.shift(shipped.astype(np.float32), (dy, dx), order=0, mode="constant",
                               cval=0.0) > 0.5
                mv = mv[y0:y1, x0:x1] & em_c
                if mv.sum() == 0:
                    continue
                # re-match the mass exactly by keeping a random subset / topping up from emask
                if mv.sum() > n_shipped:
                    idx = np.nonzero(mv.ravel())[0]
                    pick = np.random.default_rng(7).choice(idx, n_shipped, replace=False)
                    mv = np.zeros(mv.size, bool); mv[pick] = True
                    mv = mv.reshape(em_c.shape)
                c_runs.append(dti_of(mv, t_c, k_near, n_truth)["dti"])
            entry["C_shifted"] = dict(dti=float(np.mean(c_runs)) if c_runs else None,
                                      dtis=[round(x, 6) for x in c_runs], n_shifts=len(c_runs))

            # D: dots where the shipped field is ABSENT but still inside the emittable domain,
            #    chosen as the lowest-rank complement -- approximated by a random subset of the
            #    emittable domain that excludes the shipped dots (a "wrong-place, right-mass" arm)
            wrong = em_c & ~sh_c
            if wrong.sum() >= n_shipped:
                idx = np.nonzero(wrong.ravel())[0]
                pick = np.random.default_rng(31).choice(idx, n_shipped, replace=False)
                w = np.zeros(wrong.size, bool); w[pick] = True
                entry["D_wrongplace"] = dti_of(w.reshape(em_c.shape), t_c, k_near, n_truth)
            rows.append(entry)
        results[pname] = rows
        if rows:
            a = np.array([r["A_shipped"]["dti"] for r in rows])
            b = np.array([r["B_random"]["dti"] for r in rows])
            c = np.array([r["C_shifted"]["dti"] for r in rows if r["C_shifted"]["dti"] is not None])
            d = np.array([r["D_wrongplace"]["dti"] for r in rows if "D_wrongplace" in r])
            bsd = np.array([r["B_random"]["sd"] for r in rows])
            wins = int((a > b).sum())
            print(f"\n[{pname}] {len(rows)} usable blocks, "
              + (f"prevalence target {prev:.5f}" if prev else "ALL isolated components"))
            print(f"   A shipped   mean DTI {a.mean():.5f}  (blocks {len(a)})")
            print(f"   B random    mean DTI {b.mean():.5f}  sd {bsd.mean():.5f}  "
                  f"[{b.min():.5f}, {b.max():.5f}]")
            print(f"   C shifted   mean DTI {c.mean():.5f}" if c.size else "   C shifted   n/a")
            print(f"   D wrongplace mean DTI {d.mean():.5f}" if d.size else "   D wrongplace n/a")
            print(f"   A beats B on {wins}/{len(a)} blocks;  A-B = {a.mean()-b.mean():+.5f} "
                  f"({(a.mean()/b.mean() if b.mean() else float('nan')):.2f}x)")
            if c.size:
                print(f"   A-C = {a.mean()-c.mean():+.5f}")

    out = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        seconds=round(time.time() - t0, 1),
        purpose=("random / shifted / wrong-place controls at matched mass, spacing and flank "
                 "buffer on folds identical to scripts/run_sweep_a.py (seed 20261006, 6x6 blocks, "
                 "MIN_TRUTH_PX=50). This is the control whose absence closed the gates on both "
                 "prior candidates recorded on main."),
        shipped_raster=str(shipped_path[0]),
        shipped_positive_px=int(shipped.sum()),
        spacing_px=SPACING, flank_buffer_px=FLANK_B, n_random_seeds=N_RANDOM_SEEDS,
        controls=("A shipped dots; B uniform random field through the identical emitter, 20 seeds; "
                  "C shipped pattern translated by 45-60 px in six directions (keeps density and "
                  "clustering, destroys alignment); D same mass placed on emittable pixels the "
                  "shipped field rejected"),
        results=results,
    )
    summary = {}
    for pname, rows in results.items():
        if not rows:
            continue
        a = np.array([r["A_shipped"]["dti"] for r in rows])
        b = np.array([r["B_random"]["dti"] for r in rows])
        c = np.array([r["C_shifted"]["dti"] for r in rows if r["C_shifted"]["dti"] is not None])
        d = np.array([r["D_wrongplace"]["dti"] for r in rows if "D_wrongplace" in r])
        summary[pname] = dict(
            n_blocks=len(rows),
            A_shipped_mean=round(float(a.mean()), 6),
            B_random_mean=round(float(b.mean()), 6),
            B_random_sd=round(float(np.mean([r["B_random"]["sd"] for r in rows])), 6),
            C_shifted_mean=round(float(c.mean()), 6) if c.size else None,
            D_wrongplace_mean=round(float(d.mean()), 6) if d.size else None,
            A_minus_B=round(float(a.mean() - b.mean()), 6),
            A_over_B=round(float(a.mean() / b.mean()), 4) if b.mean() else None,
            A_minus_C=round(float(a.mean() - c.mean()), 6) if c.size else None,
            blocks_where_A_beats_B=int((a > b).sum()),
            paired_t_like=round(float((a - b).mean() / max((a - b).std(ddof=1) / np.sqrt(a.size),
                                                            1e-12)), 3),
        )
    out["summary"] = summary
    verdict = all(v["A_minus_B"] > 0 and (v["A_minus_C"] or 0) > 0 for v in summary.values())
    out["verdict"] = dict(
        candidate_beats_random_on_every_prevalence=verdict,
        rule=("promote only if A beats B and C on every prevalence frame by a margin outside the "
              "random control's own spread; otherwise mark RESEARCH ONLY, as main did for H47-B "
              "and H47-GSA"),
    )
    (EV / "controls.json").write_text(json.dumps(out, indent=1))
    print(f"\n[verdict] beats random and shifted on every frame: {verdict}")
    print(f"wrote {EV/'controls.json'}   ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
