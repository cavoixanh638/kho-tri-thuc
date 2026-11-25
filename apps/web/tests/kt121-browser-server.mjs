import { build, preview } from 'vite';
import react from '@vitejs/plugin-react';
await build({ configFile: false, plugins: [react()], build: { outDir: 'tmp/kt121-browser', emptyOutDir: true, rolldownOptions: { input: 'tests/kt121-browser.html' } } });
if (!process.env.KT121_BUILD_ONLY) {
  const server = await preview({ configFile: false, build: { outDir: 'tmp/kt121-browser' }, preview: { host: '127.0.0.1', port: Number(process.env.KT121_PORT ?? 62221), strictPort: true } });
  server.printUrls();
}
