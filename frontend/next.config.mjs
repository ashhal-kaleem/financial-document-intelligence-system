/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // Local-only proxy. Production calls the configured Render API directly.
    // Do not point production routes at the removed Vercel Python backend.
    return process.env.NODE_ENV === "development"
      ? [
          {
            source: "/api/v1/:path*",
            destination: "http://127.0.0.1:8000/api/v1/:path*",
          },
        ]
      : [];
  },
};
export default nextConfig;
