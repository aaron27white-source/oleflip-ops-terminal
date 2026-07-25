"use client";

import { useState } from "react";

import { Sheet } from "@/components/common/Sheet";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/common/states";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { Eyebrow, PageHeader } from "@/components/ui/primitives";
import { useCreateLead, useDeleteLead, useLeads, useUpdateLead } from "@/lib/queries";
import type { Lead } from "@/lib/types";

// ITAD companies live in the dedicated Suppliers CRM (/suppliers), not here.
const KINDS = [
  { value: "university", label: "University surplus" },
  { value: "fb_search", label: "FB searches" },
  { value: "govdeals_search", label: "GovDeals searches" },
  { value: "other", label: "Other" },
];

export default function LeadsPage() {
  const leads = useLeads();
  const create = useCreateLead();
  const update = useUpdateLead();
  const del = useDeleteLead();
  const [adding, setAdding] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [kind, setKind] = useState("university");
  const [name, setName] = useState("");
  const [contact, setContact] = useState("");
  const [location, setLocation] = useState("");

  const reset = () => {
    setName("");
    setContact("");
    setLocation("");
    setKind("university");
    setEditId(null);
  };

  const openAdd = () => {
    reset();
    setAdding(true);
  };
  const openEdit = (l: Lead) => {
    setEditId(l.id);
    setKind(l.kind);
    setName(l.name);
    setContact(l.contact ?? "");
    setLocation(l.location ?? "");
    setAdding(true);
  };

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const data = { kind, name: name.trim(), contact, location };
    if (editId) await update.mutateAsync({ id: editId, data });
    else await create.mutateAsync(data);
    setAdding(false);
    reset();
  }

  const saving = create.isPending || update.isPending;

  const grouped = KINDS.map((k) => ({
    ...k,
    items: leads.data?.items.filter((l) => l.kind === k.value) ?? [],
  })).filter((g) => g.items.length > 0);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader
        title="Sourcing Leads"
        subtitle="University surplus schedules, saved searches, and other leads to chase."
        action={
          <button onClick={openAdd} className="btn-accent">
            ＋ Add lead
          </button>
        }
      />

      {leads.isLoading && <LoadingSkeleton rows={3} />}
      {leads.isError && <ErrorState message="Couldn't load leads." onRetry={() => leads.refetch()} />}
      {leads.data && leads.data.items.length === 0 && (
        <EmptyState title="No leads yet — add surplus schedules and saved searches to chase." />
      )}
      {grouped.map((g) => (
        <GlassPanel key={g.value} className="p-6">
          <Eyebrow className="mb-4">{g.label}</Eyebrow>
          <div className="space-y-2">
            {g.items.map((l) => (
              <div
                key={l.id}
                className="flex items-start justify-between gap-2 rounded-xl border border-white/[0.07] bg-white/[0.03] p-3"
              >
                <button onClick={() => openEdit(l)} className="min-w-0 text-left">
                  <div className="font-medium">{l.name}</div>
                  <div className="mt-0.5 text-xs text-ink/50">
                    {[l.location, l.contact, l.schedule_note].filter(Boolean).join(" · ")}
                  </div>
                </button>
                <button
                  onClick={() => {
                    if (confirm(`Delete lead "${l.name}"?`)) del.mutate(l.id);
                  }}
                  className="!min-h-0 shrink-0 text-xs text-ink/40 hover:text-loss"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </GlassPanel>
      ))}

      <Sheet
        open={adding}
        onClose={() => {
          setAdding(false);
          reset();
        }}
        title={editId ? "Edit lead" : "Add a lead"}
      >
        <form onSubmit={submit} className="space-y-3">
          <select value={kind} onChange={(e) => setKind(e.target.value)} className="glass-field w-full">
            {KINDS.map((k) => (
              <option key={k.value} value={k.value}>
                {k.label}
              </option>
            ))}
          </select>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Name"
            className="glass-field w-full"
            autoFocus
          />
          <input
            value={contact}
            onChange={(e) => setContact(e.target.value)}
            placeholder="Contact (phone/email/URL)"
            className="glass-field w-full"
          />
          <input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Location (e.g. Houston, TX)"
            className="glass-field w-full"
          />
          <button type="submit" disabled={!name.trim() || saving} className="btn-accent w-full disabled:opacity-50">
            {saving ? "Saving…" : editId ? "Save changes" : "Add lead"}
          </button>
        </form>
      </Sheet>
    </div>
  );
}
