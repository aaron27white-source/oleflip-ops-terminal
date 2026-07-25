"use client";

import { useState } from "react";

import { Sheet } from "@/components/common/Sheet";
import { useLogItadPurchase } from "@/lib/queries";

const inputCls = "glass-field w-full text-sm";

export function LogItadPurchaseSheet({ companyId, open, onClose }: { companyId: number; open: boolean; onClose: () => void }) {
  const log = useLogItadPurchase(companyId);
  const [model, setModel] = useState("");
  const [qty, setQty] = useState("");
  const [unit, setUnit] = useState("");
  const [working, setWorking] = useState("");
  const [hadRam, setHadRam] = useState(false);
  const [hadStorage, setHadStorage] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    await log.mutateAsync({
      model: model || null,
      quantity: parseInt(qty) || 1,
      unit_price: parseFloat(unit) || 0,
      working_count: working ? parseInt(working) : null,
      had_ram: hadRam, had_storage: hadStorage,
    });
    onClose();
    setModel(""); setQty(""); setUnit(""); setWorking(""); setHadRam(false); setHadStorage(false);
  }

  return (
    <Sheet open={open} onClose={onClose} title="Log a purchase">
      <form onSubmit={submit} className="space-y-3">
        <input autoFocus value={model} onChange={(e) => setModel(e.target.value)} placeholder="Model (e.g. OptiPlex 3060)" className={inputCls} />
        <div className="grid grid-cols-2 gap-3">
          <input value={qty} onChange={(e) => setQty(e.target.value)} placeholder="Qty" inputMode="numeric" className={inputCls} />
          <input value={unit} onChange={(e) => setUnit(e.target.value)} placeholder="$/unit" inputMode="decimal" className={inputCls} />
        </div>
        <input value={working} onChange={(e) => setWorking(e.target.value)} placeholder="How many worked (optional)" inputMode="numeric" className={inputCls} />
        <div className="flex gap-4 text-sm">
          <label className="flex items-center gap-2"><input type="checkbox" checked={hadRam} onChange={(e) => setHadRam(e.target.checked)} /> had RAM</label>
          <label className="flex items-center gap-2"><input type="checkbox" checked={hadStorage} onChange={(e) => setHadStorage(e.target.checked)} /> had storage</label>
        </div>
        {log.error && <p className="text-sm text-red-600">{log.error.message}</p>}
        <button type="submit" disabled={!qty || !unit || log.isPending}
          className="btn-accent w-full disabled:opacity-50">
          {log.isPending ? "Saving…" : "Log purchase"}
        </button>
      </form>
    </Sheet>
  );
}
