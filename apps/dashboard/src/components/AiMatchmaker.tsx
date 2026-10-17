import { useState } from "react";
import type { Challenge, ChallengeType } from "../types";
import { TYPE_META, countdown, formatUSD, platformColor } from "../lib/format";
import {
  ARCHETYPES,
  type Experience,
  type Goal,
  type Profile,
  type RecommendationResult,
  getWorkerUrl,
  loadProfile,
  recommend,
  saveProfile,
  setWorkerUrl,
} from "../lib/recommender";

interface Props {
  all: Challenge[];
  now: number;
}

const LANGS = ["TypeScript", "Python", "Rust", "Go", "Java", "C / C++", "C#", "Swift / Kotlin", "SQL"];
const TYPES: ChallengeType[] = ["hackathon", "dev_challenge", "oss_bounty", "coding_contest", "fellowship"];
const EXPERIENCES: { id: Experience; label: string }[] = [
  { id: "newcomer", label: "Newcomer" },
  { id: "intermediate", label: "Intermediate" },
  { id: "senior", label: "Senior engineer" },
];
const GOALS: { id: Goal; label: string }[] = [
  { id: "ship", label: "⌁ Build & ship" },
  { id: "earn", label: "💰 Max payout" },
  { id: "reputation", label: "🏆 Leaderboard & PRs" },
  { id: "learn", label: "📚 Learn & mentorship" },
];

function Chip({ on, onClick, children }: { on: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      aria-pressed={on}
      onClick={onClick}
      className={`rounded-full border px-3 py-1 font-mono text-[11px] transition ${
        on ? "border-sky-300/60 bg-sky-300/15 text-sky-100" : "border-white/12 text-[#faf6e8]/65 hover:border-white/25 hover:text-[#faf6e8]"
      }`}
    >
      {children}
    </button>
  );
}

