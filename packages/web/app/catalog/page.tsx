"use client";

import { useState } from "react";

import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/common/states";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { PageHeader } from "@/components/ui/primitives";
import { money } from "@/lib/format";
import { useParts, useRecordPrice, useRefreshComps, useStaleness } from "@/lib/queries";
import type { Part } from "@/lib/types";

const PART_CATEGORIES = ["", "RAM", "SSD", "CPU", "GPU", "NIC", "WIFI", "PSU"];

const REFRESH_SOURCES = [
  { value: "rapidapi", label: "RapidAPI" },
  { value: "api", label: "Official eBay API" },
  { value: "scrape", label: "Direct scrape" },
];

export default function CatalogPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [source, setSource] = useState("rapidapi");
  const parts = useParts(search, category);
  const staleness = useStaleness();
  const refresh = useRefreshComps();

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <PageHeader title="Part Catalog" subtitle="Resale prices and net profit by part." />

      <div className="flex items-center gap-2">
        <select
          value={source}
          onChange={(e) => setSource(e.target.value)}
          aria-label="Price source"
          className="glass-field text-sm"
        >
          {REFRESH_SOURCES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
        <button
          onClick={() => refresh.mutate({ all: true, source })}
          disabled={refresh.isPending}
          className="btn-accent flex-1 disabled:opacity-50"
        >
          {refresh.isPending ? "Refreshing…" : "↻ Refresh prices"}
        </button>
      </div>

      {staleness.data && staleness.data.blind > 0 && (
        <p className="text-xs text-warn">
          ⚠️ {staleness.data.blind} of {staleness.data.total} parts have no price in the last 30
          days — refresh to keep bids accurate.
        </p>
      )}
      {refresh.isError && (
        <p className="rounded-lg bg-loss/[0.08] p-2 text-xs text-loss">{refresh.error.message}</p>
      )}
      {refresh.data && !refresh.isPending && (
        <p className="text-xs text-profit">
          Refreshed {refresh.data.parts} parts · {refresh.data.inserted} new comps recorded.
          {refresh.data.warnings &&
            refresh.data.warnings.length > 0 &&
            ` (${refresh.data.warnings.length} skipped)`}
        </p>
      )}

      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search parts…"
        className="glass-field w-full"
      />

      <div className="flex gap-2 overflow-x-auto pb-1">
        {PART_CATEGORIES.map((c) => (
          <button
            key={c || "all"}
            onClick={() => setCategory(c)}
            className={`!min-h-0 whitespace-nowrap rounded-full px-3.5 py-1.5 text-sm transition-colors ${
              category === c
                ? "bg-accent/[0.16] text-ink [border:1px_solid_rgba(120,170,255,0.4)]"
                : "border border-white/10 bg-white/[0.03] text-ink/60 hover:bg-white/[0.06]"
            }`}
          >
            {c || "All"}
          </button>
        ))}
      </div>

      {parts.isLoading && <LoadingSkeleton rows={5} />}
      {parts.isError && <ErrorState message="Couldn't load parts." onRetry={() => parts.refetch()} />}
      {parts.data && parts.data.items.length === 0 && <EmptyState title="No parts match." />}
      {parts.data && parts.data.items.length > 0 && (
        <div className="space-y-3">
          {parts.data.items.map((p) => (
            <PartRow key={p.id} part={p} />
          ))}
        </div>
      )}
    </div>
  );
}

function PartRow({ part }: { part: Part }) {
  const record = useRecordPrice();
  const [open, setOpen] = useState(false);
  const [price, setPrice] = useState("");

  const logPrice = () => {
    if (!price) return;
    record.mutate(
      { partId: part.id, price: Number(price), source: "manual" },
      {
        onSuccess: () => {
          setPrice("");
          setOpen(false);
        },
      },
    );
  };

  return (
    <GlassPanel className="p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate font-medium">{part.name}</div>
          <div className="text-xs text-ink/50">
            {part.category}
            {part.subcategory ? ` · ${part.subcategory}` : ""} · {part.sell_speed}
          </div>
        </div>
        <div className="text-right">
          <div className="mono font-semibold">{part.price ? money(part.price.avg_price_30d) : "—"}</div>
          {part.net_profit != null && (
            <div className="mono text-xs text-profit">net {money(part.net_profit)}</div>
          )}
          <button onClick={() => setOpen((v) => !v)} className="!min-h-0 mt-1 text-xs text-accent">
            {open ? "cancel" : "+ comp"}
          </button>
        </div>
      </div>
      {open && (
        <div className="mt-2.5 flex items-center gap-2 text-sm">
          <span className="text-xs text-ink/40">Sold price $</span>
          <input
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            inputMode="decimal"
            aria-label="sold price"
            className="glass-field mono !min-h-0 w-24 !py-1.5"
          />
          <button
            onClick={logPrice}
            disabled={record.isPending || !price}
            className="btn-accent !min-h-0 !py-1.5 !text-xs disabled:opacity-50"
          >
            {record.isPending ? "…" : "Log"}
          </button>
        </div>
      )}
    </GlassPanel>
  );
}
