"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { useAgents } from "@/lib/queries";
import { LiveDot } from "@/components/ui/primitives";

type NavItem = { href: string; label: string; icon: string };

const PRIMARY: NavItem[] = [
  { href: "/", label: "Home", icon: "◆" },
  { href: "/bid", label: "Bid Calculator", icon: "▲" },
  { href: "/voice", label: "Voice Log", icon: "🎤" },
  { href: "/inventory", label: "Inventory & P&L", icon: "▣" },
  { href: "/scanner", label: "Scanner", icon: "◉" },
  { href: "/agents", label: "Agent Ops", icon: "✦" },
];

const MORE: NavItem[] = [
  { href: "/watchlist", label: "Watch List & Bids", icon: "★" },
  { href: "/catalog", label: "Parts Catalog", icon: "▤" },
  { href: "/products", label: "Products", icon: "▦" },
  { href: "/profiles", label: "Machine Profiles", icon: "▥" },
  { href: "/tools", label: "Calculators", icon: "∑" },
  { href: "/sources", label: "Sources", icon: "⇄" },
  { href: "/leads", label: "Sourcing Leads", icon: "⌖" },
  { href: "/suppliers", label: "ITAD Suppliers", icon: "☎" },
  { href: "/settings", label: "Notifications", icon: "🔔" },
];

const MOBILE: NavItem[] = [
  { href: "/", label: "Home", icon: "◆" },
  { href: "/bid", label: "Bid", icon: "▲" },
  { href: "/voice", label: "Voice", icon: "🎤" },
  { href: "/inventory", label: "Stock", icon: "▣" },
  { href: "/more", label: "More", icon: "⋯" },
];

function isActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(href + "/");
}

function useClock() {
  const [now, setNow] = useState<string | null>(null);
  useEffect(() => {
    const fmt = () =>
      new Date()
        .toLocaleString("en-US", {
          month: "short",
          day: "2-digit",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
        })
        .toUpperCase()
        .replace(",", "");
    setNow(fmt());
    const id = setInterval(() => setNow(fmt()), 30_000);
    return () => clearInterval(id);
  }, []);
  return now;
}

function ThemeToggle() {
  const [light, setLight] = useState(false);
  useEffect(() => {
    const stored = localStorage.getItem("oleflip-theme");
    if (stored === "light") {
      document.documentElement.setAttribute("data-theme", "light");
      setLight(true);
    }
  }, []);
  const toggle = () => {
    const next = !light;
    setLight(next);
    if (next) {
      document.documentElement.setAttribute("data-theme", "light");
      localStorage.setItem("oleflip-theme", "light");
    } else {
      document.documentElement.removeAttribute("data-theme");
      localStorage.setItem("oleflip-theme", "dark");
    }
  };
  return (
    <button
      onClick={toggle}
      className="!min-h-0 text-ink/55 transition-colors hover:text-ink"
      aria-label="Toggle theme"
      title="Toggle light / dark"
    >
      {light ? "☀" : "☾"}
    </button>
  );
}

function NavLink({ item, idx }: { item: NavItem; idx?: string }) {
  const pathname = usePathname();
  const active = isActive(pathname, item.href);
  return (
    <Link
      href={item.href}
      className={`flex items-center gap-2.5 rounded-[10px] px-3 py-2.5 transition-colors ${
        active
          ? "bg-accent/[0.14] [border-left:3px_solid_rgba(120,170,255,0.5)]"
          : "border-l-[3px] border-transparent hover:bg-white/[0.05]"
      }`}
    >
      {idx && <span className="mono text-[11px] text-ink/40">{idx}</span>}
      <span className="w-4 text-center text-ink/45">{item.icon}</span>
      <span className={`text-[13px] font-semibold ${active ? "text-ink" : "text-ink/60"}`}>
        {item.label}
      </span>
    </Link>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const clock = useClock();
  const agents = useAgents();
  const online = agents.data?.items.filter((a) => a.enabled).length ?? 8;

  return (
    <div className="flex h-[100dvh] flex-col overflow-hidden">
      {/* Top status bar */}
      <header className="flex h-11 shrink-0 items-center justify-between border-b border-white/[0.08] bg-black/30 px-4 md:px-5">
        <div className="mono flex items-center gap-2.5 text-[11px] tracking-[0.06em] text-ink/55 md:text-[12px]">
          <span className="font-semibold text-ink">[ OLEFLIP ]</span>
          <span className="hidden sm:inline">OPS TERMINAL // v2.4</span>
        </div>
        <div className="mono flex items-center gap-3 text-[11px] text-ink/55 md:gap-4 md:text-[12px]">
          <span className="flex items-center gap-1.5">
            <LiveDot />
            <span className="text-profit">LIVE</span>
          </span>
          <span className="hidden md:inline">API KEY · CONNECTED</span>
          {clock && <span className="hidden sm:inline">{clock} CDT</span>}
          <ThemeToggle />
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        {/* Desktop sidebar */}
        <aside className="hidden w-[246px] shrink-0 flex-col gap-5 border-r border-white/[0.08] bg-white/[0.03] p-[18px_14px] backdrop-blur-xl md:flex">
          <div className="px-2">
            <div className="text-[15px] font-bold leading-tight">Oleflip</div>
            <div className="text-[15px] font-bold leading-tight text-accent">Electronics</div>
            <div className="mono mt-1.5 text-[10px] tracking-[0.14em] text-ink/40">
              SOLO OPERATOR CONSOLE
            </div>
          </div>

          <nav className="flex flex-1 flex-col gap-4 overflow-y-auto">
            <div className="flex flex-col gap-0.5">
              {PRIMARY.map((it, i) => (
                <NavLink key={it.href} item={it} idx={String(i + 1).padStart(2, "0")} />
              ))}
            </div>
            <div className="flex flex-col gap-0.5">
              <div className="eyebrow px-3 pb-1">More</div>
              {MORE.map((it) => (
                <NavLink key={it.href} item={it} />
              ))}
            </div>
          </nav>

          <div className="glass-tile p-3">
            <div className="eyebrow mb-1.5">System Status</div>
            <div className="flex items-center gap-1.5 text-[12px] text-ink/75">
              <LiveDot pulse={false} />
              <span>{online} agents online · sync OK</span>
            </div>
          </div>
        </aside>

        {/* Content */}
        <main className="min-w-0 flex-1 overflow-y-auto px-4 pb-24 pt-6 md:px-10 md:pb-14 md:pt-8">
          {children}
        </main>
      </div>

      {/* Mobile bottom nav */}
      <nav className="fixed inset-x-0 bottom-0 z-20 border-t border-white/[0.08] bg-black/40 backdrop-blur-xl md:hidden">
        <ul className="flex">
          {MOBILE.map((it) => (
            <li key={it.href} className="flex-1">
              <MobileTab item={it} />
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}

function MobileTab({ item }: { item: NavItem }) {
  const pathname = usePathname();
  const active = isActive(pathname, item.href);
  return (
    <Link
      href={item.href}
      className={`flex flex-col items-center gap-0.5 py-2.5 text-[11px] ${
        active ? "font-semibold text-accent" : "text-ink/50"
      }`}
    >
      <span className="text-base leading-none">{item.icon}</span>
      {item.label}
    </Link>
  );
}
