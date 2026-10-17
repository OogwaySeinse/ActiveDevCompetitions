"""Normalisation helpers: dates, prizes -> USD, URL canonicalisation, developer taxonomy inference."""

from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timezone
from typing import Iterable, List, Optional, Tuple, Union
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from dateutil import parser as date_parser

from scraper.fx import get_fx_rates
from scraper.models import ChallengeRecord

ENDING_SOON_DAYS = 7

TRACKING_QUERY_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "ref",
    "source",
    "fbclid",
    "gclid",
}

CHALLENGE_TYPES = ("hackathon", "dev_challenge", "oss_bounty", "coding_contest", "fellowship")

CURRENCY_ALIASES = {
    "$": "USD",
    "us$": "USD",
    "usd": "USD",
    "usdc": "USDC",
    "usdt": "USDT",
    "€": "EUR",
    "eur": "EUR",
    "£": "GBP",
    "gbp": "GBP",
    "cad": "CAD",
    "c$": "CAD",
    "aud": "AUD",
    "a$": "AUD",
    "₹": "INR",
    "inr": "INR",
    "rs": "INR",
    "¥": "JPY",
    "jpy": "JPY",
    "cny": "CNY",
    "rmb": "CNY",
    "sgd": "SGD",
    "s$": "SGD",
    "chf": "CHF",
    "brl": "BRL",
    "r$": "BRL",
}

# ---------------------------------------------------------------------------
# Taxonomy: Software engineering domain (category), stack (ecosystem), languages
# ---------------------------------------------------------------------------

CATEGORY_RULES: List[Tuple[str, List[str]]] = [
    (
        "AI Agents & LLM Apps",
        [
            "ai agent*",
            "agentic",
            "llm*",
            "rag",
            "genai",
            "generative ai",
            "gemini",
            "openai",
            "anthropic",
            "claude",
            "langchain",
            "llamaindex",
            "mcp",
            "model context protocol",
            "multimodal",
            "voice ai",
            "copilot*",
            "machine learning",
            "natural language",
            "computer vision",
        ],
    ),
    (
        "Cloud, DevOps & Infra",
        [
            "kubernetes",
            "k8s",
            "docker",
            "container*",
            "devops",
            "cloud native",
            "cloud-native",
            "serverless",
            "aws",
            "gcp",
            "google cloud",
            "azure",
            "cloudflare",
            "terraform",
            "observability",
            "opentelemetry",
            "prometheus",
            "ebpf",
            "cicd",
            "ci/cd",
            "microservices",
            "distributed system*",
        ],
    ),
    (
        "Developer Tools & CLI",
        [
            "devtool*",
            "developer tool*",
            "cli",
            "sdk",
            "ide",
            "vscode",
            "vs code",
            "neovim",
            "compiler*",
            "linter*",
            "transpiler*",
            "lsp",
            "language server",
            "wasm",
            "webassembly",
            "testing framework*",
            "debugging",
            "git",
            "package manager",
        ],
    ),
    (
        "Open Source & Core Systems",
        [
            "open source",
            "open-source",
            "oss",
            "linux kernel",
            "operating system*",
            "embedded",
            "firmware",
            "iot",
            "hardware",
            "robotics",
            "network*",
            "protocol*",
            "runtime",
            "virtual machine",
            "posix",
            "raft",
            "consensus",
        ],
    ),
    (
        "Mobile & Cross-Platform",
        [
            "ios",
            "android",
            "flutter",
            "react native",
            "swift",
            "swiftui",
            "kotlin",
            "jetpack compose",
            "mobile app*",
            "wearable*",
        ],
    ),
    (
        "Data Engineering & Databases",
        [
            "database*",
            "postgres*",
            "sqlite",
            "duckdb",
            "clickhouse",
            "redis",
            "kafka",
            "spark",
            "bigquery",
            "snowflake",
            "data pipeline*",
            "etl",
            "analytics",
            "graphql",
            "vector db",
            "olap",
            "sql",
        ],
    ),
    (
        "Security & AppSec",
        [
            "cybersecurity",
            "security",
            "appsec",
            "bug bounty",
            "vulnerability",
            "penetration",
            "pentest*",
            "zero trust",
            "cryptography",
            "authentication",
            "oauth*",
            "passkey*",
            "devsecops",
            "ctf",
        ],
    ),
    (
        "Game Dev, XR & Creative Tech",
        [
            "game*",
            "gaming",
            "unity",
            "unreal",
            "godot",
            "webgl",
            "three.js",
            "xr",
            "vr",
            "ar",
            "spatial computing",
            "shader*",
            "audio",
            "media",
        ],
    ),
    (
        "Algorithms & Competitive Coding",
        [
            "competitive programming",
            "codeforces",
            "leetcode",
            "atcoder",
            "icpc",
            "algorithm*",
            "data structure*",
            "dynamic programming",
            "graph theory",
            "combinatorics",
            "advent of code",
            "project euler",
        ],
    ),
    (
        "Fintech & Enterprise Systems",
        [
            "fintech",
            "banking",
            "payment*",
            "stripe",
            "enterprise",
            "crm",
            "erp",
            "healthcare",
            "healthtech",
            "biotech",
            "edtech",
            "education",
            "climate",
            "sustainability",
            "civic",
            "social good",
        ],
    ),
    (
        "Full-Stack & Web Apps",
        [
            "full-stack",
            "fullstack",
            "full stack",
            "frontend",
            "front-end",
            "backend",
            "back-end",
            "web app*",
            "nextjs",
            "next.js",
            "react",
            "vue",
            "svelte*",
            "angular",
            "tailwind*",
            "node.js",
            "nodejs",
            "typescript",
            "javascript",
            "rest api",
            "saas",
            "browser extension*",
            "chrome extension*",
        ],
    ),
]

