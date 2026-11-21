import assert from 'node:assert/strict';
import { after, afterEach, before, beforeEach, test } from 'node:test';
import { setImmediate as settle } from 'node:timers/promises';
import { createServer } from 'vite';
import { JSDOM, VirtualConsole } from 'jsdom';

let server, ui, dom, root, container, calls;
const originalFetch = globalThis.fetch;
const reply = (data, status = 200) => new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });
before(async () => {
  dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'http://127.0.0.1:5173/', pretendToBeVisual: true, virtualConsole: new VirtualConsole() });
  for (const name of ['window', 'document', 'location', 'navigator', 'HTMLElement', 'Element', 'Node', 'Event', 'MouseEvent', 'CustomEvent', 'MutationObserver', 'getComputedStyle']) {
    Object.defineProperty(globalThis, name, { value: name === 'getComputedStyle' ? dom.window[name].bind(dom.window) : dom.window[name], configurable: true, writable: true });
  }
  window.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
  globalThis.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
  Object.defineProperty(document, 'fonts', { value: new dom.window.EventTarget(), configurable: true });
  globalThis.requestAnimationFrame = window.requestAnimationFrame.bind(window); globalThis.cancelAnimationFrame = window.cancelAnimationFrame.bind(window);
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  server = await createServer({ server: { middlewareMode: true, hmr: false, host: '127.0.0.1' }, appType: 'custom', logLevel: 'silent' });
  ui = await server.ssrLoadModule('/tests/kt119-entry.tsx');
});
beforeEach(() => {
  container = document.createElement('div'); document.body.append(container); root = ui.createRoot(container); calls = [];
  globalThis.fetch = async (path, options) => { calls.push({ path, method: options?.method ?? 'GET' }); return reply(ui.connections); };
});
afterEach(async () => { await ui.act(async () => { root.unmount(); await settle(); }); container.remove(); globalThis.fetch = originalFetch; });
after(async () => { await server?.close(); dom?.window.close(); });
async function render(component = ui.RelatedItems, props = {}) {
  await ui.act(async () => { root.render(ui.createElement(ui.MantineProvider, { forceColorScheme: 'light' }, ui.createElement(component, { id: ui.corpus.target, ...props }))); await settle(); });
}
async function click(label) {
  const button = [...container.querySelectorAll('button')].find((entry) => entry.textContent === label); assert.ok(button, label);
  await ui.act(async () => { button.click(); await settle(); });
}
test('30 Item fixture has separate 15 explicit backlinks / 10 related / 5 same-group destinations', async () => {
  await render();
  assert.equal(ui.corpus.items.length, 30);
  assert.match(container.querySelector('#item-related-title').textContent, /\(10\)/);
  assert.match(container.querySelector('#item-backlinks-title').textContent, /\(15\)/);
  assert.match(container.querySelector('#item-samegroup-title').textContent, /\(5\)/);
  for (const [heading, flag, expected] of [['item-related-title', 'related', 10], ['item-backlinks-title', 'backlink', 15], ['item-samegroup-title', 'same_group', 5]]) {
    const links = [...container.querySelector('#' + heading).parentElement.querySelectorAll('a')];
    assert.equal(links.length, expected);
    assert.deepEqual(new Set(links.map((link) => link.getAttribute('href'))), new Set(ui.corpus.items.filter((item) => item[flag]).map((item) => '#/muc/' + item.item_id)));
  }
  assert.ok(container.textContent.includes('lexical-v3')); assert.ok(container.textContent.includes('fixture-source-15'));
  assert.ok(container.textContent.includes('không phải xác suất đã kiểm chứng'));
  assert.equal(calls.filter((call) => call.path.endsWith('/related')).length, 1);
  assert.ok(calls.every((call) => call.method === 'GET'), 'reference/context panels are read-only');
});
test('hiding a similar suggestion is reversible display-only; curated relation and pinned groups remain untouched', async () => {
  const snapshot = JSON.stringify(ui.connections);
  await render();
  assert.equal(container.querySelectorAll('.related-items > li').length, 10);
  assert.equal([...container.querySelectorAll('button')].filter((button) => button.textContent === 'Ẩn gợi ý trong lần xem này').length, 9);
  await click('Ẩn gợi ý trong lần xem này');
  assert.equal(container.querySelectorAll('.related-items > li').length, 9);
  assert.ok(container.textContent.includes('Đã ẩn 1 gợi ý')); assert.match(container.querySelector('#item-related-title').textContent, /\(10\)/);
  assert.ok(container.textContent.includes('curated_reference'));
  await click('Hiện lại gợi ý'); assert.equal(container.querySelectorAll('.related-items > li').length, 10);
  assert.equal(JSON.stringify(ui.connections), snapshot);
  assert.equal(calls.filter((call) => call.path.endsWith('/related')).length, 1);
  assert.ok(calls.every((call) => call.method === 'GET'), 'hiding does not mutate any reference or relation');
});
test('source cards deduplicate source/assets, show actual versions and verified/missing/pending states', async () => {
  await render();
  assert.equal(container.querySelectorAll('.related-source-card').length, 6);
  assert.equal(container.querySelectorAll('[id^="related-asset-"]').length, 3);
  assert.ok(container.textContent.includes('VERIFIED')); assert.ok(container.textContent.includes('MISSING')); assert.ok(container.textContent.includes('PENDING'));
  assert.ok(container.textContent.includes('tệp phiên bản 2')); assert.ok(container.textContent.includes('phiên bản v1'));
  assert.ok(container.textContent.includes('Trang 3')); assert.ok(container.textContent.includes('Mốc 12–18 giây'));
  const references = [...container.querySelectorAll('.related-asset-references a')]; assert.equal(references.length, 2);
  await ui.act(async () => { references[0].click(); await settle(); });
  assert.equal(document.activeElement.id, references[0].getAttribute('href').slice(1));
  assert.ok(container.textContent.includes('Chưa có văn bản trích từ tệp'));
});
test('active URL/HTML source data is inert, invalid IDs never become item or asset links', async () => {
  const bad = structuredClone(ui.connections);
  bad.results.push({ ...bad.results[0], item_id: 'javascript:alert(1)', title: '<img src=x onerror=alert(1)>' });
  bad.results.push({ ...bad.results[0], item_id: ui.corpus.target });
  bad.evidence.sources.push({ source_id: 4, original_url: 'https://user:password@example.invalid', asset_ids: ['bad-id'], parts: [] });
  bad.evidence.assets.push({ ...bad.evidence.assets[0], asset_id: 'javascript:alert(1)' });
  globalThis.fetch = async () => reply(bad);
  await render();
  assert.equal(container.querySelectorAll('script,img,iframe,a[href^="javascript:"],a[href^="data:"],a[href*="password"]').length, 0);
  assert.equal(container.querySelectorAll('.related-items > li').length, 10);
  assert.equal(container.querySelectorAll('[id^="related-asset-"]').length, 3);
  for (const link of container.querySelectorAll('a[target="_blank"]')) assert.equal(link.rel, 'noopener noreferrer');
});
test('old or mismatched derived versions cannot display a current locator', async () => {
  const bad = structuredClone(ui.connections);
  bad.evidence.assets[0].parts[1].locator = { page: 99, start_seconds: 999 };
  bad.evidence.assets[0].parts.push({ ...bad.evidence.assets[0].parts[0], id: 100, matches_current_asset: false, locator: { page: 88 } });
  globalThis.fetch = async () => reply(bad); await render();
  assert.ok(!container.textContent.includes('Trang 99')); assert.ok(!container.textContent.includes('Trang 88')); assert.ok(!container.textContent.includes('999 giây'));
  assert.ok(container.textContent.includes('Hash đầu vào khác tệp hiện tại'));
});
test('source evidence exposes an optional asset callback without inventing a viewer route', async () => {
  const opened = [];
  await render(ui.SourceEvidence, { evidence: ui.connections.evidence, onOpenAsset: (id) => opened.push(id) });
  await click('Mở tệp'); assert.deepEqual(opened, [ui.connections.evidence.assets[0].asset_id]);
});
test('zero samples show honest empty states and no accuracy assertion', async () => {
  globalThis.fetch = async () => reply({ results: [], backlinks: [], same_group: [], counts: { related: 0, backlinks: 0, same_group: 0 }, evidence: { sources: [], assets: [], unassociated_parts: [], truncated: false } });
  await render(); assert.ok(container.textContent.includes('Chưa tìm thấy liên kết trực tiếp')); assert.ok(container.textContent.includes('Chưa có bài cùng nhóm'));
  assert.ok(container.textContent.includes('Chưa có nguồn hoặc tệp')); assert.ok(!container.textContent.includes('100%'));
});
for (const status of [401, 403, 404, 500]) test(`API ${status} hides all source/relationship data`, async () => {
  globalThis.fetch = async () => reply({ title: 'PRIVATE' }, status);
  await render(); assert.ok(container.textContent.includes('Chưa tải được')); assert.equal(container.querySelectorAll('a').length, 0); assert.ok(!container.textContent.includes('PRIVATE'));
});
test('refresh updates provenance while preserving local hidden state; another Item resets it', async () => {
  await render(ui.RelatedSources, { refreshKey: 'one' }); await click('Ẩn gợi ý trong lần xem này');
  await render(ui.RelatedSources, { refreshKey: 'two' }); assert.ok(container.textContent.includes('Đã ẩn 1 gợi ý'));
  await render(ui.RelatedSources, { id: '30000000-0000-4000-8000-000000000001', refreshKey: 'three' });
  assert.ok(!container.textContent.includes('Đã ẩn 1 gợi ý'));
});
test('bounded API lists disclose larger totals and truncated source evidence', async () => {
  const bounded = structuredClone(ui.connections); bounded.counts = { related: 50, backlinks: 40, same_group: 20 }; bounded.evidence.truncated = true;
  globalThis.fetch = async () => reply(bounded); await render();
  assert.ok(container.textContent.includes('10 trong 50')); assert.ok(container.textContent.includes('15 trong 40')); assert.ok(container.textContent.includes('5 trong 20'));
  assert.ok(container.textContent.includes('chưa phải toàn bộ bằng chứng'));
});
