import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { after, afterEach, before, beforeEach, test } from 'node:test';
import { setImmediate as settle } from 'node:timers/promises';
import { createServer } from 'vite';
import { JSDOM, VirtualConsole } from 'jsdom';

const fixtures = JSON.parse(await readFile(new URL('./kt117-fixtures.json', import.meta.url), 'utf8'));
let server, ui, dom, root, container;
const originalFetch = globalThis.fetch;
const originalNow = Date.now;
const session = (username = 'kt117-alice') => ({ authenticated: true, username, csrf_token: 'fixture-csrf' });
const receipt = { capture_id: '00000000-0000-4000-8000-000000000001', item_id: '00000000-0000-4000-8000-000000000002', received_at: '2026-11-20T02:00:00Z', state: 'received' };
function response(data, status = 200) { return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } }); }
before(async () => {
  dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'http://127.0.0.1:5173/', pretendToBeVisual: true, virtualConsole: new VirtualConsole() });
  for (const name of ['window', 'document', 'location', 'navigator', 'HTMLElement', 'Element', 'Node', 'Event', 'MouseEvent', 'CustomEvent', 'MutationObserver', 'getComputedStyle']) {
    Object.defineProperty(globalThis, name, { value: name === 'getComputedStyle' ? dom.window[name].bind(dom.window) : dom.window[name], configurable: true, writable: true });
  }
  window.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
  globalThis.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
  Object.defineProperty(document, 'fonts', { value: new dom.window.EventTarget(), configurable: true });
  globalThis.requestAnimationFrame = window.requestAnimationFrame.bind(window);
  globalThis.cancelAnimationFrame = window.cancelAnimationFrame.bind(window);
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  server = await createServer({ server: { middlewareMode: true, hmr: false, host: '127.0.0.1' }, appType: 'custom', logLevel: 'silent' });
  ui = await server.ssrLoadModule('/tests/kt117-entry.tsx');
});
beforeEach(() => {
  window.history.replaceState(null, '', '/#/gui');
  ui.clearCaptureDraft('kt117-alice'); ui.clearCaptureDraft('kt117-bob');
  container = document.createElement('div'); document.body.append(container); root = ui.createRoot(container);
  globalThis.fetch = async (path) => response(path.endsWith('/session') ? session() : { results: [], next_offset: null });
});
afterEach(async () => {
  await ui.act(async () => { root.unmount(); await settle(); });
  container.remove(); Date.now = originalNow; globalThis.fetch = originalFetch;
});
after(async () => { await server?.close(); dom?.window.close(); });
async function render(component = ui.CaptureScreen, strict = true) {
  const element = ui.createElement(ui.MantineProvider, { forceColorScheme: 'light' }, ui.createElement(component, { csrf: 'fixture-csrf' }));
  await ui.act(async () => { root.render(strict ? ui.createElement(ui.StrictMode, null, element) : element); await settle(); await settle(); });
}
async function submit(times = 1) {
  await ui.act(async () => {
    for (let i = 0; i < times; i++) container.querySelector('form').dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true }));
    await settle(); await settle();
  });
}
async function input(field, value) {
  await ui.act(async () => {
    Object.getOwnPropertyDescriptor(field.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype, 'value').set.call(field, value);
    field.dispatchEvent(new window.Event('input', { bubbles: true })); await settle();
  });
}
async function click(label) {
  const button = [...container.querySelectorAll('button')].find((entry) => entry.textContent === label);
  assert.ok(button, label);
  await ui.act(async () => { button.click(); await settle(); });
}
async function remount() {
  await ui.act(async () => { root.unmount(); await settle(); }); root = ui.createRoot(container); await render();
}

