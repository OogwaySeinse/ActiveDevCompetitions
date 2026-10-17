from __future__ import annotations

from typing import Callable, Dict, List

from scraper.models import ChallengeRecord
from scraper.sources import (
    bugcrowd,
    codeforces,
    curated,
    devfolio,
    devpost,
    github_bounties,
    hackerearth,
    mlh,
    topcoder,
)

ALL_SCRAPERS: Dict[str, Callable[[], List[ChallengeRecord]]] = {
    "devpost": devpost.scrape,
    "topcoder": topcoder.scrape,
    "github_bounties": github_bounties.scrape,
    "devfolio": devfolio.scrape,
    "mlh": mlh.scrape,
    "hackerearth": hackerearth.scrape,
    "codeforces": codeforces.scrape,
    "bugcrowd": bugcrowd.scrape,
    "curated": curated.scrape,
}

