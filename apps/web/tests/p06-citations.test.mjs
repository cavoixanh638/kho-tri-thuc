import assert from 'node:assert/strict';
import { before, after, afterEach, test } from 'node:test';
import { setImmediate as settle } from 'node:timers/promises';
import { createServer } from 'vite';
import { JSDOM, VirtualConsole } from 'jsdom';
import { locatorCases, materialize } from './kt116-fixtures.mjs';

let server, ui, dom, root, container;
const originalFetch = globalThis.fetch;

before(async () => {
  dom = new JSDOM('<!doctype html><html><body></body></html>', {
    url: 'http://127.0.0.1:5173', pretendToBeVisual: true, virtualConsole: new VirtualConsole(),
  });
  for (const name of ['window', 'document', 'navigator', 'HTMLElement', 'Element', 'Node', 'Event', 'MouseEvent', 'CustomEvent', 'MutationObserver']) {
    Object.defineProperty(globalThis, name, { value: dom.window[name], writable: true, configurable: true });
  }
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  window.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
  server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom', logLevel: 'silent' });
  ui = await server.ssrLoadModule('/tests/p06-entry.tsx');
});
afterEach(async () => {
  if (root) { await ui.act(async () => root.unmount()); root = null; }
  container?.remove(); container = null;
  globalThis.fetch = originalFetch;
});
after(async () => { await server?.close(); dom?.window.close(); });

async function render(component, props) {
  if (root) { await ui.act(async () => root.unmount()); root = null; }
  container?.remove();
  container = document.createElement('div'); document.body.append(container);
  root = ui.createRoot(container);
  await ui.act(async () => {
    root.render(ui.createElement(ui.MantineProvider, { forceColorScheme: 'light' }, ui.createElement(component, props)));
    await settle();
  });
}
async function click(label) {
  const button = [...container.querySelectorAll('button')].find((node) => node.textContent === label);
  assert.ok(button, label);
  await ui.act(async () => { button.click(); await settle(); });
}

test('30/30 authored+PDF/ASR/web/missing/stale association cases keep exact provenance and rendered state', async () => {
  assert.equal(locatorCases.length, 30);
  let checked = 0;
  for (const [index, row] of locatorCases.entries()) {
    const { name, part, viewer } = materialize(row, index);
    const citation = { ...part, text: 'Nguồn trích <không phải> ghi chú.', format: 'text' };
    const entries = ui.mapCitationParts([citation], viewer ? [viewer] : []);
    assert.equal(entries.length, 1);
    const resolution = entries[0].resolution;
    assert.equal(resolution.state, row[5], name);
    assert.equal(resolution.association.assetId, row[1], name);
    assert.equal(resolution.association.version, row[2], name);
    assert.equal(resolution.association.sourceId, row[1] ? null : row[3].source_id ?? null, name);
    assert.equal(resolution.association.processorVersion, 'v1', name);
    if (resolution.state === 'AVAILABLE') {
      assert.equal(resolution.viewer.assetId, row[1], name);
      assert.equal(resolution.locator.kind === 'page' ? resolution.locator.page : resolution.locator.seconds, row[6], name);
    }
    await render(ui.SourceCitationList, { parts: [citation], sourceViewers: viewer ? [viewer] : [] });
    assert.equal(container.querySelector('.source-citations').getAttribute('aria-label'), 'Dẫn chứng nguồn cho ghi chú');
    assert.equal(container.querySelector('[data-citation-state]').getAttribute('data-citation-state'), row[5], name);
    assert.equal(container.querySelector('.source-locator').dataset.state, row[5], name);
    assert.equal(container.querySelector('[data-part-id]').getAttribute('data-part-id'), String(index), name);
    assert.equal(container.querySelector('script'), null);
    checked++;
  }
  assert.equal(checked, 30);
});

test('authored note stays present while PDF, video, and web evidence appear separately', async () => {
  const pdf = materialize(locatorCases[0], 1).part;
  const video = materialize(locatorCases[14], 2).part;
  const web = materialize(locatorCases[18], 3).part;
  const raw = '# Nội dung người viết\n**Giữ nguyên** và không ghép nguồn tự động.';
  globalThis.fetch = async (path, options) => {
    assert.equal(path, '/api/v1/items/fixture/knowledge');
    assert.equal(options.credentials, 'same-origin');
    return new Response(JSON.stringify({ origin: 'authored', text: raw, truncated: false, needs_review: false,
      parts: [pdf, video, web].map((part) => ({ ...part, text: 'Văn bản từ nguồn', format: 'text' })) }));
  };
  await render(ui.KnowledgeReading, { id: 'fixture', onIllustration() {} });
  assert.match(container.textContent, /Giữ nguyên/);
  assert.equal(container.querySelectorAll('[data-citation-state]').length, 3);
  assert.equal(container.querySelectorAll('.knowledge-text').length, 1);
  assert.equal(container.querySelectorAll('.source-citation-excerpt').length, 3);
  assert.equal(container.querySelectorAll('audio, video, iframe').length, 0);
  await render(ui.SourceCitationBridge, { id: 'fixture', onIllustration() {} });
  assert.equal(container.querySelectorAll('.knowledge-text').length, 0);
  assert.equal(container.querySelectorAll('[data-citation-state]').length, 3);
  assert.doesNotMatch(container.textContent, /Giữ nguyên/);
});

