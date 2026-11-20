import assert from 'node:assert/strict';
import { test } from 'node:test';
import { pathToFileURL } from 'node:url';
import { mkdirSync, writeFileSync } from 'node:fs';

test('real Chromium explicit template selection, callback, local fixture reload and responsive states', { skip: !process.env.KT121_CDP_MODULE }, async () => {
  const { Browser } = await import(pathToFileURL(process.env.KT121_CDP_MODULE).href);
  const browser = await Browser.launch({ extraArgs: ['--no-proxy-server'] });
  const report = { transport: 'Local production-built fixture, same-tab browser storage; no API calls', checks: [], device: 'Android and native IME NOT_RUN' };
  const out = 'tmp/kt121-qa'; mkdirSync(out, { recursive: true });
  try {
    const page = await browser.newPage({ width: 1440, height: 900 });
    await page.goto(process.env.KT121_BROWSER_URL ?? 'http://127.0.0.1:62221/tests/kt121-browser.html');
    const note = () => page.eval(() => document.querySelector('#fixture-note').value);
    const initial = await note();
    const click = (label) => page.eval((label) => [...document.querySelectorAll('button')].find((button) => button.textContent === label || button.querySelector('strong')?.textContent === label).click(), label);
    for (const label of ['Bài học', 'Sách / Chương', 'Cuộc họp', 'Video nguồn']) {
      await click(label); assert.equal(await note(), initial);
      assert.equal(await page.eval(() => window.kt121.applications), 0);
    }
    report.checks.push('four selections preview without changing note PASS');
    await page.eval(() => document.querySelector('.note-template-actions button').focus());
    await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, text: '\r', unmodifiedText: '\r' });
    await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
    await new Promise((resolve) => setTimeout(resolve, 150));
    const applied = await note(); assert.ok(applied.startsWith(initial)); assert.ok(applied.includes('# Video nguồn'), JSON.stringify(await page.eval(() => ({ active: document.activeElement.textContent, applied: window.kt121.applications, alert: document.querySelector('[role=alert]')?.textContent }))));
    assert.equal(await page.eval(() => window.kt121.applications), 1);
    report.checks.push('keyboard Enter explicitly applies once and preserves original prefix PASS');
    await click('Lưu vào phiên kiểm thử');
    await page.goto(process.env.KT121_BROWSER_URL ?? 'http://127.0.0.1:62221/tests/kt121-browser.html');
    assert.equal(await note(), applied);
    report.checks.push('local fixture save/reload keeps template text PASS; separate PostgreSQL tests cover persistence');
    await click('Bài học'); await page.eval(() => { window.kt121.reject = true; }); await click('Thêm mẫu vào cuối');
    await new Promise((resolve) => setTimeout(resolve, 150));
    assert.equal(await note(), applied); assert.ok(await page.eval(() => document.querySelector('[role=alert]')?.textContent.includes('Bản nháp đã thay đổi')));
    report.checks.push('rejected host application leaves note and preview PASS');
    for (const width of [1440, 768, 390]) {
      await page.setViewport({ width, height: 900 });
      assert.ok(await page.eval(() => document.documentElement.scrollWidth <= window.innerWidth));
      assert.ok(await page.eval(() => [...document.querySelectorAll('.note-template-options button,.note-template-actions button')].every((button) => button.getBoundingClientRect().height >= 44)));
      await page.screenshot({ path: `${out}/templates-${width}.png`, format: 'png', fullPage: true });
      report.checks.push(`${width}px no overflow; template actions >=44px PASS`);
    }
    await page.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
    assert.ok(await page.eval(() => !!document.querySelector('.note-template-preview')));
    report.checks.push('reduced motion retains preview PASS');
    writeFileSync(`${out}/results.json`, JSON.stringify(report, null, 2));
  } finally { await browser.close(); }
});
