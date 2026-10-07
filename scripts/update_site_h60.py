#!/usr/bin/env python3
"""Rewrite the pages that must make the H60 artifact obviously downloadable.

Run after ``scripts/build_submission_h60.py``.  Every replacement asserts that it
actually changed the file, so a silent miss fails the run instead of publishing a
page that still points at the previous candidate.  H50 is demoted to a clearly
labelled fallback (still valid, no longer the primary).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

receipt = json.loads((DOCS / "data" / "h60-artifact.json").read_text())
STEM = receipt["artifact"]
TIF = f"{STEM}-allfinite.tif"
ZIP = f"{STEM}.zip"
NOTE = f"{STEM}-note.txt"
SHA = receipt["sha256_tif"]
BYTES = receipt["bytes"]
DOTS = receipt["budget"]
FLOOR = receipt["conformal"]["certified_floor_dti"]
COV = receipt["conformal"]["coverage_at_least"]
RANK = receipt["conformal"]["rank_1_based"]
SEL = receipt["holdout"]["candidate_pooled_dti"]
SGMC = receipt["holdout"]["candidate_sgmc_pooled_dti"]


def apply(path: Path, pairs: list[tuple[str, str]], count: int = 1) -> None:
    text = path.read_text()
    for old, new in pairs:
        found = text.count(old)
        if found < count:
            raise SystemExit(f"{path.name}: expected >= {count} match(es) for {old[:70]!r}, "
                             f"found {found}")
        text = text.replace(old, new)
    path.write_text(text)
    print(f"updated {path.relative_to(ROOT)}")


# ---------------------------------------------------------------- index + summary
OLD_STATUS = ('<strong>NEW SUBMISSION READY · OK TO DOWNLOAD AND SUBMIT</strong>'
              '<span>H50 · 37,654 dots · 280 m · split-conformal 91% · one click below. '
              'Research-only H47-C1 / H47-QC / H49 artifacts below are NOT for '
              'submission.</span>')
NEW_STATUS = ('<strong>NEW SUBMISSION READY · OK TO DOWNLOAD AND SUBMIT</strong>'
              f'<span>H60 · {DOTS:,} dots · 200 m · split-conformal {COV:.0%} · '
              'one click below. H50 is a valid fallback; research-only H47-C1 / '
              'H47-QC / H49 artifacts are NOT for submission.</span>')

OLD_PANEL_OPEN = ('<div class="download-panel ready" id="primary-download"><div>'
                  '<span class="eyebrow">New hypothesis · ready to submit · 291,321 bytes'
                  '</span><h2>Download this one GeoTIFF and submit it.</h2>')
NEW_PANEL_OPEN = ('<div class="download-panel ready" id="primary-download"><div>'
                  f'<span class="eyebrow">New hypothesis · ready to submit · {BYTES:,} bytes'
                  '</span><h2>Download this one GeoTIFF and submit it.</h2>')

OLD_PANEL_TEXT = ('<p>A genuinely new H50 field, not a copy of any prior GEMSDOE submission: '
                  'the rank of official band&nbsp;19 (detrended elevation slope) '
                  '<em>above its own 2.5&nbsp;km regional level</em>, so a fault scarp — '
                  'a locally steep step on a gentle surface — outranks a uniformly steep '
                  'mountain front. Emitted as 37,654 unit dots at 280&nbsp;m over the '
                  'evaluated domain (competition footprint minus the USGS/INGENIOUS '
                  'catalogue, which is masked out of scoring). '
                  '<strong>Values are 0/1 only, float32, single band, EPSG:32611, '
                  '100&nbsp;m, all finite, no NoData tag.</strong></p>')
NEW_PANEL_TEXT = ('<p>A genuinely new H60 field, not a copy of any prior GEMSDOE submission: '
                  'the per-cell maximum of the ranks of six scarp channels of the '
                  'owner-derived 1&nbsp;m lidar stack (step height, crest convexity, base '
                  'concavity, up/down-facing and across-slope gradients), masked against '
                  'roads and mine claims — the direct scarp detector, not the 100&nbsp;m '
                  'slope proxy. Emitted as 37,654 unit dots at 200&nbsp;m over the '
                  'evaluated domain (competition footprint minus the USGS/INGENIOUS '
                  'catalogue, which is masked out of scoring). '
                  '<strong>Values are 0/1 only, float32, single band, EPSG:32611, '
                  '100&nbsp;m, all finite, no NoData tag.</strong></p>')

OLD_PANEL_LINKS = ('<a href="downloads/gems47-h50-slopeanom-s2p8-20261007-allfinite.tif" '
                   'class="button primary" download="">↓ Download GeoTIFF (submit this)</a>'
                   '<a href="downloads/gems47-h50-slopeanom-s2p8-20261007.zip" '
                   'class="button secondary" download="">ZIP + note + receipt</a>'
                   '<a href="h50.html" class="button secondary">Why it should work</a>'
                   '<a href="downloads/gems47-h50-slopeanom-s2p8-20261007-note.txt" '
                   'class="text-link">Submission note (copy-paste)</a></div>'
                   '<p class="filename">gems47-h50-slopeanom-s2p8-20261007-allfinite.tif</p>')
NEW_PANEL_LINKS = (f'<a href="downloads/{TIF}" class="button primary" download="">'
                   f'↓ Download GeoTIFF (submit this)</a>'
                   f'<a href="downloads/{ZIP}" class="button secondary" download="">'
                   'ZIP + note + receipt</a>'
                   '<a href="h60.html" class="button secondary">Why it should work</a>'
                   f'<a href="downloads/{NOTE}" class="text-link">Submission note '
                   '(copy-paste)</a></div>'
                   f'<p class="filename">{TIF}</p>')

OLD_EXPORT = ('<p class="export-confidence">Spacing 2.8 px / 280 m · chosen on a selection '
              'half of 20 spatially blocked blocks and certified on the disjoint '
              'calibration half of 21 blocks · split-conformal finite-sample coverage at '
              'least 90.91% (rank 20 of 22) · certified holdout floor 0.0957 DTI · '
              'conditional on block exchangeability</p>'
              '<p class="hash">SHA-256 <code>'
              '97e3c3816cd6b458d01e34d7022f871935bb57710e3982a11d9edaec13e91a17</code></p>'
              '<p class="export-confidence"><strong>Note for the DrivenData form\'s optional '
              'Note field:</strong> <code>h50 slope-anomaly d2p8 conformal90</code></p>')
NEW_EXPORT = (f'<p class="export-confidence">Spacing 2.0 px / 200 m · chosen on a selection '
              f'half of 20 spatially blocked blocks and certified on the disjoint '
              f'calibration half of 21 blocks · split-conformal finite-sample coverage at '
              f'least {COV:.2%} (rank {RANK} of 22) · certified holdout floor {FLOOR:.4f} '
              'DTI · conditional on block exchangeability</p>'
              f'<p class="hash">SHA-256 <code>{SHA}</code></p>'
              '<p class="export-confidence"><strong>Note for the DrivenData form\'s optional '
              'Note field:</strong> <code>h60 lidar-scarp d2p0 conformal90</code></p>')

OLD_GOOD = ('<section class="notice good"><strong>OK TO DOWNLOAD AND SUBMIT</strong>'
            '<h2>What was checked before publishing.</h2>')
NEW_GOOD = ('<section class="notice good"><strong>OK TO DOWNLOAD AND SUBMIT</strong>'
            '<h2>What was checked before publishing.</h2>')

OLD_GOOD_BODY_END = ('On the spatially blocked holdout the candidate reaches 0.1659 pooled '
                     'DTI against 0.0494 for the owner-reported d2.8 reference, 0.0483 for '
                     'the previous holdout best and 0.0470 for mass-matched spaced '
                     'random.</p><div class="actions"><a href="h50.html">Full H50 evidence '
                     '→</a><a href="submit.html">Step-by-step submission guide →</a>'
                     '<a href="data/h50-artifact.json">Machine-readable receipt</a>'
                     '</div></section>')
NEW_GOOD_BODY_END = (f'On the spatially blocked holdout the candidate reaches {SEL:.4f} '
                     'pooled DTI on the primary lidar-peak instrument against 0.1659 for '
                     'H50 (previous candidate), 0.0494 for the owner-reported d2.8 '
                     'reference, 0.0483 for the previous holdout best and 0.0463 for '
                     f'mass-matched spaced random — and {SGMC:.4f} on the independent SGMC '
                     'off-catalogue fault population against 0.0698 random and 0.1221 for '
                     'H50, an instrument the field does not read.</p>'
                     '<div class="actions"><a href="h60.html">Full H60 evidence →</a>'
                     '<a href="submit.html">Step-by-step submission guide →</a>'
                     '<a href="data/h60-artifact.json">Machine-readable receipt</a>'
                     '</div></section>'
                     '<section class="notice"><strong>H50 · VALID FALLBACK · superseded by '
                     'H60</strong><h2>The previous candidate, kept one click away.</h2>'
                     '<p>H50 (rank of band 19 above its 2.5 km regional level, 2.8 px, '
                     '37,654 dots) passed the same gate in the previous round and remains a '
                     'valid, format-checked, unique submission option if you prefer its '
                     'slope-proxy hypothesis: '
                     '<a href="downloads/gems47-h50-slopeanom-s2p8-20261007-allfinite.tif" '
                     'download>gems47-h50-slopeanom-s2p8-20261007-allfinite.tif</a> · '
                     '<a href="h50.html">H50 evidence</a>. The current recommendation is '
                     'H60 above, which beat H50 on both the primary and the independent '
                     'instrument under the same frozen design.</p></section>')

OLD_STATS = ('<div class="stats"><div><strong>37,654</strong><span>unit-dot predictions '
             'at 280 m</span></div><div><strong>0.165881</strong><span>blocked-holdout '
             'pooled DTI, off-catalogue lidar-scarp instrument</span></div>'
             '<div><strong>0.0957</strong><span>split-conformal floor at ≥90.91 % coverage '
             '(conditional)</span></div><div><strong>0</strong><span>competition slots '
             'spent</span></div></div>')
NEW_STATS = ('<div class="stats"><div><strong>37,654</strong><span>unit-dot predictions '
             'at 200 m</span></div><div><strong>0.2879</strong><span>blocked-holdout '
             'pooled DTI, off-catalogue lidar-scarp instrument</span></div>'
             f'<div><strong>{FLOOR:.4f}</strong><span>split-conformal floor at '
             '≥90.91 % coverage (conditional)</span></div><div><strong>0.1938</strong>'
             '<span>independent SGMC off-catalogue DTI (random control 0.0698)</span>'
             '</div></div>')

OLD_HERO = ('<p class="lede">A geological hypothesis becomes useful only when it survives '
            'the controls. The new H50 slope-anomaly detector passed every control on the '
            'spatially blocked holdout, so it is published as <strong>OK to download and '
            'submit</strong> — the first artifact in this repository to be.</p>')
NEW_HERO = ('<p class="lede">A geological hypothesis becomes useful only when it survives '
            'the controls. The new H60 lidar scarp-crest detector passed every control on '
            'the spatially blocked holdout — including an independent fault compilation it '
            'never reads — so it is published as <strong>OK to download and submit</strong>.'
            '</p>')

OLD_TABLE = ('<tbody><tr><td><strong>H50 slope-anomaly field</strong></td>'
             '<td><strong>0.165881</strong></td><td><strong>0.163039</strong></td>'
             '<td><strong>2.8 px</strong></td></tr>')
NEW_TABLE = ('<tbody><tr><td><strong>H60 lidar scarp-crest field</strong></td>'
             '<td><strong>0.287891</strong></td><td><strong>0.284379</strong></td>'
             '<td><strong>2.0 px</strong></td></tr>'
             '<tr><td>H50 slope-anomaly field (previous candidate)</td>'
             '<td>0.165881</td><td>0.163039</td><td>2.8 px</td></tr>')

OLD_BLOCKS = ('<p>Sixty-one contiguous blocks with a 3 px guard; roles assigned before any '
              'score was computed; blocks with few or no truth pixels kept.')
NEW_BLOCKS = ('<p>Forty-one contiguous blocks with a 3 px guard; roles assigned before any '
              'score was computed; blocks with few or no truth pixels kept. (An earlier '
              'version of this page said sixty-one; the count is 41 = 20 selection + 21 '
              'calibration — corrected 2026-10-07.)')

OLD_CONF = ('<div class="confidence"><strong>Selected spacing 2.8 px / 280 m · '
            'split-conformal, max-residual, rank 20 of 22, coverage ≥ 90.91 %</strong>')
NEW_CONF = ('<div class="confidence"><strong>Selected spacing 2.0 px / 200 m · '
            'split-conformal, max-residual, rank 20 of 22, coverage ≥ 90.91 %</strong>')

OLD_FLOORTEXT = ('<div class="notice"><strong>WHAT THE FLOOR MEANS, AND WHAT IT DOES NOT</strong>'
                '<p>The 0.0957 figure is a finite-sample split-conformal lower bound on the '
                '<em>holdout</em> DTI of the H50 spacing choice,')
NEW_FLOORTEXT = ('<div class="notice"><strong>WHAT THE FLOOR MEANS, AND WHAT IT DOES NOT</strong>'
                f'<p>The {FLOOR:.4f} figure is a finite-sample split-conformal lower bound '
                'on the <em>holdout</em> DTI of the H60 spacing choice,')

for page in ("index.html", "executive-summary.html"):
    p = DOCS / page
    pairs = [(OLD_STATUS, NEW_STATUS), (OLD_PANEL_OPEN, NEW_PANEL_OPEN),
             (OLD_PANEL_TEXT, NEW_PANEL_TEXT), (OLD_PANEL_LINKS, NEW_PANEL_LINKS),
             (OLD_EXPORT, NEW_EXPORT), (OLD_GOOD_BODY_END, NEW_GOOD_BODY_END)]
    if page == "index.html":
        pairs += [(OLD_STATS, NEW_STATS), (OLD_HERO, NEW_HERO), (OLD_TABLE, NEW_TABLE),
                  (OLD_BLOCKS, NEW_BLOCKS), (OLD_CONF, NEW_CONF),
                  (OLD_FLOORTEXT, NEW_FLOORTEXT)]
    apply(p, pairs)

# the executive summary's portal note/name block
apply(DOCS / "executive-summary.html", [
    ('<pre id="portal-note">h50 slope-anomaly d2p8 conformal90</pre>',
     '<pre id="portal-note">h60 lidar-scarp d2p0 conformal90</pre>'),
    ('<code id="submission-name">GEMSDOE47-C1-D2p8-bdf4508769c8</code>',
     '<code id="submission-name">GEMSDOE47-H60-lidarscarp-s2p0-20261007</code>'),
    ('31 characters. This is the exact text for the optional Note field.',
     '34 characters. This is the exact text for the optional Note field.'),
    ('<title>Executive summary: how to submit H50 · GEMSDOE47</title>',
     '<title>Executive summary: how to submit H60 · GEMSDOE47</title>'),
])

# ---------------------------------------------------------------- register
reg = DOCS / "all-downloads.html"
apply(reg, [
    ('<p class="lede">The landing page leads with <strong>H50, which is OK to download and submit</strong>,',
     '<p class="lede">The landing page leads with <strong>H60, which is OK to download and submit</strong>,'),
    ('<strong>One file has passed its gate: the H50 slope-anomaly raster, which is OK to download and submit.</strong>',
     '<strong>Two files have passed their gates: the H60 lidar scarp-crest raster (primary recommendation) and the H50 slope-anomaly raster (valid fallback).</strong>'),
    ('<!--h49:row-->  <tr>',
     f'<!--h60:row-->  <tr>\n    <td><a href="downloads/{TIF}" download>{TIF}</a><br>\n'
     f'    <a href="downloads/{ZIP}">ZIP with note + receipt</a> ·\n'
     f'    <a href="downloads/{NOTE}">Submission note (copy-paste)</a> ·\n'
     f'    <a href="downloads/{STEM}-receipt.json">Receipt</a> ·\n'
     '    <a href="h60.html">Evidence page</a></td>\n'
     '    <td><strong>PRIMARY · OK TO DOWNLOAD AND SUBMIT</strong><br>'
     'H60 lidar scarp-crest field, road/claim masked, split-conformal 2.0 px, '
     'passed preregistered gate (primary + independent instruments)</td>\n'
     '    <td>37,654</td>\n    <td>float32 {0,1}, EPSG:32611, all-finite</td>\n'
     f'    <td>{BYTES:,}</td>\n    <td><code>{SHA[:16]}…</code></td>\n'
     '    <td>PROMOTED</td>\n  </tr>\n  <!--h50:row-->  <tr>'),
])

# ---------------------------------------------------------------- irregularities
irr = DOCS / "irregularities.html"
addition = (
    '<section class="notice" id="ir-2026-10-07-b">\n'
    '<strong>IR-2026-10-07-B · provenance wording corrected (lidar stack)</strong>\n'
    '<p>The H50 documentation called the 1 m lidar scarp stack "organiser-supplied". '
    'The restore manifest is authoritative: the stack was derived by the owner\'s CI from '
    'USGS 3DEP 1 m DEM tiles (706/716; tile list OCR-recovered from the competition PDF), '
    'pinned at <code>registry/data_manifest.json</code> entry '
    '<code>ext_lidar_scarp_features_u8</code>. All session-5 text says "owner-derived"; '
    'the affected H50-era sentences are corrected in the README and evidence pages. '
    'No bytes changed.</p>\n</section>\n'
    '<section class="notice" id="ir-2026-10-07-c">\n'
    '<strong>IR-2026-10-07-C · block-count wording corrected (H50 screen)</strong>\n'
    '<p>The H50 page said "sixty-one contiguous blocks"; the frozen H50 screen design has '
    '41 blocks (20 selection + 21 calibration) after dropping geometric cells with no '
    'evaluated pixel. The H50 screen JSON and blocks.json always said 20/21; only the '
    'prose was wrong. Corrected on the landing page with a dated note.</p>\n</section>\n'
    '<section class="notice" id="ir-2026-10-07-d">\n'
    '<strong>IR-2026-10-07-D · two session-5 implementation deviations, recorded</strong>\n'
    '<p>(1) The preregistered H61 per-trace allocation used a min-1 floor per component; '
    'measured, it over-emitted whenever trace components outnumbered the budget (649 dots '
    'for a 294 budget on block 0; 2,357 for 1,400 on block 5). Replaced by deterministic '
    'largest-remainder allocation; H61 failed its gate either way. '
    '(2) The H60 screen initially reported emitted mass divided by 7 (an aggregation bug); '
    'recomputed directly from the spacing history (H60: 17,889 of 21,198 budget dots on '
    'the selection half — under-emission is the noise-masked domain\'s own capacity limit, '
    'published as such). No score changed.</p>\n</section>\n'
)
apply(irr, [('<main id="main">', '<main id="main">\n' + addition)])

print("site updated for H60")
return_code = 0
sys.exit(return_code)
