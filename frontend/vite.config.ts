import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiBase = process.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  define: {
    __APP_API_BASE__: JSON.stringify(apiBase),
  },
  test: {
    environment: "jsdom",
  },
});