DEFAULT_CATEGORY_BY_TYPE = {
    "hackathon": "Full-Stack & Web Apps",
    "dev_challenge": "Full-Stack & Web Apps",
    "oss_bounty": "Open Source & Core Systems",
    "coding_contest": "Algorithms & Competitive Coding",
    "fellowship": "Open Source & Core Systems",
}

ECOSYSTEM_RULES: List[Tuple[str, List[str]]] = [
    (
        "AI / LLM Stack",
        [
            "llm*",
            "ai agent*",
            "agentic",
            "rag",
            "gemini",
            "openai",
            "anthropic",
            "langchain",
            "llamaindex",
            "mcp",
            "pytorch",
            "huggingface",
            "genai",
            "generative ai",
        ],
    ),
    (
        "Cloud & Kubernetes",
        [
            "kubernetes",
            "k8s",
            "docker",
            "cloud native",
            "cloud-native",
            "aws",
            "gcp",
            "google cloud",
            "azure",
            "cloudflare",
            "terraform",
            "serverless",
            "devops",
            "opentelemetry",
            "cncf",
        ],
    ),
    (
        "Systems & Native",
        [
            "rust",
            "c++",
            "golang",
            "zig",
            "linux",
            "kernel",
            "ebpf",
            "wasm",
            "webassembly",
            "embedded",
            "hardware",
            "iot",
            "robotics",
            "systems programming",
        ],
    ),
    (
        "Mobile (iOS / Android)",
        [
            "ios",
            "android",
            "flutter",
            "react native",
            "swift",
            "swiftui",
            "kotlin",
            "mobile",
        ],
    ),
    (
        "Data & Streaming",
        [
            "postgres*",
            "sqlite",
            "duckdb",
            "clickhouse",
            "kafka",
            "spark",
            "bigquery",
            "snowflake",
            "redis",
            "database*",
            "sql",
            "data engineering",
        ],
    ),
    (
        "Open Source / GitHub",
        [
            "open source",
            "open-source",
            "algora",
            "polar.sh",
            "gsoc",
            "outreachy",
            "lfx",
            "github bounty",
            "pull request",
        ],
    ),
    (
        "Web & Full-Stack",
        [
            "react",
            "nextjs",
            "next.js",
            "vue",
            "svelte*",
            "angular",
            "typescript",
            "javascript",
            "node.js",
            "nodejs",
            "full-stack",
            "fullstack",
            "web",
            "frontend",
            "backend",
            "django",
            "fastapi",
            "rails",
        ],
    ),
]

