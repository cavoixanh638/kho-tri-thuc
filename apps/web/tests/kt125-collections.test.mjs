import assert from 'node:assert/strict';
import { before, after, beforeEach, afterEach, test } from 'node:test';
import { createServer } from 'vite';
import { JSDOM, VirtualConsole } from 'jsdom';
import { setImmediate as settle } from 'node:timers/promises';
let server, ui, dom, root, container, calls, rows, collections;
const originalFetch = globalThis.fetch;
const id = '12345678-1234-4567-89ab-123456789abc';
before(async () => {
  dom = new JSDOM('<html><body></body></html>', { url: 'http://127.0.0.1/#/thu-vien', pretendToBeVisual: true, virtualConsole: new VirtualConsole() });
  for (const name of ['window', 'document', 'sessionStorage', 'navigator', 'HTMLElement', 'Element', 'Node', 'Event', 'MouseEvent', 'CustomEvent', 'MutationObserver', 'getComputedStyle'])
    Object.defineProperty(globalThis, name, { value: name === 'getComputedStyle' ? dom.window[name].bind(dom.window) : dom.window[name], configurable: true, writable: true });
  window.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {} });
  globalThis.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
  Object.defineProperty(document, 'fonts', { value: new dom.window.EventTarget(), configurable: true });
  globalThis.requestAnimationFrame = window.requestAnimationFrame.bind(window); globalThis.cancelAnimationFrame = window.cancelAnimationFrame.bind(window);
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom', logLevel: 'silent' });
  ui = await server.ssrLoadModule('/tests/kt125-entry.tsx');
});
beforeEach(() => {
  calls = [];
  rows = [{ item_id: id, kind: 'text', title: 'Bài tổng hợp', note: '# Tiếng Việt', description: '', saved_at: '2026-11-20T00:00:00Z', updated_at: '2026-11-20T00:00:00Z', published_at: null, favorite: true, deleted: false, classification_status: 'pending', original_url: '', assets: [] }];
  collections = [{ id, name: 'Bộ lọc yêu thích', query: ui.emptyCollectionQuery(), view: 'table', version: 1 }];
  globalThis.fetch = async (path, options = {}) => {
    const method = options.method ?? 'GET'; const body = options.body && JSON.parse(options.body);
    calls.push({ path, method, body, csrf: options.headers?.get('X-CSRFToken') });
    if (path.endsWith('/groups')) return Response.json({ topics: [{ id: 1, name: 'Lĩnh vực' }], projects: [], tags: [] });
    if (path.endsWith('/collections/preview')) return Response.json({ results: rows, count: rows.length, next_offset: null });
    if (path.includes('/items?')) return Response.json({ results: rows, count: rows.length, next_offset: null });
    if (path.endsWith('/collections') && method === 'GET') return Response.json({ results: collections });
    if (path.endsWith('/collections') && method === 'POST') return Response.json({ ...body, id, version: 1 }, { status: 201 });
    if (path.endsWith('/collections/' + id)) {
      if (method === 'PATCH') { collections[0] = { ...body, id, version: 2 }; delete collections[0].expected_version; }
      if (method === 'DELETE') return Response.json({ state: 'deleted' });
      return Response.json(collections[0]);
    }
    return Response.json({}, { status: 404 });
  };
  container = document.createElement('div'); document.body.append(container); root = ui.createRoot(container);
});
afterEach(async () => { await ui.act(async () => root.unmount()); container.remove(); });
after(async () => { globalThis.fetch = originalFetch; await server.close(); dom.window.close(); });
async function render(component, props = {}) { await ui.act(async () => { root.render(ui.createElement(ui.MantineProvider, null, ui.createElement(component, props))); await settle(); }); }
async function click(text) { const button = [...container.querySelectorAll('button')].find((entry) => entry.textContent === text); assert.ok(button, text); await ui.act(async () => { button.click(); await settle(); }); }
async function input(label, value) {
  const text = [...container.querySelectorAll('label')].find((entry) => entry.textContent.startsWith(label));
  const field = text?.htmlFor ? document.getElementById(text.htmlFor) : text?.querySelector('input');
  assert.ok(field, label);
  await ui.act(async () => { Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(field, value); field.dispatchEvent(new Event('input', { bubbles: true })); await settle(); });
}
test('sidebar clearly distinguishes a dynamic saved filter from folders', async () => {
  await render(ui.SavedCollectionsPanel);
  assert.match(container.textContent, /Bộ sưu tập thông minh/);
  assert.match(container.textContent, /không di chuyển hay nhân bản/);
  assert.equal(container.querySelector('a').getAttribute('href'), '#/thu-vien?collection=' + id);
  assert.equal(calls.filter((entry) => entry.method !== 'GET').length, 0);
});
test('URL saved collection UUID survives reload and hostile values are rejected', () => {
  assert.equal(ui.collectionIdFromHash(ui.collectionHref(id)), id);
  assert.equal(ui.collectionIdFromHash('#/thu-vien?collection=new'), 'new');
  for (const value of ['javascript:alert(1)', '../private', 'not-uuid']) assert.equal(ui.collectionIdFromHash('#/thu-vien?collection=' + value), undefined);
});
test('create form preview makes no Item or collection write; explicit save includes CSRF and view', async () => {
  await render(ui.SavedCollectionScreen, { csrf: 'test-csrf', id: 'new' });
  await input('Tên bộ sưu tập', 'Nghiên cứu sách');
  await input('Từ khóa trong tri thức', 'Tiếng Việt');
  await click('Xem trước kết quả');
  assert.equal(calls.filter((entry) => entry.method !== 'GET').length, 1);
  assert.equal(calls.find((entry) => entry.path.endsWith('/preview')).body.query.q, 'Tiếng Việt');
  await click('Lưu bộ sưu tập');
  const mutation = calls.find((entry) => entry.method === 'POST' && entry.path.endsWith('/collections'));
  assert.equal(mutation.csrf, 'test-csrf'); assert.equal(mutation.body.name, 'Nghiên cứu sách');
  assert.equal(mutation.body.view, 'list');
  assert.equal(calls.some((entry) => entry.path.endsWith('/captures') || entry.path.includes('/organization')), false);
});
test('saved table query reloads results and deleting only removes collection', async () => {
  await render(ui.SavedCollectionScreen, { csrf: 'csrf', id });
  assert.ok(container.querySelector('table'));
  assert.equal(container.querySelector('[data-library-item]').dataset.libraryItem, id);
  await click('Xóa bộ sưu tập');
  assert.match(container.textContent, /giữ tất cả bài và nhóm/);
  await click('Xác nhận xóa bộ lọc');
  assert.equal(calls.filter((entry) => entry.method === 'DELETE').length, 1);
  assert.equal(calls.find((entry) => entry.method === 'DELETE').path, '/api/v1/collections/' + id);
});
test('editing saved conditions sends expected version and does not mutate query on preview', async () => {
  await render(ui.SavedCollectionScreen, { csrf: 'csrf', id });
  await click('Xem điều kiện / chỉnh sửa'); await input('Tên bộ sưu tập', 'Tên mới');
  await click('Lưu bộ sưu tập');
  const patch = calls.find((entry) => entry.method === 'PATCH');
  assert.equal(patch.body.expected_version, 1); assert.equal(patch.body.name, 'Tên mới'); assert.equal(patch.body.view, 'table');
});
test('all four saved views consume identical item IDs', async () => {
  for (const mode of ['list', 'table', 'card', 'timeline']) {
    collections[0].view = mode;
    await render(ui.SavedCollectionScreen, { csrf: 'csrf', id });
    const matches = [...container.querySelectorAll('[data-library-item]')].map((entry) => entry.dataset.libraryItem);
    assert.deepEqual(matches, [id]);
    await ui.act(async () => { root.unmount(); }); root = ui.createRoot(container);
  }
});
test('property chips expose actual fields without invented author/custom schema', () => {
  const html = ui.renderToStaticMarkup(ui.createElement(ui.PropertyChips, { item: rows[0], groups: [{ kind: 'Nhãn', name: 'Sách' }] }));
  assert.match(html, /Nhãn: Sách/); assert.match(html, /Yêu thích/); assert.doesNotMatch(html, /Tác giả|Supertag/);
});
