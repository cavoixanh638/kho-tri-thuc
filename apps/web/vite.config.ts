import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: process.env.API_PROXY_TARGET ?? 'http://127.0.0.1:8000',
        // Django must compare the CSRF Origin against the same Host the browser used.
        changeOrigin: false,
      },
    },
  },
});
