import type { Metadata, Viewport } from "next";
import { Inter, IBM_Plex_Mono } from "next/font/google";

import { AppShell } from "@/components/nav/AppShell";
import { PwaProvider } from "@/components/nav/PwaProvider";
import { Providers } from "./providers";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-sans",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Oleflip — Ops Terminal",
  description: "Glass Logistics Terminal — bid calculator, inventory, sourcing, agent ops.",
  manifest: "/manifest.json",
  appleWebApp: { capable: true, title: "OLEFLIP", statusBarStyle: "black-translucent" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#0a0d13",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${plexMono.variable}`}>
      <body>
        <Providers>
          <PwaProvider />
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