test('bridge never reveals citations to a different user or after item removal', async () => {
  for (const status of [401, 403, 404]) {
    globalThis.fetch = async () => new Response('{}', { status });
    await render(ui.SourceCitationBridge, { id: 'private-item' });
    assert.ok(container.querySelector('[role="alert"]'), String(status));
    assert.equal(container.querySelector('.source-citations'), null);
    assert.equal(container.querySelector('iframe'), null);
  }
});

test('same asset with two extracted versions selects its exact viewer, not the first viewer', () => {
  const first = materialize(locatorCases[0], 1);
  const older = { ...first.part, id: 2, source: { ...first.part.source, version: 'another-hash', asset_version: 9 } };
  const secondViewer = { ...first.viewer, version: 'another-hash', assetVersion: 9 };
  const mapped = ui.mapCitationParts([
    { ...first.part, text: 'v1', format: 'text' }, { ...older, text: 'v2', format: 'text' },
  ], [secondViewer, first.viewer]);
  assert.equal(mapped[0].resolution.state, 'AVAILABLE');
  assert.equal(mapped[1].resolution.state, 'AVAILABLE');
  assert.equal(mapped[0].viewer.version, first.part.source.version);
  assert.equal(mapped[1].viewer.version, 'another-hash');
});

test('PDF page request uses authenticated version-pinned viewer, not Drive thumbnail', async () => {
  const hash = 'a'.repeat(64), assetId = '11111111-1111-4111-8111-111111111111';
  const part = { id: 46, kind: 'document_text', text: 'Trang bảy', format: 'text', asset_id: assetId, locator: { page: 7 },
    processor: 'fixture', processor_version: 'v1',
    source: { state: 'current', version: hash, asset_version: 3, source_id: null, source_url: null, mime: 'application/pdf' } };
  const url = `/api/v1/assets/${assetId}/content/3/${hash}`;
  globalThis.fetch = async (path, options) => {
    assert.equal(path, `/api/v1/assets/${assetId}/viewer`); assert.equal(options.credentials, 'same-origin');
    return new Response(JSON.stringify({ assetId, version: hash, assetVersion: 3, url, kind: 'pdf', pageNavigationVerified: true }));
  };
  await render(ui.SourceCitationList, { parts: [part] });
  assert.equal(container.querySelector('iframe'), null);
  await click('Mở và định vị PDF riêng tư');
  assert.equal(container.querySelector('.source-locator').dataset.state, 'AVAILABLE');
  assert.equal(new URL(container.querySelector('iframe').src).pathname + new URL(container.querySelector('iframe').src).hash, url + '#page=7');
});

test('stale source cannot open a private PDF viewer or falsely promise precise navigation', async () => {
  const { part, viewer } = materialize(locatorCases[23], 23);
  let calls = 0; globalThis.fetch = async () => { calls++; throw Error('no private request allowed'); };
  await render(ui.SourceCitationList, { parts: [{ ...part, text: 'stale', format: 'text' }], sourceViewers: viewer ? [viewer] : [] });
  assert.equal(container.querySelector('[data-citation-state]').getAttribute('data-citation-state'), 'STALE_SOURCE');
  assert.equal([...container.querySelectorAll('button')].some(b => /Đến vị trí nguồn|Mở và định vị PDF/.test(b.textContent)), false);
  assert.equal(calls, 0);
});

test('pagination never drops late citations and does not mutate the source list', async () => {
  const { part } = materialize(locatorCases[18], 18);
  const rows = Array.from({ length: 45 }, (_, n) => ({ ...part, id: n + 1, text: 'S' + n, format: 'text' }));
  await render(ui.SourceCitationList, { parts: rows, truncated: true });
  assert.equal(container.querySelectorAll('[data-citation-state]').length, 20);
  await click('Xem thêm dẫn chứng (25 còn lại)');
  assert.equal(container.querySelectorAll('[data-citation-state]').length, 40);
  await click('Xem thêm dẫn chứng (5 còn lại)');
  assert.equal(container.querySelectorAll('[data-citation-state]').length, 45);
  assert.equal(rows.length, 45);
  assert.match(container.textContent, /rút gọn/);
});


