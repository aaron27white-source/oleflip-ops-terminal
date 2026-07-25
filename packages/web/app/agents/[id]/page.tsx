"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { ErrorState, LoadingSkeleton } from "@/components/common/states";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { Eyebrow } from "@/components/ui/primitives";
import { money } from "@/lib/format";
import { useAgentDetail, useAgentPrompts, useAgentRuns } from "@/lib/queries";

const RUN_TONE: Record<string, string> = {
  success: "text-profit",
  error: "text-loss",
  skipped_budget: "text-warn",
  running: "text-accent",
};

export default function AgentDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const detail = useAgentDetail(id);
  const runs = useAgentRuns(id);
  const prompts = useAgentPrompts(id);

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <Link href="/agents" className="text-sm text-accent">
        ← Agent Ops
      </Link>

      {detail.isLoading && <LoadingSkeleton rows={4} />}
      {detail.isError && <ErrorState message={detail.error.message} />}
      {detail.data && (
        <>
          <div>
            <h1 className="text-[22px] font-bold">{detail.data.agent.display_name}</h1>
            <div className="mono mt-1 text-sm text-ink/50">
              {detail.data.agent.layer} · {detail.data.agent.provider}/{detail.data.agent.model}
              {detail.data.agent.schedule_cron
                ? ` · ${detail.data.agent.schedule_cron}`
                : " · on-demand"}{" "}
              · budget {money(detail.data.agent.daily_budget_usd)}/day
              {detail.data.agent.enabled === 0 && " · off"}
            </div>
          </div>

          <GlassPanel className="p-6">
            <Eyebrow className="mb-3">
              Active prompt{" "}
              {detail.data.active_prompt && (
                <span className="text-ink/40">
                  {detail.data.active_prompt.version} · {detail.data.active_prompt.created_by}
                </span>
              )}
            </Eyebrow>
            <p className="whitespace-pre-wrap text-xs text-ink/70">
              {detail.data.active_prompt?.body ?? "—"}
            </p>
          </GlassPanel>
        </>
      )}

      <GlassPanel className="p-6">
        <Eyebrow className="mb-4">Run history</Eyebrow>
        {runs.isLoading && <LoadingSkeleton rows={3} />}
        {runs.data && runs.data.items.length === 0 && <p className="text-sm text-ink/40">No runs yet.</p>}
        <div className="space-y-1.5">
          {runs.data?.items.map((r) => (
            <div key={r.id} className="rounded-lg border border-white/[0.07] bg-white/[0.03] p-2.5 text-xs">
              <div className="flex items-center justify-between gap-2">
                <span className={RUN_TONE[r.status] ?? "text-ink/50"}>{r.status}</span>
                <span className="mono text-ink/40">
                  {r.started_at} · {r.tokens_in + r.tokens_out} tok · {money(r.cost_usd)}
                </span>
              </div>
              {r.output_summary && <p className="mt-0.5 text-ink/60">{r.output_summary}</p>}
              {r.error && <p className="mt-0.5 text-loss">{r.error}</p>}
            </div>
          ))}
        </div>
      </GlassPanel>

      <GlassPanel className="p-6">
        <Eyebrow className="mb-4">Prompt versions</Eyebrow>
        <div className="space-y-1.5">
          {prompts.data?.items.map((p) => (
            <div
              key={p.id}
              className="flex items-center justify-between rounded-lg border border-white/[0.07] bg-white/[0.03] p-2.5 text-xs"
            >
              <span className="mono">{p.version}</span>
              <span className="mono text-ink/40">
                {p.created_by}
                {p.active ? " · active" : ""}
              </span>
            </div>
          ))}
        </div>
      </GlassPanel>
    </div>
  );
}