export function AiMatchmaker({ all, now }: Props) {
  const [profile, setProfile] = useState<Profile>(loadProfile);
  const [result, setResult] = useState<(RecommendationResult & { fallbackReason?: string }) | null>(null);
  const [loading, setLoading] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [workerUrl, setWorkerUrlState] = useState(getWorkerUrl);
  const [openPlan, setOpenPlan] = useState<string | null>(null);

  const byId = new Map(all.map((c) => [c.id, c]));
  const update = (patch: Partial<Profile>) => setProfile((p) => ({ ...p, ...patch }));
  const toggle = <T,>(list: T[], v: T) => (list.includes(v) ? list.filter((x) => x !== v) : [...list, v]);

  const run = async (p: Profile = profile) => {
    setLoading(true);
    saveProfile(p);
    try {
      setResult(await recommend(all, p, now));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="ai-matchmaker" className="wunder-glass scroll-mt-6 rounded-3xl border border-white/10 p-4 sm:p-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="font-mono text-xs uppercase tracking-widest text-sky-300/90">// DEVELOPER MATCHMAKER</div>
          <h2 className="mt-1 font-display text-3xl tracking-tight text-[#faf6e8] sm:text-4xl">
            Which live build, bounty or contest should <span className="italic text-sky-200">you</span> ship this week?
          </h2>
          <p className="mt-1 max-w-2xl font-mono text-xs text-[#faf6e8]/55">
            Select your stack and goals. Ranking runs instantly in your browser
            {workerUrl ? " and is refined by a Gemini 3.8 Flash worker" : ""}; your profile stays in localStorage.
          </p>
        </div>
        <button
          onClick={() => setShowConfig((s) => !s)}
          className="wunder-pill rounded-xl px-3 py-1.5 font-mono text-[11px] text-[#faf6e8]/70 transition hover:text-[#faf6e8]"
          aria-expanded={showConfig}
        >
          ⚙ {workerUrl ? "Gemini worker: on" : "Connect Gemini worker"}
        </button>
      </div>

      {showConfig && (
        <div className="mt-3 flex flex-col gap-2 rounded-xl border border-white/10 bg-black/30 p-3 sm:flex-row sm:items-center">
          <input
            value={workerUrl}
            onChange={(e) => setWorkerUrlState(e.target.value)}
            placeholder="https://wunderdev-recommender.<you>.workers.dev"
            aria-label="Gemini worker URL"
            className="flex-1 rounded-lg border border-white/12 bg-black/40 px-3 py-1.5 font-mono text-xs text-[#faf6e8] placeholder:text-[#faf6e8]/30 focus:border-sky-300/60 focus:outline-none"
          />
          <button
            onClick={() => {
              setWorkerUrl(workerUrl);
              setShowConfig(false);
            }}
            className="rounded-lg bg-[#faf6e8] px-3 py-1.5 font-mono text-[11px] font-semibold text-[#0b1018]"
          >
            Save
          </button>
          <span className="font-mono text-[10px] text-[#faf6e8]/40">Deploy from workers/recommender — leave blank for local-only.</span>
        </div>
      )}

      {/* Archetypes */}
      <div className="mt-4 flex flex-wrap gap-2">
        {ARCHETYPES.map((a) => (
          <button
            key={a.id}
            onClick={() => {
              setProfile(a.profile);
              run(a.profile);
            }}
            className="wunder-pill rounded-xl px-3 py-1.5 font-mono text-[11px] text-[#faf6e8]/80 transition hover:border-sky-300/40 hover:text-sky-100"
          >
            {a.label}
          </button>
        ))}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-[1.1fr_1fr]">
        <div className="space-y-3">
          <textarea
            value={profile.prompt}
            onChange={(e) => update({ prompt: e.target.value })}
            rows={3}
            placeholder="e.g. I build Next.js + Python/Rust backends and want an online AI agent hackathon or $500+ GitHub open-source bounty closing in the next 3 weeks."
            aria-label="Describe what you're looking for"
            className="w-full resize-none rounded-xl border border-white/12 bg-black/35 p-3 text-sm text-[#faf6e8] placeholder:text-[#faf6e8]/30 focus:border-sky-300/60 focus:outline-none"
          />
          <div>
            <div className="mb-1.5 font-mono text-[10px] uppercase tracking-widest text-[#faf6e8]/40">Languages & Stack</div>
            <div className="flex flex-wrap gap-1.5">
              {LANGS.map((l) => (
                <Chip key={l} on={profile.languages.includes(l)} onClick={() => update({ languages: toggle(profile.languages, l) })}>
                  {l}
                </Chip>
              ))}
            </div>
          </div>
          <div>
            <div className="mb-1.5 font-mono text-[10px] uppercase tracking-widest text-[#faf6e8]/40">Project / Challenge types</div>
            <div className="flex flex-wrap gap-1.5">
              {TYPES.map((t) => (
                <Chip key={t} on={profile.types.includes(t)} onClick={() => update({ types: toggle(profile.types, t) })}>
                  {TYPE_META[t].icon} {TYPE_META[t].label}
                </Chip>
              ))}
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <div className="mb-1.5 font-mono text-[10px] uppercase tracking-widest text-[#faf6e8]/40">Experience</div>
              <div className="flex flex-wrap gap-1.5">
                {EXPERIENCES.map((x) => (
                  <Chip key={x.id} on={profile.experience === x.id} onClick={() => update({ experience: x.id })}>
                    {x.label}
                  </Chip>
                ))}
              </div>
            </div>
            <div>
              <div className="mb-1.5 font-mono text-[10px] uppercase tracking-widest text-[#faf6e8]/40">Primary Goal</div>
              <div className="flex flex-wrap gap-1.5">
                {GOALS.map((g) => (
                  <Chip key={g.id} on={profile.goal === g.id} onClick={() => update({ goal: g.id })}>
                    {g.label}
                  </Chip>
                ))}
              </div>
            </div>
          </div>
          <label className="block">
            <span className="mb-1.5 flex justify-between font-mono text-[10px] uppercase tracking-widest text-[#faf6e8]/40">
              Weekly build budget <span className="text-sky-200">{profile.hoursPerWeek}h / week</span>
            </span>
            <input
              type="range"
              min={2}
              max={40}
              step={1}
              value={profile.hoursPerWeek}
              onChange={(e) => update({ hoursPerWeek: Number(e.target.value) })}
              className="w-full accent-sky-300"
            />
          </label>
          <button
            onClick={() => run()}
            disabled={loading}
            className="wunder-cta-glow w-full rounded-full bg-[#faf6e8] px-6 py-3 font-mono text-sm font-semibold text-[#0b1018] transition hover:bg-white disabled:opacity-60"
          >
            {loading ? "Ranking live dev opportunities…" : "✦ Find my best matches →"}
          </button>
        </div>

        <div className="space-y-3" aria-live="polite">
          {!result && (
            <div className="flex h-full min-h-[240px] items-center justify-center rounded-2xl border border-dashed border-white/12 p-6 text-center font-mono text-xs text-[#faf6e8]/45">
              Pick a developer archetype above or describe your stack, then click “Find my best matches”.
            </div>
          )}
          {result && (
            <>
              <div className="rounded-xl border border-white/10 bg-black/25 p-3">
                <div className="font-mono text-[10px] uppercase tracking-widest text-[#faf6e8]/40">
                  {result.source === "gemini-worker" ? `✦ ${result.model ?? "Gemini"} synthesis` : "⚙ Local neural ranker"}
                  {result.fallbackReason && <span className="ml-2 text-amber-300/80">(worker unavailable: {result.fallbackReason})</span>}
                </div>
                <p className="mt-1 text-sm text-[#faf6e8]/80">{result.summary}</p>
              </div>
              {result.recommendations.map((r) => {
                const c = byId.get(r.id);
                if (!c) return null;
                const col = platformColor(c.platform);
                const open = openPlan === r.id;
                return (
                  <article key={r.id} className="rounded-2xl border border-white/10 bg-black/25 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-1.5 font-mono text-[10px]">
                          <span className="rounded px-1.5 py-0.5" style={{ backgroundColor: `${col}22`, color: col }}>
                            {c.platform}
                          </span>
                          <span className="text-[#faf6e8]/45">{r.headline}</span>
                        </div>
                        <a href={c.url} target="_blank" rel="noopener noreferrer" className="mt-1 block truncate font-medium text-[#faf6e8] hover:text-sky-200">
                          {c.title}
                        </a>
                        <div className="mt-0.5 font-mono text-[11px] text-[#faf6e8]/50">
                          {c.prize_usd > 0 ? formatUSD(c.prize_usd) : c.prize} · {c.mode} · ⏳ {countdown(c, now)}
                        </div>
                      </div>
                      <div className="shrink-0 text-right">
                        <div className="font-display text-3xl text-sky-200">{r.match_score}%</div>
                        <div className="font-mono text-[9px] uppercase tracking-widest text-[#faf6e8]/40">match</div>
                      </div>
                    </div>
                    <ul className="mt-2 space-y-1 text-xs text-[#faf6e8]/75">
                      {r.fit_reasons.map((reason) => (
                        <li key={reason} className="flex gap-2">
                          <span className="text-emerald-300">✓</span>
                          {reason}
                        </li>
                      ))}
                      <li className="flex gap-2 text-amber-200/80">
                        <span>⚠</span>
                        {r.watch_outs}
                      </li>
                    </ul>
                    <button
                      onClick={() => setOpenPlan(open ? null : r.id)}
                      aria-expanded={open}
                      className="mt-2 font-mono text-[11px] text-[#faf6e8]/55 hover:text-[#faf6e8]"
                    >
                      {open ? "▾ Hide" : "▸ Show"} 4-phase execution plan
                    </button>
                    {open && (
                      <ol className="mt-2 space-y-1.5 border-l border-sky-300/30 pl-3">
                        {r.weekly_plan.map((step) => (
                          <li key={step.week + step.focus} className="text-xs">
                            <div className="font-mono text-[10px] text-sky-200/80">{step.week}</div>
                            <div className="text-[#faf6e8]/85">{step.focus}</div>
                            <div className="text-[#faf6e8]/50">→ {step.deliverable}</div>
                          </li>
                        ))}
                      </ol>
                    )}
                  </article>
                );
              })}
            </>
          )}
        </div>
      </div>
    </section>
  );
}