for (const fixture of fixtures) test(`30-share-corpus / ${fixture.name}: exact raw, one submit, receipt`, async () => {
  window.history.replaceState(null, '', '/?' + new URLSearchParams(fixture.params) + '#/gui');
  let sent, calls = 0;
  globalThis.fetch = async (path, options) => {
    if (options?.method === 'POST') { calls++; sent = JSON.parse(options.body); return response(receipt, 201); }
    return response(path.endsWith('/session') ? session() : { results: [], next_offset: null });
  };
  const parsed = ui.readSharedCapture();
  assert.equal(parsed.kind, fixture.kind);
  assert.equal(parsed.url, fixture.url);
  assert.equal(fixture.kind === 'link' ? parsed.annotation : parsed.note, fixture.raw);
  await render();
  assert.equal(window.location.search, ''); assert.equal(window.location.hash, '#/gui');
  assert.equal(container.querySelector('textarea').value, fixture.raw.replace(/\r\n?/g, '\n'), 'textarea display normalizes CRLF; submitted raw must remain exact');
  assert.equal(container.querySelectorAll('script,img,iframe').length, 0);
  await submit(2);
  assert.equal(calls, 1, 'double submit creates one request');
  assert.deepEqual(sent, { kind: fixture.kind, source_channel: 'share', ...(fixture.kind === 'link' ? { url: fixture.url } : {}), text: fixture.raw });
  assert.ok(container.textContent.includes('Đã tiếp nhận lúc'));
  assert.ok(container.textContent.includes(receipt.capture_id));
  assert.equal(container.querySelector('textarea').value, '', 'clear only after ACK');
  assert.ok(!container.textContent.includes('Đã xác minh trên Drive'));
});

for (const failure of ['network', 'timeout', 401, 403, 400, 422, 500]) test(`failure ${failure} retains draft and retry key; explicit resend creates a new key`, async () => {
  let fail = true; const sends = [];
  globalThis.fetch = async (path, options) => {
    if (options?.method === 'POST') {
      sends.push({ key: options.headers.get('Idempotency-Key'), body: JSON.parse(options.body) });
      if (fail) {
        if (failure === 'network') throw new TypeError('fixture disconnected');
        if (failure === 'timeout') throw new DOMException('fixture timeout', 'AbortError');
        return response({}, failure);
      }
      return response(receipt);
    }
    return response(path.endsWith('/session') ? session() : { results: [], next_offset: null });
  };
  await render(); await input(container.querySelector('textarea'), '  Nháp tiếng Việt\r\n**giữ nguyên**  ');
  await submit();
  assert.equal(container.querySelector('textarea').value, '  Nháp tiếng Việt\n**giữ nguyên**  ');
  assert.ok(container.textContent.includes('Chưa ')); assert.ok(!container.textContent.includes('Đã tiếp nhận lúc'));
  if (failure === 401) { await remount(); assert.ok(container.querySelector('textarea').value.includes('Nháp tiếng Việt')); }
  fail = false; await submit();
  assert.equal(sends[0].key, sends[1].key); assert.deepEqual(sends[0].body, sends[1].body);
  await click('Dùng lại nội dung'); await submit();
  assert.notEqual(sends[1].key, sends[2].key); assert.deepEqual(sends[1].body, sends[2].body);
});

test('actual App 401 unmount/login path restores the same account draft and pending key', async () => {
  let loggedIn = true; const keys = [];
  globalThis.fetch = async (path, options) => {
    if (path.endsWith('/session')) {
      if (options?.method === 'POST') loggedIn = true;
      return response(loggedIn ? session() : { authenticated: false, username: null, csrf_token: 'fixture-csrf' });
    }
    if (options?.method === 'POST') {
      keys.push(options.headers.get('Idempotency-Key'));
      if (keys.length === 1) { loggedIn = false; return response({}, 401); }
      return response(receipt);
    }
    return response({ results: [], next_offset: null });
  };
  await render(ui.App); await input(container.querySelector('textarea'), 'Giữ khi đăng nhập lại'); await submit();
  assert.equal(container.querySelector('textarea'), null);
  await input(container.querySelector('input[autocomplete="username"]'), 'kt117-alice');
  await input(container.querySelector('input[type="password"]'), 'fixture-only'); await submit();
  assert.equal(container.querySelector('textarea').value, 'Giữ khi đăng nhập lại');
  await submit(); assert.equal(keys.length, 2); assert.equal(keys[0], keys[1]);
});

test('drafts are scoped to account; clearing is explicit and never sends a request', async () => {
  await render(); await input(container.querySelector('textarea'), 'Nháp của Alice');
  globalThis.fetch = async (path) => response(path.endsWith('/session') ? session('kt117-bob') : { results: [], next_offset: null });
  await remount(); assert.equal(container.querySelector('textarea').value, '');
  globalThis.fetch = async (path) => response(path.endsWith('/session') ? session() : { results: [], next_offset: null });
  await remount(); assert.equal(container.querySelector('textarea').value, 'Nháp của Alice');
  await click('Xóa bản nháp'); await remount(); assert.equal(container.querySelector('textarea').value, '');
});

