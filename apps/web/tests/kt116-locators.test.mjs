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
  window.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
  server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom', logLevel: 'silent' });
  ui = await server.ssrLoadModule('/tests/kt116-entry.tsx');
});
afterEach(async () => { if (root) { await ui.act(async () => root.unmount()); root = null; } container?.remove(); globalThis.fetch = originalFetch; });
after(async () => { await server?.close(); dom?.window.close(); });
async function render(component, props) {
  container = document.createElement('div'); document.body.append(container); root = ui.createRoot(container);
  await ui.act(async () => { root.render(ui.createElement(ui.MantineProvider, { forceColorScheme: 'light' }, ui.createElement(component, props))); await settle(); });
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
    assert.equal(result.association.assetId, row[1], name + ' asset'); assert.equal(result.association.version, row[2], name + ' version');
    assert.equal(result.association.sourceId, row[1] ? null : row[3].source_id, name + ' web source');
    assert.equal(result.association.processorVersion, 'v1', name + ' processor version');
    if (result.state === 'AVAILABLE') {
      assert.equal(result.viewer.assetId, row[1], name + ' viewer asset'); assert.equal(result.viewer.version, row[2], name + ' viewer version');
      assert.equal(result.locator.kind === 'page' ? result.locator.page : result.locator.seconds, row[6], name + ' target');
    }
  }
});
test('reject non-finite, hostile URLs, credentials and mismatched viewer asset versions', () => {
  for (const value of [Infinity, NaN, true, '20', null]) assert.equal(ui.parseLocator({ start_seconds: value }), undefined);
  for (const value of ['javascript:alert(1)', 'https://user:secret@example.invalid', 'https://example.invalid/?access_token=secret', 'https://example.invalid/?X-Amz-Signature=secret', 'https://example.invalid/?%61ccess_token=secret', 'https://example.invalid/#access_token=secret']) assert.equal(ui.safeOriginalUrl(value), undefined);
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

test('late open response is aborted and cannot attach an old asset URL to a new citation', async () => {
  const { part } = materialize(locatorCases[0], 0);
  let resolveOld, signal;
  globalThis.fetch = async (_path, options) => { signal = options.signal; return new Promise(resolve => { resolveOld = resolve; }); };
  await render(ui.SourceLocatorCitation, { part });
  await click('Mở nguồn gốc');
  const newer = { ...part, id: 999, asset_id: 'pdf-new', source: { ...part.source, version: 'new-version' } };
  await ui.act(async () => { root.render(ui.createElement(ui.MantineProvider, { forceColorScheme: 'light' }, ui.createElement(ui.SourceLocatorCitation, { part: newer }))); await settle(); });
  assert.equal(signal.aborted, true);
  await ui.act(async () => { resolveOld(new Response(JSON.stringify({ url: 'https://example.invalid/old-private-asset' }))); await settle(); });
  assert.equal(container.querySelector('a'), null);
});

test('reading real transcript segments creates individual citation targets and escapes untrusted text', async () => {
  const { part } = materialize(locatorCases[14], 0);
  globalThis.fetch = async () => new Response(JSON.stringify({ origin: 'extracted', text: '', truncated: false, needs_review: true,
    parts: [{ ...part, text: 'bounded fallback', format: 'text', locator: { section: 'Transcript', segments: [{ start: .125, end: 1, text: '<script>fixture</script>' }, { start: 2.5, end: 3, text: 'Second segment' }] } }] }));
  await render(ui.KnowledgeReading, { id: 'fixture', onIllustration() {} });
  assert.equal(container.querySelectorAll('[data-state]').length, 2);
  assert.equal(container.querySelector('script'), null);
  assert.ok(container.textContent.includes('0:00.125'));
  assert.ok(container.textContent.includes('0:02.5'));
  assert.ok(container.textContent.includes('Cần đối chiếu video'));
});

test('reading multiple assets selects each viewer by asset ID even when host viewer order is reversed', async () => {
  const first = materialize(locatorCases[0], 1), second = materialize(locatorCases[1], 2);
  globalThis.fetch = async () => new Response(JSON.stringify({ origin: 'extracted', text: '', truncated: false, needs_review: false,
    parts: [first.part, second.part].map(part => ({ ...part, text: 'PDF fixture', format: 'text' })) }));
  await render(ui.KnowledgeReading, { id: 'fixture', sourceViewers: [second.viewer, first.viewer], onIllustration() {} });
  const buttons = [...container.querySelectorAll('button')].filter(button => button.textContent === 'Đến vị trí nguồn');
  assert.equal(buttons.length, 2);
  await ui.act(async () => { for (const button of buttons) button.click(); await settle(); });
  const frames = [...container.querySelectorAll('iframe')].map(frame => new URL(frame.src));
  assert.deepEqual(frames.map(frame => frame.pathname + frame.hash), ['/api/v1/assets/pdf-a/stream#page=1', '/api/v1/assets/pdf-b/stream#page=200']);
});

function privateMediaPart() {
  return { id: 900, kind: 'transcript', asset_id: '11111111-1111-4111-8111-111111111111', locator: { start_seconds: 2.5 },
    processor: 'fixture', source: { state: 'current', version: 'a'.repeat(64), asset_version: 3, mime: 'audio/wav', source_id: null, source_url: null } };
}
function privateMediaViewer(part) {
  return { assetId: part.asset_id, version: part.source.version, assetVersion: 3,
    url: `/api/v1/assets/${part.asset_id}/content/3/${part.source.version}`, kind: 'media', rangeVerified: true };
}
test('private viewer is loaded only on explicit action through cookie API and pinned source bytes', async () => {
  const part = privateMediaPart(); let calls = 0;
  globalThis.fetch = async (path, options) => {
    calls++; assert.equal(path, `/api/v1/assets/${part.asset_id}/viewer`); assert.equal(options.credentials, 'same-origin');
    return new Response(JSON.stringify(privateMediaViewer(part)));
  };
  await render(ui.SourceLocatorCitation, { part });
  assert.equal(calls, 0); assert.equal(container.querySelector('audio'), null);
  await click('Mở và định vị nguồn riêng tư');
  assert.equal(calls, 1); assert.equal(container.querySelector('[data-state]').dataset.state, 'AVAILABLE');
  assert.equal(new URL(container.querySelector('audio').src).pathname, privateMediaViewer(part).url);
});
test('private viewer rejects changed or hostile pinned paths and reports unavailable instead of loading media', async () => {
  const part = privateMediaPart(), viewer = privateMediaViewer(part);
  for (const changed of [{ ...viewer, url: viewer.url.replace('/content/3/', '/content/2/') },
    { ...viewer, url: viewer.url + '?token=do-not-render' }, { ...viewer, version: 'b'.repeat(64) },
    { ...viewer, rangeVerified: false }]) {
    assert.notEqual(ui.resolveLocator(part, changed).state, 'AVAILABLE');
  }
  globalThis.fetch = async () => new Response('{}', { status: 409 });
  await render(ui.SourceLocatorCitation, { part }); await click('Mở và định vị nguồn riêng tư');
  assert.equal(container.querySelector('audio'), null); assert.ok(container.querySelector('[role="alert"]'));
  assert.equal(container.querySelector('[data-state]').dataset.state, 'NOT_SUPPORTED');
});
test('late private descriptor cannot open an old asset after citation changes', async () => {
  const part = privateMediaPart(); let resolveOld, signal;
  globalThis.fetch = async (_path, options) => { signal = options.signal; return new Promise(resolve => { resolveOld = resolve; }); };
  await render(ui.SourceLocatorCitation, { part }); await click('Mở và định vị nguồn riêng tư');
  await ui.act(async () => { root.render(ui.createElement(ui.MantineProvider, { forceColorScheme: 'light' }, ui.createElement(ui.SourceLocatorCitation,
    { part: { ...part, id: 901, asset_id: '22222222-2222-4222-8222-222222222222' } }))); await settle(); });
  assert.equal(signal.aborted, true);
  await ui.act(async () => { resolveOld(new Response(JSON.stringify(privateMediaViewer(part)))); await settle(); });
  assert.equal(container.querySelector('audio'), null);
});
