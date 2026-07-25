"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useRef, useState } from "react";

import { MarkSoldSheet } from "@/components/inventory/MarkSoldSheet";
import { ErrorState, LoadingSkeleton } from "@/components/common/states";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { Eyebrow } from "@/components/ui/primitives";
import { money } from "@/lib/format";
import {
  useDeleteInventory,
  useDeletePhoto,
  useInventoryItem,
  useInventoryPhotos,
  useSetPrimaryPhoto,
  useUploadPhotos,
} from "@/lib/queries";
import type { InventoryPhoto } from "@/lib/types";

const STATUS_META: Record<string, { label: string; cls: string }> = {
  in_stock: { label: "In stock", cls: "bg-accent/15 text-accent" },
  listed: { label: "Listed", cls: "bg-accent-cyan/15 text-accent-cyan" },
  sold: { label: "Sold", cls: "bg-profit/15 text-profit" },
  scrapped: { label: "Scrapped", cls: "bg-warn/15 text-warn" },
};

export default function InventoryDetailPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const router = useRouter();
  const item = useInventoryItem(id);
  const del = useDeleteInventory();
  const [markSold, setMarkSold] = useState(false);

  if (item.isLoading) return <LoadingSkeleton rows={4} />;
  if (item.isError || !item.data)
    return <ErrorState message="Couldn't load this item." onRetry={() => item.refetch()} />;

  const it = item.data;
  const sold = it.status === "sold";
  const meta = STATUS_META[it.status] ?? { label: it.status, cls: "bg-white/10 text-ink/60" };

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <Link href="/inventory" className="text-sm text-accent">
        ← Inventory
      </Link>

      <PhotoGallery itemId={id} />

      <div>
        <h1 className="text-[22px] font-bold">{it.title}</h1>
        <div className="mono mt-1 flex flex-wrap items-center gap-2 text-sm text-ink/60">
          <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${meta.cls}`}>
            {meta.label}
          </span>
          <span>bought {money(it.buy_price + it.buy_shipping)}</span>
          {sold && it.sell_price != null && <span>· sold {money(it.sell_price)}</span>}
          {sold && <span className="text-profit">· net {money(it.net_profit)}</span>}
        </div>
        {it.machine_model && <div className="mt-1 text-xs text-ink/45">{it.machine_model}</div>}
        {it.notes && <p className="mt-3 text-sm text-ink/70">{it.notes}</p>}
      </div>

      <div className="flex gap-2">
        {!sold && (
          <button onClick={() => setMarkSold(true)} className="btn-accent">
            Mark sold
          </button>
        )}
        <button
          onClick={() => {
            if (confirm(`Delete "${it.title}" and its photos?`))
              del.mutate(it.id, { onSuccess: () => router.push("/inventory") });
          }}
          className="btn-ghost !text-loss"
        >
          Delete item
        </button>
      </div>

      <MarkSoldSheet item={it} open={markSold} onClose={() => setMarkSold(false)} />
    </div>
  );
}

function PhotoGallery({ itemId }: { itemId: number }) {
  const photos = useInventoryPhotos(itemId);
  const upload = useUploadPhotos(itemId);
  const del = useDeletePhoto(itemId);
  const setPrimary = useSetPrimaryPhoto(itemId);
  const camRef = useRef<HTMLInputElement>(null);
  const galleryRef = useRef<HTMLInputElement>(null);
  const [zoom, setZoom] = useState<InventoryPhoto | null>(null);

  const onPick = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files ? Array.from(e.target.files).slice(0, 6) : [];
    if (files.length) upload.mutate(files);
    e.target.value = "";
  };

  const items = photos.data?.items ?? [];

  return (
    <GlassPanel className="p-5">
      <div className="mb-4 flex items-center justify-between">
        <Eyebrow>Photos ({items.length})</Eyebrow>
        <div className="flex gap-2">
          <button onClick={() => camRef.current?.click()} className="btn-accent !py-2 !text-xs">
            📷 Take
          </button>
          <button onClick={() => galleryRef.current?.click()} className="btn-ghost !py-2 !text-xs">
            ＋ Add
          </button>
        </div>
      </div>

      {/* camera (mobile: opens rear camera) + gallery picker */}
      <input ref={camRef} type="file" accept="image/*" capture="environment" multiple hidden onChange={onPick} />
      <input ref={galleryRef} type="file" accept="image/*" multiple hidden onChange={onPick} />

      {upload.isPending && <p className="mono mb-3 animate-pulse text-xs text-ink/50">Uploading…</p>}
      {upload.isError && <p className="mb-3 text-xs text-loss">{upload.error.message}</p>}

      {items.length === 0 ? (
        <p className="text-sm text-ink/40">
          No photos yet — snap a few of the item; the first becomes the cover.
        </p>
      ) : (
        <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
          {items.map((p) => (
            <div key={p.id} className="group relative aspect-square overflow-hidden rounded-xl border border-white/10">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={p.url}
                alt=""
                className="h-full w-full cursor-zoom-in object-cover"
                onClick={() => setZoom(p)}
              />
              {p.is_primary === 1 && (
                <span className="mono absolute left-1 top-1 rounded bg-black/60 px-1.5 py-0.5 text-[9px] text-warn">
                  ★ COVER
                </span>
              )}
              <div className="absolute inset-x-0 bottom-0 flex justify-between gap-1 bg-black/50 p-1 opacity-0 transition-opacity group-hover:opacity-100">
                <button
                  onClick={() => setPrimary.mutate(p.id)}
                  disabled={p.is_primary === 1}
                  className="!min-h-0 text-[10px] text-ink/80 disabled:opacity-40"
                >
                  Set cover
                </button>
                <button
                  onClick={() => del.mutate(p.id)}
                  className="!min-h-0 text-[10px] text-loss"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {zoom && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-4"
          onClick={() => setZoom(null)}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={zoom.url} alt="" className="max-h-full max-w-full rounded-lg object-contain" />
        </div>
      )}
    </GlassPanel>
  );
}
