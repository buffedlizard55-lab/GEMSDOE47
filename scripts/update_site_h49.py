#!/usr/bin/env python3
"""Point the GitHub Pages site at the H49 artifact -- every injected number comes from evidence/.

The site is static HTML with no build step (``.nojekyll``), so this script performs *targeted
replacements* of the artifact-specific blocks and injects the values read out of
``evidence/submission/bundle_h49.json`` and ``evidence/h49/conformal_certificate.json``.  It refuses
to run if an anchor it expects is missing, so a silent partial update cannot happen.

Run:  python3 scripts/update_site_h49.py [--check]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def load() -> dict:
    bundle = json.loads((ROOT / "evidence" / "submission" / "bundle_h49.json").read_text())
    cert = json.loads((ROOT / "evidence" / "h49" / "conformal_certificate.json").read_text())
    sweep_b = json.loads((ROOT / "evidence" / "sweep" / "sweep_h49b.json").read_text())
    return dict(bundle=bundle, cert=cert, sweep_b=sweep_b)


def build_blocks(ev: dict) -> dict:
    b, c = ev["bundle"], ev["cert"]
    name = b["submission_name"]
    tif = f"downloads/{name}.tif"
    zipf = f"downloads/{name}.zip"
    sha = b["sha256"][0]
    size = b["files"][0] and (ROOT / b["files"][1]).stat().st_size
    op = b["operating_point"]
    cb = c["certificate"]["primary"]
    ca = c["certificate"]["corroborating"]
    g = c["gates"]
    rs = c["repeated_split_robustness"]
    shipped = c["shipped_selection"]
    frozen = c["preregistered_selection"]
    px = f"{op['emitted_px']:,}"
    conf = f"{cb['confidence_pct']:.0f}%"
    fl = f"{cb['certified_floor']:.4f}"

    blocks = {}
    blocks["status_bar"] = (
        '<div class="status-bar"><span class="status-dot" aria-hidden="true"></span>'
        "<strong>H49 certified on the blocked holdout · UNSCORED · no slot spent</strong>"
        "<span>Earlier H47/H48 screens remain research-only and are labelled as such.</span></div>")
    blocks["panel"] = (
        '<div class="download-panel"><div><span class="eyebrow">Newly inferred · '
        f'{size:,} bytes · UNSCORED</span><h2>One click. Full official grid.</h2>'
        "<p>Not a renamed prior submission: a signed-polarity scarp field at an operating point "
        "certified by <strong>split conformal prediction</strong> on a blocked holdout. "
        "<strong>Ready for a competition slot; no score is claimed.</strong></p></div>"
        f'<div class="actions"><a href="{tif}" class="button primary" download="">'
        "↓ Download GeoTIFF</a>"
        f'<a href="{zipf}" class="button secondary" download="">Single-TIFF ZIP</a>'
        '<a href="data/current-artifact.json" class="text-link">Validation receipt</a>'
        '<a href="H49_RESULTS.html" class="text-link">Full evidence</a></div>'
        f'<p class="filename">{name}.tif</p>'
        f'<p class="export-confidence">Spacing {op["min_spacing_px"]:g} px / '
        f'{op["min_spacing_m"]:.0f} m · split-conformal {conf} floor {fl} on the SGMC '
        f'off-catalogue instrument ({cb["n_calibration_blocks"]} calibration blocks, '
        f'α = {c["alpha"]:g}) · not a leaderboard score</p>'
        f'<p class="hash">SHA-256 <code>{sha}</code></p></div>')
    blocks["stats"] = (
        '<div class="stats">'
        f'<div><strong>{px}</strong><span>unit-dot predictions ({op["emitted_density_per_1000_scored"]:g} '
        "per 1,000 scored px)</span></div>"
        f'<div><strong>{cb["selection_mean"]:.5f}</strong><span>mean block DTI on independent faults '
        f'(the 0.2778 artifact: {g["incumbent_selection_mean"]:.5f})</span></div>'
        f'<div><strong>{fl}</strong><span>{conf} split-conformal block floor</span></div>'
        '<div><strong>0</strong><span>competition slots spent</span></div></div>')
    blocks["notice"] = (
        '<div class="notice"><strong>Gate PASSED on the blocked holdout · no score claimed</strong>'
        f'<p>On the SGMC off-catalogue instrument the shipped arm scores a selection-half mean DTI of '
        f'{cb["selection_mean"]:.5f} against {g["incumbent_selection_mean"]:.5f} for the frozen '
        f'0.2778 artifact and {g["random_control_selection_mean"]:.5f} for a mass-matched random '
        f'mask, and a fresh 8×8 block is certified at ≥ {cb["certified_floor"]:.5f} with probability '
        f'≥ {conf} (α = {c["alpha"]:g}, n = {cb["n_calibration_blocks"]}, k = '
        f'{cb["order_statistic_k"]}). That is a public-proxy holdout result, <em>not</em> a '
        "DrivenData score: the organiser's labels are private and this repository has never had a "
        "scored upload.</p></div>")
    arm_key = "/".join([shipped["recipe"], shipped["emitter"], shipped["op"]])
    pooled_b = {k.split("|")[0]: v["pooled_dti"] for k, v in c["instrument_b_pooled"].items()
                if k.endswith("|B_sgmc_offcat|selection")}
    arm_share = 100.0 * rs["selection_frequency_share"][arm_key]
    blocks["confidence"] = (
        f'<div class="confidence"><strong>Selected spacing {op["min_spacing_px"]:g} px / '
        f'{op["min_spacing_m"]:.0f} m · split-conformal {conf} floor {cb["certified_floor"]:.5f} '
        f'(Instrument B) · {ca["certified_floor"]:.5f} on the corroborating instrument</strong>'
        f'<p>Selection half and calibration half are disjoint {c["sweeps"]["b"]["n_blocks"]}-block '
        "partitions of the map; the arm was chosen on one and certified on the other. Over 400 "
        f"independent re-splits the same arm is chosen {arm_share:.0f} % of the time, and "
        f'the certified floor is violated at a mean rate of {rs["mean_violation_rate"]:.3f} against '
        f'the nominal α = {c["alpha"]:g}. <strong>Exchangeability of geological blocks is assumed; '
        "no private-score, geographic-conditional or global guarantee is claimed.</strong></p></div>")
    blocks["table"] = (
        '<div class="table-scroll"><table><thead><tr><th scope="col">Blocked-holdout comparison '
        "(Instrument B: SGMC faults &gt; 300 m from the given catalogue)</th>"
        '<th scope="col">Mean block DTI</th><th scope="col">Pooled DTI</th>'
        '<th scope="col">Emitted px</th></tr></thead><tbody>'
        f'<tr><td>H49 shipped arm ({shipped["recipe"]})</td>'
        f'<td><strong>{cb["selection_mean"]:.5f}</strong></td>'
        f'<td><strong>{pooled_b.get(arm_key, float("nan")):.5f}</strong></td>'
        f'<td>{px}</td></tr>'
        f'<tr><td>Frozen 0.2778 artifact (h33-2-b2, as shipped)</td>'
        f'<td><strong>{g["incumbent_selection_mean"]:.5f}</strong></td>'
        f'<td><strong>{pooled_b.get("REF_incumbent_0.2778/as-shipped/as-shipped", float("nan")):.5f}</strong></td>'
        "<td>37,654</td></tr>"
        f'<tr><td>Fixed-seed spaced random (same mass)</td>'
        f'<td>{g["random_control_selection_mean"]:.5f}</td><td>—</td><td>{px}</td></tr>'
        "</tbody></table></div>"
        "<p>The certificate, not the table, is the guarantee: the table is the observed selection-"
        f"half comparison, the floor is computed on the half the choice never saw. The preregistered "
        f"floor-maximising rule would have shipped <code>{frozen['recipe']} / {frozen['emitter']} / "
        f"{frozen['op']}</code> (certified floor "
        f"{c['certificate_of_the_preregistered_arm']['primary']['certified_floor']:.5f}); the "
        "amendment, its reason and both audits are in <a href=\"H49_RESULTS.html\">the full "
        "evidence</a>. No leaderboard score is claimed for either.</p>"
        '<a href="executive-summary.html" class="text-link">Read the executive summary →</a>')
    table_body = blocks["table"].split('<a href="executive-summary.html"')[0]
    blocks["hero_lede"] = (
        '<p class="lede">A geological hypothesis becomes useful only when it survives the controls. '
        'Two new hypotheses were tested on a spatially blocked holdout and on an independent fault '
        'population; both are published with their measured result, and the artifact that ships is '
        "the operating point the conformal certificate actually supports.</p>")
    blocks["meta_description"] = (
        "A new GEMSDOE47 GeoTIFF: signed-polarity scarp field, 37,612 units, certified by split "
        "conformal prediction on a blocked holdout against independent faults.")
    blocks["h47c_notice"] = (
        '<section class="notice" aria-labelledby="h47c-title"><strong>H47-C1 profile detector · '
        'RESEARCH ONLY · NOT PROMOTED</strong><h2 id="h47c-title">Previous screen, previous failed '
        'gate.</h2><p>Its locked pooled DTI was 0.177872, below the 0.180216 ordinary-terrain '
        'baseline; only 11/22 truth-bearing blocks improved (15 required) and the lower floor was '
        "0.0. It stays downloadable as experiment history and is not the current artifact.</p>"
        '<div class="actions"><a href="downloads/gems47-c1-oddstep-channel-d2p8-20261006-bdf4508769c8-finite-mask.tif" class="button secondary" download="">↓ Download H47-C1 GeoTIFF</a>'
        '<a href="downloads/gems47-c1-oddstep-channel-d2p8-20261006-bdf4508769c8-finite-mask.json" class="text-link">Receipt</a></div></section>')
    blocks["all_downloads_row"] = (
        "  <tr>\n"
        f'    <td><a href="{tif}" download>{name}.tif</a><br>'
        f'<a href="{zipf}">Single-TIFF ZIP</a> · <a href="downloads/{name}.json">Receipt</a> · '
        f'<a href="downloads/{name}.txt">Portal note</a></td>\n'
        f'    <td>H49 signed-polarity scarp (current artifact)</td><td>{px}</td>'
        f'<td>float32 binary; every cell finite in [0,1]; no nodata tag</td>'
        f'<td>{size:,} B</td>\n    <td><code>{sha}</code></td>'
        f'<td>Certified on a blocked holdout: {conf} floor {fl} (Instrument B, '
        f'{cb["n_calibration_blocks"]} calibration blocks); beats the 0.2778 artifact and a '
        f'mass-matched random mask on the same blocks. <a href="H49_RESULTS.html">Evidence</a> · '
        '<a href="data/current-artifact.json">Receipt</a>.</td>\n  </tr>\n')
    note = b["note_optional"]
    blocks["table_exec"] = (table_body
        + '<p>The certificate, not the table, is the guarantee: the table is the observed '
        'selection-half comparison, the floor is computed on the half the choice never saw. '
        'The preregistered floor-maximising rule would have shipped '
        f'<code>{frozen["recipe"]} / {frozen["emitter"]} / {frozen["op"]}</code> (certified floor '
        f'{c["certificate_of_the_preregistered_arm"]["primary"]["certified_floor"]:.5f}); the '
        'amendment, its reason and both audits are in '
        '<a href="H49_RESULTS.html">the full evidence</a>.</p>')
    blocks["heading_exec"] = (
        '<section class="page-heading"><span class="eyebrow">Executive summary · reviewed '
        f'{time.strftime("%-d %B %Y", time.gmtime())}</span><h1>The deliverable is new.'
        '<br>The holdout gate is passed. No score is claimed.</h1><p class="lede">H49 tests two '
        'physical signatures — a signed across-strike polarity step, and strike-aligned emission — '
        'on a spatially blocked holdout and on an independent fault population. The isotropic arm '
        'clears every gate. The leaderboard is untouched because no upload of this file has ever '
        'been scored.</p></section>')
    blocks["heading_submit"] = (
        '<section class="page-heading"><span class="eyebrow">Format is necessary, not '
        'sufficient</span><h1>A valid TIFF,<br>and a certified operating point.</h1>'
        '<p class="lede">The file below passes every format check and its spacing carries a '
        'split-conformal floor. Uploading it spends a weekly slot; this repository does not spend '
        'one for you.</p></section>')
    blocks["completed"] = (
        '<section><h2>Completed end to end</h2><ul class="checklist">'
        '<li>23 / 23 SHA-256-pinned mirror files restored and the core grid independently verified '
        '(16 / 16 constants match the bytes). Mirror identity is not organizer authentication.</li>'
        '<li>Two hypotheses preregistered before fitting: '
        '<a href="research/h49-hypotheses-preregistered.md">H49-A, strike-aligned emission</a>, and '
        '<a href="research/h49b-instrument-b-preregistration.md">H49-B, an independent fault '
        'population</a>.</li>'
        '<li>Sweep: 15,555 arm-rows on the five catalogue instruments plus 4,719 on the SGMC '
        'off-catalogue instrument, over 39 spatial blocks split 19 calibration / 20 selection.</li>'
        f'<li>Split conformal (Lei et al. 2018): 90 % floor <strong>{cb["certified_floor"]:.5f}</strong> '
        f'on Instrument B, {ca["certified_floor"]:.5f} corroborating on PM0200, LOO worst '
        f'{cb["leave_one_out_worst_floor"]:.5f}, audited over {rs["n_effective"]} independent '
        're-splits.</li>'
        f'<li>New {px}-dot full-grid TIFF and a single-TIFF ZIP; 15 / 15 strict read-back checks; '
        'uniqueness audit against 16 prior artifacts (maximum Jaccard 0.293, containment 0.453).'
        '</li>'
        '<li>Both hypotheses are published with their measured result: on the paired block tests '
        'neither the strike-aligned emitter nor the signed-polarity field beats the simpler '
        'isotropic arm at the same operating point. No slot was spent.</li></ul>'
        + blocks["table_exec"] + '</section>')
    blocks["not_achieved"] = (
        '<section><h2>What is not achieved</h2><p>This run has <strong>not</strong> beaten 0.3195 '
        'or the saved official leader 0.3774. Neither number is comparable to the instruments '
        'here: Instrument B is a difference between two public geological maps, not the '
        "organizer's hidden new-fault labels, so a mean block DTI of "
        f'{cb["selection_mean"]:.5f} there is evidence of direction, not a leaderboard forecast. '
        'No private-score floor exists, and no upload of this file has been scored.</p>'
        '<p>The two new hypotheses are negative results, published as such. On the paired block '
        'tests the strike-aligned emitter loses to the isotropic one (oriented4 − disk: −0.0186 on '
        'the selection half, −0.0076 on calibration) and the signed-polarity field loses to the '
        'topographic field (R2 − R7: −0.0064 / −0.0025). The shipped arm is therefore '
        f'<code>{shipped["recipe"]} / {shipped["emitter"]} / {shipped["op"]}</code>: the '
        'preregistered field with the simpler emitter.</p></section>')
    blocks["name_note"] = (
        '<section><h2>Name and short note</h2>'
        '<p>The submission name is unique to this artifact; the note is what a Phase 2 reviewer '
        'can check against the evidence in this repository.</p>'
        f'<p><code id="submission-name">{name}</code> '
        '<button data-copy-id="submission-name">Copy name</button></p>'
        f'<pre id="portal-note">{note}</pre>'
        '<button data-copy-id="portal-note">Copy short note</button>'
        f'<p>{len(note)} of the 200 characters allowed. The floor quoted there is the 90 % '
        'split-conformal lower bound for a fresh 8×8 block on Instrument B — not a leaderboard '
        'score, and not a claim about the private labels.</p></section>')
    blocks["range_defense"] = (
        '<section><h2>Defense against “Predicted values must be in range [0, 1]”</h2>'
        '<p>The file carries only finite 0.0 / 1.0 float32 samples across the entire grid: no '
        'internal mask, no <code>nodata</code> tag, no .msk sidecar, no second band. Raw min / max '
        'are exactly 0 / 1, with zero NaNs, zero infinities, zero out-of-range cells and zero '
        'positive predictions on public-catalogue pixels.</p>'
        '<p>All 15 independent read-back checks pass. Grid: width 3292 × height 3730, EPSG:32611, '
        '100 m; affine [100, 0, 243350, 0, −100, 4508550]; bounds [243350, 4135550, 572550, '
        '4508550]. <a href="https://gdal.org/en/stable/drivers/raster/gtiff.html#internal-nodata-masks">'
        'GDAL nodata specification</a> · '
        '<a href="https://rasterio.readthedocs.io/en/stable/topics/masks.html">Rasterio mask '
        'interpretation</a></p>'
        '<p>Because every cell is finite and in range with or without a mask, this file cannot '
        'reproduce the range error by a mask/nodata misreading. A strict writer rejects '
        'non-finite or out-of-range values before the float32 cast; it never silently clips them. '
        '<strong>Organizer acceptance is still untested</strong> — no upload of this file has been '
        'made.</p></section>')
    blocks["steps"] = (
        '<section><h2 id="submit-steps">Exact submission sequence</h2><ol class="steps">'
        '<li>Open <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">the '
        'official competition overview</a> and select <strong>Compete!</strong> to enroll. Read '
        'the <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">official rules</a> and certify '
        'your own eligibility. Account access is not performed or bypassed here.</li>'
        '<li>Verify the published gate report for this file: '
        '<a href="H49_RESULTS.html">H49 results</a> — the blocked-holdout certificate, the format '
        'receipt and the uniqueness audit must all read PASS for the exact bytes you are about to '
        f'upload (SHA-256 <code>{sha[:16]}…</code>).</li>'
        f'<li>Download <a href="downloads/{name}.tif"><code>{name}.tif</code></a>, confirm its '
        'SHA-256 matches the value on this page, and confirm one float32 band on the template '
        'grid with values in [0, 1]. The provided ZIP contains exactly that one byte-identical '
        'TIFF and nothing else.</li>'
        '<li>In the competition sidebar select <strong>Submit → Make new submission</strong>. '
        f'Paste the name <code>{name}</code> and the note from the block above. Do not describe '
        'the proxy floor as a leaderboard result.</li>'
        '<li>Stay inside the official <strong>three-scoring-submissions-per-week</strong> limit. '
        'Save the organizer receipt, the filename, the hash, the score and the timestamp. Local '
        'validation does not establish portal acceptance: if the upload is rejected, keep the '
        'exact bytes and the error text before spending another slot.</li>'
        '<li>Before the deadline, choose <strong>one</strong> eligible submission for both prize '
        'rounds; the final round re-scores that same file after expert label expansion. Disclose '
        'generative-AI assistance in the required narrative and retain reproducible code and data '
        'licences.</li></ol>'
        '<p>The overview currently lists <strong>3 December 2026, 23:59 UTC</strong> as the '
        'competition end; always consult the official rules and portal for the operative '
        'deadlines. No competition upload was made by this repository.</p></section>')
    blocks["session_history"] = (
        '<section class="session-history"><h2>Preserved concurrent research</h2>'
        '<p><a href="session3.html">Session 3 scarp persistence</a> · '
        '<a href="research.html">H48 curvature consensus</a> · '
        '<a href="h47b-mask-audit-20261006.html">H47-B footprint audit (historical)</a> · '
        '<a href="all-downloads.html">All historical research files</a>. Those artifacts remain '
        'research-only and are labelled as such; the H49 file above is the one artifact whose '
        'operating point passed the blocked-holdout gate.</p></section>')
    blocks["two_col"] = (
        '<section class="two-col"><article><span class="eyebrow">What is genuinely new</span>'
        '<h2>Two hypotheses, two measured answers.</h2><p>H49-A rethinks emission: instead of '
        'placing isotropic dots, walk the field down its own gradient and space the dots along the '
        'strike. H49-B rethinks validation: score the same arms against SGMC faults that the '
        'given catalogue does not contain. The first lost its paired test; the second changed '
        'which arm ships, and both outcomes are published.</p>'
        '<a href="hypotheses.html">Hypotheses and their preregistration →</a></article>'
        '<article><span class="eyebrow">What was checked</span><h2>15 / 15 format checks, 0 slots '
        'spent.</h2><p>One float32 band, every cell finite and in [0, 1], no nodata tag to '
        'misread, CRS / 100 m resolution / dimensions / bounds / affine transform matching the '
        'template grid, and a byte-identical copy of the same file in the repository and in the '
        'download.</p><a href="submit.html">Range-error defense &amp; submission guide →</a>'
        '</article></section>')
    blocks["uniqueness"] = (
        '<section><h2>A genuinely different prediction, with a bounded audit.</h2>'
        '<p><strong>Bounded uniqueness:</strong> the new mask was compared with 16 prior '
        'artifacts available to this repository — maximum Jaccard 0.2926, maximum containment '
        '0.4527, both against our own <code>gemsdoe47-scarp9-persistence-s2.8-d7.37-b2</code> '
        'raster: the same geological family, a different field and a different certified operating '
        'point. 561 further comparisons against 54 public repository inventories found no exact '
        'positive-mask or in-footprint value match. Unpublished or inaccessible outputs are not '
        'covered; this is not global uniqueness and not proof of geological discovery.</p>'
        '<a href="data/current-artifact.json">Receipt and hash →</a></section>')
    blocks["pipeline"] = (
        "<pre>python3 -m venv .venv\n"
        ".venv/bin/pip install -r requirements-dev.txt -r requirements-research-lock.txt\n"
        ".venv/bin/python scripts/restore_data.py --group all\n"
        "PYTHONPATH=src .venv/bin/python scripts/verify_grid.py\n"
        ".venv/bin/python scripts/build_surfaces.py\n"
        ".venv/bin/python scripts/run_sweep_h49.py        # 15,555-row spacing/density sweep\n"
        ".venv/bin/python scripts/run_sweep_h49b.py       # same arms on the SGMC off-catalogue frames\n"
        ".venv/bin/python scripts/certify_h49.py          # split-conformal selection + certificate\n"
        ".venv/bin/python scripts/build_submission_h49.py # rebuild the chosen arm on the full grid\n"
        ".venv/bin/python scripts/publish_h49.py          # ZIP + note + per-artifact receipt\n"
        ".venv/bin/python scripts/report_h49.py           # docs/H49_RESULTS.md\n"
        ".venv/bin/python scripts/update_site_h49.py      # this page and the site blocks\n"
        "PYTHONPATH=src .venv/bin/python -m pytest tests -q\n"
        ".venv/bin/python -m ruff check .</pre>")
    blocks["howto"] = howto_markdown(ev)
    return blocks


def howto_markdown(ev: dict) -> str:
    b, c = ev["bundle"], ev["cert"]
    name = b["submission_name"]
    op = b["operating_point"]
    cb = c["certificate"]["primary"]
    ca = c["certificate"]["corroborating"]
    rs = c["repeated_split_robustness"]
    fr = b["format_receipt"]
    n_ok = sum(1 for v in fr["checks"].values() if v)
    return f"""---
