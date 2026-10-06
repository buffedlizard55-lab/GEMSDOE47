#!/usr/bin/env python3
"""Compute and cache every H47 detector surface from the official 19-band feature stack.

All surfaces except H47-A are label-free, so they are computed ONCE for the whole grid and
cached; H47-A depends on which catalogue pixels are visible, and is recomputed per holdout
fold by scripts/run_sweep.py from the cached physics density.

Run:  python3 scripts/build_surfaces.py [--quick]
Out:  data/surfaces/*.npy  +  evidence/surfaces_receipt.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems47s3 import field as F            # noqa: E402
from gems47s3.grid import Grid, robust_unit  # noqa: E402

OUT = ROOT / "data" / "surfaces"
EV = ROOT / "evidence"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="single smoothing scale, for smoke tests")
    args = ap.parse_args()
    scales = (2.0,) if args.quick else (1.0, 2.0, 3.0)

    OUT.mkdir(parents=True, exist_ok=True)
    EV.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    g = Grid()
    print(f"[grid] footprint {int(g.footprint.sum())}  catalogue {int(g.catalogue.sum())}  "
          f"({time.time()-t0:.1f}s)")

    valid = g.all_bands_finite()
    np.save(OUT / "valid.npy", valid)
    print(f"[grid] all-19-bands-finite {int(valid.sum())} px  ({time.time()-t0:.1f}s)")

    # ---- multi-family corroboration (the expensive step: 17 bands x len(scales) Hessians)
    corr = F.corroboration(g, valid, sigmas=scales)
    for name, arr in corr["families"].items():
        np.save(OUT / f"fam_{name}.npy", arr)
    for key in ("count", "mean", "max"):
        np.save(OUT / f"corr_{key}.npy", corr[key].astype(np.float32))
    print(f"[H47] corroboration done: {list(corr['families'])}  ({time.time()-t0:.1f}s)")

    # ---- structure tensor for the oriented blur (on the topography + magnetics composite)
    comp = np.maximum(corr["families"]["topo"], corr["families"]["mag"])
    theta, coh = F.structure_tensor(comp, valid, 2.0)
    np.save(OUT / "theta.npy", theta)
    np.save(OUT / "coherence.npy", coh)
    print(f"[H47] structure tensor done  ({time.time()-t0:.1f}s)")

    # ---- the five hypothesis surfaces
    a = F.h47a_vacancy_residual(g, valid, corr)
    np.save(OUT / "A_physics_density.npy", a["physics_density"].astype(np.float32))
    np.save(OUT / "A_catalogue_density.npy", a["catalogue_density"].astype(np.float32))
    b = F.h47b_braid_number(g, valid, corr)
    np.save(OUT / "B_braid.npy", b["braid"])
    np.save(OUT / "B_braid_count.npy", b["count"])
    print(f"[H47] A (vacancy inputs) + B (braid) done  ({time.time()-t0:.1f}s)")

    c = F.h47c_drainage_asymmetry(g, valid)
    np.save(OUT / "C_drain_asym.npy", c["azimuth_asymmetry"])
    np.save(OUT / "C_drain_mag.npy", c["magnitude_asymmetry"])
    print(f"[H47] C (drainage asymmetry) done  ({time.time()-t0:.1f}s)")

    d = F.h47d_strain_partitioning(g, valid)
    np.save(OUT / "D_strain.npy", np.nan_to_num(d["score"], nan=0.0).astype(np.float32))
    np.save(OUT / "D_ratio.npy", d["ratio"].astype(np.float32))
    print(f"[H47] D (strain partitioning) done  ({time.time()-t0:.1f}s)")

    e = F.h47e_signed_basement_step(g, valid, corr)
    np.save(OUT / "E_basement.npy", np.nan_to_num(e["step_score"], nan=0.0).astype(np.float32))
    np.save(OUT / "E_persistence.npy", e["persistence"])
    np.save(OUT / "E_signflip.npy", np.nan_to_num(e["sign_flip"], nan=0.0).astype(np.float32))
    print(f"[H47] E (signed basement step) done  ({time.time()-t0:.1f}s)")

    np.save(OUT / "d_catalogue.npy", g.d_catalogue)
    np.save(OUT / "catalogue.npy", g.catalogue)
    np.save(OUT / "footprint.npy", g.footprint)
    np.save(OUT / "scored.npy", g.scored)

    # ---- receipt: what each surface actually contains (a hallucination check a reviewer can run)
    receipt = dict(generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   scales=list(scales), seconds=round(time.time() - t0, 1),
                   valid_all_bands_finite=int(valid.sum()), surfaces={})
    for p in sorted(OUT.glob("*.npy")):
        arr = np.load(p, mmap_mode="r")
        a2 = np.asarray(arr)
        fin = np.isfinite(a2)
        receipt["surfaces"][p.name] = dict(
            dtype=str(a2.dtype), shape=list(a2.shape),
            finite=int(fin.sum()),
            min=float(np.nanmin(a2[fin])) if fin.any() else None,
            p50=float(np.median(a2[fin])) if fin.any() else None,
            max=float(np.nanmax(a2[fin])) if fin.any() else None,
            positive=int((fin & (a2 > 0)).sum()),
        )
    (EV / "surfaces_receipt.json").write_text(json.dumps(receipt, indent=2))
    print(f"\nwrote {len(receipt['surfaces'])} cached arrays to {OUT}")
    print(f"receipt -> {EV/'surfaces_receipt.json'}   total {time.time()-t0:.1f}s")
    for k, v in receipt["surfaces"].items():
        print(f"  {k:28s} {v['dtype']:8s} min={v['min'] if v['min'] is None else round(v['min'],4)} "
              f"max={v['max'] if v['max'] is None else round(v['max'],4)} pos={v['positive']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
