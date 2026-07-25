"use client";

import { useState } from "react";

import { GlassPanel } from "@/components/ui/GlassPanel";
import { Eyebrow, PageHeader } from "@/components/ui/primitives";
import { money } from "@/lib/format";
import { useCompare, useScrap, useWhatIf } from "@/lib/queries";

function Verdict({ v }: { v: "BUY" | "PASS" | null }) {
  if (!v) return null;
  return (
    <span className={`mono font-bold ${v === "BUY" ? "text-profit" : "text-loss"}`}>{v}</span>
  );
}

const inputCls = "glass-field w-full text-sm";

export default function ToolsPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <PageHeader
        title="Calculators"
        subtitle="Bid-engine tools: model a sale, evaluate a scrap lot, and compare lots side by side."
      />
      <WhatIfTool />
      <ScrapTool />
      <CompareTool />
    </div>
  );
}

function WhatIfTool() {
  const whatif = useWhatIf();
  const [machine, setMachine] = useState("");
  const [buyPrice, setBuyPrice] = useState("");
  const [discount, setDiscount] = useState("");
  const r = whatif.data;
  return (
    <GlassPanel className="space-y-3 p-5">
      <Eyebrow>What-if — model a sale</Eyebrow>
      <input className={inputCls} value={machine} onChange={(e) => setMachine(e.target.value)} placeholder="Machine (e.g. OptiPlex 7080)" />
      <div className="flex gap-2">
        <input className={`${inputCls} mono`} value={buyPrice} onChange={(e) => setBuyPrice(e.target.value)} inputMode="decimal" placeholder="Buy price $" />
        <input className={`${inputCls} mono`} value={discount} onChange={(e) => setDiscount(e.target.value)} inputMode="decimal" placeholder="Sell discount %" />
      </div>
      <button
        onClick={() =>
          machine &&
          whatif.mutate({ machine, buy_price: Number(buyPrice || 0), sell_discount: discount ? Number(discount) : undefined })
        }
        disabled={whatif.isPending || !machine}
        className="btn-accent w-full disabled:opacity-50"
      >
        {whatif.isPending ? "…" : "Run what-if"}
      </button>
      {whatif.isError && <p className="text-xs text-loss">{whatif.error.message}</p>}
      {r && (
        <div className="text-sm">
          {r.warning ? (
            <p className="text-warn">{r.warning}</p>
          ) : (
            <div className="grid grid-cols-2 gap-1">
              <span className="text-ink/50">Verdict</span>
              <span className="text-right"><Verdict v={r.verdict} /></span>
              <span className="text-ink/50">Parts value</span>
              <span className="mono text-right">{money(r.parts_value)}</span>
              <span className="text-ink/50">Adjusted max bid</span>
              <span className="mono text-right font-semibold">{money(r.adjusted_max_bid)}</span>
              <span className="text-ink/50">Baseline max bid</span>
              <span className="mono text-right">{money(r.baseline_max_bid)}</span>
            </div>
          )}
        </div>
      )}
    </GlassPanel>
  );
}

function ScrapTool() {
  const scrap = useScrap();
  const [count, setCount] = useState("");
  const [price, setPrice] = useState("");
  const [pct, setPct] = useState("");
  const r = scrap.data;
  return (
    <GlassPanel className="space-y-3 p-5">
      <Eyebrow>Scrap lot — bulk untested units</Eyebrow>
      <div className="flex gap-2">
        <input className={`${inputCls} mono`} value={count} onChange={(e) => setCount(e.target.value)} inputMode="numeric" placeholder="# units" />
        <input className={`${inputCls} mono`} value={price} onChange={(e) => setPrice(e.target.value)} inputMode="decimal" placeholder="Lot price $" />
        <input className={`${inputCls} mono`} value={pct} onChange={(e) => setPct(e.target.value)} inputMode="decimal" placeholder="% working" />
      </div>
      <button
        onClick={() =>
          count && price && scrap.mutate({ count: Number(count), price: Number(price), expected_working_pct: pct ? Number(pct) : undefined })
        }
        disabled={scrap.isPending || !count || !price}
        className="btn-accent w-full disabled:opacity-50"
      >
        {scrap.isPending ? "…" : "Evaluate scrap lot"}
      </button>
      {scrap.isError && <p className="text-xs text-loss">{scrap.error.message}</p>}
      {r && (
        <div className="grid grid-cols-2 gap-1 text-sm">
          <span className="text-ink/50">Verdict</span>
          <span className="text-right"><Verdict v={r.verdict} /></span>
          <span className="text-ink/50">Expected working</span>
          <span className="mono text-right">{r.expected_working}</span>
          <span className="text-ink/50">Expected value</span>
          <span className="mono text-right">{money(r.expected_value)}</span>
          <span className="text-ink/50">Max bid</span>
          <span className="mono text-right font-semibold">{money(r.max_bid)}</span>
        </div>
      )}
    </GlassPanel>
  );
}

function CompareTool() {
  const compare = useCompare();
  const [text, setText] = useState("");
  const parse = () =>
    text
      .split("\n")
      .map((l) => l.split(","))
      .filter((p) => p[0]?.trim() && p[1])
      .map((p) => ({ name: p[0].trim(), price: Number(p[1]), shipping: p[2] ? Number(p[2]) : 0 }));
  const r = compare.data;
  return (
    <GlassPanel className="space-y-3 p-5">
      <Eyebrow>Compare lots</Eyebrow>
      <textarea
        className={`${inputCls} h-24`}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={"One lot per line: name, price, shipping\ne.g.\nLot A, 120, 15\nLot B, 90, 25"}
      />
      <button
        onClick={() => {
          const lots = parse();
          if (lots.length) compare.mutate({ lots });
        }}
        disabled={compare.isPending}
        className="btn-accent w-full disabled:opacity-50"
      >
        {compare.isPending ? "…" : "Compare"}
      </button>
      {compare.isError && <p className="text-xs text-loss">{compare.error.message}</p>}
      {r && (
        <div className="space-y-1 text-sm">
          {r.ranked.map((lot, i) => (
            <div key={lot.name + i} className="flex justify-between">
              <span className={i === 0 ? "font-semibold text-profit" : ""}>
                {i + 1}. {lot.name}
              </span>
              <span className="mono">{money(lot.total)}</span>
            </div>
          ))}
        </div>
      )}
    </GlassPanel>
  );
}
