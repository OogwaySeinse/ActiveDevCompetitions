import { useEffect, useRef } from "react";

interface Cluster {
  x: number;
  y: number;
  vx: number;
  vy: number;
  lines: string[];
  tint: string;
  alpha: number;
  phase: number;
}

const DEV_ASCII_CLUSTERS: { lines: string[]; tint: string }[] = [
  {
    lines: [
      "┌─ PR #1428 · MERGED ──────────┐",
      "│ feat(raft): leader election  │",
      "│ +412 −38 · CI 14/14 passed ✓ │",
      "└──────────────────────────────┘",
    ],
    tint: "rgba(56, 189, 248, 0.72)",
  },
  {
    lines: [
      "async fn poll_next(self: Pin<&mut Self>, cx: &mut Context<'_>)",
      "  -> Poll<Option<Result<Frame, TransportError>>> {",
      "  tokio::select! { biased; _ = shutdown.recv() => Poll::Ready(None) }",
    ],
    tint: "rgba(250, 246, 232, 0.60)",
  },
  {
    lines: [
      "kubectl rollout status deploy/edge-gateway -n prod",
      "p99_latency_ms = 4.2ms  │  error_rate = 0.001%",
      "otel.trace_id = 0x7f9a…e31b  [SPAN_STATUS_OK]",
    ],
    tint: "rgba(52, 211, 153, 0.62)",
  },
  {
    lines: [
      "docker buildx build --platform linux/amd64,linux/arm64",
      "  --cache-from type=gha --push ghcr.io/wunderdev/agent:v2",
      "sha256:9c8b4e10f2a7…  size: 18.4 MB",
    ],
    tint: "rgba(167, 139, 250, 0.60)",
  },
  {
    lines: [
      "const agent = new MCPServer({ tools: [gitDiff, runTests] });",
      "await streamText({ model: gemini('gemini-3.8-flash'),",
      "  stopWhen: stepCountIs(8) }); // ✦ tool_call → pass",
    ],
    tint: "rgba(56, 189, 248, 0.64)",
  },
  {
    lines: [
      "EXPLAIN (ANALYZE, BUFFERS) SELECT repo, SUM(bounty_usd)",
      "FROM active_dev_bounties WHERE status = 'OPEN'",
      "GROUP BY 1 ORDER BY 2 DESC LIMIT 25; -- 0.84ms",
    ],
    tint: "rgba(251, 191, 36, 0.58)",
  },
  {
    lines: [
      "⟦ DEVPOST · TOPCODER · GITHUB BOUNTIES · DEVFOLIO ⟧",
      "  ⟦ MLH · HACKEREARTH · CODEFORCES · BUGCROWD ⟧",
      "  refresh_cron : 0 6 * * * UTC",
    ],
    tint: "rgba(250, 246, 232, 0.54)",
  },
  {
    lines: [
      "dp[mask][u] = min(dp[mask ^ (1<<u)][v] + w(v, u))",
      "O(n² · 2ⁿ) → AC (42ms / 256MB)  [Div.1 Grandmaster]",
      "git push origin main --tags",
    ],
    tint: "rgba(244, 114, 182, 0.56)",
  },
];

export function AsciiBackdrop() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    let animId = 0;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);
    const onResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", onResize);
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const clusters: Cluster[] = DEV_ASCII_CLUSTERS.map((c, i) => ({
      x: (((i % 3) + 0.5) / 3) * width + (Math.random() - 0.5) * 140,
      y: ((Math.floor(i / 3) + 0.45) / 3) * height + (Math.random() - 0.5) * 90,
      vx: (Math.random() - 0.5) * 0.18,
      vy: (Math.random() - 0.5) * 0.14,
      lines: c.lines,
      tint: c.tint,
      alpha: 0.2 + (i % 3) * 0.06,
      phase: i * 1.15,
    }));

    let tick = 0;
    const render = () => {
      tick += 0.012;
      ctx.clearRect(0, 0, width, height);
      ctx.font = '11px "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace';
      ctx.textBaseline = "top";

      for (const cl of clusters) {
        if (!reducedMotion) {
          cl.x += cl.vx;
          cl.y += cl.vy;
          if (cl.x < -280) cl.x = width + 60;
          if (cl.x > width + 120) cl.x = -260;
          if (cl.y < -80) cl.y = height + 40;
          if (cl.y > height + 80) cl.y = -60;
        }
        const alpha = cl.alpha * (0.78 + 0.22 * Math.sin(tick + cl.phase));
        const grad = ctx.createRadialGradient(cl.x + 90, cl.y + 20, 4, cl.x + 90, cl.y + 20, 155);
        grad.addColorStop(0, `rgba(14, 58, 92, ${alpha * 0.9})`);
        grad.addColorStop(0.55, `rgba(18, 28, 48, ${alpha * 0.45})`);
        grad.addColorStop(1, "rgba(9, 13, 20, 0)");
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(cl.x + 90, cl.y + 20, 155, 0, Math.PI * 2);
        ctx.fill();

        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.fillStyle = cl.tint;
        cl.lines.forEach((line, idx) => ctx.fillText(line, cl.x, cl.y + idx * 15));
        ctx.restore();
      }
      if (!reducedMotion) animId = window.requestAnimationFrame(render);
    };
    render();

    return () => {
      window.removeEventListener("resize", onResize);
      if (animId) window.cancelAnimationFrame(animId);
    };
  }, []);

  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden select-none" aria-hidden="true">
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(circle at 16% 14%, rgba(16, 88, 128, 0.34) 0%, transparent 46%), radial-gradient(circle at 84% 22%, rgba(76, 52, 148, 0.28) 0%, transparent 48%), radial-gradient(circle at 50% 82%, rgba(16, 98, 76, 0.26) 0%, transparent 55%), linear-gradient(180deg, #090d14 0%, #0c121c 48%, #070a10 100%)",
        }}
      />
      <div
        className="absolute inset-0 opacity-[0.06]"
        style={{
          backgroundImage:
            "linear-gradient(to right, rgba(250,246,232,0.18) 1px, transparent 1px), linear-gradient(to bottom, rgba(250,246,232,0.18) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
      />
      <canvas ref={canvasRef} className="absolute inset-0 h-full w-full opacity-90" />
    </div>
  );
}

