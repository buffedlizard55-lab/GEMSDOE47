#!/usr/bin/env python3
"""Historical H49 v1 public-catalogue proxy analysis, retained but disabled.

This earlier script predates the Instrument-B addendum and the later mean-rule amendment. Its
original output can be useful for reproducing the earlier exploratory analysis, but it is not the
final H49 report, does not establish block exchangeability, and cannot authorize a submission slot.
The active CLI exits before reading evidence or overwriting the historical selection receipt.

Historical implementation follows (not approved for rerun):
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems47s3.conformal import (
    conformal_order_statistic,
    conformal_quantile,
    dkw_epsilon,
    dkw_mean_lower_bound,
    min_blocks_for_alpha,
)

PRIMARY = "PM0200"
INSTRUMENTS = ("PM0200", "PM0112", "PM0294", "A1", "A2")
ALPHA = 0.10
ALPHA_GRID = (0.05, 0.10, 0.20, 0.25, 0.30)
MIN_BLOCKS_PER_HALF = 12          # a 90 % floor needs n >= 9; 12 keeps a margin for the audit
#: control arms: measured and reported, never eligible for selection (the random arm has no
#: geological content, the incumbent is an external artifact this repo cannot re-derive)
CONTROL_RECIPES = ("RANDOM_fixed_seed", "REF_incumbent_0.2778")
N_REPEATED_SPLITS = 400
SEED = 20261007


def load_arms(path: Path) -> tuple[dict, dict]:
    sweep = json.loads(Path(path).read_text())
    arms: dict[tuple, dict] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    pooled: dict[tuple, dict] = defaultdict(lambda: defaultdict(lambda: defaultdict(
        lambda: dict(tp=0.0, S=0.0, M=0.0, n_truth=0.0, emitted=0.0, blocks=0.0))))
    for row in sweep["rows"]:
        key = (row["recipe"], row["emitter"], row["op"])
        arms[key][row["instrument"]][row["half"]].append((row["block_index"], row["dti"]))
        acc = pooled[key][row["instrument"]][row["half"]]
        for f in ("tp", "S", "M", "n_truth", "emitted"):
            acc[f] += float(row.get(f) or 0.0)
        acc["blocks"] += 1.0
    # sort each (arm, instrument, half) list by block index so that index i is the same physical
    # block in every arm -- required for the repeated-split audit
    out = {}
    for key, per_inst in arms.items():
        out[key] = {}
        for inst, halves in per_inst.items():
            out[key][inst] = {h: sorted(v) for h, v in halves.items()}
    for per_inst in pooled.values():
        for halves in per_inst.values():
            for acc in halves.values():
                denom = 0.2 * (acc["tp"] + acc["S"] - acc["M"]) + 0.8 * acc["n_truth"]
                acc["dti_pooled"] = (acc["tp"] / denom) if denom > 0 else 0.0
    return sweep, out, pooled


def usable(arms: dict) -> dict:
    keep = {}
    for key, per_inst in arms.items():
        ok = True
        for inst in INSTRUMENTS:
            halves = per_inst.get(inst, {})
            if (len(halves.get("selection", [])) < MIN_BLOCKS_PER_HALF
                    or len(halves.get("calibration", [])) < MIN_BLOCKS_PER_HALF):
                ok = False
                break
        if ok:
            keep[key] = per_inst
    return keep


def arm_stats(per_inst: dict, half: str, alphas=ALPHA_GRID) -> dict:
    means, floors = {}, {}
    for inst in INSTRUMENTS:
        vals = np.array([v for _, v in per_inst[inst][half]], float)
        means[inst] = float(vals.mean())
        floors[inst] = {a: float(conformal_quantile(vals, a, side="lower")) for a in alphas}
    return dict(means=means, floors=floors)


def choose(arms: dict, half_for_choice: str, alpha: float) -> tuple[tuple, dict]:
    """The preregistered rule, verbatim from docs/research/h49-hypotheses-preregistered.md:

    "maximise the primary-instrument (PM0200) mean selection-half DTI, tie-broken by the worst
    normalised mean across the five instruments, then by larger minimum spacing."

    No positivity screen, no post-hoc exclusion: the frozen key is used as written.  The only
    additions are total-order tie-breaks after the three frozen ones (flank buffer then recipe name
    then emitter), which can only decide exact ties the frozen rule leaves open.
    """
    cands = {k: v for k, v in arms.items() if k[0] not in CONTROL_RECIPES}
    stats = {k: arm_stats(v, half_for_choice) for k, v in cands.items()}
    best_of = {i: max(s["means"][i] for s in stats.values()) for i in INSTRUMENTS}
    screened = stats

    def key(k):
        s = screened[k]
        worst_norm = min(s["means"][i] / max(best_of[i], 1e-12) for i in INSTRUMENTS)
        recipe, emitter, op = k
        fields = op_params(op)
        return (-s["means"][PRIMARY], -worst_norm, -fields.get("min_dist", 0.0),
                -fields.get("flank_b", 0.0), recipe, emitter)

    chosen = min(screened, key=key)
    return chosen, dict(stats=stats, screened=screened, best_of=best_of,
                        n_screened=len(screened), n_arms=len(cands))


def op_params(op: str) -> dict:
    """Parse an operating-point label.  A missing ``b`` token means the pre-flank-axis 2 px
    default, so this script also runs on the quick sweep written during bring-up."""
    out = {"min_dist": 2.8, "density_per_1000": 7.37, "flank_b": 2.0}
    for tok in op.split("_"):
        if tok[0] not in "sdb" or not tok[1:].replace(".", "", 1).replace("e", "", 1).replace(
                "+", "", 1).replace("-", "", 1).isdigit():
            continue                      # e.g. the incumbent's "as-shipped" label
        out[{"s": "min_dist", "d": "density_per_1000", "b": "flank_b"}[tok[0]]] = float(tok[1:])
    return out


def gate_report(arms: dict, pooled: dict, chosen: tuple, sel: dict, cal: dict,
                alpha: float) -> dict:
    """The preregistered submission gate, evaluated on the frozen numbers.

    "A candidate that does not beat the isotropic control on the primary instrument's selection
    half does not get submitted."  The isotropic control is the SAME recipe at the SAME operating
    point emitted with ``nms_disk`` instead of the strike-aligned rule, so the comparison isolates
    the emitter.  Positive certified floor and the frozen-incumbent comparison are reported
    alongside; they are necessary but not sufficient conditions.
    """
    iso = (chosen[0], "disk", chosen[2])
    out = dict(
        isotropic_control_arm="/".join(iso),
        control_present=iso in arms,
        beats_isotropic_control=None, beats_incumbent_mean=None, beats_incumbent_pooled=None,
        beats_random_mean=None, positive_certified_floor=None, all_gates_pass=None,
    )
    p = "PM0200"
    if iso in arms and iso != chosen:
        c = sel["means"][p]
        k = arm_stats(arms[iso], "selection")["means"][p]
        out.update(beats_isotropic_control=bool(c > k),
                   chosen_selection_mean_primary=round(c, 6),
                   isotropic_selection_mean_primary=round(k, 6),
                   relative_gain_pct=round(100.0 * (c - k) / k, 3) if k else None)
    elif iso == chosen:
        out.update(beats_isotropic_control=False,
                   note="chosen arm IS the isotropic control; H49-A did not win")
    inc = next((k for k in arms if k[0] == "REF_incumbent_0.2778"), None)
    rnd = next((k for k in arms if k[0] == "RANDOM_fixed_seed" and k[2] == chosen[2]), None)
    if inc is not None:
        out["beats_incumbent_mean"] = bool(
            sel["means"][p] > arm_stats(arms[inc], "selection")["means"][p])
        out["incumbent_selection_mean_primary"] = round(
            arm_stats(arms[inc], "selection")["means"][p], 6)
        out["beats_incumbent_pooled"] = bool(
            pooled[chosen][p]["selection"]["dti_pooled"]
            > pooled[inc][p]["selection"]["dti_pooled"])
        out["incumbent_pooled_dti_selection_primary"] = round(
            pooled[inc][p]["selection"]["dti_pooled"], 6)
    if rnd is not None:
        out["beats_random_mean"] = bool(
            sel["means"][p] > arm_stats(arms[rnd], "selection")["means"][p])
        out["random_selection_mean_primary"] = round(
            arm_stats(arms[rnd], "selection")["means"][p], 6)
    out["positive_certified_floor"] = bool(cal["floors"][p][alpha] > 0.0)
    out["chosen_pooled_dti_selection_primary"] = round(
        pooled[chosen][p]["selection"]["dti_pooled"], 6)
    checks = [out["beats_isotropic_control"], out["positive_certified_floor"]]
    if out["beats_incumbent_mean"] is not None:
        checks.append(out["beats_incumbent_mean"])
    if out["beats_random_mean"] is not None:
        checks.append(out["beats_random_mean"])
    out["all_gates_pass"] = bool(all(bool(c) for c in checks))
    out["checks_evaluated"] = len(checks)
    return out


def _legacy_main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", default=str(ROOT / "evidence" / "sweep" / "sweep_h49.json"))
    ap.add_argument("--out", default=str(ROOT / "evidence" / "h49" / "conformal_selection.json"))
    ap.add_argument("--alpha", type=float, default=ALPHA)
    args = ap.parse_args()
    t0 = time.time()

    sweep, arms, pooled = load_arms(Path(args.sweep))
    us = usable(arms)
    print(f"[arms] {len(arms)} total, {len(us)} usable "
          f"(>= {MIN_BLOCKS_PER_HALF} blocks per half on all instruments) "
          f"({time.time() - t0:.1f}s)")
    chosen, diag = choose(us, "selection", args.alpha)
    print(f"[choose] {chosen}")

    per_inst = us[chosen]
    sel = arm_stats(per_inst, "selection")
    cal = arm_stats(per_inst, "calibration")
    cal_arrays = {i: np.array([v for _, v in per_inst[i]["calibration"]], float)
                  for i in INSTRUMENTS}
    sel_arrays = {i: np.array([v for _, v in per_inst[i]["selection"]], float)
                  for i in INSTRUMENTS}

    floors = {i: float(conformal_quantile(cal_arrays[i], args.alpha, side="lower"))
              for i in INSTRUMENTS}
    n_cal = {i: int(cal_arrays[i].size) for i in INSTRUMENTS}
    k_used = {i: conformal_order_statistic(n_cal[i], args.alpha) for i in INSTRUMENTS}
    primary_floor = floors[PRIMARY]

    alpha_sensitivity = {}
    for a in ALPHA_GRID:
        alpha_sensitivity[f"alpha={a:.2f}"] = dict(
            confidence_pct=round(100.0 * (1.0 - a), 3),
            order_statistic_k=conformal_order_statistic(n_cal[PRIMARY], a),
            n_calibration_blocks=n_cal[PRIMARY],
            certified_floor_primary_instrument=float(
                conformal_quantile(cal_arrays[PRIMARY], a, side="lower")),
            vacuous=not math.isfinite(conformal_quantile(cal_arrays[PRIMARY], a, side="lower")),
            floors_all_instruments={i: float(conformal_quantile(cal_arrays[i], a, side="lower"))
                                    for i in INSTRUMENTS},
        )

    loo = {i: float(min(conformal_quantile(np.delete(cal_arrays[i], j), args.alpha, side="lower")
                        for j in range(n_cal[i]))) for i in INSTRUMENTS}
    eps = {i: dkw_epsilon(n_cal[i], args.alpha) for i in INSTRUMENTS}
    dkw_floor = {
        i: dkw_mean_lower_bound(cal_arrays[i], args.alpha, support=(0.0, 1.0))
        for i in INSTRUMENTS
    }
    dkw_floor_observed_range_scaled_retracted = {
        i: float(cal_arrays[i].mean() - eps[i] * float(
            cal_arrays[i].max() - cal_arrays[i].min()
        ))
        for i in INSTRUMENTS
    }
    cleared = {i: bool(sel_arrays[i].min() >= floors[i]) for i in INSTRUMENTS}
    viol_cal = {i: float((cal_arrays[i] < floors[i]).mean()) for i in INSTRUMENTS}
    viol_sel = {i: float((sel_arrays[i] < floors[i]).mean()) for i in INSTRUMENTS}

    # ---- repeated-split audit: re-run the WHOLE procedure (selection included) on fresh splits
    rng = np.random.default_rng(SEED)
    all_blocks = sorted({b for i in INSTRUMENTS for b, _ in per_inst[i]["calibration"]}
                        | {b for i in INSTRUMENTS for b, _ in per_inst[i]["selection"]})
    by_block = {}
    for i in INSTRUMENTS:
        d = {b: v for b, v in per_inst[i]["calibration"]}
        d.update({b: v for b, v in per_inst[i]["selection"]})
        by_block[i] = d
    floors_over_splits = defaultdict(list)
    viol_over_splits = defaultdict(list)
    for s in range(N_REPEATED_SPLITS):
        perm = rng.permutation(len(all_blocks))
        n_a = len(all_blocks) // 2
        half_a = [all_blocks[i] for i in perm[:n_a]]
        half_b = [all_blocks[i] for i in perm[n_a:]]
        # build the two half-views of every arm, keeping the SAME rule
        view = {}
        for key in us:
            view[key] = {}
            for i in INSTRUMENTS:
                d = by_block[i]
                view[key][i] = {"selection": sorted((b, d[b]) for b in half_a if b in d),
                                "calibration": sorted((b, d[b]) for b in half_b if b in d)}
        if min(len(view[k][i]["selection"]) for k in view for i in INSTRUMENTS) < 9:
            continue
        try:
            k_s, _ = choose(view, "selection", args.alpha)
        except RuntimeError:
            continue
        for i in INSTRUMENTS:
            ca = np.array([v for _, v in view[k_s][i]["calibration"]], float)
            if ca.size < 9:
                continue
            # the ORDER STATISTIC is indexed by block position inside half_b, and half_a is the
            # selection half; comparing half_a's realised values with the floor measures the whole
            # procedure, selection bias included
            sl_half = np.array([v for _, v in view[k_s][i]["selection"]], float)
            n_ca = ca.size
            k_ord = conformal_order_statistic(n_ca, args.alpha)
            if k_ord > n_ca:
                continue
            floor = float(np.sort(ca)[n_ca - k_ord])
            floors_over_splits[i].append(floor)
            viol_over_splits[i].append(float((sl_half < floor).mean()))

    repeated = {}
    for i in INSTRUMENTS:
        f = np.array(floors_over_splits[i], float)
        v = np.array(viol_over_splits[i], float)
        repeated[i] = dict(n_splits=int(f.size),
                           floor_p05=float(np.quantile(f, 0.05)) if f.size else None,
                           floor_p25=float(np.quantile(f, 0.25)) if f.size else None,
                           floor_median=float(np.median(f)) if f.size else None,
                           floor_mean=float(f.mean()) if f.size else None,
                           mean_violation_rate_on_selection_half=float(v.mean()) if v.size else None,
                           median_violation_rate_on_selection_half=float(np.median(v)) if v.size else None)

    # what the control arms would have certified, for context
    def describe(key):
        pi = us[key]
        c = {i: np.array([v for _, v in pi[i]["calibration"]], float) for i in INSTRUMENTS}
        s = {i: np.array([v for _, v in pi[i]["selection"]], float) for i in INSTRUMENTS}
        return dict(recipe=key[0], emitter=key[1], op=key[2],
                    params=op_params(key[2]),
                    selection_mean={i: float(s[i].mean()) for i in INSTRUMENTS},
                    calibration_mean={i: float(c[i].mean()) for i in INSTRUMENTS},
                    certified_floor_at_alpha={i: float(conformal_quantile(c[i], args.alpha,
                                                                          side="lower"))
                                              for i in INSTRUMENTS})

    runner_up = [describe(k) for k in
                 sorted(diag["screened"], key=lambda k: -diag["stats"][k]["means"][PRIMARY])[:8]]
    controls = {k[0] + "/" + k[2]: describe(k) for k in us if k[0] in CONTROL_RECIPES}

    out = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        seconds=round(time.time() - t0, 1),
        method="split conformal selection (Lei, G'Sell, Rinaldo, Tibshirani & Wasserman, JASA 2018)",
        method_doi="https://doi.org/10.1080/01621459.2017.1322365",
        unit_of_exchangeability="spatial holdout block (8x8 contiguous cells, whole catalogue "
                                "components, prevalence-matched instruments)",
        sweep=dict(path=str(args.sweep), n_rows=len(sweep["rows"]),
                   n_blocks=sweep["n_blocks"], blocks_per_side=sweep["blocks_per_side"],
                   calibration_block_indices=sweep["calibration_block_indices"],
                   selection_block_indices=sweep["selection_block_indices"],
                   spacings=sweep["spacings"], densities=sweep["densities_per_1000"],
                   flank_buffers=sweep.get("flank_buffers_px",
                                           [sweep.get("flank_buffer_px", 2.0)])),
        n_arms_total=diag["n_arms"], n_arms_screened=diag["n_screened"],
        note_ranking_key="preregistered: max PM0200 selection-half mean DTI, then worst normalised "
                         "mean over the five instruments, then larger minimum spacing",
        primary_instrument=PRIMARY,
        instruments=list(INSTRUMENTS),
        alpha=args.alpha, confidence_pct=round(100.0 * (1.0 - args.alpha), 3),
        min_blocks_required_for_alpha=min_blocks_for_alpha(args.alpha),
        chosen=dict(recipe=chosen[0], emitter=chosen[1], op=chosen[2], params=op_params(chosen[2]),
                    selection_mean=sel["means"], calibration_mean=cal["means"]),
        guarantee=dict(
            certified_floor_primary_instrument=primary_floor,
            certified_floors_by_instrument=floors,
            n_calibration_blocks_by_instrument=n_cal,
            order_statistic_k_by_instrument=k_used,
            leave_one_out_worst_floor=loo,
            dkw_mean_floor=dkw_floor,
            dkw_mean_floor_observed_range_scaled_retracted=dkw_floor_observed_range_scaled_retracted,
            dkw_epsilon=eps,
            dkw_support={i: [0.0, 1.0] for i in INSTRUMENTS},
            dkw_support_predeclared=True,
            dkw_method="Massart DKW CDF bound with fixed metric support; not scaled by observed sample range",
            dkw_scope="fixed selected-arm calibration-block mean under iid sampling, conditional on selection-only choice",
            dkw_iid_sampling_verified=False,
            dkw_candidate_choice_uses_calibration=False,
            dkw_prospective_protocol_fixation_verified=False,
            dkw_mean_floor_valid_for_full_adaptive_procedure=False,
            single_split_clears_floor_on_selection_half=cleared,
            empirical_violation_rate_on_calibration_half=viol_cal,
            empirical_violation_rate_on_selection_half=viol_sel,
            caveat=("The code chooses on the selection half and computes the fixed-arm floor on "
                    "disjoint calibration blocks. The finite-sample interpretation still requires "
                    "a candidate grid and selection rule fixed independently of calibration and "
                    "exchangeable future/spatial blocks; this script cannot verify those design "
                    "assumptions or prospective protocol timing. Repeated splits reuse the same "
                    "blocks and are sensitivity diagnostics, not independent validation samples."),
        ),
        alpha_sensitivity=alpha_sensitivity,
        repeated_split_robustness=dict(n_requested=N_REPEATED_SPLITS, seed=SEED,
                                       per_instrument=repeated),
        runner_up=runner_up,
        controls=controls,
        pooled_dti={f"{k[0]}/{k[1]}/{k[2]}|{inst}|{h}": round(v["dti_pooled"], 6)
                    for k, pi in pooled.items() for inst, hs in pi.items() for h, v in hs.items()},
        gates=gate_report(us, pooled, chosen, sel, cal, args.alpha),
    )
    p = Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))
    print(f"[chosen] {chosen[0]} / {chosen[1]} / {chosen[2]}")
    print(f"[floor ] {PRIMARY} {primary_floor:.5f} at {out['confidence_pct']:.0f} % "
          f"(n={n_cal[PRIMARY]} calibration blocks, k={k_used[PRIMARY]})")
    print(f"[audit ] repeated-split floor median "
          f"{repeated[PRIMARY]['floor_median']:.5f}, p05 {repeated[PRIMARY]['floor_p05']:.5f}, "
          f"mean violation {repeated[PRIMARY]['mean_violation_rate_on_selection_half']:.3f} "
          f"vs nominal alpha {args.alpha}")
    print(f"wrote {p}  ({time.time() - t0:.1f}s)")
    return 0


def main() -> int:
    print("DISABLED: historical H49 v1 analysis is superseded; no evidence read or file written. See docs/H49_RESULTS.md.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
