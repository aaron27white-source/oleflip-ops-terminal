"use client";

import { useState } from "react";

import { ErrorState, LoadingSkeleton } from "@/components/common/states";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { Eyebrow, PageHeader } from "@/components/ui/primitives";
import { money } from "@/lib/format";
import { useRunScan, useWatches } from "@/lib/queries";
import type { ScanLot } from "@/lib/types";

export default function ScannerPage() {
  const watches = useWatches();
  const scan = useRunScan();
  const [activeOnly, setActiveOnly] = useState(false);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <PageHeader
        title="GovDeals Scanner"
        subtitle="Scans GovDeals for Dell/HP/Lenovo lots, matches your machine profiles, and works out per-unit price vs. your max safe bid."
      />

      <label className="flex items-center gap-2 text-sm text-ink/70">
        <input
          type="checkbox"
          checked={activeOnly}
          onChange={(e) => setActiveOnly(e.target.checked)}
          className="!min-h-0"
        />
        Active auctions only (this actor mostly returns sold lots, so this often comes back empty)
      </label>

      <GlassPanel className="p-6">
        <Eyebrow className="mb-4">Saved searches — tap to scan</Eyebrow>
        {watches.isLoading && <LoadingSkeleton rows={2} />}
        {watches.data && (
          <div className="flex flex-wrap gap-2">
            {watches.data.items.map((w) => (
              <button
                key={w.id}
                onClick={() =>
                  scan.mutate({ watch: w.search_text, dry_run: true, active_only: activeOnly })
                }
                disabled={scan.isPending}
                className="!min-h-0 rounded-full border border-white/10 bg-white/[0.04] px-3.5 py-1.5 text-sm text-ink/75 transition-colors hover:bg-white/[0.08] disabled:opacity-50"
              >
                {w.search_text}
              </button>
            ))}
          </div>
        )}
      </GlassPanel>

      {scan.isPending && <p className="mono animate-pulse text-sm text-ink/50">Scanning GovDeals…</p>}
      {scan.isError && (
        <ErrorState
          message={
            scan.error.message.includes("APIFY")
              ? "GovDeals scanning needs APIFY_API_TOKEN set on the server (free Apify account). See the README."
              : scan.error.message
          }
        />
      )}

      {scan.data && !scan.isPending && (
        <div className="space-y-3">
          <p className="mono text-sm text-ink/60">
            {scan.data.scanned} lots · {scan.data.matched} matched a profile · {scan.data.good}{" "}
            good-margin{scan.data.sold ? ` · ${scan.data.sold} sold/completed` : ""}
          </p>
          {scan.data.lots.length === 0 && (
            <p className="text-sm text-ink/40">No lots returned for this search.</p>
          )}
          {scan.data.lots.map((l, i) => (
            <LotCard key={l.url || `${l.title}-${i}`} lot={l} />
          ))}
        </div>
      )}
    </div>
  );
}

function LotCard({ lot }: { lot: ScanLot }) {
  const bulk = lot.quantity > 1;
  return (
    <GlassPanel accent={lot.margin_good ? "profit" : undefined} className="p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="font-medium">
            {lot.matched_model || <span className="text-ink/40">no profile match</span>}
            {bulk && <span className="ml-2 text-xs text-ink/50">{lot.quantity}× units</span>}
          </div>
          <div className="truncate text-xs text-ink/50">{lot.title}</div>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-1">
          {lot.is_sold && (
            <span className="mono rounded bg-white/10 px-1.5 py-0.5 text-[10px] font-semibold text-ink/60">
              SOLD
            </span>
          )}
          {lot.priced && (
            <span className={`mono text-xs font-bold ${lot.margin_good ? "text-profit" : "text-loss"}`}>
              {lot.margin_good ? "BUY" : "PASS"}
            </span>
          )}
        </div>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
        <Row label="Total price" value={money(lot.total_cost)} />
        {bulk && <Row label="Per unit" value={money(lot.per_unit_cost)} strong />}
        {lot.priced && (
          <>
            <Row label={bulk ? "Max / unit" : "Max safe bid"} value={money(lot.max_bid_per_unit)} />
            {lot.headroom != null && (
              <Row label="Headroom" value={money(lot.headroom)} tone={lot.margin_good ? "good" : "bad"} />
            )}
          </>
        )}
      </div>

      {!lot.priced && lot.matched_model && (
        <p className="mt-1 text-xs text-warn">matched, but no pricing for this model yet</p>
      )}
      {lot.url && (
        <a href={lot.url} target="_blank" rel="noreferrer" className="mt-2 block text-xs text-accent">
          View on GovDeals ↗
        </a>
      )}
    </GlassPanel>
  );
}

function Row({
  label,
  value,
  strong,
  tone,
}: {
  label: string;
  value: string;
  strong?: boolean;
  tone?: "good" | "bad";
}) {
  const cls = tone === "good" ? "text-profit" : tone === "bad" ? "text-loss" : "";
  return (
    <div className="flex justify-between">
      <span className="text-ink/50">{label}</span>
      <span className={`mono ${strong ? "font-semibold" : ""} ${cls}`}>{value}</span>
    </div>
  );
}
