import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/reset": "http://localhost:7860",
      "/step": "http://localhost:7860",
      "/state": "http://localhost:7860",
      "/health": "http://localhost:7860",
      "/api": "http://localhost:7860",
      "/metadata": "http://localhost:7860",
      "/schema": "http://localhost:7860",
    },
  },
  build: {
    outDir: "dist",
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test-setup.js",
  },
});
