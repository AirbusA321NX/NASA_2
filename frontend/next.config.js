/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4004',
  },
  // Allow images from any domain (needed for dynamic image loading from NASA OSDR)
  images: {
    domains: ['*'],
    unoptimized: true,
  },
  // Enable experimental features if needed
  experimental: {
    // Add any experimental features here
  },
}

module.exports = nextConfig