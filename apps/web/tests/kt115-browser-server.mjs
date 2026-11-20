import { build, preview } from 'vite';
import react from '@vitejs/plugin-react';
import { execFileSync } from 'node:child_process';
const baseline = { name: 'kt115-fixed-baseline', enforce: 'pre', load(id) {
  if (process.env.KT115_BASELINE && id.replaceAll('\\', '/').endsWith('/src/ItemScreen.tsx'))
    return execFileSync('git', ['show', '7044b4a0f50a7c831a391f27b1f90cc4aaa21d8b:apps/web/src/ItemScreen.tsx'], { encoding: 'utf8' });
} };
await build({ configFile: false, plugins: [baseline, react()], build: { outDir: 'tmp/kt115-browser', emptyOutDir: true, rolldownOptions: { input: 'tests/kt115-browser.html' } } });
if (!process.env.KT115_BUILD_ONLY) {
  const server = await preview({ configFile: false, build: { outDir: 'tmp/kt115-browser' }, preview: { host: '127.0.0.1', port: Number(process.env.KT115_PORT ?? 62115), strictPort: true } });
  server.printUrls();
}
