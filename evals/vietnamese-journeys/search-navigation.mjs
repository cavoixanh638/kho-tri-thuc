import assert from 'node:assert/strict';

// These are read-only actions on the established 36-note Windows QA pilot.
export async function checkSearchNavigation({ page, wait, items, labels, seed, knownIds }) {
  const steps = [];
  const query = Object.fromEntries(labels.judgments.map(entry => [entry.id, entry.query]));
  const searchInput = '.search-form input[type="search"]';
  const topicSelect = '.search-form select';
  const folder = 'thu âm';
  let topicId;

  async function submit(newText) {
    if (newText !== undefined) {
      await page.eval(selector => { const input = document.querySelector(selector); input.focus(); input.select(); }, searchInput);
      await page.send('Input.insertText', { text: newText });
      assert.equal(await page.eval(selector => document.querySelector(selector).value, searchInput), newText);
    }
    await page.eval(() => document.querySelector('.search-form button[type="submit"]').click());
  }

  async function chooseTopic(name) {
    await wait(selector => document.querySelector(selector)?.options.length > 1, topicSelect);
    const option = await page.eval(({ selector, name }) => {
      const select = document.querySelector(selector);
      select.focus();
      const index = [...select.options].findIndex(option => option.textContent === name);
      return index < 0 ? null : { index, value: select.options[index].value };
    }, { selector: topicSelect, name });
    assert.ok(option, 'Missing pilot topic ' + name);
    async function key(name, code) {
      for (const type of ['keyDown', 'keyUp']) {
        await page.send('Input.dispatchKeyEvent', { type, key: name, code: name, windowsVirtualKeyCode: code });
      }
    }
    await key('Home', 36);
    for (let i = 0; i < option.index; i++) await key('ArrowDown', 40);
    await wait(({ selector, value }) => document.querySelector(selector)?.value === value, { selector: topicSelect, value: option.value });
    return option.value;
  }

  async function checkResults(action, target, { filtered = false, expanded = false, present = false } = {}) {
    const criteria = { query: query[target], topic: filtered ? topicId : '', expanded, searchInput, topicSelect };
    await wait(expected => {
      const panel = document.querySelector('.search-results');
      const params = new URLSearchParams(location.hash.split('?')[1]);
      const select = document.querySelector(expected.topicSelect);
      return location.hash.split('?')[0] === '#/tim-kiem' && params.get('q') === expected.query
        && (params.get('topic_id') ?? '') === expected.topic && (params.get('expand') === 'true') === expected.expanded
        && !params.has('cursor_item_id') && document.querySelector(expected.searchInput)?.value === expected.query
        && select?.options.length > 1 && select.value === expected.topic
        && panel !== window.qaNavigationLastPanel && Boolean(panel?.querySelector('.search-list, .empty-state'));
    }, criteria);
    const state = await page.eval(() => {
      const panel = document.querySelector('.search-results');
      window.qaNavigationLastPanel = panel;
      const list = panel.querySelector('.search-list');
      const notice = panel.querySelector('#search-partial-match');
      const ids = [...panel.querySelectorAll('li h3 a')].map(a => a.hash.replace('#/muc/', ''));
      const actions = [...panel.querySelectorAll('a')].map(a => a.textContent);
      return { ids, partial: Boolean(notice?.getClientRects().length && list?.getAttribute('aria-describedby') === notice.id),
        canExpand: actions.includes('Tìm gần đúng'), canReturn: actions.includes('Về kết quả ban đầu') };
    });
    assert.ok(state.ids.every(id => knownIds.has(id)), action + ': unexpected note');
    assert.equal(state.ids.includes(seed.items[target]), present, action + ': target presence');
    assert.equal(state.canReturn, expanded, action + ': return link');
    if (expanded) {
      assert.equal(state.canExpand, false, action + ': repeated expansion');
      if (state.ids.length) assert.ok(state.partial, action + ': expanded notes must be labeled');
    }
    steps.push({ action, query_for: target, topic: filtered ? folder : null, expanded, partial_label: state.partial,
      results: state.ids.map(id => knownIds.get(id)) });
    return state;
  }

  async function checkArticle(action, target) {
    const note = items.get(target);
    await wait(expected => location.hash === '#/muc/' + expected.id && document.querySelector('main h1')?.textContent === expected.title
      && document.querySelector('.markdown-item-detail .raw-knowledge pre')?.textContent === expected.note,
    { ...note, id: seed.items[target] });
    steps.push({ action, article: target, raw_note_verified: true });
  }

  async function openArticle(target) {
    await page.eval(id => document.querySelector(`.search-list a[href="#/muc/${id}"]`).click(), seed.items[target]);
  }

  await page.eval(() => document.querySelector('a[href="#/tim-kiem"]').click());
  await wait(selector => document.querySelector(selector)?.value === '', searchInput);
  await submit(query.M02);
  const initial = await checkResults('submit_memory_query', 'M02');
  assert.ok(initial.canExpand, 'Fixture must offer expansion');
  await page.eval(() => [...document.querySelectorAll('.search-results a')].find(a => a.textContent === 'Tìm gần đúng').click());
  await checkResults('expand', 'M02', { expanded: true, present: true });
  await openArticle('M02');
  await checkArticle('open_expanded_result', 'M02');
  await page.eval(() => history.back());
  await checkResults('back_to_expansion', 'M02', { expanded: true, present: true });
  await page.eval(() => history.forward());
  await checkArticle('forward_reopens_article', 'M02');
  await page.eval(() => history.back());
  await checkResults('back_from_article', 'M02', { expanded: true, present: true });
  await page.eval(() => history.back());
  await checkResults('back_to_initial_search', 'M02');
  await page.eval(() => history.forward());
  await checkResults('forward_restores_expansion', 'M02', { expanded: true, present: true });
  await submit(query.M14);
  await checkResults('new_query_exits_expansion', 'M14', { present: true });
  await page.eval(() => history.back());
  await checkResults('back_restores_previous_query_and_mode', 'M02', { expanded: true, present: true });

  topicId = await chooseTopic(folder);
  await submit();
  await checkResults('submit_topic_drops_expansion', 'M02', { filtered: true });
  await page.eval(() => history.back());
  await checkResults('back_removes_filter', 'M02', { expanded: true, present: true });
  await page.eval(() => history.forward());
  await checkResults('forward_restores_filter', 'M02', { filtered: true });
  await submit(query.M14);
  await checkResults('change_query_keeps_filter', 'M14', { filtered: true });
  await chooseTopic('Tất cả');
  await submit();
  await checkResults('remove_filter_restores_note', 'M14', { present: true });
  await openArticle('M14');
  await checkArticle('open_unfiltered_result', 'M14');
  return steps;
}
