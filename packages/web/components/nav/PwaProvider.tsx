"use client";

import { useEffect, useState } from "react";

// Minimal BeforeInstallPromptEvent typing (not in lib.dom yet).
interface BIPEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: string }>;
}

/** Registers the service worker, shows an offline banner and an install prompt. */
export function PwaProvider() {
  const [offline, setOffline] = useState(false);
  const [installEvt, setInstallEvt] = useState<BIPEvent | null>(null);

  useEffect(() => {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js").catch(() => {});
    }
    const on = () => setOffline(!navigator.onLine);
    on();
    window.addEventListener("online", on);
    window.addEventListener("offline", on);

    const onInstall = (e: Event) => {
      e.preventDefault();
      setInstallEvt(e as BIPEvent);
    };
    window.addEventListener("beforeinstallprompt", onInstall);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", on);
      window.removeEventListener("beforeinstallprompt", onInstall);
    };
  }, []);

  return (
    <>
      {offline && (
        <div className="fixed inset-x-0 top-0 z-30 bg-amber-500 py-1 text-center text-xs font-medium text-white">
          Offline — cached data shown; changes will wait.
        </div>
      )}
      {installEvt && (
        <button
          onClick={async () => {
            await installEvt.prompt();
            setInstallEvt(null);
          }}
          className="fixed bottom-20 right-4 z-30 rounded-full bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-lg"
        >
          ＋ Install app
        </button>
      )}
    </>
  );
}
