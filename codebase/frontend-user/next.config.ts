import type { NextConfig } from "next";

/** Server-side target for rewrites (Docker: http://backend:8000). */
const backendUrl = (
  process.env.BACKEND_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
