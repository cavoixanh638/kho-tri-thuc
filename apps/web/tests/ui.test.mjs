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

test('search explains partial matches on the same results page and only for a nonempty partial response', async () => {
  const hit = { item_id: 'note-id', title: 'Ghi chú đã lưu', evidence: [] };
  const pages = {
    partial: { results: [hit], match_kind: 'partial' },
    standard: { results: [hit], match_kind: 'standard' },
    legacy: { results: [hit] },
    empty: { results: [], match_kind: 'partial' },
  };
  globalThis.fetch = async path => {
    const url = new URL(path, window.location.origin);
    if (url.pathname === '/api/v1/groups') return response({ topics: [], projects: [], tags: [] });
    assert.equal(url.pathname, '/api/v1/search');
    return response({ ...pages[url.searchParams.get('q')], next_cursor: null });
  };

  for (const mode of Object.keys(pages)) {
    await render(ui.SearchScreen, { path: '#/tim-kiem?q=' + mode });
    const section = container.querySelector('[aria-labelledby="search-results-title"]');
    assert.equal(section.querySelector('h2').textContent, 'Kết quả tìm kiếm');
    const label = section.querySelector('[role="status"]');
    const list = section.querySelector('ol');
    if (mode === 'partial') {
      assert.equal(label.textContent, 'Ghi chú khớp một phần từ khóa');
      assert.equal(list.getAttribute('aria-describedby'), label.id);
    } else {
      assert.equal(label, null);
      assert.equal(list?.hasAttribute('aria-describedby') ?? false, false);
    }
    if (mode === 'empty') {
      assert.equal(section.querySelector('.empty-state').textContent, 'Không tìm thấy mục phù hợp.');
    } else {
      assert.equal(list.querySelector('a').getAttribute('href'), '#/muc/note-id');
    }
  }
});

test('approximate search is explicit and keeps group filters and pagination in the chosen mode', async () => {
  const requested = [];
  const next = { score: 3, item_id: 'first' };
  globalThis.fetch = async path => {
    const url = new URL(path, window.location.origin);
    if (url.pathname === '/api/v1/groups') return response({ topics: [], projects: [], tags: [] });
    const params = url.searchParams;
    requested.push(params);
    if (params.get('expand') !== 'true') return response({ results: [], next_cursor: null, can_expand: true });
    const id = params.has('cursor_item_id') ? 'second' : 'first';
    return response({ match_kind: 'partial', can_expand: true,
      results: [{ item_id: id, title: id, evidence: [] }], next_cursor: id === 'first' ? next : null });
  };
  const route = async hash => render(ui.SearchScreen, { key: hash, path: hash });
  const action = label => [...container.querySelectorAll('.search-results a')].find(link => link.textContent === label);
  await route('#/tim-kiem?q=tr%C3%AD+nh%E1%BB%9B&topic_id=4&project_id=8&tag_id=2');
  assert.equal(requested.at(-1).has('expand'), false);
  assert.ok(container.querySelector('.empty-state'));
  const expand = action('Tìm gần đúng');
  assert.ok(expand);
  await route(expand.hash);
  const params = requested.at(-1);
  assert.equal(params.get('expand'), 'true');
  assert.equal(params.get('q'), 'trí nhớ');
  for (const [key, value] of Object.entries({ topic_id: '4', project_id: '8', tag_id: '2' })) {
    assert.equal(params.get(key), value);
  }
  assert.equal(params.has('cursor_item_id'), false);
  assert.equal(action('Tìm gần đúng'), undefined);
  assert.ok(container.querySelector('ol[aria-describedby="search-partial-match"]'));
  await click('Trang sau');
  assert.equal(requested.at(-1).get('expand'), 'true');
  assert.equal(requested.at(-1).get('cursor_item_id'), 'first');
  assert.equal(requested.at(-1).get('cursor_score'), '3');
  assert.equal(container.querySelector('ol a').textContent, 'second');

  const back = action('Về kết quả ban đầu');
  assert.ok(back);
  await route(back.hash);
  assert.equal(requested.at(-1).has('expand'), false);
  assert.equal(requested.at(-1).has('cursor_item_id'), false);
  assert.ok(container.querySelector('.empty-state'));
});

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

