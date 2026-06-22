import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // Racine du monorepo = `externam-hub/` (2 niveaux au-dessus de apps/frontend),
  // pour que la trace du build `standalone` ne remonte pas vers un lockfile parent hors-projet.
  turbopack: {
    root: path.join(__dirname, "..", ".."),
  },
  reactCompiler: true,
  compiler: {
    removeConsole: process.env.NODE_ENV === "production",
  },
  async redirects() {
    return [
      {
        source: "/dashboard",
        destination: "/dashboard/default",
        permanent: false,
      },
    ];
  },
};

export default nextConfig;
