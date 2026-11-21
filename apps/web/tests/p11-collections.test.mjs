// P11: independent KT125 cross-view audit; no production component edits.
import assert from 'node:assert/strict';
import { before, after, test } from 'node:test';
import { createServer } from 'vite';
import { JSDOM } from 'jsdom';

let vite, react, library;
before(async () => {
  vite = await createServer({
    server: { middlewareMode: true, hmr: false },
    appType: 'custom', logLevel: 'silent',
  });
  react = await vite.ssrLoadModule('/tests/kt125-entry.tsx');
  library = await vite.ssrLoadModule('/src/LibraryViews.tsx');
});
after(async () => { await vite?.close(); });

function row(n, extras = {}) {
  return {
    item_id: '00000000-0000-4000-8000-' + String(n + 1).padStart(12, '0'),
    kind: 'text', title: 'Tri thức ' + n, description: '', note: '# Ghi chú ' + n,
    original_url: '', assets: [], favorite: n % 2 === 0,
    classification_status: 'pending', source_fetch: 'not_applicable',
    asset_storage: 'not_applicable', content_extract: 'not_available',
    saved_at: new Date(Date.UTC(2026, 10, 20 + n % 3, 15)).toISOString(),
    published_at: n % 4 === 0 ? null : new Date(Date.UTC(2025, 1, 1 + n % 5)).toISOString(),
    updated_at: new Date(Date.UTC(2026, 10, 21)).toISOString(),
    user_edit_version: 0, deleted: false, ...extras,
  };
}
function viewIds(items, mode) {
  const html = react.renderToStaticMarkup(
    react.createElement(library.LibraryViews, { items, mode }),
  );
  const document = new JSDOM(html).window.document;
  return { ids: [...document.querySelectorAll('[data-library-item]')]
    .map(node => node.getAttribute('data-library-item')), document, html };
}
const modes = ['list', 'table', 'card', 'timeline'];

test('every view displays exactly the same 50 IDs on each of two pages', () => {
  const all = Array.from({ length: 120 }, (_, n) => row(n));
  for (const [start, end] of [[0, 50], [50, 100], [100, 120]]) {
    const slice = all.slice(start, end);
    const expected = slice.map(item => item.item_id).sort();
    for (const mode of modes) {
      const { ids } = viewIds(slice, mode);
      assert.equal(ids.length, slice.length, mode);
      assert.equal(new Set(ids).size, slice.length, mode + ' duplicate');
      assert.deepEqual([...ids].sort(), expected, mode + ' membership');
    }
  }
});

test('published_at remains distinct from saved_at in table and timeline', () => {
  const item = row(9, {
    saved_at: '2026-11-21T17:30:00Z',
    published_at: '2025-02-01T00:00:00Z',
  });
  const table = viewIds([item], 'table').document;
  const times = [...table.querySelectorAll('tbody time')];
  assert.equal(times.length, 2);
  assert.equal(times[0].getAttribute('datetime'), item.saved_at);
  assert.equal(times[1].getAttribute('datetime'), item.published_at);
  const timeline = viewIds([item], 'timeline').document;
  assert.equal(timeline.querySelectorAll('[data-library-item]').length, 1);
  assert.match(timeline.querySelector('section').getAttribute('aria-label'), /22\/11\/2026/);
});

test('HTML-looking collection Item fields stay escaped in four views', () => {
  const hostile = row(11, {
    title: '<script>alert(1)</script>',
    note: '<img src=x onerror=alert(1)>',
  });
  for (const mode of modes) {
    const { document } = viewIds([hostile], mode);
    assert.equal(document.querySelectorAll('script,img').length, 0, mode);
    assert.equal(document.querySelectorAll('[data-library-item]').length, 1);
  }
});

test('timeline exposes non-contiguous grouping order divergence without losing IDs', () => {
  // Server published-desc order may interleave saved dates: A(20), B(21), C(20).
  // The current Timeline groups all 20th rows into one section: A,C,B.
  // This is an audit repro, not a request to change LibraryViews (owned by P01).
  const rows = [
    row(0, { saved_at: '2026-11-20T00:00:00Z', published_at: '2026-11-22T00:00:00Z' }),
    row(1, { saved_at: '2026-11-21T00:00:00Z', published_at: '2026-11-21T00:00:00Z' }),
    row(2, { saved_at: '2026-11-20T00:00:00Z', published_at: '2026-11-20T00:00:00Z' }),
  ];
  const input = rows.map(item => item.item_id);
  const table = viewIds(rows, 'table');
  const timeline = viewIds(rows, 'timeline');
  assert.deepEqual(table.ids, input);
  assert.deepEqual([...timeline.ids].sort(), [...input].sort());
  assert.deepEqual(timeline.ids, [input[0], input[2], input[1]]);
  assert.notDeepEqual(timeline.ids, input);
  assert.match(table.document.querySelector('caption').textContent, /Thứ tự nhận lần đầu/);
});

test('saved collection deep link is an allowlisted UUID, not script or path injection', () => {
  const good = row(0).item_id;
  assert.equal(react.collectionIdFromHash(react.collectionHref(good)), good);
  assert.equal(react.collectionIdFromHash('#/thu-vien?collection=new'), 'new');
  for (const bad of ['javascript:alert(1)', '../other', 'null', '1%27%3Bdrop']) {
    assert.equal(react.collectionIdFromHash('#/thu-vien?collection=' + bad), undefined);
  }
});
