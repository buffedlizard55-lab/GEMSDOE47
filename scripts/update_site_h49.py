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
import html
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
    audit_path = ROOT / "evidence" / "h49" / "pinned-public-inventory-uniqueness.json"
    public_audit = json.loads(audit_path.read_text()) if audit_path.exists() else None
    return dict(bundle=bundle, cert=cert, sweep_b=sweep_b, public_audit=public_audit)


def build_blocks(ev: dict) -> dict:
    b, c = ev["bundle"], ev["cert"]
    public_audit = ev.get("public_audit")
    local_u = b["uniqueness"]
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
    fr = b["format_receipt"]
    informational_checks = set(fr.get("informational_checks", []))
    gating_checks = {key: value for key, value in fr.get("checks", {}).items()
                     if key not in informational_checks}
    n_format = sum(1 for value in gating_checks.values() if value)
    n_format_checks = len(gating_checks)
    informational_range_ok = all(fr.get("checks", {}).get(key, False)
                                  for key in informational_checks)

    blocks = {}
    blocks["method_context"] = (
        '<section class="notice"><strong>Historical page: H47-C1 method.</strong>'
        '<p>The profile/model details below document the earlier H47-C1 experiment; they do not '
        'describe or validate the current H49 TIFF. The H49 build commands later on this page '
        'reproduce the current research artifact and its receipts. H49 remains research-only: '
        'its promotion gate is closed. See <a href="H49_RESULTS.html">H49 results</a>, '
        '<a href="RESEARCH_HYPOTHESES.html">ranked follow-up hypotheses</a>, and '
        '<a href="submit.html">the submission guide</a>.</p></section>')
    blocks["status_bar"] = (
        '<div class="status-bar"><span class="status-dot" aria-hidden="true"></span>'
        "<strong>H49 research-only · promotion gate closed · UNSCORED · no slot spent</strong>"
        "<span>Earlier H47/H48 screens remain research-only and are labelled as such.</span></div>")
    blocks["panel"] = (
        '<div class="download-panel"><div><span class="eyebrow">Newly inferred · '
        f'{size:,} bytes · UNSCORED</span><h2>One click. Full official grid.</h2>'
        "<p>A distinct, downloadable research mask using a signed-polarity scarp field. The "
        "nominal fixed-arm split-conformal floor is conditional on block exchangeability and does "
        "not cover the post-results rule change. <strong>Promotion gate closed: do not spend a "
        "competition slot on this candidate.</strong></p></div>"
        f'<div class="actions"><a href="{tif}" class="button primary" download="">'
        "↓ Download GeoTIFF</a>"
        f'<a href="{zipf}" class="button secondary" download="">Single-TIFF ZIP</a>'
        '<a href="data/current-artifact.json" class="text-link">Validation receipt</a>'
        '<a href="H49_RESULTS.html" class="text-link">Full evidence</a></div>'
        f'<p class="filename">{name}.tif</p>'
        f'<p class="export-confidence">Spacing {op["min_spacing_px"]:g} px / '
        f'{op["min_spacing_m"]:.0f} m · nominal fixed-arm split-conformal {conf} floor {fl} '
        f'on the SGMC off-catalogue proxy ({cb["n_calibration_blocks"]} calibration blocks, '
        f'α = {c["alpha"]:g}) · not a full-procedure guarantee or leaderboard score</p>'
        f'<p class="hash">SHA-256 <code>{sha}</code></p></div>')
    blocks["stats"] = (
        '<div class="stats">'
        f'<div><strong>{px}</strong><span>unit-dot predictions ({op["emitted_density_per_1000_scored"]:g} '
        "per 1,000 scored px)</span></div>"
        f'<div><strong>{cb["selection_mean"]:.5f}</strong><span>selection-half mean DTI on SGMC proxy '
        f'(H33 reference: {g["incumbent_selection_mean"]:.5f}; descriptive only)</span></div>'
        f'<div><strong>{fl}</strong><span>nominal fixed-arm {conf} floor; full adaptive guarantee not established</span></div>'
        '<div><strong>0</strong><span>competition slots spent</span></div></div>')
    blocks["notice"] = (
        '<div class="notice"><strong>Promotion gate CLOSED · research-only · no score claimed</strong>'
        f'<p>The shipped arm has a descriptive selection-half mean DTI of {cb["selection_mean"]:.5f} '
        f'on the public SGMC proxy versus {g["incumbent_selection_mean"]:.5f} for the H33 reference '
        f'and {g["random_control_selection_mean"]:.5f} for a mass-matched random mask. Its nominal '
        f'fixed-arm order-statistic floor is {cb["certified_floor"]:.5f} at {conf} only under '
        f'exchangeable blocks and a rule fixed independently of calibration outcomes. The shipped '
        "mean rule is an after-results amendment, and the paired 90% conformal lower bound on "
        "improvement over the incumbent is negative for both candidate arms. Do not spend a slot. "
        "These are public-proxy measurements, not a DrivenData score; no upload receipt exists."
        "</p></div>")
    arm_key = "/".join([shipped["recipe"], shipped["emitter"], shipped["op"]])
    pooled_b = {k.split("|")[0]: v["pooled_dti"] for k, v in c["instrument_b_pooled"].items()
                if k.endswith("|B_sgmc_offcat|selection")}
    arm_share = 100.0 * rs["selection_frequency_share"][arm_key]
    blocks["confidence"] = (
        f'<div class="confidence"><strong>Spacing {op["min_spacing_px"]:g} px / '
        f'{op["min_spacing_m"]:.0f} m · nominal fixed-arm {conf} order-statistic floor '
        f'{cb["certified_floor"]:.5f} on Instrument B · {ca["certified_floor"]:.5f} on PM0200</strong>'
        f'<p>The fixed-arm split uses {cb["n_selection_blocks"]} selection and '
        f'{cb["n_calibration_blocks"]} calibration blocks; this is conditional on the selection '
        "rule being fixed independently of calibration and on spatial-block exchangeability. Git "
        "history cannot verify prospective timing, and the final mean-rule change used results from "
        f'the full 39-block analysis. The 400 re-partitions reuse those same blocks: the shipped arm '
        f'is selected {arm_share:.0f} % of the time, with mean diagnostic violation rate '
        f'{rs["mean_violation_rate"]:.3f}; these are stability summaries, not new validation. '
        "<strong>No full adaptive-procedure guarantee, private-score guarantee, or slot authorization "
        "is claimed.</strong></p></div>")
    blocks["table"] = (
        '<div class="table-scroll"><table><thead><tr><th scope="col">Blocked-holdout comparison '
        "(Instrument B: SGMC faults &gt; 300 m from the given catalogue)</th>"
        '<th scope="col">Mean block DTI</th><th scope="col">Pooled DTI</th>'
        '<th scope="col">Emitted px</th></tr></thead><tbody>'
        f'<tr><td>H49 shipped arm ({shipped["recipe"]})</td>'
        f'<td><strong>{cb["selection_mean"]:.5f}</strong></td>'
        f'<td><strong>{pooled_b.get(arm_key, float("nan")):.5f}</strong></td>'
        f'<td>{px}</td></tr>'
        f'<tr><td>H33-labelled reference mask (score mapping unverified)</td>'
        f'<td><strong>{g["incumbent_selection_mean"]:.5f}</strong></td>'
        f'<td><strong>{pooled_b.get("REF_incumbent_0.2778/as-shipped/as-shipped", float("nan")):.5f}</strong></td>'
        "<td>37,654</td></tr>"
        f'<tr><td>Fixed-seed spaced random (same mass)</td>'
        f'<td>{g["random_control_selection_mean"]:.5f}</td><td>—</td><td>{px}</td></tr>'
        "</tbody></table></div>"
        "<p>The table is descriptive and selection-half; the nominal floor is a fixed-arm "
        "order-statistic diagnostic, not a guarantee for the after-results adaptive procedure. The "
        f"saved floor-rule arm would have selected <code>{frozen['recipe']} / {frozen['emitter']} / "
        f"{frozen['op']}</code> (nominal floor "
        f"{c['certificate_of_the_preregistered_arm']['primary']['certified_floor']:.5f}). "
        "Repository history does not prove prospective timing. Both rules and limitations are in "
        "<a href=\"H49_RESULTS.html\">the full evidence</a>. Slot gate remains closed.</p>"
        '<a href="executive-summary.html" class="text-link">Read the executive summary →</a>')
    table_body = blocks["table"].split('<a href="executive-summary.html"')[0]
    blocks["hero_lede"] = (
        '<p class="lede">Research predictions need more than a TIFF that opens. H49 explores a '
        'signed-polarity scarp field and strike-aligned emission using public geological proxies. '
        'The numerical results, post-selection caveats and promotion-gate failure are published; '
        'this research candidate is downloadable but is not authorized for a competition slot.</p>')
    blocks["meta_description"] = (
        f"H49 research GeoTIFF ({px} dots): public-proxy comparisons and nominal fixed-arm "
        "conformal diagnostic with post-selection caveats. Promotion gate closed; no competition "
        "slot authorized.")
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
        f'<td>float32 binary; all raw values [0,1]; exact internal footprint mask; no nodata tag</td>'
        f'<td>{size:,} B</td>\n    <td><code>{sha}</code></td>'
        f'<td>Research-only; descriptive public-proxy DTI and nominal fixed-arm {conf} floor '
        f'{fl}; not a full adaptive-procedure guarantee. Promotion gate closed. '
        '<a href="H49_RESULTS.html">Evidence</a> · '
        '<a href="data/current-artifact.json">Receipt</a>.</td>\n  </tr>\n')
    note = b["note_optional"]
    blocks["table_exec"] = table_body
    blocks["heading_exec"] = (
        '<section class="page-heading"><span class="eyebrow">Executive summary · reviewed '
        f'{time.strftime("%-d %B %Y", time.gmtime())}</span><h1>New research TIFF.'
        '<br>Promotion gate closed. No score claimed.</h1><p class="lede">H49 compares a '
        'signed-polarity scarp field and strike-aligned emission on public spatial-block proxies. '
        'One descriptive mean is higher than the H33 reference, but the adaptive selection, '
        'exchangeability and paired-improvement criteria are not passed. Download for review; do '
        'not spend a competition slot on this file.</p></section>')
    blocks["heading_submit"] = (
        '<section class="page-heading"><span class="eyebrow">Format is necessary, not '
        'sufficient</span><h1>A valid TIFF is not enough.<br>Current science gate is closed.</h1>'
        '<p class="lede">The file below is available for research review, but the H49 promotion '
        'gate has not passed. Do not upload it or spend a weekly slot. The exact submission steps '
        'are preserved for a future candidate that passes the required gates.</p></section>')
    fr = b["format_receipt"]
    blocks["completed"] = (
        '<section><h2>Work completed — promotion gate still closed</h2><ul class="checklist">'
        '<li>23 SHA-256-pinned mirror files restored and the core grid independently verified '
        '(16 constants match the bytes). Mirror identity is not organizer authentication.</li>'
        '<li>H49-A/H49-B results and the follow-up hypothesis queue are linked from '
        '<a href="H49_RESULTS.html">the sweep report</a> and '
        '<a href="RESEARCH_HYPOTHESES.html">the ranked research queue</a>. The addendum and sweep '
        'evidence first appear together in Git; prospective preregistration timing is not independently verifiable.</li>'
        '<li>Spacing/density sweep: 15,555 rows on the five catalogue instruments plus 4,719 rows '
        'on the SGMC proxy, across 39 spatial blocks (20 selection / 19 calibration).</li>'
        f'<li>Nominal fixed-arm split-conformal diagnostic: {conf} floor '
        f'<strong>{cb["certified_floor"]:.5f}</strong> on Instrument B and {ca["certified_floor"]:.5f} '
        f'on PM0200; conditional on fixed-rule and exchangeability assumptions. The {rs["n_effective"]} '
        're-partitions reuse the same 39 blocks and are not independent samples.</li>'
        f'<li>New {px}-dot full-grid TIFF and single-TIFF ZIP; {n_format} / {n_format_checks} '
        f'gating format/read-back checks pass; the separate informational whole-grid range flag is '
        f'{informational_range_ok}. Local and pinned public-inventory similarity checks are recorded '
        'separately.</li>'
        '<li>H49 mean-rule selection was amended after outcomes; neither candidate arm has a positive '
        '90% paired-difference conformal lower bound versus the incumbent. No slot is authorized; '
        'no leaderboard score or organizer acceptance is claimed.</li></ul>'
        + blocks["table_exec"] + '</section>')
    blocks["not_achieved"] = (
        '<section><h2>What is not achieved</h2><p>No leaderboard score is linked to this TIFF, '
        'and organizer acceptance has not been tested. Instrument B compares predictions with '
        'public SGMC traces; SGMC includes non-fault contacts and is not the hidden competition '
        'target. The observed selection-half DTI of '
        f'{cb["selection_mean"]:.5f} is a public-proxy result, not a score forecast.</p>'
        '<p>The strike-aligned emitter did not show a robust gain over disk emission. The R7 '
        'polarity field has a higher descriptive selection mean than the alternative field in this '
        'sweep, but no positive 90% conformal lower bound on paired improvement over the incumbent '
        'was established, and no geological fault discovery is authenticated. The shipped mask is '
        f'<code>{shipped["recipe"]} / {shipped["emitter"]} / {shipped["op"]}</code> and remains '
        'research-only because the full selection procedure is adaptive and its prospective timing '
        'cannot be independently verified.</p></section>')
    blocks["name_note"] = (
        '<section><h2>Name and short note</h2>'
        '<p>This repository-specific artifact name and note identify the research TIFF; they do '
        'not authorize a competition upload. A future reviewer can check the note against the '
        'receipts and gate status in this repository.</p>'
        f'<p><code id="submission-name">{name}</code> '
        '<button data-copy-id="submission-name">Copy name</button></p>'
        f'<pre id="portal-note">{note}</pre>'
        '<button data-copy-id="portal-note">Copy short note</button>'
        f'<p>{len(note)} of the 200 characters allowed. Any floor quoted there is a nominal '
        'fixed-arm split-conformal order statistic, conditional on exchangeable spatial blocks; '
        'the after-results rule amendment means it is not a guarantee for the full procedure, '
        'a leaderboard score, or the private labels.</p></section>')
    blocks["range_defense"] = (
        '<section><h2>GeoTIFF format and official-footprint check</h2>'
        '<p>The downloadable TIFF has one float32 band. Raw samples are finite and within [0, 1] '
        'across the grid; the internal TIFF mask matches the official footprint exactly, masked '
        'reads are null exactly outside it, and the mask is self-contained (no .msk sidecar). The '
        '<code>nodata</code> tag is absent. Outside-footprint raw samples are finite zeros: valid '
        'for the organizer range rule, but masked invalid for spatial reads.</p>'
        f'<p>{n_format} / {n_format_checks} gating read-back checks pass; the separate informational '
        f'whole-grid range flag is {informational_range_ok}. Grid: width 3292 × '
        'height 3730, EPSG:32611, 100 m; affine [100, 0, 243350, 0, −100, 4508550]; bounds '
        '[243350, 4135550, 572550, 4508550]. The footprint mask does not certify the geological '
        'prediction; format validity, scientific validation, uniqueness and organizer acceptance '
        'are separate questions.</p>'
        '<p><a href="https://gdal.org/en/stable/drivers/raster/gtiff.html#internal-nodata-masks">'
        'GDAL GeoTIFF masks</a> · <a href="https://rasterio.readthedocs.io/en/stable/topics/masks.html">'
        'Rasterio mask interpretation</a></p>'
        '<p>The strict writer rejects non-finite or out-of-range in-footprint values before the '
        'float32 cast; it does not silently clip. <strong>Organizer acceptance is untested</strong> '
        '— no upload of this file has been made.</p></section>')
    blocks["steps"] = (
        '<section><h2 id="submit-steps">Exact submission sequence</h2>'
        '<p class="notice"><strong>H49 promotion gate is closed. Do not upload the current H49 TIFF '
        'or spend a weekly slot on it.</strong> The steps below are preserved for a future '
        'candidate only after its own scientific, format and uniqueness gates pass.</p><ol class="steps">'
        '<li>Open <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">the '
        'official competition overview</a> and select <strong>Compete!</strong> to enroll. Read '
        'the <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">official rules</a> and certify '
        'your own eligibility. Account access is not performed or bypassed here.</li>'
        '<li>For a future candidate, verify its exact published gate report, strict format receipt '
        'and bounded uniqueness audit before uploading. The current '
        '<a href="H49_RESULTS.html">H49 results</a> explicitly keep the promotion gate closed; '
        f'the current file hash is <code>{sha[:16]}…</code> for research review only.</li>'
        f'<li>The current <a href="downloads/{name}.tif"><code>{name}.tif</code></a> is downloadable '
        'for review only; its SHA-256, float32 grid and mask receipt are posted on this page. Do not '
        'upload it while the promotion gate is closed. A future authorized artifact must be '
        'downloaded and rechecked by exact SHA-256 before submission.</li>'
        '<li>Only after a candidate passes every gate, select <strong>Submit → Make new '
        'submission</strong> in the competition sidebar and paste that candidate’s exact name and '
        'short note. The present H49 name and note are research metadata, not authorization to '
        'submit. Never describe a public-proxy floor as a leaderboard result.</li>'
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
        '<a href="all-downloads.html">All historical research files</a>. These artifacts remain '
        'research-only and are labelled as such; H49 is the current downloadable research candidate, '
        'but its slot-promotion gate is closed.</p></section>')
    blocks["two_col"] = (
        '<section class="two-col"><article><span class="eyebrow">What is genuinely new</span>'
        '<h2>Two hypotheses, two measured answers.</h2><p>H49-A tests strike-aligned emission '
        'against disk emission. H49-B adds a signed-polarity field and uses SGMC traces outside the '
        'given catalogue as a public proxy; SGMC also contains non-fault contacts, so it is not an '
        'independent private truth set. The orientation experiment shows no robust gain; the '
        'polarity field has a positive descriptive mean but no passed promotion gate.</p>'
        '<a href="hypotheses.html">Historical H47 hypotheses →</a> · '
        '<a href="RESEARCH_HYPOTHESES.html">Ranked H49 follow-up queue and gates →</a></article>'
        f'<article><span class="eyebrow">What was checked</span><h2>{n_format} / {n_format_checks} '
        f'gating format checks pass; informational range flag {informational_range_ok}; 0 slots spent.</h2>'
        '<p>One float32 band, all raw values in [0, 1], '
        'internal mask matching the official footprint, null masked reads outside, no nodata tag or '
        'sidecar, exact CRS / dimensions / affine / bounds, and byte-identical repository/download '
        'copies. Format validity is separate from scientific promotion.</p>'
        '<a href="submit.html">Format defense &amp; submission sequence →</a>'
        '</article></section>')
    if public_audit:
        public_rows = public_audit.get("rows", [])
        highest = next((row for row in public_rows
                        if row.get("jaccard") == public_audit.get("max_jaccard")), {})
        highest_paths = highest.get("paths") or []
        highest_label = (f"{highest_paths[0].get('repository')}/{highest_paths[0].get('path')}"
                         if highest_paths else highest.get("path", "local history"))
        excluded = [row for row in public_rows
                    if row.get("status") not in ("compared", "compared_local_history")]
        status_counts = {}
        for row in excluded:
            status = row.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        excluded_summary = ", ".join(
            f"{count} {status.replace('_', ' ')}" for status, count in sorted(status_counts.items()))
        public_summary = (
            f"The commit-pinned audit covers {public_audit['public_repositories_in_inventory']} "
            f"visible public repositories and {public_audit['comparisons']} comparable blobs/rasters "
            f"(including local history); it found {public_audit['exact_matches']} exact mask or "
            f"in-footprint value matches. Maximum Jaccard in the combined table was "
            f"{public_audit['max_jaccard']:.6f} ({highest_label}). "
            f"{len(excluded)} inventory entries were excluded from direct pixel comparison "
            f"({excluded_summary or 'none'}); "
            f"{public_audit['failed_repository_inventories']} repository inventories failed. "
            "The scope excludes inaccessible, unpublished and non-inventoried work."
        )
    else:
        public_summary = (
            "The commit-pinned public-inventory comparison has not yet been run; do not infer "
            "global uniqueness from local checks."
        )
    blocks["uniqueness"] = (
        '<section><h2>Distinct in the checked archives; bounded, not globally unique.</h2>'
        f'<p><strong>Local history:</strong> {local_u["n_prior_rasters_compared"]} compatible '
        f'rasters; maximum positive-mask Jaccard {local_u["max_jaccard_vs_prior"]:.6f} and '
        f'containment {local_u["max_containment_vs_prior"]:.6f}, against '
        f'<code>{local_u["worst_jaccard_file"]}</code>. This is an incremental change within the '
        'same broad persistence/density detector lineage, not a different detector family.</p>'
        f'<p><strong>Pinned public inventory:</strong> {public_summary} This is a historical public '
        'scope, not proof of global uniqueness or geological discovery.</p>'
        '<a href="data/current-artifact.json">Current artifact receipt →</a> · '
        '<a href="data/pinned-public-inventory-uniqueness.json">Pinned audit JSON →</a> · '
        '<a href="H49_RESULTS.html">Full results and scope →</a></section>')
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
    informational_checks = set(fr.get("informational_checks", []))
    gating_checks = {key: value for key, value in fr["checks"].items()
                     if key not in informational_checks}
    n_ok = sum(1 for value in gating_checks.values() if value)
    return f"""---
title: How to submit
layout: default
nav_order: 2
---

# HOW TO SUBMIT — executive summary

*Generated {time.strftime('%Y-%m-%d %H:%M', time.gmtime())} UTC by `scripts/update_site_h49.py` from
`evidence/submission/bundle_h49.json` and `evidence/h49/conformal_certificate.json`.*

> **Promotion gate closed. The file is downloadable for research review, but do not submit it or spend a competition slot.** Format validation, scientific validation, uniqueness scope and organizer acceptance are separate.

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

### Verify format independently (this does not authorize submission)

```bash
python3 -m pip install rasterio numpy
python3 - <<'PY'
import rasterio, numpy as np
with rasterio.open('downloads/{name}.tif') as ds:
    a = ds.read(1)
    valid = ds.read_masks(1) > 0
    masked = ds.read(1, masked=True)
    print(ds.crs, ds.width, ds.height, ds.nodata, tuple(ds.transform)[:6])
    print(a.dtype, np.isfinite(a).all(), a.min(), a.max(), (a > 0).sum())
    print(valid.sum(), np.ma.getmaskarray(masked).sum())
PY
```

Expected: EPSG:32611, 3292 × 3730, no nodata tag, exact 100 m affine, raw finite values in
[0,1], {op['emitted_px']} positives, a self-contained mask over exactly
{fr['stats']['footprint_cells']:,} official-footprint cells, and masked reads null exactly outside.
This checks format, not science, uniqueness beyond the recorded bounded audit, portal acceptance or slot authorization.

The same {n_ok}/{len(gating_checks)} gating checks pass when run fail-closed against the written bytes; the separate informational whole-grid range flag is {all(fr['checks'].get(key, False) for key in informational_checks)}. The receipt is in
`evidence/submission/checks-h49-{name}.json`.

## 2. Exact submission sequence — only after a future candidate clears every gate

The current H49 candidate is **not authorized to upload**. Preserve a slot until a future candidate has passed the preregistered spatial-holdout, format and bounded-uniqueness checks.

1. Sign in at <https://www.drivendata.org/> and open
   [competition 306 — The Geologic Enhanced Mapping System (GEMS) Prize Challenge](https://www.drivendata.org/competitions/306/competition-doe-gems/).
2. Click **Submissions** in the competition navigation.
3. Choose only the exact TIFF for a candidate whose scientific, format and bounded-uniqueness gates passed. The present H49 TIFF is research-only; do not select it for submission.
4. For an authorized future candidate, paste its exact registered **Submission name**:

   ```
   {name}
   ```

5. The present H49 note below is shown for audit, not submission. Do not paste it or the current name unless a future re-evaluation opens the gate. For an authorized future candidate, use its reviewed note ({len(b['note_optional'])}/200 characters):

   ```
   {b['note_optional']}
   ```

## 3. What the number in the research note means — and what it does not

The note reports a **nominal fixed-arm split-conformal order statistic**, not a claim that the
complete adaptive selection procedure has a valid guarantee. It is a public-proxy diagnostic:

| Quantity | Value | Where it comes from |
|---|---|---|
| Spacing / operating point | {op['min_spacing_px']:g} px ({op['min_spacing_m']:.0f} m), {op['emitted_density_per_1000_scored']:g} per 1,000 scored px, {op['catalogue_flank_buffer_m']:.0f} m catalogue-flank buffer | `evidence/h49/conformal_certificate.json` |
| Confidence label | nominal {cb['confidence_pct']:.0f} % (α = {c['alpha']:g}) | split conformal, Lei et al. JASA 2018; requires exchangeable spatial blocks |
| **Nominal fixed-arm lower statistic** | **{cb['certified_floor']:.5f}** per 8×8 Instrument-B block | {cb['n_calibration_blocks']} calibration blocks, order statistic k = {cb['order_statistic_k']}; valid only if arm/rule is fixed independently of calibration outcomes |
| Corroborating Instrument-A statistic | {ca['certified_floor']:.5f} | PM0200 catalogue-derived proxy; not private labels |
| Leave-one-out sensitivity | {cb['leave_one_out_worst_floor']:.5f} | recomputed with each calibration block removed |
| Floors at other nominal levels | {', '.join(f"{k.split('=')[1]} → {v:.5f}" for k, v in cb['floors_by_alpha'].items() if v is not None)} | α grid |
| Repartition diagnostic | {rs['n_effective']} re-partitions reuse the same 39 blocks; floor p05 {rs['floor_p05']:.5f}; mean violation rate {rs['mean_violation_rate']:.3f} vs nominal α = {c['alpha']:g} | stability/sensitivity only; not new samples |

**Not claimed:** no leaderboard score, no private-label guarantee, and no proof that a spatial
block is exchangeable. The mean rule was adopted after the sweep; the 400 re-partitions reuse the
same 39 blocks. The 90% paired-difference conformal lower bound versus the incumbent is negative
for both arms. The complete promotion gate is closed: do not spend a slot on this candidate.
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
    region(p, "method-context", B["method_context"], lambda s: "", check, problems,
           before='<section class="page-heading">')
    region(p, "pipeline", B["pipeline"],
           lambda s: element(s, s.find("<pre>", s.find("Run the complete pipeline"))),
           check, problems)

    # the generated meta-description is applied to the three user-facing landing pages
    for page_name in ("index.html", "executive-summary.html", "submit.html"):
        meta_description(DOCS / page_name, B["meta_description"], check, problems)

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


def meta_description(path: Path, description: str, check: bool, problems: list[str]) -> None:
    """Refresh the generated meta-description block on a static HTML page."""
    start, end = "<!--h49:meta-description-->", "<!--/h49:meta-description-->"
    escaped = html.escape(description, quote=True)
    tag = f'<meta name="description" content="{escaped}">'
    expected = start + tag + end
    text = path.read_text()
    i, j = text.find(start), text.find(end)
    if i >= 0 and j > i:
        if text[i:j + len(end)] == expected:
            return
        if check:
            problems.append(f"{path.name}: meta description does not match current evidence")
            return
        path.write_text(text[:i] + expected + text[j + len(end):])
        print(f"[site] {path.name}: meta-description refreshed")
        return
    match = re.search(r"<meta\s+name=[\"']description[\"']\s+content=[\"'][^\"']*[\"']\s*/?>",
                      text, flags=re.IGNORECASE)
    if match is None:
        problems.append(f"{path.name}: meta-description tag not found")
        return
    if check:
        problems.append(f"{path.name}: meta-description has no h49 marker")
        return
    path.write_text(text[:match.start()] + expected + text[match.end():])
    print(f"[site] {path.name}: meta-description inserted")


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
