import assert from 'node:assert/strict';
import { before, after, beforeEach, afterEach, test } from 'node:test';
import { createServer } from 'vite';
import { JSDOM, VirtualConsole } from 'jsdom';
import { setImmediate as settle } from 'node:timers/promises';

let server, ui, dom, root, container, calls, proposals;
const originalFetch = globalThis.fetch;
const id = '12345678-1234-4567-89ab-123456789abc';
before(async () => {
  dom = new JSDOM('<html><body></body></html>', { url: 'http://127.0.0.1/', pretendToBeVisual: true, virtualConsole: new VirtualConsole() });
  for (const name of ['window', 'document', 'navigator', 'HTMLElement', 'Element', 'Node', 'Event', 'MouseEvent', 'CustomEvent', 'MutationObserver', 'getComputedStyle'])
    Object.defineProperty(globalThis, name, { value: name === 'getComputedStyle' ? dom.window[name].bind(dom.window) : dom.window[name], configurable: true, writable: true });
  window.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {} });
  globalThis.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
  Object.defineProperty(document, 'fonts', { value: new dom.window.EventTarget(), configurable: true });
  globalThis.requestAnimationFrame = window.requestAnimationFrame.bind(window);
  globalThis.cancelAnimationFrame = window.cancelAnimationFrame.bind(window);
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom', logLevel: 'silent' });
  ui = await server.ssrLoadModule('/tests/p12-org-entry.tsx');
});
beforeEach(() => {
  calls = [];
  proposals = [{
    kind: 'topic', group_id: 3, group_name: 'Quản lý dự án',
    field: 'ghi chú', excerpt: 'Chủ đề: Quản lý dự án',
    processor: 'user', processor_version: '', confidence: 1,
    method_version: 'kt129-catalog-rule-review-v1',
    source_version: 'abcdefabcdefabcde', receipt: 'signed-proposal',
  }];
  globalThis.fetch = async (path, options = {}) => {
    const method = options.method ?? 'GET';
    const body = options.body ? JSON.parse(options.body) : undefined;
    calls.push({ path, method, body, csrf: options.headers?.get('X-CSRFToken') });
    if (method === 'GET') return Response.json({
      evidence_status: 'available', current: [], proposals,
      confidence_note: 'Điểm quy tắc, không phải xác suất.',
    });
    if (method === 'POST') {
      proposals = [];
      return Response.json({ state: 'accepted', writes: 1, undo_receipt: 'signed-undo' });
    }
    return Response.json({}, { status: 404 });
  };
  container = document.createElement('div');
  document.body.append(container);
  root = ui.createRoot(container);
});
afterEach(async () => { await ui.act(async () => root.unmount()); container.remove(); });
after(async () => { globalThis.fetch = originalFetch; await server.close(); dom.window.close(); });
async function render() {
  await ui.act(async () => {
    root.render(ui.createElement(ui.MantineProvider, null,
      ui.createElement(ui.OrganizationReview, { id, csrf: 'csrf-p12' })));
    await settle();
  });
}
async function click(label) {
  const button = [...container.querySelectorAll('button')].find((node) => node.textContent === label);
  assert.ok(button, label);
  await ui.act(async () => { button.click(); await settle(); });
}
test('review shows evidence and never writes on load', async () => {
  await render();
  assert.match(container.textContent, /Chủ đề: Quản lý dự án/);
  assert.match(container.textContent, /Chủ đề: Quản lý dự án/);
  assert.match(container.textContent, /Điểm quy tắc/);
  assert.equal(calls.some((entry) => entry.method === 'POST'), false);
});
test('explicit acceptance sends scoped receipt and CSRF; undo is available', async () => {
  await render();
  await click('Áp dụng');
  const action = calls.find((entry) => entry.method === 'POST');
  assert.equal(action.path, '/api/v1/items/' + id + '/organization-review/accept');
  assert.deepEqual(action.body, { receipt: 'signed-proposal' });
  assert.equal(action.csrf, 'csrf-p12');
  assert.match(container.textContent, /Hoàn tác/);
  await click('Hoàn tác');
  const undo = calls.filter((entry) => entry.method === 'POST')[1];
  assert.equal(undo.path, '/api/v1/items/' + id + '/organization-review/undo');
  assert.deepEqual(undo.body, { receipt: 'signed-undo' });
});
