import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

const resolvePath = (value) => path.resolve(__dirname, value);

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      { find: /^zustand$/, replacement: resolvePath("./src/store/zustandCompat.js") },
      { find: "@app", replacement: resolvePath("./src/app") },
      { find: "@layout", replacement: resolvePath("./src/layout") },
      { find: "@renderer", replacement: resolvePath("./src/renderer") },
      { find: "@ui", replacement: resolvePath("./src/ui") },
      { find: "@analytics", replacement: resolvePath("./src/analytics") },
      { find: "@events", replacement: resolvePath("./src/events") },
      { find: "@detector", replacement: resolvePath("./src/detector") },
      { find: "@timeline", replacement: resolvePath("./src/timeline") },
      { find: "@config", replacement: resolvePath("./src/config") },
      { find: "@debug", replacement: resolvePath("./src/debug") },
      { find: "@assets", replacement: resolvePath("./src/assets") },
      { find: "@collaboration", replacement: resolvePath("./src/collaboration") },
      { find: "@experiments", replacement: resolvePath("./src/experiments") },
      { find: "@store", replacement: resolvePath("./src/store") },
      { find: "@services", replacement: resolvePath("./src/services") }
    ]
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: "dist",
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ["react", "react-dom", "zustand"],
          render: ["three", "@react-three/fiber"],
          analytics: ["d3"]
        }
      }
    }
  }
});
