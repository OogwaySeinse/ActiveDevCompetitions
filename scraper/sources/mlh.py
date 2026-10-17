"""Major League Hacking (MLH): official 2026–2027 season developer hackathons."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from scraper.http import create_session, safe_get, save_source_cache
from scraper.models import ChallengeRecord
from scraper.normalize import build_record, canonicalize_url

logger = logging.getLogger(__name__)

SOURCE_NAME = "mlh"
SEASON_URLS = [
    (2027, "https://mlh.io/seasons/2027/events"),
    (2026, "https://mlh.io/seasons/2026/events"),
]

_MONTH_NUM = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

_DATE_RANGE_RE = re.compile(
    r"^(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+(\d{1,2})\s*-\s*"
    r"(?:(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+)?(\d{1,2})$",
    re.IGNORECASE,
)


def parse_mlh_dates(text: str, season_year: int) -> Tuple[Optional[str], Optional[str]]:
    """Parse MLH date strings like 'OCT 23 - 25' or 'OCT 31 - NOV 01' for an MLH season."""
    m = _DATE_RANGE_RE.match((text or "").strip())
    if not m:
        return None, None
    m1_s, d1_s, m2_s, d2_s = m.groups()
    m1 = _MONTH_NUM[m1_s.lower()]
    m2 = _MONTH_NUM[(m2_s or m1_s).lower()]
    # MLH season Y runs roughly July (Y-1) through June (Y)
    y1 = season_year - 1 if m1 >= 7 else season_year
    y2 = season_year - 1 if m2 >= 7 else season_year
    if y2 < y1:
        y2 = y1 + 1
    try:
        start = datetime(y1, m1, int(d1_s))
        end = datetime(y2, m2, int(d2_s))
        return start.strftime("%Y-%m-%dT00:00:00Z"), end.strftime("%Y-%m-%dT23:59:00Z")
    except ValueError:
        return None, None


def extract_events_from_html(html: str, season_year: int) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html or "", "html.parser")
    out: List[Dict[str, str]] = []
    for a in soup.find_all("a", href=True):
        href = str(a["href"])
        if "utm_campaign=events" not in href:
            continue
        strings = [s.strip() for s in a.stripped_strings if s.strip()]
        date_str = next((s for s in strings if _DATE_RANGE_RE.match(s)), "")
        if not date_str:
            continue

        qs = parse_qs(urlparse(href).query)
        title_from_qs = (qs.get("utm_content") or [""])[0].replace("+", " ").strip()
        date_idx = strings.index(date_str)
        title = title_from_qs or (strings[date_idx - 1] if date_idx > 0 else "")
        if not title or len(title) <= 1:
            continue

        after = strings[date_idx + 1 :]
        location = after[0] if after else "Global"
        mode_raw = " ".join(after[1:]).lower()
        if "digital" in mode_raw or "online" in mode_raw or "everywhere" in location.lower():
            mode = "Online"
        elif "hybrid" in mode_raw:
            mode = "Hybrid"
        else:
            mode = "In-Person"

        badges = [b for b in after[1:] if b.upper() not in ("IN-PERSON", "DIGITAL", "HYBRID")]
        out.append(
            {
                "title": title,
                "url": canonicalize_url(href) or href,
                "date_str": date_str,
                "season_year": str(season_year),
                "location": location,
                "mode": mode,
                "badges": ", ".join(badges),
            }
        )
    return out


def scrape() -> List[ChallengeRecord]:
    session = create_session()
    raw_events: List[Dict[str, str]] = []
    for season_year, url in SEASON_URLS:
        resp = safe_get(session, url)
        if resp is not None:
            raw_events.extend(extract_events_from_html(resp.text, season_year))
    save_source_cache(SOURCE_NAME, raw_events)

    records: List[ChallengeRecord] = []
    for ev in raw_events:
        start, end = parse_mlh_dates(ev["date_str"], int(ev["season_year"]))
        badges = [b.strip().lower() for b in ev.get("badges", "").split(",") if b.strip()]
        rec = build_record(
            title=ev["title"],
            platform="MLH",
            source=SOURCE_NAME,
            url=ev["url"],
            challenge_type="hackathon",
            prize="MLH & Sponsor Prizes",
            start_date=start,
            end_date=end,
            tags=["mlh", "hackathon", ev["mode"].lower(), *badges],
            description=f"Official Major League Hacking ({ev['season_year']} Season) hackathon · {ev['location']} ({ev['mode']}).",
            organizer="Major League Hacking",
            mode=ev["mode"],
            category_hint=" ".join([ev["title"], *badges]),
        )
        if rec:
            records.append(rec)

    logger.info("MLH yielded %d active/upcoming hackathons", len(records))
    return records

