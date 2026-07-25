"use client";

import { useState } from "react";

import { Sheet } from "@/components/common/Sheet";
import { useLogCall } from "@/lib/queries";

const inputCls = "glass-field w-full text-sm";

export function LogCallSheet({ companyId, open, onClose }: { companyId: number; open: boolean; onClose: () => void }) {
  const log = useLogCall(companyId);
  const [spokeWith, setSpokeWith] = useState("");
  const [notes, setNotes] = useState("");
  const [hasInventory, setHasInventory] = useState(false);
  const [pricing, setPricing] = useState("");
  const [followUp, setFollowUp] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    await log.mutateAsync({
      spoke_with: spokeWith || null, notes: notes.trim(),
      has_inventory: hasInventory, pricing_text: pricing || null, follow_up: followUp || null,
    });
    onClose();
    setSpokeWith(""); setNotes(""); setHasInventory(false); setPricing(""); setFollowUp("");
  }

  return (
    <Sheet open={open} onClose={onClose} title="Log a call">
      <form onSubmit={submit} className="space-y-3">
        <input value={spokeWith} onChange={(e) => setSpokeWith(e.target.value)} placeholder="Spoke with (name)" className={inputCls} />
        <textarea autoFocus value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="What was said…" className={inputCls} rows={3} />
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={hasInventory} onChange={(e) => setHasInventory(e.target.checked)} />
          They have inventory right now
        </label>
        <input value={pricing} onChange={(e) => setPricing(e.target.value)} placeholder='Pricing (e.g. "$50 bare, no SSD")' className={inputCls} />
        <input value={followUp} onChange={(e) => setFollowUp(e.target.value)} placeholder="Follow-up (e.g. call back next month)" className={inputCls} />
        {log.error && <p className="text-sm text-red-600">{log.error.message}</p>}
        <button type="submit" disabled={!notes.trim() || log.isPending}
          className="btn-accent w-full disabled:opacity-50">
          {log.isPending ? "Saving…" : "Log call"}
        </button>
      </form>
    </Sheet>
  );
}
