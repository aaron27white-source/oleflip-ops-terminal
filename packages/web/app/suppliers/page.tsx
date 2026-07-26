"use client";

import dynamic from "next/dynamic";
import { useState } from "react";

import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/common/states";
import { AddSupplierSheet } from "@/components/itad/AddSupplierSheet";
import { SupplierCard } from "@/components/itad/SupplierCard";
import { PageHeader } from "@/components/ui/primitives";
import { useGeocodeMissing, useSuppliers, useSuppliersInBounds, type Bounds } from "@/lib/queries";
import type { ItadStatus } from "@/lib/types";

// Leaflet touches `window`, so the map is client-only (no SSR).
const SupplierMap = dynamic(
  () => import("@/components/itad/SupplierMap").then((m) => m.SupplierMap),
  { ssr: false, loading: () => <LoadingSkeleton rows={6} /> },
);

const STATUSES: { label: string; value: ItadStatus | "" }[] = [
  { label: "All", value: "" },
  { label: "Active", value: "active" },
  { label: "Contacted", value: "contacted" },
  { label: "Not contacted", value: "not-contacted" },
  { label: "Dead", value: "dead" },
];

export default function SuppliersPage() {
  const [view, setView] = useState<"list" | "map">("list");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<ItadStatus | "">("");
  const [adding, setAdding] = useState(false);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <PageHeader
        title="ITAD Suppliers"
        subtitle="Who to call, what they charge, and where they are."
        action={
          <div className="flex items-center gap-2">
            <div className="flex rounded-full border border-white/10 bg-white/[0.03] p-0.5 text-sm">
              {(["list", "map"] as const).map((v) => (
                <button
                  key={v}
                  onClick={() => setView(v)}
                  className={`!min-h-0 rounded-full px-3 py-1 capitalize transition-colors ${
                    view === v ? "bg-accent/[0.18] text-ink" : "text-ink/55 hover:text-ink/80"
                  }`}
                >
                  {v === "map" ? "🗺 Map" : "☰ List"}
                </button>
              ))}
            </div>
            <button onClick={() => setAdding(true)} className="btn-accent">
              ＋ Add supplier
            </button>
          </div>
        }
      />

      {view === "list" ? (
        <ListView search={search} setSearch={setSearch} status={status} setStatus={setStatus} onAdd={() => setAdding(true)} />
      ) : (
        <MapView />
      )}

      <AddSupplierSheet open={adding} onClose={() => setAdding(false)} />
    </div>
  );
}

function ListView({
  search, setSearch, status, setStatus, onAdd,
}: {
  search: string; setSearch: (s: string) => void;
  status: ItadStatus | ""; setStatus: (s: ItadStatus | "") => void;
  onAdd: () => void;
}) {
  const suppliers = useSuppliers(search, "", status);
  return (
    <>
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
          action={<button onClick={onAdd} className="btn-accent">＋ Add supplier</button>}
        />
      )}
      {suppliers.data && suppliers.data.items.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2">
          {suppliers.data.items.map((c) => (
            <SupplierCard key={c.id} c={c} />
          ))}
        </div>
      )}
    </>
  );
}

function MapView() {
  const [bounds, setBounds] = useState<Bounds | null>(null);
  const suppliers = useSuppliersInBounds(bounds);
  const geocode = useGeocodeMissing();
  const items = suppliers.data?.items ?? [];

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-ink/60">
        <span>
          {suppliers.isLoading ? "Loading…" : `${items.length} supplier${items.length === 1 ? "" : "s"} in view`}
          <span className="text-ink/35"> · pan or zoom to search an area</span>
        </span>
        <button
          onClick={() => geocode.mutate()}
          disabled={geocode.isPending}
          className="btn-ghost !py-1.5 !text-xs"
          title="Look up coordinates for suppliers that don't have them yet"
        >
          {geocode.isPending ? "Geocoding…" : "📍 Geocode missing"}
        </button>
      </div>

      {geocode.data && (
        <p className="text-xs text-ink/50">
          Geocoded {geocode.data.geocoded} of {geocode.data.checked} un-located suppliers.
        </p>
      )}

      <SupplierMap companies={items} onBoundsChange={setBounds} />

      <p className="text-xs text-ink/40">
        Suppliers without coordinates don&apos;t appear on the map — add an address (they geocode on
        save) or use <span className="text-ink/60">Geocode missing</span>.
      </p>
    </div>
  );
}
