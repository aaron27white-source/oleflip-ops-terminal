import type { ItadStatus } from "@/lib/types";

const MAP: Record<ItadStatus, { label: string; cls: string }> = {
  active: { label: "Active", cls: "bg-profit/15 text-profit" },
  contacted: { label: "Contacted", cls: "bg-warn/15 text-warn" },
  dead: { label: "Dead", cls: "bg-loss/15 text-loss" },
  "not-contacted": { label: "Not contacted", cls: "bg-white/10 text-ink/50" },
};

export function StatusBadge({ status }: { status: ItadStatus }) {
  const { label, cls } = MAP[status];
  return <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${cls}`}>{label}</span>;
}

export function Stars({ n }: { n: number }) {
  return (
    <span className="text-warn" title={`${n}/5`}>
      {"★".repeat(n)}
      <span className="text-white/15">{"★".repeat(5 - n)}</span>
    </span>
  );
}
