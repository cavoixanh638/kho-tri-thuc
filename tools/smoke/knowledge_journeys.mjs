/**
 * P08 / KT128: REAL built React App + Django session/CSRF + isolated PostgreSQL.
 * No mock fetch, no production data, no Drive/AI provider. Never claims PASS on prereq failure.
 * Usage and prerequisites: tools/smoke/p08_README.md.
 */
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { resolve, basename } from 'node:path';
import { Browser } from './p08_cdp.mjs';
import { CASES, qaUrl, qaDatabase, makeReport, findCase, record, unsatisfied, cleanError, saveReport } from './p08_report.mjs';

const BASE_SHA = '9716a6a876d6ec41e10b3c3dcbdc095ab4ddd84d';
const out = resolve(process.env.KT_JOURNEY_OUT || 'tmp/p08-kt128');
const reportFile = resolve(out, 'p08-results.json');
const sha = (() => { try { return execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim(); } catch { return null; } })();
const report = makeReport({ codeSha: sha, baseSha: BASE_SHA, environment: 'local browser + built App + Django + temporary PostgreSQL, no provider/Drive' });
const context = { root: null, folder: null, parent: null, child: null, original: null };
const persist = () => saveReport(report, reportFile);
const notRunAll = (reason) => { for (const c of CASES) record(report, c.id, 'NOT_RUN', 'No user journey executed', { reason }); persist(); console.log(`P08 NOT_RUN (${reason}); report: ${reportFile}`); process.exitCode = 2; };

let url;
let prerequisitesReady = true;
try {
  url = qaUrl(process.env.KT_JOURNEY_URL);
  report.qa_db_name = qaDatabase(process.env.KT_JOURNEY_DB_NAME);
  if (process.env.KT_JOURNEY_ISOLATED !== 'YES') throw Error('EXPLICIT_ISOLATED_QA_CONFIRMATION_REQUIRED');
  if (!process.env.KT_JOURNEY_USER || !process.env.KT_JOURNEY_PASSWORD) throw Error('SYNTHETIC_QA_ACCOUNT_REQUIRED');
} catch (error) {
  prerequisitesReady = false;
  notRunAll(cleanError(error));
}

