import assert from 'node:assert/strict';
import { after, afterEach, before, beforeEach, test } from 'node:test';
import { setImmediate as settle } from 'node:timers/promises';
import { createServer } from 'vite';
import { JSDOM, VirtualConsole } from 'jsdom';

let server, ui, dom, root, container, clock;
const originalNow = Date.now;
const originalFetch = globalThis.fetch;

before(async () => {
  dom = new JSDOM('<!doctype html><html><body></body></html>', {
    url: 'http://127.0.0.1:5173/', pretendToBeVisual: true, virtualConsole: new VirtualConsole(),
  });
  for (const name of ['window', 'document', 'navigator', 'HTMLElement', 'Element', 'Node', 'Event', 'MouseEvent', 'CustomEvent', 'MutationObserver', 'getComputedStyle']) {
    Object.defineProperty(globalThis, name, { value: name === 'getComputedStyle' ? dom.window[name].bind(dom.window) : dom.window[name], configurable: true, writable: true });
  }
  window.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
  globalThis.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
  Object.defineProperty(document, 'fonts', { value: new dom.window.EventTarget(), configurable: true });
  globalThis.requestAnimationFrame = window.requestAnimationFrame.bind(window);
  globalThis.cancelAnimationFrame = window.cancelAnimationFrame.bind(window);
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  server = await createServer({ server: { middlewareMode: true, hmr: false, host: '127.0.0.1' }, appType: 'custom', logLevel: 'silent' });
  ui = await server.ssrLoadModule('/tests/ui-entry.tsx');
});

beforeEach(() => {
  window.history.replaceState(null, '', '/');
  container = document.createElement('div');
  document.body.append(container);
  root = ui.createRoot(container);
  let now = 0, sequence = 0;
  const timers = new Map();
  window.setTimeout = (callback, delay = 0) => {
    const id = ++sequence;
    timers.set(id, { at: now + delay, callback });
    return id;
  };
  window.clearTimeout = (id) => timers.delete(id);
  Date.now = () => now;
  clock = {
    async advance(ms) {
      const target = now + ms;
      for (;;) {
        const next = [...timers].filter(([, timer]) => timer.at <= target).sort((a, b) => a[1].at - b[1].at)[0];
        if (!next) break;
        timers.delete(next[0]);
        now = next[1].at;
        await ui.act(async () => { next[1].callback(); await settle(); });
      }
      now = target;
    },
    get size() { return timers.size; },
  };
});

afterEach(async () => {
  await ui.act(async () => { root.unmount(); await settle(); });
  container.remove();
  Date.now = originalNow;
  globalThis.fetch = originalFetch;
});
after(async () => { await server?.close(); dom?.window.close(); });

function response(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });
}
async function render(component, props = {}, strict = false) {
  const element = ui.createElement(ui.MantineProvider, { forceColorScheme: 'light' }, ui.createElement(component, props));
  await ui.act(async () => { root.render(strict ? ui.createElement(ui.StrictMode, null, element) : element); await settle(); });
}
async function click(label) {
  const button = [...container.querySelectorAll('button')].find((entry) => entry.textContent === label);
  assert.ok(button, 'Expected button ' + label);
  await ui.act(async () => { button.dispatchEvent(new window.MouseEvent('click', { bubbles: true })); await settle(); });
}
function Probe({ path = '/fixture', maxPollMs }) {
  const resource = ui.useResource(path, { pollWhile: (data) => data.pending, maxPollMs });
  return ui.createElement('div', null,
    ui.createElement('output', null, JSON.stringify(resource)),
    ui.createElement('button', { onClick: resource.retry }, 'Refresh'),
  );
}
const probe = () => JSON.parse(container.querySelector('output').textContent);

test('pending resources poll sequentially and stop when processing completes', async () => {
  let calls = 0;
  globalThis.fetch = async () => response({ pending: ++calls === 1, value: calls });
  await render(Probe);
  assert.equal(probe().data.value, 1);
  await clock.advance(2_500);
  assert.equal(probe().data.value, 2);
  await clock.advance(60_000);
  assert.equal(calls, 2);
  assert.equal(clock.size, 0);
});

