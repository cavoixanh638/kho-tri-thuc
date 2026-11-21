import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { Browser } from './p08_cdp.mjs';

test('native Chromium navigates, evaluates JS, emulates reduced motion, screenshots 390 and 1920', { timeout: 30000 }, async () => {
  const browser = await Browser.launch();
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
    await page.setViewport({ width: 1920, height: 1080 });
    assert.equal(await page.eval(() => innerWidth), 1920);
    await page.close();
  } finally {
    await browser.close();
    rmSync(tmp, { recursive: true, force: true });
  }
});
