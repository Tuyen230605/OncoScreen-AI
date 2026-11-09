/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // E2E build riêng (`npm run e2e`) để không ghi đè `.next` của `npm run dev`/`build`.
  ...(process.env.NEXT_DIST_DIR ? { distDir: process.env.NEXT_DIST_DIR } : {}),
};
export default nextConfig;
