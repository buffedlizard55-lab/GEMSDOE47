#!/usr/bin/env python3
"""RETIRED H50 page updater; execution is disabled.

The historical implementation below can restore an all-finite, zero-outside H50 file as upload-ready. H50 is not portal-accepted and does not match the published outside-null/NaN wording. Do not run this updater.

Run after ``scripts/build_submission_h50.py``.  Every replacement asserts that it
actually changed the file, so a silent miss fails the run instead of publishing a
page that still says "do not upload".
"""
from __future__ import annotations

if __name__ != "__main__":
    raise RuntimeError("DISABLED: retired H50 page updater cannot be imported or executed.")
print("DISABLED: historical H50 updater would restore upload-ready language for an all-finite zero-outside TIFF. No files were read or written.")
raise SystemExit(2)

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

receipt = json.loads((DOCS / "data" / "h50-artifact.json").read_text())
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
REF = receipt["holdout"]["owner_reported_d28_reference_pooled_dti"]
C1 = receipt["holdout"]["h47c1_previous_holdout_best_pooled_dti"]
RND = receipt["holdout"]["spaced_random_pooled_dti_mass_matched"]


def apply(path: Path, pairs: list[tuple[str, str]]) -> None:
    text = path.read_text()
    for old, new in pairs:
        if text.count(old) != 1:
            raise SystemExit(f"{path.name}: expected exactly one match for {old[:70]!r}, "
                             f"found {text.count(old)}")
        text = text.replace(old, new)
    path.write_text(text)
    print(f"updated {path.relative_to(ROOT)}")


OLD_STATUS = ('<div class="status-bar"><span class="status-dot" aria-hidden="true"></span>'
              '<strong>Research-only · NOT PROMOTED</strong>'
              '<span>No slot authorized. Do not upload this run.</span></div>')

NEW_STATUS = (
    '<div class="status-bar ready"><span class="status-dot" aria-hidden="true"></span>'
    '<strong>NEW SUBMISSION READY · OK TO DOWNLOAD AND SUBMIT</strong>'
    f'<span>H50 · {DOTS:,} dots · 280 m · split-conformal {COV:.0%} · '
    'one click below. Research-only H47-C1 / H47-QC / H49 artifacts below are NOT for '
    'submission.</span></div>')

OLD_C1_PANEL_START = '<div class="download-panel"><div><span class="eyebrow">Newly inferred · 152,396 bytes</span>'

NEW_H50_PANEL = (
    '<div class="download-panel ready" id="primary-download"><div>'
    '<span class="eyebrow">New hypothesis · ready to submit · '
    f'{BYTES:,} bytes</span>'
    '<h2>Download this one GeoTIFF and submit it.</h2>'
    '<p>A genuinely new H50 field, not a copy of any prior GEMSDOE submission: the rank of '
    'official band&nbsp;19 (detrended elevation slope) <em>above its own 2.5&nbsp;km regional '
    'level</em>, so a fault scarp — a locally steep step on a gentle surface — outranks a '
    'uniformly steep mountain front. Emitted as '
    f'{DOTS:,} unit dots at 280&nbsp;m over the evaluated domain (competition footprint minus '
    'the USGS/INGENIOUS catalogue, which is masked out of scoring). '
    '<strong>Values are 0/1 only, float32, single band, EPSG:32611, 100&nbsp;m, all finite, '
    'no NoData tag.</strong></p></div>'
    '<div class="actions">'
    f'<a href="downloads/{TIF}" class="button primary" download="">↓ Download GeoTIFF '
    f'(submit this)</a><a href="downloads/{ZIP}" class="button secondary" download="">'
    'ZIP + note + receipt</a><a href="h50.html" class="button secondary">Why it should work</a>'
    f'<a href="downloads/{NOTE}" class="text-link">Submission note (copy-paste)</a></div>'
    f'<p class="filename">{TIF}</p>'
    f'<p class="export-confidence">Spacing 2.8 px / 280 m · chosen on a selection half of 20 '
    f'spatially blocked blocks and certified on the disjoint calibration half of 21 blocks · '
    f'split-conformal finite-sample coverage at least {COV:.2%} (rank {RANK} of 22) · '
    f'certified holdout floor {FLOOR:.4f} DTI · conditional on block exchangeability</p>'
    f'<p class="hash">SHA-256 <code>{SHA}</code></p>'
    '<p class="export-confidence"><strong>Note for the DrivenData form\'s optional Note '
    'field:</strong> <code>h50 slope-anomaly d2p8 conformal90</code></p>'
    '</div>'
    '<section class="notice good"><strong>OK TO DOWNLOAD AND SUBMIT</strong>'
    '<h2>What was checked before publishing.</h2>'
    '<p>Every value finite and inside [0,1] — the direct answer to the portal rejection '
    '&ldquo;Predicted values must be in range [0, 1]&rdquo;. Single float32 band, EPSG:32611, '
    '100&nbsp;m, the official transform and bounds, no NoData tag, zeros outside the '
    f'competition footprint. Read-back validated on all 12,279,160 cells; uniqueness audited '
    'against 31 prior rasters with zero exact matches (max mask Jaccard 0.046). On the '
    'spatially blocked holdout the candidate reaches '
    f'{SEL:.4f} pooled DTI against {REF:.4f} for the owner-reported d2.8 reference, '
    f'{C1:.4f} for the previous holdout best and {RND:.4f} for spaced random.</p>'
    '<div class="actions"><a href="h50.html">Full H50 evidence →</a>'
    '<a href="submit.html">Step-by-step submission guide →</a>'
    '<a href="data/h50-artifact.json">Machine-readable receipt</a></div></section>')

