"use client";

import { useState } from "react";

import { ErrorState, LoadingSkeleton } from "@/components/common/states";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { Eyebrow, LiveDot, PageHeader } from "@/components/ui/primitives";
import { registerPush } from "@/lib/push";
import {
  useNotificationLog,
  useNotificationPrefs,
  useSendTestNotification,
  useUpdateNotificationPref,
} from "@/lib/queries";
import type { NotificationPref } from "@/lib/types";

const EVENT_META: Record<string, { label: string; icon: string; note?: string }> = {
  deal_found: { label: "High-value deals", icon: "🔥", note: "BUY verdicts over the headroom threshold" },
  deal_escalated: { label: "Big deals (escalated)", icon: "🚀", note: "$150+ headroom" },
  inventory_stale: { label: "Aging inventory", icon: "⚠️", note: "items held 60+ days" },
  daily_brief: { label: "Daily brief", icon: "📋", note: "8 AM summary" },
  agent_failure: { label: "Agent failures", icon: "🚨" },
  system: { label: "System", icon: "🔔" },
};

const CHANNEL_LABEL: Record<string, string> = {
  discord: "💬 Discord",
  slack: "🟣 Slack",
  push: "📱 Push",
};

const CHANNEL_HINT: Record<string, string> = {
  discord: "set DISCORD_WEBHOOK_URL in .env",
  slack: "set SLACK_WEBHOOK_URL in .env",
  push: "set VAPID keys in .env",
};

export default function SettingsPage() {
  const prefs = useNotificationPrefs();
  const update = useUpdateNotificationPref();
  const test = useSendTestNotification();
  const log = useNotificationLog();
  const [pushMsg, setPushMsg] = useState<string | null>(null);

  if (prefs.isLoading) return <LoadingSkeleton rows={5} />;
  if (prefs.isError || !prefs.data)
    return <ErrorState message="Couldn't load settings." onRetry={() => prefs.refetch()} />;

  const channels = prefs.data.channels;
  const grouped = new Map<string, NotificationPref[]>();
  for (const p of prefs.data.items) {
    (grouped.get(p.event_type) ?? grouped.set(p.event_type, []).get(p.event_type)!).push(p);
  }

  const enablePush = async () => {
    setPushMsg("Requesting…");
    try {
      const r = await registerPush(prefs.data!.vapid_public_key);
      setPushMsg(
        {
          ok: "Push enabled on this device ✓",
          unsupported: "This browser doesn't support push.",
          denied: "Notification permission denied.",
          "no-key": "Server has no VAPID key set (see .env).",
        }[r],
      );
    } catch (e) {
      setPushMsg("Failed: " + (e as Error).message);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <PageHeader title="Notifications" subtitle="Get pinged when something matters — instead of checking the app." />

      {/* Integration status */}
      <GlassPanel className="p-6">
        <Eyebrow className="mb-4">Integration Status</Eyebrow>
        <div className="space-y-2 text-sm">
          {Object.entries(channels).map(([name, ok]) => (
            <StatusRow
              key={name}
              ok={ok}
              label={CHANNEL_LABEL[name] ?? name}
              hint={ok ? "connected" : (CHANNEL_HINT[name] ?? "not configured")}
            />
          ))}
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button onClick={enablePush} className="btn-ghost !py-2 !text-xs" disabled={!channels.push}>
            Enable push on this device
          </button>
          <button
            onClick={() => test.mutate(Object.keys(channels))}
            disabled={test.isPending}
            className="btn-accent !py-2 !text-xs disabled:opacity-50"
          >
            {test.isPending ? "Sending…" : "📨 Send test"}
          </button>
          {pushMsg && <span className="text-xs text-ink/60">{pushMsg}</span>}
          {test.data && (
            <span className="mono text-xs text-ink/60">
              {Object.entries(test.data.results).map(([c, ok]) => `${c}:${ok ? "✓" : "✕"}`).join("  ")}
            </span>
          )}
        </div>
      </GlassPanel>

      {/* Per-event channel toggles */}
      {[...grouped.entries()].map(([event, ps]) => {
        const meta = EVENT_META[event] ?? { label: event, icon: "🔔" };
        return (
          <GlassPanel key={event} className="p-6">
            <div className="mb-3 flex items-baseline justify-between gap-3">
              <div className="font-semibold">
                {meta.icon} {meta.label}
              </div>
              {meta.note && <span className="text-xs text-ink/40">{meta.note}</span>}
            </div>
            <div className="flex flex-wrap gap-2">
              {ps.map((p) => (
                <button
                  key={p.channel}
                  onClick={() =>
                    update.mutate({ event_type: p.event_type, channel: p.channel, enabled: p.enabled === 0 })
                  }
                  className={`!min-h-0 rounded-full border px-3.5 py-1.5 text-sm transition-colors ${
                    p.enabled
                      ? "border-accent/40 bg-accent/[0.16] text-ink"
                      : "border-white/10 bg-white/[0.03] text-ink/50"
                  }`}
                >
                  {CHANNEL_LABEL[p.channel] ?? p.channel} {p.enabled ? "on" : "off"}
                  {p.min_headroom != null && p.enabled ? ` · ≥$${p.min_headroom}` : ""}
                </button>
              ))}
            </div>
          </GlassPanel>
        );
      })}

      {/* Recent deliveries */}
      <GlassPanel className="p-6">
        <Eyebrow className="mb-4">Recent Deliveries</Eyebrow>
        {(log.data?.items.length ?? 0) === 0 ? (
          <p className="text-sm text-ink/40">Nothing sent yet.</p>
        ) : (
          <div className="space-y-1.5">
            {log.data!.items.slice(0, 20).map((e) => (
              <div key={e.id} className="flex items-center justify-between gap-2 text-xs">
                <span className="min-w-0 truncate text-ink/70">
                  <span className={e.success ? "text-profit" : "text-loss"}>{e.success ? "✓" : "✕"}</span>{" "}
                  {e.title || e.event_type}{" "}
                  <span className="text-ink/40">· {e.channel}</span>
                </span>
                <span className="mono shrink-0 text-ink/30">{e.created_at?.slice(5, 16)}</span>
              </div>
            ))}
          </div>
        )}
      </GlassPanel>
    </div>
  );
}

function StatusRow({ ok, label, hint }: { ok: boolean; label: string; hint: string }) {
  return (
    <div className="flex items-center gap-2">
      <LiveDot color={ok ? "#3ddc97" : "rgba(238,241,246,0.3)"} pulse={false} />
      <span className="text-ink/80">{label}</span>
      <span className="text-xs text-ink/40">— {hint}</span>
    </div>
  );
}
