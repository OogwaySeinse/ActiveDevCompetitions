"""GitHub & Algora open-source development bounties via the public GitHub Search Issues API."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from scraper.http import create_session, safe_get_json, save_source_cache
from scraper.models import ChallengeRecord
from scraper.normalize import build_record

logger = logging.getLogger(__name__)

SOURCE_NAME = "github_bounties"
SEARCH_URL = "https://api.github.com/search/issues"

QUERIES = [
    'is:issue is:open "algora.io" in:body sort:updated-desc',
    'is:issue is:open label:"💎 Bounty" sort:updated-desc',
    'is:issue is:open label:bounty "$" in:title,body sort:updated-desc',
]

_DOLLAR_RE = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})+|\d{2,6})(?:\.\d{2})?(?!\d)")


def extract_bounty_amount(title: str, labels: List[str], body: str) -> Optional[float]:
    """Extract USD bounty amount from issue labels, title, or body."""
    for text in [*labels, title, body[:1200]]:
        for m in _DOLLAR_RE.finditer(text or ""):
            try:
                val = float(m.group(1).replace(",", ""))
                if 20 <= val <= 100_000:
                    return val
            except ValueError:
                continue
    return None


def parse_issues(items: List[Dict[str, Any]]) -> List[ChallengeRecord]:
    records: List[ChallengeRecord] = []
    seen_urls = set()

    for it in items:
        if not isinstance(it, dict) or "pull_request" in it:
            continue
        html_url = str(it.get("html_url") or "")
        if not html_url or html_url in seen_urls:
            continue

        title = str(it.get("title") or "").strip()
        body = str(it.get("body") or "")
        labels = [str(l.get("name") or "") for l in (it.get("labels") or []) if isinstance(l, dict) and l.get("name")]
        amount = extract_bounty_amount(title, labels, body)
        if amount is None:
            continue

        seen_urls.add(html_url)
        repo_api = str(it.get("repository_url") or "")
        repo_slug = "/".join(repo_api.rstrip("/").split("/")[-2:]) if "/" in repo_api else "github/open-source"
        repo_url = f"https://github.com/{repo_slug}" if "/" in repo_slug else None
        org = repo_slug.split("/")[0] if "/" in repo_slug else "GitHub"

        is_algora = "algora" in " ".join(labels).lower() or "algora.io" in body.lower()
        platform = "Algora / GitHub" if is_algora else "GitHub Bounties"

        clean_title = re.sub(r"^\s*\[?\$\d[\d,]*\]?\s*[-:·]?\s*", "", title).strip() or title
        full_title = f"[{repo_slug}] {clean_title}"

        rec = build_record(
            title=full_title,
            platform=platform,
            source=SOURCE_NAME,
            url=html_url,
            challenge_type="oss_bounty",
            prize=amount,
            prize_currency="USD",
            start_date=it.get("created_at"),
            end_date=None,
            tags=["open-source", "github", "bounty", org.lower(), *[l.lower() for l in labels[:5]]],
            description=body[:420] or f"Open-source issue bounty on {repo_slug}.",
            organizer=org,
            mode="Online",
            submissions_count=it.get("comments") or None,
            repo_url=repo_url,
            logo_url=((it.get("user") or {}).get("avatar_url") if isinstance(it.get("user"), dict) else None),
            category_hint=" ".join([repo_slug, *labels]),
        )
        if rec:
            records.append(rec)
    return records


def scrape() -> List[ChallengeRecord]:
    session = create_session()
    all_items: List[Dict[str, Any]] = []
    for q in QUERIES:
        data = safe_get_json(
            session,
            SEARCH_URL,
            params={"q": q, "per_page": 35},
            headers={"Accept": "application/vnd.github+json"},
            delay=0.35,
        )
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            all_items.extend(data["items"])
    save_source_cache(SOURCE_NAME, all_items)
    records = parse_issues(all_items)
    logger.info("GitHub/Algora yielded %d open-source bounties", len(records))
    return records

