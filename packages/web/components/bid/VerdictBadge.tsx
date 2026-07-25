import type { Verdict } from "@/lib/types";

/** Green BUY / red PASS / amber "needs pricing" (verdict null + warning). */
export function VerdictBadge({ verdict }: { verdict: Verdict }) {
  const map = {
    BUY: { text: "BUY", cls: "bg-profit/15 text-profit border-profit-dim/35" },
    PASS: { text: "PASS", cls: "bg-loss/15 text-loss border-loss/35" },
    NEEDS: { text: "NEEDS PRICING", cls: "bg-warn/15 text-warn border-warn/35" },
  };
  const key = verdict === "BUY" ? "BUY" : verdict === "PASS" ? "PASS" : "NEEDS";
  const { text, cls } = map[key];
  return (
    <span className={`mono inline-block rounded-full border px-4 py-1.5 text-lg font-bold tracking-wide ${cls}`}>
      {text}
    </span>
  );
}