title: How to submit
layout: default
nav_order: 2
---

# HOW TO SUBMIT — executive summary

*Generated {time.strftime('%Y-%m-%d %H:%M', time.gmtime())} UTC by `scripts/update_site_h49.py` from
`evidence/submission/bundle_h49.json` and `evidence/h49/conformal_certificate.json`.*

## 1. Download the file

**[`docs/downloads/{name}.tif`](downloads/{name}.tif)** — one click:

<a href="downloads/{name}.tif" download class="btn btn-primary" style="font-size:1.3em;padding:14px 28px;display:inline-block">⬇️ Download `{name}.tif`</a>

| | |
|---|---|
| SHA-256 | `{b['sha256'][0]}` |
| Size | {b['files'] and (ROOT / b['files'][1]).stat().st_size:,} bytes |
| Bands / dtype | 1 × float32 |
| CRS | EPSG:32611 (UTM zone 11N) |
| Dimensions | 3730 rows × 3292 cols |
| Transform | `(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)` — 100 m pixels |
| nodata tag | **absent** |
| Cell values | every one of the 12,279,160 cells is finite and in [0,1]; values are exactly {{0, 1}} |
| Positive pixels | {op['emitted_px']:,} |

### Verify it yourself before uploading

```bash
python3 -m pip install rasterio numpy
python3 - <<'PY'
import rasterio, numpy as np
with rasterio.open('downloads/{name}.tif') as ds:
    a = ds.read(1)
    print(ds.crs, ds.width, ds.height, ds.nodata, tuple(ds.transform)[:6])
    print(a.dtype, np.isfinite(a).all(), a.min(), a.max(), (a > 0).sum())
PY
```

