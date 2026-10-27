import type { NextConfig } from 'next';

const nextConfig: NextConfig =
  process.env.TICKET_STATIC_EXPORT === 'true'
    ? { output: 'export', trailingSlash: true, images: { unoptimized: true } }
    : {};

export default nextConfig;
