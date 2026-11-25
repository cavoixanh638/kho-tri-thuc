import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { Browser } from '../../tools/smoke/p08_cdp.mjs';

const origin = new URL(process.env.KT_EVAL_BROWSER_ORIGIN || 'http://127.0.0.1:62310');
assert.match(origin.origin, /^http:\/\/(?:127\.0\.0\.1|localhost):\d+$/u);
const byName = (name) => new URL(name, import.meta.url);
const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');
const json = (bytes) => JSON.parse(bytes.toString('utf8').replace(/^\uFEFF/, ''));
const [corpusBytes, labelBytes, seedBytes] = await Promise.all([
  readFile(byName('corpus.json')), readFile(byName('provisional.json')),
  readFile(process.env.KT_EVAL_BROWSER_SEED),
]);
const corpus = json(corpusBytes);
const labels = json(labelBytes);
const seed = json(seedBytes);
assert.equal(seed.corpus_sha256, hash(corpusBytes));
assert.equal(corpus.items.length, 36);
assert.equal(labels.judgments.length, 36);
assert.equal(labels.negative_queries.length, 3);
assert.ok(/^kt-browser-eval-[\w-]+$/u.test(process.env.KT_EVAL_BROWSER_USER ?? ''), 'Expected a dedicated QA account');
assert.equal(process.env.KT_EVAL_BROWSER_QA, '1');

const repo = fileURLToPath(byName('../../'));
const codeSha = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repo, encoding: 'utf8' }).trim();
const status = execFileSync('git', ['status', '--porcelain', '--', 'apps/backend', 'apps/web'], { cwd: repo, encoding: 'utf8' });
const knownIds = new Map(Object.entries(seed.items).map(([key, id]) => [id, key]));
assert.equal(knownIds.size, 36);
const items = new Map(corpus.items.map(item => [item.id, item]));
const rows = [];

function latency(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const percentile = (fraction) => sorted.length ? sorted[Math.ceil(sorted.length * fraction) - 1] : null;
  return { samples: sorted.length, p50: percentile(.50), p95: percentile(.95), max: sorted.at(-1) ?? null };
}

function summarize(records) {
  const positive = records.filter(row => row.target);
  const negative = records.filter(row => !row.target);
  return {
    queries: records.length,
    target_at_rank1: { count: positive.filter(row => row.rank === 1).length, total: positive.length },
    target_in_top5: { count: positive.filter(row => row.rank > 0 && row.rank <= 5).length, total: positive.length },
    clicked: positive.filter(row => row.open).length,
    opened_correctly: positive.filter(row => row.open?.correct).length,
    opened_wrong: positive.filter(row => row.open && !row.open.correct).length,
    negative_with_results: { count: negative.filter(row => row.results.length).length, total: negative.length },
    search_to_render_ms: latency(records.map(row => row.search_ms)),
    click_to_article_ms: latency(records.flatMap(row => row.open?.correct ? [row.open.ms] : [])),
    submit_to_article_ms: latency(records.flatMap(row => row.open?.correct ? [row.open.total_ms] : [])),
  };
}

