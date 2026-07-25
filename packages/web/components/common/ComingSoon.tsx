export function ComingSoon({ title, milestone }: { title: string; milestone: string }) {
  return (
    <div className="py-16 text-center">
      <h1 className="text-xl font-bold">{title}</h1>
      <p className="mt-2 text-sm text-neutral-500">
        The backend for this is built and tested. The screen lands in {milestone}.
      </p>
    </div>
  );
}
