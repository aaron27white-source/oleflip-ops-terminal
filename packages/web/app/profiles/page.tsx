"use client";

import { useState } from "react";

import { ErrorState, LoadingSkeleton } from "@/components/common/states";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { Eyebrow, PageHeader } from "@/components/ui/primitives";
import { money } from "@/lib/format";
import {
  useAllMachines,
  useCreateMachine,
  useDeleteMachine,
  useMachineProfile,
  useUpdateMachine,
} from "@/lib/queries";
import type { MachineProfile } from "@/lib/types";

const BLANK = {
  model: "",
  brand: "",
  standard_ram: "",
  standard_ssd: "",
  standard_cpu: "",
  estimated_total_value: "",
  safe_max_bid: "",
  notes: "",
};

export default function ProfilesPage() {
  const machines = useAllMachines();
  const create = useCreateMachine();
  const [form, setForm] = useState({ ...BLANK });
  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const submit = () => {
    if (!form.model.trim()) return;
    create.mutate(
      {
        model: form.model.trim(),
        brand: form.brand.trim() || "Unknown",
        standard_ram: form.standard_ram.trim() || undefined,
        standard_ssd: form.standard_ssd.trim() || undefined,
        standard_cpu: form.standard_cpu.trim() || undefined,
        estimated_total_value: form.estimated_total_value ? Number(form.estimated_total_value) : undefined,
        safe_max_bid: form.safe_max_bid ? Number(form.safe_max_bid) : undefined,
        notes: form.notes.trim() || undefined,
      },
      { onSuccess: () => setForm({ ...BLANK }) },
    );
  };

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <PageHeader
        title="Machine Profiles"
        subtitle="The bid engine's machine profiles. Editing preserves the parts breakdown."
      />

      <GlassPanel className="p-5">
        <Eyebrow className="mb-3">Add a profile</Eyebrow>
        <input
          value={form.model}
          onChange={(e) => set("model", e.target.value)}
          placeholder="Model (e.g. OptiPlex 7080) — required"
          className="glass-field w-full text-sm"
        />
        <div className="mt-2 grid grid-cols-2 gap-2">
          <input value={form.brand} onChange={(e) => set("brand", e.target.value)} placeholder="Brand" className="glass-field text-sm" />
          <input value={form.standard_cpu} onChange={(e) => set("standard_cpu", e.target.value)} placeholder="CPU" className="glass-field text-sm" />
          <input value={form.standard_ram} onChange={(e) => set("standard_ram", e.target.value)} placeholder="RAM" className="glass-field text-sm" />
          <input value={form.standard_ssd} onChange={(e) => set("standard_ssd", e.target.value)} placeholder="SSD" className="glass-field text-sm" />
          <input value={form.estimated_total_value} onChange={(e) => set("estimated_total_value", e.target.value)} inputMode="decimal" placeholder="Est. value $" className="glass-field mono text-sm" />
          <input value={form.safe_max_bid} onChange={(e) => set("safe_max_bid", e.target.value)} inputMode="decimal" placeholder="Safe max bid $" className="glass-field mono text-sm" />
        </div>
        <button onClick={submit} disabled={create.isPending || !form.model.trim()} className="btn-accent mt-2 w-full disabled:opacity-50">
          {create.isPending ? "Adding…" : "Add profile"}
        </button>
      </GlassPanel>

      {machines.isLoading && <LoadingSkeleton rows={5} />}
      {machines.isError && <ErrorState message={machines.error.message} />}
      <div className="space-y-2">
        {machines.data?.items.map((m) => (
          <MachineRow key={m} model={m} />
        ))}
      </div>
    </div>
  );
}

function MachineRow({ model }: { model: string }) {
  const [open, setOpen] = useState(false);
  return (
    <GlassPanel className="overflow-hidden">
      <button onClick={() => setOpen((v) => !v)} className="flex w-full items-center justify-between p-4 text-left text-sm">
        <span className="truncate font-medium">{model}</span>
        <span className="text-ink/40">{open ? "−" : "edit"}</span>
      </button>
      {open && <MachineEditor model={model} onDone={() => setOpen(false)} />}
    </GlassPanel>
  );
}

function MachineEditor({ model, onDone }: { model: string; onDone: () => void }) {
  const profile = useMachineProfile(model);
  if (profile.isLoading) return <div className="p-4"><LoadingSkeleton rows={2} /></div>;
  if (!profile.data) return <p className="p-4 text-xs text-loss">Could not load profile.</p>;
  return <MachineEditForm profile={profile.data} onDone={onDone} />;
}

function MachineEditForm({ profile, onDone }: { profile: MachineProfile; onDone: () => void }) {
  const update = useUpdateMachine();
  const del = useDeleteMachine();
  const [ram, setRam] = useState(profile.standard_ram ?? "");
  const [ssd, setSsd] = useState(profile.standard_ssd ?? "");
  const [cpu, setCpu] = useState(profile.standard_cpu ?? "");
  const [val, setVal] = useState(profile.estimated_total_value?.toString() ?? "");
  const [bid, setBid] = useState(profile.safe_max_bid?.toString() ?? "");

  const save = () => {
    // Full-replace PUT — echo the whole profile so parts + other fields aren't wiped.
    update.mutate(
      {
        model: profile.model,
        data: {
          model: profile.model,
          brand: profile.brand ?? "Unknown",
          generation: profile.generation ?? undefined,
          standard_ram: ram || undefined,
          standard_ssd: ssd || undefined,
          standard_cpu: cpu || undefined,
          standard_wifi: profile.standard_wifi ?? undefined,
          standard_psu: profile.standard_psu ?? undefined,
          has_cooler: profile.has_cooler === 1,
          estimated_total_value: val ? Number(val) : undefined,
          safe_max_bid: bid ? Number(bid) : undefined,
          notes: profile.notes ?? undefined,
          parts: profile.parts,
        },
      },
      { onSuccess: onDone },
    );
  };

  return (
    <div className="border-t border-white/[0.07] p-4">
      <div className="grid grid-cols-2 gap-2 text-sm">
        <input value={cpu} onChange={(e) => setCpu(e.target.value)} placeholder="CPU" className="glass-field !py-2" />
        <input value={ram} onChange={(e) => setRam(e.target.value)} placeholder="RAM" className="glass-field !py-2" />
        <input value={ssd} onChange={(e) => setSsd(e.target.value)} placeholder="SSD" className="glass-field !py-2" />
        <input value={val} onChange={(e) => setVal(e.target.value)} inputMode="decimal" placeholder="Est. value $" className="glass-field mono !py-2" />
        <input value={bid} onChange={(e) => setBid(e.target.value)} inputMode="decimal" placeholder="Safe max bid $" className="glass-field mono !py-2" />
      </div>
      <div className="mt-1.5 text-xs text-ink/40">{profile.parts.length} part(s) in breakdown (preserved on save)</div>
      <div className="mt-2.5 flex gap-2">
        <button onClick={save} disabled={update.isPending} className="btn-accent !py-2 !text-xs disabled:opacity-50">
          {update.isPending ? "Saving…" : "Save"}
        </button>
        <button
          onClick={() => del.mutate(profile.model, { onSuccess: onDone })}
          className="!min-h-0 rounded-[10px] border border-loss/30 px-3 py-2 text-xs text-loss"
        >
          Delete profile
        </button>
      </div>
      {profile.estimated_total_value != null && (
        <div className="mono mt-1.5 text-xs text-ink/40">current est. {money(profile.estimated_total_value)}</div>
      )}
    </div>
  );
}
