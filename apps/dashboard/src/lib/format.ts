import type { Challenge, ChallengeStatus, ChallengeType, Difficulty, Filters, View } from "../types";

export const TYPE_META: Record<ChallengeType, { label: string; short: string; icon: string; color: string }> = {
  hackathon: { label: "Hackathon", short: "Hack", icon: "⌁", color: "#38bdf8" },
  dev_challenge: { label: "Dev Challenge", short: "Dev", icon: "⌘", color: "#a78bfa" },
  oss_bounty: { label: "OSS & AppSec Bounty", short: "Bounty", icon: "⌥", color: "#34d399" },
  coding_contest: { label: "Coding Contest", short: "Contest", icon: "⚡", color: "#fbbf24" },
  fellowship: { label: "Fellowship & Arena", short: "Fellowship", icon: "∞", color: "#f472b6" },
};

export const VIEW_TYPES: Record<View, ChallengeType[]> = {
  live: ["hackathon", "dev_challenge", "coding_contest"],
  hackathon: ["hackathon"],
  dev_challenge: ["dev_challenge"],
  oss_bounty: ["oss_bounty"],
  coding_contest: ["coding_contest"],
  fellowship: ["fellowship"],
  all: ["hackathon", "dev_challenge", "oss_bounty", "coding_contest", "fellowship"],
};

const PLATFORM_COLORS: Record<string, string> = {
  Devpost: "#38bdf8",
  Topcoder: "#a78bfa",
  "Algora / GitHub": "#34d399",
  "GitHub Bounties": "#5eead4",
  Devfolio: "#60a5fa",
  MLH: "#fb7185",
  HackerEarth: "#f59e0b",
  Codeforces: "#facc15",
  LeetCode: "#fb923c",
  Bugcrowd: "#f472b6",
  "Google Open Source": "#4ade80",
  "Linux Foundation": "#818cf8",
  Outreachy: "#e879f9",
  "Fly.io": "#c084fc",
  Protohackers: "#2dd4bf",
  CodeCrafters: "#fbbf24",
  "Advent of Code": "#34d399",
  Exercism: "#93c5fd",
};

export function platformColor(platform: string): string {
  if (PLATFORM_COLORS[platform]) return PLATFORM_COLORS[platform];
  let hash = 0;
  for (const ch of platform) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
  return `hsl(${hash % 360} 70% 70%)`;
}

export const STATUS_META: Record<ChallengeStatus, { label: string; cls: string; dot: string }> = {
  active: { label: "Live", cls: "border-emerald-400/35 bg-emerald-400/10 text-emerald-200", dot: "bg-emerald-400" },
  ending_soon: { label: "Closing ≤ 7d", cls: "border-amber-400/45 bg-amber-400/15 text-amber-200", dot: "bg-amber-400" },
  upcoming: { label: "Upcoming", cls: "border-sky-400/35 bg-sky-400/10 text-sky-200", dot: "bg-sky-400" },
  ongoing: { label: "Always-on", cls: "border-teal-400/30 bg-teal-400/10 text-teal-200", dot: "bg-teal-400" },
};

export const DIFFICULTY_CLS: Record<Difficulty, string> = {
  Beginner: "border-emerald-400/30 bg-emerald-400/10 text-emerald-200",
  Intermediate: "border-sky-400/30 bg-sky-400/10 text-sky-200",
  Advanced: "border-violet-400/30 bg-violet-400/10 text-violet-200",
  Expert: "border-rose-400/35 bg-rose-400/10 text-rose-200",
};