test('knowledge Markdown renders structure while HTML, active URLs and remote images stay inert', async () => {
  await render(ui.KnowledgeText, { text: '# Tri thức\n\n**Ý chính**\n\n| Cột | Giá trị |\n| --- | --- |\n| A | 42 |\n\n[nguồn](https://example.com/doc)\n\n[xấu](javascript:alert%281%29)\n\n![minh họa](https://example.com/pixel.png)\n\n<script>alert(1)</script><img src=x onerror=alert(1)>' });
  assert.equal(container.querySelector('.knowledge-text h2').textContent, 'Tri thức');
  assert.equal(container.querySelector('strong').textContent, 'Ý chính');
  assert.equal(container.querySelector('td').textContent, 'A');
  assert.equal(container.querySelector('a').rel, 'noopener noreferrer');
  assert.equal(container.querySelectorAll('script,img,iframe').length, 0);
  assert.equal(container.querySelectorAll('a[href^="javascript:"]').length, 0);
  assert.ok(container.textContent.includes('Ảnh minh họa'));
});

test('new capture defaults to text and preserves Markdown bytes in the submitted knowledge', async () => {
  let sent;
  globalThis.fetch = async (path, options) => {
    if (options?.method === 'POST') { sent = JSON.parse(options.body); return response({ item_id: 'new-text', capture_id: 'event', received_at: '2026-11-19T00:00:00Z' }); }
    return response({ results: [], next_offset: null });
  };
  await render(ui.CaptureScreen, { csrf: 'fixture-csrf' });
  const field = container.querySelector('textarea');
  assert.ok(field, 'Text is the primary capture');
  const markdown = '# Ghi chép\n\n  Tiếng Việt **nguyên văn**  ';
  await ui.act(async () => {
    Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set.call(field, markdown);
    field.dispatchEvent(new window.Event('input', { bubbles: true })); await settle();
  });
  await click('Gửi vào kho');
  assert.equal(sent.kind, 'text');
  assert.equal(sent.text, markdown);
});
function itemRoutes(current) {
  return async (path, options) => {
    if (path.endsWith('/retry')) return response({ queued: 1 });
    if (path.endsWith('/items/fixture-item')) return response(current(options));
    if (path.includes('/organization')) return response({ topics: [], projects: [], tags: [] });
    if (path.includes('/knowledge')) return response({ origin: 'missing', text: '', parts: [], truncated: false, needs_review: false });
    return response({ results: [], next_offset: null });
  };
}

test('P01: unavailable structure payload never hides the source note, editor or clipper', async () => {
  const fallback = itemRoutes(() => item({ kind: 'text', title: 'Ghi chú có nguồn',
    note: 'Nội dung **người dùng viết**', original_url: 'https://example.org/article' }));
  let previewBody, previewCsrf;
  globalThis.fetch = async (path, options) => {
    if (path.endsWith('/clips/preview')) {
      previewBody = JSON.parse(options.body);
      previewCsrf = options.headers.get('X-CSRFToken');
      return response({ receipt: 'preview-1', quote: '', url: previewBody.url,
        page_title: 'Nguồn kiểm thử', verification: 'link_only', locator: {}, source_version: 'v1' });
    }
    // An older/mock server returns its ordinary empty page for unknown endpoints.
    // This must not crash the whole item page when /structure is not yet available.
    return fallback(path, options);
  };
  await render(ui.ItemScreen, { id: 'fixture-item', csrf: 'fixture-csrf' });
  assert.equal(container.querySelector('h1').textContent, 'Ghi chú có nguồn');
  assert.equal(container.querySelector('.knowledge-text strong').textContent, 'người dùng viết');
  assert.ok(container.querySelector('.source-description a[href="https://example.org/article"]'));
  const structure=container.querySelector('[aria-label="Cấu trúc bài cha và bài con"]');
  assert.ok(structure,'Optional structure panel remains mounted');
  assert.match(structure.textContent, /Chưa tải được cấu trúc bài/);
  assert.ok(structure.querySelector('[role="alert"] button'),'Recoverable malformed structure offers retry');
  assert.ok(container.querySelector('#item-clipper .research-clipper'), 'Clipper remains mounted');

  const urlField = container.querySelector('#item-clipper input[type="url"]');
  assert.ok(urlField);
  await ui.act(async () => {
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(urlField, 'https://example.org/public');
    urlField.dispatchEvent(new window.Event('input', { bubbles: true }));
    await settle();
  });
  await click('Xem trước nguồn / đoạn trích');
  assert.deepEqual(previewBody, { mode: 'link', url: 'https://example.org/public', quote: '', target_item_id: 'fixture-item' });
  assert.equal(previewCsrf, 'fixture-csrf');
  assert.ok(container.textContent.includes('Nguồn kiểm thử'));
  await click('Chỉnh sửa');
  assert.ok(container.querySelector('.markdown-item-detail form textarea'), 'Editable user note remains available');
});

