"""Source failures must never invent a fresh score or a score-to-file receipt."""
import importlib.util
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("feed", ROOT / "scripts" / "refresh_source_feed.py")
F = importlib.util.module_from_spec(spec); spec.loader.exec_module(F)
URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"


def table(scores=("0.3774", "0.3345", "0.3262")):
    return '<table><tbody>' + ''.join(f'<tr><td>{i}</td><td><a href="/users/user{i}/">user{i}</a></td><td>{s}</td></tr>'
                                    for i, s in enumerate(scores, 1)) + '</tbody></table>'


def test_ranked_official_table_parses_without_inventing_file_mapping():
    rows = F.parse_leaderboard(table(), URL)
    assert rows[0] == {"rank": 1, "participant": "user1", "score": .3774,
                       "profile_url": "https://www.drivendata.org/users/user1/"}
    assert all("filename" not in r for r in rows)


@pytest.mark.parametrize("html", ["<h1>Sign in</h1>", table(("0.2", "0.3", "0.1")), table(("0.5000", "0.7000", "0.3000"))])
def test_layout_and_rank_anomalies_fail_instead_of_guessing(html):
    with pytest.raises(ValueError):
        F.parse_leaderboard(html, URL)


def test_ssl_failure_preserves_the_last_observation_and_marks_it_stale():
    def fail(*a, **kw):
        raise requests.exceptions.SSLError("test-only network failure")
    sources = [{"id": "official-leaderboard", "title": "Test fixture", "url": "https://example.org/permitted-fixture", "evidence_class": "official"}]
    previous = {"leaderboard": {"observed_utc": "2026-10-05T12:00:00Z", "rows": [{"rank": 1, "score": .3774}]},
                "sources": [{"id": "official-leaderboard", "last_success_utc": "2026-10-05T12:00:00Z"}]}
    result = F.refresh(sources, previous, fetcher=fail)
    assert result["leaderboard"]["rows"] == previous["leaderboard"]["rows"]
    assert result["leaderboard"]["observed_utc"] == "2026-10-05T12:00:00Z"
    assert result["leaderboard"]["status"] == "STALE_LAST_OBSERVATION_RETAINED"
    assert result["sources"][0]["last_success_utc"] == "2026-10-05T12:00:00Z"
    assert result["sources"][0]["status"] == "FETCH_FAILED"
    assert not result["leaderboard"]["file_to_score_mapping_verified"]


def test_initial_failure_produces_no_numeric_score():
    def fail(*a, **kw):
        raise requests.exceptions.ConnectionError()
    source = {"id": "official-leaderboard", "title": "Test fixture", "url": "https://example.org/permitted-fixture", "evidence_class": "official"}
    result = F.refresh([source], {}, fetcher=fail)
    assert result["leaderboard"]["status"] == "UNAVAILABLE_NO_SCORE_INVENTED"
    assert "rows" not in result["leaderboard"]


def test_drivendata_terms_disable_unpermitted_automatic_monitoring():
    def forbidden(*a, **kw):
        pytest.fail("no DrivenData request may be sent without recorded written permission")
    source = {"id": "official-leaderboard", "title": "Official", "url": URL, "evidence_class": "official"}
    record, body = F.fetch_source(source, fetcher=forbidden)
    assert body is None and record["status"] == "SKIPPED_TERMS_WRITTEN_PERMISSION_NOT_RECORDED"
    assert "http_status" not in record and "last_attempt_utc" not in record
    result = F.refresh([source], {}, fetcher=forbidden)
    assert result["policy_skips"] == 1
    assert not result["drivendata_automated_monitoring_enabled"]


def test_automation_workflows_track_the_current_ref_not_a_retired_branch():
    workflows = [
        ROOT / ".github" / "workflows" / "site.yml",
        ROOT / ".github" / "workflows" / "source-probes.yml",
    ]
    for workflow in workflows:
        text = workflow.read_text()
        assert "arena/50b2a166-gemsdoe47" not in text
        assert "branches: [main]" in text
        assert "ref: ${{ github.ref }}" in text