LANGUAGE_RULES: List[Tuple[str, List[str]]] = [
    ("TypeScript", ["typescript", "javascript", "node.js", "nodejs", "react", "nextjs", "next.js", "vue", "svelte*", "angular", "deno", "bun"]),
    ("Python", ["python", "fastapi", "django", "flask", "pytorch", "langchain", "pandas"]),
    ("Rust", ["rust", "cargo", "tokio", "wasm", "webassembly"]),
    ("Go", ["golang", "go ", "kubernetes", "docker", "cncf", "terraform"]),
    ("Java", ["java", "spring", "spring boot", "jvm", "maven", "gradle", "scala"]),
    ("C / C++", ["c++", "cpp", "clang", "llvm", "embedded", "firmware", "cuda", "opengl"]),
    ("C#", ["c#", "csharp", ".net", "dotnet", "unity", "blazor"]),
    ("Swift / Kotlin", ["swift", "swiftui", "kotlin", "ios", "android", "flutter", "dart"]),
    ("SQL", ["sql", "postgres*", "postgresql", "mysql", "sqlite", "duckdb", "clickhouse", "bigquery", "snowflake"]),
]

_PATTERN_CACHE: dict = {}

LANGUAGE_CANON = {
    "typescript": "TypeScript",
    "javascript": "TypeScript",
    "js": "TypeScript",
    "ts": "TypeScript",
    "node.js": "TypeScript",
    "nodejs": "TypeScript",
    "react": "TypeScript",
    "next.js": "TypeScript",
    "nextjs": "TypeScript",
    "python": "Python",
    "py": "Python",
    "rust": "Rust",
    "go": "Go",
    "golang": "Go",
    "java": "Java",
    "scala": "Java",
    "c++": "C / C++",
    "c": "C / C++",
    "cpp": "C / C++",
    "c/c++": "C / C++",
    "c#": "C#",
    "csharp": "C#",
    ".net": "C#",
    "swift": "Swift / Kotlin",
    "kotlin": "Swift / Kotlin",
    "dart": "Swift / Kotlin",
    "flutter": "Swift / Kotlin",
    "sql": "SQL",
    "postgresql": "SQL",
}


def _kw_pattern(keyword: str) -> "re.Pattern[str]":
    pat = _PATTERN_CACHE.get(keyword)
    if pat is None:
        if keyword.endswith("*"):
            body = re.escape(keyword[:-1])
            pat = re.compile(rf"(?<![a-z0-9]){body}")
        else:
            pat = re.compile(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])")
        _PATTERN_CACHE[keyword] = pat
    return pat


def _matches(hay: str, keywords: Iterable[str]) -> bool:
    return any(_kw_pattern(k).search(hay) for k in keywords)


def _haystack(*parts: Union[str, Iterable[str], None]) -> str:
    chunks: List[str] = []
    for p in parts:
        if not p:
            continue
        if isinstance(p, str):
            chunks.append(p)
        else:
            chunks.extend(str(x) for x in p)
    return f" {' '.join(chunks).lower()} "


def infer_category(title: str, description: str = "", tags: Iterable[str] = (), hint: str = "") -> Optional[str]:
    strong = _haystack(hint, title, tags)
    for category, keywords in CATEGORY_RULES:
        if _matches(strong, keywords):
            return category
    weak = _haystack(description[:600])
    for category, keywords in CATEGORY_RULES:
        if _matches(weak, keywords):
            return category
    return None


def infer_ecosystem(title: str, description: str = "", tags: Iterable[str] = (), hint: str = "") -> Optional[str]:
    strong = _haystack(hint, title, tags)
    for eco, keywords in ECOSYSTEM_RULES:
        if _matches(strong, keywords):
            return eco
    weak = _haystack(description[:600])
    for eco, keywords in ECOSYSTEM_RULES:
        if _matches(weak, keywords):
            return eco
    return None


