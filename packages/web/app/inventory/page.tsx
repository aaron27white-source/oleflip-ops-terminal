"use client";

import { useState } from "react";

import { StatTile } from "@/components/common/StatTile";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/common/states";
import { InventoryRow } from "@/components/inventory/InventoryRow";
import { LogPurchaseSheet } from "@/components/inventory/LogPurchaseSheet";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { Eyebrow, PageHeader, ProgressBar } from "@/components/ui/primitives";
import { money } from "@/lib/format";
import {
  useApplySuggestion,
  useInventory,
  useInventorySuggestions,
  usePnl,
  useSourcePerformance,
} from "@/lib/queries";
import type { InventoryItem, InventorySuggestion, InvStatus } from "@/lib/types";

const FILTERS: { label: string; value: InvStatus | "" }[] = [
  { label: "All", value: "" },
  { label: "In stock", value: "in_stock" },
  { label: "Listed", value: "listed" },
  { label: "Sold", value: "sold" },
];

export default function InventoryPage() {
  const [status, setStatus] = useState<InvStatus | "">("");
  const [logging, setLogging] = useState(false);
  const inv = useInventory(status || undefined);
  const pnl = usePnl("month");
  const sold = useInventory("sold");
  const sources = useSourcePerformance();
  const suggestions = useInventorySuggestions();

  const soldCount = pnl.data?.by_status?.sold ?? 0;
  const suggestionItems = suggestions.data?.items ?? [];

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        title="Inventory & P&L"
        subtitle="What you own, what it's worth, and the money at a glance."
        action={
          <button onClick={() => setLogging(true)} className="btn-accent">
            ＋ Log purchase
          </button>
        }
      />

      {/* KPI row */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatTile label="Total items" value={String(pnl.data?.item_count ?? "—")} />
        <StatTile label="Tied up in stock" value={money(pnl.data?.unrealized_cost)} />
        <StatTile
          label="Realized profit (mo)"
          value={money(pnl.data?.realized_profit)}
          tone={(pnl.data?.realized_profit ?? 0) >= 0 ? "good" : "bad"}
        />
        <StatTile label="Sold this month" value={String(soldCount)} />
      </div>

      {/* Aging-stock suggestions from the E-Inventory agent (Tier 1) */}
      {suggestionItems.length > 0 && <SuggestionsPanel items={suggestionItems} />}

      {/* Filters */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setStatus(f.value)}
            className={`!min-h-0 whitespace-nowrap rounded-full px-3.5 py-1.5 text-sm transition-colors ${
              status === f.value
                ? "bg-accent/[0.16] text-ink [border:1px_solid_rgba(120,170,255,0.4)]"
                : "border border-white/10 bg-white/[0.03] text-ink/60 hover:bg-white/[0.06]"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Inventory list */}
      {inv.isLoading && <LoadingSkeleton rows={4} />}
      {inv.isError && <ErrorState message="Couldn't load inventory." onRetry={() => inv.refetch()} />}
      {inv.data && inv.data.items.length === 0 && (
        <EmptyState
          title="Nothing logged yet."
          action={
            <button onClick={() => setLogging(true)} className="btn-accent">
              ＋ Log your first find
            </button>
          }
        />
      )}
      {inv.data && inv.data.items.length > 0 && (
        <div className="space-y-3">
          {inv.data.items.map((it) => (
            <InventoryRow key={it.id} item={it} />
          ))}
        </div>
      )}

      {/* P&L panels */}
      <div className="grid gap-5 md:grid-cols-2">
        <GlassPanel className="p-6">
          <Eyebrow className="mb-4">Profit by source</Eyebrow>
          <ProfitBySource
            rows={sources.data?.items ?? []}
            loading={sources.isLoading}
          />
        </GlassPanel>
        <GlassPanel className="p-6">
          <Eyebrow className="mb-4">Monthly profit trend</Eyebrow>
          <MonthlyTrend items={sold.data?.items ?? []} />
        </GlassPanel>
      </div>

      <LogPurchaseSheet open={logging} onClose={() => setLogging(false)} />
    </div>
  );
}

function SuggestionsPanel({ items }: { items: InventorySuggestion[] }) {
  const apply = useApplySuggestion();
  return (
    <GlassPanel accent="warn" className="p-6">
      <Eyebrow className="mb-4 !text-warn/80">Aging stock — agent suggestions ({items.length})</Eyebrow>
      <div className="space-y-2">
        {items.map((s) => (
          <div
            key={s.id}
            className="flex items-start justify-between gap-3 rounded-xl border border-warn/20 bg-warn/[0.06] p-3"
          >
            <div className="min-w-0">
              <div className="truncate text-sm font-medium">{s.title}</div>
              <div className="mt-0.5 text-xs text-ink/60">{s.reasoning}</div>
              <div className="mono mt-1 flex flex-wrap gap-3 text-[11px] text-ink/45">
                {s.days_held != null && <span>held {s.days_held}d</span>}
                {s.suggested_platform && <span>→ {s.suggested_platform}</span>}
                {s.suggested_price != null && <span>@ {money(s.suggested_price)}</span>}
              </div>
            </div>
            <button
              onClick={() => apply.mutate(s.id)}
              disabled={apply.isPending}
              className="btn-ghost !min-h-0 shrink-0 !py-1.5 !text-xs disabled:opacity-50"
            >
              Done
            </button>
          </div>
        ))}
      </div>
    </GlassPanel>
  );
}

function ProfitBySource({
  rows,
  loading,
}: {
  rows: { name: string; realized_profit: number }[];
  loading: boolean;
}) {
  const withProfit = rows.filter((r) => r.realized_profit > 0);
  if (loading) return <div className="h-24 animate-pulse rounded-xl bg-white/[0.04]" />;
  if (withProfit.length === 0)
    return <p className="text-sm text-ink/40">No realized profit by source yet.</p>;
  const max = Math.max(...withProfit.map((r) => r.realized_profit));
  return (
    <div className="flex flex-col gap-3.5">
      {withProfit.map((r) => (
        <div key={r.name}>
          <div className="mb-1.5 flex justify-between text-[13px]">
            <span className="text-ink/80">{r.name}</span>
            <span className="mono font-semibold text-profit">{money(r.realized_profit)}</span>
          </div>
          <ProgressBar pct={(r.realized_profit / max) * 100} tone="profit" height={8} />
        </div>
      ))}
    </div>
  );
}

/**
 * Monthly profit trend. No backend endpoint exposes a monthly series, so this
 * derives bars client-side from sold-item `sold_on` dates. When there are no
 * sales yet it renders a flat illustrative axis (labeled "no sales") rather
 * than fabricating numbers — per the handoff "flag, don't invent" rule.
 */
function MonthlyTrend({ items }: { items: InventoryItem[] }) {
  const byMonth = new Map<string, number>();
  for (const it of items) {
    const d = it.sold_on || it.sell_date;
    if (!d) continue;
    const key = new Date(d).toLocaleString("en-US", { month: "short" });
    byMonth.set(key, (byMonth.get(key) ?? 0) + it.net_profit);
  }
  const months = [...byMonth.entries()];
  if (months.length === 0) {
    return (
      <div className="flex h-[150px] items-end gap-3">
        {["Feb", "Mar", "Apr", "May", "Jun", "Jul"].map((m) => (
          <div key={m} className="flex flex-1 flex-col items-center gap-2">
            <div className="w-full rounded-t-md bg-white/[0.05]" style={{ height: "8%" }} />
            <span className="text-[11px] text-ink/30">{m}</span>
          </div>
        ))}
        <span className="mono absolute -mt-6 text-[10px] text-ink/30">no sales yet</span>
      </div>
    );
  }
  const max = Math.max(...months.map(([, v]) => v), 1);
  return (
    <div className="flex h-[150px] items-end gap-3.5">
      {months.map(([m, v]) => (
        <div key={m} className="flex h-full flex-1 flex-col items-center justify-end gap-2">
          <span className="mono text-[10px] text-ink/50">{money(v)}</span>
          <div
            className="w-full rounded-t-md"
            style={{
              height: `${Math.max(4, (v / max) * 100)}%`,
              background: "linear-gradient(180deg,#6fd3ff,#4f8cff)",
            }}
          />
          <span className="text-[11px] text-ink/45">{m}</span>
        </div>
      ))}
    </div>
  );
}
