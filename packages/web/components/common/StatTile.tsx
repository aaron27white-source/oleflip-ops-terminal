/** Glass KPI tile — mono value, uppercase label, optional profit/loss accent. */
export function StatTile({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "good" | "bad";
}) {
  const good = tone === "good";
  const bad = tone === "bad";
  const valueCls = good ? "text-profit" : bad ? "text-loss" : "text-ink";
  const tileCls = good
    ? "glass-tile !border-profit-dim/25 [background:linear-gradient(180deg,rgba(61,220,151,0.12),rgba(255,255,255,0.02))]"
    : "glass-tile";
  return (
    <div className={`${tileCls} p-[18px]`}>
      <div className="text-[11px] uppercase tracking-[0.08em] text-ink/45">{label}</div>
      <div className={`mono mt-1.5 text-2xl font-bold ${valueCls}`}>{value}</div>
    </div>
  );
}
