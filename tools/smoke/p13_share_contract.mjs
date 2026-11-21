#!/usr/bin/env node
/** P13 standalone Android/PWA Share Target contract and IME readiness checks.
 * Source/fixture checks are not a real Android or browser acceptance test.
 */
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const read = p => readFileSync(resolve(root, p), 'utf8');
const manifest = JSON.parse(read('apps/web/public/manifest.webmanifest'));
const fixture = JSON.parse(read('apps/backend/ingestion/fixtures/kt117-fixtures.json'));
const share = read('apps/web/src/sharedCapture.ts');
const screen = read('apps/web/src/CaptureScreen.tsx');
const tests = read('apps/web/tests/kt117-capture.test.mjs');
const checks = [];
function check(id, assertion, note) {
  try { assertion(); checks.push({ id, status: 'SOURCE_PASS', note }); }
  catch (error) { checks.push({ id, status: 'SOURCE_FAIL', note, reason: String(error.message).slice(0, 170) }); }
}
check('manifest-get-target', () => {
  assert.equal(manifest.share_target?.method, 'GET');
  assert.equal(manifest.share_target?.action, '/');
  assert.deepEqual(manifest.share_target?.params, {
    title: 'shared_title', text: 'shared_text', url: 'shared_url',
  });
}, 'PWA share targets map title/text/url; native file share is not supported by this GET manifest');
check('pwa-start', () => {
  assert.equal(manifest.start_url, '/#/gui'); assert.equal(manifest.display, 'standalone');
}, 'Start route and PWA display');
check('30-fixtures', () => {
  assert.equal(fixture.length, 30);
  assert.equal(new Set(fixture.map(x=>x.name)).size, 30);
  for (const [i, row] of fixture.entries()) {
    assert.ok(row.params && typeof row.params === 'object', `params missing at ${i}`);
    assert.ok(['link','text'].includes(row.kind));
    assert.equal(typeof row.raw, 'string');
    assert.equal(typeof row.url, 'string');
    assert.ok(Object.keys(row.params).every(k=>['shared_title','shared_text','shared_url'].includes(k)));
  }
  for(const name of ['unicode-combining','emoji-cjk','crlf','multiple-urls','credentials','javascript-url','youtube-title','tiktok','long-query'])
    assert.ok(fixture.some(x=>x.name===name), name);
}, 'Thirty synthetic Vietnamese/Unicode/URL/share fixtures exist and are unique');
check('share-safe-parse', () => {
  assert.match(share, /export function readSharedCapture/);
  assert.match(share, /captureHttpUrl\(/);
  assert.match(share, /!url\.username && !url\.password/);
  assert.match(share, /export function saveCaptureDraft/);
  assert.match(share, /export function readCaptureDraft/);
}, 'Share parses URL defensively and keeps owner-scoped tab-memory draft');
check('receipt-not-upload', () => {
  assert.match(screen, /if \(inFlight\.current\) return/);
  assert.match(screen, /idempotencyKey: attempt\.current\.key/);
  assert.match(screen, /idempotencyKey: fileAttempt\.current\.key/);
  assert.match(screen, /Chưa xác nhận tệp đã được lưu và kiểm tra trên Drive/);
}, 'Client does not confuse acknowledgement with verified storage');
check('auth-network-retry', () => {
  assert.match(tests, /failure \$\{failure\} retains draft and retry key/);
  assert.match(tests, /actual App 401 unmount\/login path/);
  assert.match(tests, /file retry retains File\/key/);
  assert.match(tests, /30-share-corpus/);
}, 'Existing KT117 dynamic tests exercise retry/login/30-share cases');
check('ime-regression-contract', () => {
  assert.match(screen, /<Textarea label="Nội dung tri thức \(Markdown\)"/);
  assert.match(screen, /onChange=\{\(event\) => \{ clearAttempt\(\); setNote\(event\.currentTarget\.value\); \}\}/);
  assert.match(screen, /Array\.from\(text\)\.length > 65_536/);
}, 'Controlled textarea receives input value and retains Unicode; native IME still NOT_RUN');
check('responsive-ui-source', () => {
  const css=read('apps/web/src/capture.css');
  assert.ok(css.includes('@media'), 'capture CSS has no responsive media query');
  assert.ok(css.includes('capture-compose'));
}, 'Responsive CSS exists; 390/768 physical viewport acceptance NOT_RUN');
const report = {
  task:'P13',mode:'SOURCE_CONTRACT_ONLY',base:'coord/notes-parallel-20261121-frozen',
  checks, source_pass:checks.filter(x=>x.status==='SOURCE_PASS').length,
  source_fail:checks.filter(x=>x.status==='SOURCE_FAIL').length,
  simulated_browser:'NOT_RUN', android_physical:'NOT_RUN', ime_unikey_evkey:'NOT_RUN',
  real_postgres_api:'NOT_RUN', real_share_file_target:'UNSUPPORTED_MANIFEST_GET',
  conclusion:'Source checks only; run P13 isolated API probe, existing kt117 DOM suites and Android manual gate separately.',
};
const out=resolve(root,process.env.P13_OUT || 'tmp/p13-source-contract.json');
mkdirSync(dirname(out),{recursive:true});writeFileSync(out,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({ checks: checks.length, pass: report.source_pass, fail: report.source_fail, out, status: report.source_fail?'SOURCE_FAIL':'SOURCE_PASS' }));
if(report.source_fail)process.exitCode=1;
