"use client";

import "leaflet/dist/leaflet.css";
import L from "leaflet";
import Link from "next/link";
import { MapContainer, Marker, Popup, TileLayer, useMap, useMapEvents } from "react-leaflet";

import type { Bounds } from "@/lib/queries";
import type { ItadCompany } from "@/lib/types";

// Status → pin colour (mirrors the StatusBadge palette). A CSS divIcon avoids
// Leaflet's default-marker image paths, which break under bundlers.
const PIN_COLOR: Record<string, string> = {
  active: "#3ddc97",
  contacted: "#ffcd80",
  "not-contacted": "#8aa0c0",
  dead: "#ff6b6b",
};

function pin(status: string) {
  const color = PIN_COLOR[status] ?? "#8aa0c0";
  return L.divIcon({
    className: "",
    html: `<span style="display:block;width:16px;height:16px;border-radius:50%;
      background:${color};border:2px solid rgba(0,0,0,0.55);
      box-shadow:0 0 0 2px ${color}55,0 1px 4px rgba(0,0,0,0.5)"></span>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
}

function toBounds(map: L.Map): Bounds {
  const b = map.getBounds();
  return { minLat: b.getSouth(), minLng: b.getWest(), maxLat: b.getNorth(), maxLng: b.getEast() };
}

/** Emits the viewport bounds on mount and after every pan/zoom. */
function BoundsWatcher({ onChange }: { onChange: (b: Bounds) => void }) {
  const map = useMap();
  useMapEvents({ moveend: () => onChange(toBounds(map)) });
  // Fire once on mount so the first query has a box.
  if (typeof window !== "undefined") {
    // defer to next tick so the map has laid out
    setTimeout(() => onChange(toBounds(map)), 0);
  }
  return null;
}

export function SupplierMap({
  companies,
  onBoundsChange,
  center = [32.5, -93.5], // AR/LA/TX corridor
  zoom = 6,
}: {
  companies: ItadCompany[];
  onBoundsChange: (b: Bounds) => void;
  center?: [number, number];
  zoom?: number;
}) {
  const pinned = companies.filter((c) => c.latitude != null && c.longitude != null);
  return (
    <MapContainer
      center={center}
      zoom={zoom}
      scrollWheelZoom
      className="h-[520px] w-full overflow-hidden rounded-2xl border border-white/10"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <BoundsWatcher onChange={onBoundsChange} />
      {pinned.map((c) => (
        <Marker key={c.id} position={[c.latitude!, c.longitude!]} icon={pin(c.status)}>
          <Popup>
            <div className="space-y-0.5 text-sm">
              <Link href={`/suppliers/${c.id}`} className="font-semibold text-blue-600 hover:underline">
                {c.name}
              </Link>
              <div className="text-black/60">
                {c.city}, {c.state} · {c.status}
              </div>
              <div className="text-black/60">
                {"★".repeat(c.reliability)}
                {c.phone ? ` · ${c.phone}` : ""}
              </div>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
