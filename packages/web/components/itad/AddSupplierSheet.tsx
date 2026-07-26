"use client";

import { useState } from "react";

import { Sheet } from "@/components/common/Sheet";
import { useCreateSupplier } from "@/lib/queries";

const inputCls = "glass-field w-full text-sm";

export function AddSupplierSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const create = useCreateSupplier();
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [city, setCity] = useState("Houston");
  const [state, setState] = useState("TX");
  const [notes, setNotes] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    await create.mutateAsync({
      name: name.trim(), phone: phone || null, address: address.trim() || null,
      city: city.trim() || "Houston", state: state.trim() || "TX", notes: notes || null,
    });
    onClose();
    setName(""); setPhone(""); setAddress(""); setCity("Houston"); setState("TX"); setNotes("");
  }

  return (
    <Sheet open={open} onClose={onClose} title="Add supplier">
      <form onSubmit={submit} className="space-y-3">
        <input autoFocus value={name} onChange={(e) => setName(e.target.value)} placeholder="Company name" className={inputCls} />
        <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="Phone" className={inputCls} inputMode="tel" />
        <input value={address} onChange={(e) => setAddress(e.target.value)} placeholder="Street address (optional — improves map accuracy)" className={inputCls} />
        <div className="flex gap-3">
          <input value={city} onChange={(e) => setCity(e.target.value)} placeholder="City" className={inputCls} />
          <input value={state} onChange={(e) => setState(e.target.value)} placeholder="State" className={`${inputCls} !w-24`} />
        </div>
        <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Notes" className={inputCls} rows={2} />
        <p className="text-xs text-ink/40">Coordinates are looked up from the address on save (for the map).</p>
        {create.error && <p className="text-sm text-red-600">{create.error.message}</p>}
        <button type="submit" disabled={!name.trim() || create.isPending}
          className="btn-accent w-full disabled:opacity-50">
          {create.isPending ? "Saving…" : "Add supplier"}
        </button>
      </form>
    </Sheet>
  );
}
