"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { StatTile } from "@/components/common/StatTile";
import { ErrorState, LoadingSkeleton } from "@/components/common/states";
import { LogCallSheet } from "@/components/itad/LogCallSheet";
import { LogItadPurchaseSheet } from "@/components/itad/LogItadPurchaseSheet";
import { Stars, StatusBadge } from "@/components/itad/StatusBadge";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { Eyebrow } from "@/components/ui/primitives";
import {
  useDeleteCall,
  useDeletePurchase,
  useDeleteSupplier,
  useSupplier,
  useUpdateSupplier,
} from "@/lib/queries";
import { money, percent } from "@/lib/format";
import type { ItadStatus } from "@/lib/types";

const STATUS_OPTIONS: ItadStatus[] = ["not-contacted", "contacted", "active", "dead"];

export default function SupplierDetail() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);
  const q = useSupplier(id);
  const update = useUpdateSupplier(id);
  const delSupplier = useDeleteSupplier();
  const delCall = useDeleteCall();
  const delPurchase = useDeletePurchase();
  const [logging, setLogging] = useState(false);
  const [buying, setBuying] = useState(false);

  if (q.isLoading) return <LoadingSkeleton rows={5} />;
  if (q.isError || !q.data)
    return <ErrorState message="Couldn't load this supplier." onRetry={() => q.refetch()} />;

  const { company: c, calls, purchases } = q.data;

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <Link href="/suppliers" className="text-sm text-accent">
        ← Suppliers
      </Link>

      <div className="flex items-start justify-between gap-2">
        <div>
          <h1 className="text-[22px] font-bold">{c.name}</h1>
          <p className="text-sm text-ink/50">
            {c.city}, {c.state}
            {c.phone ? ` · ${c.phone}` : ""}
            {c.contact_person ? ` · ${c.contact_person}` : ""}
          </p>
        </div>
        <Stars n={c.reliability} />
      </div>

      <div className="flex items-center gap-2">
        <StatusBadge status={c.status} />
        <select
          value={c.status}
          onChange={(e) => update.mutate({ status: e.target.value })}
          className="glass-field !min-h-0 !py-1.5 text-xs"
        >
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        {c.sells_singles ? <span className="text-xs text-profit">sells singles</span> : null}
      </div>

      {(c.typical_bare_price != null || c.typical_loaded_price != null) && (
        <div className="grid grid-cols-2 gap-4">
          <StatTile label="Bare price" value={money(c.typical_bare_price)} />
          <StatTile label="Loaded price" value={money(c.typical_loaded_price)} />
        </div>
      )}

      <div className="grid grid-cols-3 gap-4">
        <StatTile label="Spent" value={money(c.total_spent)} />
        <StatTile label="Units" value={String(c.total_units)} />
        <StatTile label="Win rate" value={percent(c.win_rate_pct)} />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <button onClick={() => setLogging(true)} className="btn-accent">
          ＋ Log call
        </button>
        <button onClick={() => setBuying(true)} className="btn-ghost !text-profit">
          ＋ Log purchase
        </button>
      </div>

      {/* Call log timeline */}
      <GlassPanel className="p-6">
        <Eyebrow className="mb-4">Call log ({c.call_count})</Eyebrow>
        {calls.length === 0 ? (
          <p className="text-sm text-ink/40">No calls yet.</p>
        ) : (
          <div className="space-y-2">
            {calls.map((call) => (
              <div key={call.id} className="rounded-xl border border-white/[0.07] bg-white/[0.03] p-3">
                <div className="flex justify-between text-xs text-ink/50">
                  <span>
                    {call.call_date}
                    {call.spoke_with ? ` · ${call.spoke_with}` : ""}
                  </span>
                  <span className="flex items-center gap-2">
                    {call.has_inventory ? <span className="text-profit">had inventory</span> : null}
                    <button
                      onClick={() => {
                        if (confirm("Delete this call log?"))
                          delCall.mutate({ companyId: id, callId: call.id });
                      }}
                      className="!min-h-0 text-ink/40 hover:text-loss"
                      aria-label="delete call"
                    >
                      ✕
                    </button>
                  </span>
                </div>
                <p className="mt-1 text-sm">{call.notes}</p>
                {call.pricing_text && <p className="mt-1 text-xs text-ink/50">💵 {call.pricing_text}</p>}
                {call.follow_up && <p className="mt-1 text-xs text-warn">↩ {call.follow_up}</p>}
              </div>
            ))}
          </div>
        )}
      </GlassPanel>

      {/* Purchase history */}
      <GlassPanel className="p-6">
        <Eyebrow className="mb-4">Purchases ({c.purchase_count})</Eyebrow>
        {purchases.length === 0 ? (
          <p className="text-sm text-ink/40">No purchases logged.</p>
        ) : (
          <div className="space-y-1.5">
            {purchases.map((p) => (
              <div key={p.id} className="flex items-center justify-between gap-2 text-sm">
                <span className="min-w-0 truncate text-ink/70">
                  {p.purchase_date} · {p.quantity}× {p.model || "units"} @ {money(p.unit_price)}
                  {p.working_count != null ? ` · ${p.working_count} worked` : ""}
                </span>
                <span className="flex shrink-0 items-center gap-2">
                  <span className="mono font-medium">{money(p.total_cost)}</span>
                  <button
                    onClick={() => {
                      if (confirm("Delete this purchase?"))
                        delPurchase.mutate({ companyId: id, purchaseId: p.id });
                    }}
                    className="!min-h-0 text-ink/40 hover:text-loss"
                    aria-label="delete purchase"
                  >
                    ✕
                  </button>
                </span>
              </div>
            ))}
          </div>
        )}
      </GlassPanel>

      {c.notes && (
        <p className="rounded-xl border border-white/[0.07] bg-white/[0.03] p-3 text-sm text-ink/70">
          {c.notes}
        </p>
      )}

      <button
        onClick={() => {
          if (confirm(`Delete supplier "${c.name}" and all its logs? This can't be undone.`)) {
            delSupplier.mutate(id, { onSuccess: () => router.push("/suppliers") });
          }
        }}
        className="w-full rounded-xl border border-loss/30 py-2.5 text-sm font-medium text-loss"
      >
        Delete supplier
      </button>

      <LogCallSheet companyId={id} open={logging} onClose={() => setLogging(false)} />
      <LogItadPurchaseSheet companyId={id} open={buying} onClose={() => setBuying(false)} />
    </div>
  );
}