test('P01: valid structure payload exposes children and accepts command-palette move action', async () => {
  const fallback = itemRoutes(() => item({ kind: 'text', note: 'Bản văn giữ nguyên', original_url: '' }));
  globalThis.fetch = async (path, options) => {
    if (path.endsWith('/items/fixture-item/structure')) {
      return response({ item_id: 'fixture-item', home_topic_id: 2, parent_item_id: null,
        sort_order: 0, structure_version: 4, origin: 'user', ancestors: [],
        children: [{ item_id: '22345678-1234-4567-89ab-123456789abc', title: 'Bài con có thật' }] });
    }
    if (path.endsWith('/knowledge-tree')) return response({ nodes: [{ id: 2, path: 'Sổ tay / Dự án' }] });
    return fallback(path, options);
  };
  await render(ui.ItemScreen, { id: 'fixture-item', csrf: 'fixture-csrf' });
  const panel = container.querySelector('[aria-label="Cấu trúc bài cha và bài con"]');
  assert.ok(panel, 'Structure panel mounts when API is valid');
  assert.match(panel.textContent, /Bài con \(1\)/);
  assert.ok(panel.querySelector('a[href="#/muc/22345678-1234-4567-89ab-123456789abc"]'));
  await ui.act(async () => {
    window.dispatchEvent(new window.CustomEvent('knowledge-command', {
      detail: { action: 'move', itemId: 'fixture-item' },
    }));
    await settle();
  });
  const controls = [...panel.querySelectorAll('details')].find((node) => node.textContent.includes('Chuyển thư mục / thêm lối tắt'));
  assert.equal(controls?.open, true);
  assert.ok(controls.querySelector('select'), 'Folder selector is attached to the command');
});

test('a text article reads as knowledge without misleading missing-extraction status or repeated title', async () => {
  globalThis.fetch = itemRoutes(() => item({ kind: 'text', title: 'Bài tri thức', note: '# Bài tri thức\n\nNội dung **đã có**.', original_url: '', source_fetch: 'not_applicable', asset_storage: 'not_applicable' }));
  await render(ui.ItemScreen, { id: 'fixture-item', csrf: 'fixture-csrf' });
  assert.equal(container.querySelector('h1').textContent, 'Bài tri thức');
  assert.equal(container.querySelector('.knowledge-text strong').textContent, 'đã có');
  assert.equal(container.querySelector('.knowledge-text h3'), null);
  assert.equal(container.querySelector('#extracted-content'), null);
  assert.ok(!container.textContent.includes('Chưa có nội dung'));
});