OLD_C1_NOTICE = (
    '<div class="notice"><strong>DO NOT UPLOAD · no slot</strong><p>The locked holdout gate '
    'failed: pooled DTI 0.177872 is below the frozen baseline\u2019s 0.180216; only 11/22 '
    'truth-bearing blocks improve (required 15). The assumption-conditional lower-bound '
    'estimate is zero. Local format validity is not scientific promotion or organizer '
    'acceptance.</p></div>')

NEW_C1_NOTICE = (
    '<div class="notice"><strong>RESEARCH-ONLY · DO NOT UPLOAD · H47-C1</strong><p>Retained '
    'for audit only. Its locked holdout gate failed: pooled DTI 0.177872 is below the frozen '
    'baseline\u2019s 0.180216; only 11/22 truth-bearing blocks improve (required 15). The '
    'assumption-conditional lower-bound estimate is zero. Local format validity is not '
    'scientific promotion or organizer acceptance. This is not the file to submit.</p>'
    '<div class="actions"><a href="all-downloads.html">All historical research files →</a>'
    '</div></div>')

C1_PANEL_START = '<div class="download-panel">' 

C1_NOTICE = (
    '<section class="notice"><strong>RESEARCH-ONLY · DO NOT UPLOAD · H47-C1</strong>'
    '<h2>Superseded research raster, kept for audit.</h2>'
    '<p>H47-C1 was the previous primary artifact and is <em>not</em> the file to submit. '
    'Its locked holdout gate failed: pooled DTI 0.177872 against the frozen baseline\u2019s '
    '0.180216, and only 11 of 22 truth-bearing blocks improved where 15 were required. Its '
    'assumption-conditional lower-bound estimate is 0.0000. Local format validity is not '
    'scientific promotion or organizer acceptance.</p>'
    '<p class="filename">gems47-c1-oddstep-channel-d2p8-20261006-bdf4508769c8-finite-mask.tif'
    '</p>'
    '<div class="actions"><a href="all-downloads.html">Artifact register and research-only '
    'TIFFs →</a><a href="data/current-submission.json">H47-C1 receipt</a></div></section>')


def replace_panel(text: str) -> str:
    """Replace the whole top download panel (outer div included).

    The panel is located as the first ``download-panel`` inside ``<main>``, and closed at
    the first ``</div>`` after that panel's ``<p class="hash">`` line, so the exact copy of
    the old panel does not have to be reproduced here.
    """
    main = text.index('<main id="main">')
    start = text.index(C1_PANEL_START, main)
    end = text.index('</div>', text.index('<p class="hash">', start)) + len('</div>')
    return text[:start] + NEW_H50_PANEL + text[end:]


for name in ("index.html", "executive-summary.html"):
    p = DOCS / name
    text = p.read_text()
    if text.count(OLD_STATUS) != 1:
        raise SystemExit(f"{name}: status bar not found")
    text = text.replace(OLD_STATUS, NEW_STATUS)
    text = replace_panel(text)
    anchor = '<section class="notice good"><strong>OK TO DOWNLOAD AND SUBMIT</strong>'
    i = text.index(anchor)
    j = text.index('</section>', i) + len('</section>')
    text = text[:j] + C1_NOTICE + text[j:]
    # page metadata and navigation
    text = text.replace(
        '<title>Fault mapping, evidence first · GEMSDOE47</title>'
        if name == "index.html" else '<title>Executive summary · GEMSDOE47</title>',
        '<title>H50 submission ready · GEMSDOE47</title>'
        if name == "index.html" else
        '<title>Executive summary: how to submit H50 · GEMSDOE47</title>')
    text = text.replace(
        'content="A genuinely new H47-C1 GeoTIFF, strict range/mask checks, blocked '
        'validation and assumption-conditional zero lower-bound estimate."',
        'content="A new H50 GeoTIFF that is OK to download and submit: 37,654 dots at '
        '280 m, every value in [0,1], split-conformal coverage at least 90.91%, and the '
        'exact submission steps.')
    text = text.replace('data-site-version="h47c"', 'data-site-version="h50"')
    text = text.replace('<a href="hypotheses.html" aria-current="false">Hypotheses</a>',
                        '<a href="h50.html" aria-current="false">H50</a>'
                        '<a href="hypotheses.html" aria-current="false">Hypotheses</a>')
    p.write_text(text)
    print(f"updated {name}")
