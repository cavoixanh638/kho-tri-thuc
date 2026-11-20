import assert from 'node:assert/strict';
import { before, after, beforeEach, afterEach, test } from 'node:test';
import { createServer } from 'vite';
import { JSDOM, VirtualConsole } from 'jsdom';
import { setImmediate as settle } from 'node:timers/promises';

let server, ui, dom, root, container, current, patches, race;
const originalFetch = globalThis.fetch;
const response = (data, status = 200) => new Response(JSON.stringify(data), { status });
before(async () => {
  dom = new JSDOM('<html><body></body></html>', { url: 'http://127.0.0.1/', pretendToBeVisual: true, virtualConsole: new VirtualConsole() });
  for (const name of ['window', 'document', 'sessionStorage', 'navigator', 'HTMLElement', 'Element', 'Node', 'Event', 'MouseEvent', 'CustomEvent', 'MutationObserver', 'getComputedStyle']) Object.defineProperty(globalThis, name, { value: name === 'getComputedStyle' ? dom.window[name].bind(dom.window) : dom.window[name], configurable: true, writable: true });
  window.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
  globalThis.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
  Object.defineProperty(document, 'fonts', { value: new dom.window.EventTarget(), configurable: true });
  globalThis.requestAnimationFrame = window.requestAnimationFrame.bind(window);
  globalThis.cancelAnimationFrame = window.cancelAnimationFrame.bind(window);
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom', logLevel: 'silent' });
  ui = await server.ssrLoadModule('/tests/notes-ux-entry.tsx');
});
beforeEach(() => {
  sessionStorage.clear(); patches = []; race = false;
  current = { item_id: 'fixture-contract', kind: 'text', title: 'Phiên bản', description: '', note: 'Gốc\r\n', user_edit_version: 7,
    saved_at: '2026-11-20T00:00:00Z', updated_at: '2026-11-20T00:00:00Z', published_at: null, favorite: false, deleted: false,
    classification_status: 'unclassified', original_url: '', source_fetch: 'not_applicable', content_extract: 'done', asset_storage: 'not_applicable', assets: [] };
  container = document.createElement('div'); document.body.append(container); root = ui.createRoot(container);
  globalThis.fetch = async (path, options = {}) => {
    if (path.endsWith('/items/fixture-contract')) {
      if (options.method === 'PATCH') {
        const body = JSON.parse(options.body); patches.push(body);
        if (race) { current = { ...current, note: 'Phiên khác vừa lưu', user_edit_version: 8 }; return response({ code: 'edit_conflict' }, 409); }
        current = { ...current, ...body }; delete current.expected_edit_version;
      }
      return response(current);
    }
    if (path.includes('/organization')) return response({ topics: [], projects: [], tags: [] });
    return response({ results: [], next_offset: null });
  };
});
afterEach(async () => { await ui.act(async () => root.unmount()); container.remove(); });
after(async () => { globalThis.fetch = originalFetch; await server.close(); dom.window.close(); });
async function render(component = ui.ItemScreen, props = { id: 'fixture-contract', csrf: 'fixture' }) {
  await ui.act(async () => { root.render(ui.createElement(ui.MantineProvider, null, ui.createElement(component, props))); await settle(); });
}
async function click(label) {
  const button = [...container.querySelectorAll('button')].find((button) => button.textContent === label); assert.ok(button, label);
  await ui.act(async () => { button.click(); await settle(); });
}
async function edit() {
  await click('Chỉnh sửa'); const field = container.querySelector('.markdown-editor textarea');
  await ui.act(async () => { Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set.call(field, 'Nháp tiếng Việt Tiếng\n'); field.dispatchEvent(new window.Event('input', { bubbles: true })); await settle(); });
}
test('409 after clean preflight retains draft, raw note and recovery storage', async () => {
  await render(); await edit(); race = true; await click('Lưu thay đổi');
  assert.deepEqual(patches, [{ note: 'Nháp tiếng Việt Tiếng\r\n', expected_edit_version: 7 }]);
  assert.match(container.querySelector('form').textContent, /Nội dung đã thay đổi ở phiên khác/);
  assert.equal(container.querySelector('.markdown-editor textarea').value, 'Nháp tiếng Việt Tiếng\n');
  assert.ok(sessionStorage.getItem('kt-markdown-draft-v1:fixture-contract').includes('Nháp tiếng Việt'));
  assert.equal(current.note, 'Phiên khác vừa lưu');
});
test('successful save sends real version zero and clears the draft', async () => {
  current.user_edit_version = 0; await render(); await edit(); await click('Lưu thay đổi');
  assert.equal(patches[0].expected_edit_version, 0); assert.equal(sessionStorage.length, 0);
});
test('old server without version uses legacy PATCH without a fake precondition', async () => {
  delete current.user_edit_version; await render(); await edit(); await click('Lưu thay đổi');
  assert.equal(Object.hasOwn(patches[0], 'expected_edit_version'), false); assert.equal(sessionStorage.length, 0);
});
const id = '12345678-1234-4567-89ab-123456789abc';
test('strict UUID internal note links stay same-tab while HTTP links keep safe external behavior', async () => {
  await render(ui.KnowledgeText, { text: `[Mục liên quan](#/muc/${id})\n\n[Nguồn](https://example.org)` });
  const [internal, external] = container.querySelectorAll('a');
  assert.equal(internal.getAttribute('href'), `#/muc/${id}`); assert.equal(internal.getAttribute('target'), null); assert.equal(internal.getAttribute('rel'), null);
  assert.equal(external.target, '_blank'); assert.equal(external.rel, 'noopener noreferrer');
  internal.click(); await new Promise((resolve) => setTimeout(resolve, 25)); assert.equal(window.location.hash, `#/muc/${id}`);
});
test('only exact internal item hrefs pass; internal images and all active/relative variants stay inert', async () => {
  const bad = [`#/muc/${id}/extra`, `#/muc/${id}?x=1`, '#/muc/not-a-uuid', '#/thu-vien', `/muc/${id}`, `//evil.invalid/#/muc/${id}`, `#/muc/%31${id.slice(1)}`, 'javascript:alert%281%29', 'data:text/html;base64,eA=='];
  await render(ui.KnowledgeText, { text: bad.map((url, index) => `[bad${index}](${url})`).join('\n\n') + `\n\n![internal image](#/muc/${id})\n\n![safe image](https://example.org/image.png)\n\n<script>alert(1)</script>` });
  const links = [...container.querySelectorAll('a')];
  assert.equal(links.length, 1); assert.equal(links[0].href, 'https://example.org/image.png');
  assert.equal(container.querySelectorAll('script,img,iframe').length, 0);
  assert.ok(container.textContent.includes('internal image'));
});
