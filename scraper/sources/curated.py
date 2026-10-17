"""Curated developer fellowships, open-source stipends, and evergreen systems engineering practice arenas.

Includes flagship paid open-source fellowships (GSoC, LFX Mentorship, Outreachy, MLH Fellowship,
Summer of Bitcoin, Sovereign Tech Fellowship) and evergreen systems challenges (CodeCrafters,
Fly.io Gossip Glomers, Protohackers, Advent of Code, Project Euler, Exercism).
"""

from __future__ import annotations

import logging
from typing import Dict, List

from scraper.models import ChallengeRecord
from scraper.normalize import build_record

logger = logging.getLogger(__name__)

SOURCE_NAME = "curated"

FELLOWSHIPS_AND_ARENAS: List[Dict] = [
    {
        "title": "Google Summer of Code (GSoC)",
        "platform": "Google Open Source",
        "url": "https://summerofcode.withgoogle.com/",
        "prize": "$6,600",
        "category": "Open Source & Core Systems",
        "ecosystem": "Open Source / GitHub",
        "languages": ["Python", "Rust", "Go", "C / C++"],
        "difficulty": "Intermediate",
        "tags": ["fellowship", "gsoc", "open-source", "mentorship", "stipend"],
        "description": "Global online program focused on bringing new contributors into open-source software development across 180+ mentoring organizations, with stipends up to $6,600.",
    },
    {
        "title": "LFX Mentorship (Linux Foundation & CNCF)",
        "platform": "Linux Foundation",
        "url": "https://mentorship.lfx.linuxfoundation.org/",
        "prize": "$6,600",
        "category": "Cloud, DevOps & Infra",
        "ecosystem": "Cloud & Kubernetes",
        "languages": ["Go", "Rust", "C / C++", "Python"],
        "difficulty": "Intermediate",
        "tags": ["fellowship", "lfx", "kubernetes", "cncf", "linux-kernel", "open-source"],
        "description": "Spring, Summer, and Fall paid open-source mentorships across Kubernetes, Linux Kernel, Prometheus, Envoy, OpenTelemetry, Cilium, and CNCF projects.",
    },
    {
        "title": "Outreachy Open-Source Internships",
        "platform": "Outreachy",
        "url": "https://www.outreachy.org/",
        "prize": "$7,000",
        "category": "Open Source & Core Systems",
        "ecosystem": "Open Source / GitHub",
        "languages": ["Python", "TypeScript", "Rust", "C / C++"],
        "difficulty": "Beginner",
        "tags": ["fellowship", "outreachy", "open-source", "remote", "stipend"],
        "description": "Paid 3-month remote open-source and open-science internships ($7,000 stipend) with Mozilla, Debian, GNOME, Fedora, LLVM, Wikimedia, and OCaml.",
    },
    {
        "title": "MLH Fellowship (Software Engineering & Open Source)",
        "platform": "MLH",
        "url": "https://fellowship.mlh.io/",
        "prize": "$5,000",
        "category": "Full-Stack & Web Apps",
        "ecosystem": "Open Source / GitHub",
        "languages": ["TypeScript", "Python", "Rust", "Go"],
        "difficulty": "Intermediate",
        "tags": ["fellowship", "mlh", "open-source", "production-engineering", "sre"],
        "description": "12-week remote software engineering and site-reliability fellowship matching developers to Meta, AWS, Solana, and major open-source maintainers.",
    },
    {
        "title": "Fly.io Distributed Systems Challenges (Gossip Glomers)",
        "platform": "Fly.io",
        "url": "https://fly.io/dist-sys/",
        "prize": "Skill-building",
        "category": "Cloud, DevOps & Infra",
        "ecosystem": "Systems & Native",
        "languages": ["Go", "Rust", "Python", "Java"],
        "difficulty": "Advanced",
        "tags": ["practice", "distributed-systems", "raft", "consensus", "jepsen", "maelstrom"],
        "description": "Six progressive distributed-systems challenges built on Kyle Kingsbury's Jepsen Maelstrom workbench: broadcast, CRDT counters, Kafka logs, and Raft consensus.",
    },
    {
        "title": "Protohackers — Network & Socket Programming Arena",
        "platform": "Protohackers",
        "url": "https://protohackers.com/",
        "prize": "Leaderboard / Non-cash",
        "category": "Open Source & Core Systems",
        "ecosystem": "Systems & Native",
        "languages": ["Rust", "Go", "C / C++", "Python"],
        "difficulty": "Intermediate",
        "tags": ["practice", "networking", "tcp", "udp", "protocols", "systems"],
        "description": "Build and deploy live TCP/UDP network servers tested automatically against strict protocol specifications, custom binary framing, MITM proxies, and congestion control.",
    },
    {
        "title": "CodeCrafters — Build Your Own Redis, Git, Docker & SQLite",
        "platform": "CodeCrafters",
        "url": "https://codecrafters.io/",
        "prize": "Skill-building",
        "category": "Developer Tools & CLI",
        "ecosystem": "Systems & Native",
        "languages": ["Rust", "Go", "C / C++", "Python"],
        "difficulty": "Intermediate",
        "tags": ["practice", "systems", "redis", "git", "sqlite", "kafka", "bittorrent"],
        "description": "Step-by-step automated test-harness challenges to recreate Redis, Git, SQLite, Kafka, Docker, HTTP servers, DNS resolvers, and shells from scratch.",
    },
    {
        "title": "Advent of Code — Annual Systems & Algorithmic Puzzles",
        "platform": "Advent of Code",
        "url": "https://adventofcode.com/",
        "prize": "Leaderboard / Non-cash",
        "category": "Algorithms & Competitive Coding",
        "ecosystem": "Cross-Stack / General",
        "languages": ["Rust", "Python", "TypeScript", "Go"],
        "difficulty": "Intermediate",
        "tags": ["practice", "algorithms", "puzzles", "advent-of-code"],
        "description": "Two-part daily algorithmic and systems programming puzzles with global and private leaderboards across 500+ events and 10+ years of archives.",
    },
    {
        "title": "Exercism — 70+ Language Engineering Tracks",
        "platform": "Exercism",
        "url": "https://exercism.org/",
        "prize": "Skill-building",
        "category": "Developer Tools & CLI",
        "ecosystem": "Cross-Stack / General",
        "languages": ["Rust", "Go", "TypeScript", "Python"],
        "difficulty": "Beginner",
        "tags": ["practice", "mentorship", "open-source", "languages"],
        "description": "Open-source coding platform offering 70+ programming language tracks (Rust, Go, Zig, Elixir, Haskell, TypeScript, C++) with automated analyzers and human mentoring.",
    },
]


def scrape() -> List[ChallengeRecord]:
    records: List[ChallengeRecord] = []
    for arena in FELLOWSHIPS_AND_ARENAS:
        rec = build_record(
            title=arena["title"],
            platform=arena["platform"],
            source=SOURCE_NAME,
            url=arena["url"],
            challenge_type="fellowship",
            prize=arena["prize"],
            category=arena["category"],
            ecosystem=arena["ecosystem"],
            languages=arena["languages"],
            tags=arena["tags"],
            description=arena["description"],
            organizer=arena["platform"],
            difficulty=arena["difficulty"],
            mode="Online",
        )
        if rec:
            records.append(rec)
    logger.info("Curated developer fellowships & practice arenas: %d", len(records))
    return records

