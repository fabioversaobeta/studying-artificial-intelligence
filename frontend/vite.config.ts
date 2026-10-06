import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

// The browser always calls the API on the page's own origin (/api/...), so the
// HttpOnly refresh cookie is first-party: this proxy does it in dev and `vite
// preview`, the Vercel rewrite in vercel.json does it in production.
const apiProxy = {
  '/api': { target: process.env.API_PROXY_TARGET ?? 'http://127.0.0.1:8000', changeOrigin: false },
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: apiProxy,
  },
  preview: {
    port: 4173,
    proxy: apiProxy,
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    restoreMocks: true,
    // Hermetic: a developer's local .env (VITE_API_URL) must not change what the tests assert.
    env: { VITE_API_URL: '' },
  },
})