def infer_languages(title: str, description: str = "", tags: Iterable[str] = (), ecosystem: str = "", challenge_type: str = "") -> List[str]:
    hay = _haystack(title, tags, description[:600])
    langs = [lang for lang, keys in LANGUAGE_RULES if _matches(hay, keys)]
    if not langs:
        if challenge_type == "coding_contest":
            return ["C / C++", "Python", "Java"]
        defaults = {
            "Web & Full-Stack": ["TypeScript", "Python"],
            "AI / LLM Stack": ["Python", "TypeScript"],
            "Cloud & Kubernetes": ["Go", "Python"],
            "Systems & Native": ["Rust", "C / C++"],
            "Mobile (iOS / Android)": ["Swift / Kotlin", "TypeScript"],
            "Data & Streaming": ["Python", "SQL"],
            "Open Source / GitHub": ["TypeScript", "Python", "Rust"],
            "Cross-Stack / General": ["TypeScript", "Python"],
        }
        langs = list(defaults.get(ecosystem, ["TypeScript", "Python"]))
    return langs[:4]


# ---------------------------------------------------------------------------
# URL / ID helpers
# ---------------------------------------------------------------------------


def canonicalize_url(url: str) -> str:
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return ""
    if not parsed.netloc:
        return ""
    query = [(k, v) for k, v in parse_qsl(parsed.query) if k.lower() not in TRACKING_QUERY_KEYS]
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parsed.path.rstrip("/") or "/"
    return urlunparse(("https", netloc, path, "", urlencode(query), ""))


def slugify_title(title: str) -> str:
    t = re.sub(r"[^a-z0-9]+", " ", (title or "").lower())
    t = re.sub(r"\b(hackathon|challenge|competition|bounty|the|developer|dev|coding|contest)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def make_record_id(platform: str, title: str, url: str) -> str:
    raw = f"{platform}|{title}|{canonicalize_url(url)}".lower()
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:14]


# ---------------------------------------------------------------------------
# Prize parsing
# ---------------------------------------------------------------------------


def to_usd(amount: float, currency: str) -> float:
    rates = get_fx_rates()
    rate = rates.get((currency or "USD").upper(), 0.0)
    return round(float(amount) * rate, 2) if rate else 0.0


def format_usd_label(amount_usd: float) -> str:
    if amount_usd >= 1_000_000:
        return f"${amount_usd / 1_000_000:,.2f}M".replace(".00M", "M")
    if amount_usd >= 10_000:
        return f"${amount_usd / 1_000:,.0f}K"
    if amount_usd >= 1_000:
        return f"${amount_usd / 1_000:,.1f}K".replace(".0K", "K")
    return f"${amount_usd:,.0f}"


def format_prize(amount: float, currency: str) -> Tuple[str, float]:
    """Return (display label, usd value) for a numeric amount in some currency."""
    cur = (currency or "USD").upper()
    usd = to_usd(amount, cur)
    if cur in ("USD", "USDC", "USDT"):
        label = format_usd_label(usd)
        if cur != "USD":
            label = f"{label} {cur}"
        return label, usd
    pretty_amount = f"{amount:,.2f}".rstrip("0").rstrip(".") if amount < 100 else f"{amount:,.0f}"
    return f"{pretty_amount} {cur}", usd


_AMOUNT_RE = re.compile(
    r"(?<![a-z0-9])(?P<pre>[$€£₹¥]|us\$|cad|aud|sgd|brl|r\$|usdc|usdt|usd|inr|rs\.?)?\s?"
    r"(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s?"
    r"(?P<mult>k|m|mm|million|thousand)?(?![a-z0-9])\s?(?:in\s)?"
    r"(?P<post>usdc|usdt|usd|eur|gbp|cad|aud|inr|jpy|cny|rmb|sgd|chf|brl)?(?![a-z0-9])",
    re.IGNORECASE,
)


def _fallback_label(text: str) -> str:
    first = next((ln.strip(" -•*:") for ln in text.splitlines() if ln.strip(" -•*:")), "")
    if not first:
        return "Leaderboard / Non-cash"
    if len(first) > 42:
        return "Prizes & Swag (see page)"
    return first


