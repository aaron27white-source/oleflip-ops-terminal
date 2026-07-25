import type { Config } from "tailwindcss";

export default {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Glass Logistics Terminal palette
        surface: "#0a0d13",
        ink: "#eef1f6",
        accent: { DEFAULT: "#4f8cff", cyan: "#6fd3ff" },
        profit: { DEFAULT: "#6df0b8", dim: "#3ddc97" },
        loss: { DEFAULT: "#ff8f8f", dim: "#ff6b6b" },
        warn: "#ffcd80",
        // legacy aliases still referenced in a few places
        buy: "#6df0b8",
        pass: "#ff8f8f",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "IBM Plex Mono", "monospace"],
      },
      boxShadow: {
        panel: "0 24px 48px -28px rgba(0,0,0,0.7), inset 0 1px 0 rgba(255,255,255,0.06)",
        tile: "0 16px 32px -24px rgba(0,0,0,0.6)",
      },
      keyframes: {
        oleflipPulse: { "0%,100%": { opacity: "1" }, "50%": { opacity: "0.35" } },
      },
      animation: { pulseDot: "oleflipPulse 1.8s ease-in-out infinite" },
    },
  },
  plugins: [],
} satisfies Config;
