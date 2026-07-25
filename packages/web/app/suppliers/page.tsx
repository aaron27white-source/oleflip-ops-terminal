"use client";

import { useState } from "react";

import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/common/states";
import { AddSupplierSheet } from "@/components/itad/AddSupplierSheet";
import { SupplierCard } from "@/components/itad/SupplierCard";
import { PageHeader } from "@/components/ui/primitives";
import { useSuppliers } from "@/lib/queries";
import type { ItadStatus } from "@/lib/types";

const STATUSES: { label: string; value: ItadStatus | "" }[] = [
  { label: "All", value: "" },
  { label: "Active", value: "active" },
  { label: "Contacted", value: "contacted" },
  { label: "Not contacted", value: "not-contacted" },
  { label: "Dead", value: "dead" },
];

export default function SuppliersPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<ItadStatus | "">("");
  const [adding, setAdding] = useState(false);
  const suppliers = useSuppliers(search, "", status);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <PageHeader
        title="ITAD Suppliers"
        subtitle="Who to call, what they charge, and what you've bought."
        action={
          <button onClick={() => setAdding(true)} className="btn-accent">
            ＋ Add supplier
          </button>
        }
      />

      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search suppliers…"
        className="glass-field w-full"
      />

      <div className="flex gap-2 overflow-x-auto pb-1">
        {STATUSES.map((s) => (
          <button
            key={s.value}
            onClick={() => setStatus(s.value)}
            className={`!min-h-0 whitespace-nowrap rounded-full px-3.5 py-1.5 text-sm transition-colors ${
              status === s.value
                ? "bg-accent/[0.16] text-ink [border:1px_solid_rgba(120,170,255,0.4)]"
                : "border border-white/10 bg-white/[0.03] text-ink/60 hover:bg-white/[0.06]"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {suppliers.isLoading && <LoadingSkeleton rows={4} />}
      {suppliers.isError && (
        <ErrorState message="Couldn't load suppliers." onRetry={() => suppliers.refetch()} />
      )}
      {suppliers.data && suppliers.data.items.length === 0 && (
        <EmptyState
          title="No suppliers yet — add the ITAD companies you call."
          action={
            <button onClick={() => setAdding(true)} className="btn-accent">
              ＋ Add supplier
            </button>
          }
        />
      )}
      {suppliers.data && suppliers.data.items.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2">
          {suppliers.data.items.map((c) => (
            <SupplierCard key={c.id} c={c} />
          ))}
        </div>
      )}

      <AddSupplierSheet open={adding} onClose={() => setAdding(false)} />
    </div>
  );
}
