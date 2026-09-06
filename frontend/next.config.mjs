/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination:
          process.env.NODE_ENV === 'development'
            ? 'http://127.0.0.1:8000/api/v1/:path*'
            : '/api/index.py',
      },
      {
        source: '/api/backend/:path*',
        destination:
          process.env.NODE_ENV === 'development'
            ? 'http://127.0.0.1:8000/api/v1/:path*'
            : '/api/index.py',
      },
    ];
  },
};

export default nextConfig;
