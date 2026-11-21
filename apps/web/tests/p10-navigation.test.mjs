// P10 independent frontend audit. Source modules are read-only.
import assert from 'node:assert/strict';
import { before, after, beforeEach, afterEach, test } from 'node:test';
import { setTimeout as delay } from 'node:timers/promises';
import { headingId, remarkNoteOutline } from '../src/NoteOutline.ts';
import { wikiInsertion, wikiQuery } from '../src/WikiCompletion.ts';

const A = '12345678-1234-4567-89ab-123456789abc';
const B = '22345678-1234-4567-89ab-123456789abc';
const duplicate = [
  { item_id: A, title: 'Tiêu đề trùng', saved_at: '2026-11-20T08:00:00Z' },
  { item_id: B, title: 'Tiêu đề trùng', saved_at: '2026-11-20T09:00:00Z' },
];

test('30 Unicode headings at H1-H6 have unique stable NFC IDs and preserve AST content', () => {
  const names = Array.from({ length: 30 }, (_, i) => i % 4 === 0 ? 'Tiếng Việt' : 'Mục ' + i + ' — 測試');
  const nodes = names.map((value, i) => ({ type: 'heading', depth: i % 6 + 1, children: [{ type: 'text', value }] }));
  const tree = { type: 'root', children: [{ type: 'code', value: '# not a heading' }, ...nodes] };
  const original = JSON.stringify(nodes.map((node) => [node.depth, node.children[0].value]));
  remarkNoteOutline()(tree);
  assert.equal(tree.children[0].data.hProperties['aria-label'], 'Mục lục trong bài');
  const entries = tree.children[0].children[1].children;
  assert.equal(entries.length, 30);
  assert.equal(new Set(nodes.map((node) => node.data.hProperties.id)).size, 30);
  for (let i = 0; i < nodes.length; i++) {
    assert.equal(entries[i].children[0].children[0].url, '#' + nodes[i].data.hProperties.id);
    assert.equal(entries[i].data.hProperties['data-depth'], i % 6 + 1);
  }
  assert.equal(original, JSON.stringify(nodes.map((node) => [node.depth, node.children[0].value])));
  assert.equal(headingId('Tiếng Việt', 2), headingId('Tiếng Việt', 2));
});

test('duplicate wiki titles select target UUID and preserve raw Markdown', () => {
  const raw = 'Đầu\r\n[[Tiêu đề trùng]]\r\nCuối';
  const found = wikiQuery(raw, raw.indexOf(']]'));
  assert.equal(found.query, 'Tiêu đề trùng');
  const result = wikiInsertion(raw, found, duplicate[1]);
  assert.equal(result.text, 'Đầu\r\n[Tiêu đề trùng](#/muc/' + B + ')\r\nCuối');
  assert.equal(raw, 'Đầu\r\n[[Tiêu đề trùng]]\r\nCuối');
  assert.equal(wikiInsertion(raw, found, { item_id: 'javascript:evil', title: 'Bad' }), undefined);
  const sanitized = wikiInsertion('[[x', wikiQuery('[[x', 3), { item_id: A, title: 'Tên [evil]<script>' });
  assert.ok(sanitized.text.includes('](#/muc/' + A + ')'));
  assert.ok(!sanitized.text.includes('<script>'));
});

test('fenced, escaped, indented, HTML and code-only wiki triggers are inert', () => {
  const tick = String.fromCharCode(96);
  const invalid = ['~~~\n[[x', tick.repeat(3) + '\n[[x', tick + 'code [[x',
    '\\[[x', '<script>[[x', '    [[x', '\t[[x', '> [[x'];
  for (const raw of invalid) assert.equal(wikiQuery(raw, raw.length), undefined, raw);
  for (const raw of ['[[', 'Lời mở [[tên', 'Dòng 1\n[[hồ sơ']) {
    assert.equal(wikiQuery(raw, raw.length).end, raw.length);
  }
});

