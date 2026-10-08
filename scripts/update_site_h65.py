#!/usr/bin/env python3
"""Publish the H65-round artifacts on the site, honestly labelled.

Run after ``scripts/build_submission_h65.py``.  Every replacement asserts that it
actually changed the file (and is idempotent on re-runs), so a silent miss fails the
run instead of publishing a page that still points at the previous state.

Labelling (frozen in docs/research/h65-hypotheses-preregistered.md, six conditions):

* **H60 stays PRIMARY · OK TO DOWNLOAD AND SUBMIT.**  No arm displaced it under all
  six frozen conditions: H65 beat it on both holdout instruments (conditions 1-5) but
  its emission overlaps the H60 artifact at mask Jaccard 0.5119 >= 0.5, failing
  condition 6 (bounded uniqueness).
* **H65 is the round's headline scientific result** — published as a research
  artifact, NOT OK TO SUBMIT while the frozen uniqueness bar stands (it is unique,
  max Jaccard 0.0067, against every scored prior submission; the overlap is only with
  the unsubmitted incumbent it would supersede).
* **H68 is the new unique TIF** — the frozen winner by the SGMC tie-break, passing
  control conditions 1-4 and the uniqueness bar (0.3066): a valid submission, OK to
  download, but NOT the recommendation while H60 stands.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

a65 = json.loads((DOCS / "data" / "h65-artifact.json").read_text())
a68 = json.loads((DOCS / "data" / "h68-artifact.json").read_text())
screen = json.loads((DOCS / "data" / "h65-screen.json").read_text())

S65, S68 = a65["artifact"], a68["artifact"]
T65, T68 = f"{S65}-allfinite.tif", f"{S68}-allfinite.tif"
SHA65, SHA68 = a65["sha256_tif"], a68["sha256_tif"]
B65, B68 = a65["bytes"], a68["bytes"]
SP65, SP68 = a65["spacing_px"], a68["spacing_px"]
F65 = a65["conformal"]["certified_floor_dti"]
F68 = a68["conformal"]["certified_floor_dti"]
COV = a65["conformal"]["coverage_at_least"]
RANK = a65["conformal"]["rank_1_based"]
N_CAL = a65["conformal"]["calibration_blocks"]
NOTE68 = a68["submission_note_field"]
P65 = a65["holdout"]["candidate_pooled_dti"]
SG65 = a65["holdout"]["candidate_sgmc_pooled_dti"]
P68 = a68["holdout"]["candidate_pooled_dti"]
SG68 = a68["holdout"]["candidate_sgmc_pooled_dti"]
H60P = a65["holdout"]["h60_incumbent_pooled_dti"]
H60S = a65["holdout"]["h60_incumbent_sgmc_pooled_dti"]
H50P = a65["holdout"]["h50_anchor_pooled_dti"]
J65 = a65["uniqueness"]["max_jaccard"]
J68 = a68["uniqueness"]["max_jaccard"]
N65 = a65["uniqueness"]["compared"]
N68 = a68["uniqueness"]["compared"]
SUBNAME68 = "GEMSDOE47-H68-lidar8ch-s2p8-20261008"


def apply(path: Path, pairs: list[tuple[str, str]], count: int = 1) -> None:
    """One-shot asserted replacement, idempotent on re-runs."""
    text = path.read_text()
    changed = False
    for old, new in pairs:
        if text.count(new) >= count:
            continue  # already applied
        found = text.count(old)
        if found < count:
            raise SystemExit(f"{path.name}: expected >= {count} match(es) for {old[:70]!r}, "
                             f"found {found}")
        text = text.replace(old, new)
        changed = True
    if changed:
        path.write_text(text)
    print(f"updated {path.relative_to(ROOT)}")


# ---------------------------------------------------------------- status bar
OLD_STATUS = ('<strong>NEW SUBMISSION READY · OK TO DOWNLOAD AND SUBMIT</strong>'
              '<span>H60 · 37,654 dots · 200 m · split-conformal 91% · one click below. '
              'H50 is a valid fallback; research-only H47-C1 / H47-QC / H49 artifacts are '
              'NOT for submission.</span>')
NEW_STATUS = ('<strong>NEW SUBMISSION READY · OK TO DOWNLOAD AND SUBMIT</strong>'
              '<span>H60 · 37,654 dots · 200 m · split-conformal 91% · one click below. '
              'New this session: the unique H68 candidate (valid submission, not the '
              'recommendation) one click further down, and the H65 consensus result '
              '(beats H60 on both holdout instruments, NOT OK to submit — uniqueness '
              'bar) in the notices. H50 is a valid fallback; research-only H47-C1 / '
              'H47-QC / H49 artifacts are NOT for submission.</span>')

# ---------------------------------------------------------------- H68 panel
PANEL_ANCHOR = ('<p class="export-confidence"><strong>Note for the DrivenData form\'s '
                'optional Note field:</strong> <code>h60 lidar-scarp d2p0 conformal90'
                '</code></p></div>')
H68_PANEL = (PANEL_ANCHOR +
             f'<div class="download-panel" id="h68-download"><div>'
             f'<span class="eyebrow">New unique candidate · generated 2026-10-08 · '
             f'preregistered gate passed · NOT THE RECOMMENDATION WHILE H60 STANDS · '
             f'{B68:,} bytes</span>'
             '<h2>New this session: the H68 eight-channel lidar field — a unique TIF, '
             'not a copy of any prior submission.</h2>'
             '<p>A genuinely new field: the per-cell maximum of the ranks of '
             '<em>eight</em> scarp channels of the owner-derived 1&nbsp;m lidar stack '
             '(H60&rsquo;s six plus slope-excess <code>ex_max</code> and local relief '
             '<code>relief</code>), masked against roads and mine claims. Emitted as '
             f'{a68["budget"]:,} unit dots at {SP68:g}&nbsp;px ({SP68*100:g}&nbsp;m) over '
             'the noise-masked off-catalogue domain (1,610,706 cells). '
             '<strong>Values are 0/1 only, float32, single band, EPSG:32611, 100&nbsp;m, '
             'all finite, no NoData tag.</strong> It passed the preregistered '
             'four-condition gate: it beats the H50 anchor by +68&nbsp;%, it carries a '
             'certified split-conformal floor of 0.0993 DTI at &ge;90.91&nbsp;% coverage, '
             'and it beats the mass-matched random control on both the primary and the '
             'independent SGMC instruments.</p></div>'
             f'<div class="actions"><a href="downloads/{T68}" class="button primary" '
             'download="">↓ Download the new H68 GeoTIFF</a>'
             f'<a href="downloads/{S68}.zip" class="button secondary" download="">ZIP + '
             f'note + receipt</a><a href="h65.html" class="button secondary">Why it '
             f'should work</a><a href="downloads/{S68}-note.txt" class="text-link">'
             'Submission note (copy-paste)</a></div>'
             f'<p class="filename">{T68}</p>'
             f'<p class="export-confidence">Spacing {SP68:g} px / {SP68*100:g} m · '
             'selected by split conformal prediction (Lei, G&rsquo;Sell, Rinaldo, '
             'Tibshirani &amp; Wasserman, JASA 2018, Algorithm 2) as the spacing with the '
             f'greatest CERTIFIED lower bound · max-residual rank {RANK} of {N_CAL + 1} · '
             f'finite-sample coverage at least {COV:.2%} (confidence level {COV:.2%}) · '
             f'certified holdout floor {F68:.4f} DTI · conditional on block '
             'exchangeability</p>'
             f'<p class="hash">SHA-256 <code>{SHA68}</code></p>'
             '<p class="export-confidence"><strong>Note for the DrivenData form\'s optional '
             f'Note field:</strong> <code>{NOTE68}</code></p>'
             '<p class="export-confidence"><strong>OK to download: YES · valid submission · '
             'recommended for submission: NO — H60 above remains the file to submit.</strong> '
             f'H68 beat every control and the H50 anchor ({P68:.4f} vs {H50P:.4f} primary), '
             f'and it beats the H60 incumbent on the independent SGMC off-catalogue '
             f'population ({SG68:.4f} vs {H60S:.4f}) — the round&rsquo;s best — but it does '
             f'<em>not</em> beat H60 on the primary lidar-peak instrument ({P68:.4f} vs '
             f'{H60P:.4f}), the instrument whose DTI is positively rank-correlated with the '
             'owner-reported leaderboard scores, so the frozen promotion rule keeps H60 as '
             f'the primary. Uniqueness: {N68} prior rasters compared, zero exact matches, '
             f'maximum mask Jaccard {J68:.4f}. Submit H68 only if you accept that trade-off; '
             'the full comparison is on <a href="h65.html">the H65–H68 evidence page</a>.</p></div>')

# ---------------------------------------------------------------- H65 notice
H50_NOTICE_ANCHOR = '<section class="notice"><strong>H50 · VALID FALLBACK · superseded by H60</strong>'
H65_NOTICE = (
    '<section class="notice" id="h65-review"><strong>H65 · NEW SCIENTIFIC RESULT · NOT OK '
    'TO SUBMIT while the uniqueness bar stands · research artifact retained for audit</strong>'
    '<h2>The scarp-consensus field beat the H60 incumbent on both holdout instruments.</h2>'
    f'<p>The H65 scarp-consensus field — the per-cell count of the six lidar scarp channels '
    f'that fire above their frozen thresholds, amplitude-tie-broken — is the strongest arm '
    f'of the session-6 slate: on the frozen 41-block holdout it reaches <strong>{P65:.4f} '
    f'pooled DTI</strong> on the primary lidar-peak instrument against the H60 '
    f'incumbent&rsquo;s {H60P:.4f} (+1.4&nbsp;%) and <strong>{SG65:.4f}</strong> on the '
    f'independent SGMC off-catalogue population against {H60S:.4f} (+2.4&nbsp;%) — the only '
    'arm of the round to beat the incumbent on <em>both</em>. Its operating point is '
    f'certified by split conformal prediction: spacing {SP65:g} px ({SP65*100:g} m) chosen '
    f'as the argmax certified floor, rank {RANK} of {N_CAL + 1}, finite-sample coverage at '
    f'least {COV:.2%} (confidence level {COV:.2%}), certified holdout floor {F65:.4f} DTI, '
    'conditional on block exchangeability.</p>'
    f'<p><strong>Why it is not the file to submit:</strong> its 37,654-dot emission at '
    f'{SP65:g}&nbsp;px overlaps the H60 incumbent artifact at mask Jaccard '
    f'<strong>{J65:.4f} &ge; 0.5</strong>, failing the frozen condition 6 (bounded '
    'uniqueness) — this repository will not recommend spending a slot on an emission that '
    'shares most of its dots with the standing incumbent. It is <em>unique against every '
    'scored prior submission</em> (maximum mask Jaccard 0.0067 across the restored scored '
    f'family rasters; {N65} priors compared, zero exact matches); the overlap is '
    'exclusively with the unsubmitted H60 candidate it would supersede. The file is '
    'published for audit, not for submission: <a '
    f'href="downloads/{T65}" download>{T65}</a> · <a href="downloads/{S65}.zip">ZIP + note '
    f'+ receipt</a> · <a href="downloads/{S65}-note.txt">submission note (research)</a> · '
    f'<a href="downloads/{S65}-receipt.json">receipt</a> · <a href="h65.html">H65–H68 '
    'evidence page</a>.</p>'
    f'<p class="filename">{T65}</p>'
    f'<p class="hash">SHA-256 <code>{SHA65}</code> · {B65:,} bytes · 37,654 unit dots at '
    f'{SP65:g} px · 17/17 format read-back checks pass</p></section>\n')

for page in ("index.html", "executive-summary.html"):
    apply(DOCS / page, [(OLD_STATUS, NEW_STATUS),
                        (PANEL_ANCHOR, H68_PANEL),
                        (H50_NOTICE_ANCHOR, H65_NOTICE + H50_NOTICE_ANCHOR)])

# ------------------------------------- executive summary: name + note for the form
OLD_NAME_NOTE = ('<p>34 characters. This is the exact text for the optional Note field. '
                 'The conformal figure is a conditional, proxy-instrument guarantee — '
                 'never present it as a private-label or leaderboard score.</p>')
NEW_NAME_NOTE = (OLD_NAME_NOTE +
                 '<h2>New this session: the H68 candidate (valid submission, not the '
                 'recommendation)</h2>'
                 '<p>The H68 eight-channel lidar field is a new, unique, format-verified '
                 'GeoTIFF generated on 2026-10-08 (download panel above; '
                 '<a href="h65.html">H65–H68 evidence page</a>). It passed the '
                 'preregistered four-condition gate and the uniqueness bar, so it is a '
                 'valid submission — but it does not beat the H60 incumbent on the primary '
                 'holdout instrument, so the repository&rsquo;s recommendation remains the '
                 'H60 file above. Use these identifiers only if you choose to submit the '
                 'H68 file:</p>'
                 f'<p><code id="submission-name-h68">{SUBNAME68}</code> '
                 '<button data-copy-id="submission-name-h68">Copy name</button></p>'
                 f'<pre id="portal-note-h68">{NOTE68}</pre>'
                 '<button data-copy-id="portal-note-h68">Copy short note</button>'
                 f'<p>{len(NOTE68)} characters. This is the exact text for the optional '
                 'Note field if you submit the H68 file. The conformal figure is a '
                 'conditional, proxy-instrument guarantee — never present it as a '
                 'private-label or leaderboard score.</p>'
                 '<h2>Also new: the H65 consensus result (NOT OK to submit)</h2>'
                 '<p>The H65 scarp-consensus field beat the H60 incumbent on <em>both</em> '
                 'holdout instruments (0.2919 vs 0.2879 primary; 0.1984 vs 0.1938 SGMC) — '
                 'the strongest scientific result of the round — but its emission overlaps '
                 'the H60 artifact at mask Jaccard 0.5119, failing the frozen uniqueness '
                 'bar, so it is published as a research artifact and is <strong>not OK to '
                 'submit</strong> while the bar stands. It carries no portal note on '
                 'purpose. See the notice above and <a href="h65.html">the H65–H68 '
                 'evidence page</a>.</p>')
apply(DOCS / "executive-summary.html", [(OLD_NAME_NOTE, NEW_NAME_NOTE)])

# ---------------------------------------------------------------- register
H68_ROW = (f'  <!--h68:row-->  <tr>\n'
           f'    <td><a href="downloads/{T68}" download>{T68}</a><br>\n'
           f'    <a href="downloads/{S68}.zip">ZIP with note + receipt</a> ·\n'
           f'    <a href="downloads/{S68}-note.txt">Submission note (copy-paste)</a> ·\n'
           f'    <a href="downloads/{S68}-receipt.json">Receipt</a> ·\n'
           f'    <a href="h65.html">Evidence page</a></td>\n'
           f'    <td><strong>NEW UNIQUE CANDIDATE · OK TO DOWNLOAD · VALID SUBMISSION · '
           f'NOT THE RECOMMENDATION WHILE H60 STANDS</strong><br>H68 eight-channel lidar '
           f'field, road/claim masked, split-conformal {SP68:g} px (confidence {COV:.2%}, '
           f'floor {F68:.4f}), passed the preregistered four-condition gate and the '
           f'uniqueness bar; does not beat H60 on the primary instrument ({P68:.4f} vs '
           f'{H60P:.4f})</td>\n'
           f'    <td>{a68["budget"]:,}</td>\n'
           f'    <td>float32 {{0,1}}, EPSG:32611, all-finite</td>\n'
           f'    <td>{B68:,}</td>\n'
           f'    <td><code>{SHA68}</code></td>\n'
           f'    <td>VALIDATED CANDIDATE</td>\n'
           f'  </tr>\n')
H65_ROW = (f'  <!--h65:row-->  <tr>\n'
           f'    <td><a href="downloads/{T65}" download>{T65}</a><br>\n'
           f'    <a href="downloads/{S65}.zip">ZIP with note + receipt</a> ·\n'
           f'    <a href="downloads/{S65}-note.txt">Research note</a> ·\n'
           f'    <a href="downloads/{S65}-receipt.json">Receipt</a> ·\n'
           f'    <a href="h65.html">Evidence page</a></td>\n'
           f'    <td><strong>RESEARCH ARTIFACT · NOT OK TO SUBMIT WHILE THE UNIQUENESS '
           f'BAR STANDS</strong><br>H65 scarp-consensus field, road/claim masked, '
           f'split-conformal {SP65:g} px (confidence {COV:.2%}, floor {F65:.4f}); BEAT '
           f'the H60 incumbent on both instruments ({P65:.4f} vs {H60P:.4f} primary; '
           f'{SG65:.4f} vs {H60S:.4f} SGMC) but the emission overlaps the H60 artifact '
           f'at mask Jaccard {J65:.4f} &ge; 0.5, failing frozen condition 6; unique '
           f'against every scored prior submission (max 0.0067)</td>\n'
           f'    <td>{a65["budget"]:,}</td>\n'
           f'    <td>float32 {{0,1}}, EPSG:32611, all-finite</td>\n'
           f'    <td>{B65:,}</td>\n'
           f'    <td><code>{SHA65}</code></td>\n'
           f'    <td>RESEARCH ONLY</td>\n'
           f'  </tr>\n')
apply(DOCS / "all-downloads.html",
      [("  <!--h60:row-->  <tr>", H65_ROW + H68_ROW + "  <!--h60:row-->  <tr>")])

# ---------------------------------------------------------------- irregularities
addition = (
    '<section class="notice" id="ir-2026-10-08-a">\n'
    '<strong>IR-2026-10-08-A · session-6 verdicts (corrected after IR-2026-10-08-D): '
    'all four arms passed the controls; H65 beat the H60 incumbent on both instruments</strong>\n'
    '<p>The session-6 slate (preregistered in <code>docs/research/'
    'h65-hypotheses-preregistered.md</code> before any score) measured on the frozen '
    '41-block holdout: H65 (scarp consensus), H66 (far-field), H67 (lidar+Th/K '
    'alteration) and H68 (eight channels) <strong>all passed the four control '
    'conditions</strong>. H65 is the strongest: pooled selection-half DTI 0.2919 primary '
    '(vs the H60 incumbent&rsquo;s 0.2879, +1.4&nbsp;%) and 0.1984 on the independent '
    'SGMC population (vs 0.1938, +2.4&nbsp;%) — the only arm to beat the incumbent on '
    'both. H68 holds the round&rsquo;s best SGMC DTI (0.2145) but not the primary '
    '(0.2783). An earlier draft of this entry recorded H65 as refuted; that verdict '
    'measured an inverted consensus rank (IR-2026-10-08-D) and is corrected here.</p>\n</section>\n'
    '<section class="notice" id="ir-2026-10-08-b">\n'
    '<strong>IR-2026-10-08-B · tie-break tension recorded, not hidden</strong>\n'
    '<p>The frozen winner rule (highest pooled SGMC selection DTI, then conformal floor) '
    'selects H68 (SGMC 0.2145), and H68 also beats H60 on that independent population '
    '(+10.7&nbsp;%). But the SGMC off-catalogue DTI is <em>negatively</em> '
    'rank-correlated with the 13 owner-reported scores (Spearman −0.421, '
    '<code>evidence/h50/instrument-ranking.json</code>) while the primary lidar-peak '
    'instrument is positively correlated (+0.548) — so the tie-break and the '
    'score-correlation evidence point at different arms. The promotion decision follows '
    'the frozen conditions and the positively correlated instrument; the tension is '
    'published here and on <a href="h65.html">the H65–H68 evidence page</a> rather than '
    'resolved silently.</p>\n</section>\n'
    '<section class="notice" id="ir-2026-10-08-c">\n'
    '<strong>IR-2026-10-08-C · h33-2-b2 measured: a pruning of a scored prior, not a new '
    'signal</strong>\n'
    '<p><code>evidence/h33_reference_analysis.json</code> measures the owner-reported '
    'd2.8 reference (0.2778, attribution unverified): it is the scored d2.8 emission '
    '(44,090 dots, owner-reported 0.2600) <strong>pruned to 37,654 dots</strong> — a '
    'strict mask subset (Jaccard 0.854) — and 59.6&nbsp;% of its dots sit inside the '
    'TIGER-road / BLM-claim noise masks H60 excludes. The owner-reported 0.2600 → 0.2778 '
    'move is the DTI pruning algebra (deleting the lowest-credit dots leaves TP '
    'unchanged while FP falls), i.e. mass discipline on an existing field, not a new '
    'geological signal. The repo&rsquo;s uniqueness gate (max Jaccard &lt; 0.5) would '
    'reject a re-pruning of that emission.</p>\n</section>\n'
    '<section class="notice" id="ir-2026-10-08-d">\n'
    '<strong>IR-2026-10-08-D · H65 consensus-rank inversion, caught by a test and '
    'corrected before publication</strong>\n'
    '<p>The first screen run built the H65 field through a lexicographic rank that '
    'assigned the <em>largest</em> value to the <em>lowest</em>-priority cell, so the '
    'greedy emitter picked the worst cells first and H65 measured 0.0157 (recorded as '
    '&ldquo;refuted&rdquo;). <code>tests/test_h65.py::test_lexicographic_rank_is_tie_free_and_in_unit_interval</code> '
    'failed before any artifact was built; the helper was fixed (<code>r[::-1]</code>) '
    'to implement the preregistered definition exactly, and the screen was re-run. The '
    'corrected H65 beats the H60 incumbent on both instruments. Full record with both '
    'runs&rsquo; numbers: <code>evidence/h65/erratum-consensus-rank-20261008.md</code>. '
    'The preregistration is unchanged — the fix implements the frozen definition; the '
    'bug implemented its reverse.</p>\n</section>\n'
    '<section class="notice" id="ir-2026-10-08-e">\n'
    '<strong>IR-2026-10-08-E · the round&rsquo;s best arm is blocked by the frozen '
    'uniqueness bar, and is published anyway</strong>\n'
    '<p>H65 beat the H60 incumbent on both holdout instruments (conditions 1-5) but its '
    '37,654-dot emission at 2.0&nbsp;px overlaps the H60 artifact at mask Jaccard '
    '<strong>0.5119 &ge; 0.5</strong>, failing frozen condition 6 (bounded uniqueness), so '
    'H60 remains the primary and H65 is published as a research artifact that is '
    '<strong>NOT OK to submit while the bar stands</strong>. The bar was set to stop '
    'H51-style re-emissions (Jaccard 0.8543); H65 is a different field definition '
    '(consensus count vs per-cell max) that shares 68&nbsp;% of its dots with the '
    'incumbent, and it is unique (max 0.0067) against every scored prior submission. '
    'The organiser would accept the file; the bar is this repository&rsquo;s own '
    'slot-protection discipline, and amending it after the scores would be the H49 '
    'failure mode. The artifact, receipt, audit and this disclosure are published '
    'rather than silently dropped.</p>\n</section>\n'
)
apply(DOCS / "irregularities.html", [('<main id="main">', '<main id="main">\n' + addition)])

print("site updated for the H65 round (H60 stays primary; H65 research artifact; "
      "H68 validated candidate)")
sys.exit(0)
