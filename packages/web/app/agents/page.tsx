"use client";

import Link from "next/link";
import { useState } from "react";

import { ErrorState, LoadingSkeleton } from "@/components/common/states";
import { StatTile } from "@/components/common/StatTile";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { Eyebrow, PageHeader } from "@/components/ui/primitives";
import { money } from "@/lib/format";
import {
  useActivatePrompt,
  useAgentCosts,
  useAgents,
  useAgentScores,
  useHealth,
  useIntel,
  usePendingPrompts,
  useRunAgent,
  useUpdateAgent,
} from "@/lib/queries";
import type { Agent, AgentCosts, AgentScore, PendingPrompt } from "@/lib/types";

// Status → dot color + label (last_status: success/running/error/skipped_budget/null)
const STATUS_META: Record<string, { color: string; label: string; pulse?: boolean }> = {
  success: { color: "#3ddc97", label: "OK" },
  running: { color: "#4f8cff", label: "RUNNING", pulse: true },
  error: { color: "#ff6b6b", label: "ERROR" },
  skipped_budget: { color: "#ffcd80", label: "PAUSED" },
};
const IDLE: { color: string; label: string; pulse?: boolean } = {
  color: "rgba(238,241,246,0.4)",
  label: "IDLE",
};

// Static role descriptions (the API doesn't expose a per-agent role blurb).
const ROLE: Record<string, string> = {
  auditor: "Scores every agent weekly and proposes prompt fixes.",
  marketing: "Plans promos and cross-listing pushes to move stock.",
  "research-bot": "Tracks demand trends for GPUs, RAM, and enterprise gear.",
  "e-customer": "Drafts buyer message replies for review before sending.",
  "e-inventory": "Flags slow-moving stock and suggests price cuts.",
  "e-listings": "Writes marketplace listing copy for newly logged inventory.",
  "e-pricer": "Refreshes eBay sold-comp pricing across the parts catalog.",
  "e-scanner": "Scans GovDeals + auction feeds for lots under max-safe-bid.",
};

// Derived "verdict" line from last_status (no last-summary field on Agent).
function verdictFor(a: Agent): string {
  switch (a.last_status) {
    case "success":
      return "Last run completed cleanly.";
    case "error":
      return "Last run failed — needs review.";
    case "running":
      return "Running now…";
    case "skipped_budget":
      return "Paused — daily budget reached.";
    default:
      return "Not run yet.";
  }
}

export default function AgentsPage() {
  const agents = useAgents();
  const costs = useAgentCosts();
  const health = useHealth();

  const monthTotal = costs.data?.month_total ?? 0;
  const todayTotal = agents.data?.items.reduce((s, a) => s + a.cost_today, 0) ?? 0;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        title="Agent Ops"
        subtitle="The 8-agent brain — status, cost, and verdicts. They recommend and track; you decide."
      />

      <div className="grid grid-cols-3 gap-4">
        <StatTile label="Cost today" value={money(todayTotal)} />
        <StatTile label="This month" value={money(monthTotal)} />
        <StatTile label="Projected mo." value={money(costs.data?.projected_month ?? 0)} />
      </div>

      {costs.data && costs.data.by_day.length > 0 && <CostChart costs={costs.data} />}

      {/* Agent cards */}
      {agents.isLoading && <LoadingSkeleton rows={4} />}
      {agents.isError && <ErrorState message={agents.error.message} />}
      {agents.data && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {agents.data.items.map((a) => (
            <AgentCard key={a.id} agent={a} />
          ))}
        </div>
      )}

      {/* Scores + proposals side by side */}
      <div className="grid gap-5 md:grid-cols-2">
        <ScoresPanel />
        <ProposalsPanel />
      </div>

      <IntelPanel />

      {/* System health */}
      {health.data && (
        <GlassPanel className="p-6">
          <Eyebrow className="mb-4">System Health</Eyebrow>
          <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
            {Object.entries(health.data.agents.providers).map(([name, present]) => (
              <span key={name} className="flex items-center gap-1.5 text-ink/75">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ background: present ? "#3ddc97" : "rgba(238,241,246,0.25)" }}
                />
                {name} key
              </span>
            ))}
          </div>
          <div className="mono mt-3 text-xs text-ink/50">
            Scheduler: {health.data.agents.scheduler.running ? "running" : "off"} ·{" "}
            {health.data.agents.scheduler.jobs} scheduled jobs · DB{" "}
            {health.data.db_ok ? "ok" : "down"}
          </div>
          {Object.values(health.data.agents.providers).every((p) => !p) && (
            <p className="mt-2 text-xs text-warn">
              No provider keys set — agents will record an error until a key is added to the
              backend .env (ANTHROPIC_API_KEY / DEEPSEEK_API_KEY / …).
            </p>
          )}
        </GlassPanel>
      )}
    </div>
  );
}

