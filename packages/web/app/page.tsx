"use client";

import Link from "next/link";

import { StatTile } from "@/components/common/StatTile";
import { ErrorState, LoadingSkeleton } from "@/components/common/states";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { Eyebrow, PageHeader } from "@/components/ui/primitives";
import { money } from "@/lib/format";
import { useDashboard } from "@/lib/queries";

export default function Home() {
  const dash = useDashboard("month");

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader title="Ops Dashboard" subtitle="Your flipping console at a glance." />

      <Link href="/bid" className="block">
        <GlassPanel className="p-6 transition-transform hover:-translate-y-0.5" accent="profit">
          <div className="flex items-center justify-between gap-4">
            <div>
              <div className="text-lg font-semibold">▲ Bid Calculator</div>
              <div className="mt-1 text-sm text-ink/55">
                Standing in front of a pallet? Get BUY or PASS instantly.
              </div>
            </div>
            <span className="mono text-2xl text-accent">→</span>
          </div>
        </GlassPanel>
      </Link>

      {dash.isLoading && <LoadingSkeleton rows={2} />}
      {dash.isError && <ErrorState message="Couldn't load stats." onRetry={() => dash.refetch()} />}

      {dash.data && (
        <>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatTile
              label="Profit this month"
              value={money(dash.data.profit_this_period)}
              tone={dash.data.profit_this_period >= 0 ? "good" : "bad"}
            />
            <StatTile label="Tied up in stock" value={money(dash.data.unrealized_cost)} />
            <StatTile label="In stock" value={String(dash.data.items_in_stock)} />
            <StatTile label="Listed" value={String(dash.data.items_listed)} />
          </div>

          {dash.data.best_deals.length > 0 && (
            <GlassPanel className="p-6">
              <Eyebrow className="mb-4">🔥 Best flagged deals</Eyebrow>
              <div className="space-y-2.5">
                {dash.data.best_deals.map((d) => (
                  <Link
                    key={d.id}
                    href="/scanner"
                    className="block rounded-xl border border-profit-dim/25 bg-profit/[0.07] p-3"
                  >
                    <div className="flex justify-between">
                      <span className="font-medium">{d.matched_model}</span>
                      <span className="mono text-profit">+{money(d.headroom)} headroom</span>
                    </div>
                    <div className="truncate text-xs text-ink/50">{d.title}</div>
                  </Link>
                ))}
              </div>
            </GlassPanel>
          )}

          {dash.data.recent_sales.length > 0 && (
            <GlassPanel className="p-6">
              <Eyebrow className="mb-4">Recent sales</Eyebrow>
              <div className="space-y-2">
                {dash.data.recent_sales.map((s) => (
                  <div key={s.id} className="flex justify-between text-sm">
                    <span className="truncate text-ink/70">{s.title}</span>
                    <span className={`mono ${s.net_profit >= 0 ? "text-profit" : "text-loss"}`}>
                      {money(s.net_profit)}
                    </span>
                  </div>
                ))}
              </div>
            </GlassPanel>
          )}

          {dash.data.staleness_warnings > 0 && (
            <p className="text-center text-xs text-warn">
              ⚠️ {dash.data.staleness_warnings} parts have stale pricing — refresh comps soon.
            </p>
          )}

          <div className="grid grid-cols-2 gap-4">
            <NavCard href="/inventory" title="▣ Inventory" note="Buys & sales" />
            <NavCard href="/scanner" title="◉ Scanner" note="GovDeals deals" />
          </div>
        </>
      )}
    </div>
  );
}

function NavCard({ href, title, note }: { href: string; title: string; note: string }) {
  return (
    <Link href={href}>
      <GlassPanel className="p-4 transition-transform hover:-translate-y-0.5">
        <div className="font-semibold">{title}</div>
        <div className="mt-0.5 text-xs text-ink/50">{note}</div>
      </GlassPanel>
    </Link>
  );
}
