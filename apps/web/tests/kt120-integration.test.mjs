import assert from 'node:assert/strict';
import { before, after, beforeEach, afterEach, test } from 'node:test';
import { setImmediate as settle } from 'node:timers/promises';
import { JSDOM, VirtualConsole } from 'jsdom';
import { createServer } from 'vite';

let ui, server, dom, root, container, item, calls, updates, busyStates, behavior;
const originalFetch = globalThis.fetch;
const json = (value, status = 200) => new Response(JSON.stringify(value), { status });
const capability = (enabled = true) => ({ enabled, provider_configured: false, mode: 'manual_review_poc' });
const proposal = () => ({ item_id: item.item_id, source_version: 'source-v1', base_edit_version: item.user_edit_version,
  before: item.note, after: 'Đề xuất e\u0302\u0301\r\n', receipt: 'signed', expires_in: 900,
  provenance: { provider: 'none', model: 'none', method: 'user_supplied_poc', prompt_version: 'not_run' } });

before(async () => {
  dom = new JSDOM('<html><body></body></html>', { url: 'http://127.0.0.1/', pretendToBeVisual: true, virtualConsole: new VirtualConsole() });
  for (const name of ['window', 'document', 'navigator', 'HTMLElement', 'Element', 'Node', 'Event', 'MouseEvent', 'CustomEvent', 'MutationObserver', 'getComputedStyle']) {
    Object.defineProperty(globalThis, name, { value: name === 'getComputedStyle' ? dom.window[name].bind(dom.window) : dom.window[name], configurable: true, writable: true });
  }
  window.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
  globalThis.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
  Object.defineProperty(document, 'fonts', { value: new dom.window.EventTarget(), configurable: true });
  globalThis.requestAnimationFrame = window.requestAnimationFrame.bind(window);
  globalThis.cancelAnimationFrame = window.cancelAnimationFrame.bind(window);
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom', logLevel: 'silent' });
  ui = await server.ssrLoadModule('/tests/kt120-integration-entry.tsx');
});
beforeEach(() => {
  item = { item_id: '00000000-0000-4000-8000-000000000120', kind: 'text', note: 'Bản gốc e\u0302\u0301\r\n', title: '', user_edit_version: 2, deleted: false, assets: [] };
  calls = []; updates = []; busyStates = []; behavior = undefined;
  globalThis.fetch = async (url, options) => {
    calls.push({ url, body: options.body && JSON.parse(options.body), method: options.method });
    if (behavior) { const response = await behavior(url, options); if (response) return response; }
    if (url.endsWith('/capabilities')) return json(capability());
    if (url.endsWith('/preview')) return json(proposal());
    if (url.endsWith('/accept')) return json({ note: proposal().after, edit_version: 3, source_version: 'source-v1', undo_receipt: 'undo-signed', updated_at: '2026-11-20T12:00:01Z' });
    if (url.endsWith('/undo')) return json({ note: 'Bản gốc e\u0302\u0301\r\n', edit_version: 4, source_version: 'source-v1', undo_receipt: '', updated_at: '2026-11-20T12:00:02Z' });
    return json({ state: 'rejected', writes: 0 });
  };
  container = document.createElement('div'); document.body.append(container); root = ui.createRoot(container);
});
afterEach(async () => { await ui.act(async () => root.unmount()); container.remove(); });
after(async () => { globalThis.fetch = originalFetch; await server.close(); dom.window.close(); });

async function render(extra = {}) {
  await ui.act(async () => { root.render(ui.createElement(ui.MantineProvider, null, ui.createElement(ui.ItemSuggestionPanel, {
    item, csrf: 'fixture-csrf', editing: false, draftDirty: false, onUpdated: (value) => { updates.push(value); item = value; }, onBusyChange: (value) => busyStates.push(value), ...extra,
  }))); await settle(); });
}
const button = (text) => [...container.querySelectorAll('button')].find((node) => node.textContent === text);
async function click(text) { assert.ok(button(text), text); await ui.act(async () => { button(text).click(); await settle(); }); }
async function input(text) {
  const field = container.querySelector('textarea'); assert.ok(field);
  await ui.act(async () => { Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set.call(field, text); field.dispatchEvent(new window.Event('input', { bubbles: true })); await settle(); });
}
async function preview() { await render(); await input('Đề xuất e\u0302\u0301\n'); await click('Xem khác biệt'); }

