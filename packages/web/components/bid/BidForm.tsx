"use client";

import { useState } from "react";

import { LogPurchaseSheet } from "@/components/inventory/LogPurchaseSheet";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { Eyebrow } from "@/components/ui/primitives";
import { ApiError } from "@/lib/api";
import { useBid, useMachines } from "@/lib/queries";
import { BidResultCard } from "./BidResultCard";

export function BidForm() {
  const [machine, setMachine] = useState("");
  const [price, setPrice] = useState("");
  const [shipping, setShipping] = useState("");
  const [logging, setLogging] = useState(false);
  const bid = useBid();
  const machines = useMachines(machine);

  const suggestions =
    machines.data?.items.filter((m) => m.toLowerCase() !== machine.toLowerCase()).slice(0, 6) ?? [];

  function submit(e: React.FormEvent) {
    e.preventDefault();
    bid.mutate({
      machine: machine.trim(),
      price: parseFloat(price) || 0,
      shipping: parseFloat(shipping) || 0,
    });
  }

  // A 422 with an "ambiguous" message carries suggestions in the text.
  const err = bid.error instanceof ApiError ? bid.error : null;

  return (
    <div className="space-y-5">
      <div className="grid gap-5 md:grid-cols-2 md:items-start">
        {/* New assessment */}
        <GlassPanel className="p-6">
          <Eyebrow className="mb-4">New Assessment</Eyebrow>
          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs text-ink/55">Machine / Lot</label>
              <input
                value={machine}
                onChange={(e) => setMachine(e.target.value)}
                placeholder="OptiPlex 7080"
                className="glass-field w-full text-sm font-medium"
                autoComplete="off"
              />
              {suggestions.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {suggestions.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setMachine(s)}
                      className="!min-h-0 rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs text-ink/70 transition-colors hover:bg-white/[0.08]"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs text-ink/55">Asking Price</label>
                <div className="glass-field flex items-center gap-1.5 !py-2.5">
                  <span className="mono text-2xl text-ink/40">$</span>
                  <input
                    inputMode="decimal"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    placeholder="55"
                    className="mono !min-h-0 w-full border-0 bg-transparent p-0 text-2xl font-semibold outline-none"
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs text-ink/55">Shipping</label>
                <div className="glass-field flex items-center gap-1.5 !py-2.5">
                  <span className="mono text-2xl text-ink/40">$</span>
                  <input
                    inputMode="decimal"
                    value={shipping}
                    onChange={(e) => setShipping(e.target.value)}
                    placeholder="30"
                    className="mono !min-h-0 w-full border-0 bg-transparent p-0 text-2xl font-semibold outline-none"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={!machine.trim() || bid.isPending}
              className="btn-accent w-full disabled:opacity-50"
            >
              {bid.isPending ? "Calculating…" : "Calculate Verdict"}
            </button>
          </form>
        </GlassPanel>

        {/* Verdict */}
        <div>
          {bid.isPending && (
            <div className="h-full min-h-[220px] animate-pulse rounded-2xl border border-white/[0.06] bg-white/[0.04]" />
          )}

          {err && !bid.isPending && (
            <GlassPanel accent="loss" className="p-6">
              <Eyebrow className="mb-2 !text-loss/70">Verdict</Eyebrow>
              <p className="text-sm text-loss">{err.message}</p>
              <button onClick={() => bid.reset()} className="btn-ghost mt-4">
                Dismiss
              </button>
            </GlassPanel>
          )}

          {bid.data && !bid.isPending && <BidResultCard result={bid.data} />}

          {!bid.data && !bid.isPending && !err && (
            <GlassPanel className="flex min-h-[220px] flex-col items-center justify-center p-6 text-center">
              <Eyebrow className="mb-2">Verdict</Eyebrow>
              <p className="text-sm text-ink/40">
                Enter a machine and price, then calculate to see the call.
              </p>
            </GlassPanel>
          )}
        </div>
      </div>

      {bid.data && bid.data.verdict === "BUY" && !bid.isPending && (
        <button onClick={() => setLogging(true)} className="btn-ghost w-full !text-accent">
          ＋ Log this purchase
        </button>
      )}

      {bid.data && (
        <LogPurchaseSheet
          key={`${bid.data.machine}:${price}`}
          open={logging}
          onClose={() => setLogging(false)}
          prefill={{
            title: bid.data.machine,
            buy_price: parseFloat(price) || 0,
            machine_model: bid.data.machine,
          }}
        />
      )}
    </div>
  );
}
