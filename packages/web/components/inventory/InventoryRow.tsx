"use client";

import Link from "next/link";
import { useState } from "react";

import { money } from "@/lib/format";
import { useDeleteInventory } from "@/lib/queries";
import type { InventoryItem } from "@/lib/types";
import { MarkSoldSheet } from "./MarkSoldSheet";

const STATUS_META: Record<string, { label: string; cls: string }> = {
  in_stock: { label: "In stock", cls: "bg-accent/15 text-accent" },
  listed: { label: "Listed", cls: "bg-accent-cyan/15 text-accent-cyan" },
  sold: { label: "Sold", cls: "bg-profit/15 text-profit" },
  scrapped: { label: "Scrapped", cls: "bg-warn/15 text-warn" },
};

export function InventoryRow({ item }: { item: InventoryItem }) {
  const [markSold, setMarkSold] = useState(false);
  const del = useDeleteInventory();
  const sold = item.status === "sold";
  const netTone = item.net_profit >= 0 ? "text-profit" : "text-loss";
  const meta = STATUS_META[item.status] ?? { label: item.status, cls: "bg-white/10 text-ink/60" };
  const count = item.photo_count ?? 0;

  return (
    <div className="glass-tile p-4">
      <div className="flex items-start gap-3">
        {/* cover thumbnail → detail page */}
        <Link
          href={`/inventory/${item.id}`}
          className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-white/10 bg-white/[0.03]"
        >
          {item.primary_photo ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={`/uploads/${item.id}/${item.primary_photo}`}
              alt=""
              className="h-full w-full object-cover"
            />
          ) : (
            <span className="text-lg text-ink/30">▤</span>
          )}
        </Link>

        <div className="min-w-0 flex-1">
          <Link href={`/inventory/${item.id}`} className="block truncate font-medium text-ink/90 hover:text-accent">
            {item.title}
          </Link>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-ink/50">
            <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${meta.cls}`}>
              {meta.label}
            </span>
            <span>bought {money(item.buy_price + item.buy_shipping)}</span>
            {sold && item.sell_price != null && <span>· sold {money(item.sell_price)}</span>}
            {count > 0 && <span>· 📸 {count}</span>}
          </div>
        </div>

        <div className="text-right">
          <div className={`mono font-semibold ${sold ? netTone : "text-ink/40"}`}>
            {sold ? money(item.net_profit) : "—"}
          </div>
          {sold && item.roi_pct != null && (
            <div className="mono text-xs text-ink/50">{item.roi_pct}% ROI</div>
          )}
        </div>
      </div>
      <div className="mt-3 flex items-center gap-2">
        {!sold && (
          <button onClick={() => setMarkSold(true)} className="btn-ghost flex-1 !py-2 !text-[13px]">
            Mark sold
          </button>
        )}
        <Link href={`/inventory/${item.id}`} className="btn-ghost !py-2 !text-[13px]">
          Photos
        </Link>
        <button
          onClick={() => {
            if (confirm(`Delete "${item.title}" from inventory?`)) del.mutate(item.id);
          }}
          className="btn-ghost !py-2 !text-[13px] !text-ink/40 hover:!text-loss"
        >
          Delete
        </button>
      </div>
      <MarkSoldSheet item={item} open={markSold} onClose={() => setMarkSold(false)} />
    </div>
  );
}
