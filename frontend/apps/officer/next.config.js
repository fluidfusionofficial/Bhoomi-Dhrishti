/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@bhoomi/ui', '@bhoomi/api-client', '@bhoomi/map', '@bhoomi/types'],
  eslint: {
    ignoreDuringBuilds: true,
  },
};

module.exports = nextConfig;
