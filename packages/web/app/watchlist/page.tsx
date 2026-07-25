"use client";

import { useState } from "react";

import { ErrorState, LoadingSkeleton } from "@/components/common/states";
import { StatTile } from "@/components/common/StatTile";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { Eyebrow, PageHeader } from "@/components/ui/primitives";
import { money, percent } from "@/lib/format";
import {
  useBids,
  useCreateWatch,
  useDeleteWatch,
  useUpdateWatch,
  useWatchlist,
} from "@/lib/queries";
import type { WatchedListing } from "@/lib/types";

export default function WatchlistPage() {
  const watchlist = useWatchlist();
  const bids = useBids();
  const create = useCreateWatch();
  const [name, setName] = useState("");
  const [target, setTarget] = useState("");
  const [maxBid, setMaxBid] = useState("");

  const submit = () => {
    if (!name.trim()) return;
    create.mutate(
      {
        item_name: name.trim(),
        target_price: target ? Number(target) : undefined,
        max_bid: maxBid ? Number(maxBid) : undefined,
      },
      {
        onSuccess: () => {
          setName("");
          setTarget("");
          setMaxBid("");
        },
      },
    );
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader
        title="Watch List & Bids"
        subtitle="Track listings you're eyeing and the bids you place — win rate rolls up automatically."
      />

      <div className="grid grid-cols-2 gap-4">
        <StatTile label="Watching" value={String(watchlist.data?.total ?? "—")} />
        <StatTile
          label="Bid win rate"
          value={percent(bids.data?.win_rate != null ? bids.data.win_rate * 100 : null)}
        />
      </div>

      {/* Add form */}
      <GlassPanel className="p-5">
        <Eyebrow className="mb-3">Add a listing</Eyebrow>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Item name (e.g. Dell R740 lot)"
          className="glass-field w-full text-sm"
        />
        <div className="mt-2.5 flex gap-2.5">
          <input
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            inputMode="decimal"
            placeholder="Target $"
            className="glass-field mono w-full text-sm"
          />
          <input
            value={maxBid}
            onChange={(e) => setMaxBid(e.target.value)}
            inputMode="decimal"
            placeholder="Max bid $"
            className="glass-field mono w-full text-sm"
          />
        </div>
        <button
          onClick={submit}
          disabled={create.isPending || !name.trim()}
          className="btn-accent mt-2.5 w-full disabled:opacity-50"
        >
          {create.isPending ? "Adding…" : "Add to watch list"}
        </button>
      </GlassPanel>

      {watchlist.isLoading && <LoadingSkeleton rows={3} />}
      {watchlist.isError && <ErrorState message={watchlist.error.message} />}
      {watchlist.data && watchlist.data.items.length === 0 && (
        <p className="text-sm text-ink/40">Nothing on the watch list yet.</p>
      )}
      <div className="space-y-3">
        {watchlist.data?.items.map((w) => (
          <WatchRow key={w.id} watch={w} />
        ))}
      </div>
    </div>
  );
}

const STATUS_TONE: Record<string, string> = {
  active: "text-accent",
  won: "text-profit",
  lost: "text-loss",
  expired: "text-ink/40",
  cancelled: "text-ink/40",
};

function WatchRow({ watch }: { watch: WatchedListing }) {
  const update = useUpdateWatch();
  const del = useDeleteWatch();
  const setStatus = (status: string) => update.mutate({ id: watch.id, data: { status } });

  return (
    <GlassPanel className="p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate font-medium">{watch.item_name}</div>
          <div className="mono mt-0.5 text-xs text-ink/50">
            {watch.target_price != null && <>target {money(watch.target_price)} · </>}
            {watch.max_bid != null && <>max {money(watch.max_bid)} · </>}
            <span className={STATUS_TONE[watch.status] ?? ""}>{watch.status}</span>
          </div>
        </div>
        <button
          onClick={() => del.mutate(watch.id)}
          className="!min-h-0 shrink-0 text-xs text-ink/40 hover:text-loss"
        >
          Remove
        </button>
      </div>
      {watch.status === "active" && (
        <div className="mt-3 flex gap-2">
          <button
            onClick={() => setStatus("won")}
            className="!min-h-0 rounded-lg bg-profit/15 px-3 py-1.5 text-xs font-semibold text-profit"
          >
            Won
          </button>
          <button
            onClick={() => setStatus("lost")}
            className="!min-h-0 rounded-lg bg-loss/15 px-3 py-1.5 text-xs font-semibold text-loss"
          >
            Lost
          </button>
          <button
            onClick={() => setStatus("cancelled")}
            className="!min-h-0 rounded-lg bg-white/[0.06] px-3 py-1.5 text-xs text-ink/60"
          >
            Cancel
          </button>
        </div>
      )}
    </GlassPanel>
  );
}
