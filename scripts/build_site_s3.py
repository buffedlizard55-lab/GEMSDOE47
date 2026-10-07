#!/usr/bin/env python3
"""Render the session-3 markdown pages to HTML using main's existing site skin.

`docs/.nojekyll` is present, so GitHub Pages serves `docs/` as plain static files: a `.md` link
shows raw markdown text.  Main's own convention is a hand-written `.md`/`.html` pair per page
(`analysis.md` + `analysis.html`, `method.md` + `method.html`, ...) sharing `assets/site.css` and
one nav.  This script produces the `.html` half for the pages session 3 added, so they render in
the same skin and the nav is identical on every page.

It does not rewrite the reviewed static pages. `--check` rejects any main-owned docs change
outside explicit status-reconciliation and Pages-link-repair allowlists; core H50/H51/H49 status
and receipt sentinels are checked there, while the site tests check links, hashes, TIFF read-back
and page wording.

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
    ("session3.md", "Session 3 — historical research",
     "Historical Session 3/H47-C1 research results, exact artifact hash, bounded uniqueness review, "
     "random and shifted controls, and the failed holdout gate. This is not the current candidate."),
    ("HOW_TO_SUBMIT.md", "H50 local review and guarded submission checklist",
     "H50's locally promoted public-proxy evidence, NaN-outside serialized read-back, exact suggested "
     "Name and Note, conditional conformal limits, and guarded submission steps. No organizer acceptance "
     "or competition-slot authorization is established."),
    ("RESULTS.md", "Historical results (s3)",
     "Historical H47-C1 measurements with scripts and frozen gate: band-scale diagnostics, holdout "
     "instruments, transform search, derived-surface skill, and the corrected spacing selection. "
     "H47-C1 is not the current candidate."),
    ("H49_RESULTS.md", "H49 results",
     "The H49 round in full: the signed-polarity scarp field and the preregistered arm, the "
     "spacing/density sweep on both instruments, the split-conformal floor quoted next to the "
     "chosen spacing, the paired block tests, and every arm that lost."),
    ("why-02778.md", "What the reported 0.2778 does and does not establish",
     "The participant-level 0.2778 leaderboard observation is not authenticated to the H33-2-B2 "
     "TIFF. Owner-reported score/file attribution and all dependent analyses remain conditional."),
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

# Deliberate current-status reconciliation against the main snapshot. These pages previously
# presented H50 as organizer-ready or H51 as independently validated. The allowlist is narrow and
# explicit; changes outside it still fail --check. Core page/receipt assertions below ensure the
# correction is present, and tests/test_site.py exercises exact file bytes and all local links.
INTENTIONAL_STATUS_RECONCILIATION = {
    "docs/COMPLIANCE.html", "docs/COMPLIANCE.md", "docs/H49_RESULTS.html", "docs/H49_RESULTS.md",
    "docs/HOW_TO_SUBMIT.html", "docs/HOW_TO_SUBMIT.md", "docs/README.md",
    "docs/REMAINING_WORK.html", "docs/REMAINING_WORK.md", "docs/RESULTS.html", "docs/RESULTS.md",
    "docs/all-downloads.html", "docs/analysis.html", "docs/data/current-artifact.json",
    "docs/data/h50-artifact.json", "docs/data/h51-artifact.json", "docs/downloads/README.md",
    "docs/downloads/gems47-h50-slopeanom-s2p8-20261007-note.txt",
    "docs/downloads/gems47-h50-slopeanom-s2p8-20261007-receipt.json",
    "docs/downloads/gems47-h50-slopeanom-s2p8-20261007.zip",
    "docs/downloads/gems47-h51-multiscale-s2p8-20261007-note.txt",
    "docs/downloads/gems47-h51-multiscale-s2p8-20261007-receipt.json",
    "docs/downloads/gemsdoe47-h49-polarity-scarp-s2.8-d7.37-b3.json",
    "docs/evidence.html", "docs/executive-summary.html", "docs/h47b-mask-audit-20261006.html",
    "docs/h50.html", "docs/h50a.html", "docs/h51.html", "docs/hypotheses-s3.html",
    "docs/hypotheses.html", "docs/index.html", "docs/irregularities.html", "docs/knowledge.html",
    "docs/leaderboard.html", "docs/method.html", "docs/next-session.md",
    "docs/portal-checklist.html", "docs/portal-checklist.md", "docs/research.html",
    "docs/session3.html", "docs/sources.html", "docs/submit.html", "docs/why-02778.html",
}

# Small, separately reviewed repairs to Markdown links that escaped GitHub Pages' docs/ artifact.
# These entries do not authorize status/content edits: each changed file must contain its exact
# repository URL sentinel, and local links are checked by tests/test_site.py.
INTENTIONAL_PAGES_LINK_REPAIRS = {
    "docs/irregularities.md": (
        "https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/README.md",
    ),
    "docs/research.md": (
        "https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/README.md",
    ),
    "docs/research/readme-main-750f3b7.md": (
        "https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/README.md",
    ),
    "docs/research/readme-preC1-20261006.md": (
        "https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/README.md",
    ),
    "docs/session3.md": (
        "https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/README.md",
    ),
    "docs/why-02778.md": (
        "https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/knowledge/02_the_metric_algebra.md",
    ),
}
STATUS_SENTINELS = {
    "docs/index.html": ("H50 · locally promoted public-proxy candidate", "h51 multi-scale variant",
                        "2e32d8ed384692bc44ff768ca5d3814ed48d7b627ba3c818743ee13ab3538d5b"),
    "docs/executive-summary.html": ("not organizer-accepted", "0.095701", "H51 multi-scale variant"),
    "docs/h50.html": ("H50 · locally promoted public-proxy candidate", "no organizer acceptance",
                       "2e32d8ed384692bc44ff768ca5d3814ed48d7b627ba3c818743ee13ab3538d5b"),
    "docs/h51.html": ("research only", "no fresh H51-specific", "do not transfer the H50 result to H51"),
    "docs/all-downloads.html": ("locally promoted", "not organizer acceptance", "research-only variant"),
    "docs/data/current-artifact.json": ("LOCALLY_PROMOTED_PUBLIC_PROXY_CANDIDATE_NOT_ORGANIZER_ACCEPTED",
                                        '"slot_authorized": false', '"organizer_acceptance_established": false'),
    "docs/data/h50-artifact.json": ("locally_promoted_public_proxy_candidate", '"slot_authorized": false',
                                     '"organizer_acceptance_established": false', "nanoutside.tif"),
    "docs/data/h51-artifact.json": ("research_only_candidate", '"applies_to_h51": false',
                                     '"slot_authorized": false', "not_transferable_to_h51"),
    "docs/HOW_TO_SUBMIT.md": ("H50 local review package", "not organizer-accepted", "No portal access, account action, upload"),
    "docs/REMAINING_WORK.md": ("H50 is the last locally promoted candidate", "H51 remains research-only",
                               "0.040976", "−0.01050"),
    "docs/COMPLIANCE.md": ("No artifact is organizer-accepted", "H50's documented public-proxy gate passed",
                           "H51's NaN-outside encoding"),
    "docs/H49_RESULTS.md": ("0.04098", "0.03801", "−0.03342", "−0.01050"),
}

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
                    help="reject changes outside the explicit status/link-repair allowlists")
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
            if f in INTENTIONAL_STATUS_RECONCILIATION:
                text = p.read_text(encoding="utf-8", errors="replace")
                missing_tokens = [token for token in STATUS_SENTINELS.get(f, ())
                                  if token.lower() not in text.lower()]
                if "H50 · OK TO DOWNLOAD AND SUBMIT" in text:
                    bad.append((f, "stale H50 upload-ready banner remains"))
                elif missing_tokens:
                    bad.append((f, "status reconciliation sentinel(s) missing: " +
                                ", ".join(missing_tokens)))
                else:
                    print(f"OK: {f} differs intentionally under the H50/H51/H49 status review")
                continue
            if f in INTENTIONAL_PAGES_LINK_REPAIRS:
                text = p.read_text(encoding="utf-8", errors="replace")
                missing_tokens = [token for token in INTENTIONAL_PAGES_LINK_REPAIRS[f]
                                  if token.lower() not in text.lower()]
                if missing_tokens:
                    bad.append((f, "Pages-link repair sentinel(s) missing: " +
                                ", ".join(missing_tokens)))
                else:
                    print(f"OK: {f} contains only an explicitly reviewed Pages-link repair")
                continue
            bad.append((f, "modified outside explicit status-reconciliation/link-repair allowlists"))
        if bad:
            print("FAIL: main's docs files were changed:")
            for f, why in bad:
                print(f"  {why}: {f}")
            return 1
        print(f"OK: all {len(files)} main docs files are unchanged or explicitly reviewed status updates")
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