def parse_prize(raw: Optional[Union[str, float, int]], default_currency: str = "USD") -> Tuple[str, float, str]:
    """Parse free-text prize strings into (label, usd, currency). Picks the largest amount."""
    if raw is None or raw == "":
        return "Leaderboard / Non-cash", 0.0, default_currency
    if isinstance(raw, (int, float)):
        label, usd = format_prize(float(raw), default_currency)
        return (label, usd, default_currency) if usd > 0 else ("Leaderboard / Non-cash", 0.0, default_currency)

    text = re.sub(r"<[^>]+>", "", str(raw)).replace("$$", "$")
    best_usd = 0.0
    best = ("", 0.0, default_currency)
    for m in _AMOUNT_RE.finditer(text):
        pre = (m.group("pre") or "").lower().rstrip(".")
        post = (m.group("post") or "").lower()
        if not pre and not post:
            continue
        try:
            num = float(m.group("num").replace(",", ""))
        except ValueError:
            continue
        mult = (m.group("mult") or "").lower()
        if mult in ("k", "thousand"):
            num *= 1_000
        elif mult in ("m", "mm", "million"):
            num *= 1_000_000
        cur = CURRENCY_ALIASES.get(post) or CURRENCY_ALIASES.get(pre) or default_currency
        usd = to_usd(num, cur)
        if usd > best_usd:
            best_usd = usd
            label, _ = format_prize(num, cur)
            best = (label, usd, cur)
    if best_usd <= 0:
        return _fallback_label(text), 0.0, default_currency
    return best


# ---------------------------------------------------------------------------
# Dates & status
# ---------------------------------------------------------------------------


def parse_date(raw: Optional[Union[str, int, float]]) -> Optional[str]:
    """Return an ISO-8601 UTC timestamp string (YYYY-MM-DDTHH:MM:SSZ) or None."""
    if raw is None or raw == "":
        return None
    try:
        if isinstance(raw, (int, float)) or (isinstance(raw, str) and raw.strip().isdigit()):
            ts = float(raw)
            if ts > 1e12:  # milliseconds
                ts /= 1000.0
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        else:
            dt = date_parser.parse(str(raw))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt = dt.astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, OverflowError, TypeError):
        return None


def _to_dt(iso: Optional[str]) -> Optional[datetime]:
    if not iso:
        return None
    try:
        dt = date_parser.parse(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, OverflowError):
        return None


