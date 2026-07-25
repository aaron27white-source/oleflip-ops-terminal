"use client";

import { useEffect, useRef, useState } from "react";

import { ErrorState } from "@/components/common/states";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { Eyebrow, PageHeader } from "@/components/ui/primitives";
import { money } from "@/lib/format";
import { useDeleteInventory, useVoiceLog } from "@/lib/queries";
import type { InventoryItem } from "@/lib/types";

// Minimal shape of the Web Speech API (not in the DOM lib types).
interface SpeechRecognitionLike {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onend: (() => void) | null;
  onerror: (() => void) | null;
}

function getRecognition(): SpeechRecognitionLike | null {
  if (typeof window === "undefined") return null;
  const Ctor =
    (window as unknown as { SpeechRecognition?: new () => SpeechRecognitionLike }).SpeechRecognition ||
    (window as unknown as { webkitSpeechRecognition?: new () => SpeechRecognitionLike })
      .webkitSpeechRecognition;
  return Ctor ? new Ctor() : null;
}

export default function VoicePage() {
  const voiceLog = useVoiceLog();
  const del = useDeleteInventory();
  const [text, setText] = useState("");
  const [listening, setListening] = useState(false);
  const [logged, setLogged] = useState<InventoryItem[]>([]);
  const [supported, setSupported] = useState(true);
  const recogRef = useRef<SpeechRecognitionLike | null>(null);

  useEffect(() => {
    const r = getRecognition();
    if (!r) {
      setSupported(false);
      return;
    }
    r.lang = "en-US";
    r.continuous = false;
    r.interimResults = false;
    r.onresult = (e) => {
      const said = e.results[0]?.[0]?.transcript ?? "";
      setText(said);
      if (said.trim()) submit(said);
    };
    r.onend = () => setListening(false);
    r.onerror = () => setListening(false);
    recogRef.current = r;
    return () => r.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleMic = () => {
    const r = recogRef.current;
    if (!r) return;
    if (listening) {
      r.stop();
      setListening(false);
    } else {
      setText("");
      voiceLog.reset();
      r.start();
      setListening(true);
    }
  };

  function submit(transcript: string) {
    const t = transcript.trim();
    if (!t) return;
    voiceLog.mutate(t, {
      onSuccess: (res) => {
        setLogged((prev) => [...res.items, ...prev].slice(0, 20));
        setText("");
      },
    });
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader
        title="Voice Log"
        subtitle="Standing at a pallet? Say what you bought — it lands in inventory."
      />

      <GlassPanel className="flex flex-col items-center gap-5 p-8">
        {supported ? (
          <button
            onClick={toggleMic}
            aria-label={listening ? "Stop" : "Speak"}
            className={`flex h-32 w-32 items-center justify-center rounded-full border text-4xl transition-transform ${
              listening
                ? "animate-pulseDot border-accent/50 bg-accent/20 text-accent"
                : "border-white/10 bg-white/[0.05] text-ink/80 hover:-translate-y-0.5"
            }`}
          >
            🎙️
          </button>
        ) : (
          <p className="text-center text-sm text-ink/50">
            Voice input isn&apos;t supported in this browser — use the text box below (works
            everywhere).
          </p>
        )}
        <div className="text-center text-sm text-ink/55">
          {listening ? "Listening… tap to stop" : supported ? "Tap to speak" : ""}
        </div>

        <div className="flex w-full items-center gap-2">
          <div className="h-px flex-1 bg-white/10" />
          <span className="eyebrow">or type it</span>
          <div className="h-px flex-1 bg-white/10" />
        </div>

        <form
          className="flex w-full gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            submit(text);
          }}
        >
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Dell Optiplex 7080, 45 bucks, two of them"
            className="glass-field w-full text-sm"
          />
          <button
            type="submit"
            disabled={voiceLog.isPending || !text.trim()}
            className="btn-accent shrink-0 disabled:opacity-50"
          >
            {voiceLog.isPending ? "Logging…" : "Log It"}
          </button>
        </form>

        {voiceLog.isError && <ErrorState message={voiceLog.error.message} />}
      </GlassPanel>

      {logged.length > 0 && (
        <GlassPanel className="p-6">
          <Eyebrow className="mb-4">Just logged ({logged.length})</Eyebrow>
          <div className="space-y-2">
            {logged.map((it) => (
              <div
                key={it.id}
                className="flex items-center justify-between gap-2 rounded-xl border border-profit-dim/20 bg-profit/[0.06] p-3"
              >
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium">{it.title}</div>
                  <div className="mono text-xs text-ink/50">
                    {money(it.buy_price)}
                    {it.machine_model ? ` · ${it.machine_model}` : ""}
                  </div>
                </div>
                <span className="flex shrink-0 items-center gap-2">
                  <span className="text-profit">✓</span>
                  <button
                    onClick={() => {
                      del.mutate(it.id);
                      setLogged((prev) => prev.filter((x) => x.id !== it.id));
                    }}
                    className="!min-h-0 text-xs text-ink/40 hover:text-loss"
                    aria-label="remove"
                  >
                    ✕
                  </button>
                </span>
              </div>
            ))}
          </div>
          <p className="mt-3 text-xs text-ink/40">
            Wrong parse? Remove it here, or fine-tune the item on the Inventory screen.
          </p>
        </GlassPanel>
      )}
    </div>
  );
}
