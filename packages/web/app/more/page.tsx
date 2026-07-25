import Link from "next/link";

import { GlassPanel } from "@/components/ui/GlassPanel";
import { PageHeader } from "@/components/ui/primitives";

const LINKS = [
  { href: "/agents", title: "✦ Agent Ops", note: "Scan, price, list & audit — LLM agents" },
  { href: "/watchlist", title: "★ Watch List", note: "Tracked listings + bid win rate" },
  { href: "/suppliers", title: "☎ Suppliers (ITAD)", note: "Call logs, pricing, purchases" },
  { href: "/catalog", title: "▤ Part Catalog", note: "Prices & profit by part" },
  { href: "/products", title: "▦ Products", note: "Phones, monitors, laptops — resale ranges" },
  { href: "/profiles", title: "▥ Machine Profiles", note: "Bid-engine machine profiles + specs" },
  { href: "/tools", title: "∑ Calculators", note: "What-if, scrap lot, compare lots" },
  { href: "/sources", title: "⇄ Sources", note: "What makes money" },
  { href: "/leads", title: "⌖ Source Finder", note: "University surplus, saved searches" },
  { href: "/settings", title: "🔔 Notifications", note: "Discord / push alerts, daily brief" },
];

export default function MorePage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader title="More" subtitle="Everything else in the terminal." />
      <div className="grid gap-3 sm:grid-cols-2">
        {LINKS.map((l) => (
          <Link key={l.href} href={l.href}>
            <GlassPanel className="p-4 transition-transform hover:-translate-y-0.5">
              <div className="font-semibold">{l.title}</div>
              <div className="mt-0.5 text-xs text-ink/50">{l.note}</div>
            </GlassPanel>
          </Link>
        ))}
      </div>
    </div>
  );
}
