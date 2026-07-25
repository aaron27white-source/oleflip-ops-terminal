"use client";

import { useState } from "react";

import { Sheet } from "@/components/common/Sheet";
import { useUpdateInventory } from "@/lib/queries";
import type { InventoryItem } from "@/lib/types";

const PLATFORMS = ["eBay", "FB", "flea", "other"];
const EBAY_FEE_RATE = 0.1325; // mirrors Phase 1's EBAY_FEE_PERCENT

export function MarkSoldSheet({
  item,
  open,
  onClose,
}: {
  item: InventoryItem;
  open: boolean;
  onClose: () => void;
}) {
  const update = useUpdateInventory(item.id);
  const [sellPrice, setSellPrice] = useState("");
  const [soldOn, setSoldOn] = useState("eBay");
  const [fees, setFees] = useState("");

  // Suggest eBay's fee when the platform is eBay and the user hasn't overridden it.
  const suggestedFee =
    soldOn === "eBay" && sellPrice ? (parseFloat(sellPrice) * EBAY_FEE_RATE).toFixed(2) : "";

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    await update.mutateAsync({
      status: "sold",
      sell_price: parseFloat(sellPrice) || 0,
      sell_fees: parseFloat(fees || suggestedFee) || 0,
      sold_on: soldOn,
    });
    onClose();
  }

  return (
    <Sheet open={open} onClose={onClose} title={`Mark sold — ${item.title}`}>
      <form onSubmit={submit} className="space-y-3">
        <label className="block">
          <span className="text-sm font-medium text-ink/70">Sold for ($)</span>
          <input
            autoFocus
            inputMode="decimal"
            value={sellPrice}
            onChange={(e) => setSellPrice(e.target.value)}
            className={inputCls}
          />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-ink/70">Platform</span>
          <select value={soldOn} onChange={(e) => setSoldOn(e.target.value)} className={inputCls}>
            {PLATFORMS.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="text-sm font-medium text-ink/70">
            Fees ($){suggestedFee && !fees ? ` — eBay suggests $${suggestedFee}` : ""}
          </span>
          <input
            inputMode="decimal"
            value={fees}
            onChange={(e) => setFees(e.target.value)}
            placeholder={suggestedFee || "0"}
            className={inputCls}
          />
        </label>
        <button
          type="submit"
          disabled={!sellPrice || update.isPending}
          className="btn-accent w-full disabled:opacity-50"
        >
          {update.isPending ? "Saving…" : "Mark sold"}
        </button>
      </form>
    </Sheet>
  );
}

const inputCls = "glass-field mt-1 w-full text-sm";
