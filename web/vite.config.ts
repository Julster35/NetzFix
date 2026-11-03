import { defineConfig } from "vite";

// Dev: `npm run dev` (port 5173) proxies /api to the Python server (`uv run netzfix serve`).
export default defineConfig({
  server: { proxy: { "/api": "http://127.0.0.1:8765" } },
  build: { outDir: "dist", chunkSizeWarningLimit: 2500 },
});
