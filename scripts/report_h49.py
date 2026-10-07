#!/usr/bin/env python3
"""Historical H49 report generator retained for audit; execution is disabled.

Its original generated wording overstated proxy representativeness, conformal coverage, comparator
attribution, uniqueness, and format compliance. The corrected static report is maintained in
``docs/H49_RESULTS.md`` with the audit overlay in ``evidence/h49/format-contract-audit.json``.
The CLI exits without reading evidence or overwriting the correction.

Historical implementation follows (not approved; do not run). Reads
  evidence/h49/conformal_certificate.json   the selection + certificate + gates
  evidence/submission/bundle_h49.json       the written artifact (if it exists)
  evidence/sweep/sweep_h49.json             Instrument-A sweep (blocked, 5 instruments)
  evidence/sweep/sweep_h49b.json            Instrument-B sweep (SGMC off-catalogue)
  data/reference/h33-2-b2-zeros.tif         the incumbent 0.2778 artifact, via the bundle

The active CLI is disabled; do not overwrite the corrected report.
"""
from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path):
    return json.loads(Path(path).read_text()) if Path(path).exists() else None


def pooled_by_op(rows: list[dict], key_fn) -> dict:
    acc = defaultdict(lambda: defaultdict(float))
    n = defaultdict(int)
    for r in rows:
        k = key_fn(r)
        for f in ("tp", "S", "M", "n_truth", "emitted", "n_scored"):
            acc[k][f] += float(r.get(f) or 0.0)
        n[k] += 1
    return {k: dict(v, n=n[k], pooled=v["tp"] / (0.2 * (v["tp"] + v["S"] - v["M"])
                                                 + 0.8 * v["n_truth"] + 1e-12))
            for k, v in acc.items()}


