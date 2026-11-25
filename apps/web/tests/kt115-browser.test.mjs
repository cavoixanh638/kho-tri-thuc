import assert from 'node:assert/strict';
import { test } from 'node:test';
import { pathToFileURL } from 'node:url';
import { mkdirSync, writeFileSync } from 'node:fs';

test('real Chromium native keyboard, draft recovery, save and responsive preview', { skip: !process.env.KT115_CDP_MODULE }, async () => {
  const { Browser } = await import(pathToFileURL(process.env.KT115_CDP_MODULE).href);
  const browser = await Browser.launch({ extraArgs: ['--no-proxy-server'] });
  const url = process.env.KT115_BROWSER_URL ?? 'http://127.0.0.1:62115/tests/kt115-browser.html';
  const report = { browser: 'Real installed Chromium, headless CDP; synthetic transport', checks: [], device: 'Android and native Unikey/EVKey NOT_RUN' };
  const out = 'tmp/kt115-qa'; mkdirSync(out, { recursive: true });
  try {
    const page = await browser.newPage({ width: 1920, height: 1080 });
    await page.goto(url);
    const value = () => page.eval(() => document.querySelector('.markdown-editor textarea').value);
    const key = async (key, code, modifiers = 0) => {
      await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key, code, windowsVirtualKeyCode: ({ Backspace: 8, ArrowLeft: 37, Enter: 13, Tab: 9, z: 90, c: 67, v: 86, a: 65 })[key], modifiers });
      await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key, code, modifiers });
    };
    const click = (label) => page.eval((label) => [...document.querySelectorAll('button')].find((button) => button.textContent === label).click(), label);
    const original = await value();
    await page.eval(() => { const textarea = document.querySelector('.markdown-editor textarea'); textarea.focus(); textarea.setSelectionRange(textarea.value.length, textarea.value.length); });
    await page.send('Input.insertText', { text: '\n\nTiếng Việt NFD: Tiếng' });
    const typed = await value(); assert.equal(typed, original + '\n\nTiếng Việt NFD: Tiếng');
    await key('ArrowLeft', 'ArrowLeft'); await key('Backspace', 'Backspace');
    assert.notEqual(await value(), typed);
    await key('z', 'KeyZ', 2); assert.equal(await value(), typed);
    await key('z', 'KeyZ', 10); assert.notEqual(await value(), typed);
    await key('z', 'KeyZ', 2); assert.equal(await value(), typed);
    report.checks.push('native Vietnamese insert, arrow, backspace, Ctrl+Z undo, Ctrl+Shift+Z redo PASS');
    await browser.send('Browser.grantPermissions', { origin: new URL(url).origin, permissions: ['clipboardReadWrite', 'clipboardSanitizedWrite'] });
    await page.eval(() => { const textarea = document.querySelector('.markdown-editor textarea'); textarea.focus(); textarea.select(); });
    await key('c', 'KeyC', 2);
    assert.equal((await page.eval(() => navigator.clipboard.readText())).replace(/\r\n/g, '\n'), typed, 'Windows clipboard uses CRLF');
    await key('v', 'KeyV', 2); assert.equal(await value(), typed);
    report.checks.push('native copy/paste Unicode exact PASS');
    await page.eval(() => { window.kt115.failSave = true; }); await click('Lưu thay đổi');
    await new Promise((resolve) => setTimeout(resolve, 150)); assert.equal(await value(), typed);
    assert.equal(await page.eval(() => window.kt115.patches.length), 0);
    await page.eval(() => { window.dispatchEvent(new Event('session-expired')); });
    // Restore a fresh draft and accept the browser's beforeunload warning for this test navigation.
    await click('Chỉnh sửa');
    await page.eval(() => { const textarea = document.querySelector('.markdown-editor textarea'); textarea.focus(); textarea.setSelectionRange(textarea.value.length, textarea.value.length); });
    await page.send('Input.insertText', { text: '\n\nKhôi phục tiếng Việt' }); const recovery = await value();
    browser.listeners.get(page.sessionId + '|Page.javascriptDialogOpening')?.clear();
    browser.on(page.sessionId, 'Page.javascriptDialogOpening', () => page.send('Page.handleJavaScriptDialog', { accept: true }));
    await page.goto(url);
    assert.equal(await value(), recovery);
    assert.equal(await page.eval(() => document.body.textContent.includes('Đã khôi phục bản nháp')), true);
    report.checks.push('network failure retains draft; same-tab reload recovers PASS');
    await page.eval(() => document.querySelector('.markdown-editor textarea').focus()); await key('Enter', 'Enter', 2);
    await new Promise((resolve) => setTimeout(resolve, 150));
    const result = await page.eval(() => ({ saved: window.kt115.item.note, patches: window.kt115.patches, drafts: Object.keys(sessionStorage).filter((key) => key.startsWith('kt-markdown')) }));
    assert.equal(result.saved, recovery.replace(/\n/g, '\r\n')); assert.equal(result.patches.length, 1); assert.equal(result.drafts.length, 0);
    report.checks.push('Ctrl+Enter saves exact raw CRLF with one PATCH PASS');
    await click('Chỉnh sửa'); await click('Soạn + Xem trước');
    for (const width of [1920, 1440, 768, 390]) {
      await page.setViewport({ width, height: width === 1920 ? 1080 : 900 });
      const measured = await page.eval(() => ({ width: window.innerWidth, document: document.documentElement.scrollWidth, panes: [...document.querySelectorAll('.markdown-editor-panes > *')].map((node) => ({ x: node.getBoundingClientRect().x, width: node.getBoundingClientRect().width })) }));
      assert.ok(measured.document <= width, JSON.stringify(measured));
      await page.screenshot({ path: `${out}/editor-${width}.png`, format: 'png', fullPage: true });
      report.checks.push(`width ${width}: no page overflow; screenshot recorded PASS`);
    }
    await page.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
    await click('Đọc bản nháp'); assert.equal(await page.eval(() => document.querySelector('.markdown-editor textarea').hidden || document.querySelector('.markdown-editor textarea').parentElement.hidden), true);
    assert.ok(await page.eval(() => !!document.querySelector('.markdown-editor-preview table')));
    report.checks.push('Read mode and reduced motion content PASS');
    writeFileSync(`${out}/results.json`, JSON.stringify(report, null, 2));
  } finally { await browser.close(); }
});
