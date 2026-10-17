"""Bugcrowd: live open application, web, API, and cloud security bug bounty programs."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from scraper.http import create_session, safe_get_json, save_source_cache
from scraper.models import ChallengeRecord
from scraper.normalize import build_record

logger = logging.getLogger(__name__)

SOURCE_NAME = "bugcrowd"
API_URL = "https://bugcrowd.com/engagements.json"


def parse_engagements(items: List[Dict[str, Any]]) -> List[ChallengeRecord]:
    records: List[ChallengeRecord] = []
    for item in items:
        if not isinstance(item, dict) or item.get("isPrivate") or item.get("isDemo"):
            continue
        name = str(item.get("name") or "").strip()
        brief = str(item.get("briefUrl") or "").strip()
        if not name or not brief:
            continue
        reward = item.get("rewardSummary") or {}
        max_reward = reward.get("maxReward") or reward.get("summary") or "Hall of Fame / Points"
        industry = str(item.get("industryName") or "Software & Cloud")
        tagline = str(item.get("tagline") or f"Public application & cloud security bounty program ({industry}).")
        url = f"https://bugcrowd.com{brief}" if brief.startswith("/") else brief

        rec = build_record(
            title=name,
            platform="Bugcrowd",
            source=SOURCE_NAME,
            url=url,
            challenge_type="oss_bounty",
            prize=max_reward,
            prize_currency="USD",
            start_date=None,
            end_date=item.get("endsAt"),
            category="Security & AppSec",
            tags=["bugcrowd", "appsec", "bug-bounty", industry.lower()],
            description=f"{tagline} · Reward range: {reward.get('summary') or max_reward}.",
            organizer=name.replace("Managed Bug Bounty Engagement", "").replace("Bug Bounty", "").strip() or "Bugcrowd",
            mode="Online",
            logo_url=item.get("logoUrl"),
            category_hint=f"security appsec {industry} {tagline}",
        )
        if rec:
            records.append(rec)
    return records


def scrape() -> List[ChallengeRecord]:
    session = create_session()
    all_items: List[Dict[str, Any]] = []
    for page in (1, 2):
        data = safe_get_json(
            session,
            API_URL,
            params={
                "category": "bug_bounty",
                "page": page,
                "sort_by": "promoted",
                "sort_direction": "desc",
            },
        )
        if not isinstance(data, dict):
            break
        batch = data.get("engagements") or []
        if not isinstance(batch, list) or not batch:
            break
        all_items.extend(batch)
    save_source_cache(SOURCE_NAME, all_items)
    records = parse_engagements(all_items)
    logger.info("Bugcrowd yielded %d public security/software bounty programs", len(records))
    return records