test('disabled capability hides all proposal UI and makes no write request', async () => {
  behavior = async () => json(capability(false)); await render();
  assert.equal(container.querySelector('details, textarea, button'), null); assert.equal(calls.length, 1); assert.equal(calls[0].method, undefined); assert.equal(updates.length, 0);
});
test('manual preview sends only explicit text after click and leaves host unchanged', async () => {
  await render(); assert.equal(calls.length, 1); assert.match(container.textContent, /Chưa kết nối AI/);
  await input('Đề xuất e\u0302\u0301\n'); assert.equal(calls.length, 1); await click('Xem khác biệt');
  assert.deepEqual(calls[1].body, { proposed_note: 'Đề xuất e\u0302\u0301\n' });
  assert.equal(updates.length, 0); assert.match(container.textContent, /Duyệt đề xuất/);
  await click('Từ chối'); assert.equal(updates.length, 0); assert.equal(item.user_edit_version, 2);
});
test('accept and undo ACK synchronize exact note/edit version without changing identity or assets', async () => {
  const original = { ...item }; await preview(); await click('Chấp nhận');
  assert.equal(updates.length, 1); assert.equal(item.note, 'Đề xuất e\u0302\u0301\r\n'); assert.equal(item.user_edit_version, 3);
  assert.equal(item.updated_at, '2026-11-20T12:00:01Z');
  assert.equal(item.item_id, original.item_id); assert.deepEqual(item.assets, original.assets);
  await render(); await click('Hoàn tác đề xuất');
  assert.equal(item.note, original.note); assert.equal(item.user_edit_version, 4); assert.deepEqual(busyStates, [true, false, true, false]);
  assert.equal(item.updated_at, '2026-11-20T12:00:02Z');
  assert.equal(calls.find((call) => call.url.endsWith('/undo')).body.receipt, 'undo-signed');
});
test('editing or dirty draft disables proposal acceptance and undo', async () => {
  await preview(); await render({ editing: true }); assert.equal(button('Chấp nhận').disabled, true); assert.equal(container.querySelector('textarea').disabled, true);
  await render({ draftDirty: true }); assert.equal(button('Chấp nhận').disabled, true); assert.equal(updates.length, 0);
  await render(); await click('Chấp nhận'); await render({ editing: true }); assert.equal(button('Hoàn tác đề xuất').disabled, true);
});
test('409 and 503 preserve manual input and do not update host note', async () => {
  for (const status of [409, 503]) {
    await preview(); behavior = async (url) => url.endsWith('/accept') ? json({}, status) : undefined;
    await click('Chấp nhận'); assert.equal(updates.length, 0); assert.equal(item.user_edit_version, 2);
    assert.equal(container.querySelector('textarea').value, 'Đề xuất e\u0302\u0301\n'); assert.ok(container.querySelector('[role="alert"]'));
  }
});
test('pending accept locks proposal replacement and duplicate clicks', async () => {
  await preview(); let resolve; behavior = async (url) => url.endsWith('/accept') ? new Promise((done) => { resolve = () => done(json({ note: 'Đã duyệt', edit_version: 3, source_version: 'source-v1', undo_receipt: 'u' })); }) : undefined;
  await click('Chấp nhận'); assert.equal(button('Xem khác biệt').disabled, true); assert.equal(button('Dùng văn bản hiện tại').disabled, true);
  await click('Chấp nhận'); assert.equal(calls.filter((call) => call.url.endsWith('/accept')).length, 1);
  await ui.act(async () => { resolve(); await settle(); }); assert.equal(item.note, 'Đã duyệt'); assert.deepEqual(busyStates, [true, false]);
});
test('a late preview from another item cannot appear in the next item', async () => {
  await render(); let resolve; const old = proposal(); behavior = async (url) => url.endsWith('/preview') ? new Promise((done) => { resolve = () => done(json(old)); }) : undefined;
  await input('Đề xuất'); await click('Xem khác biệt'); item = { ...item, item_id: '00000000-0000-4000-8000-000000000121', note: 'Bài khác' }; await render();
  await ui.act(async () => { resolve(); await settle(); }); assert.equal(container.querySelector('.ai-suggestion-review'), null); assert.equal(container.querySelector('textarea').value, 'Bài khác'); assert.equal(updates.length, 0);
});
test('a newer host version is preserved when a delayed acceptance ACK arrives', async () => {
  await preview(); let resolve; behavior = async (url) => url.endsWith('/accept') ? new Promise((done) => { resolve = () => done(json({ note: 'ACK cũ', edit_version: 3, source_version: 'source-v1', undo_receipt: 'u' })); }) : undefined;
  await click('Chấp nhận'); item = { ...item, note: 'Bản mới hơn', user_edit_version: 5 }; await render();
  await ui.act(async () => { resolve(); await settle(); }); assert.equal(updates.length, 0); assert.equal(item.note, 'Bản mới hơn'); assert.equal(item.user_edit_version, 5);
});
