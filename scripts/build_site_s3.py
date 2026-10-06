#!/usr/bin/env python3
"""Render the session-3 markdown pages to HTML using main's existing site skin.

`docs/.nojekyll` is present, so GitHub Pages serves `docs/` as plain static files: a `.md` link
shows raw markdown text.  Main's own convention is a hand-written `.md`/`.html` pair per page
(`analysis.md` + `analysis.html`, `method.md` + `method.html`, ...) sharing `assets/site.css` and
one nav.  This script produces the `.html` half for the pages session 3 added, so they render in
the same skin and the nav is identical on every page.

It never touches a file that belongs to main: `scripts/build_site_s3.py --check` lists exactly
which paths it owns and asserts that every other file under `docs/` is byte-identical to `main`.

Run:  python3 scripts/build_site_s3.py [--check]
"""
from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

# The pages session 3 owns, in nav order.  Basenames differ from every page main ships, so
# rendering cannot overwrite main's site.
# (markdown file, nav label, meta description).  tests/test_site.py requires every page under
# docs/ to carry exactly one meta description, lang="en" and a non-empty title; session 3's
# pages are held to main's own site-integrity suite rather than exempted from it.
PAGES = [
    ("session3.md", "Session 3 — submission",
     "Session 3 of GEMSDOE47: the downloadable candidate GeoTIFF, its SHA-256, the uniqueness "
     "assertion against all 18 reference artifacts, the random and shifted controls, and the "
     "split-conformal floor quoted next to the chosen spacing."),
    ("HOW_TO_SUBMIT.md", "How to submit (s3)",
     "Step-by-step upload instructions for the session-3 candidate raster, the exact submission "
     "name and Note text, a verify-it-yourself snippet, and why the file is all-finite with no "
     "nodata tag."),
    ("RESULTS.md", "Results (s3)",
     "Every session-3 measurement with the script that reproduces it: band scale diagnostics, the "
     "two holdout instruments, the transform search, derived-surface skill, the inversion of the "
     "organiser's published scores, and the sweep with its conformal selection."),
    ("why-02778.md", "Why 0.2778",
     "Why GEMSDOE32 h33-2-b2 scored 0.2778, derived from the metric's own algebra and the "
     "organiser's eleven published scores, and whether it can be beaten."),
    ("hypotheses-s3.md", "Hypotheses H47",
     "Five new geological hypotheses ranked by expected DTI improvement over implementation cost, "
     "the spatially-blocked validation gate, and five refuted candidates with their numbers."),
    ("research.md", "Research base (s3)",
     "Session-3 research knowledge base index and every official link cited in the repository, "
     "with a two-level obtainability verdict for each external data source."),
    ("REMAINING_WORK.md", "Remaining work (s3)",
     "Session-3 remaining work and limitations: the unuploaded submission, what the holdout cannot "
     "say, the coverage assumption behind the mass ceiling, and how every claim is checked."),
    ("COMPLIANCE.md", "Compliance (s3)",
     "Pass 3: every acceptance criterion and standing constraint from the brief, checked line by "
     "line, with the artifact that satisfies it or a plain statement that it is not satisfied."),
]

# Main's nav, reproduced verbatim so the two bodies of work read as one site.
MAIN_NAV = [
    ("index.html", "Home"),
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
    ("../README.md", "README / brief"),
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
  <h1>GEMSDOE47 <span class="badge b-info">SESSION 3</span></h1>
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
                    help="assert that no file owned by main was modified")
    args = ap.parse_args()

    if args.check:
        files = subprocess.run(["git", "ls-tree", "-r", "--name-only", "main", "docs/"],
                               cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
        bad = []
        for f in files:
            p = ROOT / f
            if not p.exists():
                bad.append((f, "deleted"))
                continue
            head = subprocess.run(["git", "show", f"main:{f}"], cwd=ROOT,
                                  capture_output=True, check=True).stdout
            if head == p.read_bytes():
                continue
            if f == "docs/index.html":
                # The ONE sanctioned change to a main file: a nav link and a status block, both
                # purely additive.  Verify that rather than trusting the commit message -- every
                # line of main's version must still be present, in the same order.
                want = head.decode().splitlines()
                have = iter(p.read_text().splitlines())
                missing_lines = [ln for ln in want
                                 if not any(ln == h for h in have)]
                if missing_lines:
                    bad.append((f, f"additive check FAILED, {len(missing_lines)} line(s) lost"))
                else:
                    print(f"OK: {f} changed additively -- all {len(want)} of main's lines survive "
                          f"in order ({len(p.read_text().splitlines()) - len(want)} lines added)")
                continue
            bad.append((f, "modified"))
        if bad:
            print("FAIL: main's docs files were changed:")
            for f, why in bad:
                print(f"  {why}: {f}")
            return 1
        print(f"OK: all {len(files)} of main's docs files are byte-identical to main")
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
