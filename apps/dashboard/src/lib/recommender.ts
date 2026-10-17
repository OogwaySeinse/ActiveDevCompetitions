import type { Challenge, ChallengeType } from "../types";
import { TYPE_META, formatUSD, msUntil } from "./format";

export type Experience = "newcomer" | "intermediate" | "senior";
export type Goal = "earn" | "ship" | "reputation" | "learn";

export interface Profile {
  prompt: string;
  experience: Experience;
  languages: string[];
  goal: Goal;
  types: ChallengeType[];
  hoursPerWeek: number;
}

export interface PlanStep {
  week: string;
  focus: string;
  deliverable: string;
}

export interface Recommendation {
  id: string;
  match_score: number;
  headline: string;
  fit_reasons: string[];
  watch_outs: string;
  weekly_plan: PlanStep[];
}

export interface RecommendationResult {
  summary: string;
  recommendations: Recommendation[];
  source: "local-ranker" | "gemini-worker";
  model?: string;
}

export const DEFAULT_PROFILE: Profile = {
  prompt: "",
  experience: "intermediate",
  languages: ["TypeScript", "Python"],
  goal: "ship",
  types: ["hackathon", "dev_challenge", "oss_bounty"],
  hoursPerWeek: 12,
};

export const ARCHETYPES: { id: string; label: string; profile: Profile }[] = [
  {
    id: "ai-fullstack-builder",
    label: "⌁ AI Agent & Full-Stack Builder",
    profile: {
      prompt: "Full-stack TypeScript & Python engineer looking to build and ship an AI agent, MCP tool, or SaaS product at a high-prize online hackathon.",
      experience: "intermediate",
      languages: ["TypeScript", "Python"],
      goal: "ship",
      types: ["hackathon", "dev_challenge"],
      hoursPerWeek: 14,
    },
  },
  {
    id: "oss-bounty-hunter",
    label: "⌥ Open-Source Bounty Hunter",
    profile: {
      prompt: "Experienced contributor hunting paid open-source GitHub / Algora issue bounties and Topcoder challenges in TypeScript, Rust, or Go.",
      experience: "senior",
      languages: ["TypeScript", "Rust", "Go"],
      goal: "earn",
      types: ["oss_bounty", "dev_challenge"],
      hoursPerWeek: 15,
    },
  },
  {
    id: "systems-cloud-infra",
    label: "🦀 Systems, Cloud & Infra Engineer",
    profile: {
      prompt: "Systems and cloud-native developer interested in Rust, Go, Kubernetes, distributed systems, DevTools, and application security bounties.",
      experience: "senior",
      languages: ["Rust", "Go", "C / C++"],
      goal: "reputation",
      types: ["dev_challenge", "oss_bounty", "fellowship"],
      hoursPerWeek: 12,
    },
  },
  {
    id: "first-hackathon-fellowship",
    label: "🌱 First Hackathon & OSS Fellowship",
    profile: {
      prompt: "CS student or newer developer looking for beginner-friendly online hackathons, paid open-source fellowships (GSoC, LFX, Outreachy), and starter issues.",
      experience: "newcomer",
      languages: ["Python", "TypeScript"],
      goal: "learn",
      types: ["hackathon", "fellowship", "oss_bounty"],
      hoursPerWeek: 8,
    },
  },
  {
    id: "algo-sprinter",
    label: "⚡ Competitive Programmer",
    profile: {
      prompt: "Algorithmic problem solver who enjoys timed Codeforces/LeetCode rounds, graph & DP optimization challenges, and fast weekend sprints.",
      experience: "intermediate",
      languages: ["C / C++", "Python", "Rust"],
      goal: "reputation",
      types: ["coding_contest", "dev_challenge"],
      hoursPerWeek: 8,
    },
  },
];

const DIFFICULTY_FIT: Record<Experience, Record<string, number>> = {
  newcomer: { Beginner: 22, Intermediate: 8, Advanced: -12, Expert: -26 },
  intermediate: { Beginner: 4, Intermediate: 18, Advanced: 10, Expert: -6 },
  senior: { Beginner: -10, Intermediate: 6, Advanced: 16, Expert: 20 },
};

const STOPWORDS = new Set(
  "a an and are as at be but by for from has have i in into is it its looking me my of on or so that the this to want where which with would like".split(" "),
);

