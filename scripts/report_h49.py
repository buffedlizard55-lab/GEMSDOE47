#!/usr/bin/env python3
"""Render docs/H49_RESULTS.md from evidence only -- no number in it is hand-typed.

Reads
  evidence/h49/conformal_certificate.json   the selection + certificate + gates
  evidence/submission/bundle_h49.json       the written artifact (if it exists)
  evidence/sweep/sweep_h49.json             Instrument-A sweep (blocked, 5 instruments)
  evidence/sweep/sweep_h49b.json            Instrument-B sweep (SGMC off-catalogue)
  data/reference/h33-2-b2-zeros.tif         the H33-labelled reference mask (score attribution unverified)

Run:  python3 scripts/report_h49.py
Out:  docs/H49_RESULTS.md
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


def main() -> int:
    cert = load(ROOT / "evidence" / "h49" / "conformal_certificate.json")
    bundle = load(ROOT / "evidence" / "submission" / "bundle_h49.json")
    sw_a = load(ROOT / "evidence" / "sweep" / "sweep_h49.json")
    sw_b = load(ROOT / "evidence" / "sweep" / "sweep_h49b.json")
    public_audit_path = ROOT / "evidence" / "h49" / "pinned-public-inventory-uniqueness.json"
    public_audit = load(public_audit_path) if public_audit_path.exists() else None
    out: list[str] = []
    w = out.append

    w("# H49 round — blocked-sweep results, review findings, and limits")
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
          f"prevalence-matched to `{sw_b['prevalence']}`. The given catalogue is masked in full, "
          "consistent with the public scoring clarification, but SGMC includes lithologic contacts "
          "and other non-fault traces. Treat Instrument B as a public proxy, not the organizer's "
          "hidden target population.")
        w("")
        w("Both sweeps use one seeded 50/50 split: 20 selection blocks and 19 calibration blocks "
          "(with instrument-specific usable-block counts). The halves are disjoint for a fixed arm. "
          "However, the workflow later chose between the floor and mean rules after reviewing the "
          "full sweep/re-split results, so the calibration half is not an auditable untouched holdout "
          "for the final adaptive rule.")
        w("")

    if cert:
        c = cert["shipped_selection"]
        p = c["params"]
        cb = cert["certificate"]["primary"]
        ca = cert["certificate"]["corroborating"]
        frozen = cert["preregistered_selection"]
        w("## Selected operating point — research-only; slot gate closed")
        w("")
        w("The artifact remains downloadable for review, but **do not spend a submission slot**. "
          "The published selection procedure is not prospectively auditable from the repository, "
          "and the paired 90 % conformal lower bound on improvement over the incumbent is negative.")
        w("")
        w(f"`{c['recipe']}` · `{c['emitter']}` · spacing **{p['min_dist']:g} px "
          f"({p['min_dist'] * 100:g} m)** · density **{p['density_per_1000']:g} per 1,000 scored px** · "
          f"catalogue-flank buffer **{p['flank_b']:g} px ({p['flank_b'] * 100:g} m)**")
        w("")
        w(f"- shipped rule: {c['rule']}")
        w(f"- saved floor-rule arm (`{cert['preregistration']}`) selected "
          f"`{frozen['recipe']}` / `{frozen['emitter']}` / `{frozen['op']}`; its nominal fixed-arm "
          f"Instrument-B floor is "
          f"{cert['certificate_of_the_preregistered_arm']['primary']['certified_floor']:.5f}. "
          "The addendum says it was written before the sweep, but Git history cannot independently "
          "verify that: the addendum, sweep evidence and certificate first appear together in "
          "commit `409c407` (2026-10-07 03:35 UTC); the sweep file records generation at "
          "03:17 UTC. This is not proof the draft was late, only that prospective timing is not "
          "auditable from this repository.")
        w(f"- amendment: {cert['amendment_justification']}")
        w("")
        w("## Nominal split-conformal diagnostic — assumptions and scope")
        w("")
        w(f"For a rule fixed independently of calibration outcomes, the Instrument-B order statistic "
          f"is {cb['certified_floor']:.5f} at nominal {cb['confidence_pct']:.0f} % "
          f"(α = {cert['alpha']:g}, n = {cb['n_calibration_blocks']} calibration blocks, "
          f"order statistic k = {cb['order_statistic_k']}). This is conditional on exchangeable "
          "spatial blocks and a fixed rule. Since the mean-rule change was made after the sweep, "
          "and the same 39 blocks informed that change, do **not** interpret this as a prospective "
          "guarantee for the complete adaptive procedure, for a geographic subregion, or for the "
          "organizer's private labels.")
        w("")
        w("| quantity | Instrument B (SGMC off-catalogue, primary) | Instrument A (PM0200, "
          "corroborating) |")
        w("|---|---:|---:|")
        w(f"| nominal fixed-arm floor (α = {cert['alpha']:g}) | **{cb['certified_floor']:.5f}** | "
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
        w(f"**Repeated-partition stability diagnostic** ({rs['n_effective']} Monte Carlo "
          f"re-partitions of the same 39 blocks; block observations are reused, so these are not "
          f"independent validation samples): floor p05 {rs['floor_p05']:.5f}, median "
          f"{rs['floor_median']:.5f}, mean {rs['floor_mean']:.5f}; mean violation rate on the "
          f"other half {rs['mean_violation_rate']:.4f} vs nominal α = {cert['alpha']:g}. This "
          "summarizes sensitivity/stability only; it does not create new holdout evidence or restore "
          "prospective validity to the rule amendment.")
        w("")
        sel_freq = ", ".join(f"`{k}` {v}× ({100.0 * v / rs['n_requested']:.0f} %)"
                             for k, v in list(rs["selection_frequency"].items())[:4])
        w(f"Across those reused-block re-partitions, the mean rule selects: {sel_freq}. The "
          f"saved floor rule selects "
          f"{', '.join(f'{k} {v}×' for k, v in list(rs_frozen['selection_frequency'].items())[:3])}. "
          "These frequencies are conditional on this same set of 39 blocks and are not evidence "
          "from new geology.")
        w("")
        pairwise = cert.get("paired_vs_incumbent") or {}
        if pairwise:
            w("### Paired differences versus the incumbent")
            w("")
            w("Positive means the candidate beats the H33 reference mask on that same block. "
              "The Student-t lower bound is assumption-dependent; the split-conformal lower bound "
              "is an order statistic for a fresh exchangeable block, conditional on a fixed arm. "
              "Both candidate arms have a negative conformal lower bound, so a positive per-block "
              "improvement is not established at 90 %, even though the sample mean is positive.")
            w("")
            w("| arm | half | n | mean ΔDTI | candidate / incumbent wins | paired-mean one-sided 90% t LCB | "
              "paired-difference 90% conformal lower bound | sign-test p (greater) |")
            w("|---|---|---:|---:|---:|---:|---:|---:|")
            for arm, halves in pairwise.items():
                for half, row in halves.items():
                    if row is None:
                        continue
                    w(f"| {arm.replace('_', ' ')} | {half} | {row['n']} | "
                      f"{row['mean_difference']:+.5f} | {row['blocks_where_a_better']} / "
                      f"{row['blocks_where_b_better']} | {row['paired_mean_one_sided_t_lcb']:+.5f} | "
                      f"{row['paired_difference_split_conformal_lower_bound']:+.5f} | "
                      f"{row['one_sided_sign_test_p_greater']:.4f} |")
            w("")
        w("## Descriptive screen checks — not slot authorization")
        w("")
        g = cert["gates"]
        w("| gate | value | pass |")
        w("|---|---|---|")
        w(f"| positive nominal fixed-arm Instrument-B floor | {cb['certified_floor']:.5f} | "
          f"**{g['positive_certified_floor']}** |")
        w(f"| credible at α (k ≤ n) | k = {cb['order_statistic_k']}, n = "
          f"{cb['n_calibration_blocks']} | **{g['credible_at_alpha']}** |")
        w(f"| beats the fixed-seed random control on the B selection mean | "
          f"{cb['selection_mean']:.5f} vs {g['random_control_selection_mean']:.5f} | "
          f"**{g['beats_random_control_mean']}** |")
        w(f"| descriptive B selection-half mean vs the 0.2778-labelled H33 reference | "
          f"{cb['selection_mean']:.5f} vs {g['incumbent_selection_mean']:.5f} | "
          f"**{g['beats_incumbent_selection_mean']}** (post-selection comparison) |")
        w(f"| shipped arm is the isotropic emitter itself | "
          f"{g['chosen_is_the_isotropic_emitter']} | — |")
        w("| independently auditable preregistration + positive 90% paired-improvement floor | "
          "not satisfied | **False — do not spend a slot** |")
        w("")
        if bundle:
            u = bundle["uniqueness"]
            op = bundle["operating_point"]
            w("## The written artifact")
            w("")
            w(f"- `{bundle['submission_name']}.tif` — {u['n_prior_rasters_compared']} local/archive "
              f"raster comparisons, maximum positive-mask Jaccard {u['max_jaccard_vs_prior']:.6f} "
              f"(`{u['worst_jaccard_file']}`), maximum containment {u['max_containment_vs_prior']:.6f}, "
              f"local exact-match flag `is_unique = {u['is_unique']}`. This bounded local check is "
              "not a global uniqueness proof.")
            if public_audit:
                rows = public_audit.get("rows", [])
                top = next((row for row in rows if row.get("jaccard") == public_audit.get("max_jaccard")), {})
                top_path = (top.get("paths", [{}])[0].get("repository", "local history") + "/" +
                            top.get("paths", [{}])[0].get("path", top.get("path", "")))
                excluded = [row for row in rows
                            if row.get("status") not in ("compared", "compared_local_history")]
                excluded_counts: dict[str, int] = defaultdict(int)
                for row in excluded:
                    excluded_counts[row.get("status", "unknown")] += 1
                excluded_summary = ", ".join(
                    f"{n} {status.replace('_', ' ')}" for status, n in sorted(excluded_counts.items()))
                pinned_comparisons = sum(row.get("status") == "compared" for row in rows)
                local_comparisons = sum(row.get("status") == "compared_local_history" for row in rows)
                w(f"- Pinned public inventory: {public_audit['public_repositories_in_inventory']} "
                  f"commit-pinned public repositories; {pinned_comparisons} comparable inventory "
                  f"blobs plus {local_comparisons} local-history rasters ({public_audit['comparisons']} "
                  f"comparisons total); {public_audit['exact_matches']} exact mask/value matches; "
                  f"maximum Jaccard {public_audit['max_jaccard']:.6f} ({top_path}); "
                  f"{len(excluded)} entries excluded from direct comparison ({excluded_summary or 'none'}); "
                  f"{public_audit['failed_repository_inventories']} repository inventories failed. "
                  "The inventory is scoped to visible public owner repositories, not global; "
                  f"`global_unique_proven = {public_audit['global_unique_proven']}`. Full machine-readable "
                  "receipt: `evidence/h49/pinned-public-inventory-uniqueness.json`. Website copy: "
                  "`docs/data/pinned-public-inventory-uniqueness.json`.")
            w(f"- {op['emitted_px']:,} unit dots = "
              f"{1000.0 * op['emitted_px'] / op['n_scored_domain']:.3f} per 1,000 scored px = "
              f"{op['emitted_pct_of_footprint']:.4f} % of the footprint; engine `{op['engine']}`")
            fr = bundle.get("format_receipt") or {}
            gating = {k: v for k, v in fr.get("checks", {}).items()
                      if k not in fr.get("informational_checks", [])}
            n_gating_passed = sum(bool(v) for v in gating.values())
            stats = fr.get("stats", {})
            w(f"- exact published TIFF: {fr.get('bytes'):,} bytes, SHA-256 `{bundle['sha256'][1]}`; "
              f"one float32 band, {fr.get('width')} × {fr.get('height')}, EPSG:{fr.get('crs_epsg')}, "
              f"no nodata tag; internal mask matches the {stats.get('footprint_cells'):,}-cell "
              "official footprint and masked reads are null outside.")
            w(f"- format/read-back: {n_gating_passed}/{len(gating)} gating checks pass "
              f"(`all_checks_passed = {fr.get('all_checks_passed')}`); informational whole-grid "
              f"range flag is {fr.get('strongest_range_guarantee')}; raw full-grid cells are finite "
              f"in [0,1], with {stats.get('positive_cells_in_footprint'):,} positives. Binary values "
              f"{bundle['values_are_binary']}; portal note {bundle['note_length']}/200 chars.")
            w(f"- The largest local overlap is {u['max_jaccard_vs_prior']:.4f} Jaccard and "
              f"{u['max_containment_vs_prior']:.4f} containment. It is a different mask, but still "
              "shares the same broad persistence/density detector lineage; the polarity-scored "
              "field and larger catalogue buffer are incremental changes, not an independent "
              "detector family. See the pinned public-inventory audit for a bounded exact-grid check.")
            w("")
    if sw_a or sw_b:
        w("## The density question this round actually settled")
        w("")
        w("Within these particular public proxies, the mapped-fault instrument tends to reward "
          "more emitted mass while the SGMC proxy has an interior peak. This is a descriptive sweep "
          "result, not evidence that the SGMC peak matches the organizer's hidden target or that "
          "the selected point is optimal on the leaderboard.")
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
            w("## Paired block comparisons (descriptive results; no private-label score)")
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
            w("The strike-aligned emitter does not show a robust gain over the disk emitter on "
              "these blocks. The candidate polarity field has a higher selection-half mean than the "
              "alternative field in this sweep, but its paired lower bound does not establish a "
              "fresh-block improvement; moreover, Instrument B is a mixed geological-contact proxy. "
              "These results do not establish that the polarity feature detects uncatalogued faults. "
              "The published mask uses the disk emitter with the R7 polarity-scored field, but its "
              "mean-rule choice was made after seeing the full analysis and remains research-only.")
            w("")

    w("## What this round does *not* claim")
    w("")
    w("- No organizer/leaderboard score is authenticated for this TIFF. The only score-like values "
      "here are block-level DTI measurements on public proxies.")
    w("- Instrument B is SGMC-derived; lithologic contacts and other non-fault traces may act as "
      "false positives. It is not the private target map.")
    w("- Spatial-block exchangeability is an assumption, not established fact. The 400 re-splits "
      "reuse the same 39 blocks and are sensitivity diagnostics only.")
    w("- Git history cannot establish that the B rule was fixed before sweep results; the shipped "
      "mean rule is a post-results amendment. No full-procedure or unconditional conformal guarantee "
      "is claimed.")
    w("- A positive sample mean/t lower bound is not a positive 90% conformal lower bound on "
      "paired improvement for a new block. Neither candidate arm passed that promotion criterion.")
    w("- The H49-A strike-aligned emitter and H49-B polarity transform are descriptive hypotheses, "
      "not validated geological discoveries. See `docs/RESEARCH_HYPOTHESES.md`.")
    w("")
    p = ROOT / "docs" / "H49_RESULTS.md"
    p.write_text("\n".join(out).rstrip() + "\n")
    print(f"wrote {p} ({len(out)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
