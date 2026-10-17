"""HackerEarth: live ongoing & upcoming developer hackathons and hiring/coding challenges."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from scraper.http import create_session, safe_get_json, save_source_cache
from scraper.models import ChallengeRecord
from scraper.normalize import build_record

logger = logging.getLogger(__name__)

SOURCE_NAME = "hackerearth"
API_URL = "https://www.hackerearth.com/chrome-extension/events/"


def parse_events(items: List[Dict[str, Any]]) -> List[ChallengeRecord]:
    records: List[ChallengeRecord] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or item.get("subscribe") or "").strip()
        if not title or not url:
            continue
        raw_status = str(item.get("status") or "").strip().lower()
        ctype_raw = str(item.get("challenge_type") or "").lower()
        if "hackathon" in url.lower() or "hackathon" in title.lower() or "hackathon" in ctype_raw:
            challenge_type = "hackathon"
        elif "hiring" in ctype_raw or "competitive" in url.lower():
            challenge_type = "dev_challenge"
        else:
            challenge_type = "hackathon"

        rec = build_record(
            title=title,
            platform="HackerEarth",
            source=SOURCE_NAME,
            url=url,
            challenge_type=challenge_type,
            prize="Cash Prizes & Hiring Opportunities",
            start_date=item.get("start_utc_tz") or item.get("start_tz"),
            end_date=item.get("end_utc_tz") or item.get("end_tz"),
            raw_status="upcoming" if raw_status == "upcoming" else "active",
            tags=["hackerearth", challenge_type, ctype_raw or "developer"],
            description=str(item.get("description") or f"{title} on HackerEarth."),
            organizer="HackerEarth",
            mode="Online",
            logo_url=item.get("thumbnail") or item.get("cover_image"),
            category_hint=f"{title} {ctype_raw}",
        )
        if rec:
            records.append(rec)
    return records


def scrape() -> List[ChallengeRecord]:
    session = create_session()
    data = safe_get_json(session, API_URL)
    items = data.get("response") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return []
    save_source_cache(SOURCE_NAME, items)
    records = parse_events(items)
    logger.info("HackerEarth yielded %d live challenges", len(records))
    return records

