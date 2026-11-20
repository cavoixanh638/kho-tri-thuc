import assert from 'node:assert/strict';
import { before, after, afterEach, test } from 'node:test';
import { setImmediate as settle } from 'node:timers/promises';
import { createServer } from 'vite';
import { JSDOM, VirtualConsole } from 'jsdom';
import { locatorCases, materialize } from './kt116-fixtures.mjs';
let server, ui, dom, root, container;
const originalFetch = globalThis.fetch;
before(async () => {
  dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'http://127.0.0.1:5173', pretendToBeVisual: true, virtualConsole: new VirtualConsole() });
  for (const name of ['window', 'document', 'navigator', 'HTMLElement', 'Element', 'Node', 'Event', 'MouseEvent', 'CustomEvent', 'MutationObserver']) Object.defineProperty(globalThis, name, { value: dom.window[name], writable: true, configurable: true });
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom', logLevel: 'silent' });
  ui = await server.ssrLoadModule('/tests/kt116-entry.tsx');
});
afterEach(async () => { if (root) { await ui.act(async () => root.unmount()); root = null; } container?.remove(); globalThis.fetch = originalFetch; });
after(async () => { await server?.close(); dom?.window.close(); });
async function render(component, props) {
  container = document.createElement('div'); document.body.append(container); root = ui.createRoot(container);
  await ui.act(async () => { root.render(ui.createElement(component, props)); await settle(); });
}
async function click(text) {
  const target = [...container.querySelectorAll('button')].find(e => e.textContent === text); assert.ok(target, text);
  await ui.act(async () => { target.click(); await settle(); });
}
test('30 independent ground-truth locators retain exact asset/source/version and target', () => {
  assert.equal(locatorCases.length, 30);
  for (const [index, row] of locatorCases.entries()) {
    const { name, part, viewer } = materialize(row, index);
    const result = ui.resolveLocator(part, viewer);
    assert.equal(result.state, row[5], name);
    assert.equal(part.asset_id, row[1], name + ' asset'); assert.equal(part.source.version, row[2], name + ' version');
    if (result.state === 'AVAILABLE') {
      assert.equal(result.viewer.assetId, row[1], name + ' viewer asset'); assert.equal(result.viewer.version, row[2], name + ' viewer version');
      assert.equal(result.locator.kind === 'page' ? result.locator.page : result.locator.seconds, row[6], name + ' target');
    }
  }
});
test('reject non-finite, hostile URLs, credentials and mismatched viewer asset versions', () => {
  for (const value of [Infinity, NaN, true, '20', null]) assert.equal(ui.parseLocator({ start_seconds: value }), undefined);
  for (const value of ['javascript:alert(1)', 'https://user:secret@example.invalid', 'https://example.invalid/?access_token=secret', 'https://example.invalid/?X-Amz-Signature=secret']) assert.equal(ui.safeOriginalUrl(value), undefined);
  for (const value of ['//evil.invalid/stream', 'https://drive.google.com/preview', '/api/v1/assets/a/thumbnail', '/api/v1/assets/a/stream?token=secret']) assert.equal(ui.privateViewerUrl(value), undefined);
  const { part, viewer } = materialize(locatorCases[0], 0);
  assert.equal(ui.resolveLocator(part, { ...viewer, assetId: 'different' }).state, 'STALE_SOURCE');
  assert.equal(ui.resolveLocator(part, { ...viewer, assetVersion: 8 }).state, 'STALE_SOURCE');
});
test('producer transcript segments preserve millisecond targets without parsing metadata', () => {
  const rows = ui.transcriptSegments({ segments: [{ start: .125, end: 1.7, text: 'Một' }, { start: 2.5, end: 4, text: 'Hai' }] });
  assert.equal(ui.parseLocator(rows[0].locator).seconds, .125); assert.equal(ui.parseLocator(rows[1].locator).seconds, 2.5);
  assert.deepEqual(ui.transcriptSegments({ segments: [{ start: 2, end: 1, text: 'bad' }] }), []);
  assert.deepEqual(ui.transcriptSegments({ segments: [{ start: 0, end: 1, text: '<script>' }, { start: -1, end: 0, text: 'bad' }] }), []);
});
test('default UI tells the truth about Drive previews and opens original through authenticated API', async () => {
  const { part } = materialize(locatorCases[0], 0);
  globalThis.fetch = async (path, options) => { assert.equal(path, '/api/v1/assets/pdf-a/open'); assert.equal(options.credentials, 'same-origin'); return new Response(JSON.stringify({ url: 'https://drive.google.com/open?id=fixture' })); };
  await render(ui.SourceLocatorCitation, { part });
  assert.equal(container.querySelector('[data-state]').dataset.state, 'NOT_SUPPORTED');
  assert.ok(!container.textContent.includes('Đến vị trí nguồn'));
  await click('Mở nguồn gốc');
  assert.equal(container.querySelector('a').rel, 'noopener noreferrer');
  assert.match(container.querySelector('a').textContent, /không định vị/);
});
test('403, 404 and expiring/unsafe URL failures keep private values out of UI', async () => {
  const { part } = materialize(locatorCases[0], 0);
  let status = 403;
  globalThis.fetch = async () => status === 200 ? new Response(JSON.stringify({ url: 'https://example.invalid?access_token=DO-NOT-RENDER' })) : new Response('{}', { status });
  await render(ui.SourceLocatorCitation, { part });
  for (status of [403, 404, 503, 200]) { await click('Mở nguồn gốc'); assert.ok(container.querySelector('[role="alert"]')); assert.equal(container.querySelector('a'), null); assert.ok(!container.innerHTML.includes('DO-NOT-RENDER')); }
});
test('missing source disables original open, stale citation keeps explicit warning', async () => {
  const { part } = materialize(locatorCases[22], 0);
  await render(ui.SourceLocatorCitation, { part });
  assert.equal(container.querySelector('button'), null);
});
test('media assignment checks seekable ranges and duration; this is not browser seek evidence', () => {
  const media = { duration: 10, seekable: { length: 1, start: () => 0, end: () => 10 }, currentTime: 0 };
  ui.seekMedia(media, 4.25); assert.equal(media.currentTime, 4.25);
  assert.throws(() => ui.seekMedia(media, 11)); media.seekable.length = 0; assert.throws(() => ui.seekMedia(media, 1));
});
