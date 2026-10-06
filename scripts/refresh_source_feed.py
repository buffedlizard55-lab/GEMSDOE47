#!/usr/bin/env python3
"""Refresh public source availability and the official participant leaderboard.

No credentials, no submission calls, no scraping login-walled training data.
Failures preserve the last successful leaderboard observation and explicitly
mark it stale. Owner pages are SECONDARY evidence; never map a score to a TIFF.
Raw snapshots and full datasets stay in ignored cache, not the Git patch.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from itertools import pairwise
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILE = ROOT / "registry" / "current-source-list.json"
DEFAULT_OUT = ROOT / "docs" / "data" / "source-feed.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_leaderboard(html: str, source_url: str) -> list[dict]:
    """Parse only ranked score rows; fail if the official table layout changes."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.select("table tr"):
        cells = tr.find_all("td", recursive=False)
        if len(cells) < 3:
            continue
        rank_match = re.fullmatch(r"\s*#?(\d+)\s*", cells[0].get_text(" ", strip=True))
        if not rank_match:
            continue
        score_cells = [c for c in cells[1:] if re.fullmatch(r"[01]\.\d{4,8}", c.get_text(" ", strip=True))]
        if len(score_cells) != 1:
            raise ValueError("a ranked row has no unambiguous score cell")
        rank, score = int(rank_match[1]), float(score_cells[0].get_text(strip=True))
        if rank < 1 or not 0 <= score <= 1:
            raise ValueError("rank/score outside permitted domain")
        # A participant cell may include avatar links, elapsed time and counts.
        user_links = [a for c in cells[1:] for a in c.find_all("a", href=True)
                      if "/users/" in a["href"] and a.get_text(strip=True)]
        participant = user_links[-1].get_text(strip=True) if user_links else None
        profile = urljoin(source_url, user_links[-1]["href"]) if user_links else None
        if participant is None:
            # A team can have two linked avatars and an unlinked team name.
            for c in cells[1:]:
                text = c.get_text(" ", strip=True)
                if "submission" in text.lower():
                    participant = re.split(r"\s+\d+\s*(?:s|min|h|d|w)|\s*[·⸱]", text)[0].strip() or None
                    break
        rows.append({"rank": rank, "participant": participant, "score": score, "profile_url": profile})
    rows.sort(key=lambda r: r["rank"])
    if len(rows) < 3 or rows[0]["rank"] != 1 or len({r["rank"] for r in rows}) != len(rows):
        raise ValueError("no unique ranked leaderboard table found; last observation retained")
    if any(a["score"] < b["score"] for a, b in pairwise(rows)):
        raise ValueError("leaderboard scores not in descending rank order")
    return rows


def fetch_source(source: dict, *, fetcher=requests.get) -> tuple[dict, str | None]:
    attempt = utc_now()
    record = {"id": source["id"], "title": source["title"], "url": source["url"],
              "evidence_class": source["evidence_class"], "last_attempt_utc": attempt,
              "verified_claims": False}
    # Only permitted HTTPS public URLs from the versioned registry are fetched.
    # DrivenData Terms (Prohibited Uses) prohibit robot/spider monitoring. No
    # written organizer permission or documented authorized feed is recorded.
    # A public page and a user's research request are not that permission.
    parsed = urlparse(source["url"])
    if parsed.hostname == "drivendata.org" or (parsed.hostname or "").endswith(".drivendata.org"):
        record.pop("last_attempt_utc")
        record["policy_checked_utc"] = attempt
        return {**record, "status": "SKIPPED_TERMS_WRITTEN_PERMISSION_NOT_RECORDED",
                "reason": "Automated DrivenData monitoring disabled; retain dated observation and official link.",
                "terms_url": "https://www.drivendata.org/termsofuse/"}, None
    if parsed.scheme != "https" or parsed.username or parsed.password:
        return {**record, "status": "INVALID_PUBLIC_SOURCE_URL"}, None
    try:
        with fetcher(source["url"], timeout=(8, 25), stream=True,
                     headers={"User-Agent": "GEMSDOE47-public-source-review/1.0"}) as response:
            record["http_status"] = response.status_code
            record["final_url"] = response.url
            if "/accounts/login" in response.url or "/login" in urlparse(response.url).path:
                return {**record, "status": "LOGIN_REQUIRED"}, None
            response.raise_for_status()
            content = bytearray()
            for chunk in response.iter_content(64 * 1024):
                content.extend(chunk)
                if len(content) > 12_000_000:
                    return {**record, "status": "CONTENT_LIMIT_EXCEEDED"}, None
            raw = bytes(content)
            record["content_sha256"] = hashlib.sha256(raw).hexdigest()
            record["bytes"] = len(raw)
            record["last_success_utc"] = utc_now()
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" in content_type or "<html" in raw[:2000].decode("utf-8", errors="ignore").lower():
                html = raw.decode(response.encoding or "utf-8", errors="replace")
                title = BeautifulSoup(html, "html.parser").find("title")
                record["page_title"] = title.get_text(" ", strip=True) if title else None
                record["status"] = "FETCHED_HTML"
                return record, html
            if raw.startswith(b"%PDF"):
                return {**record, "status": "FETCHED_PDF_NOT_REINTERPRETED"}, None
            return {**record, "status": "FETCHED_NON_HTML"}, None
    except requests.RequestException as error:
        record["status"] = "FETCH_FAILED"
        record["error_type"] = type(error).__name__
        # Do not expose request objects or environment credentials in errors.
        return record, None


