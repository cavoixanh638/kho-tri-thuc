import assert from 'node:assert/strict';
import { before, after, beforeEach, afterEach, test } from 'node:test';
import { setImmediate as settle } from 'node:timers/promises';
import { createServer } from 'vite';
import { JSDOM, VirtualConsole } from 'jsdom';
import { fixtures } from './kt115-fixtures.mjs';

let server, ui, dom, root, container, saved, requests, failSave, latest;
const originalFetch = globalThis.fetch;
before(async () => {
  dom = new JSDOM('<html><body></body></html>', { url: 'http://127.0.0.1/', pretendToBeVisual: true, virtualConsole: new VirtualConsole() });
  for (const name of ['window', 'document', 'sessionStorage', 'navigator', 'HTMLElement', 'Element', 'Node', 'Event', 'MouseEvent', 'CustomEvent', 'MutationObserver', 'getComputedStyle']) {
    Object.defineProperty(globalThis, name, { value: name === 'getComputedStyle' ? dom.window[name].bind(dom.window) : dom.window[name], configurable: true, writable: true });
  }
  window.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
  globalThis.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
  Object.defineProperty(document, 'fonts', { value: new dom.window.EventTarget(), configurable: true });
  globalThis.requestAnimationFrame = window.requestAnimationFrame.bind(window);
  globalThis.cancelAnimationFrame = window.cancelAnimationFrame.bind(window);
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom', logLevel: 'silent' });
  ui = await server.ssrLoadModule('/tests/kt115-entry.tsx');
});
const response = (data, status = 200) => new Response(JSON.stringify(data), { status });
beforeEach(() => {
  sessionStorage.clear(); requests = []; failSave = false; latest = undefined;
  saved = { item_id: 'kt115', kind: 'text', title: 'Bài kiểm thử', description: '', note: 'Gốc', saved_at: '2026-11-20T00:00:00Z', updated_at: '2026-11-20T00:00:00Z', published_at: null, favorite: false, deleted: false, classification_status: 'unclassified', original_url: '', source_fetch: 'not_applicable', content_extract: 'done', asset_storage: 'not_applicable', assets: [] };
  container = document.createElement('div'); document.body.append(container); root = ui.createRoot(container);
  globalThis.fetch = async (path, options = {}) => {
    requests.push({ path, ...options });
    if (path.endsWith('/items/kt115')) {
      if (options.method === 'PATCH') {
        if (failSave) return response({}, 503);
        saved = { ...saved, ...JSON.parse(options.body) };
      }
      return response(latest ?? saved);
    }
    if (path.includes('/organization')) return response({ topics: [], projects: [], tags: [] });
    return response({ results: [], next_offset: null });
  };
});
afterEach(async () => { await ui.act(async () => root.unmount()); container.remove(); });
after(async () => { globalThis.fetch = originalFetch; await server.close(); dom.window.close(); });
async function render() {
  await ui.act(async () => { root.render(ui.createElement(ui.MantineProvider, null, ui.createElement(ui.ItemScreen, { id: 'kt115', csrf: 'fixture-csrf' }))); await settle(); });
}
async function click(label) {
  const button = [...container.querySelectorAll('button')].find((node) => node.textContent === label);
  assert.ok(button, label);
  await ui.act(async () => { button.click(); await settle(); });
}
const field = () => container.querySelector('.markdown-editor textarea');
async function input(value) {
  await ui.act(async () => {
    Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set.call(field(), value);
    field().dispatchEvent(new window.Event('input', { bubbles: true })); await settle();
  });
}
async function event(type, options = {}) {
  await ui.act(async () => {
    field().dispatchEvent(type.startsWith('composition') ? new window.CompositionEvent(type, { bubbles: true, ...options }) : new window.KeyboardEvent(type, { bubbles: true, cancelable: true, ...options })); await settle();
  });
}
async function reload() {
  await ui.act(async () => root.unmount()); root = ui.createRoot(container); await render();
}
test('corpus contains exactly 40 distinct fixtures', () => { assert.equal(fixtures.length, 40); assert.equal(new Set(fixtures.map(([id]) => id)).size, 40); });
for (const [id, raw, selector, expected] of fixtures) test(`raw + HTML round trip: ${id}`, async () => {
  saved.note = raw; await render(); await click('Chỉnh sửa');
  assert.equal(sessionStorage.length, 0, 'opening does not create a draft or mutate raw');
  await click('Soạn + Xem trước');
  assert.equal(container.querySelector(`.markdown-editor-preview ${selector}`)?.textContent, expected);
  await click('Đọc bản nháp'); await click('Soạn thảo');
  const suffix = '\n\nSửa chủ ý ✓';
  await input(field().value + suffix);
  await click('Lưu thay đổi');
  const newline = raw.match(/\r\n|\r|\n/)?.[0] ?? '\n';
  const intended = raw + suffix.replace(/\n/g, newline);
  assert.deepEqual(Buffer.from(saved.note), Buffer.from(intended), 'unexpected_changed_bytes = 0');
  const patches = requests.filter((request) => request.method === 'PATCH');
  assert.equal(patches.length, 1); assert.deepEqual(JSON.parse(patches[0].body), { note: intended });
  assert.equal(patches[0].headers.get('X-CSRFToken'), 'fixture-csrf');
  assert.equal(sessionStorage.length, 0);
  await reload();
  assert.equal(container.querySelector('.raw-knowledge pre').textContent, intended);
  assert.equal(container.querySelector(`.knowledge-text ${selector}`)?.textContent, expected);
  assert.equal(container.querySelectorAll('script,img,iframe').length, 0);
  assert.equal(container.querySelectorAll('a[href^="javascript:"],a[href^="data:"]').length, 0);
  assert.ok(requests.every(({ method, path }) => !method || method === 'PATCH' && path.endsWith('/items/kt115')), 'no capture/asset/Drive writes');
});
test('failed network save retains draft, survives remount, retries once and clears recovery', async () => {
  await render(); await click('Chỉnh sửa'); await input('Bản nháp chưa gửi'); failSave = true;
  await click('Lưu thay đổi'); assert.equal(field().value, 'Bản nháp chưa gửi');
  await reload(); assert.equal(field().value, 'Bản nháp chưa gửi'); assert.match(container.textContent, /Đã khôi phục/);
  failSave = false; await click('Lưu thay đổi'); assert.equal(saved.note, 'Bản nháp chưa gửi'); assert.equal(sessionStorage.length, 0);
});
test('composition blocks submit and shortcuts, then Ctrl+Enter saves committed Vietnamese', async () => {
  await render(); await click('Chỉnh sửa'); await event('compositionstart'); await input('Tiếng Việt');
  await event('keydown', { key: 'Enter', ctrlKey: true, isComposing: true }); await click('Lưu thay đổi');
  assert.equal(requests.filter(({ method }) => method === 'PATCH').length, 0);
  await event('compositionend', { data: 'Việt' });
  await event('keydown', { key: 'ArrowLeft' }); await event('keydown', { key: 'Backspace' });
  assert.equal(field().value, 'Tiếng Việt', 'jsdom dispatch does not emulate native edits');
  await event('keydown', { key: 'Enter', ctrlKey: true }); assert.equal(saved.note, 'Tiếng Việt');
});
test('discard requires explicit choice; beforeunload warns while dirty; expiry removes drafts', async () => {
  await render(); await click('Chỉnh sửa'); await input('Nháp');
  const leaving = new window.Event('beforeunload', { cancelable: true }); window.dispatchEvent(leaving); assert.equal(leaving.defaultPrevented, true);
  await click('Hủy'); assert.ok(field()); await click('Tiếp tục soạn'); assert.equal(field().value, 'Nháp');
  await click('Hủy'); await click('Bỏ bản nháp'); assert.equal(sessionStorage.length, 0); assert.equal(saved.note, 'Gốc');
  await click('Chỉnh sửa'); await input('Riêng tư');
  await ui.act(async () => window.dispatchEvent(new window.Event('session-expired'))); assert.equal(sessionStorage.length, 0);
});
test('observed concurrent edit blocks PATCH and retains draft', async () => {
  await render(); await click('Chỉnh sửa'); await input('Nháp của tôi'); latest = { ...saved, note: 'Sửa ở phiên khác' };
  await click('Lưu thay đổi'); assert.match(container.textContent, /Nội dung đã thay đổi ở phiên khác/); assert.equal(field().value, 'Nháp của tôi');
  assert.equal(requests.filter(({ method }) => method === 'PATCH').length, 0);
});
test('editing in middle preserves mixed newlines and decomposed Unicode around the changed span', () => {
  assert.equal(ui.editRawMarkdown('A\r\nB\nC\rD', 'A\nViệt\nC\nD'), 'A\r\nViệt\nC\rD');
  assert.equal(ui.editRawMarkdown('Tiếng\r\nViệt', 'Tiếng\nViệt!'), 'Tiếng\r\nViệt!');
  assert.equal(ui.editRawMarkdown('a\r\nb', 'a\nb'), 'a\r\nb');
});
test('storage quota failure is visible and the live draft remains saveable', async () => {
  const prototype = window.Storage.prototype, original = prototype.setItem;
  prototype.setItem = () => { throw new window.DOMException('quota', 'QuotaExceededError'); };
  try {
    await render(); await click('Chỉnh sửa'); await input('Nháp còn trong bộ nhớ');
    assert.match(container.querySelector('form').textContent, /Không lưu được bản nháp trong tab/);
    await click('Lưu thay đổi'); assert.equal(saved.note, 'Nháp còn trong bộ nhớ');
  } finally { prototype.setItem = original; }
});