function AgentCard({ agent }: { agent: Agent }) {
  const run = useRunAgent();
  const update = useUpdateAgent();
  const [input, setInput] = useState("");
  const [budget, setBudget] = useState(String(agent.daily_budget_usd));
  const disabled = agent.enabled === 0;
  const meta = (agent.last_status && STATUS_META[agent.last_status]) || IDLE;
  const paramKey = agent.id === "e-customer" ? "message" : agent.id === "e-listings" ? "specs" : null;

  const trigger = () => {
    const params = paramKey && input.trim() ? { [paramKey]: input.trim() } : undefined;
    run.mutate({ id: agent.id, params });
  };
  const saveBudget = () => {
    const v = Number(budget);
    if (!Number.isNaN(v) && v !== agent.daily_budget_usd) {
      update.mutate({ id: agent.id, data: { daily_budget_usd: v } });
    }
  };

  return (
    <GlassPanel className="flex flex-col p-[18px]">
      <div className="flex items-center justify-between gap-2">
        <Link href={`/agents/${agent.id}`} className="truncate text-[13px] font-bold hover:text-accent">
          {agent.display_name}
        </Link>
        <span className="flex shrink-0 items-center gap-1.5">
          <span
            className={`h-1.5 w-1.5 rounded-full ${meta.pulse ? "animate-pulseDot" : ""}`}
            style={{ background: meta.color }}
          />
          <span className="mono text-[10px] tracking-[0.06em]" style={{ color: meta.color }}>
            {disabled ? "OFF" : meta.label}
          </span>
        </span>
      </div>

      <div className="mt-2 min-h-[34px] text-xs leading-relaxed text-ink/55">
        {ROLE[agent.id] ?? `${agent.layer} · ${agent.model}`}
      </div>

      <div className="mt-2.5 border-t border-white/[0.07] pt-2.5 text-xs text-ink/80">
        {run.data
          ? run.data.status === "success"
            ? `✓ ${run.data.summary ?? "done"}`
            : run.data.status === "skipped_budget"
              ? "⏸ Skipped — budget reached"
              : `✕ ${run.data.error ?? "error"}`
          : verdictFor(agent)}
      </div>

      <div className="mono mt-2.5 flex justify-between text-[11px] text-ink/40">
        <span>{agent.runs_today} run(s) today</span>
        <span>
          {money(agent.cost_today)}/{money(agent.daily_budget_usd)}
        </span>
      </div>

      {paramKey && (
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={paramKey === "message" ? "Paste buyer message…" : "Item specs…"}
          className="glass-field mt-2.5 w-full !py-2 text-xs"
        />
      )}

      <div className="mt-2.5 flex items-center gap-2">
        <button
          onClick={trigger}
          disabled={run.isPending || disabled}
          className="btn-accent flex-1 !py-2 !text-xs disabled:opacity-50"
        >
          {run.isPending ? "Running…" : "Trigger"}
        </button>
        <button
          onClick={() => update.mutate({ id: agent.id, data: { enabled: disabled } })}
          className="btn-ghost !min-h-0 !px-2.5 !py-2 !text-xs"
        >
          {disabled ? "On" : "Off"}
        </button>
      </div>

      <div className="mono mt-2 flex items-center gap-1.5 text-[11px] text-ink/40">
        <span>$</span>
        <input
          value={budget}
          onChange={(e) => setBudget(e.target.value)}
          onBlur={saveBudget}
          inputMode="decimal"
          aria-label="daily budget"
          className="glass-field !min-h-0 w-14 !px-2 !py-1 text-[11px]"
        />
        <span>/day</span>
      </div>

      {run.isError && <p className="mt-2 text-[11px] text-loss">{run.error.message}</p>}
    </GlassPanel>
  );
}

const TREND_ARROW: Record<string, string> = { up: "▲", down: "▼", flat: "→" };

