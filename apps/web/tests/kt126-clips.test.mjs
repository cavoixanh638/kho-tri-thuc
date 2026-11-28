import assert from 'node:assert/strict';
import { before, after, beforeEach, afterEach, test } from 'node:test';
import { createServer } from 'vite';
import { JSDOM, VirtualConsole } from 'jsdom';
import { setImmediate as settle } from 'node:timers/promises';

let server, ui, dom, root, container, sent, preview, fail, hold, result, applied;
const originalFetch = globalThis.fetch;
const id = '12345678-1234-4567-89ab-123456789abc';
before(async () => {
  dom = new JSDOM('<html><body></body></html>', { url: 'http://127.0.0.1/', pretendToBeVisual: true, virtualConsole: new VirtualConsole() });
  for (const name of ['window', 'document', 'sessionStorage', 'navigator', 'HTMLElement', 'Element', 'Node', 'Event', 'MouseEvent', 'CustomEvent', 'MutationObserver', 'getComputedStyle'])
    Object.defineProperty(globalThis, name, { value: name === 'getComputedStyle' ? dom.window[name].bind(dom.window) : dom.window[name], configurable: true, writable: true });
  window.matchMedia = () => ({ matches: true, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
  globalThis.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
  Object.defineProperty(document, 'fonts', { value: new dom.window.EventTarget(), configurable: true });
  globalThis.requestAnimationFrame = window.requestAnimationFrame.bind(window);
  globalThis.cancelAnimationFrame = window.cancelAnimationFrame.bind(window);
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom', logLevel: 'silent' });
  ui = await server.ssrLoadModule('/tests/kt126-entry.tsx');
});
beforeEach(() => {
  sent = []; fail = false; hold = undefined; applied = undefined;
  preview = { receipt: 'signed-fixture', quote: 'Trích nguyên văn Tiếng Việt <script>alert(1)</script>', url: 'https://example.org', page_title: 'Nguồn kiểm thử', verification: 'current', source_version: 'a'.repeat(64), locator: {} };
  result = { results: [], next_offset: null };
  container = document.createElement('div'); document.body.append(container); root = ui.createRoot(container);
  globalThis.fetch = async (path, options = {}) => {
    const body = options.body && JSON.parse(options.body); sent.push({ path, method: options.method ?? 'GET', body, headers: options.headers });
    if (fail) return Response.json({ code: 'failure' }, { status: 409 });
    if (path.endsWith('/clips/preview')) return Response.json(preview);
    if (path.endsWith('/clips') && options.method === 'POST') {
      if (hold) await hold;
      return Response.json({ item_id: id, capture_id: 'capture-fixture', received_at: '2026-11-21T00:00:00Z', state: 'received' });
    }
    if (path.endsWith('/insert')) return Response.json({ note: 'Gốc\r\n\r\n> Trích', user_edit_version: 8, updated_at: '2026-11-21T00:00:00Z' });
    if (path.endsWith('/source')) return Response.json({ before: 'Đầu ', quote: 'Trích nguyên văn', after: ' cuối', state: 'current' });
    return Response.json(result);
  };
});
afterEach(async () => { await ui.act(async () => root.unmount()); container.remove(); });
after(async () => { globalThis.fetch = originalFetch; await server.close(); dom.window.close(); });
async function render(component = ui.ResearchClipper, props = { id, csrf: 'fixture' }) {
  await ui.act(async () => { root.render(ui.createElement(ui.MantineProvider, null, ui.createElement(component, props))); await settle(); });
}
async function click(text) {
  const button = [...container.querySelectorAll('button')].find((node) => node.textContent === text);
  assert.ok(button, text);
  await ui.act(async () => { button.click(); await settle(); });
}
async function field(label, value) {
  const node = [...container.querySelectorAll('label')].find((node) => node.textContent === label);
  assert.ok(node, label);
  const input = document.getElementById(node.htmlFor);
  await ui.act(async () => {
    const proto = input.tagName === 'SELECT' ? window.HTMLSelectElement.prototype : input.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, 'value').set.call(input, value);
    input.dispatchEvent(new window.Event(input.tagName === 'SELECT' ? 'change' : 'input', { bubbles: true })); await settle();
  });
}
async function makePreview(mode = 'link') {
  await field('Cách thu thập', mode); await field('URL nguồn công khai', 'https://example.org');
  if (mode === 'selection') await field('Đoạn trích nguyên văn', 'Trích nguyên văn');
  await click('Xem trước nguồn / đoạn trích');
}
for (const mode of ['link', 'article', 'selection']) test('explicit ' + mode + ' preview then save to current Item without PATCH', async () => {
  await render(); await makePreview(mode);
  const previews = sent.filter((row) => row.path.endsWith('/clips/preview'));
  assert.equal(previews.length, 1); assert.equal(previews[0].body.target_item_id, id); assert.equal(previews[0].body.mode, mode);
  assert.equal(sent.some((row) => row.path.endsWith('/clips') && row.method === 'POST'), false);
  assert.equal(container.querySelector('script'), null);
  await click('Lưu trích dẫn vào bài này');
  const saved = sent.filter((row) => row.path.endsWith('/clips') && row.method === 'POST');
  assert.equal(saved.length, 1); assert.equal(saved[0].body.receipt, preview.receipt);
  assert.ok(saved[0].headers.get('Idempotency-Key')); assert.equal(saved[0].headers.get('X-CSRFToken'), 'fixture');
  assert.equal(sent.some((row) => row.method === 'PATCH'), false);
  assert.match(container.textContent, /Đã tiếp nhận trích dẫn/);
});
test('unverified selection is labelled and never claims extracted knowledge', async () => {
  preview.verification = 'unverified'; await render(); await makePreview('selection');
  assert.match(container.textContent, /chưa xác minh trong nguồn/);
  assert.equal(container.querySelector('script'), null);
});
test('editing the URL invalidates preview and repeated click accepts once', async () => {
  await render(); await makePreview(); await field('URL nguồn công khai', 'https://example.org/changed');
  assert.equal(container.querySelector('.clip-preview'), null);
  await click('Xem trước nguồn / đoạn trích');
  let release; hold = new Promise((resolve) => { release = resolve; });
  const button = [...container.querySelectorAll('button')].find((node) => node.textContent === 'Lưu trích dẫn vào bài này');
  await ui.act(async () => { button.click(); button.click(); await settle(); });
  assert.equal(sent.filter((row) => row.path.endsWith('/clips') && row.method === 'POST').length, 1);
  await ui.act(async () => { release(); await settle(); });
});
test('failed receipt keeps preview and reuses original idempotency key', async () => {
  await render(); await makePreview(); fail = true; await click('Lưu trích dẫn vào bài này');
  assert.ok(container.querySelector('.clip-preview')); const key = sent.at(-1).headers.get('Idempotency-Key');
  fail = false; await click('Lưu trích dẫn vào bài này'); assert.equal(sent.at(-1).headers.get('Idempotency-Key'), key);
});
function clip(state = 'current') {
  return { id, quote: 'Trích nguyên văn', state, source_url: 'https://example.org', page_title: 'Nguồn',
    source_id: 1, part_id: 2, asset_id: null, source_version: 'a'.repeat(64), processor_version: '1', locator: {}, inserted_edit_version: null };
}
const item = { item_id: id, kind: 'text', title: 'Bài gốc', note: 'Gốc\r\n', description: '', user_edit_version: 7, assets: [], deleted: false };
test('saved annotation highlights verified text and only inserts after explicit versioned approval', async () => {
  result.results = [clip()];
  await render(ui.ClipAnnotations, { item, csrf: 'fixture', disabled: false, onUpdated: (value) => { applied = value; }, onIllustration() {} });
  await click('Xem đúng đoạn trong văn bản nguồn');
  assert.equal(container.querySelector('mark').textContent, 'Trích nguyên văn');
  assert.equal(applied, undefined);
  await click('Duyệt chèn vào bản biên soạn');
  assert.equal(sent.find((row) => row.path.endsWith('/insert')).body.expected_edit_version, 7);
  assert.equal(applied.item_id, id); assert.equal(applied.user_edit_version, 8);
});
test('stale source disables highlight and insertion rather than opening wrong version', async () => {
  result.results = [clip('stale')];
  await render(ui.ClipAnnotations, { item, csrf: 'fixture', disabled: false, onUpdated() {}, onIllustration() {} });
  assert.match(container.textContent, /Nguồn đã thay đổi/);
  assert.equal([...container.querySelectorAll('button')].some((row) => row.textContent === 'Duyệt chèn vào bản biên soạn'), false);
});
