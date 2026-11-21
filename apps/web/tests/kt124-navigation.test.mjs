import assert from 'node:assert/strict';
import { before, after, beforeEach, afterEach, test } from 'node:test';
import { createServer } from 'vite';
import { JSDOM, VirtualConsole } from 'jsdom';
import { setTimeout as delay } from 'node:timers/promises';
let server, ui, dom, root, container, calls;
const originalFetch = globalThis.fetch;
const target = { item_id: '12345678-1234-4567-89ab-123456789abc', title: 'Đầu tư trùng tên', saved_at: '2026-11-20T00:00:00Z' };
before(async () => {
  dom = new JSDOM('<html><body></body></html>', { url: 'http://127.0.0.1/', pretendToBeVisual: true, virtualConsole: new VirtualConsole() });
  for (const name of ['window', 'document', 'sessionStorage', 'navigator', 'HTMLElement', 'Element', 'Node', 'Event', 'MouseEvent', 'CustomEvent', 'MutationObserver', 'getComputedStyle'])
    Object.defineProperty(globalThis, name, { value: name === 'getComputedStyle' ? dom.window[name].bind(dom.window) : dom.window[name], configurable: true, writable: true });
  window.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
  window.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
  window.HTMLDialogElement.prototype.close = function () { this.open = false; };
  window.HTMLElement.prototype.scrollIntoView = function () { this.dataset.scrolled = 'yes'; };
  globalThis.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
  globalThis.requestAnimationFrame = window.requestAnimationFrame.bind(window);
  globalThis.cancelAnimationFrame = window.cancelAnimationFrame.bind(window);
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom', logLevel: 'silent' });
  ui = await server.ssrLoadModule('/tests/kt124-entry.tsx');
});
beforeEach(() => {
  calls = [];
  container = document.createElement('div'); document.body.append(container); root = ui.createRoot(container);
  globalThis.fetch = async (path) => {
    calls.push(path);
    return Response.json(path.endsWith('/links') ? { outgoing: [target], unlinked: [{ ...target, item_id: '22345678-1234-4567-89ab-123456789abc', title: 'Chỉ nhắc tên' }] }
      : { items: [target, { ...target, item_id: '22345678-1234-4567-89ab-123456789abc' }], folders: [{ id: 2, name: 'Đầu tư' }], next_offset: null });
  };
});
afterEach(async () => { await ui.act(async () => root.unmount()); container.remove(); });
after(async () => { globalThis.fetch = originalFetch; await server.close(); dom.window.close(); });
async function render(component, props) {
  await ui.act(async () => { root.render(ui.createElement(ui.MantineProvider, null, ui.createElement(component, props))); await delay(10); });
}
async function click(selector) { await ui.act(async () => { container.querySelector(selector).click(); await delay(170); }); }
async function input(selector, value) {
  await ui.act(async () => {
    const field = container.querySelector(selector);
    const proto = field.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, 'value').set.call(field, value); field.setSelectionRange(value.length, value.length);
    field.dispatchEvent(new window.Event('input', { bubbles: true })); await delay(170);
  });
}
async function key(selector, key, options = {}) { await ui.act(async () => { container.querySelector(selector).dispatchEvent(new window.KeyboardEvent('keydown', { key, bubbles: true, cancelable: true, ...options })); await delay(10); }); }
for (let index = 0; index < 30; index++) test('Markdown AST outline preserves Unicode/GFM/code raw ' + index, async () => {
  const raw = '# Tiếng Việt ' + index + '\r\n\r\n## Trùng ế\r\n\r\n### Trùng ế\r\n\r\n#### H4\r\n\r\n##### H5\r\n\r\n###### H6\r\n\r\n~~~md\r\n# Không phải heading\r\n~~~\r\n\r\n[đọc](javascript:alert%281%29)\r\n\r\n<script>bad()</script>';
  const copy = raw;
  await render(ui.KnowledgeText, { text: raw });
  const links = [...container.querySelectorAll('.note-outline a')];
  assert.equal(links.length, 6);
  assert.equal(new Set(links.map((node) => node.getAttribute('href'))).size, 6);
  assert.equal(container.querySelectorAll('script').length, 0);
  assert.equal(raw, copy);
  await ui.act(async () => links[1].click());
  const node = container.querySelector(links[1].getAttribute('href'));
  assert.equal(node.dataset.scrolled, 'yes'); assert.equal(document.activeElement, node);
  assert.equal(window.location.hash, '');
});
test('completion chooses the UUID among identical titles, preserves prefix/newlines and inserts only on explicit Enter', async () => {
  let note = '';
  await render(ui.Editor, { initial: 'Gốc\r\n', onChange: (text) => { note = text; } });
  await input('textarea', 'Gốc\n[[Đầu');
  assert.ok(note.endsWith('[[Đầu')); assert.equal(container.querySelectorAll('[role="option"]').length, 2);
  await key('textarea', 'ArrowDown'); await key('textarea', 'Enter');
  assert.equal(note, 'Gốc\r\n[Đầu tư trùng tên](#/muc/22345678-1234-4567-89ab-123456789abc)');
});
test('fenced/inline/escaped/raw HTML wiki triggers stay inert; malicious UUID cannot insert', () => {
  for (const raw of ['~~~\n[[x', '`code [[x', '\\[[x', '<script>[[x', '    [[x'])
    assert.equal(ui.wikiQuery(raw, raw.length), undefined);
  const raw = '[[x'; const query = ui.wikiQuery(raw, raw.length);
  assert.equal(ui.wikiInsertion(raw, query, { ...target, item_id: 'javascript:evil' }), undefined);
  assert.equal(ui.headingId('ế', 1), ui.headingId('ế', 1));
});
test('palette opens visibly and keyboard triggers 20 commands without stealing IME/text input', async () => {
  const actions = [];
  await render(ui.KnowledgeCommandPalette, { currentItemId: target.item_id, onAction: (action) => actions.push(action) });
  for (let index = 0; index < 20; index++) {
    await click('.knowledge-palette-trigger');
    await input('.knowledge-palette input', 'Tạo ghi chú');
    const options = [...container.querySelectorAll('[role="option"]')];
    assert.ok(options.some((node) => node.textContent.includes('Tạo ghi chú')));
    await ui.act(async () => options.find((node) => node.textContent.includes('Tạo ghi chú')).click());
  }
  assert.equal(actions.length, 20);
  const field = document.createElement('input'); document.body.append(field); field.focus();
  await ui.act(async () => field.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true, isComposing: true })));
  assert.equal(container.querySelector('dialog').open, false);
  await ui.act(async () => field.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true })));
  assert.equal(container.querySelector('dialog').open, false); field.remove();
  await ui.act(async () => window.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true })));
  assert.equal(container.querySelector('dialog').open, true);
  await key('.knowledge-palette input', 'Escape'); assert.equal(container.querySelector('dialog').open, false);
});
test('link context keeps outgoing references separate from unlinked mention candidates', async () => {
  await render(ui.NoteLinkContext, { id: target.item_id });
  assert.match(container.textContent, /Liên kết đi/);
  assert.match(container.textContent, /chỉ là gợi ý/);
  assert.equal(container.querySelectorAll('a').length, 2);
  assert.equal(calls.length, 1);
});