let dom, server, ui, unavailable, root, container;
const originalFetch = globalThis.fetch;
before(async () => {
  try {
    const [{ createServer }, { JSDOM, VirtualConsole }] = await Promise.all([import('vite'), import('jsdom')]);
    dom = new JSDOM('<html><body></body></html>', {
      url: 'http://127.0.0.1/', pretendToBeVisual: true, virtualConsole: new VirtualConsole(),
    });
    for (const name of ['window', 'document', 'sessionStorage', 'navigator', 'HTMLElement',
      'Element', 'Node', 'Event', 'MouseEvent', 'CustomEvent', 'MutationObserver', 'getComputedStyle']) {
      Object.defineProperty(globalThis, name, {
        configurable: true, writable: true,
        value: name === 'getComputedStyle' ? dom.window[name].bind(dom.window) : dom.window[name],
      });
    }
    window.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {} });
    window.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
    window.HTMLDialogElement.prototype.close = function () { this.open = false; };
    window.HTMLElement.prototype.scrollIntoView = function () { this.dataset.scrolled = 'yes'; };
    globalThis.ResizeObserver = class { observe() {} disconnect() {} };
    globalThis.requestAnimationFrame = window.requestAnimationFrame.bind(window);
    globalThis.cancelAnimationFrame = window.cancelAnimationFrame.bind(window);
    globalThis.IS_REACT_ACT_ENVIRONMENT = true;
    server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom', logLevel: 'silent' });
    ui = await server.ssrLoadModule('/tests/kt124-entry.tsx');
  } catch (error) { unavailable = String(error.message ?? error); }
});
beforeEach(() => {
  if (!ui) return;
  container = document.createElement('div'); document.body.append(container);
  root = ui.createRoot(container);
  globalThis.fetch = async (path) => Response.json(String(path).endsWith('/links')
    ? { outgoing: [duplicate[0]], unlinked: [duplicate[1]], unavailable_outgoing_count: 1 }
    : { items: duplicate, folders: [{ id: 17, name: 'Thư mục nghiên cứu' }], next_offset: null });
});
afterEach(async () => { if (root) { await ui.act(async () => root.unmount()); root = undefined; } container?.remove(); container = undefined; });
after(async () => { globalThis.fetch = originalFetch; await server?.close(); dom?.window.close(); });
async function render(component, props = {}) {
  await ui.act(async () => {
    root.render(ui.createElement(ui.MantineProvider, null, ui.createElement(component, props)));
    await delay(25);
  });
}
async function key(target, name, opts = {}) {
  await ui.act(async () => {
    target.dispatchEvent(new window.KeyboardEvent('keydown', { key: name, bubbles: true, cancelable: true, ...opts }));
    await delay(5);
  });
}

test('30 real rendered headings, fenced code and malicious HTML remain inert', async (t) => {
  if (!ui) return t.skip('npm/Vite/JSDOM unavailable: ' + unavailable);
  const headings = Array.from({ length: 30 }, (_, i) =>
    '#'.repeat(i % 6 + 1) + ' ' + (i % 4 === 0 ? 'Tiếng Việt' : 'Mục ' + i + ' — 測試'));
  const markdown = headings.join('\n\n') + '\n\n~~~md\n# FAKE_HEADING\n~~~\n\n<script>alert(1)</script>';
  await render(ui.KnowledgeText, { text: markdown });
  const anchors = [...container.querySelectorAll('.note-outline a')];
  assert.equal(anchors.length, 30);
  assert.equal(new Set(anchors.map((node) => node.getAttribute('href'))).size, 30);
  assert.equal(container.querySelectorAll('script,iframe').length, 0);
  await ui.act(async () => anchors[0].click());
  const target = container.querySelector(anchors[0].getAttribute('href'));
  assert.equal(target.dataset.scrolled, 'yes');
  assert.equal(document.activeElement, target);
});

test('20 IME/field Ctrl+K attempts ignored; Arrow/Enter/Esc use correct UUID', async (t) => {
  if (!ui) return t.skip('npm/Vite/JSDOM unavailable: ' + unavailable);
  const actions = [];
  await render(ui.KnowledgeCommandPalette, { currentItemId: A, onAction: (action) => actions.push(action) });
  const dialog = container.querySelector('dialog');
  const trigger = container.querySelector('.knowledge-palette-trigger');
  const fields = ['input', 'textarea', 'select'].map((tag) => {
    const field = document.createElement(tag); document.body.append(field); return field;
  });
  try {
    for (let i = 0; i < 20; i++) {
      const mode = i % 5;
      if (mode < 3) await key(fields[mode], 'k', { ctrlKey: true });
      else if (mode === 3) await key(window, 'k', { ctrlKey: true, isComposing: true });
      else {
        const e = new window.KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true });
        Object.defineProperty(e, 'keyCode', { value: 229 });
        await ui.act(async () => window.dispatchEvent(e));
      }
      assert.equal(dialog.open, false);
    }
    await key(window, 'k', { ctrlKey: true });
    assert.equal(dialog.open, true);
    await ui.act(async () => delay(170));
    assert.equal([...dialog.querySelectorAll('[role="option"]')].filter((e) => e.textContent.includes('Tiêu đề trùng')).length, 2);
    const input = dialog.querySelector('input');
    await key(input, 'ArrowDown', { isComposing: true });
    await key(input, 'Enter', { isComposing: true });
    await key(input, 'Escape', { isComposing: true });
    assert.equal(dialog.open, true);
    assert.equal(dialog.querySelector('[aria-selected="true"]').textContent.includes(A), true);
    await key(input, 'ArrowDown');
    await key(input, 'Enter');
    assert.equal(dialog.open, false);
    assert.equal(window.location.hash, '#/muc/' + B);
    assert.equal(document.activeElement, trigger);
    await key(window, 'k', { metaKey: true });
    assert.equal(dialog.open, true);
    await key(dialog.querySelector('input'), 'Escape');
    assert.equal(dialog.open, false);
    assert.deepEqual(actions, []);
  } finally { fields.forEach((field) => field.remove()); window.location.hash = ''; }
});

test('unlinked mentions remain visibly labelled as suggestions', async (t) => {
  if (!ui) return t.skip('npm/Vite/JSDOM unavailable: ' + unavailable);
  await render(ui.NoteLinkContext, { id: A });
  assert.match(container.textContent, /Liên kết đi/);
  assert.match(container.textContent, /chỉ là gợi ý/);
  assert.equal(container.querySelectorAll('.note-link-context a').length, 2);
});
