// Run only from storage.test_viewer_browser: actual Django session/API, generated WAV/VP8.
import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { createServer } from 'vite';
const { Browser } = await import(pathToFileURL(process.env.KT116_CDP_HELPER).href);
const cases = JSON.parse(process.env.KT116_CASES);
assert.equal(cases.length, 2);
const out = path.resolve(process.env.KT116_EVIDENCE_DIR ?? '../../tmp/kt116-private-browser');
mkdirSync(out, { recursive: true });
let server, browser;
const report = { scope: 'Actual Django session-authenticated viewer API, injected synthetic StoragePort; no Drive traffic', audio: [], video: [], ranges: [], tolerance_seconds: 1, production_drive: 'NOT_RUN', pdf_page_navigation: 'NOT_RUN', android: 'NOT_RUN' };
try {
  server = await createServer({ server: { host: '127.0.0.1', port: 0, proxy: { '/api': { target: process.env.KT116_API, changeOrigin: false } } }, logLevel: 'error' });
  await server.listen(); const origin = server.resolvedUrls.local[0].replace(/\/$/, '');
  browser = await Browser.launch({ width: 1440, height: 1000 });
  report.browser = (await browser.send('Browser.getVersion')).product;
  const page = await browser.newPage({ width: 1440, height: 1000 });
  await page.goto(origin + '/tests/kt116-private-browser.html', { settleMs: 500 });
  const loggedIn = await page.eval(async () => {
    const session = await fetch('/api/v1/session').then(response => response.json());
    return (await fetch('/api/v1/session', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': session.csrf_token }, body: JSON.stringify({ username: 'kt-viewer-synthetic', password: 'qa-viewer-only' }) })).status;
  });
  assert.equal(loggedIn, 200);
  const marks = [0, .125, .5, 1, 1.25, 2.5, 3, 4.125, 5, 6.5, 7.75, 8, 9.5, 10.25, 11, 12.5, 14, 16.25, 18, 20];
  for (const fixture of cases) {
    const content = `/api/v1/assets/${fixture.assetId}/content/1/${fixture.version}`;
    assert.equal((await fetch(origin + content)).status, 401, 'actual API rejects absent session');
    for (const range of ['bytes=0-31', 'bytes=0-', `bytes=${fixture.size - 100}-`]) {
      const result = await page.eval(async ({ content, range }) => {
        const response = await fetch(content, { headers: { Range: range } });
        return { status: response.status, range: response.headers.get('Content-Range'), size: (await response.arrayBuffer()).byteLength };
      }, { content, range });
      assert.equal(result.status, 206); assert.ok(result.size <= 4 * 1024 * 1024);
      report.ranges.push({ mime: fixture.mime, requested: range, ...result });
    }
    for (const seconds of fixture.mime.startsWith('audio') ? [...marks, 24, 26, 28] : marks) {
      await page.eval(({ fixture, seconds }) => window.ktPrivateViewer.render(fixture, seconds), { fixture, seconds });
      await page.eval(`new Promise((resolve, reject) => { const end = Date.now() + 8000; const poll = () => { const button = [...document.querySelectorAll('button')].find(button => button.textContent === 'Mở và định vị nguồn riêng tư'); if (button) { button.click(); resolve(); } else if (Date.now() > end) reject(new Error('missing private action')); else setTimeout(poll, 20); }; poll(); })`);
      const result = await page.eval(`new Promise((resolve, reject) => { const end = Date.now() + 10000; const poll = () => { const media = document.querySelector('audio,video'); const status = document.querySelector('.source-locator-viewer [role=status]')?.textContent; if (media && status?.startsWith('Đã đến')) resolve({ actual: media.currentTime, duration: media.duration, tag: media.tagName, width: media.videoWidth ?? null, height: media.videoHeight ?? null, url: new URL(media.src).pathname, status }); else if (Date.now() > end) reject(new Error(status || document.querySelector('[role=alert]')?.textContent || 'media load timeout')); else setTimeout(poll, 25); }; poll(); })`);
      assert.ok(Math.abs(result.actual - seconds) <= 1); assert.equal(result.url, content);
      if (fixture.mime.startsWith('video')) { assert.equal(result.width, 320); assert.equal(result.height, 180); }
      report[fixture.mime.startsWith('video') ? 'video' : 'audio'].push({ target: seconds, ...result });
    }
  }
  for (const width of [1440, 768, 390]) {
    await page.setViewport({ width, height: width === 390 ? 844 : 1000 });
    const dimensions = await page.eval('({ width: innerWidth, scroll: document.documentElement.scrollWidth })');
    assert.ok(dimensions.scroll <= width);
    await page.screenshot({ path: path.join(out, `viewer-${width}.png`), format: 'png' });
  }
  assert.equal(page.consoleErrors.length, 0, page.consoleErrors.join('\n'));
  report.max_error_seconds = Math.max(...report.audio.concat(report.video).map(row => Math.abs(row.target - row.actual)));
  writeFileSync(path.join(out, 'results.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ browser: report.browser, audio: report.audio.length, video: report.video.length, max_error_seconds: report.max_error_seconds, ranges: report.ranges.length, out }));
} finally { await browser?.close(); await server?.close(); }