def compute_days_remaining(end_iso: Optional[str], now: Optional[datetime] = None) -> Optional[int]:
    end = _to_dt(end_iso)
    if end is None:
        return None
    ref = now or datetime.now(timezone.utc)
    seconds = (end - ref).total_seconds()
    return int(seconds // 86400) if seconds >= 0 else -1


def resolve_status(
    start_iso: Optional[str],
    end_iso: Optional[str],
    raw_status: str = "",
    now: Optional[datetime] = None,
) -> Tuple[bool, str, Optional[int]]:
    """Return (is_active, status, days_remaining).

    status in {"active", "ending_soon", "upcoming", "ongoing"}; inactive records are dropped.
    """
    ref = now or datetime.now(timezone.utc)
    raw = (raw_status or "").lower()
    if raw in ("ended", "finished", "complete", "completed", "closed", "cancelled", "canceled", "past", "paused"):
        return False, "ended", None

    start = _to_dt(start_iso)
    end = _to_dt(end_iso)
    days = compute_days_remaining(end_iso, ref)

    if end is not None and end < ref:
        return False, "ended", days
    if start is not None and start > ref:
        return True, "upcoming", days
    if raw in ("upcoming", "created", "scheduled", "future", "registration", "before"):
        return True, "upcoming", days
    if end is None:
        return True, "ongoing", None
    if days is not None and days <= ENDING_SOON_DAYS:
        return True, "ending_soon", days
    return True, "active", days


def infer_difficulty(challenge_type: str, prize_usd: float, title: str, description: str) -> str:
    hay = _haystack(title, description[:400])
    if _matches(hay, ("first2finish", "good first issue", "beginner", "starter", "first timer*", "intro*", "student", "div. 3", "div. 4")):
        return "Beginner"
    if _matches(hay, ("distributed system*", "compiler*", "kernel", "ebpf", "div. 1", "grandmaster", "zero-day", "architecture")):
        return "Expert"
    if challenge_type == "oss_bounty":
        if prize_usd >= 2_500:
            return "Expert"
        if prize_usd >= 800:
            return "Advanced"
        if 0 < prize_usd <= 150:
            return "Beginner"
        return "Intermediate"
    if prize_usd >= 100_000:
        return "Advanced"
    if challenge_type == "coding_contest":
        if "div. 2" in hay or "biweekly" in hay or "weekly" in hay:
            return "Intermediate"
        return "Advanced"
    return "Intermediate"


def clean_text(text: Optional[str], limit: int = 420) -> str:
    if not text:
        return ""
    t = re.sub(r"<[^>]+>", " ", str(text))
    t = re.sub(r"[#*_`>\[\]]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[: limit - 1] + "…" if len(t) > limit else t


def build_record(
    *,
    title: str,
    platform: str,
    source: str,
    url: str,
    challenge_type: str,
    prize: Optional[Union[str, float, int]] = None,
    prize_currency: str = "USD",
    start_date: Optional[Union[str, int, float]] = None,
    end_date: Optional[Union[str, int, float]] = None,
    raw_status: str = "",
    category: Optional[str] = None,
    ecosystem: Optional[str] = None,
    languages: Optional[List[str]] = None,
    tags: Optional[Iterable[str]] = None,
    description: str = "",
    organizer: str = "",
    difficulty: Optional[str] = None,
    mode: str = "Online",
    participants_count: Optional[int] = None,
    submissions_count: Optional[int] = None,
    repo_url: Optional[str] = None,
    logo_url: Optional[str] = None,
    category_hint: str = "",
    now: Optional[datetime] = None,
) -> Optional[ChallengeRecord]:
    """Normalise raw scraped fields into a ChallengeRecord, or None if inactive/invalid."""
    title = re.sub(r"\s+", " ", (title or "")).strip()
    if not title or not url:
        return None
    if challenge_type not in CHALLENGE_TYPES:
        challenge_type = "hackathon"

    start_iso = parse_date(start_date)
    end_iso = parse_date(end_date)
    active, status, days = resolve_status(start_iso, end_iso, raw_status, now)
    if not active:
        return None
    if challenge_type in ("oss_bounty", "fellowship") and end_iso is None:
        status = "ongoing"

    label, usd, currency = parse_prize(prize, prize_currency)
    tag_list = [t.strip().lower() for t in (tags or []) if t and str(t).strip()]
    desc = clean_text(description)

    eco = ecosystem or infer_ecosystem(title, desc, tag_list, category_hint)
    if not eco:
        if challenge_type == "oss_bounty":
            eco = "Open Source / GitHub"
        elif challenge_type == "coding_contest":
            eco = "Cross-Stack / General"
        else:
            eco = "Web & Full-Stack"
    cat = category or infer_category(title, desc, tag_list, category_hint) or DEFAULT_CATEGORY_BY_TYPE[challenge_type]
    langs = languages if languages else infer_languages(title, desc, tag_list, eco, challenge_type)
    langs = list(dict.fromkeys(LANGUAGE_CANON.get(str(l).lower(), str(l)) for l in langs))[:4]

    return ChallengeRecord(
        id=make_record_id(platform, title, url),
        title=title,
        platform=platform,
        source=source,
        url=url,
        prize=label,
        prize_usd=usd,
        prize_currency=currency,
        prize_raw=str(prize) if prize is not None else "",
        start_date=start_iso,
        end_date=end_iso,
        days_remaining=days,
        status=status,
        challenge_type=challenge_type,
        category=cat,
        ecosystem=eco,
        languages=langs,
        tags=sorted(set(tag_list))[:10],
        description=desc,
        organizer=organizer or platform,
        difficulty=difficulty or infer_difficulty(challenge_type, usd, title, desc),
        mode=mode or "Online",
        participants_count=participants_count,
        submissions_count=submissions_count,
        repo_url=repo_url,
        logo_url=logo_url,
        scraped_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def refresh_status(rec: ChallengeRecord, now: Optional[datetime] = None) -> bool:
    """Recompute status/days for a cached record. Returns False if it has expired."""
    active, status, days = resolve_status(rec.start_date, rec.end_date, "", now)
    if not active:
        return False
    rec.status = "ongoing" if rec.challenge_type in ("oss_bounty", "fellowship") and not rec.end_date else status
    rec.days_remaining = days
    return True


def today_utc() -> date:
    return datetime.now(timezone.utc).date()