test('transient failures retain prior data, back off and stop after three failures', async () => {
  let calls = 0;
  globalThis.fetch = async () => ++calls === 1 ? response({ pending: true, value: 'saved' }) : response({}, 503);
  await render(Probe);
  await clock.advance(2_500);
  assert.equal(probe().data.value, 'saved');
  assert.equal(probe().refreshError, true);
  await clock.advance(4_999);
  assert.equal(calls, 2);
  await clock.advance(1);
  assert.equal(calls, 3);
  await clock.advance(10_000);
  assert.equal(probe().pollingPaused, true);
  await clock.advance(60_000);
  assert.equal(calls, 4);
});

test('expired sessions erase cached data and stop polling', async () => {
  let calls = 0, expired = 0;
  const listener = () => { expired += 1; };
  window.addEventListener('session-expired', listener);
  globalThis.fetch = async () => ++calls === 1 ? response({ pending: true, value: 'private fixture' }) : response({}, 401);
  await render(Probe);
  await clock.advance(2_500);
  assert.equal(probe().data, undefined);
  assert.equal(probe().error, true);
  assert.equal(expired, 1);
  await clock.advance(60_000);
  assert.equal(calls, 2);
  window.removeEventListener('session-expired', listener);
});

test('polling pauses within its time budget and manual refresh resumes it', async () => {
  let calls = 0;
  globalThis.fetch = async () => response({ pending: true, value: ++calls });
  await render(Probe, { maxPollMs: 3_000 });
  await clock.advance(2_500);
  assert.equal(probe().pollingPaused, true);
  await clock.advance(30_000);
  assert.equal(calls, 2);
  await click('Refresh');
  assert.equal(calls, 3);
  assert.equal(probe().pollingPaused, undefined);
});

test('route changes abort the old request and ignore its late response', async () => {
  let resolveOld, oldSignal;
  globalThis.fetch = async (path, options) => {
    if (path.endsWith('/old')) {
      oldSignal = options.signal;
      return await new Promise((resolve) => { resolveOld = resolve; });
    }
    return response({ pending: false, value: 'new item' });
  };
  await render(Probe, { path: '/old' });
  await render(Probe, { path: '/new' });
  assert.equal(oldSignal.aborted, true);
  await ui.act(async () => { resolveOld(response({ pending: true, value: 'old item' })); await settle(); });
  assert.equal(probe().data.value, 'new item');
  assert.equal(clock.size, 0);
});

test('unmount aborts in-flight polling and removes scheduled work', async () => {
  let signal, calls = 0;
  globalThis.fetch = async (_path, options) => {
    signal = options.signal;
    calls += 1;
    return await new Promise(() => {});
  };
  await render(Probe);
  await ui.act(async () => { root.unmount(); await settle(); });
  assert.equal(signal.aborted, true);
  await clock.advance(60_000);
  assert.equal(calls, 1);
  root = ui.createRoot(container);
});

const item = (patch = {}) => ({
  item_id: 'fixture-item', kind: 'link', title: 'Fixture title', description: 'Fixture description', note: 'Ghi chú gốc',
  saved_at: '2026-11-19T00:00:00Z', published_at: null, updated_at: '2026-11-19T00:00:00Z', favorite: false, deleted: false,
  classification_status: 'unclassified', original_url: 'https://example.invalid/source', source_fetch: 'pending',
  asset_storage: 'pending', content_extract: 'not_available', assets: [], ...patch,
});
function itemRoutes(current) {
  return async (path, options) => {
    if (path.endsWith('/retry')) return response({ queued: 1 });
    if (path.endsWith('/items/fixture-item')) return response(current(options));
    if (path.includes('/organization')) return response({ topics: [], projects: [], tags: [] });
    return response({ results: [], next_offset: null });
  };
}