function ScoresPanel() {
  const scores = useAgentScores();
  const latest = new Map<string, AgentScore>();
  for (const s of scores.data?.items ?? []) {
    if (!latest.has(s.agent_id)) latest.set(s.agent_id, s);
  }
  const rows = [...latest.values()];

  return (
    <GlassPanel className="p-6">
      <Eyebrow className="mb-4">Auditor — Weekly Scores</Eyebrow>
      {rows.length === 0 ? (
        <p className="text-sm text-ink/40">No weekly scores yet — Auditor runs Sundays.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {rows.map((s) => (
            <div key={s.agent_id} className="flex items-center gap-3 text-sm">
              <span className="w-24 shrink-0 truncate text-ink/80">{s.agent_id}</span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/[0.06]">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${((s.score ?? 0) / 10) * 100}%`,
                    background: "linear-gradient(90deg,#4f8cff,#6fd3ff)",
                  }}
                />
              </div>
              <span className="mono w-14 shrink-0 text-right">
                {s.score ?? "—"}/10{" "}
                <span
                  className={
                    s.trend === "up" ? "text-profit" : s.trend === "down" ? "text-loss" : "text-ink/40"
                  }
                >
                  {s.trend ? TREND_ARROW[s.trend] : ""}
                </span>
              </span>
            </div>
          ))}
        </div>
      )}
    </GlassPanel>
  );
}

function CostChart({ costs }: { costs: AgentCosts }) {
  const max = Math.max(...costs.by_day.map((d) => d.cost), 0.0001);
  return (
    <GlassPanel className="p-5">
      <Eyebrow className="mb-3">Cost / day (last 30)</Eyebrow>
      <div className="flex h-16 items-end gap-0.5">
        {costs.by_day.map((d) => (
          <div
            key={d.day}
            title={`${d.day}: ${money(d.cost)}`}
            className="flex-1 rounded-t"
            style={{
              height: `${Math.max((d.cost / max) * 100, 2)}%`,
              background: "linear-gradient(180deg,#6fd3ff,#4f8cff)",
            }}
          />
        ))}
      </div>
    </GlassPanel>
  );
}

function IntelPanel() {
  const intel = useIntel();
  const items = intel.data?.items ?? [];
  if (items.length === 0) return null;
  return (
    <GlassPanel className="p-6">
      <Eyebrow className="mb-4">Research Intel</Eyebrow>
      <div className="space-y-2.5">
        {items.slice(0, 12).map((it) => (
          <div key={it.id} className="rounded-xl border border-white/[0.07] bg-white/[0.03] p-3 text-sm">
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium">{it.subject}</span>
              <span className="mono shrink-0 text-xs text-ink/40">
                {it.category}
                {it.consumed ? " · used" : ""}
              </span>
            </div>
            <p className="mt-0.5 text-xs text-ink/60">{it.signal}</p>
            {it.action && <p className="mt-0.5 text-xs text-accent">→ {it.action}</p>}
          </div>
        ))}
      </div>
    </GlassPanel>
  );
}

function ProposalsPanel() {
  const pending = usePendingPrompts();
  const activate = useActivatePrompt();
  const items = pending.data?.items ?? [];

  return (
    <GlassPanel accent={items.length > 0 ? "warn" : undefined} className="p-6">
      <Eyebrow className={`mb-4 ${items.length > 0 ? "!text-warn/80" : ""}`}>
        Pending Prompt Improvements{items.length > 0 ? ` (${items.length})` : ""}
      </Eyebrow>
      {items.length === 0 ? (
        <p className="text-sm text-ink/40">No prompt changes awaiting approval.</p>
      ) : (
        <div className="space-y-3">
          {items.map((p: PendingPrompt) => (
            <div key={p.id} className="rounded-xl border border-warn/25 bg-warn/[0.06] p-3">
              <div className="flex items-center justify-between gap-2">
                <span className="text-[13px] font-semibold">{p.display_name}</span>
                <button
                  onClick={() => activate.mutate(p.id)}
                  disabled={activate.isPending}
                  className="btn-accent shrink-0 !py-1.5 !text-xs disabled:opacity-50"
                >
                  {activate.isPending ? "Activating…" : "Approve"}
                </button>
              </div>
              <p className="mt-1.5 line-clamp-3 text-xs text-ink/60">{p.body}</p>
            </div>
          ))}
        </div>
      )}
    </GlassPanel>
  );
}