test('extracted transcript is the main reading content with a source illustration link', async () => {
  globalThis.fetch = async (path) => {
    if (path.endsWith('/items/fixture-item')) return response(item({ note: '', content_extract: 'done', source_fetch: 'done', asset_storage: 'verified', assets: [{ asset_id: 'video', filename: 'source.mp4', status: 'verified', mime: 'video/mp4' }] }));
    if (path.endsWith('/knowledge')) return response({ origin: 'extracted', text: '', parts: [{ id: 1, kind: 'video_transcript', text: '[00:05–00:10] Giữ mặt gậy mở.', asset_id: 'video', locator: { section: 'Đoạn 5–10 giây' }, processor: 'faster-whisper', format: 'text' }], truncated: false, needs_review: true });
    if (path.includes('/organization')) return response({ topics: [], projects: [], tags: [] });
    return response({ results: [], next_offset: null });
  };
  await render(ui.ItemScreen, { id: 'fixture-item', csrf: 'fixture-csrf' });
  assert.ok(container.querySelector('[aria-labelledby="item-content"]').textContent.includes('Giữ mặt gậy mở.'));
  assert.ok(container.textContent.includes('Cần đối chiếu video'));
  const media = container.querySelector('#item-media');
  assert.equal(media.open, false);
  media.scrollIntoView = () => {};
  await click('Xem minh họa từ nguồn');
  assert.equal(media.open, true);
});

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
  assert.ok(container.querySelector('.capture-share-source')?.textContent.includes('https://example.invalid/video'));
  assert.equal(container.querySelectorAll('.capture-compose textarea').length, 1, 'Single unified intake input');
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

test('knowledge export requires opt in, sends CSRF and polls until the Drive revision is ready', async () => {
  const base = { enabled: false, format: 'markdown', status: 'disabled', stale: false,
    source_version: '', exported_version: '', truncated: false, last_error: '', last_synced_at: null, url: null };
  let phase = 'disabled', pendingReads = 0, write;
  globalThis.fetch = async (path, options) => {
    assert.equal(path, '/api/v1/items/fixture-item/knowledge-export');
    if (options.method === 'POST') {
      write = { body: JSON.parse(options.body), csrf: options.headers.get('X-CSRFToken') };
      phase = 'pending';
      return response({ ...base, enabled: true, status: 'pending', stale: true });
    }
    if (phase === 'pending' && ++pendingReads >= 2) phase = 'synced';
    return response(phase === 'disabled' ? base : { ...base, enabled: true, status: phase,
      stale: phase !== 'synced', url: phase === 'synced' ? 'https://drive.google.com/open?id=fixture-export' : null });
  };
  await render(ui.KnowledgeExportPanel, { id: 'fixture-item', csrf: 'fixture-csrf', deleted: false, refreshKey: '1' });
  assert.equal(write, undefined);
  assert.ok(container.textContent.includes('Đang tắt'));
  await click('Bật xuất tri thức');
  assert.deepEqual(write, { body: { enabled: true, format: 'markdown' }, csrf: 'fixture-csrf' });
  assert.ok(container.textContent.includes('Đang chờ đồng bộ'));
  await clock.advance(2_500);
  assert.ok(container.textContent.includes('Đã đồng bộ'));
  assert.equal(container.querySelector('a').href, 'https://drive.google.com/open?id=fixture-export');
});

test('knowledge export explains blocked or stale content and never opens a blocked file', async () => {
  globalThis.fetch = async () => response({ enabled: true, format: 'text', status: 'failed', stale: true,
    source_version: 'new', exported_version: 'old', truncated: true, last_error: 'knowledge_sensitive_input',
    last_synced_at: null, url: null });
  await render(ui.KnowledgeExportPanel, { id: 'fixture-item', csrf: 'fixture-csrf', deleted: false, refreshKey: '1' });
  assert.ok(container.textContent.includes('Đã chặn xuất'));
  assert.ok(container.textContent.includes('chưa theo kịp dữ liệu nguồn'));
  assert.ok(container.textContent.includes('bản xuất có giới hạn'));
  assert.equal(container.querySelector('a'), null);
});

