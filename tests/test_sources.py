import json

from scraper.dedupe import deduplicate_records
from scraper.models import ChallengeRecord
from scraper.sources.codeforces import parse_codeforces, parse_leetcode
from scraper.sources.devfolio import extract_hackathons_from_html
from scraper.sources.devpost import parse_submission_period
from scraper.sources.github_bounties import extract_bounty_amount, parse_issues
from scraper.sources.mlh import parse_mlh_dates
from scraper.sources.topcoder import parse_challenges


def test_devpost_submission_period_parser():
    assert parse_submission_period("Oct 05 - 25, 2026") == ("2026-10-05", "2026-10-25T23:59:00Z")
    assert parse_submission_period("Sep 20 - Nov 05, 2026") == ("2026-09-20", "2026-11-05T23:59:00Z")
    assert parse_submission_period("Dec 20, 2026 - Jan 10, 2027") == ("2026-12-20", "2027-01-10T23:59:00Z")
    assert parse_submission_period("") == (None, None)


def test_mlh_date_parser():
    assert parse_mlh_dates("OCT 23 - 25", 2027) == ("2026-10-23T00:00:00Z", "2026-10-25T23:59:00Z")
    assert parse_mlh_dates("OCT 31 - NOV 01", 2027) == ("2026-10-31T00:00:00Z", "2026-11-01T23:59:00Z")
    assert parse_mlh_dates("FEB 12 - 14", 2027) == ("2027-02-12T00:00:00Z", "2027-02-14T23:59:00Z")


def test_topcoder_parser():
    sample = [
        {
            "id": "abc-123",
            "name": "Build Rust gRPC Microservice",
            "status": "ACTIVE",
            "startDate": "2026-10-15T00:00:00.000Z",
            "submissionEndDate": "2099-10-25T00:00:00.000Z",
            "track": {"name": "Development"},
            "type": {"name": "First2Finish"},
            "skills": [{"name": "Rust"}, {"name": "Docker"}],
            "prizeSets": [{"type": "PLACEMENT", "prizes": [{"type": "USD", "value": 800}, {"type": "USD", "value": 400}]}],
            "numOfRegistrants": 18,
            "numOfSubmissions": 3,
        }
    ]
    recs = parse_challenges(sample)
    assert len(recs) == 1
    assert recs[0].prize_usd == 1200.0
    assert "Rust" in recs[0].languages


def test_github_bounty_extraction():
    assert extract_bounty_amount("Fix memory leak", ["💎 $500", "bounty"], "") == 500.0
    assert extract_bounty_amount("[$1,250] Add WebGPU backend", ["bounty"], "") == 1250.0
    issues = [
        {
            "html_url": "https://github.com/org/repo/issues/42",
            "repository_url": "https://api.github.com/repos/org/repo",
            "title": "[$750] Implement OpenTelemetry exporter in Go",
            "body": "Algora bounty on algora.io",
            "labels": [{"name": "💎 Bounty"}],
            "created_at": "2026-10-10T10:00:00Z",
            "comments": 5,
        }
    ]
    recs = parse_issues(issues)
    assert len(recs) == 1
    assert recs[0].prize_usd == 750.0
    assert recs[0].repo_url == "https://github.com/org/repo"


def test_devfolio_next_data_extraction():
    payload = {
        "props": {
            "pageProps": {
                "dehydratedState": {
                    "queries": [
                        {
                            "state": {
                                "data": {
                                    "open_hackathons": [{"slug": "ethindia", "name": "ETHIndia"}],
                                    "upcoming_hackathons": [{"slug": "ai-build", "name": "AI Build"}],
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    html = f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(payload)}</script>'
    items = extract_hackathons_from_html(html)
    assert [i["slug"] for i in items] == ["ethindia", "ai-build"]


def test_codeforces_and_leetcode_parsers():
    now_ts = 1_792_000_000.0
    cf = parse_codeforces(
        [{"id": 2278, "name": "Codeforces Round (Div. 2)", "type": "ICPC", "phase": "BEFORE", "startTimeSeconds": now_ts + 86400, "durationSeconds": 7200}],
        now_ts=now_ts,
    )
    lc = parse_leetcode(
        [{"title": "Weekly Contest 525", "titleSlug": "weekly-contest-525", "startTime": now_ts + 3600, "duration": 5400}],
        now_ts=now_ts,
    )
    assert len(cf) == 1 and cf[0].challenge_type == "coding_contest"
    assert len(lc) == 1 and lc[0].platform == "LeetCode"


def _rec(**kw):
    base = dict(id="1", title="Cloud Hackathon", platform="Devpost", source="devpost", url="https://devpost.com/a")
    base.update(kw)
    return ChallengeRecord(**base)


def test_dedupe_merges_same_url_and_keeps_richer_fields():
    a = _rec(prize_usd=0.0, description="")
    b = _rec(id="2", prize="$50K", prize_usd=50_000.0, description="Longer description of the hackathon")
    out = deduplicate_records([a, b])
    assert len(out) == 1
    assert out[0].prize_usd == 50_000.0
    assert out[0].description.startswith("Longer")