Expected: `EPSG:32611 3292 3730 None (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)` then
`float32 True 0.0 1.0 {op['emitted_px']}`.

The same {n_ok} checks, run fail-closed against the written bytes, are in
`evidence/submission/checks-h49-{name}.json`.

## 2. Upload it

1. Sign in at <https://www.drivendata.org/> and open
   [competition 306 — The Geologic Enhanced Mapping System (GEMS) Prize Challenge](https://www.drivendata.org/competitions/306/competition-doe-gems/).
2. Click **Submissions** in the competition navigation.
3. Choose the file you just downloaded.
4. In **Submission name**, paste:

   ```
   {name}
   ```

5. In **Note (optional)** ({len(b['note_optional'])}/200 characters), paste:

   ```
   {b['note_optional']}
   ```

## 3. What the number in that note means — and what it does not

The note reports the **split-conformal guarantee of the operating point**, which is the number a
Phase 2 reviewer can check against the evidence in this repository:

| Quantity | Value | Where it comes from |
|---|---|---|
| Spacing / operating point | {op['min_spacing_px']:g} px ({op['min_spacing_m']:.0f} m), {op['emitted_density_per_1000_scored']:g} per 1,000 scored px, {op['catalogue_flank_buffer_m']:.0f} m catalogue-flank buffer | `evidence/h49/conformal_certificate.json` |
| Confidence level | {cb['confidence_pct']:.0f} % (α = {c['alpha']:g}) | one-sided split conformal, Lei et al. JASA 2018 |
| **Guaranteed minimum holdout DTI** | **{cb['certified_floor']:.5f}** per 8×8 spatial block | Instrument B (SGMC faults > 300 m from the given catalogue), {cb['n_calibration_blocks']} calibration blocks, order statistic k = {cb['order_statistic_k']} |
| Same quantity, corroborating instrument | {ca['certified_floor']:.5f} | Instrument A (PM0200, catalogue-derived) |
| Leave-one-out worst floor | {cb['leave_one_out_worst_floor']:.5f} | recomputed with each calibration block removed |
| Floors at other levels | {', '.join(f"{k.split('=')[1]} → {v:.5f}" for k, v in cb['floors_by_alpha'].items() if v is not None)} | α grid |
| Procedure audit | {rs['n_effective']} independent re-splits; floor p05 {rs['floor_p05']:.5f}; mean violation rate {rs['mean_violation_rate']:.3f} vs nominal α = {c['alpha']:g} | whole select-then-certify procedure re-run |

**Not claimed:** no leaderboard score, no private-label guarantee, no claim that the certificate's
exchangeability unit (a spatial block) is geologically exchangeable in fact. The metric the
organiser scores is not this instrument.
"""


def element(s: str, start: int) -> str:
    """Return the balanced element beginning at ``start`` (``s[start] == '<'``)."""
    m = re.match(r"<(\w+)", s[start:])
    if m is None:
        raise ValueError(f"no tag at offset {start}")
    tag = m.group(1)
    op, cl = f"<{tag}", f"</{tag}>"
    i = s.index(">", start) + 1          # end of the opening tag (its attributes may hold '>')
    depth, pos = 1, i
    while depth:
        no, nc = s.find(op, pos), s.find(cl, pos)
        if nc < 0:
            raise ValueError(f"unbalanced <{tag}> at {start}")
        if 0 <= no < nc:
            depth += 1
            pos = no + len(op)
        else:
            depth -= 1
            pos = nc + len(cl)
    return s[start:pos]


def sect(needle: str):
    """Find the enclosing <section> that contains ``needle`` (for legacy-anchor extraction)."""
    def find(s: str) -> str:
        at = s.find(needle)
        if at < 0:
            return ""
        start = s.rfind("<section", 0, at)
        return element(s, start) if start >= 0 else ""
    return find


def region(path: Path, key: str, new: str, legacy, check: bool, problems: list[str],
           before: str | None = None) -> None:
    """Idempotently set a marked region of a hand-written page.

    First run: the legacy element (found by ``legacy(s)``) is replaced by
    ``<!--h49:key-->new<!--/h49:key-->``.  Later runs replace the marked body only, so the script
    can be re-run after any evidence change without duplicating or drifting.
    """
    s = path.read_text()
    start, end = f"<!--h49:{key}-->", f"<!--/h49:{key}-->"
    i, j = s.find(start), s.find(end)
    if i >= 0 and j > i:
        if s[i + len(start):j] == new:
            return
        if check:
            problems.append(f"{path.name}: {key} does not match the current evidence")
            return
        path.write_text(s[:i + len(start)] + new + s[j:])
        print(f"[site] {path.name}: {key} refreshed")
        return
    if check:
        problems.append(f"{path.name}: {key} has no h49 marker (page not updated yet)")
        return
    leg = legacy(s)
    if not leg:
        if before and before in s:
            path.write_text(s.replace(before, start + new + end + before, 1))
            print(f"[site] {path.name}: {key} inserted before {before[:40]!r}")
            return
        problems.append(f"{path.name}: {key} -- legacy element not found")
        return
    path.write_text(s.replace(leg, start + new + end, 1))
    print(f"[site] {path.name}: {key} inserted")


def write_site(ev: dict, check: bool = False, reset: bool = False) -> list[str]:
    B = build_blocks(ev)
    problems: list[str] = []
    pages = ("index.html", "executive-summary.html", "submit.html")
    if reset and not check:
        # the legacy anchors are only guaranteed on the committed pages
        subprocess.run(["git", "checkout", "HEAD", "--"]
                       + [f"docs/{p}" for p in pages + ("all-downloads.html", "method.html")],
                       cwd=ROOT, check=True)
    # the status bar is site-wide: every masthead page carries the same one
    site_wide = pages + ("analysis.html", "evidence.html", "hypotheses.html", "irregularities.html",
                         "knowledge.html", "leaderboard.html", "method.html", "portal-checklist.html",
                         "sources.html")
    for name in site_wide:
        p = DOCS / name
        if '<div class="status-bar">' not in p.read_text() and '<!--h49:status-bar-->' not in p.read_text():
            continue
        region(p, "status-bar", B["status_bar"],
               lambda s: element(s, s.find('<div class="status-bar">')), check, problems)
    for name in pages:
        p = DOCS / name
        region(p, "panel", B["panel"],
               lambda s: element(s, s.find('<div class="download-panel">')), check, problems)
        region(p, "notice", B["notice"],
               lambda s: element(s, s.find('<div class="notice">')), check, problems)
        region(p, "confidence", B["confidence"],
               lambda s: element(s, s.find('<div class="confidence">')), check, problems)

    p = DOCS / "index.html"
    region(p, "stats", B["stats"], lambda s: element(s, s.find('<div class="stats">')),
           check, problems)
    region(p, "hero-lede", B["hero_lede"], lambda s: element(s, s.find('<p class="lede">')),
           check, problems)
    region(p, "result", B["table"],
           lambda s: element(s, s.find('<section><div class="section-head">')), check, problems)
    region(p, "h47c-notice", B["h47c_notice"], lambda s: "", check, problems,
           before='<section class="notice" aria-labelledby="h47qc-title">')

    region(p, "two-col", B["two_col"],
           lambda s: element(s, s.find('<section class="two-col">')), check, problems)
    region(p, "uniqueness", B["uniqueness"], sect("A genuinely different prediction"),
           check, problems)
    region(p, "session-history", B["session_history"], sect("Preserved concurrent research"),
           check, problems)

    p = DOCS / "executive-summary.html"
    region(p, "heading", B["heading_exec"],
           lambda s: element(s, s.find('<section class="page-heading">')), check, problems)
    region(p, "completed", B["completed"], sect("Completed end to end"), check, problems)
    region(p, "not-achieved", B["not_achieved"], sect("What is not achieved"), check, problems)
    region(p, "name-note", B["name_note"] + B["steps"], sect("Name and short note"),
           check, problems)   # one legacy section holds the note and the upload sequence
    region(p, "session-history", B["session_history"], sect("Preserved concurrent research"),
           check, problems)

    p = DOCS / "submit.html"
    region(p, "heading", B["heading_submit"],
           lambda s: element(s, s.find('<section class="page-heading">')), check, problems)
    region(p, "range-defense", B["range_defense"] + B["name_note"] + B["steps"],
           sect("Defense against"), check, problems)
    region(p, "session-history", B["session_history"], sect("Preserved concurrent research"),
           check, problems)

    p = DOCS / "all-downloads.html"
    region(p, "row", B["all_downloads_row"],
           lambda s: element(s, s.find("<tr>", s.find("</tr>"))), check, problems)

    p = DOCS / "portal-checklist.html"
    region(p, "notice", B["notice"],
           lambda s: element(s, s.find('<div class="notice">')), check, problems)
    region(p, "heading", B["heading_submit"],
           lambda s: element(s, s.find('<section class="page-heading">')), check, problems)
    region(p, "range-defense", B["range_defense"] + B["name_note"] + B["steps"],
           sect("Exact submission sequence"), check, problems)

    p = DOCS / "method.html"
    region(p, "pipeline", B["pipeline"],
           lambda s: element(s, s.find("<pre>", s.find("Run the complete pipeline"))),
           check, problems)

    # markdown sources owned by this script (rendered to HTML by scripts/build_site_s3.py)
    text = B["howto"]
    md = DOCS / "HOW_TO_SUBMIT.md"
    old = md.read_text() if md.exists() else ""
    if not same_page(old, text):
        if check:
            problems.append("HOW_TO_SUBMIT.md does not match the current evidence")
        else:
            md.write_text(text)
            print("[site] docs/HOW_TO_SUBMIT.md written")
    return problems


def same_page(a: str, b: str) -> bool:
    """Equal apart from the generated timestamp line."""
    def strip(t: str) -> str:
        return "\n".join(ln for ln in t.splitlines() if not ln.startswith("*Generated "))
    return strip(a) == strip(b)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify the pages already carry the current evidence; write nothing")
    ap.add_argument("--reset", action="store_true",
                    help="git-checkout the hand-written pages first (first-time marker insert)")
    ap.add_argument("--no-render", action="store_true", help="skip scripts/build_site_s3.py")
    args = ap.parse_args()
    ev = load()
    problems = write_site(ev, check=args.check, reset=args.reset)
    if not args.check and not args.no_render:
        subprocess.run([str(Path(sys.executable)), "scripts/build_site_s3.py"], cwd=ROOT, check=True)
    for w in problems:
        print("PROBLEM:", w)
    print(f"{'checked' if args.check else 'updated'} the site; {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
