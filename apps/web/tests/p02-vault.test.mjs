import assert from 'node:assert/strict';
import { test, before, after } from 'node:test';
import { createServer } from 'vite';
import { JSDOM, VirtualConsole } from 'jsdom';

let dom, server, ui, react, root, container;
const savedFetch = globalThis.fetch;
before(async () => {
  dom = new JSDOM('<!doctype html><html><body></body></html>', {
    url: 'http://127.0.0.1/', pretendToBeVisual: true,
    virtualConsole: new VirtualConsole(),
  });
  for (const key of ['window', 'document', 'navigator', 'HTMLElement',
    'Element', 'Node', 'Event', 'MouseEvent', 'MutationObserver', 'getComputedStyle']) {
    Object.defineProperty(globalThis, key, { configurable: true, writable: true,
      value: key === 'getComputedStyle' ? dom.window[key].bind(dom.window) : dom.window[key] });
  }
  window.matchMedia = () => ({ matches: true, addListener() {}, removeListener() {},
    addEventListener() {}, removeEventListener() {} });
  globalThis.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
  Object.defineProperty(document, 'fonts', { value: new dom.window.EventTarget(), configurable: true });
  globalThis.requestAnimationFrame = window.requestAnimationFrame.bind(window);
  globalThis.cancelAnimationFrame = window.cancelAnimationFrame.bind(window);
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  server = await createServer({ server: { middlewareMode: true, hmr: false },
    appType: 'custom', logLevel: 'silent' });
  ui = await server.ssrLoadModule('/src/KnowledgeVaultPanel.tsx');
  react = await server.ssrLoadModule('/tests/kt126-entry.tsx');
  container = document.createElement('div'); document.body.append(container);
  root = react.createRoot(container);
});
after(async () => {
  await react.act(async () => root.unmount());
  container.remove(); globalThis.fetch = savedFetch;
  await server.close(); dom.window.close();
});
test('standalone panel renders with no implicit export/import write', async () => {
  const calls = [];
  globalThis.fetch = async (...args) => { calls.push(args); throw Error('unexpected request'); };
  await react.act(async () => {
    root.render(react.createElement(react.MantineProvider, null,
      react.createElement(ui.KnowledgeVaultPanel, { csrf: 'synthetic-csrf' })));
  });
  assert.match(container.textContent, /Kho Markdown di động/);
  assert.match(container.textContent, /không thay thế backup PostgreSQL/);
  assert.ok([...container.querySelectorAll('button')].some((button) =>
    button.textContent.includes('Xuất Markdown Vault')));
  assert.ok([...container.querySelectorAll('button')].some((button) =>
    button.textContent.includes('Xem trước nhập') && button.disabled));
  assert.equal(calls.length, 0);
});
test('export endpoint is a same-origin read, never a mutation', async () => {
  const calls = [];
  globalThis.fetch = async (path, options) => {
    calls.push({ path, options });
    return Response.json({ code: 'blocked' }, { status: 422 });
  };
  const button = [...container.querySelectorAll('button')].find((entry) =>
    entry.textContent.includes('Xuất Markdown Vault'));
  await react.act(async () => button.click());
  assert.equal(calls.length, 1);
  assert.equal(calls[0].path, '/api/v1/vault/export');
  assert.equal(calls[0].options.credentials, 'same-origin');
  assert.equal(calls[0].options.method, undefined);
  assert.match(container.textContent, /Chưa tạo được bản xuất/);
});
