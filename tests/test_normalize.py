from datetime import datetime, timezone

import pytest

from scraper import fx
from scraper.normalize import (
    build_record,
    canonicalize_url,
    infer_category,
    infer_ecosystem,
    infer_languages,
    parse_date,
    parse_prize,
    resolve_status,
)

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def fixed_fx(monkeypatch):
    rates = dict(fx.FALLBACK_TO_USD)
    rates.update({"EUR": 1.1, "INR": 0.012, "CAD": 0.75})
    monkeypatch.setattr(fx, "_MEMO_RATES", rates)


@pytest.mark.parametrize(
    "raw,currency,label,usd",
    [
        ("$50,000 in USD", "USD", "$50K", 50000.0),
        ("10000 USDC", "USDC", "$10K USDC", 10000.0),
        ("$<span data-currency-value>15,000</span>", "USD", "$15K", 15000.0),
        ("1st Place - $2,500\r\n2nd Place - $1,000", "USD", "$2.5K", 2500.0),
        ("- 1st Place: 50,000 INR\n- 2nd Place: 25,000 INR", "INR", "50,000 INR", 600.0),
    ],
)
def test_parse_prize_amounts(raw, currency, label, usd):
    got_label, got_usd, got_cur = parse_prize(raw, "USD")
    assert got_cur == currency
    assert got_label == label
    assert got_usd == pytest.approx(usd)


def test_parse_prize_long_free_text_fallback():
    label, usd, _ = parse_prize("Top winning teams receive cloud credits, hardware kits, and mentorship")
    assert usd == 0.0
    assert label == "Prizes & Swag (see page)"


def test_parse_date_handles_epoch_and_iso():
    assert parse_date(1760367600) == "2025-10-13T15:00:00Z"
    assert parse_date("2026-11-03T18:30:00Z") == "2026-11-03T18:30:00Z"
    assert parse_date("2026-10-18T21:00:00+00:00") == "2026-10-18T21:00:00Z"
    assert parse_date("not a date") is None


def test_resolve_status_variants():
    assert resolve_status("2026-10-01T00:00:00Z", "2026-11-03T00:00:00Z", now=NOW)[:2] == (True, "active")
    assert resolve_status("2026-10-01T00:00:00Z", "2026-10-20T00:00:00Z", now=NOW)[:2] == (True, "ending_soon")
    assert resolve_status("2026-11-01T00:00:00Z", "2026-11-10T00:00:00Z", now=NOW)[:2] == (True, "upcoming")
    assert resolve_status("2026-09-01T00:00:00Z", "2026-10-01T00:00:00Z", now=NOW)[0] is False
    assert resolve_status(None, None, "finished", now=NOW)[0] is False
    assert resolve_status("2024-01-01T00:00:00Z", None, now=NOW)[:2] == (True, "ongoing")


def test_taxonomy_inference():
    assert infer_category("Gemini Multi-Agent Hackathon", "Build agentic RAG workflows") == "AI Agents & LLM Apps"
    assert infer_category("Kubernetes eBPF Observability", "Cloud native telemetry") == "Cloud, DevOps & Infra"
    assert infer_category("Rust WASM Compiler", "Fast CLI linter and language server") == "Developer Tools & CLI"
    assert infer_ecosystem("Kubernetes Operator", "Docker and Terraform") == "Cloud & Kubernetes"
    assert infer_ecosystem("Flutter Mobile Challenge", "iOS and Android apps") == "Mobile (iOS / Android)"
    langs = infer_languages("Rust & TypeScript SDK", "Build a Next.js + Cargo plugin", [], "Web & Full-Stack")
    assert "TypeScript" in langs and "Rust" in langs


def test_build_record_drops_ended_and_sets_defaults():
    assert (
        build_record(
            title="Expired Hackathon",
            platform="Devpost",
            source="devpost",
            url="https://devpost.com/expired",
            challenge_type="hackathon",
            end_date="2020-01-01",
        )
        is None
    )
    rec = build_record(
        title="Cloud Native Hackathon",
        platform="Devpost",
        source="devpost",
        url="https://devpost.com/cloud-native",
        challenge_type="hackathon",
        start_date="2099-11-05",
        end_date="2099-11-07",
        prize="$25,000",
    )
    assert rec is not None
    assert rec.status == "upcoming"
    assert rec.prize_usd == 25000.0
    assert rec.category == "Cloud, DevOps & Infra"
    assert rec.ecosystem == "Cloud & Kubernetes"


def test_oss_bounty_without_deadline_is_ongoing():
    rec = build_record(
        title="[calcom/cal.com] Add OAuth2 PKCE flow",
        platform="Algora / GitHub",
        source="github_bounties",
        url="https://github.com/calcom/cal.com/issues/123",
        challenge_type="oss_bounty",
        prize=1500,
        start_date="2026-10-01T12:00:00Z",
    )
    assert rec is not None
    assert rec.status == "ongoing"
    assert rec.days_remaining is None
    assert rec.prize == "$1.5K"
    assert rec.difficulty == "Advanced"


def test_canonicalize_url_strips_tracking_and_www():
    assert canonicalize_url("http://www.Example.com/a/?utm_source=mlh&id=2") == "https://example.com/a?id=2"

