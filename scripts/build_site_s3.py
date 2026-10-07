#!/usr/bin/env python3
"""Render the session-3 markdown pages to HTML using main's existing site skin.

`docs/.nojekyll` is present, so GitHub Pages serves `docs/` as plain static files: a `.md` link
shows raw markdown text.  Main's own convention is a hand-written `.md`/`.html` pair per page
(`analysis.md` + `analysis.html`, `method.md` + `method.html`, ...) sharing `assets/site.css` and
one nav.  This script produces the `.html` half for the pages session 3 added, so they render in
the same skin and the nav is identical on every page.

It renders the markdown pages listed in `PAGES`; H49's separate updater owns only explicitly marked
regions in existing HTML pages. `scripts/build_site_s3.py --check` permits rendered session-owned
pages and compares all other docs byte-for-byte with `main`, allowing only H49 marker bodies to differ.

Run:  python3 scripts/build_site_s3.py [--check]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import time
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

# Markdown pages maintained by this research update, in navigation order. Several are deliberately
# rendered into existing main-site filenames; their source and output are explicitly declared owned.
# (markdown file, nav label, meta description). tests/test_site.py requires every page under
# docs/ to carry exactly one meta description, lang="en" and a non-empty title; session 3's
# pages are held to main's own site-integrity suite rather than exempted from it.
PAGES = [
    ("session3.md", "Session 3 — submission",
     "Session 3 of GEMSDOE47: the downloadable candidate GeoTIFF, its SHA-256, the uniqueness "
     "assertion against all 18 reference artifacts, the random and shifted controls, and the "
     "split-conformal floor quoted next to the chosen spacing."),
    ("HOW_TO_SUBMIT.md", "How to submit — future candidate",
     "One-click H49 research download, independent format verification, a closed current slot gate, "
     "and exact future submission steps that require a prospectively validated candidate."),
    ("RESULTS.md", "Results and score-attribution correction",
     "H33 score-to-TIFF attribution limits, exact mask nesting, H49 public-proxy and paired-holdout "
     "results, nominal split-conformal assumptions, strict current TIFF format receipt, and bounded "
     "uniqueness scope."),
    ("H49_RESULTS.md", "H49 results",
     "The H49 round in full: blocked public-proxy sweeps, nominal fixed-arm split-conformal "
     "diagnostics, paired-improvement results, the closed promotion gate, exact TIFF validation, "
     "bounded uniqueness scope, and limitations."),
    ("RESEARCH_HYPOTHESES.md", "Ranked H49 follow-up hypotheses",
     "Four ranked geological follow-up hypotheses, their layers and physical signatures, novelty, "
     "qualitative effect and cost, official data-access status, and holdout/conformal promotion gates."),
    ("why-02778.md", "Why 0.2778",
     "Evidence audit of the H33 0.2778 score label: exact raster nesting is verified, but no "
     "organizer receipt maps the score to those bytes; metric reasoning and limitations are stated."),
    ("hypotheses-s3.md", "Hypotheses H47",
     "Five new geological hypotheses ranked by expected DTI improvement over implementation cost, "
     "the spatially-blocked validation gate, and five refuted candidates with their numbers."),
    ("research.md", "Research base and sources",
     "Reusable research knowledge and official source links, including access limits, score-attribution "
     "correction, and evidence boundaries."),
    ("REMAINING_WORK.md", "Remaining work and limitations",
     "Current H49 slot decision, exact artifact and audit scope, conformal assumptions, and prioritized "
     "scientific and GitHub work remaining."),
    ("COMPLIANCE.md", "Compliance and review",
     "Criterion-by-criterion review of the complete available brief, the current artifact, validation, "
     "three review passes, limitations and GitHub publication status."),
]

# Markdown sources and rendered outputs owned by this research update; they may evolve with receipts.
SESSION_OWNED_DOCS = {
    f"docs/{path}"
    for md, _label, _description in PAGES
    for path in (md, md.replace(".md", ".html"))
}
SESSION_OWNED_DOCS.update({
    "docs/method.md",
    "docs/next-session.md",
    "docs/data/current-artifact.json",
    "docs/data/pinned-public-inventory-uniqueness.json",
    "docs/downloads/gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.json",
    "docs/downloads/gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.tif",
    "docs/downloads/gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.txt",
    "docs/downloads/gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.zip",
    "docs/research/h49-hypotheses-preregistered.md",
    "docs/research/h49b-instrument-b-preregistration.md",
})

# These pre-existing HTML pages contain narrowly scoped evidence-driven H49 marker regions.
# Only the marker bodies may differ from main; the rest of each page must remain byte-for-byte stable.
H49_MARKER_DOCS = {
    "docs/index.html", "docs/executive-summary.html", "docs/submit.html",
    "docs/analysis.html", "docs/evidence.html", "docs/hypotheses.html",
    "docs/irregularities.html", "docs/knowledge.html", "docs/leaderboard.html",
    "docs/method.html", "docs/portal-checklist.html", "docs/sources.html",
    "docs/all-downloads.html",
}
H49_MARKER_RE = re.compile(r"<!--h49:([\w-]+)-->(.*?)<!--/h49:\1-->", re.DOTALL)


def without_h49_bodies(text: str) -> str:
    """Normalize evidence blocks while preserving marker names and page structure."""
    # The updater wraps a page's existing description tag in a marker on its first run; normalize
    # both that wrapped form and main's original unmarked tag to a stable placeholder.
    text = re.sub(r"<!--h49:meta-description-->.*?<!--/h49:meta-description-->",
                  '<meta name="description" content="">', text, flags=re.DOTALL)
    # The H49 updater inserts this scoped context note on main's historical H47-C1 method page.
    text = re.sub(r"<!--h49:method-context-->.*?<!--/h49:method-context-->",
                  "", text, flags=re.DOTALL)
    text = re.sub(r"<meta\s+name=[\"']description[\"']\s+content=[\"'][^\"']*[\"']\s*/?>",
                  '<meta name="description" content="">', text, flags=re.IGNORECASE)
    return H49_MARKER_RE.sub(lambda m: f"<!--h49:{m.group(1)}--><!--/h49:{m.group(1)}-->", text)


# Main's nav, reproduced verbatim so the two bodies of work read as one site.
MAIN_NAV = [
    ("index.html", "Home"),   # every other href below stays inside docs/ so that Pages can serve it
    ("executive-summary.html", "Executive summary &amp; how to submit"),
    ("hypotheses.html", "The five hypotheses"),
    ("method.html", "LATI method"),
    ("evidence.html", "Every number"),
    ("irregularities.html", "Irregularities"),
    ("leaderboard.html", "Leaderboard"),
    ("sources.html", "Sources"),
    ("submit.html", "Submit"),
    ("portal-checklist.html", "Portal checklist"),
    ("analysis.html", "Analysis"),
    ("validation-protocol.md", "Validation protocol"),
    ("review-log.md", "Review log"),
    ("next-session.md", "Next session"),
    ("https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/README.md", "README / brief"),
]

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — GEMSDOE47</title>
<meta name="description" content="{description}">
<link rel="stylesheet" href="assets/site.css">
</head>
<body>
<header class="top"><div class="wrap">
  <h1>GEMSDOE47 <span class="badge b-info">RESEARCH RECORD</span></h1>
  <p class="sub">Geologic Enhanced Mapping System (GEMS) Prize Challenge · DrivenData competition
     306 · Nevada Great Basin · 100 m grid · metric = distance-weighted Tversky index (DTI)<br>
     Generated {stamp} by <code>scripts/build_site_s3.py</code> from committed JSON receipts.</p>
  <nav>
{main_nav}
  </nav>
  <nav>
{s3_nav}
  </nav>
</div></header>
<div class="wrap">
<article>
{body}
</article>
</div>
</body>
</html>
"""