export function formatUSD(amount: number | null | undefined, compact = true): string {
  if (!amount || amount <= 0) return "—";
  if (!compact) return `$${Math.round(amount).toLocaleString("en-US")}`;
  if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(amount >= 10_000_000 ? 0 : 1).replace(/\.0$/, "")}M`;
  if (amount >= 1_000) return `$${(amount / 1_000).toFixed(amount >= 10_000 ? 0 : 1).replace(/\.0$/, "")}K`;
  return `$${Math.round(amount)}`;
}

/** Milliseconds until a challenge's relevant boundary (start for upcoming, end otherwise). */
export function msUntil(c: Challenge, now: number): number | null {
  const target = c.status === "upcoming" && c.start_date ? c.start_date : c.end_date;
  if (!target) return null;
  const t = Date.parse(target);
  return Number.isNaN(t) ? null : t - now;
}

export function countdown(c: Challenge, now: number): string {
  const ms = msUntil(c, now);
  if (ms === null) return c.challenge_type === "oss_bounty" ? "Open Bounty" : "Always-on";
  const prefix = c.status === "upcoming" ? "Starts in " : "";
  if (ms <= 0) return c.status === "upcoming" ? "Starting now" : "Closed";
  const mins = Math.floor(ms / 60000);
  const d = Math.floor(mins / 1440);
  const h = Math.floor((mins % 1440) / 60);
  const m = mins % 60;
  if (d >= 60) return `${prefix}${Math.floor(d / 30)}mo ${d % 30}d`;
  if (d >= 1) return `${prefix}${d}d ${h}h`;
  if (h >= 1) return `${prefix}${h}h ${m}m`;
  return `${prefix}${m}m`;
}

export function shortDate(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" });
}

export function relativeTime(iso: string | undefined, now: number): string {
  if (!iso) return "unknown";
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return iso;
  const s = Math.max(0, Math.round((now - t) / 1000));
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

export function matchesFilters(c: Challenge, f: Filters, bookmarks: Set<string>, now: number): boolean {
  if (!VIEW_TYPES[f.view].includes(c.challenge_type)) return false;

  switch (f.preset) {
    case "ending_soon": {
      const ms = msUntil(c, now);
      if (c.status === "upcoming" || ms === null || ms > 7 * 86400_000) return false;
      break;
    }
    case "high_prize":
      if ((c.prize_usd || 0) < 10_000) return false;
      break;
    case "online_only":
      if (c.mode.toLowerCase() !== "online") return false;
      break;
    case "new":
      if (!c.is_new) return false;
      break;
    case "beginner":
      if (c.difficulty !== "Beginner") return false;
      break;
    case "saved":
      if (!bookmarks.has(c.id)) return false;
      break;
  }

  if (f.platforms.length && !f.platforms.includes(c.platform)) return false;
  if (f.categories.length && !f.categories.includes(c.category)) return false;
  if (f.ecosystems.length && !f.ecosystems.includes(c.ecosystem)) return false;
  if (f.languages.length && !c.languages.some((l) => f.languages.includes(l))) return false;
  if (f.statuses.length && !f.statuses.includes(c.status)) return false;
  if (f.difficulties.length && !f.difficulties.includes(c.difficulty)) return false;
  if (f.minPrizeUsd > 0 && (c.prize_usd || 0) < f.minPrizeUsd) return false;

  const q = f.search.trim().toLowerCase();
  if (q) {
    const hay = [c.title, c.platform, c.organizer, c.category, c.ecosystem, c.mode, c.description, ...c.languages, ...c.tags]
      .join(" ")
      .toLowerCase();
    if (!q.split(/\s+/).every((tok) => hay.includes(tok))) return false;
  }
  return true;
}

export function optionCounts(rows: Challenge[], pick: (c: Challenge) => string | string[]) {
  const map = new Map<string, number>();
  for (const r of rows) {
    const v = pick(r);
    for (const key of Array.isArray(v) ? v : [v]) {
      if (key) map.set(key, (map.get(key) ?? 0) + 1);
    }
  }
  return [...map.entries()]
    .map(([value, count]) => ({ value, count }))
    .sort((a, b) => b.count - a.count || a.value.localeCompare(b.value));
}

/** Build a minimal RFC 5545 calendar file for a challenge deadline. */
export function downloadIcs(c: Challenge) {
  const fmt = (iso: string) => new Date(iso).toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
  const end = c.end_date ?? c.start_date;
  if (!end) return;
  const start = c.start_date && c.start_date < end ? c.start_date : end;
  const esc = (s: string) => s.replace(/[\\,;]/g, (m) => `\\${m}`).replace(/\n/g, "\\n");
  const ics = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//WUNDERDEV//Developer Competitions//EN",
    "BEGIN:VEVENT",
    `UID:${c.id}@wunderdev`,
    `DTSTAMP:${fmt(new Date().toISOString())}`,
    `DTSTART:${fmt(start)}`,
    `DTEND:${fmt(end)}`,
    `SUMMARY:${esc(`${TYPE_META[c.challenge_type].label}: ${c.title} (${c.platform})`)}`,
    `DESCRIPTION:${esc(`${c.prize} · ${c.url}`)}`,
    `URL:${c.url}`,
    "BEGIN:VALARM",
    "TRIGGER:-P1D",
    "ACTION:DISPLAY",
    `DESCRIPTION:${esc(`${c.title} closes in 24h`)}`,
    "END:VALARM",
    "END:VEVENT",
    "END:VCALENDAR",
  ].join("\r\n");
  const blob = new Blob([ics], { type: "text/calendar;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${c.title.replace(/[^a-z0-9]+/gi, "-").toLowerCase()}.ics`;
  a.click();
  URL.revokeObjectURL(a.href);
}

export function exportCsv(rows: Challenge[]) {
  const headers = ["Title", "Type", "Platform", "Organizer", "Prize", "Prize USD", "Status", "Mode", "Start", "End", "Category", "Ecosystem", "Languages", "Difficulty", "URL"];
  const esc = (v: unknown) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const lines = rows.map((c) =>
    [c.title, TYPE_META[c.challenge_type].label, c.platform, c.organizer, c.prize, c.prize_usd, c.status, c.mode, c.start_date, c.end_date, c.category, c.ecosystem, c.languages.join("; "), c.difficulty, c.url]
      .map(esc)
      .join(","),
  );
  const blob = new Blob([[headers.map(esc).join(","), ...lines].join("\n")], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "active-dev-competitions.csv";
  a.click();
  URL.revokeObjectURL(a.href);
}