def refresh(sources: list[dict], previous: dict, *, fetcher=requests.get, workers: int = 6) -> dict:
    records, board = [], None
    old_by_id = {r["id"]: r for r in previous.get("sources", [])}
    def run(source):
        return source, fetch_source(source, fetcher=fetcher)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        for source, (record, html) in executor.map(run, sources):
            old = old_by_id.get(source["id"], {})
            if "last_success_utc" not in record and old.get("last_success_utc"):
                record["last_success_utc"] = old["last_success_utc"]
            if source["id"] == "official-leaderboard" and html:
                try:
                    rows = parse_leaderboard(html, source["url"])
                    board = {"status": "FRESH_OFFICIAL_PARTICIPANT_OBSERVATION", "rows": rows,
                             "observed_utc": record["last_success_utc"], "url": source["url"],
                             "html_sha256": record["content_sha256"], "file_to_score_mapping_verified": False,
                             "scope": "Participant public scores, not TIFF scores or private performance."}
                    record["leaderboard_table_parsed"] = True
                except ValueError as error:
                    record["status"] = "PARSER_FAILED_LAST_OBSERVATION_RETAINED"
                    record["parse_error"] = str(error)
            records.append(record)
    if board is None:
        board = dict(previous.get("leaderboard", {}))
        board["status"] = "STALE_LAST_OBSERVATION_RETAINED" if board.get("rows") else "UNAVAILABLE_NO_SCORE_INVENTED"
        board["latest_attempt_utc"] = utc_now()
        board["file_to_score_mapping_verified"] = False
    return {"schema_version": 1, "generated_utc": utc_now(),
            "policy": "Availability is not claim verification; secondary pages never authenticate a score-to-file mapping.",
            "automation": "Daily Pages refresh of permitted official/owner sources; DrivenData monitoring disabled without written permission; no uploads.",
            "sources": records, "leaderboard": board,
            "drivendata_automated_monitoring_enabled": False,
            "permission_boundary": "DrivenData Terms prohibit robots/spiders; no written permission recorded. Saved dated board is not automatically refreshed.",
            "policy_skips": sum(r["status"].startswith("SKIPPED_TERMS") for r in records),
            "fetch_failures": sum(r["status"] in ("FETCH_FAILED", "PARSER_FAILED_LAST_OBSERVATION_RETAINED") for r in records)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    sources = json.loads(SOURCE_FILE.read_text())["sources"]
    previous = json.loads(args.out.read_text()) if args.out.exists() else {}
    out = refresh(sources, previous)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.out.with_suffix(".json.partial")
    temporary.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    temporary.replace(args.out)
    print(f"{len(sources)} sources attempted; failures={out['fetch_failures']}; leaderboard={out['leaderboard']['status']}")
    return 0  # failures are surfaced in the feed; never replace them by fake facts


if __name__ == "__main__":
    sys.exit(main())