test('knowledge tree routes subtree reads, excludes cyclic move parents and creates a child with CSRF', async () => {
  const node = (id, parent_id, name, path_ids, path, patch = {}) => ({
    id, parent_id, name, path_ids, path, depth: path_ids.length - 1,
    node_kind: parent_id == null ? 'library' : 'folder', sort_order: 0,
    direct_count: 0, item_count: 1, child_count: 0, ...patch,
  });
  const nodes = [
    node(1, null, 'Công nghệ', [1], 'Công nghệ', { child_count: 1 }),
    node(2, 1, 'Lập trình', [1, 2], 'Công nghệ / Lập trình', { child_count: 1 }),
    node(3, 2, 'Python', [1, 2, 3], 'Công nghệ / Lập trình / Python'),
    node(4, null, 'Đời sống', [4], 'Đời sống'),
  ];
  const reads = [];
  let created;
  globalThis.fetch = async (path, options) => {
    if (path.endsWith('/knowledge-tree') && options?.method === 'POST') {
      created = { body: JSON.parse(options.body), csrf: options.headers.get('X-CSRFToken') };
      const child = node(5, 2, created.body.name, [1, 2, 5], 'Công nghệ / Lập trình / ' + created.body.name);
      nodes.push(child);
      return response(child, 201);
    }
    if (path.endsWith('/knowledge-tree')) return response({ nodes });
    if (path.includes('/items?')) {
      reads.push(new URL(path, window.location.origin).searchParams);
      return response({ results: [item({ title: 'Bài trong nhánh con', source_fetch: 'done', asset_storage: 'verified' })], next_offset: null });
    }
    throw new Error('Unexpected request ' + path);
  };
  window.history.replaceState(null, '', '/#/thu-vien?node=1');
  await render(ui.LibraryScreen, { csrf: 'tree-csrf' });
  assert.equal(reads.at(-1).get('node_id'), '1');
  assert.ok(container.querySelector('[aria-label="Các nhánh con"]').textContent.includes('Lập trình'));
  assert.ok(container.querySelector('[aria-label="Danh sách mục"]').textContent.includes('Bài trong nhánh con'));

  const branchLink = container.querySelector('[aria-label="Các nhánh con"] a');
  await ui.act(async () => {
    window.history.replaceState(null, '', branchLink.getAttribute('href'));
    window.dispatchEvent(new window.Event('hashchange'));
    await settle();
  });
  assert.equal(reads.at(-1).get('node_id'), '2');
  assert.equal(container.querySelector('[aria-label="Đường dẫn mục lục"] a[aria-current="page"]').textContent, 'Lập trình');

  await click('Đổi tên / chuyển nhánh');
  const parentLabel = [...container.querySelectorAll('label')].find((label) => label.textContent === 'Nằm trong');
  assert.ok(parentLabel);
  const parentInput = document.getElementById(parentLabel.htmlFor);
  await ui.act(async () => { parentInput.dispatchEvent(new window.MouseEvent('click', { bubbles: true })); await settle(); });
  const parents = [...document.querySelectorAll('[role="option"]')].map((option) => option.textContent);
  assert.ok(parents.includes('Công nghệ'));
  assert.ok(parents.includes('Đời sống'));
  assert.ok(!parents.includes('Công nghệ / Lập trình'));
  assert.ok(!parents.includes('Công nghệ / Lập trình / Python'));
  await click('Hủy');

  await click('Thêm nhánh con');
  const nameLabel = [...container.querySelectorAll('label')].find((label) => label.textContent.startsWith('Tên nhánh'));
  assert.ok(nameLabel);
  const nameInput = document.getElementById(nameLabel.htmlFor);
  await ui.act(async () => {
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(nameInput, 'Tài liệu nhập môn');
    nameInput.dispatchEvent(new window.Event('input', { bubbles: true })); await settle();
  });
  await click('Lưu nhánh');
  assert.equal(created.csrf, 'tree-csrf');
  assert.deepEqual(created.body, { name: 'Tài liệu nhập môn', node_kind: 'folder', parent_id: 2, sort_order: 0 });
  assert.equal(reads.at(-1).get('node_id'), '5');
  assert.equal(window.location.hash, '#/thu-vien?node=5');
});
