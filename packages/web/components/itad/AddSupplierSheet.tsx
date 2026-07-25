"use client";

import { useState } from "react";

import { Sheet } from "@/components/common/Sheet";
import { useCreateSupplier } from "@/lib/queries";

const inputCls = "glass-field w-full text-sm";

export function AddSupplierSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const create = useCreateSupplier();
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [city, setCity] = useState("Houston");
  const [notes, setNotes] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    await create.mutateAsync({ name: name.trim(), phone: phone || null, city: city.trim() || "Houston", notes: notes || null });
    onClose();
    setName(""); setPhone(""); setCity("Houston"); setNotes("");
  }

  return (
    <Sheet open={open} onClose={onClose} title="Add supplier">
      <form onSubmit={submit} className="space-y-3">
        <input autoFocus value={name} onChange={(e) => setName(e.target.value)} placeholder="Company name" className={inputCls} />
        <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="Phone" className={inputCls} inputMode="tel" />
        <input value={city} onChange={(e) => setCity(e.target.value)} placeholder="City" className={inputCls} />
        <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Notes" className={inputCls} rows={2} />
        {create.error && <p className="text-sm text-red-600">{create.error.message}</p>}
        <button type="submit" disabled={!name.trim() || create.isPending}
          className="btn-accent w-full disabled:opacity-50">
          {create.isPending ? "Saving…" : "Add supplier"}
        </button>
      </form>
    </Sheet>
  );
}
