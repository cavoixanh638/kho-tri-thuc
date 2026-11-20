// Keep isolated native-browser harnesses opt-in; discover every DOM/unit suite.
import { spawnSync } from 'node:child_process';
import { readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const suites = readdirSync(new URL('./', import.meta.url))
  .filter((name) => name.endsWith('.test.mjs') && !name.endsWith('-browser.test.mjs'))
  .sort()
  .map((name) => path.join('tests', name));
if (!suites.length) throw new Error('No frontend unit suites discovered');
console.log(`Frontend unit suites (${suites.length}): ${suites.join(', ')}`);
// Separate processes keep each suite's JSDOM, fetch and fake clock isolated.
// Sequential files also avoid concurrent Vite dependency cache writes.
const result = spawnSync(process.execPath, ['--test', '--test-concurrency=1', ...suites], {
  cwd: root, stdio: 'inherit', env: process.env,
});
if (result.error) throw result.error;
process.exit(result.status ?? 1);