test('oversized share values remain intact and block submit rather than silently truncate', async () => {
  const huge = '🌱'.repeat(65_537);
  window.history.replaceState(null, '', '/?' + new URLSearchParams({ shared_text: huge }));
  assert.equal(ui.readSharedCapture().note, huge);
  await render(); await submit();
  assert.equal(container.querySelector('textarea').value, huge); assert.ok(container.textContent.includes('65.536'));
  const longUrl = 'https://example.invalid/?q=' + 'a'.repeat(4100);
  await ui.act(async () => { root.unmount(); }); root = ui.createRoot(container);
  window.history.replaceState(null, '', '/?' + new URLSearchParams({ shared_url: longUrl }));
  assert.equal(ui.readSharedCapture().url, longUrl);
  await render(); await submit(); assert.ok(container.textContent.includes('4.096'));
});

test('receipt latency measures submit to client response; pending draft remains visible', async () => {
  let finish, now = 1000;
  Date.now = () => now;
  globalThis.fetch = async (path, options) => {
    if (options?.method === 'POST') return new Promise((resolve) => { finish = resolve; });
    return response(path.endsWith('/session') ? session() : { results: [], next_offset: null });
  };
  await render(); await input(container.querySelector('textarea'), 'Đang gửi'); await submit();
  assert.equal(container.querySelector('textarea').value, 'Đang gửi'); assert.ok(!container.textContent.includes('Đã tiếp nhận lúc'));
  now = 1234; await ui.act(async () => { finish(response(receipt)); await settle(); });
  assert.ok(container.textContent.includes('234 ms'));
});

test('the request timeout aborts fetch without clearing the draft or changing its retry key', async () => {
  await render(); await input(container.querySelector('textarea'), 'Bản nháp timeout');
  const nativeTimeout = window.setTimeout;
  let expire, fail = true; const keys = [];
  window.setTimeout = (callback, delay) => delay === 15_000 ? (expire = callback, -1) : nativeTimeout(callback, delay);
  globalThis.fetch = async (path, options) => {
    if (options?.method === 'POST') {
      keys.push(options.headers.get('Idempotency-Key'));
      if (fail) return new Promise((resolve, reject) => options.signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true }));
      return response(receipt);
    }
    return response({ results: [], next_offset: null });
  };
  try {
    await submit();
    await ui.act(async () => { expire(); await settle(); });
    assert.equal(container.querySelector('textarea').value, 'Bản nháp timeout');
    assert.ok(!container.textContent.includes('Đã tiếp nhận lúc'));
    fail = false; await submit(); assert.equal(keys[0], keys[1]);
  } finally { window.setTimeout = nativeTimeout; }
});

test('file retry retains File/key through remount and ACK never claims verified MP4 on Drive', async () => {
  const file = new File(['fixture only'], 'fixture.mp4', { type: 'video/mp4' });
  ui.saveCaptureDraft('kt117-alice', { kind: 'file', url: '', note: '', annotation: '', shared: false, attempt: null });
  ui.saveCaptureFile('kt117-alice', { file, key: 'kt117-file-attempt' });
  let fail = true; const keys = [];
  globalThis.fetch = async (path, options) => {
    if (path.endsWith('/uploads')) {
      keys.push(options.headers.get('Idempotency-Key')); assert.equal(options.body.get('file').name, 'fixture.mp4');
      if (fail) throw new TypeError('fixture network');
      return response({ item_id: receipt.item_id, asset_id: 'fixture-asset', state: 'pending' });
    }
    return response(path.endsWith('/session') ? session() : { results: [], next_offset: null });
  };
  await render(); await submit(); assert.ok(container.textContent.includes('Chưa xác nhận tiếp nhận tệp'));
  await remount(); fail = false; await submit();
  assert.deepEqual(keys, ['kt117-file-attempt', 'kt117-file-attempt']);
  assert.ok(container.textContent.includes('Đã tiếp nhận tệp để xử lý'));
  assert.ok(container.textContent.includes('Chưa xác nhận tệp đã được lưu và kiểm tra trên Drive'));
});

test('manifest retains existing GET share target without privileged permission changes', async () => {
  const manifest = JSON.parse(await readFile(new URL('../public/manifest.webmanifest', import.meta.url), 'utf8'));
  assert.deepEqual(manifest.share_target, { action: '/', method: 'GET', params: { title: 'shared_title', text: 'shared_text', url: 'shared_url' } });
  assert.equal(manifest.start_url, '/#/gui');
});
