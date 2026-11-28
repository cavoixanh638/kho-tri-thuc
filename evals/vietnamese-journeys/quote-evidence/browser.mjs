import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { setTimeout as pause } from 'node:timers/promises';
import { Browser } from '../../../tools/smoke/p08_cdp.mjs';

const repo = fileURLToPath(new URL('../../../', import.meta.url));
const origin = new URL(process.env.KT_EVAL_BROWSER_ORIGIN);
assert.match(origin.href, /^http:\/\/127\.0\.0\.1:\d+\/$/u, 'Use an isolated local QA deployment');
const seedInput = process.env.KT_EVAL_BROWSER_SEED;
const password = process.env.KT_EVAL_BROWSER_PASSWORD;
const reportPath = process.env.KT_EVAL_BROWSER_REPORT;
assert.ok(seedInput && password && reportPath, 'Missing seed, synthetic account password, or report path');
const seedText = seedInput.trimStart().startsWith('{') ? seedInput : await readFile(seedInput, 'utf8');
const seed = JSON.parse(seedText.replace(/^\uFEFF/u, ''));
assert.ok(seed.username, 'Missing synthetic account username');
assert.ok(Array.isArray(seed.cases) && seed.cases.length > 0, 'Expected at least one search case');
assert.ok(seed.cases.every(entry => entry.expected?.status === 'checked' && Array.isArray(entry.expected.answers)),
  'Each search case must specify a checked status and an answers array');

