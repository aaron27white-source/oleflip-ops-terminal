import type { ReactNode } from "react";

/** Frosted glass surface — the core panel of the terminal. */
export function GlassPanel({
  children,
  className = "",
  accent,
  as: Tag = "div",
}: {
  children: ReactNode;
  className?: string;
  /** Optional tinted accent border/background (profit / loss / warn). */
  accent?: "profit" | "loss" | "warn";
  as?: "div" | "section" | "article";
}) {
  const accentCls =
    accent === "profit"
      ? "!border-profit-dim/30 [background:linear-gradient(180deg,rgba(61,220,151,0.12),rgba(255,255,255,0.02))]"
      : accent === "loss"
        ? "!border-loss/30 [background:linear-gradient(180deg,rgba(255,107,107,0.12),rgba(255,255,255,0.02))]"
        : accent === "warn"
          ? "!border-warn/30 [background:linear-gradient(180deg,rgba(255,182,72,0.1),rgba(255,255,255,0.02))]"
          : "";
  return <Tag className={`glass-panel ${accentCls} ${className}`}>{children}</Tag>;
}
