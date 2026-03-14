import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

const resolvePath = (value) => path.resolve(__dirname, value);

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@app": resolvePath("./src/app"),
      "@layout": resolvePath("./src/layout"),
      "@renderer": resolvePath("./src/renderer"),
      "@ui": resolvePath("./src/ui"),
      "@analytics": resolvePath("./src/analytics"),
      "@events": resolvePath("./src/events"),
      "@detector": resolvePath("./src/detector"),
      "@timeline": resolvePath("./src/timeline"),
      "@config": resolvePath("./src/config"),
      "@debug": resolvePath("./src/debug"),
      "@assets": resolvePath("./src/assets"),
      "@collaboration": resolvePath("./src/collaboration"),
      "@experiments": resolvePath("./src/experiments"),
      "@store": resolvePath("./src/store"),
      "@services": resolvePath("./src/services")
    }
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
