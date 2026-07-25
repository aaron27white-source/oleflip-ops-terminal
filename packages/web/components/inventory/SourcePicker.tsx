"use client";

import { useState } from "react";

import { useCreateSource, useSources } from "@/lib/queries";

/** Pick an existing source or type a new one (inline-created on the fly). */
export function SourcePicker({
  value,
  onChange,
}: {
  value: number | null;
  onChange: (id: number | null) => void;
}) {
  const sources = useSources();
  const createSource = useCreateSource();
  const [adding, setAdding] = useState(false);
  const [newName, setNewName] = useState("");

  async function add() {
    if (!newName.trim()) return;
    const created = await createSource.mutateAsync({ name: newName.trim(), type: "flea" });
    onChange(created.id);
    setAdding(false);
    setNewName("");
  }

  if (adding) {
    return (
      <div className="flex gap-2">
        <input
          autoFocus
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="New source name"
          className="glass-field flex-1 text-sm"
        />
        <button
          type="button"
          onClick={add}
          disabled={createSource.isPending}
          className="btn-accent !py-2 !text-sm"
        >
          Add
        </button>
        <button type="button" onClick={() => setAdding(false)} className="!min-h-0 text-sm text-ink/50">
          ✕
        </button>
      </div>
    );
  }

  return (
    <div className="flex gap-2">
      <select
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
        className="flex-1 rounded-lg border border-neutral-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900"
      >
        <option value="">— source —</option>
        {sources.data?.items.map((s) => (
          <option key={s.id} value={s.id}>
            {s.name}
          </option>
        ))}
      </select>
      <button
        type="button"
        onClick={() => setAdding(true)}
        className="btn-ghost !py-2 !text-sm"
      >
        + New
      </button>
    </div>
  );
}
