"""Devfolio: open & upcoming software engineering hackathons extracted from Next.js __NEXT_DATA__."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from scraper.flight import extract_next_data
from scraper.http import create_session, safe_get, save_source_cache
from scraper.models import ChallengeRecord
from scraper.normalize import build_record

logger = logging.getLogger(__name__)

SOURCE_NAME = "devfolio"
PAGE_URL = "https://devfolio.co/hackathons"


def extract_hackathons_from_html(html: str) -> List[Dict[str, Any]]:
    nd = extract_next_data(html)
    if not nd:
        return []
    queries = (
        nd.get("props", {})
        .get("pageProps", {})
        .get("dehydratedState", {})
        .get("queries", [])
    )
    out: List[Dict[str, Any]] = []
    for q in queries:
        data = (q.get("state") or {}).get("data")
        if not isinstance(data, dict):
            continue
        for bucket in ("open_hackathons", "upcoming_hackathons", "featured_hackathons"):
            items = data.get(bucket)
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict):
                        copy = dict(it)
                        copy["_bucket"] = bucket
                        out.append(copy)
    return out


def scrape() -> List[ChallengeRecord]:
    session = create_session()
    resp = safe_get(session, PAGE_URL)
    if resp is None:
        return []
    raw_items = extract_hackathons_from_html(resp.text)
    save_source_cache(SOURCE_NAME, raw_items)

    records: List[ChallengeRecord] = []
    for h in raw_items:
        slug = str(h.get("slug") or "").strip()
        name = str(h.get("name") or "").strip()
        if not slug or not name:
            continue
        themes: List[str] = []
        for t in h.get("themes") or []:
            if isinstance(t, dict):
                t_name = (t.get("theme") or {}).get("name") if isinstance(t.get("theme"), dict) else t.get("name")
                if t_name and str(t_name).lower() != "no restrictions":
                    themes.append(str(t_name))

        is_online = bool(h.get("is_online"))
        city = str(h.get("city") or "").strip()
        mode = "Online" if is_online else "In-Person"
        loc_desc = "Online" if is_online else (city or "In-Person")
        url = str((h.get("settings") or {}).get("site") or f"https://{slug}.devfolio.co")

        rec = build_record(
            title=name,
            platform="Devfolio",
            source=SOURCE_NAME,
            url=url,
            challenge_type="hackathon",
            prize=h.get("prize_amount") or "Sponsor Bounties & Tracks",
            start_date=h.get("starts_at"),
            end_date=h.get("ends_at"),
            raw_status="upcoming" if h.get("_bucket") == "upcoming_hackathons" else "",
            tags=["devfolio", "hackathon", mode.lower(), *[t.lower() for t in themes]],
            description=f"Devfolio builder hackathon ({loc_desc})"
            + (f" · tracks: {', '.join(themes)}." if themes else "."),
            organizer="Devfolio",
            mode=mode,
            participants_count=h.get("participants_count") or None,
            category_hint=" ".join(themes),
        )
        if rec:
            records.append(rec)

    logger.info("Devfolio yielded %d hackathons", len(records))
    return records

