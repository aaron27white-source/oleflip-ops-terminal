import type { ReactNode } from "react";

/** Mono uppercase eyebrow used above panels / sections. */
export function Eyebrow({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`eyebrow ${className}`}>{children}</div>;
}

/** Page title + optional subtitle, used at the top of each route. */
export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div>
        <h1 className="text-[22px] font-bold leading-tight">{title}</h1>
        {subtitle && <p className="mt-1 text-[13px] text-ink/50">{subtitle}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

/** Thin gradient progress bar (parts breakdown, profit-by-source). */
export function ProgressBar({
  pct,
  tone = "accent",
  height = 5,
}: {
  pct: number;
  tone?: "accent" | "profit";
  height?: number;
}) {
  const fill =
    tone === "profit"
      ? "linear-gradient(90deg,#4f8cff,#3ddc97)"
      : "linear-gradient(90deg,#4f8cff,#6fd3ff)";
  return (
    <div
      className="overflow-hidden rounded-full bg-white/[0.06]"
      style={{ height }}
    >
      <div
        className="h-full rounded-full"
        style={{ width: `${Math.max(0, Math.min(100, pct))}%`, background: fill }}
      />
    </div>
  );
}

/** Pulsing status dot (live / running / idle / error). */
export function LiveDot({ color = "#3ddc97", pulse = true }: { color?: string; pulse?: boolean }) {
  return (
    <span
      className={`inline-block h-1.5 w-1.5 rounded-full ${pulse ? "animate-pulseDot" : ""}`}
      style={{ background: color }}
    />
  );
}
