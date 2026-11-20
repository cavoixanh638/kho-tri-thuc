// Actual built application + Django/PostgreSQL QA; no mocked fetch transport.
// Supply the existing design skill CDP module and isolated QA credentials via env.
import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
import { execFileSync } from 'node:child_process';

const base = process.env.KT_UX_BROWSER_URL;
assert.equal(base, 'http://127.0.0.1:62300', 'Only the isolated QA web port is allowed');
assert.ok(process.env.KT_UX_BROWSER_USER && process.env.KT_UX_BROWSER_PASSWORD && process.env.KT_UX_CDP_MODULE);
const out = resolve(process.env.KT_UX_BROWSER_OUT ?? 'tmp/notes-ux-browser');
mkdirSync(out, { recursive: true });
const { Browser } = await import(pathToFileURL(process.env.KT_UX_CDP_MODULE).href);
const browser = await Browser.launch({ extraArgs: ['--no-proxy-server'] });
const report = { code_sha: execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(),
  transport: 'Real built React app, Django session+CSRF HTTP and isolated PostgreSQL; no worker/Drive/provider', checks: [], viewports: [] };
try {
  const page = await browser.newPage({ width: 1440, height: 900, reducedMotion: true });
  const wait = async (fn, arg) => {
    for (let attempt = 0; attempt < 100; attempt++) {
      if (await page.eval(fn, arg)) return;
      await new Promise((done) => setTimeout(done, 100));
    }
    throw new Error('Browser condition timed out: ' + fn.toString());
  };
  const click = async (label) => {
    await wait((label) => [...document.querySelectorAll('button')].some((button) => !button.disabled && (button.textContent === label || button.querySelector('strong')?.textContent === label)), label);
    await page.eval((label) => [...document.querySelectorAll('button')].find((button) => button.textContent === label || button.querySelector('strong')?.textContent === label).click(), label);
  };
  const fill = async (selector, text) => {
    await wait((selector) => !!document.querySelector(selector), selector);
    await page.eval((selector) => { const input = document.querySelector(selector); input.focus(); input.select(); }, selector);
    await page.send('Input.insertText', { text });
  };
  const api = (path, method = 'GET', body) => page.eval(async ({ path, method, body }) => {
    const session = await fetch('/api/v1/session').then((response) => response.json());
    const response = await fetch('/api/v1' + path, { method, credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': session.csrf_token },
      body: body && JSON.stringify(body) });
    return { status: response.status, data: await response.json() };
  }, { path, method, body });
  await page.goto(base);
  await fill('input[autocomplete="username"]', process.env.KT_UX_BROWSER_USER);
  await fill('input[autocomplete="current-password"]', process.env.KT_UX_BROWSER_PASSWORD);
  await click('Đăng nhập');
  await wait(() => !!document.querySelector('.capture-compose textarea'));
  assert.equal((await api('/items')).data.results.length, 0, 'Use a new empty synthetic QA account');
  const raw = '# Kiến thức tổng hợp\n\nTiếng Việt nguyên văn; media chỉ minh họa.\n';
  await fill('.capture-compose textarea', raw);
  await click('Gửi vào kho');
  await wait(() => !!document.querySelector('.receipt a'));
  const href = await page.eval(() => document.querySelector('.receipt a').getAttribute('href'));
  const id = href.split('/').at(-1);
  const captured = (await api('/items/' + id)).data;
  assert.equal(captured.note, raw); assert.equal(captured.assets.length, 0);
  const peer = await api('/captures', 'POST', { kind: 'text', text: '# Nguồn đối chiếu\n\n[Bài tri thức](#/muc/' + id + ')' });
  assert.equal(peer.status, 201);
  await page.eval((href) => { location.hash = href; }, href);
  await click('Chỉnh sửa');
  await page.eval(() => [...document.querySelectorAll('summary')].find((node) => node.textContent === 'Thêm mẫu ghi chú').click());
  await click('Bài học');
  assert.equal((await api('/items/' + id)).data.note, raw);
  await click('Thêm mẫu vào cuối');
  await click('Soạn + Xem trước');
  assert.ok(await page.eval(() => document.querySelector('.markdown-editor-preview').textContent.includes('Ý chính')));
  await click('Lưu thay đổi');
  await wait(() => !document.querySelector('.markdown-editor'));
  const templated = (await api('/items/' + id)).data;
  assert.ok(templated.note.startsWith(raw + '\n\n')); assert.equal(templated.user_edit_version, 1);
  await page.send('Page.reload', { ignoreCache: true });
  await click('Chỉnh sửa');
  assert.equal(await page.eval(() => document.querySelector('.markdown-editor textarea').value), templated.note);
  await page.eval(() => { const field = document.querySelector('.markdown-editor textarea'); field.focus(); field.setSelectionRange(field.value.length, field.value.length); });
  await page.send('Input.insertText', { text: '\nBổ sung ế / Đ / đ.\n' });
  await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, modifiers: 2 });
  await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, modifiers: 2 });
  await wait(() => !document.querySelector('.markdown-editor'));
  const edited = (await api('/items/' + id)).data;
  assert.equal(edited.note, templated.note + '\nBổ sung ế / Đ / đ.\n');
  assert.equal(edited.user_edit_version, 2);
  report.checks.push('Real login/CSRF, capture ACK, template preview/no-write, explicit append, save/reload, native Vietnamese edit and Ctrl+Enter PASS');
  await wait(() => [...document.querySelectorAll('summary')].some((node) => node.textContent.includes('So sánh đề xuất thủ công')));
  await page.eval(() => [...document.querySelectorAll('summary')].find((node) => node.textContent.includes('So sánh đề xuất thủ công')).click());
  const proposed = edited.note + '\n> Bản đề xuất thủ công cần đối chiếu.\n';
  const proposalSelector = await page.eval(() => [...document.querySelectorAll('label')].find((label) => label.textContent === 'Văn bản đề xuất thủ công')?.htmlFor);
  assert.ok(proposalSelector);
  await fill('[id="' + proposalSelector + '"]', proposed);
  await click('Xem khác biệt');
  await wait(() => !!document.querySelector('.ai-suggestion-review'));
  assert.equal((await api('/items/' + id)).data.note, edited.note);
  await click('Chấp nhận');
  await wait(() => document.body.textContent.includes('Đã áp dụng đề xuất.'));
  assert.equal((await api('/items/' + id)).data.note, proposed);
  await click('Hoàn tác đề xuất');
  await wait(() => document.body.textContent.includes('Đã hoàn tác về văn bản trước đề xuất.'));
  assert.equal((await api('/items/' + id)).data.note, edited.note);
  assert.equal((await api('/items/' + id)).data.user_edit_version, 4);
  const connections = await api('/items/' + id + '/related');
  assert.deepEqual(connections.data.backlinks.map((row) => row.item_id), [peer.data.item_id]);
  const history = await api('/items/' + id + '/captures');
  assert.equal(history.data.results.length, 1); assert.equal(history.data.results[0].raw_text, raw);
  report.checks.push('Manual review preview/no-write, accept+undo exact note/version, immutable CaptureEvent and actual explicit backlink PASS');
  for (const width of [1440, 768, 390]) {
    await page.setViewport({ width, height: 900 });
    await page.eval(() => { location.hash = '#/thu-vien'; });
    await wait(() => !!document.querySelector('[aria-label="Cách xem thư viện"]'));
    let baselineIds;
    for (const mode of ['list', 'table', 'card', 'timeline']) {
      await page.eval((mode) => { const select = document.querySelector('[aria-label="Cách xem thư viện"]'); select.value = mode; select.dispatchEvent(new Event('change', { bubbles: true })); }, mode);
      await wait((mode) => new URLSearchParams(location.hash.split('?')[1]).get('view') === (mode === 'list' ? null : mode), mode);
      await wait(() => new Set([...document.querySelectorAll('main a[href^="#/muc/"]')].map((node) => node.getAttribute('href'))).size === 2);
      const ids = await page.eval(() => [...new Set([...document.querySelectorAll('main a[href^="#/muc/"]')].map((node) => node.getAttribute('href')))].sort());
      assert.equal(ids.length, 2); baselineIds ??= ids; assert.deepEqual(ids, baselineIds);
      assert.equal(await page.eval(() => document.documentElement.scrollWidth > innerWidth), false);
    }
    await page.eval((href) => { location.hash = href; }, href);
    await click('Chỉnh sửa'); await click('Soạn + Xem trước');
    assert.equal(await page.eval(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.screenshot({ path: resolve(out, 'editor-' + width + '.png'), format: 'png' });
    await click('Hủy');
    report.viewports.push({ width, four_views_same_two_ids: true, page_overflow: false, editor_split: true });
  }
  report.checks.push('Actual API-backed list/table/card/timeline same Item IDs; editor split + no horizontal page overflow at1440/768/390 PASS');
  report.item_id = id;
  report.status = 'PASS';
} catch (error) { report.status = 'FAIL'; report.error = String(error.stack ?? error); throw error; }
finally { writeFileSync(resolve(out, 'results.json'), JSON.stringify(report, null, 2) + '\n'); await browser.close(); }