def _legacy_main() -> int:
    cert = load(ROOT / "evidence" / "h49" / "conformal_certificate.json")
    bundle = load(ROOT / "evidence" / "submission" / "bundle_h49.json")
    sw_a = load(ROOT / "evidence" / "sweep" / "sweep_h49.json")
    sw_b = load(ROOT / "evidence" / "sweep" / "sweep_h49b.json")
    out: list[str] = []
    w = out.append

    w("# H49 round — what the two blocked sweeps certified")
    w("")
    w(f"*Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} by "
      "`scripts/report_h49.py` from the evidence files. Every figure below is read out of a "
      "committed JSON receipt; nothing here is typed by hand.*")
    w("")

    if sw_a:
        w("## The two instruments")
        w("")
        w(f"- **Instrument A** (`evidence/sweep/sweep_h49.json`): {sw_a['n_blocks']} usable 8×8 "
          f"spatial blocks, {len(sw_a['rows']):,} scored rows, five prevalence-matched instruments "
          f"built from the *given* catalogue ({', '.join(sw_a['instruments'])}). Truth = whole "
          "catalogue components held out of the visible catalogue. It measures *ordering against "
          "mapped faults* and is optimistic for any topographic field.")
        w(f"- **Instrument B** (`evidence/sweep/sweep_h49b.json`): {sw_b['n_blocks']} usable 8×8 "
          f"blocks, {len(sw_b['rows']):,} scored rows, truth = USGS SGMC traces more than "
          f"{sw_b['min_cat_dist_px']:g} px (300 m) from the given catalogue, whole components, "
          f"prevalence-matched to `{sw_b['prevalence']}`. The given catalogue is masked in full, so "
          "this is the competition's own masking rule against faults the catalogue does **not** "
          "contain — the population the organiser scores.")
        w("")
        w("Both sweeps share one seeded 50/50 split of their blocks into a **selection half** and a "
          "**calibration half**; disjoint roles, so a choice made on one half is certified on the "
          "other.")
        w("")

    if cert:
        c = cert["shipped_selection"]
        p = c["params"]
        cb = cert["certificate"]["primary"]
        ca = cert["certificate"]["corroborating"]
        frozen = cert["preregistered_selection"]
        w("## The selected operating point")
        w("")
        w(f"`{c['recipe']}` · `{c['emitter']}` · spacing **{p['min_dist']:g} px "
          f"({p['min_dist'] * 100:g} m)** · density **{p['density_per_1000']:g} per 1,000 scored px** · "
          f"catalogue-flank buffer **{p['flank_b']:g} px ({p['flank_b'] * 100:g} m)**")
        w("")
        w(f"- shipped rule: {c['rule']}")
        w(f"- preregistered rule (`{cert['preregistration']}`) selected "
          f"`{frozen['recipe']}` / `{frozen['emitter']}` / `{frozen['op']}`; its own certified "
          f"Instrument-B floor is "
          f"{cert['certificate_of_the_preregistered_arm']['primary']['certified_floor']:.5f} and the "
          f"re-split audit below records how often each rule reproduces its own pick.")
        w(f"- amendment: {cert['amendment_justification']}")
        w("")
        w("## The split-conformal certificate")
        w("")
        w(f"**A fresh 8×8 spatial block scores at least DTI = {cb['certified_floor']:.5f} with "
          f"probability ≥ {cb['confidence_pct']:.0f} %** (Instrument B, α = {cert['alpha']:g}, "
          f"n = {cb['n_calibration_blocks']} calibration blocks, order statistic k = "
          f"{cb['order_statistic_k']}, rank-covered).")
        w("")
        w("| quantity | Instrument B (SGMC off-catalogue, primary) | Instrument A (PM0200, "
          "corroborating) |")
        w("|---|---:|---:|")
        w(f"| certified floor (α = {cert['alpha']:g}) | **{cb['certified_floor']:.5f}** | "
          f"{ca['certified_floor']:.5f} |")
        for a, label in (("alpha=0.05", "α = 0.05 (95 %)"), ("alpha=0.20", "α = 0.20 (80 %)"),
                         ("alpha=0.25", "α = 0.25 (75 %)"), ("alpha=0.30", "α = 0.30 (70 %)")):
            fb = cb["floors_by_alpha"].get(a)
            fa = ca["floors_by_alpha"].get(a)
            w(f"| floor at {label} | {('vacuous' if fb is None else f'{fb:.5f}')} | "
              f"{('vacuous' if fa is None else f'{fa:.5f}')} |")
        w(f"| calibration-half mean | {cb['calibration_mean']:.5f} "
          f"(min {cb['calibration_min']:.5f}) | {ca['calibration_mean']:.5f} |")
        w(f"| selection-half mean | {cb['selection_mean']:.5f} "
          f"(min {cb['selection_min']:.5f}) | {ca['selection_mean']:.5f} |")
        w(f"| leave-one-out worst floor | {cb['leave_one_out_worst_floor']:.5f} | "
          f"{ca['leave_one_out_worst_floor']:.5f} |")
        w(f"| DKW mean floor (mean over blocks, not a single block) | {cb['dkw_mean_floor']:.5f} | "
          f"{ca['dkw_mean_floor']:.5f} |")
        w(f"| blocks below the floor: calibration / selection ({cb['n_calibration_blocks']} / "
          f"{cb['n_selection_blocks']}) | {cb['blocks_below_floor_calibration']} / "
          f"{cb['blocks_below_floor_selection']} | {ca['blocks_below_floor_calibration']} / "
          f"{ca['blocks_below_floor_selection']} |")
        w(f"| empirical violation rate: calibration / selection | "
          f"{cb['violation_rate_on_calibration_half']:.4f} / "
          f"{cb['violation_rate_on_selection_half']:.4f} | "
          f"{ca['violation_rate_on_calibration_half']:.4f} / "
          f"{ca['violation_rate_on_selection_half']:.4f} |")
        w("")
        rs = cert["repeated_split_robustness"]
        rs_frozen = cert["repeated_split_robustness_of_the_preregistered_rule"]
        w(f"**Repeated-split audit of the whole procedure** ({rs['n_effective']} effective of "
          f"{rs['n_requested']} independent 50/50 splits, selection included): floor p05 "
          f"{rs['floor_p05']:.5f}, median {rs['floor_median']:.5f}, mean "
          f"{rs['floor_mean']:.5f}; mean violation rate of the certified floor on the half that did "
          f"not certify it **{rs['mean_violation_rate']:.4f} vs the nominal α = {cert['alpha']:g}** "
          f"(median {rs['median_violation_rate']:.4f}).")
        w("")
        sel_freq = ", ".join(f"`{k}` {v}× ({100.0 * v / rs['n_requested']:.0f} %)"
                             for k, v in list(rs["selection_frequency"].items())[:4])
        w(f"Under the shipped rule the re-splits select: {sel_freq}. Under the preregistered "
          f"floor rule they select "
          f"{', '.join(f'{k} {v}×' for k, v in list(rs_frozen['selection_frequency'].items())[:3])}"
          " — the maximum of an order statistic over ~20 blocks is decided by which single block "
          "lands where, which is why the shipped rule is the mean one and why this audit exists.")
        w("")
        w("## Gates")
        w("")
        g = cert["gates"]
        w("| gate | value | pass |")
        w("|---|---|---|")
        w(f"| positive certified Instrument-B floor | {cb['certified_floor']:.5f} | "
          f"**{g['positive_certified_floor']}** |")
        w(f"| credible at α (k ≤ n) | k = {cb['order_statistic_k']}, n = "
          f"{cb['n_calibration_blocks']} | **{g['credible_at_alpha']}** |")
        w(f"| beats the fixed-seed random control on the B selection mean | "
          f"{cb['selection_mean']:.5f} vs {g['random_control_selection_mean']:.5f} | "
          f"**{g['beats_random_control_mean']}** |")
        w(f"| beats the frozen 0.2778 incumbent artifact on the B selection mean | "
          f"{cb['selection_mean']:.5f} vs {g['incumbent_selection_mean']:.5f} | "
          f"**{g['beats_incumbent_selection_mean']}** |")
        w(f"| shipped arm is the isotropic emitter itself | "
          f"{g['chosen_is_the_isotropic_emitter']} | — |")
        w("")
        if bundle:
            u = bundle["uniqueness"]
            op = bundle["operating_point"]
            w("## The written artifact")
            w("")
            w(f"- `{bundle['submission_name']}.tif` — {u['n_prior_rasters_compared']} prior rasters "
              f"compared, max Jaccard {u['max_jaccard_vs_prior']:.6f} "
              f"(`{u['worst_jaccard_file']}`), max containment {u['max_containment_vs_prior']:.6f}, "
              f"`is_unique = {u['is_unique']}`")
            w(f"- {op['emitted_px']:,} unit dots = "
              f"{1000.0 * op['emitted_px'] / op['n_scored_domain']:.3f} per 1,000 scored px = "
              f"{op['emitted_pct_of_footprint']:.4f} % of the footprint; engine `{op['engine']}`")
            fr = bundle.get("format_receipt") or {}
            w(f"- format: {sum(1 for v in fr.get('checks', {}).values() if v)}/"
              f"{len(fr.get('checks', {}))} read-back checks passed "
              f"(`all_checks_passed = {fr.get('all_checks_passed')}`), binary values "
              f"{bundle['values_are_binary']}, note {bundle['note_length']}/200 chars")
            w(f"- **the overlap with our own previous artifact is the largest in the audit** "
              f"({u['max_jaccard_vs_prior']:.4f} Jaccard, {u['max_containment_vs_prior']:.4f} "
              f"containment of its dots): this is a different *operating point and field* "
              "(a signed-polarity term is added to the round-2 recipe, and the catalogue-flank "
              "buffer moves from 200 m to 300 m), not a different detector family, and the audit "
              "says so instead of hiding it.")
            w("")
    if sw_a or sw_b:
        w("## The density question this round actually settled")
        w("")
        w("Instrument A (mapped faults) keeps rewarding more mass; Instrument B (faults the "
          "catalogue does not contain) peaks in the interior. The shipped point is the interior "
          "optimum of the population that resembles the scoring target.")
        w("")
        keys_recipe = "R7_scarp9_polarity"
        for tag, sw, inst in (("B (SGMC off-catalogue)", sw_b, "B_sgmc_offcat"),
                              ("A (PM0200)", sw_a, "PM0200")):
            if not sw:
                continue
            acc = defaultdict(lambda: defaultdict(float))
            n = defaultdict(int)
            for r in sw["rows"]:
                if r["recipe"] != keys_recipe or r["emitter"] != "disk" or r["instrument"] != inst:
                    continue
                if abs(float(r.get("min_dist", 2.8)) - 2.8) > 1e-9 or abs(
                        float(r.get("flank_b", 0.0)) - 3.0) > 1e-9:
                    continue
                k = float(r["density_per_1000"])
                for f in ("tp", "S", "M", "n_truth", "dti"):
                    acc[k][f] += float(r.get(f) or 0.0)
                n[k] += 1
            if not acc:
                continue
            w(f"**Instrument {tag}** — recipe `{keys_recipe}`, `disk`, 2.8 px, 300 m flank")
            w("")
            w("| density / 1,000 scored px | mean block DTI | pooled DTI | recall of the truth | "
              "emitted px (per block, mean) |")
            w("|---:|---:|---:|---:|---:|")
            for k in sorted(acc):
                a = acc[k]
                denom = 0.2 * (a["tp"] + a["S"] - a["M"]) + 0.8 * a["n_truth"]
                w(f"| {k:g} | {a['dti'] / n[k]:.5f} | {a['tp'] / denom:.5f} | "
                  f"{a['tp'] / max(a['n_truth'], 1e-9):.4f} | {a['S'] / n[k]:.0f} |")
            w("")

    if cert:
        pt = cert.get("paired_tests") or {}
        rows = [(name, d) for name, d in pt.items() if d]
        if rows:
            w("## Paired block tests (the new hypotheses, reported even though they lose)")
            w("")
            w("| comparison | half | n blocks | mean difference | a better | b better |")
            w("|---|---|---:|---:|---:|---:|")
            for name, d in rows:
                for half, v in d.items():
                    if not v:
                        continue
                    w(f"| {name} — {v['a']} minus {v['b']} | {half} | {v['n']} | "
                      f"{v['mean_difference']:+.5f} | {v['blocks_where_a_better']} | "
                      f"{v['blocks_where_b_better']} |")
            w("")
            w("H49-A (strike-aligned `nms_oriented`) and H49-B (signed polarity coherence) are "
              "**not established**: the paired differences change sign between halves and "
              "instruments and never clear a sign test. The shipped artifact therefore uses the "
              "isotropic emitter and the frozen recipe family, at the newly certified operating "
              "point — published as a negative result, not buried.")
            w("")

    w("## What this round does *not* claim")
    w("")
    w("- No leaderboard score is claimed for the artifact; the certificate is about a *block-level* "
      "holdout DTI on a public proxy population, not about the organiser's private labels.")
    w("- Instrument B rewards topographic detectors optimistically because SGMC also contains "
      "pre-Quaternary and lithologic contacts.")
    w("- Spatial blocks are not geologically exchangeable; the leave-one-out worst floor and the "
      "repeated-split audit are reported because the single-split floor alone would hide that.")
    w("- The H49-A strike-aligned emitter and the H49-B polarity transform are reported with their "
      "measured paired results in `evidence/h49/` even where they lose.")
    w("")
    p = ROOT / "docs" / "H49_RESULTS.md"
    p.write_text("\n".join(out) + "\n")
    print(f"wrote {p} ({len(out)} lines)")
    return 0


def main() -> int:
    print("DISABLED: the historical H49 report generator would overwrite the corrected caveats. See docs/H49_RESULTS.md. No evidence read or file written.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
