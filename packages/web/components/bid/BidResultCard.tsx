"use client";

import { useState } from "react";

import { GlassPanel } from "@/components/ui/GlassPanel";
import { Eyebrow, ProgressBar } from "@/components/ui/primitives";
import { money, percent } from "@/lib/format";
import type { BidResult } from "@/lib/types";
import { VerdictBadge } from "./VerdictBadge";

export function BidResultCard({ result }: { result: BidResult }) {
  const [showParts, setShowParts] = useState(false);
  const amber = result.verdict === null;
  const accent = amber ? "warn" : result.verdict === "BUY" ? "profit" : "loss";
  const priced = result.lines.filter((l) => l.unit_price !== null);
  const maxLine = Math.max(1, ...priced.map((l) => l.line_total));

  return (
    <GlassPanel accent={accent} className="p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Eyebrow className="mb-2">Verdict</Eyebrow>
          <VerdictBadge verdict={result.verdict} />
          <div className="mt-2 text-xs text-ink/50">{result.machine}</div>
        </div>
        {!amber && (
          <div className="text-right">
            <div className="text-[10px] uppercase tracking-[0.08em] text-ink/40">Max safe bid</div>
            <div className="mono mt-1 text-2xl font-bold">{money(result.max_bid)}</div>
          </div>
        )}
      </div>

      {amber ? (
        <p className="mt-4 text-sm text-warn">{result.warning}</p>
      ) : (
        <>
          <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Metric label="Total cost" value={money(result.total_cost)} />
            <Metric label="Parts value" value={money(result.parts_value)} />
            <Metric label="Net profit" value={money(result.projection?.net)} tone="profit" />
            <Metric label="ROI" value={percent(result.projection?.roi)} />
          </div>

          <button
            onClick={() => setShowParts((s) => !s)}
            className="mt-5 w-full border-t border-white/[0.07] pt-4 text-left"
          >
            <Eyebrow>
              {showParts ? "▾" : "▸"} Parts breakdown ({result.lines.length})
            </Eyebrow>
          </button>
          {showParts && (
            <div className="mt-4 flex flex-col gap-3">
              {result.lines.map((l) => (
                <div key={l.part_id}>
                  <div className="mb-1.5 flex justify-between text-[13px]">
                    <span className="text-ink/80">
                      {l.name} <span className="text-ink/40">×{l.qty}</span>
                    </span>
                    <span className={`mono font-semibold ${l.unit_price === null ? "text-warn" : ""}`}>
                      {l.unit_price === null ? "no price" : money(l.line_total)}
                    </span>
                  </div>
                  {l.unit_price !== null && <ProgressBar pct={(l.line_total / maxLine) * 100} />}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </GlassPanel>
  );
}

function Metric({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "profit";
}) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-[0.08em] text-ink/40">{label}</div>
      <div className={`mono mt-1 text-base font-semibold ${tone === "profit" ? "text-profit" : ""}`}>
        {value}
      </div>
    </div>
  );
}