test('authored ASR evidence expands timed segments without inferring time from section strings', async () => {
  const { part } = materialize(locatorCases[14], 14);
  const withSegments = {
    ...part, text: 'Bản gốc không thay thế ghi chú', format: 'text',
    locator: { section: '00:01-00:04', segments: [
      { start: 0.125, end: 0.75, text: 'Đầu đoạn' },
      { start: 2.5, end: 3.25, text: 'Sau đoạn' },
    ] },
  };
  await render(ui.SourceCitationList, { parts: [withSegments] });
  const states = [...container.querySelectorAll('.source-citation-segments .source-locator')].map(node => node.dataset.state);
  assert.deepEqual(states, ['NOT_SUPPORTED', 'NOT_SUPPORTED']);
  assert.match(container.textContent, /0:00.125/);
  assert.match(container.textContent, /0:02.5/);
  assert.ok(!container.textContent.includes('00:01-00:04Đến vị trí nguồn'));
});


test('verified PDFium image route shows exact page without trusting native #page iframe', async () => {
  const hash = 'a'.repeat(64), assetId = '11111111-1111-4111-8111-111111111111';
  const part = { id: 207, kind: 'document_text', text: 'Trang thứ hai', format: 'text',
    asset_id: assetId, locator: { page: 2 }, processor: 'pypdfium2', processor_version: 'v1',
    source: { state: 'current', version: hash, asset_version: 4, source_id: null,
      source_url: null, mime: 'application/pdf' } };
  const url = '/api/v1/assets/' + assetId + '/content/4/' + hash;
  const pdfPage = '/api/v1/assets/' + assetId + '/pdf-page/4/' + hash + '/2';
  globalThis.fetch = async (path, opts) => {
    assert.equal(path, '/api/v1/assets/' + assetId + '/viewer');
    assert.equal(opts.credentials, 'same-origin');
    return new Response(JSON.stringify({
      assetId, version: hash, assetVersion: 4, url, kind: 'pdf',
      pageNavigationVerified: false, rangeVerified: true,
      pdfPageRenderer: 'server_pdfium2',
    }));
  };
  await render(ui.SourceCitationList, { parts: [part] });
  assert.equal(container.querySelector('img[src*="/pdf-page/"]'), null);
  await click('Mở và định vị PDF riêng tư');
  assert.equal(container.querySelector('.source-locator').dataset.state, 'AVAILABLE');
  assert.equal(container.querySelector('iframe'), null, 'native PDF iframe must not claim correct page');
  const image = container.querySelector('.source-locator-viewer img');
  assert.ok(image);
  assert.equal(new URL(image.src).pathname, pdfPage);
  assert.equal(image.getAttribute('data-verified-page'), null, 'not verified before image loads');
  await ui.act(async () => { image.dispatchEvent(new dom.window.Event('load')); await settle(); });
  assert.equal(container.querySelector('img').dataset.verifiedPage, '2');
  assert.match(container.textContent, /đúng trang 2/);
});

test('failed private page render revokes AVAILABLE and shows a clear warning', async () => {
  const hash = 'a'.repeat(64), assetId = '11111111-1111-4111-8111-111111111111';
  const part = { id: 208, kind: 'document_text', text: 'Hỏng PDF', format: 'text',
    asset_id: assetId, locator: { page: 999 }, processor: 'pypdfium2', processor_version: 'v1',
    source: { state: 'current', version: hash, asset_version: 1, source_id: null,
      source_url: null, mime: 'application/pdf' } };
  const url = '/api/v1/assets/' + assetId + '/content/1/' + hash;
  globalThis.fetch = async () => new Response(JSON.stringify({ assetId, version: hash,
    assetVersion: 1, url, kind: 'pdf', pageNavigationVerified: false,
    pdfPageRenderer: 'server_pdfium2' }));
  await render(ui.SourceCitationList, { parts: [part] });
  await click('Mở và định vị PDF riêng tư');
  const image = container.querySelector('.source-locator-viewer img'); assert.ok(image);
  await ui.act(async () => { image.dispatchEvent(new dom.window.Event('error')); await settle(); });
  assert.equal(container.querySelector('.source-locator').dataset.state, 'NOT_SUPPORTED');
  assert.equal(container.querySelector('.source-locator-viewer img'), null);
  assert.match(container.querySelector('[role="alert"]').textContent, /Không dựng được đúng trang PDF/);
});
