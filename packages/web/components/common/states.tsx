export function LoadingSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="mt-4 space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-16 animate-pulse rounded-2xl border border-white/[0.06] bg-white/[0.04]" />
      ))}
    </div>
  );
}

export function EmptyState({ title, action }: { title: string; action?: React.ReactNode }) {
  return (
    <div className="mt-6 rounded-2xl border border-dashed border-white/10 bg-white/[0.015] py-12 text-center">
      <p className="text-sm text-ink/50">{title}</p>
      {action && <div className="mt-3 flex justify-center">{action}</div>}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="mt-4 rounded-2xl border border-loss/30 bg-loss/[0.08] p-4 text-sm">
      <p className="font-medium text-loss">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-2 rounded-lg border border-loss/40 px-3 py-1 text-loss"
        >
          Retry
        </button>
      )}
    </div>
  );
}
