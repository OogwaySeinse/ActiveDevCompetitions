# ⚙ WUNDERDEV // Active Software Development Competitions

> **A live, daily-updated monitor of every open software development competition** — hackathons, paid open-source issue bounties, engineering & AppSec challenges, coding contests and developer fellowships — with live countdowns, a deadline calendar and a developer AI matchmaker. Sister site to [ActiveQuantCompetitions](https://oogwayseinse.github.io/ActiveQuantCompetitions/), [ActiveMLCompetitions](https://oogwayseinse.github.io/ActiveMLCompetitions/) and [ActiveCryptoAuditChallenges](https://oogwayseinse.github.io/ActiveCryptoAuditChallenges/).

[![Daily Dev Challenges Update & Deploy](https://github.com/OogwaySeinse/ActiveDevCompetitions/actions/workflows/daily-update.yml/badge.svg)](https://github.com/OogwaySeinse/ActiveDevCompetitions/actions/workflows/daily-update.yml)

**Live site (after first deploy):** https://oogwayseinse.github.io/ActiveDevCompetitions/

## ✨ What it tracks

| Source | Module | What | How |
| --- | --- | --- | --- |
| **Devpost** | `devpost.py` | Open + upcoming software & AI hackathons | Public `/api/hackathons` JSON |
| **Topcoder** | `topcoder.py` | Active software development, F2F, QA & architecture challenges | Public Topcoder v6 `/challenges?status=ACTIVE` API |
| **GitHub / Algora** | `github_bounties.py` | Live paid open-source issue bounties (`💎 $…`) across GitHub repos | GitHub Search Issues API (`is:issue is:open`) |
| **Devfolio** | `devfolio.py` | Open & upcoming builder hackathons | Next.js `__NEXT_DATA__` dehydrated query payload |
| **Major League Hacking** | `mlh.py` | Official MLH 2026–2027 season digital & hybrid hackathons | Embedded Inertia `data-page` JSON on `/seasons/2026/events` |
| **HackerEarth** | `hackerearth.py` | Live developer hackathons & hiring challenges | Public `/challenges/` HTML + JSON-LD extraction |
| **Codeforces & LeetCode** | `codeforces.py` | Upcoming algorithmic rounds (`BEFORE`/`CODING`) & weekly contests | Codeforces `/api/contest.list` + recurring schedule |
| **Bugcrowd AppSec** | `bugcrowd.py` | Public software & cloud application security bug bounties | Public `/engagements.json` API |
| **Curated** | `curated.py` | Paid OSS fellowships (GSoC, LFX, Outreachy, MLH Fellowship) & systems arenas (Fly.io Gossip Glomers, Protohackers, CodeCrafters) | Static verified registry |

Every record is normalised into one schema (`scraper/models.py`): USD-normalised prize (INR/EUR/GBP/CAD/SGD/AUD/… via live FX), start/end, live status (`active`, `ending_soon`, `upcoming`, `ongoing`), **challenge type** (`hackathon`, `dev_challenge`, `oss_bounty`, `coding_contest`, `fellowship`), **engineering domain** (AI & LLM Apps, Cloud & DevOps, Systems & Infrastructure, Developer Tools, Web & Full-Stack, Mobile & Cross-Platform, Security & AppSec, Data & Databases, Open Source, Game Dev & XR, Algorithms & CP), **tech stack**, **languages**, difficulty tier, repo link and participant/submission count. Records are deduplicated (URL + fuzzy title), annotated with first-seen / NEW / prize-delta / deadline-shift history, and written to `data/challenges.{json,csv}`.

If a source breaks, the pipeline falls back to its last good snapshot (re-validated against today's date so expired items drop out) and the dashboard's **feed health** panel shows it.

## 🖥️ Dashboard (`apps/dashboard/`)

React 18 + Vite 6 + TypeScript + Tailwind v4 + TanStack Table + Recharts, styled like the sibling arenas (cream frame, smoked glass, drifting systems/engineering ASCII canvas).

- **Hero** with a pausable *Closing next* ticker and flagship prize cards.
- **Live Arena** (`#live-arena`): view segments (⚡ Live Contests · Hackathons · Dev Challenges · OSS Bounties · Coding Contests · Fellowships · All), quick presets (closing ≤ 7d, ≥ $10K, beginner-friendly, new, saved), facets for platform / domain / stack / language / status / tier / min pool, live minute-level countdowns, elapsed-window meters, bookmarks, shareable URL filters, CSV export, and **one-click `.ics` calendar export with a 24h reminder**.
- **Telemetry** tab: venues, 8-week deadline calendar, engineering domain donut, tech stacks and a daily trend (from `data/history/snapshots`).
- **Developer Matchmaker** (`#ai-matchmaker`): archetypes (Full-Stack AI Builder, Open-Source Bounty Hunter, Systems & Cloud Engineer, First Hackathon / Student, Competitive Programmer) + brief, languages, types, experience, goal and hours/week → ranked matches with *why it fits*, watch-outs and a phase-by-phase execution plan. Runs fully in the browser; optionally refined by a Gemini Cloudflare Worker.
- The page re-polls `challenges.json` every 10 minutes and hides anything whose deadline passes while the tab is open.

## 🚀 Quickstart

```powershell
# Python 3.11+
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m scraper                    # all sources
.venv\Scripts\python -m scraper --only devpost topcoder   # subset

# Dashboard (Node 20+)
cd apps/dashboard
npm install
npm run dev      # http://localhost:5173
npm run build    # static site in dist/
```

The scraper writes `data/challenges.json` / `.csv` and mirrors them into `apps/dashboard/public/data/`.

## ☁️ Deploy to GitHub Pages

1. Push this folder to `https://github.com/OogwaySeinse/ActiveDevCompetitions`.
2. *Settings → Pages → Build and deployment → Source:* **GitHub Actions**.
3. *Actions → "Daily Dev Challenges Update & Deploy" → Run workflow.*

It then refreshes every day at **06:00 UTC**. No API keys are required for any source.

## ✦ Optional: Gemini worker for the Matchmaker

```powershell
cd workers/recommender
npm install
npx wrangler login
npx wrangler secret put GEMINI_API_KEY
npx wrangler deploy
```

Paste the Worker URL into **⚙ Connect Gemini worker** in the Matchmaker, or set a repository variable `VITE_RECOMMENDER_URL` so builds use it automatically. If the worker is unreachable the local ranker is used transparently.

## Repository layout

```
scraper/                 python -m scraper
  sources/               one module per platform (devpost, topcoder, github_bounties, devfolio, mlh, hackerearth, codeforces, bugcrowd, curated)
  flight.py              Next.js __NEXT_DATA__ & RSC payload parser
  normalize.py           prizes→USD, dates/status, domain/stack/language taxonomy
  dedupe.py, history.py, fx.py, pipeline.py
tests/                   pytest (parsers, normalisation, dedupe, history)
data/                    challenges.json/.csv, cache/, history/
apps/dashboard/          React dashboard
workers/recommender/     optional Gemini proxy (Cloudflare Worker)
.github/workflows/       daily scrape → commit → build → Pages
```

> Always confirm scope, rules, eligibility and terms on the official challenge page before participating.

