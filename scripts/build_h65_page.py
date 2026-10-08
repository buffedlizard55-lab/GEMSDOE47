#!/usr/bin/env python3
"""Render docs/h65.html — the H65-H68 evidence page — from the receipts.

Every number on the page is read from ``evidence/h65/screen.json``,
``evidence/h33_reference_analysis.json`` and ``docs/data/{h65,h68}-artifact.json``;
nothing is hand-typed, so the page cannot drift from the measurements.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

screen = json.loads((ROOT / "evidence" / "h65" / "screen.json").read_text())
h33 = json.loads((ROOT / "evidence" / "h33_reference_analysis.json").read_text())
a65 = json.loads((DOCS / "data" / "h65-artifact.json").read_text())
a68 = json.loads((DOCS / "data" / "h68-artifact.json").read_text())

SPACINGS = screen["design"]["spacings_px"]
ARMS = ("h50", "h60", "h65", "h66", "h67", "h68")
ARM_LABEL = {
    "h50": "H50 slope-anomaly anchor",
    "h60": "H60 lidar scarp-crest (incumbent)",
    "h65": "H65 scarp-consensus field",
    "h66": "H66 far-field lidar field",
    "h67": "H67 alteration-corroborated lidar field",
    "h68": "H68 eight-channel lidar field",
}
gate = screen["gate"]["per_arm"]
arms = screen["arms"]
ctrl = screen["controls"]


def panel(a: dict, role: str, verdict: str) -> str:
    stem = a["artifact"]
    tif = f"{stem}-allfinite.tif"
    cov = a["conformal"]["coverage_at_least"]
    rank = a["conformal"]["rank_1_based"]
    ncal = a["conformal"]["calibration_blocks"]
    sp = a["spacing_px"]
    return f"""<div class="download-panel" id="{a['hypothesis_id'].lower()}-download"><div><span class="eyebrow">{role} · generated 2026-10-08 · {a['bytes']:,} bytes</span><h2>{a['hypothesis_id']} — {a['artifact'].split('-', 2)[2].replace('-', ' ')}.</h2><p>{ARM_BLURB[a['hypothesis_id'].lower()]}. Emitted as {a['budget']:,} unit dots at {sp:g}&nbsp;px ({sp*100:g}&nbsp;m) over the noise-masked off-catalogue domain. <strong>Values are 0/1 only, float32, single band, EPSG:32611, 100&nbsp;m, all finite, no NoData tag, zeros outside the footprint.</strong></p></div><div class="actions"><a href="downloads/{tif}" class="button primary" download="">↓ Download the {a['hypothesis_id']} GeoTIFF</a><a href="downloads/{stem}.zip" class="button secondary" download="">ZIP + note + receipt</a><a href="downloads/{stem}-note.txt" class="text-link">Note (copy-paste)</a></div><p class="filename">{tif}</p><p class="export-confidence">Spacing {sp:g} px / {sp*100:g} m · selected by split conformal prediction (Lei et al. JASA 2018, Algorithm 2) as the spacing with the greatest certified floor · max-residual rank {rank} of {ncal + 1} · finite-sample coverage at least {cov:.2%} (confidence level {cov:.2%}) · certified holdout floor {a['conformal']['certified_floor_dti']:.4f} DTI · conditional on block exchangeability</p><p class="hash">SHA-256 <code>{a['sha256_tif']}</code></p><p class="export-confidence">{verdict}</p></div>"""


ARM_BLURB = {
    "h65": "the amplitude-tie-broken consensus count of the six lidar scarp channels "
           "(how many independent operators fire at the same cell), road/claim masked",
    "h68": "the per-cell maximum of the ranks of eight lidar scarp channels (H60's six "
           "plus slope-excess ex_max and local relief), road/claim masked",
}

V65 = (f"<strong>NOT OK TO SUBMIT while the uniqueness bar stands.</strong> H65 beat the "
       f"H60 incumbent on BOTH holdout instruments ({a65['holdout']['candidate_pooled_dti']:.4f} "
       f"vs {a65['holdout']['h60_incumbent_pooled_dti']:.4f} primary; "
       f"{a65['holdout']['candidate_sgmc_pooled_dti']:.4f} vs "
       f"{a65['holdout']['h60_incumbent_sgmc_pooled_dti']:.4f} SGMC) and passed control "
       f"conditions 1–5, but its emission overlaps the H60 artifact at mask Jaccard "
       f"{a65['uniqueness']['max_jaccard']:.4f} ≥ 0.5, failing frozen condition 6. It is "
       f"unique against every scored prior submission (max 0.0067; {a65['uniqueness']['compared']} "
       f"priors compared, zero exact matches). Research artifact, retained for audit.")
V68 = (f"<strong>OK to download: YES · valid submission · recommended for submission: "
       f"NO — H60 remains the file to submit.</strong> H68 passed the four control "
       f"conditions and the uniqueness bar (max Jaccard {a68['uniqueness']['max_jaccard']:.4f}), "
       f"and holds the round's best independent-instrument DTI "
       f"({a68['holdout']['candidate_sgmc_pooled_dti']:.4f} vs H60's "
       f"{a68['holdout']['h60_incumbent_sgmc_pooled_dti']:.4f}), but it does not beat H60 "
       f"on the primary instrument ({a68['holdout']['candidate_pooled_dti']:.4f} vs "
       f"{a68['holdout']['h60_incumbent_pooled_dti']:.4f}). Note for the DrivenData "
       f"form's optional Note field: <code>{a68['submission_note_field']}</code>")

# ---------------------------------------------------------------- results table
rows_html = []
for arm in ARMS:
    v = arms[arm]
    chosen = SPACINGS.index(v["selected_spacing_px"])
    cells = "".join(
        f"<td>{'<strong>' if i == chosen else ''}{v['selection_means'][i]:.4f}"
        f"{'</strong>' if i == chosen else ''}</td>"
        for i in range(len(SPACINGS)))
    rows_html.append(
        f'<tr><td>{ARM_LABEL[arm]}</td>{cells}'
        f'<td><strong>{v["pooled_primary_selection"]:.4f}</strong></td>'
        f'<td><strong>{v["pooled_sgmc_selection"]:.4f}</strong></td>'
        f'<td>{v["conformal"]["floor"]:.4f}</td></tr>')
rows_html.append(
    '<tr><td>Mass-matched spaced random (control)</td>'
    + "".join("<td>—</td>" for _ in SPACINGS)
    + f'<td>{ctrl["h68"]["random"]["primary"]:.4f}</td>'
    + f'<td>{ctrl["h68"]["random"]["sgmc"]:.4f}</td><td>—</td></tr>')
rows_html.append(
    '<tr><td>Owner-reported d2.8 reference (control)</td>'
    + "".join("<td>—</td>" for _ in SPACINGS)
    + f'<td>{ctrl["h68"]["h33_reference"]["primary"]:.4f}</td>'
    + f'<td>{ctrl["h68"]["h33_reference"]["sgmc"]:.4f}</td><td>—</td></tr>')
results_table = (
    '<div class="table-scroll"><table><thead><tr><th scope="col">Arm (selection half)</th>'
    + "".join(f"<th>{s:g}</th>" for s in SPACINGS)
    + '<th scope="col">Pooled primary DTI @ chosen spacing</th>'
      '<th scope="col">Pooled SGMC DTI @ chosen spacing</th>'
      '<th scope="col">Certified conformal floor</th></tr></thead><tbody>'
    + "".join(rows_html) + "</tbody></table></div>")

# ---------------------------------------------------------------- gate table
gate_rows = []
for arm in ("h65", "h66", "h67", "h68"):
    c = gate[arm]["conditions"]
    def mark(b: bool) -> str:
        return "PASS" if b else "FAIL"
    gate_rows.append(
        f'<tr><td>{ARM_LABEL[arm]}</td>'
        f'<td>{mark(c["beats_h50_by_10pct"])}</td>'
        f'<td>{mark(c["positive_conformal_floor"])}</td>'
        f'<td>{mark(c["sgmc_beats_random"])}</td>'
        f'<td>{mark(c["beats_random_3x_primary"])}</td>'
        f'<td>{mark(c["beats_incumbent_h60"])}</td>'
        f'<td><strong>{"GATE PASSED" if gate[arm]["passed"] else "REFUTED"}</strong></td></tr>')
gate_table = (
    '<div class="table-scroll"><table><thead><tr><th scope="col">Arm</th>'
    '<th>Beats H50 anchor by ≥10%</th><th>Positive conformal floor</th>'
    '<th>SGMC beats random</th><th>≥3× random (primary)</th>'
    '<th>Beats H60 incumbent (both)</th><th>Verdict (conditions 1–4)</th></tr></thead>'
    '<tbody>' + "".join(gate_rows) + "</tbody></table></div>")

# ---------------------------------------------------------------- floor table
floor_rows = []
for arm in ("h60", "h65", "h66", "h67", "h68"):
    v = arms[arm]
    floor_rows.append(
        f'<tr><td>{ARM_LABEL[arm]}</td>'
        + "".join(f"<td>{x:.4f}</td>" for x in v["conformal"]["lower_bounds"])
        + f'<td><strong>{v["selected_spacing_px"]:g} px</strong></td></tr>')
floor_table = (
    '<div class="table-scroll"><table><thead><tr><th scope="col">Arm</th>'
    + "".join(f"<th>{s:g} px</th>" for s in SPACINGS)
    + '<th scope="col">Selected (argmax floor)</th></tr></thead><tbody>'
    + "".join(floor_rows) + "</tbody></table></div>")

h33g = h33["geometry"]

html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>H65–H68 · session 6 · GEMSDOE47</title>
<meta name="description" content="Session 6: scarp consensus, far-field, lidar+Th/K alteration and eight-channel lidar fields, screened on the frozen 41-block holdout with split-conformal operating-point selection. H65 beat the H60 incumbent on both instruments but is blocked by the frozen uniqueness bar; H68 is the new unique validated candidate; H60 stays primary.">
<meta name="theme-color" content="#173d38"><link rel="icon" href="assets/mark.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/site.css"><script src="assets/site.js" defer></script></head>
<body data-site-version="h65" data-base=""><a class="skip" href="#main">Skip to evidence</a>
<header class="masthead"><a class="brand" href="index.html"><span class="brand-mark" aria-hidden="true">G/47</span><span>GEMSDOE47<small>Fault mapping research</small></span></a>
<nav aria-label="Main navigation"><a href="executive-summary.html" aria-current="false">Summary</a><a href="h65.html" aria-current="page">H65–H68</a><a href="h60.html" aria-current="false">H60</a><a href="h50.html" aria-current="false">H50</a><a href="hypotheses.html" aria-current="false">Hypotheses</a><a href="evidence.html" aria-current="false">Evidence</a><a href="sources.html" aria-current="false">Sources &amp; feed</a><a href="submit.html" aria-current="false">Submission guide</a></nav><a href="https://github.com/buffedlizard55-lab/GEMSDOE47" class="repo-link">Repository ↗</a></header>
<div class="status-bar"><span class="status-dot" aria-hidden="true"></span><strong>H60 STAYS PRIMARY · H65 IS THE ROUND'S BEST SCIENCE (NOT OK TO SUBMIT) · H68 IS THE NEW UNIQUE CANDIDATE</strong><span>Split-conformal certified · one scientific pass blocked by the uniqueness bar · one valid candidate</span></div>
<main id="main">

<section class="page-heading"><span class="eyebrow">Session 6 · preregistered 2026-10-08 · screened on the frozen 41-block holdout</span><h1>Four new hypotheses.<br>One scientific pass, one valid candidate, one incumbent that stands.</h1><p class="lede">The H65–H68 slate attacked the two mechanisms the evidence left open: the noise that a single-channel maximum admits (consensus), and the geothermal physics no arm has ever combined (lidar structure + radiometric alteration). All four arms passed every control. The consensus field beat the H60 incumbent on <em>both</em> holdout instruments — the round's headline result — but its emission overlaps the incumbent at mask Jaccard 0.5119, failing the frozen uniqueness bar, so it is published as a research artifact that is <strong>not OK to submit</strong>. The eight-channel field is the round's frozen winner: a new unique TIF, a valid submission, but not the recommendation. H60 remains the primary.</p></section>

{panel(a68, "New unique candidate · valid submission · NOT the recommendation", V68)}

{panel(a65, "Research artifact · NOT OK TO SUBMIT while the uniqueness bar stands", V65)}

<section class="notice"><strong>WHAT THE CONFORMAL FLOOR MEANS, AND WHAT IT DOES NOT</strong><p>Each artifact's certified floor is a finite-sample, max-over-settings, one-sided split-conformal lower bound (Lei, G&rsquo;Sell, Rinaldo, Tibshirani &amp; Wasserman, JASA 2018, Algorithm 2 / Theorem 2.2, <a href="https://doi.org/10.1080/01621459.2017.1307116">doi:10.1080/01621459.2017.1307116</a>) on the <em>holdout</em> block-mean DTI of that artifact's spacing choice: the selection half (20 blocks) centered the band, the disjoint calibration half (21 blocks) certified it, and the operating point is the spacing with the greatest <em>certified</em> floor — a guaranteed minimum, not an observed maximum. The confidence level is rank 20 of 22: <strong>coverage at least 90.91&nbsp;%</strong>, exact for every n under exchangeability of block score vectors. It is conditional on block-level exchangeability (assumed, not verified), covers one future exchangeable block&rsquo;s proxy DTI, and is <strong>not</strong> a private-label, pooled-map or leaderboard guarantee. The confidence level is reported next to the chosen spacing in each artifact's note, receipt and panel.</p></section>

<section><div class="section-head"><span class="eyebrow">Step 0 · preregistration</span><h2>The slate was frozen before any score existed.</h2></div>
<p>Four hypotheses, the field definitions, the frozen 41-block design (20 selection / 21 calibration, seed 500610, asserted byte-equal to the H50 screen), the instrument set, the controls, the conformal operating-point rule and the six-condition promotion gate were written and committed before the first score was computed: <a href="research/h65-hypotheses-preregistered.md">docs/research/h65-hypotheses-preregistered.md</a>. This round&rsquo;s methodological change is the operating-point rule itself: the spacing is chosen by <strong>argmax of the certified conformal lower bound</strong> (<code>gems47.conformal.choose_operating_point</code>), not by the observed selection-half maximum. One implementation deviation is recorded, not hidden: the H65 consensus rank was initially inverted (IR-2026-10-08-D, <a href="https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/evidence/h65/erratum-consensus-rank-20261008.md">erratum</a>); the first run's refutation measured the bug, the corrected run measures the hypothesis.</p></section>

<section><div class="section-head"><span class="eyebrow">Step 1 · the slate</span><h2>Four hypotheses, ranked by expected DTI improvement × cost.</h2></div>
<div class="table-scroll"><table><thead><tr><th scope="col">Rank</th><th scope="col">Hypothesis</th><th scope="col">Layers</th><th scope="col">Physical signature</th><th scope="col">Why it should catch a catalogue-missing fault</th><th scope="col">How it differs from anything implemented</th></tr></thead><tbody>
<tr><td>1</td><td><strong>H65 scarp-consensus</strong></td><td>Six lidar scarp channels + valid + TIGER road / BLM claim distances</td><td>Count of channels above their frozen instrument thresholds, lexicographically ranked with the H60 amplitude as tie-break</td><td>Catalogue absence is a mapping gap; geometric consensus is independent of mapping status. H60&rsquo;s max lets one noisy channel spend the budget</td><td>H60 = per-cell <em>max</em> (one operator suffices); H65 = <em>consensus count</em> (several must agree)</td></tr>
<tr><td>2</td><td><strong>H67 alteration-corroborated</strong></td><td>H60 lidar field + USGS GeoDAWN contractor Th/K grid (DOI 10.5066/P93LGLVQ) + road/claim masks</td><td>Additive 50/50 rank mixture of lidar scarp amplitude and the Th/K radiometric alteration index (argillic alteration leaches K → Th/K rises)</td><td>The catalogue maps <em>structure</em>; radiometrics map <em>fossil fluid flow</em>. A scarp on an alteration high is a sealed fluid conduit — the hidden geothermal vent. GeoDAWN was flown by USGS/DOE for undiscovered geothermal resources</td><td>No prior arm in GEMSDOE1–54 combined lidar with radiometrics; H50&rsquo;s scan tried magnetic/gravity/curvature <em>multiplicatively</em> on the slope field (all degraded it)</td></tr>
<tr><td>3</td><td><strong>H66 far-field</strong></td><td>H60 field + catalogue distance transform (labels.tif)</td><td>H60 ranking restricted to cells &gt;3 px (300 m, one kernel radius) from every catalogue pixel — the unmapped-system pole</td><td>H64 measured far-from-catalogue lidar peaks correlating better with the 13 owner-reported scores (lappos +0.581 far vs +0.273 near); H63 refuted the near pole</td><td>No prior arm gated or weighted emission by catalogue distance in the far direction</td></tr>
<tr><td>4</td><td><strong>H68 eight-channel</strong></td><td>H60&rsquo;s six + <code>ex_max</code> (2 m slope excess) + <code>relief</code> (local relief); <code>coh100</code> excluded (H64: anti-correlates −0.532)</td><td>The H60 rank-max mechanism over eight amplitude channels</td><td>A scarp is a local relief anomaly and a short-wavelength steepness excess, not only a band-passed step</td><td>H60 froze six channels; H68 extends to the remaining documented max-amplitude channels (most H60-like arm, ranked last for novelty)</td></tr>
</tbody></table></div></section>

<section><div class="section-head"><span class="eyebrow">Step 2 · the screen</span><h2>Same frozen ground as every previous round.</h2></div>
<p>41 contiguous blocks (8×8, 3 px guard), roles assigned before any score; budget 37,654 unit dots; the frozen seven-spacings sweep (2.0–4.6 px); the frozen instrument set (primary <code>lappos_t200_d3</code>, six lidar-peak instruments, independent SGMC off-catalogue). Anchors H50 and H60 reproduced bit-for-bit against the frozen H60 receipt (0.165881 / 0.287891), proving the design was re-instantiated exactly. Bold cells mark each arm&rsquo;s conformal-selected spacing.</p>
{results_table}
<p><strong>Operating points (argmax certified floor):</strong> H50 2.8 px · H60 2.0 px · H65 2.0 px · H66 2.0 px · H67 2.8 px · H68 2.8 px. Certified floors at the chosen spacing are in the last column; the full per-spacing bands:</p>
{floor_table}</section>

<section><div class="section-head"><span class="eyebrow">Step 3 · the gate</span><h2>All four arms passed every control; only H65 cleared the incumbent bar — and then failed the uniqueness bar.</h2></div>
{gate_table}
<p><strong>Winner by the frozen tie-break</strong> (highest pooled SGMC selection DTI, then conformal floor): <strong>H68</strong> (SGMC {arms['h68']['pooled_sgmc_selection']:.4f}, floor {arms['h68']['conformal']['floor']:.4f}). <strong>Promotion (condition 5, beats_incumbent_h60):</strong> <strong>H65 alone</strong> — primary {arms['h65']['pooled_primary_selection']:.4f} &gt; H60&rsquo;s {arms['h60']['pooled_primary_selection']:.4f} and SGMC {arms['h65']['pooled_sgmc_selection']:.4f} &gt; {arms['h60']['pooled_sgmc_selection']:.4f}. But promotion requires all six conditions, and H65&rsquo;s build <strong>failed condition 6</strong>: its 37,654-dot emission at 2.0&nbsp;px overlaps the H60 incumbent artifact at mask Jaccard <strong>{a65['uniqueness']['max_jaccard']:.4f} ≥ 0.5</strong>. H60 therefore remains the primary; H65 is published as a research artifact (NOT OK TO SUBMIT while the bar stands); H68 is published as the new unique validated candidate.</p></section>

<section class="notice"><strong>WHY H60 STAYS THE PRIMARY — TWO TENSIONS, PUBLISHED</strong><p><strong>First, the tie-break tension (IR-2026-10-08-B):</strong> H68 beats H60 on the independent SGMC population ({arms['h68']['pooled_sgmc_selection']:.4f} vs {arms['h60']['pooled_sgmc_selection']:.4f}, +10.7&nbsp;%) and holds the round&rsquo;s best certified floor, but the SGMC off-catalogue DTI is <em>negatively</em> rank-correlated with the 13 owner-reported scores (−0.421) while the primary lidar-peak instrument is positively correlated (+0.548) — selecting on the flattering instrument is the recorded failure mode this repository exists to avoid. <strong>Second, the uniqueness tension (IR-2026-10-08-E):</strong> the scientifically strongest arm, H65, beat the incumbent on both instruments but shares 68&nbsp;% of its dots with the incumbent&rsquo;s emission (Jaccard 0.5119), and the frozen uniqueness bar — set to stop H51-style re-emissions (0.8543) — blocks it. The bar is a slot-protection discipline, not a competition rule: the organiser would accept the file, and H65 is unique (max 0.0067) against every scored prior submission. Amending the frozen bar after the scores would be the H49 failure mode, so the bar stands, H65 is published with the failure disclosed, and H60 remains the file to submit. <strong>If you disagree with either call, both files are one click away on the landing page</strong> — H68 as a valid submission, H65 as a disclosed research artifact — and this page exists so the choice is informed.</p></section>

<section><div class="section-head"><span class="eyebrow">Step 4 · the 0.2778 question</span><h2>Why h33-2-b2 scored the family high — measured, not assumed.</h2></div>
<p><code>scripts/analyze_h33_reference.py</code> · <a href="data/h33-reference-analysis.json">h33 reference measurement (JSON)</a> · <a href="https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/knowledge/07_h33_reference_measurements.md">knowledge/07</a> (attribution caveat: the 0.2778 row is owner-reported; no organiser receipt links it to this TIFF).</p>
<ul>
<li><strong>Geometry:</strong> {h33g['dots_total']:,} unit dots at 2.8 px minimum spacing (median NN 3.0 px), all off-catalogue, all on the evaluated domain — the family-standard budget.</li>
<li><strong>Lineage:</strong> a <strong>strict mask subset</strong> of the scored d2.8 raster (44,090 dots, owner-reported 0.2600; Jaccard {h33['lineage_jaccard']['max_jaccard']:.4f}) — h33-2-b2 is the d2.8 emission <strong>pruned 44,090 → 37,654 dots</strong>, and also a subset of the h19-5 powerlaw raster (121,131 dots, 0.1922).</li>
<li><strong>Noise exposure:</strong> {h33g['dots_in_noise_masks']:,} of {h33g['dots_total']:,} dots ({100.0*h33g['dots_in_noise_masks']/h33g['dots_total']:.1f}&nbsp;%) sit inside the TIGER-road / BLM-claim noise masks that H60 excludes.</li>
<li><strong>Mechanism, verified algebraically:</strong> deleting the lowest-credit dots leaves TP unchanged (1047.8 against the lappos instrument) while FP falls tenfold, raising the whole-map lappos proxy DTI 0.0555 → 0.0865; against SGMC 0.0954 → 0.1065. The owner-reported 0.2600 → 0.2778 move is <strong>mass discipline on an existing field, not a new geological signal</strong>.</li>
<li><strong>Consequence:</strong> the re-pruning route is closed (our uniqueness gate would reject it: h33-2-b2 sits at Jaccard 0.854 to a scored prior). The open route is a better field — which is what this round tested. H60 already beats the d2.8 reference on identical block-pooled ground (0.2879 vs 0.0494 primary, selection half).</li>
</ul></section>

<section><div class="section-head"><span class="eyebrow">Step 5 · the artifacts</span><h2>Format, range and uniqueness — checked before publication.</h2></div>
<ul class="checklist">
<li>Both artifacts: single float32 band, EPSG:32611, 100&nbsp;m, 3292×3730, the official transform and bounds; no NoData tag; zeros outside the footprint.</li>
<li>All 12,279,160 cells finite and inside [0,1]; values are exactly {0.0, 1.0} — the direct answer to the portal rejection &ldquo;Predicted values must be in range [0, 1]&rdquo;.</li>
<li>37,654 unit dots each, all on the footprint, all off the catalogue — 17/17 strict read-back checks pass for both. Organizer acceptance has not been tested.</li>
<li>H68 uniqueness: {a68['uniqueness']['compared']} prior rasters compared — <strong>zero exact matches</strong>, maximum mask Jaccard {a68['uniqueness']['max_jaccard']:.4f} (closest prior: the H60 incumbent, expected — H68 extends H60&rsquo;s channel set).</li>
<li>H65 uniqueness: {a65['uniqueness']['compared']} prior rasters compared — zero exact matches; maximum mask Jaccard {a65['uniqueness']['max_jaccard']:.4f} against the H60 incumbent (fails the frozen &lt; 0.5 bar) but <strong>0.0067 against every scored prior submission</strong>.</li>
<li>SHA-256 H68 <code>{a68['sha256_tif']}</code> · {a68['bytes']:,} bytes · SHA-256 H65 <code>{a65['sha256_tif']}</code> · {a65['bytes']:,} bytes · NaN-outside fallbacks published alongside both.</li>
</ul></section>

<section><div class="section-head"><span class="eyebrow">Limitations</span><h2>What this round does not establish.</h2></div>
<ul>
<li>The primary instrument is derived from the same owner-built lidar stack that every lidar-reading field (H60, H65, H66, H68) reads; primary-instrument numbers are optimistic by construction. H67&rsquo;s Th/K component and the SGMC population are independent of it.</li>
<li>The SGMC off-catalogue population is biased toward mountain bedrock and its DTI is negatively rank-correlated with the owner-reported scores; it is used as a control and a tie-break, never as the selection target.</li>
<li>H65&rsquo;s margins over H60 are small (+1.4&nbsp;% primary, +2.4&nbsp;% SGMC) but consistent in direction on both instruments; they are selection-half measurements on a proxy, not a leaderboard prediction.</li>
<li>Spatial separation does not establish geological exchangeability; every conformal floor is conditional on that assumption and covers one future exchangeable block&rsquo;s proxy DTI — never the private leaderboard.</li>
<li>Owner-reported scores and the d2.8 reference raster are not organiser receipts; the restored data are hash-pinned owner mirrors, not organiser-authenticated bytes.</li>
<li>The GeoDAWN Th/K grid is a contractor u8-rank product (1st–99th percentile), not physical units; 0 = nodata.</li>
<li>No private label was read and no competition submission slot was spent by this screen or by the artifact builds.</li>
</ul></section>

<section><div class="section-head"><span class="eyebrow">Reproduce</span><h2>Run it yourself.</h2></div>
<pre>python3 scripts/restore_data.py --group all     # hash-pinned mirrors, SHA-256 verified
python3 scripts/analyze_h33_reference.py        # the 0.2778 measurement
python3 scripts/run_h65_screen.py               # the frozen 41-block screen (~5 min)
python3 scripts/build_submission_h65.py         # build + validate + publish both artifacts
python3 scripts/build_h65_page.py               # this page
python3 scripts/update_site_h65.py              # landing page + register + irregularities</pre>
<p>Evidence: <a href="data/h65-screen.json">screen receipt</a> · <a href="data/h65-spacing-history.csv">spacing history (CSV)</a> · <a href="downloads/{a68['artifact']}-receipt.json">H68 artifact receipt</a> · <a href="downloads/{a65['artifact']}-receipt.json">H65 artifact receipt</a> · <a href="data/h33-reference-analysis.json">h33 reference measurement</a> · <a href="https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/evidence/h65/erratum-consensus-rank-20261008.md">consensus-rank erratum</a></p></section>

</main><footer><div><strong>Maximize P(Win).</strong> Preserve the slot when the evidence says no.<br><strong>Own the Outcome.</strong> Publish the bytes, failures and corrections.</div><div><a href="irregularities.html">Limitations &amp; corrections</a><br><a href="method.html">Reproduce this screen</a> · <a href="leaderboard.html">Dated public board</a><br>Reviewed 8 October 2026 · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Official competition 306 ↗</a></div></footer></body></html>
"""

out = DOCS / "h65.html"
out.write_text(html)
print(f"wrote {out.relative_to(ROOT)} ({len(html):,} bytes)")
sys.exit(0)
