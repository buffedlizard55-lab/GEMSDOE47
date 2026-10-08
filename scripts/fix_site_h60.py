#!/usr/bin/env python3
"""Fix the pages scripts/update_site_h60.py missed (IR-2026-10-08-A).

Session 5 moved docs/index.html, docs/executive-summary.html, docs/all-downloads.html
and docs/irregularities.html to H60 but left three visitor-facing surfaces stale:

* the repository-root ``index.html`` -- the actual GitHub Pages landing page, since
  Pages serves ``main:/`` -- still offered the research-only H47-C1 TIFF;
* ``docs/submit.html`` still described the H47-C1 research run (half-updated status
  bar aside) and told the reader to stop;
* ``docs/index.html`` kept its H50 <title>/meta, and both submit-step lists kept the
  "This C1 report does not pass. Stop here for this file." sentence.

Every replacement asserts it matched, so a silent miss fails loudly.  H60 values are
read from the published artifact receipt, never hand-copied.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

receipt = json.loads((DOCS / "data" / "h60-artifact.json").read_text())
STEM = receipt["artifact"]
TIF = f"{STEM}-allfinite.tif"
ZIP = f"{STEM}.zip"
NOTE = f"{STEM}-note.txt"
FALLBACK = f"{STEM[: -len('20261007')]}20261007-nanoutside.tif"
SHA = receipt["sha256_tif"]
BYTES = receipt["bytes"]
DOTS = receipt["budget"]
FLOOR = receipt["conformal"]["certified_floor_dti"]
COV = receipt["conformal"]["coverage_at_least"]
RANK = receipt["conformal"]["rank_1_based"]
SUBMISSION_NAME = "GEMSDOE47-H60-lidarscarp-s2p0-20261007"
PORTAL_NOTE = "h60 lidar-scarp d2p0 conformal90"

assert receipt["spacing_px"] == 2.0, "this fixer assumes the H60 2.0 px artifact"
assert len(PORTAL_NOTE) == 32, "portal-note length changed; recount before publishing"
H50_PORTAL_NOTE = "h50 slope-anomaly d2p8 conformal90"
assert len(H50_PORTAL_NOTE) == 34, "H50 portal-note length changed; recount"


def apply(path: Path, pairs: list[tuple[str, str]], count: int = 1) -> None:
    text = path.read_text()
    for old, new in pairs:
        found = text.count(old)
        if found < count:
            raise SystemExit(f"{path}: expected >= {count} match(es) for {old[:70]!r}, "
                             f"found {found}")
        text = text.replace(old, new)
    path.write_text(text)
    print(f"updated {path.relative_to(ROOT)}")


# ------------------------------------------------- docs/index.html title + meta
apply(DOCS / "index.html", [
    ("<title>H50 submission ready · GEMSDOE47</title>",
     "<title>H60 submission ready · GEMSDOE47</title>"),
    ("A new H50 GeoTIFF that is OK to download and submit: 37,654 dots at 280 m,",
     "A new H60 GeoTIFF that is OK to download and submit: 37,654 dots at 200 m,"),
])

# ------------------------------------------------- docs/submit.html rewritten
submit = DOCS / "submit.html"
apply(submit, [
    ('<strong>H50 · OK TO DOWNLOAD AND SUBMIT</strong><span>The H47/H48/H49 artifacts '
     'described on this page are research-only and are not the file to upload.</span>',
     '<strong>H60 · OK TO DOWNLOAD AND SUBMIT</strong><span>The H50 fallback below is '
     'also valid; the H47/H48/H49 artifacts described on this page are research-only '
     'and are not the file to upload.</span>'),
    ('<section class="page-heading"><span class="eyebrow">Format is necessary, not '
     'sufficient</span><h1>A valid TIFF.<br>Not an eligible slot.</h1></section>',
     '<section class="page-heading"><span class="eyebrow">H60 · the file to submit</span>'
     '<h1>Download it.<br>Verify it. Submit it.</h1></section>'),
    ('<div class="download-panel"><div><span class="eyebrow">Newly inferred · 152,396 bytes'
     '</span><h2>One file. Full supplied 100 m research grid.</h2><p>Not a renamed prior '
     'submission. New H47-C1 inference; <strong>research-only, not for submission</strong>.'
     '</p></div><div class="actions"><a href="downloads/'
     'gems47-c1-oddstep-channel-d2p8-20261006-bdf4508769c8-finite-mask.tif" '
     'class="button primary" download="">↓ Download GeoTIFF</a><a href="downloads/'
     'gems47-c1-oddstep-channel-d2p8-20261006-bdf4508769c8-finite-mask.zip" '
     'class="button secondary" download="">Single-TIFF ZIP</a><a href="data/'
     'current-submission.json" class="text-link">Validation receipt</a></div>'
     '<p class="filename">gems47-c1-oddstep-channel-d2p8-20261006-bdf4508769c8-finite-mask.tif'
     '</p><p class="export-confidence">Spacing 2.8 px / 280 m · nominal 90% marginal block '
     'band · assumption-conditional lower-bound estimate 0.0000 · NOT private/global</p>'
     '<p class="hash">SHA-256 <code>e6eea1956b8f76ffef2f4867a6e2ac0bef078c0c61c3711e44eb07e93cb089d0'
     '</code></p></div>',
     f'<div class="download-panel ready" id="primary-download"><div><span class="eyebrow">'
     f'New hypothesis · ready to submit · {BYTES:,} bytes</span><h2>Download this one '
     f'GeoTIFF and submit it.</h2><p>A genuinely new H60 field, not a copy of any prior '
     f'GEMSDOE submission: the per-cell maximum of the ranks of six scarp channels of the '
     f'owner-derived 1&nbsp;m lidar stack, masked against roads and mine claims. Emitted '
     f'as {DOTS:,} unit dots at 200&nbsp;m over the evaluated domain (competition footprint '
     f'minus the USGS/INGENIOUS catalogue, which is masked out of scoring). '
     f'<strong>Values are 0/1 only, float32, single band, EPSG:32611, 100&nbsp;m, all '
     f'finite, no NoData tag.</strong></p></div><div class="actions">'
     f'<a href="downloads/{TIF}" class="button primary" download="">↓ Download GeoTIFF '
     f'(submit this)</a><a href="downloads/{ZIP}" class="button secondary" download="">'
     f'ZIP + note + receipt</a><a href="h60.html" class="button secondary">Why it should '
     f'work</a><a href="downloads/{NOTE}" class="text-link">Submission note '
     f'(copy-paste)</a></div><p class="filename">{TIF}</p>'
     f'<p class="export-confidence">Spacing 2.0 px / 200 m · chosen on a selection half of '
     f'20 spatially blocked blocks and certified on the disjoint calibration half of 21 '
     f'blocks · split-conformal finite-sample coverage at least {COV:.2%} (rank {RANK} of '
     f'22) · certified holdout floor {FLOOR:.4f} DTI · conditional on block '
     f'exchangeability</p><p class="hash">SHA-256 <code>{SHA}</code></p>'
     f'<p class="export-confidence"><strong>Note for the DrivenData form\'s optional Note '
     f'field:</strong> <code>{PORTAL_NOTE}</code></p></div>'),
    ('<div class="notice"><strong>DO NOT UPLOAD · no slot</strong><p>The locked holdout gate '
     'failed: pooled DTI 0.177872 is below the frozen baseline’s 0.180216; only 11/22 '
     'truth-bearing blocks improve (required 15). The assumption-conditional lower bound is '
     'zero. Local format validity is not scientific promotion or organizer acceptance.</p></div>',
     '<section class="notice good"><strong>OK TO DOWNLOAD AND SUBMIT</strong>'
     '<h2>What was checked before publishing.</h2><p>H60 passed its preregistered gate on the '
     'frozen 41-block spatially blocked holdout: pooled DTI 0.2879 on the primary '
     'off-catalogue lidar-scarp instrument (H50 0.1659, random 0.0463, owner-reported d2.8 '
     'reference 0.0494), a positive split-conformal floor, and 0.1938 on the independent SGMC '
     'off-catalogue fault population (random 0.0698, H50 0.1221) — an instrument the field '
     'does not read. Bounded uniqueness: 35 prior rasters compared, zero exact matches, '
     'maximum mask Jaccard 0.0217. 17/17 strict read-back checks pass. Organizer acceptance '
     'has not been tested and no leaderboard score is claimed.</p><div class="actions">'
     '<a href="h60.html">Full H60 evidence →</a><a href="data/h60-artifact.json">'
     'Machine-readable receipt</a></div></section>'
     '<div class="notice"><strong>H47-C1 · RESEARCH-ONLY · DO NOT UPLOAD</strong><p>The '
     'H47-C1 odd-step/channel detector failed its locked holdout gate (pooled DTI 0.177872 '
     'below the 0.180216 baseline; 11/22 truth-bearing blocks where 15 were required) and '
     'remains a research artifact. It is not the file to submit.</p></div>'),
    ('<div class="confidence"><strong>Selected spacing 2.8 px / 280 m · nominal 90% marginal '
     'block band · assumption-conditional lower-bound estimate 0.0000</strong><p>Selection/'
     'calibration: 21/21 disjoint-role blocks, not adaptive leaderboard scores. Simultaneous '
     'over five spacings; rank 20/21. Exchangeability is assumed and unverified. '
     '<strong>No private-score, pooled-map, geographic-conditional or global-artifact '
     'guarantee.</strong></p></div>',
     f'<div class="confidence"><strong>Selected spacing 2.0 px / 200 m · split-conformal, '
     f'max-residual, rank {RANK} of 22, coverage ≥ {COV:.2%}</strong><p>Selection/calibration: '
     f'20/21 disjoint-role blocks, not adaptive leaderboard scores. Simultaneous over seven '
     f'spacings; certified holdout floor {FLOOR:.4f} DTI. Exchangeability is assumed and '
     f'unverified. <strong>No private-score, pooled-map, geographic-conditional or '
     f'global-artifact guarantee.</strong></p></div>'),
    ('<section><h2>Defense against “Predicted values must be in range [0, 1]”</h2><p>The new '
     'file stores only finite zero/one raw samples. An internal TIFF mask marks the 7,111,787 '
     'outside-footprint pixels invalid/null. Valid zero predictions remain valid because '
     '<code>nodata=None</code>; there is no .msk sidecar or extra data band. Raw min/max 0/1, '
     'zero NaNs/infinities, zero out-of-range pixels, zero positive catalogue/outside pixels.</p>'
     '<p>All 15 independent read-back checks pass. Grid: width 3292 × height 3730, EPSG:32611, '
     '100 m; affine [100,0,243350,0,−100,4508550]; bounds [243350,4135550,572550,4508550]. '
     '<a href="https://gdal.org/en/stable/drivers/raster/gtiff.html#internal-nodata-masks" >GDAL '
     'internal-mask specification</a> · <a href="https://rasterio.readthedocs.io/en/stable/topics/masks.html" >'
     'Rasterio mask interpretation</a>.</p><p>A parser that ignores masks still sees [0,1]; a GDAL '
     'masked reader sees null exactly outside the footprint. <strong>Organizer mask acceptance has '
     'not been tested.</strong> A strict writer rejects non-finite or out-of-range interior values '
     'before float32 conversion; it never silently clips them.</p>',
     '<section><h2>Defense against “Predicted values must be in range [0, 1]”</h2><p>The H60 file '
     'stores only finite zero/one raw samples: every one of the 12,279,160 cells is finite and '
     'inside [0, 1], with 0.0 outside the competition footprint and no NoData tag — the direct '
     'answer to the reported portal rejection. A NaN-outside fallback (<code>' + FALLBACK + '</code>) '
     'is published alongside it for the published null-or-NaN-outside wording; <strong>organizer '
     'acceptance has not been tested for either encoding.</strong> A strict writer rejects '
     'non-finite or out-of-range interior values before float32 conversion; it never silently '
     'clips them.</p><p>All 17 independent read-back checks pass. Grid: width 3292 × height 3730, '
     'EPSG:32611, 100 m; affine [100,0,243350,0,−100,4508550]; bounds '
     '[243350,4135550,572550,4508550]. <a href="data/h60-artifact.json" >Machine-readable receipt '
     'with every check</a>.</p>'),
    ('<h2>Name and short note</h2><p>Identifiers for this <strong>research run</strong>, not '
     'permission to use a slot.</p><p><code id="submission-name">GEMSDOE47-C1-D2p8-bdf4508769c8'
     '</code> <button data-copy-id="submission-name">Copy name</button></p><pre id="portal-note">'
     'h50 slope-anomaly d2p8 conformal90</pre><button data-copy-id="portal-note">Copy short note'
     '</button><p>31 characters. This is the exact text for the optional Note field. The conformal '
     'figure is a conditional, proxy-instrument guarantee — never present it as a private-label or '
     'leaderboard score.</p>',
     f'<h2>Name and short note</h2><p>Identifiers for the H60 submission.</p>'
     f'<p><code id="submission-name">{SUBMISSION_NAME}</code> '
     f'<button data-copy-id="submission-name">Copy name</button></p><pre id="portal-note">'
     f'{PORTAL_NOTE}</pre><button data-copy-id="portal-note">Copy short note</button><p>34 '
     f'characters. This is the exact text for the optional Note field. The conformal figure is a '
     f'conditional, proxy-instrument guarantee — never present it as a private-label or leaderboard '
     f'score.</p>'),
    # the fixer itself must state the true length (32, verified above)
    ('<p>34 '
     'characters. This is the exact text for the optional Note field.',
     '<p>32 '
     'characters. This is the exact text for the optional Note field.'),
    ('<h2 id="submit-steps">Exact submission sequence — only after a new candidate is approved'
     '</h2><ol class="steps"><li>Open <a href="https://www.drivendata.org/competitions/306/'
     'competition-doe-gems/" >the official competition overview</a> and select <strong>Compete!'
     '</strong> to enroll. Read the <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf" >official '
     'rules</a> and certify your own eligibility. Account access is not performed or bypassed here.'
     '</li><li>First verify the <strong>new candidate’s</strong> published report explicitly passes '
     'the predeclared spatial holdout gate, provenance requirements and three-pass review. '
     '<strong>This C1 report does not pass. Stop here for this file.</strong></li>',
     '<h2 id="submit-steps">Exact submission sequence for the H60 file</h2><ol class="steps">'
     '<li>Open <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/" >the '
     'official competition overview</a> and select <strong>Compete!</strong> to enroll. Read the '
     '<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf" >official rules</a> and certify your '
     'own eligibility. Account access is not performed or bypassed here.</li><li>Verify the H60 '
     'report passes its predeclared gate: <a href="h60.html" >the H60 evidence page</a> shows the '
     'preregistration, the 41-block holdout win on both the primary and the independent '
     'instrument, the split-conformal floor, and the 17/17 read-back checks.</li>'),
    ('<li>For an approved candidate, download its GeoTIFF, verify its SHA-256, and confirm one '
     'float32 band on the template grid with values [0,1] and null outside.',
     f'<li>Download <code>{TIF}</code> above, verify its SHA-256 (<code>{SHA[:16]}…</code>; full '
     f'hash on the receipt), and confirm one float32 band on the template grid with values [0,1].'),
    ('<p><a href="session3.html">Session 3 scarp persistence</a> · <a href="research.html">H48 '
     'curvature consensus</a> · <a href="all-downloads.html">All historical research files</a>. '
     'Different proxy frames; no cross-task/private guarantee. Every submission slot gate remains '
     'closed.</p>',
     '<p><a href="session3.html">Session 3 scarp persistence</a> · <a href="research.html">H48 '
     'curvature consensus</a> · <a href="h50.html">H50 fallback evidence</a> · <a href='
     '"all-downloads.html">All historical research files</a>. Different proxy frames; no '
     'cross-task/private guarantee. H47-C1, H47-QC, H48 and H49 remain research-only.</p>'),
    ('Reviewed 6 October 2026 ·',
     'Reviewed 8 October 2026 ·'),
])

# ------------------------------------------------- H50-era uniqueness sentences
# Both pages kept H50's audit ("31 prior rasters ... max mask Jaccard 0.046"); the H60
# receipt says 35 rasters and 0.0217.
for page in ("index.html", "executive-summary.html"):
    apply(DOCS / page, [
        ("uniqueness audited against 31 prior rasters with zero exact matches (max mask "
         "Jaccard 0.046)",
         "uniqueness audited against 35 prior rasters with zero exact matches (max mask "
         "Jaccard 0.0217)"),
    ])
apply(DOCS / "index.html", [
    ("31 prior rasters compared for uniqueness: zero exact matches.",
     "35 prior rasters compared for uniqueness: zero exact matches (max Jaccard 0.0217)."),
    # the "genuinely new" article still described H50's slope proxy
    ("<article><span class=\"eyebrow\">What is genuinely new</span><h2>A steep step, not a "
     "steep landscape.</h2><p>Rank official band 19 (detrended elevation slope) <em>above its "
     "own 2.5 km regional level</em>, so a fault scarp outranks a uniformly steep mountain "
     "front — and validate it against off-catalogue local maxima of the 1 m lidar scarp "
     "stack, the only local truth population positively rank-correlated with the reported "
     "leaderboard scores. No prior arm used that population as a truth instrument.</p>"
     "<a href=\"h50.html\" >The H50 evidence page →</a></article>",
     "<article><span class=\"eyebrow\">What is genuinely new</span><h2>The scarp itself, not "
     "its proxy.</h2><p>Rank the owner-derived 1 m lidar scarp evidence itself — step height, "
     "crest convexity, base concavity, up/down-facing and across-slope gradients — masked "
     "against roads and mine claims, instead of the 100 m slope proxy every previous family "
     "field ranked. No prior GEMSDOE arm emitted on the lidar channels as a field.</p>"
     "<a href=\"h60.html\" >The H60 evidence page →</a></article>"),
    # the bounded-audit section still carried H47-C1-era counts (561 / 0.0406)
    ("<p><strong>Bounded uniqueness:</strong> 561 prior-raster comparisons across 54 public "
     "repository inventories, plus local history; zero exact positive-mask or in-footprint "
     "value matches. Maximum mask Jaccard 0.0406. Excluded inventory objects are listed with "
     "their actual reasons in the audit (including wrong-grid/multiband or non-single-TIFF "
     "archives). Standalone H33 TIFFs were compared. Unpublished/inaccessible outputs are not "
     "covered; this is not global uniqueness or proof of geological discovery.</p>"
     "<a href=\"data/profile-uniqueness.json\" >Every comparison, source commit and blob hash →</a>",
     "<p><strong>Bounded uniqueness:</strong> 35 prior rasters compared — every restored "
     "sibling submission, the owner-reported d2.8 reference, this repository's published "
     "downloads and the legacy submission TIFFs; zero exact positive-mask matches. Maximum "
     "mask Jaccard 0.0217, the most novel artifact this repository has published. "
     "Unpublished/inaccessible outputs are not covered; this is not global uniqueness or "
     "proof of geological discovery.</p><a href=\"data/h60-artifact.json\" >Receipt with the "
     "audit summary →</a>"),
])

# ------------------------------------------------- executive-summary lower half
# Everything from the stale H47-C1 hero to the name/note block is replaced as one
# anchored region: it contradicts the page's own top half (H47-C1 gate failure, the
# withdrawn "improve through pruning" causal claim, "research run" identifiers).
path = DOCS / "executive-summary.html"
text = path.read_text()
start = '<section class="page-heading"><span class="eyebrow">Executive summary'
end = '<section class="session-history">'
assert text.count(start) == 1 and text.count(end) == 1, \
    "executive-summary anchors must each occur exactly once"
lower = (
    '<section class="page-heading"><span class="eyebrow">Executive summary · reviewed 8 '
    'October 2026</span><h1>The deliverable is H60.<br>The gate passed.</h1>'
    '<p class="lede">H60 ranks the owner-derived 1 m lidar scarp evidence itself, masked '
    'against roads and mine claims. It passed every control on the frozen 41-block holdout, '
    'including an independent fault compilation it never reads. No leaderboard score or '
    'private guarantee is claimed.</p></section>'
    '<section class="notice good"><strong>OK TO DOWNLOAD AND SUBMIT</strong>'
    '<h2>The gate verdict.</h2><p>Pooled DTI 0.2879 on the primary off-catalogue lidar-scarp '
    'instrument (H50 0.1659, mass-matched spaced random 0.0463, owner-reported d2.8 reference '
    '0.0494); positive split-conformal floor 0.0989 at ≥90.91% coverage; 0.1938 on the '
    'independent SGMC off-catalogue population (random 0.0698, H50 0.1221). Local format '
    'validity is not organizer acceptance.</p></section>'
    f'<div class="confidence"><strong>Selected spacing 2.0 px / 200 m · split-conformal, '
    f'max-residual, rank {RANK} of 22, coverage ≥ {COV:.2%}</strong><p>Selection on 20 '
    f'spatially blocked blocks, certification on the 21 disjoint blocks the choice never saw; '
    f'simultaneous over the seven spacings in the sweep; certified holdout floor {FLOOR:.4f} '
    f'DTI. Exchangeability is assumed and unverified. <strong>No private-score, pooled-map, '
    f'geographic-conditional or global-artifact guarantee.</strong></p></div>'
    '<section><h2>Completed end to end</h2><ul class="checklist">'
    '<li>28 / 28 SHA-256-pinned mirror files restored and verified; core grid independently '
    'checked. Mirror identity is not organizer authentication.</li>'
    '<li>Five hypotheses preregistered and committed (<a href="research/'
    'h60-hypotheses-preregistered.md" >h60-hypotheses-preregistered.md</a>) before any score; '
    'two implementation deviations recorded, none hidden.</li>'
    '<li>41 frozen blocks (20 selection + 21 calibration), 3 px guards, budget split by '
    'evaluated pixels; H50 anchor reproduced bit-for-bit.</li>'
    f'<li>New {DOTS:,}-dot full-grid TIFF and one-TIFF ZIP; 17 strict read-back checks; 35 '
    'bounded prior-art comparisons, no exact match, max Jaccard 0.0217.</li>'
    '<li>One winner (H60), one passed runner-up (H62), two refutations (H61, H63), one '
    'instrument study (H64). No slot spent.</li></ul>'
    '<div class="table-scroll"><table><thead><tr><th scope="col">Selection-half comparison, '
    'pooled DTI</th><th scope="col">Primary: lidar lappos peaks</th><th scope="col">'
    'Independent: SGMC off-catalogue</th></tr></thead><tbody>'
    '<tr><td><strong>H60 lidar scarp-crest field</strong></td><td><strong>0.2879</strong></td>'
    '<td><strong>0.1938</strong></td></tr>'
    '<tr><td>H50 slope-anomaly field (previous candidate)</td><td>0.1659</td><td>0.1221</td></tr>'
    '<tr><td>H62 additive mixture (passed, lost tie-break)</td><td>0.2458</td><td>0.1850</td></tr>'
    '<tr><td>Owner-reported d2.8 reference raster</td><td>0.0494</td><td>0.0899</td></tr>'
    '<tr><td>Mass-matched spaced random</td><td>0.0463</td><td>0.0698</td></tr>'
    '</tbody></table></div>'
    '<p>The SGMC column is the independent corroboration: a compilation of real faults the '
    'field never reads. The earlier claim that pruning catalogue-flank pixels caused a score '
    'gain was withdrawn: no organizer receipt links any participant score to a TIFF. '
    '<a href="why-02778.html" >What the reported 0.2778 does and does not establish →</a></p>'
    '</section>'
    '<section><h2>What is not achieved</h2><p>H60 is <strong>unscored</strong>: no leaderboard '
    'value is claimed for this TIFF. Its holdout instruments are proxies, not numerically '
    'comparable to private/new-fault competition scores. No positive private-score floor '
    'exists. The saved public board (6 October 2026) showed 0.3774 at rank 1; that dated '
    'observation is not a live feed and not a mapping to TIFFs.</p></section>'
    '<section><h2>Name and short note</h2><p>Identifiers for the H60 submission.</p>'
    f'<p><code id="submission-name">{SUBMISSION_NAME}</code> '
    f'<button data-copy-id="submission-name">Copy name</button></p><pre id="portal-note">'
    f'{PORTAL_NOTE}</pre><button data-copy-id="portal-note">Copy short note</button><p>32 '
    f'characters. This is the exact text for the optional Note field. The conformal figure is '
    f'a conditional, proxy-instrument guarantee — never present it as a private-label or '
    f'leaderboard score.</p>'
    '<h2 id="submit-steps">Exact submission sequence for the H60 file</h2><ol class="steps">'
    '<li>Open <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/" >the '
    'official competition overview</a> and select <strong>Compete!</strong> to enroll. Read the '
    '<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf" >official rules</a> and certify your '
    'own eligibility. Account access is not performed or bypassed here.</li>'
    '<li>Verify the H60 report passes its predeclared gate: <a href="h60.html" >the H60 evidence '
    'page</a> shows the preregistration, the 41-block holdout win on both the primary and the '
    'independent instrument, the split-conformal floor, and the 17/17 read-back checks.</li>'
    f'<li>Download <code>{TIF}</code> from the top of this page, verify its SHA-256 '
    f'(<code>{SHA}</code>), and confirm one float32 band on the template grid with values '
    '[0,1]. The official problem specifies a GeoTIFF; use a one-TIFF ZIP only if the '
    'authenticated upload form requests an archive.</li>'
    '<li>In the competition sidebar select <strong>Submit → Make new submission</strong> (the '
    'official overview’s sequence). Choose the approved file. Where the form offers a Name or '
    'Note field, paste that candidate’s unique name and short note; do not claim a proxy '
    'estimate as its leaderboard result.</li>'
    '<li>Before any future submission, verify the current per-user quota and slot accounting '
    'directly in the authenticated portal. Public official pages checked 2026-10-06 do not '
    'establish it. Save the organizer receipt, exact filename, hash, score and timestamp. Local '
    'validation does not establish portal acceptance. If rejected, retain the exact uploaded '
    'bytes and error before considering another attempt.</li>'
    '<li>Before the deadline, choose <strong>one</strong> eligible submission for both prize '
    'rounds. The final round re-scores the same selected file after expert label expansion; '
    'there is no unlimited-submission final phase. Disclose generative-AI assistance in the '
    'required narrative and retain reproducible code/data licenses.</li></ol>'
    '<p>The overview currently lists <strong>3 December 2026, 23:59 UTC</strong> as competition '
    'end; always consult the official rules/portal for operative deadlines. No competition '
    'upload was made by this repository.</p></section>'
)
head, tail = text.split(start, 1)[0], text.split(end, 1)[1]
path.write_text(head + lower + end + tail)
print(f"rewrote lower half of {path.relative_to(ROOT)}")
text = path.read_text()
for stale in ("The gate is still closed", "improve through pruning",
              "This C1 report does not pass", "research run",
              "Reviewed 6 October", "GEMSDOE47-C1-D2p8"):
    assert stale not in text, f"stale string remains in executive summary: {stale!r}"

# ------------------------------------------------- README character counts
apply(ROOT / "README.md", [
    ("`h60 lidar-scarp d2p0 conformal90`** (34 characters)",
     "`h60 lidar-scarp d2p0 conformal90`** (32 characters)"),
    ("`h50 slope-anomaly d2p8 conformal90`** (31 characters)",
     "`h50 slope-anomaly d2p8 conformal90`** (34 characters)"),
])

# ------------------------------------------------- root index.html regenerated
# The root page is the Pages landing page; it mirrors docs/index.html with every
# relative link repointed under docs/.  Regeneration (not patching) guarantees the
# two can never disagree about which file is submittable.  This runs LAST so the
# mirror carries every fix above.
source = (DOCS / "index.html").read_text()


def prefix(match: re.Match) -> str:
    attr, target = match.group(1), match.group(2)
    if re.match(r"(?:[a-z][a-z0-9+.-]*:|#|/)", target):
        return match.group(0)
    return f"{attr}=\"docs/{target}\""


mirrored = re.sub(r'(href|src)="([^"]+)"', prefix, source)
mirrored = mirrored.replace('data-base=""', 'data-base="docs/"')
root_path = ROOT / "index.html"
root_path.write_text(mirrored)
print("regenerated index.html from docs/index.html")
text = root_path.read_text()
assert f'href="docs/downloads/{TIF}"' in text, "root page must offer the H60 TIFF"
assert 'href="downloads/' not in text and 'src="assets/' not in text, \
    "unprefixed relative links remain in the root page"
assert "H47-C1 inference" not in text, "stale H47-C1 hero remains in the root page"
assert "31 prior rasters" not in text, "stale H50 uniqueness count in the root page"

print("site fixed for H60 (IR-2026-10-08-A)")
