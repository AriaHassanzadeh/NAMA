const backendOrigin = (process.env.BACKEND_ORIGIN ?? "http://127.0.0.1:8000").replace(/\/$/, "");
const nextConfig = {
  output: "standalone",
  trailingSlash: true,
  allowedDevOrigins: ["localhost", "127.0.0.1"],
  async rewrites() {
    return [
      { source: "/api/v1/static/:path*", destination: `${backendOrigin}/api/v1/static/:path*` },
      { source: "/api/v1/:path*/", destination: `${backendOrigin}/api/v1/:path*/` },
    ];
  },
};
export default nextConfig;