if (prerequisitesReady) {
  let online = false;
  try {
    const response = await fetch(url + '/api/v1/health', { signal: AbortSignal.timeout(3500) });
    online = response.ok && (await response.json()).status === 'ready';
  } catch { /* environment precondition */ }
  if (!online) {
    notRunAll('LOCAL_BUILT_APP_DJANGO_POSTGRES_HEALTH_NOT_READY');
  } else {
    let browser;
    let page;
    async function wait(fn, arg, label = 'UI condition', timeoutMs = 15000) {
      const deadline = Date.now() + timeoutMs;
      do {
        if (await page.eval(fn, arg)) return;
        await new Promise((resolve) => setTimeout(resolve, 120));
      } while (Date.now() < deadline);
      throw Error('UI_TIMEOUT:' + label);
    }
    async function click(text, scope = 'body') {
      await wait(({ text, scope }) => [...(document.querySelector(scope)?.querySelectorAll('button') || [])]
        .some((button) => button.textContent.trim() === text && !button.disabled && button.getClientRects().length), { text, scope }, 'button:' + text);
      await page.eval(({ text, scope }) => [...document.querySelector(scope).querySelectorAll('button')]
        .find((button) => button.textContent.trim() === text && !button.disabled && button.getClientRects().length).click(), { text, scope });
    }
    async function input(label, text, scope = 'body') {
      await wait(({ label, scope }) => [...(document.querySelector(scope)?.querySelectorAll('label') || [])].some((el) => el.textContent.replaceAll('*','').trim() === label), { label, scope }, 'input:' + label);
      const found = await page.eval(({ label, scope }) => {
        const node = [...(document.querySelector(scope)?.querySelectorAll('label') || [])].find((el) => el.textContent.replaceAll('*', '').trim() === label);
        const field = node?.htmlFor ? document.getElementById(node.htmlFor) : node?.querySelector('input,textarea');
        if (!field) return false;
        field.dataset.p08Input = 'current'; field.focus(); field.select?.(); return true;
      }, { label, scope });
      assert.ok(found, 'Missing labeled input: ' + label);
      await page.send('Input.insertText', { text });
      await page.eval(() => document.querySelector('[data-p08-input="current"]')?.removeAttribute('data-p08-input'));
    }
    async function select(label, value, scope = 'body') {
      const found = await page.eval(({ label, value, scope }) => {
        const node = [...(document.querySelector(scope)?.querySelectorAll('label') || [])].find((el) => el.textContent.replaceAll('*', '').trim() === label || el.firstChild?.textContent.trim() === label);
        const field = node?.htmlFor ? document.getElementById(node.htmlFor) : node?.querySelector('select');
        if (!field) return false;
        field.value = value;
        field.dispatchEvent(new Event('change', { bubbles: true })); return true;
      }, { label, value, scope });
      assert.ok(found, 'Missing labeled select: ' + label);
    }
    async function summary(label, scope = 'body') {
      await wait(({ label, scope }) => [...(document.querySelector(scope)?.querySelectorAll('summary') || [])]
        .some((node) => node.textContent.trim() === label), { label, scope }, 'summary:' + label);
      await page.eval(({ label, scope }) => {
        const node = [...document.querySelector(scope).querySelectorAll('summary')].find((x) => x.textContent.trim() === label);
        if (!node.parentElement.open) node.click();
      }, { label, scope });
    }
    async function route(hash) {
      await page.eval((next) => { location.hash = next; }, hash);
      await wait((next) => location.hash === next, hash, 'route:' + hash);
    }
    async function api(path, method = 'GET', body) {
      return page.eval(async ({ path, method, body }) => {
        const session = await fetch('/api/v1/session', { credentials: 'same-origin' }).then((response) => response.json());
        const response = await fetch('/api/v1' + path, { method, credentials: 'same-origin',
          headers: { 'Content-Type': 'application/json', ...(session.csrf_token ? { 'X-CSRFToken': session.csrf_token } : {}) },
          ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
        let data; try { data = await response.json(); } catch { data = null; }
        return { status: response.status, data };
      }, { path, method, body });
    }
    const get = async (path) => { const response = await api(path); assert.equal(response.status, 200, 'GET ' + path); return response.data; };
    async function screenshot(name) {
      const path = resolve(out, name);
      await page.screenshot({ path, format: 'png' });
      const bytes = readFileSync(path);
      const reference = { filename: basename(path), bytes: bytes.length, sha256: createHash('sha256').update(bytes).digest('hex') };
      return reference;
    }
    async function attempt(id, fn) {
      const dependencies = unsatisfied(report, id);
      if (dependencies.length) {
        record(report, id, 'BLOCKED', 'Prerequisite journey not PASS', { reason: 'DEPENDENCY:' + dependencies.join(',') }); persist(); return;
      }
      const started = performance.now();
      try {
        const outcome = await fn();
        if (outcome?.status) record(report, id, outcome.status, outcome.actual, { reason: outcome.reason, evidence: outcome.evidence || [], durationMs: Math.round(performance.now() - started) });
        else record(report, id, 'PASS', typeof outcome === 'string' ? outcome : 'Assertions passed', { durationMs: Math.round(performance.now() - started) });
      } catch (error) {
        const reason = cleanError(error);
        const blockedPolicy = id === 'AUTH' && /ERR_BLOCKED_BY_ADMINISTRATOR/.test(reason);
        let evidence = [];
        if (page && !blockedPolicy) { try { evidence = [(await screenshot(`p08-fail-${id}.png`)).filename]; } catch { /* cannot capture */ } }
        record(report, id, blockedPolicy ? 'NOT_RUN' : 'FAIL', blockedPolicy ? 'Browser policy denied local navigation' : 'Browser assertion failed', { reason, evidence, durationMs: Math.round(performance.now() - started) });
      }
      persist();
    }
    try {
      browser = await Browser.launch();
      page = await browser.newPage({ width: 1920, height: 1080, reducedMotion: true });
      await attempt('AUTH', async () => {
        await page.goto(url);
        await wait(() => !!document.querySelector('input[autocomplete="username"]'), undefined, 'login username');
        await input('Tên đăng nhập', process.env.KT_JOURNEY_USER);
        await input('Mật khẩu', process.env.KT_JOURNEY_PASSWORD);
        await click('Đăng nhập');
        await wait(() => !!document.querySelector('.capture-compose'), undefined, 'authenticated home');
        const session = await page.eval(async () => fetch('/api/v1/session', { credentials: 'same-origin' }).then((r) => r.json()));
        assert.equal(session.authenticated, true);
        assert.equal(session.username, process.env.KT_JOURNEY_USER);
        assert.ok(typeof session.csrf_token === 'string' && session.csrf_token.length >= 32);
        const items = await get('/items');
        assert.equal(items.results.length, 0, 'Must be freshly created synthetic QA user (no personal data)');
        return 'Real login, authenticated session, CSRF token, fresh empty synthetic QA account';
      });
      await attempt('J1', async () => {
        await route('#/thu-vien');
        await click('Thêm kho con'); await input('Tên nhánh', 'P08 Khoa học'); await click('Lưu nhánh');
        await wait(() => document.body.textContent.includes('P08 Khoa học') && !document.querySelector('.knowledge-node-editor'), undefined, 'root created');
        let tree = (await get('/knowledge-tree')).nodes;
        const root = tree.find((row) => row.name === 'P08 Khoa học'); assert.ok(root); context.root = root.id;
        await route('#/thu-vien?node=' + root.id);
        await click('Thêm nhánh con'); await input('Tên nhánh', 'P08 Bộ sách'); await click('Lưu nhánh');
        await wait(() => document.body.textContent.includes('P08 Bộ sách') && !document.querySelector('.knowledge-node-editor'), undefined, 'child folder created');
        tree = (await get('/knowledge-tree')).nodes;
        const folder = tree.find((row) => row.name === 'P08 Bộ sách'); assert.equal(folder.parent_id, root.id); context.folder = folder.id;
        await route('#/thu-vien?node=' + folder.id);
        await click('Thêm ghi chú tại đây');
        await input('Tiêu đề ghi chú mới', 'P08 Giáo trình');
        context.original = '# Giáo trình\n\nTiếng Việt nguyên văn.\n\n## Luận điểm\n\n### Đối chiếu\n\n#### Thực hành\n\n##### Ghi nhớ\n\n###### Kết luận\n';
        await input('Nội dung ghi chú mới', context.original); await click('Tạo ghi chú');
        await wait(() => /^#\/muc\/[\da-f-]{36}$/.test(location.hash), undefined, 'parent note URL');
        context.parent = await page.eval(() => location.hash.split('/').at(-1));
        assert.equal((await get('/items/' + context.parent)).note, context.original);
        assert.equal((await get('/items/' + context.parent + '/placement')).home_topic_id, folder.id);
        await click('Tạo ghi chú con'); await input('Tiêu đề bài con', 'P08 Chương Một');
        await input('Nội dung bài con', '# P08 Chương Một\n\nLuận điểm cần đối chiếu.\n');
        await click('Tạo bài con');
        await wait((parent) => location.hash.startsWith('#/muc/') && !location.hash.endsWith(parent), context.parent, 'child note URL');
        context.child = await page.eval(() => location.hash.split('/').at(-1));
        assert.equal((await get('/items/' + context.child + '/structure')).parent_item_id, context.parent);
        const originalEvents = (await get('/items/' + context.child + '/captures')).results;
        await summary('Chuyển thư mục / thêm lối tắt');
        const placementPanel = '[aria-label="Cấu trúc bài cha và bài con"]';
        await wait(() => document.querySelector('[aria-label="Cấu trúc bài cha và bài con"] select')?.options.length > 1, undefined, 'folder choices');
        // The physical Item stays unique while the UI first moves the canonical home
        // and then adds a shortcut to a second folder (KT128 journey 1).
        const initialPlacement = await get('/items/' + context.child + '/placement');
        await select('Thư mục cho bài', String(context.root), placementPanel);
        await click('Chuyển vị trí chính', placementPanel);
        await wait(async ({ id, root }) => {
          const response = await fetch('/api/v1/items/' + id + '/placement');
          return response.ok && (await response.json()).home_topic_id === root;
        }, { id: context.child, root: context.root }, 'home moved by UI');
        await wait((version) => document.querySelector('[aria-label="Cấu trúc bài cha và bài con"]')?.textContent.includes('Phiên bản ' + version),
          initialPlacement.structure_version + 1, 'move version refreshed');
        await select('Thư mục cho bài', String(context.folder), placementPanel);
        await click('Chuyển vị trí chính', placementPanel);
        await wait(async ({ id, folder }) => {
          const response = await fetch('/api/v1/items/' + id + '/placement');
          return response.ok && (await response.json()).home_topic_id === folder;
        }, { id: context.child, folder: context.folder }, 'home restored by UI');
        await wait((version) => document.querySelector('[aria-label="Cấu trúc bài cha và bài con"]')?.textContent.includes('Phiên bản ' + version),
          initialPlacement.structure_version + 2, 'restore version refreshed');
        await select('Thư mục cho bài', String(context.root), placementPanel);
        await click('Thêm vào nhánh khác', placementPanel);
        await wait(async ({ id }) => {
          const response = await fetch('/api/v1/items/' + id + '/placement');
          return response.ok && (await response.json()).memberships?.length === 2;
        }, { id: context.child }, 'shortcut added via UI');
        const placement = await get('/items/' + context.child + '/placement');
        assert.equal(placement.home_topic_id, context.folder);
        assert.equal(placement.memberships.length, 2);
        assert.ok(placement.memberships.some((m) => m.folder_id === context.root && m.shortcut));
        assert.equal((await get('/items/' + context.child + '/structure')).parent_item_id, context.parent);
        assert.deepEqual((await get('/items/' + context.child + '/captures')).results, originalEvents);
        return 'Nested folders, parent/child and UI home move/restore/shortcut; stable UUID, Markdown and CaptureEvents preserved';
      });
      await attempt('J2', async () => {
        await route('#/muc/' + context.parent);
        await click('Chỉnh sửa');
        await page.eval(() => { const t = document.querySelector('.markdown-editor textarea'); t.focus(); t.setSelectionRange(t.value.length, t.value.length); });
        await page.send('Input.insertText', { text: '\n[[' });
        await wait(() => !!document.querySelector('.wiki-completion [role="option"]'), undefined, 'wiki choices');
        await wait(() => document.querySelector('.wiki-completion').textContent.includes('P08 Chương Một'), undefined, 'target wiki choice');
        await page.eval(() => [...document.querySelectorAll('.wiki-completion button')].find((node) => node.textContent.includes('P08 Chương Một')).click());
        await click('Lưu thay đổi');
        await wait(() => !document.querySelector('.markdown-editor'), undefined, 'saved wiki');
        assert.ok((await get('/items/' + context.parent)).note.includes('#/muc/' + context.child));
        assert.ok((await get('/items/' + context.child + '/links')).incoming.some((row) => row.item_id === context.parent));
        const target = await get('/items/' + context.child);
        const patched = await api('/items/' + context.child, 'PATCH', { title: 'P08 Chương Một — đổi tên', expected_edit_version: target.user_edit_version });
        assert.equal(patched.status, 200);
        await page.send('Page.reload', { ignoreCache: true });
        await wait((child) => !!document.querySelector('a[href="#/muc/' + child + '"]'), context.child, 'renamed link rendered');
        for (const tag of ['h1','h2','h3','h4','h5','h6']) assert.ok(await page.eval((tag) => !!document.querySelector('.knowledge-text ' + tag + '[id]'), tag), tag);
        await page.eval(() => document.body.focus());
        await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'k', code: 'KeyK', windowsVirtualKeyCode: 75, modifiers: 2 });
        await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'k', code: 'KeyK', windowsVirtualKeyCode: 75, modifiers: 2 });
        await wait(() => !!document.querySelector('dialog[open]'), undefined, 'command palette');
        await page.send('Input.insertText', { text: 'P08 Chương Một' });
        await wait(() => document.querySelector('dialog').textContent.includes('P08 Chương Một — đổi tên'), undefined, 'palette search');
        await page.eval(() => [...document.querySelectorAll('dialog [role="option"]')].find((node) => node.textContent.includes('P08 Chương Một — đổi tên')).click());
        await wait((child) => location.hash === '#/muc/' + child, context.child, 'palette navigation');
        return 'Wiki UUID, backlink and target rename survive reload; H1-H6 outline and Ctrl+K navigation verified';
      });
      await attempt('J3', async () => {
        if (process.env.KT_JOURNEY_PUBLIC_NETWORK !== 'YES') return { status: 'NOT_RUN', actual: 'Did not contact any external website', reason: 'EXTERNAL_PUBLIC_PAGE_OPT_IN_REQUIRED' };
        await route('#/muc/' + context.child);
        await select('Cách thu thập', 'article', '.research-clipper');
        await input('URL nguồn công khai', 'https://docs.python.org/3/library/json.html', '.research-clipper');
        const before = (await get('/items/' + context.child)).note;
        await click('Xem trước nguồn / đoạn trích', '.research-clipper');
        await wait(() => !!document.querySelector('.clip-preview'), undefined, 'public page preview', 25000);
        assert.ok(await page.eval(() => document.querySelector('.clip-preview').textContent.includes('Khớp văn bản nguồn')));
        assert.equal((await get('/items/' + context.child)).note, before);
        await click('Lưu trích dẫn vào bài này', '.research-clipper');
        await wait(() => !!document.querySelector('.clip-annotations blockquote'), undefined, 'clip recorded');
        const clips = (await get('/items/' + context.child + '/clips')).results;
        assert.equal(clips.length, 1); assert.equal(clips[0].state, 'current'); assert.ok(clips[0].source_version);
        await click('Xem đúng đoạn trong văn bản nguồn', '.clip-annotations');
        await wait(() => !!document.querySelector('.clip-annotations mark'), undefined, 'clip highlights');
        assert.equal((await get('/items/' + context.child)).note, before);
        return 'Public Python docs article source version; preview/save/highlight; authored note unchanged';
      });
      await attempt('J4', async () => {
        await route('#/muc/' + context.child);
        await click('Thêm yêu thích');
        await route('#/thu-vien?collection=new');
        await wait(() => !!document.querySelector('.saved-collection-form'), undefined, 'collection form');
        await input('Tên bộ sưu tập', 'P08 Bài yêu thích', '.saved-collection-form');
        await select('Yêu thích', 'true', '.saved-collection-form');
        await click('Lưu bộ sưu tập', '.saved-collection-form');
        await wait(() => location.hash.includes('collection=') && !location.hash.endsWith('new') && !document.querySelector('.saved-collection-form'), undefined, 'collection saved');
        const id = await page.eval(() => new URLSearchParams(location.hash.split('?')[1]).get('collection'));
        assert.deepEqual((await get('/collections/' + id + '/items')).results.map((row) => row.item_id), [context.child]);
        assert.equal((await api('/items/' + context.child, 'PATCH', { favorite: false })).status, 200);
        await click('Cập nhật kết quả');
        await wait(() => document.querySelector('.saved-collection-screen')?.textContent.includes('0 bài khớp'), undefined, 'collection recalculated');
        return 'Dynamic saved-favorite filter updated; original Item UUID retained (topic/tag/date filters not exercised here)';
      });
      await attempt('J4B', async () => {
        const child = await get('/items/' + context.child);
        const tag = await api('/groups', 'POST', { kind: 'tag', name: 'P08 Nhãn tổng hợp' });
        assert.ok([200, 201].includes(tag.status));
        assert.ok(Number.isInteger(tag.data?.id));
        const assigned = await api('/items/' + context.child + '/organization', 'PATCH', { tag_ids: [tag.data.id] });
        assert.equal(assigned.status, 200);
        const day = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Ho_Chi_Minh', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(child.saved_at));
        const groups = (any = []) => ({ any, all: [], exclude: [] });
        const query = { schema_version: 1, q: '', topics: groups([context.folder]), projects: groups(), tags: groups([tag.data.id]),
          received: { from: day, to: day }, published: {}, timezone: 'Asia/Ho_Chi_Minh', favorite: null,
          source_fetch: '', content_extract: '', sort: 'saved_desc' };
        const saved = await api('/collections', 'POST', { name: 'P08 Ngày nhóm và nhãn', view: 'list', query });
        assert.equal(saved.status, 201);
        const id = saved.data.id;
        const initial = await get('/collections/' + id + '/items');
        assert.deepEqual(initial.results.map((row) => row.item_id), [context.child]);
        await route('#/thu-vien?collection=' + id);
        await wait(() => document.querySelector('.saved-collection-screen')?.textContent.includes('P08 Chương Một'), undefined, 'topic/tag/date collection result');
        const untagged = await api('/items/' + context.child + '/organization', 'PATCH', { tag_ids: [] });
        assert.equal(untagged.status, 200);
        await click('Cập nhật kết quả');
        await wait(() => document.querySelector('.saved-collection-screen')?.textContent.includes('0 bài khớp'), undefined, 'tag change reflected');
        assert.equal((await get('/collections/' + id + '/items')).count, 0);
        assert.equal((await get('/items/' + context.child)).item_id, context.child);
        return 'Saved topic+tag+received-day AND query changes from one to zero after untag; one stable UUID';
      });
      await attempt('J5A', async () => {
        await route('#/muc/' + context.parent);
        const previous = (await get('/items/' + context.parent)).note;
        await click('Chỉnh sửa');
        await summary('Thêm mẫu ghi chú', '.raw-knowledge');
        await click('Bài học');
        assert.equal((await get('/items/' + context.parent)).note, previous, 'Template preview must not save');
        await click('Thêm mẫu vào cuối');
        await wait(() => document.body.textContent.includes('Đã thêm mẫu vào bản nháp'), undefined, 'template draft appended');
        assert.equal((await get('/items/' + context.parent)).note, previous, 'Draft must remain local');
        await click('Lưu thay đổi');
        await wait(() => !document.querySelector('.markdown-editor'), undefined, 'template saved');
        const current = (await get('/items/' + context.parent)).note;
        assert.ok(current.startsWith(previous + '\n\n'), 'Original note prefix retained');
        return 'Template preview and local draft unchanged server; explicit save preserved original prefix';
      });
      await attempt('J5B', async () => {
        const caps = await get('/items/' + context.parent + '/suggestions/capabilities');
        if (!caps.enabled || caps.mode !== 'manual_review_poc') return { status: 'NOT_RUN', actual: 'Manual-review UI not enabled', reason: 'ISOLATED_PROVIDER_OFF_POC_FLAG_REQUIRED' };
        await route('#/muc/' + context.parent);
        await summary('So sánh đề xuất thủ công (thử nghiệm)', '.item-suggestion-panel');
        const before = (await get('/items/' + context.parent)).note;
        await input('Văn bản đề xuất thủ công', before + '\n# P08 chỉ xem thử\n', '.item-suggestion-panel');
        await click('Xem khác biệt', '.item-suggestion-panel');
        await wait(() => !!document.querySelector('.ai-suggestion-review'), undefined, 'review preview');
        assert.equal((await get('/items/' + context.parent)).note, before);
        await click('Từ chối', '.ai-suggestion-review');
        await wait(() => document.querySelector('.ai-suggestion-review')?.textContent.includes('Đã từ chối'), undefined, 'reject status');
        assert.equal((await get('/items/' + context.parent)).note, before);
        return 'Manual provider-off diff/reject completed with exact source note unchanged';
      });
      await attempt('J6A', async () => {
        await route('#/muc/' + context.child);
        const before = (await get('/items/' + context.child)).note;
        await select('Cách thu thập', 'link', '.research-clipper');
        await input('URL nguồn công khai', 'https://docs.python.org/3/library/json.html', '.research-clipper');
        await click('Xem trước nguồn / đoạn trích', '.research-clipper');
        await wait(() => !!document.querySelector('.clip-preview'), undefined, 'link-only preview');
        await click('Lưu trích dẫn vào bài này', '.research-clipper');
        await wait(async (id) => { const r = await fetch('/api/v1/items/' + id + '/clips'); const data = await r.json(); return data.results?.some((x) => x.state === 'link_only'); }, context.child, 'link-only annotation saved');
        const clips = (await get('/items/' + context.child + '/clips')).results;
        const links = clips.filter((row) => row.state === 'link_only');
        assert.ok(links.length, 'At least one link-only clip');
        assert.ok(links.every((row) => !row.locator?.page && !row.locator?.time && !row.locator?.seconds));
        assert.equal((await get('/items/' + context.child)).note, before);
        return 'Link-only source truthful, no invented page/seconds; author Markdown not overwritten';
      });
      await attempt('J6B', async () => {
        if (!process.env.KT_JOURNEY_PDF_ITEM_ID || !process.env.KT_JOURNEY_MP4_ITEM_ID) return {
          status: 'NOT_RUN', actual: 'No synthetic verified PDF and MP4 assets provided', reason: 'PINNED_MEDIA_FIXTURES_ABSENT',
        };
        const check = async (id, kind) => {
          assert.match(id, /^[a-f\d-]{36}$/i);
          await route('#/muc/' + id);
          await wait(() => !!document.querySelector('.source-locator'), undefined, 'native source locator for ' + kind);
          assert.ok(await page.eval(() => [...document.querySelectorAll('.source-locator')].some((el) => el.dataset.state === 'AVAILABLE')));
          await page.eval(() => [...document.querySelectorAll('.source-locator[data-state="AVAILABLE"] button')].find((el) => el.textContent.includes('Đến vị trí nguồn'))?.click());
          await wait((kind) => !!document.querySelector(kind === 'PDF' ? '.source-locator-viewer iframe[src*="#page="]' : '.source-locator-viewer video, .source-locator-viewer audio'), kind, 'native viewer for ' + kind);
        };
        await check(process.env.KT_JOURNEY_PDF_ITEM_ID, 'PDF');
        await check(process.env.KT_JOURNEY_MP4_ITEM_ID, 'MP4');
        return { status: 'BLOCKED', actual: 'PDF iframe and MP4 player displayed but actual native page and timestamp accuracy require independent manual inspection', reason: 'NATIVE_PAGE_AND_MEDIA_SEEK_NOT_PROVEN' };
      });
      await attempt('J7', async () => {
        if (!context.folder || !context.parent || !context.child) return { status: 'BLOCKED', actual: 'Folder/note data unavailable', reason: 'DEPENDENCY:J1' };
        const widths = [1920, 1440, 768, 390];
        for (const width of widths) {
          await page.setViewport({ width, height: width === 1920 ? 1080 : 900 });
          await route('#/thu-vien?node=' + context.folder);
          await wait((id) => !!document.querySelector('.knowledge-library-content a[href="#/muc/' + id + '"]'), context.parent, 'folder content ' + width);
          const mobileToggle = await page.eval(() => !!document.querySelector('.library-tree-toggle') && getComputedStyle(document.querySelector('.library-tree-toggle')).display !== 'none');
          if (mobileToggle) await page.eval(() => { const el = document.querySelector('.library-tree-toggle'); if (el.getAttribute('aria-expanded') !== 'true') el.click(); });
          await wait(() => !!document.querySelector('.library-tree-content') && document.querySelector('.library-tree-content').getBoundingClientRect().height > 0, undefined, 'tree visible ' + width);
          assert.equal(await page.eval(() => document.documentElement.scrollWidth > innerWidth), false, 'overflow at ' + width);
          assert.equal(await page.eval(() => matchMedia('(prefers-reduced-motion: reduce)').matches), true);
          let idsBaseline;
          for (const view of ['list', 'table', 'card', 'timeline']) {
            await select('Cách xem', view);
            await wait((view) => document.querySelector('.library-view-toolbar select')?.value === view, view, 'view ' + view);
            const ids = await page.eval(() => [...new Set([...document.querySelectorAll('.knowledge-library-content a[href^="#/muc/"]')].map((el) => el.getAttribute('href')))].sort());
            assert.ok(ids.length >= 2, `Expected two synthetic Item UUIDs, got ${ids.length} at ${width}/${view}`);
            idsBaseline ??= ids; assert.deepEqual(ids, idsBaseline);
            assert.equal(await page.eval(() => document.documentElement.scrollWidth > innerWidth), false, 'overflow ' + width + '/' + view);
          }
          const evidence = await screenshot('p08-library-' + width + '.png');
          report.viewports.push({ width, height: width === 1920 ? 1080 : 900, screenshot: evidence.filename, screenshot_sha256: evidence.sha256,
            screenshot_bytes: evidence.bytes, visible_folder: true, same_distinct_ids_4_modes: true, horizontal_overflow: false, reduced_motion: true });
          persist();
        }
        return { status: 'PASS', actual: '4 viewport widths + four library modes, identical Item IDs and no overflow', evidence: report.viewports.map((row) => row.screenshot) };
      });
      await attempt('J8', async () => ({ status: 'NOT_RUN', actual: 'Frozen snapshot lacks verified KT127 vault export/import API and empty DB roundtrip', reason: 'KT127_NOT_IN_FROZEN_SNAPSHOT' }));
      await attempt('J9', async () => ({ status: 'NOT_RUN', actual: 'No seeded 10k Item/1k node DB, restore and retry run in this browser session', reason: 'SCALE_RESTORE_SEPARATE_ISOLATED_DB_REQUIRED' }));
    } catch (error) {
      report.driver_error = cleanError(error);
      for (const step of report.journeys.filter((x) => x.status === 'NOT_RUN' && x.reason === 'not_attempted')) record(report, step.id, 'NOT_RUN', 'Driver could not continue', { reason: 'BROWSER_LAUNCH_OR_DRIVER_EXCEPTION' });
    } finally {
      try { await browser?.close(); } catch { /* browser cleanup */ }
      persist();
      console.log('P08 browser report: ' + reportFile + '; status=' + report.status + '; metrics=' + JSON.stringify(report.metrics));
      process.exitCode = report.status === 'PASS' ? 0 : report.status === 'FAIL' ? 1 : 2;
    }
  }
}
