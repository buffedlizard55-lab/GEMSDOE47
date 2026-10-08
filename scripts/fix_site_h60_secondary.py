#!/usr/bin/env python3
"""Sweep H50-era site chrome on the secondary pages to H60 (IR-2026-10-08-A).

Run after scripts/fix_site_h60.py.  Covers what the first fixer left:

* the shared status bar (13 pages still say "H50 · OK TO DOWNLOAD AND SUBMIT");
* the shared "Preserved concurrent research" footer line (9 pages still say "Every
  submission slot gate remains closed", false now that H60 is submittable);
* docs/portal-checklist.html (stale C1 steps + "research run" identifiers);
* docs/irregularities.html (the four session-6 notices, lede + footer dates).

h50.html keeps its own H50 status bar (it is H50's evidence page).  Historical
footers elsewhere keep their review dates -- only pages this session actually
corrects get a new date.  Every replacement asserts it matched.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

OLD_BAR = ('<strong>H50 · OK TO DOWNLOAD AND SUBMIT</strong><span>The H47/H48/H49 artifacts '
           'described on this page are research-only and are not the file to upload.</span>')
NEW_BAR = ('<strong>H60 · OK TO DOWNLOAD AND SUBMIT</strong><span>The H50 fallback is also '
           'valid; the H47/H48/H49 artifacts described on this page are research-only and are '
           'not the file to upload. See the landing page.</span>')

OLD_GATE_LINE = ('Different proxy frames; no cross-task/private guarantee. Every submission slot '
                 'gate remains closed.</p>')
NEW_GATE_LINE = ('Different proxy frames; no cross-task/private guarantee. H47-C1, H47-QC, H48 and '
                 'H49 remain research-only; the current file to submit is H60 '
                 '(see the landing page).</p>')


def apply(path: Path, pairs: list[tuple[str, str]]) -> None:
    text = path.read_text()
    changed = False
    for old, new in pairs:
        found = text.count(old)
        if found < 1:
            if new in text:
                continue  # already applied by an earlier run
            raise SystemExit(f"{path.relative_to(ROOT)}: no match for {old[:70]!r}")
        text = text.replace(old, new)
        changed = True
    if changed:
        path.write_text(text)
    print(f"{'updated' if changed else 'already current'} {path.relative_to(ROOT)}")


bar_pages = ["COMPLIANCE.html", "REMAINING_WORK.html", "RESULTS.html", "analysis.html",
             "evidence.html", "h47b-mask-audit-20261006.html", "hypotheses.html",
             "irregularities.html", "knowledge.html", "leaderboard.html",
             "portal-checklist.html", "session3.html", "sources.html"]
for name in bar_pages:
    apply(DOCS / name, [(OLD_BAR, NEW_BAR)])

gate_pages = ["analysis.html", "evidence.html", "hypotheses.html", "irregularities.html",
              "knowledge.html", "leaderboard.html", "method.html", "portal-checklist.html",
              "sources.html"]
for name in gate_pages:
    apply(DOCS / name, [(OLD_GATE_LINE, NEW_GATE_LINE)])

# ------------------------------------------------- portal-checklist specifics
apply(DOCS / "portal-checklist.html", [
    ("<h2 id=\"submit-steps\">Exact submission sequence — only after a new candidate is approved</h2>",
     "<h2 id=\"submit-steps\">Exact submission sequence for the H60 file</h2>"),
    ("First verify the <strong>new candidate’s</strong> published report explicitly passes "
     "the predeclared spatial holdout gate, provenance requirements and three-pass review. "
     "<strong>This C1 report does not pass. Stop here for this file.</strong>",
     "Verify the H60 report passes its predeclared gate: <a href=\"h60.html\" >the H60 evidence "
     "page</a> shows the preregistration, the 41-block holdout win on both the primary and the "
     "independent instrument, the split-conformal floor, and the 17/17 read-back checks."),
    ("<li>For an approved candidate, download its GeoTIFF, verify its SHA-256, and confirm one "
     "float32 band on the template grid with values [0,1] and null outside.",
     "<li>Download <code>gems47-h60-lidarscarp-s2p0-20261007-allfinite.tif</code> from the "
     "landing page, verify its SHA-256 (<code>4ee074230a305fce6768012fc33380bf196c89170e70050a77c"
     "f4a44d74ef14c</code>), and confirm one float32 band on the template grid with values "
     "[0,1]."),
    ("<h2>Name and short note</h2><p>Identifiers for this <strong>research run</strong>, not "
     "permission to use a slot.</p><p><code id=\"submission-name\">GEMSDOE47-C1-D2p8-bdf4508769c8"
     "</code> <button data-copy-id=\"submission-name\">Copy name</button></p><pre id=\"portal-note\">"
     "h50 slope-anomaly d2p8 conformal90</pre><button data-copy-id=\"portal-note\">Copy short note"
     "</button><p>31 characters. This is the exact text for the optional Note field.",
     "<h2>Name and short note</h2><p>Identifiers for the H60 submission.</p>"
     "<p><code id=\"submission-name\">GEMSDOE47-H60-lidarscarp-s2p0-20261007</code> "
     "<button data-copy-id=\"submission-name\">Copy name</button></p><pre id=\"portal-note\">"
     "h60 lidar-scarp d2p0 conformal90</pre><button data-copy-id=\"portal-note\">Copy short note"
     "</button><p>32 characters. This is the exact text for the optional Note field."),
    ("Reviewed 6 October 2026 ·", "Reviewed 8 October 2026 ·"),
])

# ------------------------------------------------- irregularities.html notices
notice = (
    '<section class="notice" id="ir-2026-10-08-a">\n'
    '<strong>IR-2026-10-08-A · stale landing pages corrected (H60)</strong>\n'
    '<p>The session-5 site update missed the pages visitors land on: the root '
    '<code>index.html</code> still offered the research-only H47-C1 TIFF, '
    '<code>submit.html</code> still described the H47-C1 run, the executive summary lower '
    'half still carried the H47-C1 hero and the withdrawn pruning claim, and several pages '
    'kept H50 titles, counts and audit numbers. All are rewritten to H60 by the '
    'assertion-checked <code>scripts/fix_site_h60.py</code>; the root page is regenerated '
    'from <code>docs/index.html</code> and pinned by a regression test. No TIFF bytes '
    'changed.</p>\n</section>\n'
    '<section class="notice" id="ir-2026-10-08-b">\n'
    '<strong>IR-2026-10-08-B · portal-note character counts corrected</strong>\n'
    '<p>The H60 note is 32 characters (not 34) and the H50 note is 34 (not 31), verified '
    'from the literal strings. Corrected everywhere; the fixer asserts both lengths.</p>\n'
    '</section>\n'
    '<section class="notice" id="ir-2026-10-08-c">\n'
    '<strong>IR-2026-10-08-C · H60 screen aggregation bug fixed in the script</strong>\n'
    '<p>The committed <code>run_h60_screen.py</code> still divided emitted mass by 7; the fix '
    'is now in the script itself, a full rerun reproduced every score, gate verdict and the '
    'spacing history byte-for-byte, and the receipt records the rerun plus the new script '
    'digest. No score changed.</p>\n</section>\n'
    '<section class="notice" id="ir-2026-10-08-d">\n'
    '<strong>IR-2026-10-08-D · repo-wide lint is red under current ruff (hygiene)</strong>\n'
    '<p><code>ruff check .</code> reports 65 pre-existing errors at <code>main</code>, so the '
    'handoff claim of a clean tree is stale. All session-6 files are individually clean; the '
    'pre-existing errors are left for a dedicated lint pass.</p>\n</section>\n'
)
apply(DOCS / "irregularities.html", [
    ('<section class="page-heading"><span class="eyebrow">Own the corrections</span>',
     notice + '<section class="page-heading"><span class="eyebrow">Own the corrections</span>'),
    ("Updated 7 October 2026 UTC.", "Updated 8 October 2026 UTC."),
    ("Reviewed 6 October 2026 ·", "Reviewed 8 October 2026 ·"),
])

print("secondary pages swept to H60")