test('item status and attachment update without erasing a draft under editing', async () => {
  let calls = 0;
  globalThis.fetch = itemRoutes(() => ++calls === 1 ? item() : item({
    title: 'Worker metadata', source_fetch: 'done', asset_storage: 'verified',
    assets: [{ asset_id: 'fixture-asset', filename: 'fixture.mp4', status: 'verified', mime: 'video/mp4' }],
  }));
  await render(ui.ItemScreen, { id: 'fixture-item', csrf: 'fixture-csrf' });
  await click('Chỉnh sửa');
  const title = container.querySelector('input');
  await ui.act(async () => {
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(title, 'Bản nháp chưa lưu');
    title.dispatchEvent(new window.Event('input', { bubbles: true }));
    await settle();
  });
  await clock.advance(2_500);
  assert.equal(title.value, 'Bản nháp chưa lưu');
  assert.ok(container.textContent.includes('Đã xác minh trên Drive'));
  assert.ok([...container.querySelectorAll('button')].some((entry) => entry.textContent === 'Mở tệp'));
  assert.equal(calls, 2);
});

test('retry refreshes stale failed state and starts polling the queued task', async () => {
  let reads = 0;
  globalThis.fetch = itemRoutes(() => item(++reads === 1
    ? { source_fetch: 'failed', asset_storage: 'failed' }
    : reads === 2 ? {} : { source_fetch: 'done', asset_storage: 'verified' }));
  await render(ui.ItemScreen, { id: 'fixture-item', csrf: 'fixture-csrf' });
  await click('Thử xử lý lại');
  assert.ok(container.textContent.includes('Đã đưa vào hàng đợi để thử lại.'));
  assert.equal(reads, 2);
  await clock.advance(2_500);
  assert.equal(reads, 3);
  assert.ok(container.textContent.includes('Đã xác minh trên Drive'));
});

test('StrictMode share target preserves Unicode inputs after removing query parameters', async () => {
  window.history.replaceState(null, '', '/?shared_title=Chia+s%E1%BA%BB&shared_text=Ghi+ch%C3%BA&shared_url=https%3A%2F%2Fexample.invalid%2Fvideo');
  let submissions = 0, captured;
  globalThis.fetch = async (path, options) => {
    if (path.endsWith('/captures') && options.method === 'POST') {
      submissions += 1;
      captured = { body: JSON.parse(options.body), csrf: options.headers.get('X-CSRFToken') };
      return response({ capture_id: 'capture-fixture', item_id: 'fixture-item', received_at: '2026-11-19T00:00:00Z', state: 'received' });
    }
    return response({ results: [], next_offset: null });
  };
  await render(ui.CaptureScreen, { csrf: 'fixture-csrf' }, true);
  assert.equal(window.location.search, '');
  assert.equal(container.querySelector('input[placeholder="https://…"]').value, 'https://example.invalid/video');
  assert.equal(container.querySelector('textarea').value, 'Chia sẻ\nGhi chú');
  await ui.act(async () => {
    container.querySelector('form').dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true }));
    container.querySelector('form').dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true }));
    await settle();
  });
  assert.equal(submissions, 1);
  assert.equal(captured.csrf, 'fixture-csrf');
  assert.equal(captured.body.url, 'https://example.invalid/video');
  assert.equal(captured.body.text, 'Chia sẻ\nGhi chú');
  assert.ok(container.textContent.includes('Đã tiếp nhận lúc'));
});

for (const width of [390, 768, 1440]) {
  test('shared text fallback DOM at configured width ' + width, async () => {
    Object.defineProperty(window, 'innerWidth', { value: width, configurable: true });
    window.history.replaceState(null, '', '/?shared_text=Ghi+ch%C3%BA+ti%E1%BA%BFng+Vi%E1%BB%87t');
    globalThis.fetch = async () => response({ results: [], next_offset: null });
    await render(ui.CaptureScreen, { csrf: 'fixture-csrf' }, true);
    assert.equal(container.querySelector('textarea').value, 'Ghi chú tiếng Việt');
    assert.equal(container.querySelector('input[placeholder="https://…"]'), null);
    assert.equal(window.location.search, '');
  });
}
