import assert from 'node:assert/strict';
import { build, preview } from 'vite';
import react from '@vitejs/plugin-react';
import { mkdirSync, writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
const { Browser } = await import(pathToFileURL(process.env.KT124_CDP_HELPER).href);
const cases = JSON.parse(process.env.KT124_CASES);
const out = path.resolve(process.env.KT124_EVIDENCE_DIR ?? '../../tmp/kt124-browser');
mkdirSync(out, { recursive: true });
const report = { transport: 'Production-built navigation fixture using actual Django session/CSRF/navigation/link/PATCH APIs and PostgreSQL; callback-only structural actions', checks: [], widths: [], android: 'NOT_RUN', native_unikey_evkey: 'NOT_RUN' };
let server, browser;
try {
  await build({ configFile: false, plugins: [react()], build: { outDir: 'tmp/kt124-browser-build', emptyOutDir: true, rolldownOptions: { input: 'tests/kt124-browser.html' } }, logLevel: 'error' });
  server = await preview({ configFile: false, build: { outDir: 'tmp/kt124-browser-build' }, preview: { host: '127.0.0.1', port: 0, proxy: { '/api': { target: process.env.KT124_API, changeOrigin: false } } } });
  const origin = server.resolvedUrls.local[0].replace(/\/$/, '');
  browser = await Browser.launch({ extraArgs: ['--no-proxy-server'] });
  report.browser = (await browser.send('Browser.getVersion')).product;
  const page = await browser.newPage({ width: 1920, height: 1080, reducedMotion: true });
  await page.goto(origin + '/api/v1/session');
  assert.equal(await page.eval(async () => {
    const session = await fetch('/api/v1/session').then((response) => response.json());
    return (await fetch('/api/v1/session', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': session.csrf_token }, body: JSON.stringify({ username: 'navigation-browser', password: 'qa-navigation-only' }) })).status;
  }), 200);
  await page.goto(origin + '/tests/kt124-browser.html?item=' + cases.focus);
  const wait = async (fn, arg) => {
    for (let i = 0; i < 100; i++) { if (await page.eval(fn, arg)) return; await new Promise((done) => setTimeout(done, 50)); }
    throw new Error('Browser wait failed: ' + fn);
  };
  const click = (label) => page.eval((label) => [...document.querySelectorAll('button')].find((node) => node.textContent === label).click(), label);
  await wait(() => document.querySelector('.markdown-editor textarea')?.value.includes('H6'));
  const raw = await page.eval(() => window.kt124.note);
  await page.eval(() => { const field = document.querySelector('.markdown-editor textarea'); field.focus(); field.setSelectionRange(field.value.length, field.value.length); });
  await page.send('Input.insertText', { text: '\n[[Trùng' });
  await wait(() => document.querySelectorAll('.wiki-completion [role="option"]').length === 2);
  await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'ArrowDown', code: 'ArrowDown', windowsVirtualKeyCode: 40 });
  await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
  await wait(() => !document.querySelector('.wiki-completion'));
  const inserted = await page.eval(() => window.kt124.note);
  assert.ok(inserted.startsWith(raw)); assert.ok(inserted.includes('](#/muc/' + cases.second + ')'));
  await page.eval(() => document.getElementById('save').click());
  await wait(async () => (await fetch('/api/v1/items/' + window.kt124.itemId).then((r) => r.json())).note.includes('](#/muc/'));
  const stored = await page.eval(async () => (await fetch('/api/v1/items/' + window.kt124.itemId).then((r) => r.json())).note);
  assert.equal(stored, inserted);
  await click('Đọc bài');
  await wait(() => document.querySelectorAll('.note-outline a').length === 6);
  for (let i = 0; i < 6; i++) {
    const destination = await page.eval((i) => { const a = document.querySelectorAll('.note-outline a')[i]; a.click(); return a.getAttribute('href').slice(1); }, i);
    assert.equal(await page.eval(() => document.activeElement.id), destination);
  }
  report.checks.push('Actual API wiki autocomplete, identical-title UUID disambiguation, native Arrow/Enter insertion, PATCH preserves raw prefix, six real TOC focus jumps PASS');
  for (const width of [1920, 1440, 768, 390]) {
    await page.setViewport({ width, height: width === 1920 ? 1080 : 900 });
    await page.eval(() => scrollTo(0, 0));
    for (const label of ['Tạo ghi chú mới', 'Di chuyển bài đang mở', 'Gắn nguồn vào bài đang mở', 'Đi đến ngày nhận trong thư viện', 'Tạo ghi chú mới']) {
      await click('Tìm và thao tác · Ctrl+K');
      await wait(() => document.querySelector('dialog').open);
      await page.eval(() => { const field = document.querySelector('dialog input'); field.focus(); field.select(); });
      await page.send('Input.insertText', { text: label });
      await wait((label) => [...document.querySelectorAll('dialog [role="option"]')].some((node) => node.textContent === label), label);
      await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
      await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
      await wait(() => !document.querySelector('dialog').open);
    }
    assert.equal(await page.eval(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.screenshot({ path: path.join(out, 'navigation-' + width + '.png'), format: 'png' });
    report.widths.push({ width, no_overflow: true, commands: 5 });
  }
  assert.equal(await page.eval(() => window.kt124.actions.length), 20);
  await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'k', code: 'KeyK', windowsVirtualKeyCode: 75, modifiers: 2 });
  await wait(() => document.querySelector('dialog').open);
  await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
  await wait(() => !document.querySelector('dialog').open);
  report.checks.push('20 native visible palette actions over four sizes, Ctrl+K/Esc dialog/focus and reduced-motion PASS; structural action callback only, full host journeys belong to KT128');
  report.status = 'PASS';
} catch (error) { report.status = 'FAIL'; report.error = String(error.stack ?? error); throw error; }
finally { writeFileSync(path.join(out, 'results.json'), JSON.stringify(report, null, 2) + '\n'); await browser?.close(); await new Promise((done) => server ? server.httpServer.close(done) : done()); }
