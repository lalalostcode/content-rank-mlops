import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api/v1': process.env.DASHBOARD_API_TARGET ?? 'http://127.0.0.1:8080',
    },
  },
})