function tokens(text: string): string[] {
  return [...new Set(text.toLowerCase().split(/[^a-z0-9+#.-]+/).filter((t) => t.length > 2 && !STOPWORDS.has(t)))];
}

function hoursAvailable(c: Challenge, now: number, hoursPerWeek: number): number | null {
  const ms = msUntil(c, now);
  if (ms === null || c.status === "upcoming") return null;
  return (Math.max(0, ms) / (7 * 86400_000)) * hoursPerWeek;
}

function score(c: Challenge, p: Profile, now: number) {
  let s = 40;
  const reasons: string[] = [];
  const watch: string[] = [];

  const langOverlap = c.languages.filter((l) => p.languages.includes(l));
  if (langOverlap.length) {
    s += 26;
    reasons.push(`Tech stack in ${langOverlap.join(" / ")} aligns directly with your languages.`);
  } else if (c.languages.length && p.languages.length) {
    s -= 12;
    watch.push(`Targets ${c.languages.join("/")}, outside your selected stack.`);
  }

  if (p.types.includes(c.challenge_type)) s += 18;

  const diff = DIFFICULTY_FIT[p.experience][c.difficulty] ?? 0;
  s += diff;
  if (diff >= 15) reasons.push(`${c.difficulty} tier matches your ${p.experience} engineering profile.`);
  if (diff <= -12) watch.push(`${c.difficulty}-level complexity may be steep for a ${p.experience}.`);

  const prize = c.prize_usd || 0;
  if (p.goal === "earn") {
    const bump = prize > 0 ? Math.min(26, Math.log10(prize) * 4.5) : -8;
    s += bump;
    if (prize >= 1_000) reasons.push(`Cash pool / bounty of ${formatUSD(prize)} directly rewards shipping a winning solution.`);
  } else if (p.goal === "ship") {
    if (c.challenge_type === "hackathon" || c.challenge_type === "dev_challenge") {
      s += 22;
      reasons.push("Project-focused format: ship a working prototype, demo video, and repo for sponsor tracks.");
    }
  } else if (p.goal === "reputation") {
    if (c.challenge_type === "coding_contest" || c.challenge_type === "dev_challenge" || c.challenge_type === "oss_bounty") {
      s += 18;
      reasons.push("Public PRs / rated leaderboard placement builds verifiable engineering proof-of-work.");
    }
  } else if (p.goal === "learn") {
    if (c.challenge_type === "fellowship" || c.difficulty === "Beginner") {
      s += 20;
      reasons.push("Structured mentorship / beginner-friendly scope ideal for leveling up your engineering skills.");
    }
  }

  const hrs = hoursAvailable(c, now, p.hoursPerWeek);
  if (hrs !== null) {
    if (hrs < 5 && c.challenge_type !== "coding_contest") {
      s -= 15;
      watch.push(`Only ~${Math.max(1, Math.round(hrs))}h of your weekly budget left before submission cutoff.`);
    } else if (hrs >= 10) {
      s += 6;
      reasons.push(`~${Math.round(hrs)}h of build time available at ${p.hoursPerWeek}h/week before deadline.`);
    }
  }
  if (c.status === "upcoming") {
    s += 5;
    reasons.push("Starts soon — gives you time to form a team, scaffold your repo, and review sponsor APIs.");
  }
  if (c.status === "ongoing" && c.challenge_type === "oss_bounty") {
    reasons.push("Open bounty: claim the issue and submit a clean PR with tests at your own pace.");
  }

  const promptTokens = tokens(p.prompt);
  if (promptTokens.length) {
    const hay = [c.title, c.description, c.category, c.ecosystem, c.organizer, ...c.tags, ...c.languages].join(" ").toLowerCase();
    const hits = promptTokens.filter((t) => hay.includes(t));
    if (hits.length) {
      s += Math.min(24, hits.length * 6);
      reasons.push(`Matches your brief on: ${hits.slice(0, 4).join(", ")}.`);
    }
  }

  if (c.mode !== "Online") watch.push(`${c.mode} attendance required — verify travel/venue logistics.`);
  if (c.is_new) s += 3;

  if (!reasons.length) reasons.push(`${TYPE_META[c.challenge_type].label} on ${c.platform} in ${c.category}.`);
  return { s, reasons: reasons.slice(0, 3), watch };
}

function phaseHours(p: Profile, c: Challenge, now: number, phases: number): string[] {
  const hrs = hoursAvailable(c, now, p.hoursPerWeek);
  const total = hrs === null ? p.hoursPerWeek * phases : Math.max(phases, Math.round(hrs));
  const per = Math.max(1, Math.round(total / phases));
  const ms = msUntil(c, now);
  const days = ms && c.status !== "upcoming" ? Math.max(1, Math.floor(ms / 86400_000)) : null;
  return Array.from({ length: phases }, (_, i) => {
    if (days !== null && days < 21) {
      const a = Math.floor((i * days) / phases) + 1;
      const b = Math.max(a, Math.floor(((i + 1) * days) / phases));
      return `Day ${a}${b > a ? `–${b}` : ""} (~${per}h)`;
    }
    return `Phase ${i + 1} (~${Math.min(per, p.hoursPerWeek)}h)`;
  });
}

const PLAN_TEMPLATES: Record<ChallengeType, { focus: string; deliverable: string }[]> = {
  hackathon: [
    { focus: "Scope & Architecture: review sponsor tracks, judging criteria, and API docs", deliverable: "1-page technical spec + repo scaffold with CI & deployment pipeline" },
    { focus: "Core Vertical Slice: implement the primary end-to-end user flow & backend integration", deliverable: "Working core pipeline deployed on a live preview URL" },
    { focus: "Polish, Telemetry & Edge Cases: UI/UX refinement, latency tuning, and fallback handling", deliverable: "Production-ready demo app + architecture diagram in README" },
    { focus: "Demo Video & Submission Package: record crisp 2–3 min walkthrough and submit early", deliverable: "Submitted Devpost/Devfolio project + public GitHub repo & video" },
  ],
  dev_challenge: [
    { focus: "Specification & Test Harness: dissect requirements, acceptance criteria, and scoring rubric", deliverable: "Local environment running with baseline unit/integration tests" },
    { focus: "Implementation: build required endpoints, modules, or UI components to spec", deliverable: "Feature-complete implementation passing all functional checks" },
    { focus: "Edge-Case Hardening & Docs: lint, benchmark, Dockerize, and write verification guide", deliverable: "Clean container/package + step-by-step reviewer deployment guide" },
    { focus: "Final Packaging & Submission: verify archive structure and submit before cutoff", deliverable: "Verified submission bundle uploaded to challenge portal" },
  ],
  oss_bounty: [
    { focus: "Reproduction & Codebase Recon: clone repo, run test suite, and trace the target issue", deliverable: "Minimal reproduction test case + alignment comment on the issue" },
    { focus: "Patch Architecture: implement a minimal, idiomatic fix adhering to maintainer conventions", deliverable: "Focused commit solving root cause without regressions" },
    { focus: "Test Coverage & Benchmarks: add unit/integration tests covering edge cases", deliverable: "Green CI run + before/after verification output" },
    { focus: "Pull Request & Review Turnaround: open PR linking the bounty issue and address feedback", deliverable: "Merged PR + Algora/bounty payout claim" },
  ],
  coding_contest: [
    { focus: "Template & Environment Prep: fast I/O templates, stress-test scripts, and recent problem set warm-up", deliverable: "Ready local IDE + pre-tested data structure snippets" },
    { focus: "Fast Triage & Early Solves: clear A–C problems quickly with zero penalty", deliverable: "Fast initial points banked on the live scoreboard" },
    { focus: "Deep Algorithmic Push: tackle mid/hard graph, DP, or constructive problems", deliverable: "Verified asymptotic complexity + edge-case stress tests" },
    { focus: "Upsolving & Editorial Review: solve remaining problems post-contest", deliverable: "Upsolved solutions committed to personal notebook" },
  ],
  fellowship: [
    { focus: "Organization & Project Selection: filter mentoring orgs by your primary language stack", deliverable: "Shortlist of 2–3 target organizations and active project ideas" },
    { focus: "First Starter PRs: introduce yourself in community channels and fix 1–2 good-first-issues", deliverable: "Merged starter PRs demonstrating codebase familiarity" },
    { focus: "RFC / Proposal Drafting: write a concrete weekly milestone plan with mentor feedback", deliverable: "Draft proposal reviewed by project maintainers" },
    { focus: "Final Application & Practice: submit polished application or complete arena milestones", deliverable: "Submitted fellowship proposal / completed systems benchmark" },
  ],
};

function buildPlan(c: Challenge, p: Profile, now: number): PlanStep[] {
  const tpl = PLAN_TEMPLATES[c.challenge_type];
  const labels = phaseHours(p, c, now, tpl.length);
  return tpl.map((t, i) => ({ week: labels[i], ...t }));
}

export function candidatePool(all: Challenge[], p: Profile): Challenge[] {
  const allowFellowship = p.experience === "newcomer" || p.goal === "learn" || p.types.includes("fellowship");
  return all.filter((c) => allowFellowship || c.challenge_type !== "fellowship");
}

export function rankLocally(all: Challenge[], p: Profile, now: number, topN = 4): RecommendationResult {
  const scored = candidatePool(all, p)
    .map((c) => ({ c, ...score(c, p, now) }))
    .sort((a, b) => b.s - a.s);

  const picks: typeof scored = [];
  const seen = new Map<string, number>();
  for (const item of scored) {
    const key = `${item.c.platform}|${item.c.challenge_type}`;
    if ((seen.get(key) ?? 0) >= 2) continue;
    seen.set(key, (seen.get(key) ?? 0) + 1);
    picks.push(item);
    if (picks.length >= topN) break;
  }

  const top = picks[0]?.s ?? 1;
  const recommendations = picks.map(({ c, s, reasons, watch }) => ({
    id: c.id,
    match_score: Math.max(58, Math.min(98, Math.round(70 + ((s - top * 0.5) / (top || 1)) * 28))),
    headline: `${TYPE_META[c.challenge_type].label} · ${c.category}`,
    fit_reasons: reasons,
    watch_outs: watch[0] ?? "Review submission rules, repo license requirements, and judging criteria early.",
    weekly_plan: buildPlan(c, p, now),
  }));

  const types = [...new Set(picks.map((x) => TYPE_META[x.c.challenge_type].label.toLowerCase()))].join(", ");
  return {
    summary: picks.length
      ? `Ranked ${scored.length} live developer opportunities against your ${p.languages.join("/") || "polyglot"} stack, ${p.experience} level, and ${p.hoursPerWeek}h/week build budget. Top matches span ${types}.`
      : "No candidates matched — try broadening your challenge types or programming languages.",
    recommendations,
    source: "local-ranker",
  };
}

const WORKER_KEY = "wunderdev_worker_url";
const PROFILE_KEY = "wunderdev_profile_v1";

export function getWorkerUrl(): string {
  return (localStorage.getItem(WORKER_KEY) || (import.meta.env.VITE_RECOMMENDER_URL as string | undefined) || "").trim();
}

export function setWorkerUrl(url: string) {
  if (url.trim()) localStorage.setItem(WORKER_KEY, url.trim());
  else localStorage.removeItem(WORKER_KEY);
}

export function loadProfile(): Profile {
  try {
    const raw = localStorage.getItem(PROFILE_KEY);
    return raw ? { ...DEFAULT_PROFILE, ...(JSON.parse(raw) as Partial<Profile>) } : DEFAULT_PROFILE;
  } catch {
    return DEFAULT_PROFILE;
  }
}

export function saveProfile(p: Profile) {
  try {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(p));
  } catch {
    /* ignore */
  }
}

/** Ask the optional Gemini Cloudflare Worker; falls back to the local ranker on any failure. */
export async function recommend(all: Challenge[], p: Profile, now: number): Promise<RecommendationResult & { fallbackReason?: string }> {
  const local = rankLocally(all, p, now);
  const url = getWorkerUrl();
  if (!url) return local;

  const shortlist = candidatePool(all, p)
    .map((c) => ({ c, s: score(c, p, now).s }))
    .sort((a, b) => b.s - a.s)
    .slice(0, 30)
    .map(({ c }) => ({
      id: c.id,
      name: c.title,
      platform: c.platform,
      type: c.challenge_type,
      category: c.category,
      ecosystem: c.ecosystem,
      languages: c.languages,
      difficulty: c.difficulty,
      mode: c.mode,
      prize_usd: c.prize_usd,
      prize_label: c.prize,
      status: c.status,
      end_date: c.end_date,
      days_left: (() => {
        const ms = msUntil(c, now);
        return ms === null ? null : Math.round(ms / 86400_000);
      })(),
      tags: c.tags.slice(0, 8),
      description: c.description.slice(0, 260),
    }));

  try {
    const res = await fetch(`${url.replace(/\/$/, "")}/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile: p, candidates: shortlist }),
    });
    const data = (await res.json()) as RecommendationResult & { error?: string };
    if (!res.ok || !Array.isArray(data.recommendations)) throw new Error(data.error || `HTTP ${res.status}`);
    const ids = new Set(all.map((c) => c.id));
    const recs = data.recommendations.filter((r) => ids.has(r.id));
    if (!recs.length) throw new Error("Worker returned no valid ids");
    return { ...data, recommendations: recs, source: "gemini-worker" };
  } catch (err) {
    return { ...local, fallbackReason: err instanceof Error ? err.message : String(err) };
  }
}

