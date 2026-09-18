/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@bhoomi/ui', '@bhoomi/api-client', '@bhoomi/map', '@bhoomi/types'],
};

module.exports = nextConfig;
