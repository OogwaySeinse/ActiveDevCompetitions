"""Topcoder: live software development, First2Finish, code, UI prototype & architecture challenges via v6 API."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from scraper.http import create_session, safe_get_json, save_source_cache
from scraper.models import ChallengeRecord
from scraper.normalize import build_record

logger = logging.getLogger(__name__)

SOURCE_NAME = "topcoder"
API_URL = "https://api.topcoder.com/v6/challenges"


def _extract_total_prize_usd(prize_sets: Any) -> float:
    total = 0.0
    if not isinstance(prize_sets, list):
        return 0.0
    for ps in prize_sets:
        if not isinstance(ps, dict):
            continue
        if str(ps.get("type") or "").upper() not in ("PLACEMENT", "FIRST2FINISH", "COPILOT", ""):
            continue
        for p in ps.get("prizes") or []:
            if isinstance(p, dict):
                try:
                    total += float(p.get("value") or 0.0)
                except (TypeError, ValueError):
                    continue
    return total


def parse_challenges(items: List[Dict[str, Any]]) -> List[ChallengeRecord]:
    records: List[ChallengeRecord] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("id") or "")
        title = str(item.get("name") or "")
        if not cid or not title:
            continue

        track_obj = item.get("track")
        track_name = track_obj.get("name", "Development") if isinstance(track_obj, dict) else str(track_obj or "Development")
        type_obj = item.get("type")
        type_name = type_obj.get("name", "Challenge") if isinstance(type_obj, dict) else str(type_obj or "Challenge")

        skills_raw = item.get("skills") or []
        skill_names = [
            str(s.get("name")).strip()
            for s in skills_raw
            if isinstance(s, dict) and s.get("name")
        ]
        tags_raw = [str(t).strip() for t in (item.get("tags") or []) if t]
        all_tags = ["topcoder", type_name.lower(), track_name.lower(), *[s.lower() for s in skill_names], *[t.lower() for t in tags_raw]]

        prize_usd = _extract_total_prize_usd(item.get("prizeSets"))
        end_date = item.get("submissionEndDate") or item.get("endDate") or item.get("registrationEndDate")
        start_date = item.get("startDate") or item.get("registrationStartDate")

        rec = build_record(
            title=title,
            platform="Topcoder",
            source=SOURCE_NAME,
            url=f"https://www.topcoder.com/challenges/{cid}",
            challenge_type="dev_challenge",
            prize=prize_usd if prize_usd > 0 else "Topcoder Points / Swag",
            prize_currency="USD",
            start_date=start_date,
            end_date=end_date,
            raw_status=str(item.get("status") or "ACTIVE"),
            tags=all_tags,
            description=str(item.get("description") or f"{track_name} · {type_name} challenge on Topcoder."),
            organizer="Topcoder",
            mode="Online",
            participants_count=item.get("numOfRegistrants") or None,
            submissions_count=item.get("numOfSubmissions") or None,
            category_hint=" ".join([track_name, type_name, *skill_names]),
        )
        if rec:
            records.append(rec)
    return records


def scrape() -> List[ChallengeRecord]:
    session = create_session()
    data = safe_get_json(session, API_URL, params={"status": "ACTIVE", "perPage": 50})
    if not isinstance(data, list):
        return []
    save_source_cache(SOURCE_NAME, data)
    records = parse_challenges(data)
    logger.info("Topcoder yielded %d active development challenges", len(records))
    return records

