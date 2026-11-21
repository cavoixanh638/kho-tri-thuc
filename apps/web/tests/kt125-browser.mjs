import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { createServer } from 'vite';
const { Browser } = await import(pathToFileURL(process.env.KT125_CDP_HELPER).href);
const { probe, layout, app } = await import(new URL('./probe.mjs', pathToFileURL(process.env.KT125_CDP_HELPER)));
const { judge, judgeLayout, judgeApp, APP_SKIP } = await import(new URL('./rules.mjs', pathToFileURL(process.env.KT125_CDP_HELPER)));
const rows = JSON.parse(process.env.KT125_ROWS);
assert.equal(new URL(process.env.KT125_API).hostname, '127.0.0.1');
assert.notEqual(new URL(process.env.KT125_API).port, '8009');
const out = path.resolve(process.env.KT125_EVIDENCE_DIR ?? '../../tmp/kt125-browser');
mkdirSync(out, { recursive: true });
let server, browser;
const report = { scope: 'Native Chrome + actual Django/PostgreSQL/CSRF; focused component host, no fake fetch', checks: [], sizes: [], production: 'NOT_RUN', android: 'NOT_RUN' };
try {
  server = await createServer({ server: { host: '127.0.0.1', port: 0, proxy: { '/api': { target: process.env.KT125_API, changeOrigin: false } } }, logLevel: 'error' });
  await server.listen(); const origin = server.resolvedUrls.local[0].replace(/\/$/, '');
  browser = await Browser.launch({ width: 1920, height: 1080 });
  report.browser = (await browser.send('Browser.getVersion')).product;
  const page = await browser.newPage({ width: 1920, height: 1080, reducedMotion: true });
  await page.goto(origin + '/tests/kt125-browser.html');
  await page.eval(async () => {
    const session = await fetch('/api/v1/session').then((response) => response.json());
    const response = await fetch('/api/v1/session', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': session.csrf_token }, body: JSON.stringify({ username: 'collection-browser', password: 'synthetic-collections-only' }) });
    if (!response.ok) throw new Error('QA login failed');
  });
  await page.send('Page.reload', { ignoreCache: true });
  const wait = async (predicate, arg) => {
    for (let index = 0; index < 100; index++) { if (await page.eval(predicate, arg)) return; await new Promise((done) => setTimeout(done, 50)); }
    throw new Error('Condition timed out: ' + predicate.toString());
  };
  const click = async (label) => { await wait((label) => [...document.querySelectorAll('button')].some((button) => button.textContent === label && !button.disabled), label); await page.eval((label) => [...document.querySelectorAll('button')].find((button) => button.textContent === label).click(), label); };
  const choose = async (label, value) => page.eval(({ label, value }) => {
    const select = [...document.querySelectorAll('label')].find((entry) => entry.textContent.startsWith(label)).querySelector('select');
    select.value = value; select.dispatchEvent(new Event('change', { bubbles: true }));
  }, { label, value });
  await wait(() => !!document.querySelector('.saved-collection-form input'));
  await page.eval(() => document.querySelector('.saved-collection-form input').focus());
  await page.send('Input.insertText', { text: 'Ghi chú yêu thích Tiếng Việt' });
  await choose('Yêu thích', 'true'); await choose('Cách xem mặc định', 'table');
  await click('Xem trước kết quả');
  await wait(() => document.querySelector('[aria-label="Kết quả xem trước"]')?.textContent.includes('3 bài khớp'));
  const beforeSave = await page.eval(async () => (await fetch('/api/v1/collections').then((r) => r.json())).results.length);
  assert.equal(beforeSave, 0);
  // Native Enter on the submit button, exercising keyboard form submission.
  await page.eval(() => [...document.querySelectorAll('button')].find((button) => button.textContent === 'Lưu bộ sưu tập').focus());
  await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, text: '\r', unmodifiedText: '\r' });
  await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
  await new Promise((done) => setTimeout(done, 200));
  await wait(() => /collection=[a-f\d-]{36}/.test(location.hash));
  const id = await page.eval(() => new URLSearchParams(location.hash.split('?')[1]).get('collection'));
  await wait(() => document.querySelectorAll('[data-library-item]').length === 3);
  report.checks.push('Native Vietnamese input/keyboard save, preview zero writes, actual persisted query/view PASS');
  const initialIds = await page.eval(() => [...document.querySelectorAll('[data-library-item]')].map((entry) => entry.dataset.libraryItem).sort());
  assert.deepEqual(initialIds, rows.slice(0, 3).sort());
  for (const mode of ['list', 'card', 'timeline', 'table']) {
    await click('Xem điều kiện / chỉnh sửa'); await choose('Cách xem mặc định', mode); await click('Lưu bộ sưu tập');
    await wait(() => !document.querySelector('.saved-collection-form'));
    assert.deepEqual(await page.eval(() => [...document.querySelectorAll('[data-library-item]')].map((entry) => entry.dataset.libraryItem).sort()), initialIds);
    assert.equal(await page.eval(async (id) => (await fetch('/api/v1/collections/' + id).then((r) => r.json())).view, id), mode);
  }
  await page.send('Page.reload', { ignoreCache: true });
  await wait(() => !!document.querySelector('.saved-collection-screen table'));
  report.checks.push('Four saved modes retain exact Item IDs and table persists through actual reload PASS');
  const mutation = await page.eval(async (itemId) => {
    const session = await fetch('/api/v1/session').then((r) => r.json());
    const item = await fetch('/api/v1/items/' + itemId).then((r) => r.json());
    return (await fetch('/api/v1/items/' + itemId, { method: 'PATCH', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': session.csrf_token }, body: JSON.stringify({ favorite: false, expected_edit_version: item.user_edit_version }) })).status;
  }, rows[0]);
  assert.equal(mutation, 200); await click('Cập nhật kết quả');
  await wait(() => document.querySelectorAll('[data-library-item]').length === 2);
  report.checks.push('Actual favorite mutation dynamically removes Item from saved query without copying or moving it PASS');
  for (const width of [1920, 1440, 768, 390]) {
    await page.setViewport({ width, height: width === 1920 ? 1080 : 900 });
    await page.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
    assert.equal(await page.eval(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.screenshot({ path: path.join(out, 'collections-' + width + '.png'), format: 'png' });
    const metrics = await page.eval(probe), geometry = await page.eval(layout), application = await page.eval(app);
    const findings = [...judge(metrics, { width, allow: [] }), ...judgeLayout(geometry, { width, allow: [] })].filter((entry) => !APP_SKIP.has(entry.id) && entry.id !== 'no-title' && entry.id !== 'small-title');
    findings.push(...judgeApp(application, metrics, { width, allow: [] }));
    report.sizes.push({ width, overflow: false, findings });
  }
  await click('Xóa bộ sưu tập'); await click('Xác nhận xóa bộ lọc');
  const count = await page.eval(async () => (await fetch('/api/v1/collections').then((r) => r.json())).results.length);
  assert.equal(count, 0);
  report.checks.push('Explicit delete removes only definition; backend tests independently assert unchanged Item/pinned memberships PASS');
  assert.equal(page.consoleErrors.length, 0, page.consoleErrors.join('\n'));
  report.status = 'PASS';
} catch (error) { report.status = 'FAIL'; report.error = String(error.stack ?? error); throw error; }
finally { writeFileSync(path.join(out, 'results.json'), JSON.stringify(report, null, 2) + '\n'); await browser?.close(); await server?.close(); }
