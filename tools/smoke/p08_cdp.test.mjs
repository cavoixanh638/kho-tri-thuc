import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { Browser } from './p08_cdp.mjs';

test('native Chromium navigates, evaluates JS, emulates reduced motion, screenshots 390 and 1920', { timeout: 60000 }, async () => {
  // CI starts two isolated Compose stacks; allow bounded Chromium cold start.
  const browser = await Browser.launch({ startupTimeoutMs: 30000 });
  const tmp = mkdtempSync(join(tmpdir(), 'p08-browser-test-'));
  try {
    const page = await browser.newPage({ width: 390, height: 844, reducedMotion: true });
    await page.goto('about:blank');
    await page.eval(() => { document.body.innerHTML = '<label>QA TEST ONLY</label>'; });
    assert.equal(await page.eval(() => document.querySelector('label').textContent), 'QA TEST ONLY');
    assert.equal(await page.eval(() => innerWidth), 390);
    assert.equal(await page.eval(() => matchMedia('(prefers-reduced-motion: reduce)').matches), true);
    const img390 = join(tmp, '390.png');
    await page.screenshot({ path: img390 });
    assert.equal(readFileSync(img390).subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
    // Exercise the native HTML <details> disclosure using CDP keyboard
    // identity + text fields, not DOM click() (which would hide IME/key faults).
    await page.eval(() => {
      document.body.innerHTML =
        '<details><summary>Advanced tools</summary><select><option>Link</option></select></details>';
      document.querySelector('summary').focus();
    });
    const keyBase = {
      key: 'Enter', code: 'Enter',
      windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13,
    };
    await page.send('Input.dispatchKeyEvent', {
      type: 'keyDown', ...keyBase, text: '\r', unmodifiedText: '\r',
    });
    await page.send('Input.dispatchKeyEvent', { type: 'keyUp', ...keyBase });
    assert.equal(await page.eval(() => document.querySelector('details').open),
      true, 'native summary must open with CDP Enter');
    await page.eval(() => document.querySelector('select').focus());
    assert.equal(await page.eval(() => document.activeElement?.tagName),
      'SELECT', 'visible select must be focusable after keyboard-opened details');
    await page.setViewport({ width: 1920, height: 1080 });
    assert.equal(await page.eval(() => innerWidth), 1920);
    await page.close();
  } finally {
    await browser.close();
    rmSync(tmp, { recursive: true, force: true });
  }
});