const browser = await Browser.launch();
try {
  const page = await browser.newPage({ width: 1440, height: 900 });
  const chromium = await page.send('Browser.getVersion');
  const wait = async (predicate, argument) => {
    const deadline = performance.now() + 10000;
    do {
      if (await page.eval(predicate, argument)) return;
      await new Promise(resolve => setTimeout(resolve, 25));
    } while (performance.now() < deadline);
    throw Error('Expected QA control did not appear');
  };
  async function type(selector, text) {
    await wait(sel => Boolean(document.querySelector(sel)), selector);
    await page.eval(sel => document.querySelector(sel).focus(), selector);
    await page.send('Input.insertText', { text });
  }

  await page.goto(origin.href);
  await type('input[autocomplete="username"]', process.env.KT_EVAL_BROWSER_USER);
  await type('input[autocomplete="current-password"]', process.env.KT_EVAL_BROWSER_PASSWORD);
  await page.eval(() => document.querySelector('form button[type="submit"]').click());
  await wait(() => Boolean(document.querySelector('a[href="#/tim-kiem"]')));
  const session = await page.eval(async () => (await fetch('/api/v1/session')).json());
  assert.ok(session.username === process.env.KT_EVAL_BROWSER_USER, 'Unexpected QA session');
  const inventory = await page.eval(async () => (await fetch('/api/v1/items?limit=50')).json());
  assert.deepEqual(new Set(inventory.results.map(item => item.item_id)), new Set(knownIds.keys()), 'Unexpected items for QA account');

  const cases = [...labels.judgments.map(label => ({ ...label, split: items.get(label.id).split })), ...labels.negative_queries];
  for (const entry of cases) {
    await page.eval(() => { window.location.hash = '#/tim-kiem'; });
    await wait(() => location.hash === '#/tim-kiem' && document.querySelector('.search-form input')?.value === '');
    await type('.search-form input[type="search"]', entry.query);
    const targetItem = items.get(entry.id);
    const measurement = await page.eval(async (expected) => {
      const form = document.querySelector('.search-form');
      if (form.querySelector('input').value !== expected.query) throw Error('Search text did not reach form');
      const visible = async (read) => {
        const expires = performance.now() + 10000;
        while (performance.now() < expires) {
          await new Promise(resolve => requestAnimationFrame(resolve));
          const result = read();
          if (result !== null) return result;
        }
        throw Error('Search or article did not render');
      };
      const started = performance.now();
      form.querySelector('button[type="submit"]').click();
      const links = await visible(() => {
        const panel = document.querySelector('.search-results');
        if (!panel || !location.hash.includes('?') || !panel.querySelector('#search-results-title')) return null;
        if (panel.querySelector('.notice-error')) throw Error('Search API displayed an error');
        const results = [...panel.querySelectorAll('.search-list .search-result h3 a')];
        if (results.length) return results;
        if (panel.querySelector('.empty-state')) return [];
        return null;
      });
      const searchMs = performance.now() - started;
      const matches = links.map(link => link.getAttribute('href').replace('#/muc/', ''));
      const rank = expected.id ? matches.indexOf(expected.id) + 1 : null;
      if (!rank || rank > 5) return { matches, rank, searchMs, open: null };
      const clickedAt = performance.now();
      links[rank - 1].click();
      const article = await visible(() => {
        const detail = document.querySelector('.markdown-item-detail');
        if (!detail?.querySelector('.knowledge-text')?.textContent?.trim()) return null;
        return { hash: location.hash, title: document.querySelector('main h1')?.textContent ?? '',
          note: detail.querySelector('.raw-knowledge pre')?.textContent ?? '' };
      });
      const ms = performance.now() - clickedAt;
      return { matches, rank, searchMs, open: {
        correct: article.hash === '#/muc/' + expected.id && article.title === expected.title && article.note === expected.note,
        ms, total_ms: performance.now() - started,
      } };
    }, { query: entry.query, id: seed.items[entry.id] ?? null, title: targetItem?.title, note: targetItem?.note });
    assert.ok(measurement.matches.every(id => knownIds.has(id)), 'Unexpected item returned in QA search');
    rows.push({ split: entry.split, kind: entry.query_kind ?? 'negative', query: entry.query, target: entry.id ?? null,
      results: measurement.matches.map(id => knownIds.get(id)), rank: measurement.rank || null,
      search_ms: measurement.searchMs, open: measurement.open });
  }

  const allNotes = '#/thu-vien';
  await page.eval(href => { location.hash = href; }, allNotes);
  const noteLinks = '.knowledge-library-content a[href^="#/muc/"]';
  await wait(selector => new Set([...document.querySelectorAll(selector)].map(link => link.hash)).size === 36, noteLinks);
  assert.deepEqual(new Set(await page.eval(selector => [...document.querySelectorAll(selector)].map(link => link.hash), noteLinks)),
    new Set([...knownIds.keys()].map(id => '#/muc/' + id)), 'Unexpected links in rendered library');
  for (const [id, key] of knownIds) {
    const expected = { href: '#/muc/' + id, title: items.get(key).title, note: items.get(key).note };
    const sel = `.knowledge-library-content a[href="${expected.href}"]`;
    await wait(selector => Boolean(document.querySelector(selector)), sel);
    await page.eval(selector => document.querySelector(selector).click(), sel);
    await wait(entry => location.hash === entry.href && document.querySelector('main h1')?.textContent === entry.title
      && document.querySelector('.markdown-item-detail .knowledge-text')?.textContent?.trim()
      && document.querySelector('.markdown-item-detail .raw-knowledge pre')?.textContent === entry.note, expected);
    await page.eval(href => { location.hash = href; }, allNotes);
  }

  const topics = await page.eval(async () => (await (await fetch('/api/v1/knowledge-tree')).json()).nodes);
  assert.deepEqual(new Set(topics.map(topic => topic.name)), new Set(corpus.topics));
  const firstItem = knownIds.keys().next().value;
  await page.eval(id => { location.hash = '#/muc/' + id; }, firstItem);
  const placement = '[aria-label="Cấu trúc bài cha và bài con"] details';
  await wait(sel => [...document.querySelectorAll(sel)].some(details =>
    details.querySelector('summary')?.textContent === 'Chuyển thư mục / thêm lối tắt'), placement);
  await page.eval(sel => [...document.querySelectorAll(sel)].find(details =>
    details.querySelector('summary')?.textContent === 'Chuyển thư mục / thêm lối tắt').querySelector('summary').click(), placement);
  await wait(({ sel, count }) => [...document.querySelectorAll(`${sel} select option`)]
    .filter(option => option.value).length === count, { sel: placement, count: corpus.topics.length });
  const editableTopics = await page.eval(sel => [...document.querySelectorAll(`${sel} select option`)]
    .filter(option => option.value).map(option => option.textContent), placement);
  assert.deepEqual(new Set(editableTopics), new Set(corpus.topics));

  let correction;
  const correctionMode = process.env.KT_EVAL_BROWSER_CORRECTION;
  if (['1', 'verify'].includes(correctionMode)) {
    const target = { id: seed.items.M14, title: items.get('M14').title, topic: 'thu âm' };
    const folder = topics.find(topic => topic.name === target.topic);
    const assigned = () => page.eval(async ({ id, topic }) => {
      const response = await fetch(`/api/v1/items/${id}/organization`);
      if (!response.ok) throw Error('Could not check corrected topic');
      return (await response.json()).topics.some(group => group.name === topic);
    }, target);
    if (await assigned()) {
      assert.equal(correctionMode, '1', 'M14 still belongs to the corrected topic');
      await page.eval(id => { location.hash = '#/thu-vien?node=' + id; }, folder.id);
      const menuLabel = 'Thao tác ghi chú ' + target.title;
      await wait(label => [...document.querySelectorAll('.knowledge-explorer summary')]
        .some(summary => summary.getAttribute('aria-label') === label), menuLabel);
      await page.eval(label => [...document.querySelectorAll('.knowledge-explorer summary')]
        .find(summary => summary.getAttribute('aria-label') === label).click(), menuLabel);
      await wait(() => Boolean(document.querySelector('.knowledge-explorer details[open] .explorer-menu select')));
      await page.eval(id => {
        const menu = document.querySelector('.knowledge-explorer details[open] .explorer-menu');
        const select = menu.querySelector('select');
        select.value = String(id);
        select.dispatchEvent(new Event('change', { bubbles: true }));
        const remove = [...menu.querySelectorAll('button')].find(button => button.textContent === 'Bỏ khỏi nhánh đã chọn');
        if (!remove || remove.disabled) throw Error('Explorer removal control is unavailable');
        remove.click();
      }, folder.id);
      await wait(id => Boolean(document.querySelector('.knowledge-library-content .empty-state, .knowledge-library-content .library-list'))
        && !document.querySelector(`.knowledge-library-content a[href="#/muc/${id}"]`), target.id);
      assert.equal(await assigned(), false, 'Wrong topic remained assigned after Explorer removal');
      correction = { item: 'M14', topic: target.topic, action: 'removed_in_explorer', status: 'PASS' };
    } else {
      correction = { item: 'M14', topic: target.topic, action: 'already_absent', status: 'VERIFIED_ABSENT' };
    }
  }

  const assignments = await page.eval(async ids => Promise.all(ids.map(async id => {
    const response = await fetch(`/api/v1/items/${id}/organization`);
    if (!response.ok) throw Error('Could not verify pilot topic assignments');
    return (await response.json()).topics.filter(topic => topic.origin === 'auto').length;
  })), [...knownIds.keys()]);
  assert.ok(assignments.some(Boolean), 'Pilot has no automated topic memberships');

  const summary = summarize(rows);
  await writeFile(byName('results-browser-windows.json'), JSON.stringify({
    tested_sha: codeSha, app_source_dirty: Boolean(status), corpus_sha256: hash(corpusBytes), labels_sha256: hash(labelBytes),
    harness_sha256: hash(await readFile(new URL(import.meta.url))),
    platform: process.platform, chromium: chromium.product, viewport: '1440x900', items: 36,
    answer_origin: labels.origin, created_at: new Date().toISOString(),
    measurement: 'One loopback browser session. Measured from search button click to first animation frame with new list or empty state, and from target link click to rendered article. Typing and time spent choosing a result excluded. Percentiles use nearest rank.',
    pilot: { login: 'PASS', library_open_exact: knownIds.size, topics: topics.length, topics_in_placement_ui: editableTopics.length,
      auto_memberships: assignments.reduce((total, count) => total + count, 0),
      notes_with_auto_memberships: assignments.filter(Boolean).length, correction },
    summary, by_split: Object.fromEntries(['development', 'holdout'].map(split => [split, summarize(rows.filter(row => row.split === split))])),
    rows,
  }, null, 2) + '\n');
  console.log(JSON.stringify(summary));
  if (summary.opened_wrong) process.exitCode = 1;
} finally {
  await browser.close();
}
