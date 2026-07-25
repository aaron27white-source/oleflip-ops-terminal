/** @type {import('next').NextConfig} */
const API_BASE = process.env.API_BASE || "http://localhost:8000";

const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  // Dev proxy: browser calls same-origin /api/*, Next forwards to FastAPI.
  // (In prod the Caddy reverse proxy plays this role; a route handler can
  // attach the API key server-side — see BUILD_PLAN §9.)
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${API_BASE}/api/:path*` },
      // Tier 4 — uploaded photos are served by FastAPI's /uploads static mount.
      { source: "/uploads/:path*", destination: `${API_BASE}/uploads/:path*` },
    ];
  },
};

export default nextConfig;