def render_nav(active_md: str) -> tuple[str, str]:
    main_links = "\n".join(f'    <a href="{href}">{label}</a>' for href, label in MAIN_NAV)
    s3 = []
    for md, label, _desc in PAGES:
        href = md.replace(".md", ".html")
        cls = ' class="on"' if md == active_md else ""
        s3.append(f'    <a{cls} href="{href}">{label}</a>')
    return main_links, "\n".join(s3)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify unrelated docs are unchanged and marked H49 regions are isolated")
    args = ap.parse_args()

    if args.check:
        files = subprocess.run(["git", "ls-tree", "-r", "--name-only", "main", "docs/"],
                               cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
        bad = []
        owned_checked = 0
        marker_checked = 0
        for f in files:
            p = ROOT / f
            if not p.exists():
                bad.append((f, "deleted"))
                continue
            if f in SESSION_OWNED_DOCS:
                owned_checked += 1
                continue
            head = subprocess.run(["git", "show", f"main:{f}"], cwd=ROOT,
                                  capture_output=True, check=True).stdout
            current = p.read_bytes()
            if head == current:
                continue
            if f in H49_MARKER_DOCS:
                if without_h49_bodies(head.decode()) == without_h49_bodies(current.decode()):
                    marker_checked += 1
                    continue
                bad.append((f, "content outside generated H49 marker bodies changed"))
                continue
            bad.append((f, "modified outside the session-owned page list"))
        if bad:
            print("FAIL: docs changes are outside the declared session scope:")
            for f, why in bad:
                print(f"  {why}: {f}")
            return 1
        print(f"OK: checked {len(files)} tracked main docs files; "
              f"{owned_checked} are declared session-owned pages, "
              f"{marker_checked} existing pages differ only inside H49 markers, "
              "all other tracked docs are byte-identical to main")
        return 0

    stamp = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    written = []
    for md, label, description in PAGES:
        src = DOCS / md
        if not src.exists():
            print(f"[skip] {md} not present")
            continue
        text = src.read_text()
        # strip Jekyll front matter (inert under .nojekyll) and pull the title out of it
        title = label
        if text.startswith("---"):
            end = text.index("\n---", 3)
            front, text = text[3:end], text[end + 4:].lstrip("\n")
            for line in front.splitlines():
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip()
        main_nav, s3_nav = render_nav(md)
        body = markdown.markdown(
            text, extensions=["tables", "fenced_code", "toc", "attr_list", "sane_lists"])
        out = DOCS / md.replace(".md", ".html")
        out.write_text(TEMPLATE.format(title=title, stamp=stamp, main_nav=main_nav,
                                       s3_nav=s3_nav, body=body, description=description))
        written.append(out.name)
        print(f"[render] {md} -> {out.name}  ({out.stat().st_size:,} bytes)")
    print(f"\n{len(written)} pages rendered into main's site skin")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
