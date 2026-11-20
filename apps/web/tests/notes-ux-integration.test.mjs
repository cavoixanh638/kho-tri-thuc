import assert from 'node:assert/strict';
import { before, after, beforeEach, afterEach, test } from 'node:test';
import { createServer } from 'vite';
import { JSDOM, VirtualConsole } from 'jsdom';
import { setImmediate as settle } from 'node:timers/promises';

let server, ui, dom, root, container, current, patches, conflict, requests;
const originalFetch = globalThis.fetch;
const id = '12345678-1234-4567-89ab-123456789abc';
const assetId = '22345678-1234-4567-89ab-123456789abc';
const raw = '# Gốc Tiếng Việt\r\n\r\nGiữ **nguyên văn**  \r\n';
before(async () => {
  dom = new JSDOM('<html><body></body></html>', { url: 'http://127.0.0.1/', pretendToBeVisual: true, virtualConsole: new VirtualConsole() });
  for (const name of ['window', 'document', 'sessionStorage', 'navigator', 'HTMLElement', 'Element', 'Node', 'Event', 'MouseEvent', 'CustomEvent', 'MutationObserver', 'getComputedStyle'])
    Object.defineProperty(globalThis, name, { value: name === 'getComputedStyle' ? dom.window[name].bind(dom.window) : dom.window[name], configurable: true, writable: true });
  window.matchMedia = () => ({ matches: true, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
  window.HTMLElement.prototype.scrollIntoView = function () { this.dataset.scrolled = 'true'; };
  globalThis.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
  Object.defineProperty(document, 'fonts', { value: new dom.window.EventTarget(), configurable: true });
  globalThis.requestAnimationFrame = window.requestAnimationFrame.bind(window);
  globalThis.cancelAnimationFrame = window.cancelAnimationFrame.bind(window);
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom', logLevel: 'silent' });
  ui = await server.ssrLoadModule('/tests/notes-ux-integration-entry.tsx');
});
beforeEach(() => {
  sessionStorage.clear(); patches = []; conflict = false; requests = [];
  current = { item_id: id, kind: 'text', title: 'Ghi chép tiếng Việt', description: '', note: raw, user_edit_version: 0,
    saved_at: '2026-11-20T00:00:00Z', updated_at: '2026-11-20T00:00:00Z', published_at: null, favorite: false, deleted: false,
    classification_status: 'unclassified', original_url: '', source_fetch: 'not_applicable', content_extract: 'done', asset_storage: 'not_applicable', assets: [] };
  container = document.createElement('div'); document.body.append(container); root = ui.createRoot(container);
  globalThis.fetch = async (path, options = {}) => {
    requests.push([path, options.method ?? 'GET']);
    if (path.endsWith('/items/' + id)) {
      if (options.method === 'PATCH') {
        const body = JSON.parse(options.body); patches.push(body);
        if (conflict) return Response.json({ code: 'edit_conflict' }, { status: 409 });
        assert.equal(body.expected_edit_version, current.user_edit_version);
        const { expected_edit_version, ...fields } = body;
        current = { ...current, ...fields, user_edit_version: expected_edit_version + 1 };
      }
      return Response.json(current);
    }
    if (path.includes('/suggestions/capabilities')) return Response.json({ enabled: false, provider_configured: false });
    if (path.includes('/organization')) return Response.json({ topics: [], projects: [], tags: [] });
    if (path.endsWith('/related')) return Response.json({ results: [], evidence: { sources: [], unassociated_parts: [], truncated: false,
      assets: current.assets.map((asset) => ({ ...asset, content_version: 1, parts: [] })) } });
    return Response.json({ results: [], next_offset: null });
  };
});
afterEach(async () => { await ui.act(async () => root.unmount()); container.remove(); });
after(async () => { globalThis.fetch = originalFetch; await server.close(); dom.window.close(); });
async function render() {
  await ui.act(async () => { root.render(ui.createElement(ui.MantineProvider, null, ui.createElement(ui.ItemScreen, { id, csrf: 'fixture' }))); await settle(); });
}
async function click(label) {
  const button = [...container.querySelectorAll('button')].find((button) => button.textContent === label || button.querySelector('strong')?.textContent === label);
  assert.ok(button, label);
  await ui.act(async () => { button.click(); await settle(); });
}
for (const label of ['Bài học', 'Sách / Chương', 'Cuộc họp', 'Video nguồn']) {
  test('integrated editor selects, appends and saves optional template: ' + label, async () => {
    await render(); await click('Chỉnh sửa'); await click(label);
    assert.equal(current.note, raw); assert.equal(patches.length, 0);
    await click('Thêm mẫu vào cuối');
    const savedDraft = JSON.parse(sessionStorage.getItem('kt-markdown-draft-v1:' + id));
    assert.ok(savedDraft.draft.note.startsWith(raw + '\r\n\r\n'));
    assert.equal(current.note, raw); assert.equal(patches.length, 0);
    await click('Lưu thay đổi');
    assert.equal(current.note, savedDraft.draft.note);
    assert.equal(current.item_id, id); assert.equal(current.user_edit_version, 1);
    assert.equal(patches.length, 1); assert.equal(sessionStorage.length, 0);
    assert.equal(requests.filter(([path, method]) => method !== 'GET' && !path.endsWith('/items/' + id)).length, 0);
    await click('Chỉnh sửa');
    assert.equal(container.querySelector('.markdown-editor textarea').value, current.note.replaceAll('\r\n', '\n'));
  });
}
test('template cancellation and failed atomic save preserve original and recovery draft', async () => {
  await render(); await click('Chỉnh sửa'); await click('Bài học'); await click('Thêm mẫu vào cuối');
  conflict = true; await click('Lưu thay đổi');
  assert.equal(current.note, raw);
  assert.match(container.querySelector('form').textContent, /Nội dung đã thay đổi/);
  assert.ok(sessionStorage.getItem('kt-markdown-draft-v1:' + id).includes('# Bài học'));
  await click('Hủy'); await click('Bỏ bản nháp');
  assert.equal(sessionStorage.length, 0); assert.equal(current.note, raw);
  assert.equal(container.querySelector('.markdown-editor'), null);
});
test('related source action focuses its exact attached illustration without Drive navigation', async () => {
  current.assets = [{ asset_id: assetId, filename: 'Minh họa tổng hợp.mp4', mime: 'video/mp4', status: 'pending' }];
  await render();
  const action = [...container.querySelectorAll('.related-source-card button')].find((button) => button.textContent === 'Mở tệp');
  assert.ok(action);
  await ui.act(async () => { action.click(); await settle(); });
  const illustration = document.getElementById('item-asset-' + assetId);
  assert.equal(illustration.closest('details').open, true);
  assert.equal(document.activeElement, illustration);
  assert.equal(illustration.dataset.scrolled, 'true');
  assert.equal(requests.some(([path]) => path.endsWith('/open')), false);
});
