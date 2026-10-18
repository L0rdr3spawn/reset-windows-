/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Backend-Adresse für den Dev-Proxy (überschreibbar: SM_BACKEND=http://host:port npm run dev)
const backend = process.env.SM_BACKEND ?? 'http://localhost:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: backend, changeOrigin: false },
      '/ical': { target: backend, changeOrigin: false },
    },
  },
  preview: {
    proxy: {
      '/api': { target: backend, changeOrigin: false },
      '/ical': { target: backend, changeOrigin: false },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: false,
    chunkSizeWarningLimit: 900,
  },
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
});
