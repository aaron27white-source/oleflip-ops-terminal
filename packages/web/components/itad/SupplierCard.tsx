import Link from "next/link";

import { GlassPanel } from "@/components/ui/GlassPanel";
import { money } from "@/lib/format";
import type { ItadCompany } from "@/lib/types";
import { Stars, StatusBadge } from "./StatusBadge";

export function SupplierCard({ c }: { c: ItadCompany }) {
  const stats = [
    c.avg_unit_price != null ? `${money(c.avg_unit_price)} avg` : null,
    c.total_units ? `${c.total_units} units` : null,
    c.call_count ? `${c.call_count} call${c.call_count > 1 ? "s" : ""}` : null,
  ].filter(Boolean);

  return (
    <Link href={`/suppliers/${c.id}`} className="block">
      <GlassPanel className="p-4 transition-transform hover:-translate-y-0.5">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <div className="truncate font-medium">{c.name}</div>
            <div className="text-xs text-ink/50">
              {c.city}, {c.state}
              {c.phone ? ` · ${c.phone}` : ""}
            </div>
          </div>
          <StatusBadge status={c.status} />
        </div>
        <div className="mono mt-2.5 flex items-center justify-between text-xs text-ink/50">
          <span>{stats.length ? stats.join(" · ") : "no activity yet"}</span>
          <Stars n={c.reliability} />
        </div>
      </GlassPanel>
    </Link>
  );
}
