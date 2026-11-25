import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

test('without guarded isolated PostgreSQL and QA URL, driver reports NOT_RUN, never false-PASS', () => {
  const tmp = mkdtempSync(join(tmpdir(), 'kt128-p08-safety-'));
  try {
    const env = { ...process.env, KT_JOURNEY_URL: 'https://example.org', KT_JOURNEY_DB_NAME: 'postgres',
      KT_JOURNEY_USER: 'fake', KT_JOURNEY_PASSWORD: 'fake', KT_JOURNEY_ISOLATED: 'YES', KT_JOURNEY_OUT: tmp };
    const driverPath = fileURLToPath(new URL('./knowledge_journeys.mjs', import.meta.url));
    const run = spawnSync(process.execPath, [driverPath], { env, encoding: 'utf8', timeout: 7000 });
    assert.equal(run.status, 2, run.stderr);
    const report = JSON.parse(readFileSync(join(tmp, 'p08-results.json'), 'utf8'));
    assert.equal(report.status, 'NOT_RUN');
    assert.equal(report.metrics.executed, 0);
    assert.equal(report.metrics.pass_rate, null);
    assert.ok(report.journeys.every((j) => j.status === 'NOT_RUN'));
    assert.ok(!JSON.stringify(report).includes('fake'));
  } finally { rmSync(tmp, { recursive: true, force: true }); }
});
