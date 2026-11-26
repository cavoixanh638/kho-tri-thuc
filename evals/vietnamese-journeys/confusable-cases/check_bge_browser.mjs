import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { setTimeout } from 'node:timers/promises';
import { Browser } from '../../../tools/smoke/p08_cdp.mjs';

assert.equal(process.env.KT_EVAL_BROWSER_QA, '1');
const origin = new URL(process.env.KT_EVAL_BROWSER_ORIGIN);
assert.match(origin.origin, /^http:\/\/127\.0\.0\.1:\d+$/u);
const runnerRoot = fileURLToPath(new URL('../../../', import.meta.url));
const json = async (path) => JSON.parse(await readFile(path, 'utf8'));
const seed = await json(process.env.KT_EVAL_BROWSER_SEED);
assert.equal(seed.username, 'kt-eval-edge-pairs-main');
const baseline = process.env.KT_EVAL_BROWSER_LEXICAL_REPORT
  ? await json(process.env.KT_EVAL_BROWSER_LEXICAL_REPORT) : null;
const password = process.env.KT_EVAL_BROWSER_PASSWORD;
assert.ok(password, 'Missing synthetic account password');

const browser = await Browser.launch();
try {
  const page = await browser.newPage();
  const chromium = (await page.send('Browser.getVersion')).product;
  const wait = async (predicate, argument, description) => {
    const deadline = performance.now() + 15000;
    do {
      const value = await page.eval(predicate, argument);
      if (value) return value;
      await setTimeout(50);
    } while (performance.now() < deadline);
    throw Error('Chromium did not show ' + description);
  };
  async function type(selector, text) {
    await wait(sel => Boolean(document.querySelector(sel)), selector, selector);
    await page.eval(sel => document.querySelector(sel).focus(), selector);
    await page.send('Input.insertText', { text });
  }
  async function click(selector, label = null) {
    const point = await wait(({ selector, label }) => {
      const element = [...document.querySelectorAll(selector)]
        .find(node => label === null || node.textContent === label);
      if (!element?.getClientRects().length) return null;
      element.scrollIntoView({ block: 'nearest' });
      const rect = element.getBoundingClientRect();
      return { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2 };
    }, { selector, label }, label ?? selector);
    await page.send('Input.dispatchMouseEvent', { type: 'mousePressed', ...point, button: 'left', clickCount: 1 });
    await page.send('Input.dispatchMouseEvent', { type: 'mouseReleased', ...point, button: 'left', clickCount: 1 });
  }

  await page.goto(origin.href);
  await type('input[autocomplete="username"]', seed.username);
  await type('input[autocomplete="current-password"]', password);
  await click('form button[type="submit"]');
  await wait(() => Boolean(document.querySelector('a[href="#/tim-kiem"]')), null, 'authenticated navigation');
  assert.equal(await page.eval(async () => (await (await fetch('/api/v1/session')).json()).username), seed.username);
  await page.eval(() => {
    window.qaSearchResponses = [];
    const fetchOriginal = window.fetch;
    window.fetch = async (...args) => {
      const response = await fetchOriginal.apply(window, args);
      if (new URL(response.url).pathname === '/api/v1/search') {
        const copy = response.clone();
        window.qaSearchResponses.push({ url: copy.url, status: copy.status, body: await copy.json() });
      }
      return response;
    };
  });
  const initialRoute = new URLSearchParams({ q: seed.query, topic_id: seed.topic_id });
  await page.eval(params => { location.hash = '#/tim-kiem?' + params; }, String(initialRoute));

  async function checkScreen(step, expanded, ranking, responseIndex) {
    const query = { q: seed.query, topic_id: seed.topic_id };
    const desiredRoute = String(new URLSearchParams({ ...query, ...(expanded ? { expand: 'true' } : {}) }));
    const action = expanded ? 'Về kết quả ban đầu' : 'Tìm gần đúng';
    const { ids, captured } = await wait(({ desiredRoute, action, responseIndex, query }) => {
      if (location.hash !== '#/tim-kiem?' + desiredRoute) return null;
      const panel = document.querySelector('.search-results');
      if (!panel || ![...panel.querySelectorAll('a')].some(a => a.textContent === action && a.getClientRects().length)) return null;
      if (!panel.querySelector('.search-list, .empty-state')) return null;
      if (document.querySelector('.search-form input[type="search"]')?.value !== query.q
          || document.querySelector('.search-form select')?.value !== query.topic_id) return null;
      const captured = window.qaSearchResponses[responseIndex];
      if (!captured) return null;
      const ids = [...panel.querySelectorAll('li h3 a')].map(a => a.hash.replace('#/muc/', ''));
      return { ids, captured };
    }, { desiredRoute, action, responseIndex, query }, step);
    const url = new URL(captured.url);
    assert.equal(url.origin, origin.origin);
    assert.deepEqual(Object.fromEntries(url.searchParams), {
      ...query, limit: '25', ...(expanded ? { expand: 'true' } : {}),
    });
    assert.equal(captured.status, 200);
    assert.equal(captured.body.ranking, ranking);
    assert.equal(captured.body.can_expand, !expanded);
    assert.deepEqual(ids, captured.body.results.map(hit => hit.item_id));
    const results = ids.map(id => seed.items[id]);
    assert.ok(results.every(Boolean));
    return { step, route: desiredRoute, limit: 25, ranking, results, target_rank: results.indexOf(seed.target) + 1 };
  }

  const initial = await checkScreen('initial', false, 'lexical', 0);
  await click('.search-results a', 'Tìm gần đúng');
  const expanded = await checkScreen('expanded', true, baseline ? 'bge' : 'lexical', 1);
  assert.equal(expanded.target_rank, baseline ? 1 : 4);
  await click('.search-results a', 'Về kết quả ban đầu');
  const returned = await checkScreen('returned', false, 'lexical', 2);
  assert.deepEqual(returned.results, initial.results);
  assert.equal(await page.eval(() => window.qaSearchResponses.length), 3);
  if (baseline) {
    assert.deepEqual(baseline.fixture_sha256, seed.fixture_sha256);
    assert.equal(baseline.chromium, chromium);
    assert.deepEqual(baseline.initial, initial);
    assert.equal(baseline.expanded.ranking, 'lexical');
    assert.equal(baseline.expanded.target_rank, 4);
    assert.equal(baseline.expanded.route, expanded.route);
    assert.deepEqual([...baseline.expanded.results.slice(0, 5)].sort(), [...expanded.results.slice(0, 5)].sort());
    assert.deepEqual(baseline.expanded.results.slice(5), expanded.results.slice(5));
  }
  const report = {
    code_sha: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: runnerRoot, encoding: 'utf8' }).trim(),
    chromium, case: 'L16', target: seed.target, fixture_sha256: seed.fixture_sha256, initial, expanded, returned,
  };
  await writeFile(process.env.KT_EVAL_BROWSER_REPORT, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify(report));
} finally {
  await browser.close();
}
