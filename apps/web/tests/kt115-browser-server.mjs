import { build, preview } from 'vite';
import react from '@vitejs/plugin-react';
await build({ configFile: false, plugins: [react()], build: { outDir: 'tmp/kt115-browser', emptyOutDir: true, rolldownOptions: { input: 'tests/kt115-browser.html' } } });
const server = await preview({ configFile: false, build: { outDir: 'tmp/kt115-browser' }, preview: { host: '127.0.0.1', port: Number(process.env.KT115_PORT ?? 62115), strictPort: true } });
server.printUrls();
