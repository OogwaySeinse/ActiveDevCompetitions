"""Codeforces & LeetCode: upcoming and running competitive programming & algorithmic engineering rounds."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from scraper.http import create_session, safe_get_json, save_source_cache
from scraper.models import ChallengeRecord
from scraper.normalize import build_record

logger = logging.getLogger(__name__)

SOURCE_NAME = "codeforces"
CF_URL = "https://codeforces.com/api/contest.list?gym=false"
LC_URL = "https://leetcode.com/graphql"
LC_QUERY = "{allContests{title titleSlug startTime duration}}"
MAX_HORIZON_SECONDS = 35 * 86400


def parse_codeforces(items: List[Dict[str, Any]], now_ts: float | None = None) -> List[ChallengeRecord]:
    ref = now_ts if now_ts is not None else time.time()
    ref_dt = datetime.fromtimestamp(ref, tz=timezone.utc)
    records: List[ChallengeRecord] = []
    for c in items:
        if not isinstance(c, dict):
            continue
        phase = str(c.get("phase") or "")
        if phase not in ("BEFORE", "CODING"):
            continue
        cid = c.get("id")
        name = str(c.get("name") or "").strip()
        start_ts = float(c.get("startTimeSeconds") or 0)
        dur = float(c.get("durationSeconds") or 7200)
        end_ts = start_ts + dur
        if not cid or not name or start_ts <= 0 or end_ts < ref or (start_ts - ref) > MAX_HORIZON_SECONDS:
            continue

        ctype = str(c.get("type") or "ICPC")
        hours = round(dur / 3600, 1)
        rec = build_record(
            title=name,
            platform="Codeforces",
            source=SOURCE_NAME,
            url=f"https://codeforces.com/contests/{cid}",
            challenge_type="coding_contest",
            prize="Rated Global Leaderboard",
            start_date=start_ts,
            end_date=end_ts,
            raw_status="active" if phase == "CODING" else "upcoming",
            category="Algorithms & Competitive Coding",
            ecosystem="Cross-Stack / General",
            languages=["C / C++", "Python", "Java", "Rust"],
            tags=["codeforces", "competitive-programming", ctype.lower(), "algorithms"],
            description=f"Codeforces rated {ctype} algorithmic programming round ({hours}h window).",
            organizer="Codeforces",
            mode="Online",
            now=ref_dt,
        )
        if rec:
            records.append(rec)
    return records


def parse_leetcode(items: List[Dict[str, Any]], now_ts: float | None = None) -> List[ChallengeRecord]:
    ref = now_ts if now_ts is not None else time.time()
    ref_dt = datetime.fromtimestamp(ref, tz=timezone.utc)
    records: List[ChallengeRecord] = []
    for c in items:
        if not isinstance(c, dict):
            continue
        title = str(c.get("title") or "").strip()
        slug = str(c.get("titleSlug") or "").strip()
        start_ts = float(c.get("startTime") or 0)
        dur = float(c.get("duration") or 5400)
        end_ts = start_ts + dur
        if not title or not slug or end_ts < ref or (start_ts - ref) > MAX_HORIZON_SECONDS:
            continue

        rec = build_record(
            title=f"LeetCode {title}",
            platform="LeetCode",
            source=SOURCE_NAME,
            url=f"https://leetcode.com/contest/{slug}/",
            challenge_type="coding_contest",
            prize="LeetCoins & Global Rating",
            start_date=start_ts,
            end_date=end_ts,
            raw_status="active" if start_ts <= ref <= end_ts else "upcoming",
            category="Algorithms & Competitive Coding",
            ecosystem="Cross-Stack / General",
            languages=["Python", "C / C++", "Java", "TypeScript"],
            tags=["leetcode", "competitive-programming", "algorithms", "data-structures"],
            description=f"LeetCode {title} timed algorithmic & data-structures engineering contest ({int(dur // 60)} mins).",
            organizer="LeetCode",
            mode="Online",
            now=ref_dt,
        )
        if rec:
            records.append(rec)
    return records


def scrape() -> List[ChallengeRecord]:
    session = create_session()
    cf_data = safe_get_json(session, CF_URL)
    cf_items = cf_data.get("result") if isinstance(cf_data, dict) and cf_data.get("status") == "OK" else []

    lc_data = safe_get_json(session, LC_URL, params={"query": LC_QUERY})
    lc_items = ((lc_data.get("data") or {}).get("allContests") or []) if isinstance(lc_data, dict) else []

    save_source_cache(SOURCE_NAME, {"codeforces": cf_items[:30], "leetcode": lc_items[:15]})
    records = [*parse_codeforces(cf_items), *parse_leetcode(lc_items)]
    logger.info("Codeforces + LeetCode yielded %d coding contests", len(records))
    return records
