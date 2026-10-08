#!/usr/bin/env python3
"""Publish the H71-round artifacts on the reconciled site, honestly labelled.

Run after ``scripts/build_submission_h71.py``.  Every replacement asserts that it
actually changed the file (and is idempotent on re-runs).

This script is written against the site as reconciled with the concurrent session-6
sibling slate (H65-H70, merged in PR #30): their structure, their status bars and their
encoding framing are the base; this round's artifacts are added additively:

* **H74** — the new unique TIF (frozen winner by the SGMC tie-break; passed control
  conditions 1-4 and the uniqueness bar): a gate-passing valid submission, OK to
  download, NOT the recommendation while H60 stands.  Both encodings are offered with
  the same framing the site already uses for H60 (all-finite = the [0,1] range-rejection
  defense; NaN-outside = the published null/NaN-outside wording; neither
  organizer-accepted).
* **H71** — the round's best science (beat the H60 incumbent on BOTH holdout
  instruments) but its emission overlaps the H60 incumbent at mask Jaccard 0.5119 >= 0.5,
  failing frozen condition 6: a research artifact, NOT OK TO SUBMIT while the bar stands.
* H60 remains the current local candidate; no upload or slot use by any review.

The root ``index.html`` (the Pages landing page, since Pages serves ``main:/``) is
regenerated from ``docs/index.html`` with every relative link repointed under ``docs/``
— the same mirror convention the site already uses, never hand-patched.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

a71 = json.loads((DOCS / "data" / "h71-artifact.json").read_text())
a74 = json.loads((DOCS / "data" / "h74-artifact.json").read_text())

S71, S74 = a71["artifact"], a74["artifact"]
T71, T74 = f"{S71}-allfinite.tif", f"{S74}-allfinite.tif"
N71, N74 = f"{S71}-nanoutside.tif", f"{S74}-nanoutside.tif"
SHA71, SHA74 = a71["sha256_tif"], a74["sha256_tif"]
B71, B74 = a71["bytes"], a74["bytes"]
SP71, SP74 = a71["spacing_px"], a74["spacing_px"]
F71 = a71["conformal"]["certified_floor_dti"]
F74 = a74["conformal"]["certified_floor_dti"]
COV = a71["conformal"]["coverage_at_least"]
RANK = a71["conformal"]["rank_1_based"]
N_CAL = a71["conformal"]["calibration_blocks"]
NOTE74 = a74["submission_note_field"]
P71 = a71["holdout"]["candidate_pooled_dti"]
SG71 = a71["holdout"]["candidate_sgmc_pooled_dti"]
P74 = a74["holdout"]["candidate_pooled_dti"]
SG74 = a74["holdout"]["candidate_sgmc_pooled_dti"]
H60P = a71["holdout"]["h60_incumbent_pooled_dti"]
H60S = a71["holdout"]["h60_incumbent_sgmc_pooled_dti"]
H50P = a71["holdout"]["h50_anchor_pooled_dti"]
J71 = a71["uniqueness"]["max_jaccard"]
J74 = a74["uniqueness"]["max_jaccard"]
N71C = a71["uniqueness"]["compared"]
N74C = a74["uniqueness"]["compared"]
SUBNAME74 = "GEMSDOE47-H74-lidar8ch-s2p8-20261008"


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


# ---------------------------------------------------------------- status bars
OLD_STATUS_HOME = ('<strong>H60 LOCAL SCIENTIFIC GATE PASSED · NO UPLOAD OR SLOT USE</strong>\n'
                   '  <span>Organizer acceptance is untested. H47-C1 remains not promoted; its '
                   'gate remains closed.</span>')
NEW_STATUS_HOME = ('<strong>H60 LOCAL GATE PASSED · H74 NEW UNIQUE CANDIDATE · H71 RESEARCH '
                   'ARTIFACT · NO UPLOAD OR SLOT USE</strong>\n'
                   '  <span>Organizer acceptance is untested. H47-C1 remains not promoted; its '
                   'gate remains closed. Session-6 second slate (H71–H74, 8 Oct 2026): H74 is a '
                   'gate-passing valid submission but not the recommendation; H71 beat H60 on '
                   'both holdout instruments and is held back by the uniqueness bar.</span>')
OLD_STATUS_SUM = ('<strong>H60 LOCAL GATE PASSED · NO PORTAL ACTION</strong>\n'
                  '  <span>Organizer acceptance is untested. No upload or slot use is authorized '
                  'or performed in this review.</span>')
NEW_STATUS_SUM = ('<strong>H60 LOCAL GATE PASSED · H74 NEW UNIQUE CANDIDATE · H71 RESEARCH '
                  'ARTIFACT · NO PORTAL ACTION</strong>\n'
                  '  <span>Organizer acceptance is untested. No upload or slot use is authorized '
                  'or performed in this review. The H71–H74 round added a gate-passing unique '
                  'candidate (H74) and a research artifact (H71); see the panels below.</span>')

# ---------------------------------------------------------------- H74 panel
PANEL_BODY = (
    '  <div class="download-panel" id="h74-download">\n'
    '    <div>\n'
    f'      <span class="eyebrow">H74 · NEW UNIQUE CANDIDATE · generated 2026-10-08 · both '
    'encodings · NOT THE RECOMMENDATION WHILE H60 STANDS</span>\n'
    '      <h2>New this session: the H74 eight-channel lidar field — a unique TIF, not a copy '
    'of any prior submission.</h2>\n'
    '      <p>A genuinely new field: the per-cell maximum of the ranks of <em>eight</em> scarp '
    'channels of the owner-derived 1&nbsp;m lidar stack (H60&rsquo;s six plus slope-excess '
    f'<code>ex_max</code> and local relief <code>relief</code>), masked against roads and mine '
    f'claims, emitted as {a74["budget"]:,} unit dots at {SP74:g}&nbsp;px ({SP74*100:g}&nbsp;m) '
    'over the noise-masked off-catalogue domain. It passed the preregistered four-condition '
    f'gate (beats the H50 anchor by +68&nbsp;%, certified split-conformal floor {F74:.4f} DTI at '
    '&ge;{COV:.2%} coverage, beats the mass-matched random control on both instruments) and the '
    f'uniqueness bar ({N74C} prior rasters, zero exact matches, maximum mask Jaccard '
    f'{J74:.4f}). <strong>It is a gate-passing valid submission — but it does not beat the H60 '
    f'incumbent on the primary lidar-peak instrument ({P74:.4f} vs {H60P:.4f}), so H60 remains '
    'the recommendation.</strong></p>\n'
    '    </div>\n'
    '    <div class="actions">\n'
    f'      <a href="downloads/{T74}" class="button primary" download>↓ Download the new H74 '
    'GeoTIFF (all-finite, [0,1] range defense)</a>\n'
    f'      <a href="downloads/{N74}" class="button secondary" download>NaN-outside variant '
    '(null/NaN-outside wording)</a>\n'
    f'      <a href="downloads/{S74}.zip" class="button secondary" download>ZIP + note + '
    'receipt</a>\n'
    '      <a href="h71.html" class="button secondary">Why it should work (H71–H74 '
    'evidence)</a>\n'
    f'      <a href="downloads/{S74}-note.txt" class="text-link">Submission note '
    '(copy-paste)</a>\n'
    '    </div>\n'
    f'    <p class="filename">{T74}</p>\n'
    f'    <p class="hash">SHA-256 <code>{SHA74}</code> · {B74:,} bytes · NaN-outside sibling '
    f'<code>{N74}</code></p>\n'
    f'    <p class="export-confidence">Spacing {SP74:g} px / {SP74*100:g} m · selected by split '
    'conformal prediction (Lei et al. JASA 2018, Algorithm 2) as the spacing with the greatest '
    f'CERTIFIED lower bound · max-residual rank {RANK} of {N_CAL + 1} · finite-sample coverage at '
    f'least {COV:.2%} (confidence level {COV:.2%}) · certified holdout floor {F74:.4f} DTI · '
    'conditional on block exchangeability</p>\n'
    f'    <p><strong>Future-only Name:</strong> <code>{SUBNAME74}</code> · <strong>Short '
    f'Note:</strong> <code>{NOTE74}</code></p>\n'
    '    <p><strong>OK to download: YES · gate-passing valid submission · recommended for '
    'submission: NO — H60 above remains the local candidate.</strong> '
    f'Uniqueness: {N74C} prior rasters compared, zero exact matches, maximum mask Jaccard '
    f'{J74:.4f} (closest prior: the H60 incumbent, expected — H74 extends H60&rsquo;s channel '
    'set). <strong>Encoding caveat:</strong> the all-finite file is the direct answer to the '
    'portal&rsquo;s &ldquo;Predicted values must be in range [0, 1]&rdquo; rejection (every value '
    'finite and inside [0,1]); the NaN-outside sibling matches the published null/NaN-outside '
    'wording locally. Neither encoding is organizer-accepted; the historical range-error cause '
    'is unknown. Submit H74 only if you accept that trade-off and the encoding question — the '
    'full comparison is on <a href="h71.html">the H71–H74 evidence page</a>.</p>\n'
    '  </div>\n')

PRIMARY_END_HOME = ('<p><strong>Future-only Name:</strong> '
                    '<code>GEMSDOE47-H60-lidarscarp-s2p0-20261007</code> · <strong>Short '
                    'Note:</strong> <code>h60 lidar-scarp d2p0 conformal90</code></p>\n'
                    '  </div>\n'
                    '  <section class="hero">')
H74_PANEL_HOME = PRIMARY_END_HOME.replace('  <section class="hero">',
                                          PANEL_BODY + '  <section class="hero">')
SUM_PRIMARY_END = ('<p><strong>Future-only Name:</strong> '
                   '<code>GEMSDOE47-H60-lidarscarp-s2p0-20261007</code><br>'
                   '<strong>Future-only Short Note:</strong> '
                   '<code>h60 lidar-scarp d2p0 conformal90</code></p>\n'
                   '  </div>\n'
                   '  <section class="page-heading">')
H74_PANEL_SUM = SUM_PRIMARY_END.replace('  <section class="page-heading">',
                                        PANEL_BODY + '  <section class="page-heading">')

# ---------------------------------------------------------------- H71 notice
ENCODING_END = ('The historical range-error cause is unknown because rejected bytes and parser '
                'receipt are unavailable.</p>\n'
                '  </section>\n')
H71_NOTICE = (ENCODING_END +
              '  <section class="notice" id="h71-review">\n'
              '    <strong>H71 · RESEARCH ARTIFACT · NOT OK TO SUBMIT WHILE THE UNIQUENESS BAR '
              'STANDS</strong>\n'
              '    <h2>The scarp-consensus field beat the H60 incumbent on both holdout '
              'instruments — and is held back by the frozen uniqueness bar.</h2>\n'
              f'    <p>The H71 scarp-consensus field — the per-cell count of the six lidar '
              f'scarp channels that fire above their frozen thresholds, '
              f'amplitude-tie-broken — is the strongest arm of the session-6 second slate: on '
              f'the frozen 41-block holdout it reaches <strong>{P71:.4f} pooled DTI</strong> '
              f'on the primary lidar-peak instrument against the H60 incumbent&rsquo;s '
              f'{H60P:.4f} (+1.4&nbsp;%) and <strong>{SG71:.4f}</strong> on the independent '
              f'SGMC off-catalogue population against {H60S:.4f} (+2.4&nbsp;%) — the only arm '
              f'of the round to beat the incumbent on <em>both</em>. Its operating point is '
              f'certified by split conformal prediction: spacing {SP71:g} px '
              f'({SP71*100:g} m) chosen as the argmax certified floor, rank {RANK} of '
              f'{N_CAL + 1}, finite-sample coverage at least {COV:.2%} (confidence level '
              f'{COV:.2%}), certified holdout floor {F71:.4f} DTI, conditional on block '
              'exchangeability.</p>\n'
              f'    <p><strong>Why it is not the file to submit:</strong> its {a71["budget"]:,}'
              f'-dot emission at {SP71:g}&nbsp;px overlaps the H60 incumbent artifact at mask '
              f'Jaccard <strong>{J71:.4f} &ge; 0.5</strong>, failing frozen condition 6 '
              '(bounded uniqueness) — this repository will not recommend spending a slot on an '
              'emission that shares most of its dots with the standing incumbent. It is '
              '<em>unique against every scored prior submission</em> (maximum mask Jaccard '
              f'{a71["uniqueness"]["max_jaccard_vs_scored_priors"]:.4f} across the restored '
              f'scored family rasters; {N71C} priors compared, zero exact matches); the overlap '
              'is exclusively with the unsubmitted H60 candidate it would supersede. The file is '
              f'published for audit, not for submission: <a href="downloads/{T71}" '
              f'download>{T71}</a> · <a href="downloads/{S71}.zip">ZIP + note + receipt</a> · '
              f'<a href="downloads/{S71}-note.txt">research note</a> · <a '
              f'href="downloads/{S71}-receipt.json">receipt</a> · <a href="h71.html">H71–H74 '
              'evidence page</a>.</p>\n'
              f'    <p class="filename">{T71}</p>\n'
              f'    <p class="hash">SHA-256 <code>{SHA71}</code> · {B71:,} bytes · '
              f'{a71["budget"]:,} unit dots at {SP71:g} px · 17/17 format read-back checks '
              'pass</p>\n'
              '  </section>\n')

# ------------------------------------------------- frozen-evaluation extension
OLD_EVAL_TAIL = ('so H60 remains the current local candidate: '
                 '<a href="h65.html">H65 round evidence</a>.</p>')
NEW_EVAL_TAIL = ('so H60 remains the current local candidate: '
                 '<a href="h65.html">H65 round evidence</a>. A second preregistered slate the '
                 'same day (H71–H74: scarp consensus, far-field, lidar+GeoDAWN Th/K alteration, '
                 'eight-channel lidar) then found <strong>H71 beating H60 on both '
                 'instruments</strong> (0.2919 vs 0.2879 primary; 0.1984 vs 0.1938 SGMC) — held '
                 'back only by the frozen uniqueness bar (mask Jaccard 0.5119 vs the H60 '
                 'incumbent) — and <strong>H74</strong> as the round&rsquo;s frozen winner (best '
                 'independent-instrument DTI 0.2145; gate-passing unique candidate, not the '
                 'recommendation): <a href="h71.html">H71–H74 evidence</a>.</p>')

OLD_HISTORY = ('<p><a href="current-status.html">Current status</a> · '
               '<a href="h65.html">H65 challenger round (negative; H60 stands)</a> · ')
NEW_HISTORY = ('<p><a href="current-status.html">Current status</a> · '
               '<a href="h65.html">H65 challenger round (negative; H60 stands)</a> · '
               '<a href="h71.html">H71–H74 second slate (H74 candidate; H71 research '
               'artifact)</a> · ')

apply(DOCS / "index.html", [
    (OLD_STATUS_HOME, NEW_STATUS_HOME),
    (PRIMARY_END_HOME, H74_PANEL_HOME),
    (ENCODING_END, H71_NOTICE),
    (OLD_EVAL_TAIL, NEW_EVAL_TAIL),
    (OLD_HISTORY, NEW_HISTORY),
])

# ------------------------------------------------------- executive summary
SUM_PRIMARY_END = ('<p><strong>Future-only Name:</strong> '
                  '<code>GEMSDOE47-H60-lidarscarp-s2p0-20261007</code><br>'
                  '<strong>Future-only Short Note:</strong> '
                  '<code>h60 lidar-scarp d2p0 conformal90</code></p>\n'
                  '  </div>\n'
                  '  <section class="page-heading">')
H74_PANEL_SUM = (SUM_PRIMARY_END.replace('  <section class="page-heading">',
                                         '  <PLACEHOLDER>') .replace(
    '<p><strong>Future-only Name:</strong> '
    '<code>GEMSDOE47-H60-lidarscarp-s2p0-20261007</code><br>'
    '<strong>Future-only Short Note:</strong> '
    '<code>h60 lidar-scarp d2p0 conformal90</code></p>\n'
    '  </div>\n'
    '  <PLACEHOLDER>',
    '<p><strong>Future-only Name:</strong> '
    '<code>GEMSDOE47-H60-lidarscarp-s2p0-20261007</code><br>'
    '<strong>Future-only Short Note:</strong> '
    '<code>h60 lidar-scarp d2p0 conformal90</code></p>\n'
    '  </div>\n'
    + H74_PANEL_HOME.split('  </div>\n  <section class="hero">')[0].split(
        '  </div>\n', 1)[1]
    + '  <section class="page-heading">')
)
screen = json.loads((ROOT / "evidence" / "h71" / "screen.json").read_text())
P72 = screen["arms"]["h72"]["pooled_primary_selection"]
SG72 = screen["arms"]["h72"]["pooled_sgmc_selection"]
P73 = screen["arms"]["h73"]["pooled_primary_selection"]
SG73 = screen["arms"]["h73"]["pooled_sgmc_selection"]

OLD_SUM_MEASURED_END = ('<li>Bounded uniqueness: 35 prior rasters, zero exact matches, maximum '
                        'mask Jaccard 0.021707. This is not a global-uniqueness proof.</li>\n'
                        '    </ul>\n'
                        '  </section>')
NEW_SUM_MEASURED_END = (OLD_SUM_MEASURED_END +
                        '  <section>\n'
                        '    <h2>What the H71–H74 round measured (session-6 second slate, '
                        '8 October 2026)</h2>\n'
                        '    <ul class="checklist">\n'
                        '      <li>Four new hypotheses (H71 scarp consensus, H72 far-field '
                        'emission, H73 lidar+GeoDAWN Th/K alteration, H74 eight-channel lidar), '
                        'preregistered before any score and screened on the same frozen '
                        '41-block holdout; the operating point is the <strong>argmax of the '
                        'certified split-conformal lower bound</strong> (rank 20 of 22, '
                        'coverage at least 90.91&nbsp;%, conditional on block '
                        'exchangeability).</li>\n'
                        f'      <li><strong>H71 beat the H60 incumbent on both holdout '
                        f'instruments</strong> ({P71:.4f} vs {H60P:.4f} primary; {SG71:.4f} '
                        f'vs {H60S:.4f} SGMC) — the round&rsquo;s headline science — but is '
                        'held back by the frozen uniqueness bar (mask Jaccard 0.5119 vs the '
                        'H60 incumbent): a research artifact, NOT OK TO SUBMIT while the bar '
                        'stands.</li>\n'
                        f'      <li><strong>H74 is the round&rsquo;s frozen winner</strong> '
                        f'({P74:.4f} primary; {SG74:.4f} independent SGMC — the '
                        f'round&rsquo;s best) and a <strong>gate-passing unique '
                        f'candidate</strong> (zero exact matches, max Jaccard {J74:.4f}): a '
                        'valid submission, OK to download, but not the recommendation while '
                        'H60 stands.</li>\n'
                        f'      <li>H72 (far-field lidar) {P72:.4f} primary / {SG72:.4f} '
                        f'independent; H73 (lidar+Th/K alteration) {P73:.4f} / {SG73:.4f} — '
                        'both passed the four control conditions; neither beats H60 on both. '
                        'All four arms passed the controls; none was refuted.</li>\n'
                        '      <li>The 0.2778 question, measured: the owner-reported h33-2-b2 '
                        'raster is the scored d2.8 emission pruned 44,090 → 37,654 dots (strict '
                        'mask subset, Jaccard 0.854), 59.6&nbsp;% of its dots inside the '
                        'road/claim noise masks; the 0.2600 → 0.2778 move is the DTI pruning '
                        'algebra — mass discipline on an existing field, not a new '
                        'signal.</li>\n'
                        '    </ul>\n'
                        '  </section>')
SUM_ENCODING_END = ('Local read-back does not prove organizer acceptance.</p>\n'
                    '  </section>\n')
apply(DOCS / "executive-summary.html", [
    (OLD_STATUS_SUM, NEW_STATUS_SUM),
    (SUM_PRIMARY_END, H74_PANEL_SUM),
    (SUM_ENCODING_END, SUM_ENCODING_END + H71_NOTICE.split(ENCODING_END)[1]),
    (OLD_SUM_MEASURED_END, NEW_SUM_MEASURED_END),
])

# ------------------------------------------------------- root mirror
root = ROOT / "index.html"
docs_index = (DOCS / "index.html").read_text()

def repoint(m: re.Match) -> str:
    attr, url = m.group(1), m.group(2)
    if re.match(r"(?:[a-z][a-z0-9+.-]*:|#|/)", url):
        return m.group(0)
    return f'{attr}="docs/{url}"'

mirror = re.sub(r'(href|src)="([^"]+)"', repoint, docs_index)
mirror = mirror.replace('data-base=""', 'data-base="docs/"', 1)
root.write_text(mirror)
print("regenerated root index.html mirror (relative links repointed under docs/)")

print("site updated for the H71 round on the reconciled base "
      "(H60 local candidate; H74 unique candidate; H71 research artifact)")
sys.exit(0)