const browser = await Browser.launch();
try {
  const page = await browser.newPage();
  const chromium = (await page.send('Browser.getVersion')).product;
  async function waitFor(predicate, argument, description) {
    const deadline = performance.now() + 65000;
    do {
      const value = await page.eval(predicate, argument);
      if (value) return value;
      await pause(40);
    } while (performance.now() < deadline);
    const state = await page.eval(() => ({
      route: location.hash, title: document.querySelector('h1')?.textContent,
      recent: window.quoteQaRequests?.slice(-3).map(({ url, status }) => [new URL(url).pathname, status]),
    }));
    throw new Error('Chromium timed out waiting for ' + description + ' ' + JSON.stringify(state));
  }

  async function type(selector, text) {
    await waitFor(sel => Boolean(document.querySelector(sel)), selector, selector);
    await page.eval(sel => document.querySelector(sel).focus(), selector);
    await page.send('Input.insertText', { text });
  }

  async function click(selector, label = null) {
    const point = await waitFor(({ selector, label }) => {
      const element = [...document.querySelectorAll(selector)].find(node => label === null || node.textContent === label);
      if (!element?.getClientRects().length) return null;
      element.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'instant' });
      const rect = element.getClientRects()[0];
      const point = { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2 };
      return element.contains(document.elementFromPoint(point.x, point.y)) ? point : null;
    }, { selector, label }, label ?? selector);
    await page.send('Input.dispatchMouseEvent', { type: 'mousePressed', ...point, button: 'left', clickCount: 1 });
    await page.send('Input.dispatchMouseEvent', { type: 'mouseReleased', ...point, button: 'left', clickCount: 1 });
  }

  await page.goto(origin.href);
  await type('input[autocomplete="username"]', seed.username);
  await type('input[autocomplete="current-password"]', password);
  await click('form button[type="submit"]');
  await waitFor(() => Boolean(document.querySelector('a[href="#/tim-kiem"]')), null, 'authenticated navigation');
  assert.equal(await page.eval(async () => (await (await fetch('/api/v1/session')).json()).username), seed.username);

  await page.eval(() => {
    window.quoteQaRequests = [];
    const fetchOriginal = window.fetch;
    window.fetch = async (...args) => {
      const response = await fetchOriginal.apply(window, args);
      const url = new URL(response.url);
      if (url.pathname === '/api/v1/search' || /^\/api\/v1\/items\/[a-f\d-]{36}$/iu.test(url.pathname)) {
        const entry = { url: url.href, status: response.status };
        window.quoteQaRequests.push(entry);
        response.clone().json().then(body => { entry.body = body; }, () => { entry.invalidJson = true; });
      }
      return response;
    };
    document.addEventListener('click', event => {
      const action = event.target.closest('.search-results a');
      if (action?.textContent !== 'Tìm gần đúng') return;
      const started = performance.now();
      window.quoteQaClickRenderMs = null;
      const observer = new MutationObserver(() => {
        if (!document.querySelector('.search-results .search-quote p, #search-insufficient-evidence, #search-quote-unavailable')) return;
        window.quoteQaClickRenderMs = performance.now() - started;
        observer.disconnect();
        clearTimeout(timeout);
      });
      const timeout = setTimeout(() => observer.disconnect(), 65000);
      observer.observe(document.querySelector('main'), { childList: true, subtree: true });
    }, true);
  });

  const results = [];
  for (const entry of seed.cases) {
    const query = new URLSearchParams({ q: entry.query.trim() });
    for (const key of ['topic_id', 'project_id', 'tag_id']) {
      if (entry.filters?.[key]) query.set(key, String(entry.filters[key]));
    }
    const initialHash = '#/tim-kiem?' + query;
    const expectedParams = Object.fromEntries(query);
    await page.eval(hash => { location.hash = hash; }, initialHash);
    const initial = await waitFor(hash => {
      if (location.hash !== hash) return null;
      const panel = document.querySelector('.search-results');
      if (!panel?.querySelector('ol, .empty-state')) return null;
      if (![...panel.querySelectorAll('a')].some(a => a.textContent === 'Tìm gần đúng')) return null;
      return { ids: [...panel.querySelectorAll('li h3 a')].map(a => a.hash), requests: window.quoteQaRequests.length };
    }, initialHash, entry.id + ' initial results');
    assert.equal(await page.eval(() => Boolean(document.querySelector('.search-quote, #search-insufficient-evidence'))), false);
    await click('.search-results a', 'Tìm gần đúng');
    const expanded = await waitFor(start => {
      const capture = window.quoteQaRequests.slice(start).find(request => new URL(request.url).searchParams.get('expand') === 'true');
      const clickRenderMs = window.quoteQaClickRenderMs;
      if (!capture?.body || clickRenderMs === null) return null;
      const panel = document.querySelector('.search-results');
      const rows = [...panel.querySelectorAll('.search-list li')].map(row => {
        const answer = row.querySelector('.search-verification strong')?.textContent;
        return {
          item_id: row.querySelector('h3 a').hash.slice('#/muc/'.length),
          answer: { Có: 'yes', Không: 'no' }[answer],
          quotes: [...row.querySelectorAll('.search-quote p')].map(p => p.textContent),
        };
      });
      return { capture, clickRenderMs, rows, empty: Boolean(panel.querySelector('#search-insufficient-evidence')) };
    }, initial.requests, entry.id + ' checked search');
    const expandedUrl = new URL(expanded.capture.url);
    assert.equal(expandedUrl.origin, origin.origin);
    assert.deepEqual(Object.fromEntries(expandedUrl.searchParams), { ...expectedParams, expand: 'true', limit: '25' });
    assert.equal(expanded.capture.status, 200);
    const result = expanded.capture.body;
    assert.equal(result.quote_check.status, entry.expected.status);
    assert.deepEqual(expanded.rows, result.results.map(hit => ({ item_id: hit.item_id, ...hit.verification })));
    assert.deepEqual(expanded.rows, entry.expected.answers);
    assert.equal(expanded.empty, !entry.expected.answers.length);
    assert.ok(Number.isFinite(expanded.clickRenderMs) && expanded.clickRenderMs >= 0);
    const report = {
      id: entry.id, limit: 25, status: result.quote_check.status,
      click_to_render_ms: Math.round(expanded.clickRenderMs * 10) / 10, server_quote_check_ms: result.quote_check.elapsed_ms,
      results: expanded.rows.map(({ item_id, answer, quotes }) => ({ item_id, answer, quote_count: quotes.length })),
    };
    if (entry.expected.next_cursor) {
      assert.deepEqual(result.next_cursor, entry.expected.next_cursor);
      const offset = await page.eval(() => window.quoteQaRequests.length);
      await click('.search-results button', 'Trang sau');
      const next = await waitFor(({ offset, cursor }) => {
        const request = window.quoteQaRequests.slice(offset).find(r => new URL(r.url).searchParams.get('cursor_item_id') === cursor);
        if (!request?.body || !document.querySelector('.search-results .search-list, .search-results .empty-state')) return null;
        return { url: request.url, status: request.status, page: request.body };
      }, { offset, cursor: result.next_cursor.item_id }, entry.id + ' next page');
      assert.equal(next.status, 200);
      assert.deepEqual(Object.fromEntries(new URL(next.url).searchParams), {
        ...expectedParams, expand: 'true', limit: '25', cursor_score: String(result.next_cursor.score),
        cursor_item_id: result.next_cursor.item_id,
      });
      assert.equal(next.page.quote_check.status, 'checked');
      for (const hit of next.page.results) {
        assert.ok(hit.verification.quotes.length > 0);
        assert.ok(!expanded.rows.some(prior => prior.item_id === hit.item_id));
      }
      report.next_page = { checked: true, results: next.page.results.length };
    }
    if (expanded.rows.length) {
      const source = expanded.rows[0];
      const href = '#/muc/' + source.item_id;
      await click('.search-results h3 a[href="' + href + '"]');
      const item = await waitFor(({ href, itemId }) => {
        if (location.hash !== href || !document.querySelector('.raw-knowledge pre')) return null;
        return window.quoteQaRequests.find(request => new URL(request.url).pathname === '/api/v1/items/' + itemId)?.body;
      }, { href, itemId: source.item_id }, entry.id + ' opened original note');
      assert.equal(item.item_id, source.item_id);
      const sourceText = [item.title, item.description, item.note].filter(Boolean).join('\n');
      for (const quote of source.quotes) assert.ok(sourceText.includes(quote), 'Source contains the exact quote');
      report.source_opened = true;
      const history = await page.send('Page.getNavigationHistory');
      await page.send('Page.navigateToHistoryEntry', { entryId: history.entries[history.currentIndex - 1].id });
      await waitFor(() => Boolean(document.querySelector('.search-results .search-quote p')), null, entry.id + ' restored citation');
    }
    await click('.search-results a', 'Về kết quả ban đầu');
    const returned = await waitFor(hash => {
      const panel = document.querySelector('.search-results');
      if (location.hash !== hash || !panel?.querySelector('ol, .empty-state')) return null;
      if (![...panel.querySelectorAll('a')].some(a => a.textContent === 'Tìm gần đúng')) return null;
      return { ids: [...panel.querySelectorAll('li h3 a')].map(a => a.hash) };
    }, initialHash, entry.id + ' returned results');
    assert.deepEqual(returned.ids, initial.ids);
    report.returned_to_initial = true;
    results.push(report);
  }

  const report = {
    code_sha: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repo, encoding: 'utf8' }).trim(),
    chromium, origin: origin.origin, results,
  };
  await writeFile(reportPath, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify(report));
} finally {
  await browser.close();
}
