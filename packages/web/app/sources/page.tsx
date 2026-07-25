"use client";

import { ErrorState, LoadingSkeleton } from "@/components/common/states";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { PageHeader } from "@/components/ui/primitives";
import { money, percent } from "@/lib/format";
import {
  useDeleteSource,
  useSourcePerformance,
  useSources,
  useUpdateSource,
} from "@/lib/queries";
import type { Source } from "@/lib/types";

export default function SourcesPage() {
  const perf = useSourcePerformance();
  const sources = useSources();
  const update = useUpdateSource();
  const del = useDeleteSource();
  const byId = new Map<number, Source>((sources.data?.items ?? []).map((s) => [s.id, s]));

  const setReliability = (id: number, score: number) => {
    const s = byId.get(id);
    if (!s) return;
    update.mutate({
      id,
      data: { name: s.name, type: s.type, reliability_score: score, notes: s.notes ?? undefined },
    });
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader title="Sources" subtitle="Which places actually make you money." />

      {perf.isLoading && <LoadingSkeleton rows={4} />}
      {perf.isError && <ErrorState message="Couldn't load sources." onRetry={() => perf.refetch()} />}
      {perf.data && (
        <div className="space-y-3">
          {perf.data.items.map((s) => (
            <GlassPanel key={s.id} className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-medium">{s.name}</span>
                  <span className="mono ml-2 text-xs text-ink/40">{s.type}</span>
                </div>
                <span className={`mono font-semibold ${s.realized_profit >= 0 ? "text-profit" : "text-loss"}`}>
                  {money(s.realized_profit)}
                </span>
              </div>
              <div className="mono mt-1.5 flex flex-wrap gap-4 text-xs text-ink/50">
                <span>{s.items_bought} bought</span>
                <span>spend {money(s.total_spend)}</span>
                <span>ROI {percent(s.avg_roi_pct)}</span>
              </div>
              <div className="mt-2.5 flex items-center gap-2 text-xs">
                <span className="text-ink/40">Reliability</span>
                {[1, 2, 3, 4, 5].map((n) => (
                  <button
                    key={n}
                    onClick={() => setReliability(s.id, n)}
                    className={`!min-h-0 ${n <= s.reliability_score ? "text-warn" : "text-white/15"}`}
                    aria-label={`set reliability ${n}`}
                  >
                    ★
                  </button>
                ))}
                <button
                  onClick={() => {
                    if (confirm(`Delete source "${s.name}"?`)) del.mutate(s.id);
                  }}
                  className="!min-h-0 ml-auto text-ink/40 hover:text-loss"
                >
                  Remove
                </button>
              </div>
            </GlassPanel>
          ))}
        </div>
      )}
    </div>
  );
}
