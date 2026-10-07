#!/usr/bin/env python3
"""Compact evidence tables for the H49 sweep: the response surface and the arm ranking.

Reads ``evidence/sweep/sweep_h49.json`` (never re-runs anything) and prints / writes:

  * the density x spacing response of the primary instrument for every recipe x emitter pair on both
    halves, so a reviewer can see whether the chosen point is interior or a boundary artefact;
  * the mass-matched control comparison (isotropic ``nms_disk`` vs strike-aligned ``nms_oriented``
    at the identical operating point and identical emitted mass);
  * the per-instrument pooled DTI on public proxy blocks. This is not a stand-in for the
    leaderboard's hidden-label score or scoring population.

Run:  python3 scripts/analyze_h49.py [--md docs/H49_EVIDENCE.md]
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTRUMENTS = ("PM0200", "PM0112", "PM0294", "A1", "A2")
CONTROLS = ("RANDOM_fixed_seed", "REF_incumbent_0.2778")


def load(path: Path):
    sweep = json.loads(Path(path).read_text())
    rows = sweep["rows"]
    mean = defaultdict(lambda: defaultdict(list))
    pooled = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    emitted = defaultdict(list)
    for r in rows:
        k = (r["recipe"], r["emitter"], r["op"])
        mean[(k, r["instrument"], r["half"])].append(r["dti"])
        for f in ("tp", "S", "M", "n_truth"):
            pooled[(k, r["instrument"], r["half"])][f] += float(r.get(f) or 0.0)
        emitted[(k, r["instrument"])].append(r["emitted"])
    return sweep, mean, pooled, emitted


def pooled_dti(acc: dict) -> float:
    denom = 0.2 * (acc["tp"] + acc["S"] - acc["M"]) + 0.8 * acc["n_truth"]
    return acc["tp"] / denom if denom > 0 else 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", default=str(ROOT / "evidence" / "sweep" / "sweep_h49.json"))
    ap.add_argument("--selection", default=str(ROOT / "evidence" / "h49" / "conformal_selection.json"))
    ap.add_argument("--md", default="")
    args = ap.parse_args()
    sweep, mean, pooled, emitted = load(Path(args.sweep))
    sel = json.loads(Path(args.selection).read_text()) if Path(args.selection).exists() else None
    lines: list[str] = []

    def out(s: str = "") -> None:
        print(s)
        lines.append(s)

    out(f"# H49 sweep evidence ({sweep['n_blocks']} spatial blocks, "
        f"{len(sweep['spacings'])} spacings x {len(sweep['densities_per_1000'])} densities x "
        f"{len(sweep.get('flank_buffers_px', [2.0]))} flank buffers)")
    out()
    out(f"- blocks per side: {sweep['blocks_per_side']}; calibration blocks: "
        f"{len(sweep['calibration_block_indices'])}; selection blocks: "
        f"{len(sweep['selection_block_indices'])}")
    out(f"- instruments: {', '.join(sweep['instruments'])}")
    out(f"- rows: {len(sweep['rows'])}; generated {sweep['generated_utc']}")
    if sel:
        c = sel["chosen"]
        out(f"- historical v1 choice (superseded for interpretation): **{c['recipe']} / {c['emitter']} / {c['op']}**; "
            f"nominal lower-bound estimate {sel['guarantee']['certified_floor_primary_instrument']:.5f} at "
            f"{sel['confidence_pct']:.0f} % on public proxy {sel['primary_instrument']}; "
            "conditional on unverified exchangeability, not a private/global performance floor")
    out()

    keys = sorted({(r["recipe"], r["emitter"], r["op"]) for r in sweep["rows"]})
    for inst in INSTRUMENTS:
        out(f"## {inst}")
        out()
        out("| recipe | emitter | op | n_sel | sel mean | cal mean | sel pooled | cal pooled | emitted px |")
        out("|---|---|---|---:|---:|---:|---:|---:|---:|")
        for k in keys:
            sel_v = mean.get((k, inst, "selection"), [])
            cal_v = mean.get((k, inst, "calibration"), [])
            if not sel_v and not cal_v:
                continue
            sp = pooled_dti(pooled[(k, inst, "selection")]) if sel_v else float("nan")
            cp = pooled_dti(pooled[(k, inst, "calibration")]) if cal_v else float("nan")
            em = emitted.get((k, inst), [0])
            recipe_label = k[0].replace("REF_incumbent_0.2778", "REF_owner_reported_d2.8")
            out(f"| {recipe_label} | {k[1]} | {k[2]} | {len(sel_v)} | "
                f"{sum(sel_v)/len(sel_v):.4f} | {sum(cal_v)/len(cal_v):.4f} | {sp:.4f} | {cp:.4f} | "
                f"{sum(em)/len(em):.0f} |")
        out()

    # the response curve: primary instrument, chosen recipe, both emitters, per half
    if sel:
        rec = sel["chosen"]["recipe"]
        for inst in (sel["primary_instrument"],):
            out(f"## Response surface — {inst}, recipe `{rec}` (mean block DTI)")
            out()
            for half in ("selection", "calibration"):
                out(f"### {half} half")
                out()
                ops = sorted({r["op"] for r in sweep["rows"] if r["recipe"] == rec})
                emit_names = sorted({r["emitter"] for r in sweep["rows"] if r["recipe"] == rec})
                out("| op | " + " | ".join(emit_names) + " |")
                out("|---|" + "---:|" * len(emit_names))
                for op in ops:
                    cells = []
                    for em in emit_names:
                        v = mean.get(((rec, em, op), inst, half), [])
                        cells.append(f"{sum(v)/len(v):.4f}" if v else "—")
                    out(f"| {op} | " + " | ".join(cells) + " |")
                out()

    if args.md:
        Path(args.md).write_text("\n".join(lines) + "\n")
        print(f"wrote {args.md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
