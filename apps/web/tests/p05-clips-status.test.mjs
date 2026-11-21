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
test('P05 blocked access or quota is clearly unverified and no raw HTML runs', async () => {
  preview.verification = 'unverified';
  preview.fetch_status = 'access_denied';
  preview.http_status = 403;
  await render(); await makePreview('selection');
  assert.match(container.textContent, /Máy chủ từ chối truy cập/);
  assert.match(container.textContent, /HTTP 403/);
  assert.match(container.textContent, /chưa xác minh trong nguồn/);
  assert.equal(container.querySelector('script'), null);
});

test('P05 HTTP 429 and body limit status are visible without fabricated article text', async () => {
  preview.verification = 'link_only';
  preview.fetch_status = 'failed';
  preview.http_status = 429;
  preview.quote = '';
  await render(); await makePreview('article');
  assert.match(container.textContent, /HTTP 429/);
  assert.match(container.textContent, /Không lấy được bài viết/);
  assert.match(container.textContent, /Chỉ có liên kết/);
});

test('P05 page truncation is visibly disclosed', async () => {
  preview.truncated = true;
  preview.quote = 'Partial public text';
  await render(); await makePreview('article');
  assert.match(container.textContent, /chưa phải toàn bộ bài viết/);
});

test('P05 input change discards signed receipt, no request committed on preview alone', async () => {
  await render(); await makePreview('selection');
  assert.equal(sent.filter((row) => row.path.endsWith('/clips') && row.method === 'POST').length, 0);
  await field('URL nguồn công khai', 'https://example.org/new');
  assert.equal(container.querySelector('.clip-preview'), null);
});
