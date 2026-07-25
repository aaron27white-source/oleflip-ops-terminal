"use client";

import { useState } from "react";

import { Sheet } from "@/components/common/Sheet";
import { useLogPurchase } from "@/lib/queries";
import { SourcePicker } from "./SourcePicker";

const CONDITIONS = ["New", "Like-New", "Good", "Fair", "For-Parts"];

export function LogPurchaseSheet({
  open,
  onClose,
  prefill,
}: {
  open: boolean;
  onClose: () => void;
  prefill?: { title?: string; buy_price?: number; machine_model?: string };
}) {
  const log = useLogPurchase();
  const [title, setTitle] = useState(prefill?.title ?? "");
  const [buyPrice, setBuyPrice] = useState(prefill?.buy_price?.toString() ?? "");
  const [buyShipping, setBuyShipping] = useState("");
  const [condition, setCondition] = useState("");
  const [sourceId, setSourceId] = useState<number | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    await log.mutateAsync({
      title: title.trim(),
      buy_price: parseFloat(buyPrice) || 0,
      buy_shipping: parseFloat(buyShipping) || 0,
      condition: condition || null,
      source_id: sourceId,
      machine_model: prefill?.machine_model ?? null,
    });
    onClose();
    setTitle("");
    setBuyPrice("");
    setBuyShipping("");
    setCondition("");
    setSourceId(null);
  }

  return (
    <Sheet open={open} onClose={onClose} title="Log a purchase">
      <form onSubmit={submit} className="space-y-3">
        <Field label="What is it?">
          <input
            autoFocus
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. HP 24in monitor"
            className={inputCls}
          />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Paid ($)">
            <input inputMode="decimal" value={buyPrice} onChange={(e) => setBuyPrice(e.target.value)} className={inputCls} />
          </Field>
          <Field label="Shipping ($)">
            <input inputMode="decimal" value={buyShipping} onChange={(e) => setBuyShipping(e.target.value)} className={inputCls} />
          </Field>
        </div>
        <Field label="Condition">
          <select value={condition} onChange={(e) => setCondition(e.target.value)} className={inputCls}>
            <option value="">—</option>
            {CONDITIONS.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </Field>
        <Field label="Source">
          <SourcePicker value={sourceId} onChange={setSourceId} />
        </Field>
        {log.error && <p className="text-sm text-red-600">{log.error.message}</p>}
        <button
          type="submit"
          disabled={!title.trim() || log.isPending}
          className="btn-accent w-full disabled:opacity-50"
        >
          {log.isPending ? "Saving…" : "Log purchase"}
        </button>
      </form>
    </Sheet>
  );
}

const inputCls = "glass-field w-full text-sm";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-ink/70">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}
