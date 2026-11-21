// KT128 actual built App + authenticated Django/PostgreSQL. No mocked fetch.
import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

assert.equal(process.env.KT_JOURNEY_URL, 'http://127.0.0.1:62310');
assert.ok(process.env.KT_JOURNEY_USER && process.env.KT_JOURNEY_PASSWORD && process.env.KT_JOURNEY_CDP);
const out = resolve(process.env.KT_JOURNEY_OUT ?? 'tmp/kt128');
mkdirSync(out, { recursive: true });
const { Browser } = await import(pathToFileURL(process.env.KT_JOURNEY_CDP));
const browser = await Browser.launch({ extraArgs: ['--no-proxy-server'] });
const report = { checked_at: new Date().toISOString(), code_sha: execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(),
  environment: 'Actual built App + Django/session/CSRF + isolated PostgreSQL62224, noDrive/provider', journeys: [], viewports: [] };
try {
  const page = await browser.newPage({ width: 1920, height: 1080, reducedMotion: true });
  async function wait(fn, arg) {
    for (let n = 0; n < 150; n++) { if (await page.eval(fn, arg)) return; await new Promise((done) => setTimeout(done, 100)); }
    throw Error('Timed out: ' + fn.toString());
  }
  const click = async (text, scope = 'body') => {
    await wait(({ text, scope }) => [...document.querySelector(scope).querySelectorAll('button')].some((node) => node.textContent.trim() === text && !node.disabled && node.getClientRects().length), { text, scope });
    await page.eval(({ text, scope }) => [...document.querySelector(scope).querySelectorAll('button')].find((node) => node.textContent.trim() === text && !node.disabled && node.getClientRects().length).click(), { text, scope });
  };
  async function input(label, text, scope = 'body') {
    const selector = await page.eval(({ label, scope }) => {
      const node = [...document.querySelector(scope).querySelectorAll('label')].find((node) => node.textContent.replaceAll('*', '').trim() === label);
      if (!node) return null;
      const field = node.htmlFor ? document.getElementById(node.htmlFor) : node.querySelector('input,textarea,select');
      if (!field) return null;
      field.dataset.ktJourney = 'field'; field.focus(); if (field.select) field.select();
      return '[data-kt-journey="field"]';
    }, { label, scope });
    assert.ok(selector, label);
    await page.send('Input.insertText', { text });
    await page.eval(() => document.querySelector('[data-kt-journey="field"]').removeAttribute('data-kt-journey'));
  }
  async function select(label, value, scope = 'body') {
    await page.eval(({ label, value, scope }) => {
      const node = [...document.querySelector(scope).querySelectorAll('label')].find((node) => node.textContent.replaceAll('*', '').trim() === label || node.firstChild?.textContent.trim() === label);
      const field = node?.htmlFor ? document.getElementById(node.htmlFor) : node?.querySelector('select');
      if (!field) throw Error('No select: ' + label);
      field.value = value; field.dispatchEvent(new Event('change', { bubbles: true }));
    }, { label, value, scope });
  }
  async function summary(label, scope = 'body') {
    await wait(({ label, scope }) => [...document.querySelector(scope).querySelectorAll('summary')].some((node) => node.textContent.trim() === label), { label, scope });
    await page.eval(({ label, scope }) => {
      const node = [...document.querySelector(scope).querySelectorAll('summary')].find((node) => node.textContent.trim() === label);
      if (!node.parentElement.open) node.click();
    }, { label, scope });
  }
  const api = (path, method = 'GET', body) => page.eval(async ({ path, method, body }) => {
    const session = await fetch('/api/v1/session').then((r) => r.json());
    const response = await fetch('/api/v1' + path, { method, credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': session.csrf_token }, body: body && JSON.stringify(body) });
    return { status: response.status, data: await response.json() };
  }, { path, method, body });
  async function route(hash) { await page.eval((hash) => { location.hash = hash; }, hash); }
  await page.goto(process.env.KT_JOURNEY_URL);
  await wait(() => !!document.querySelector('input[autocomplete="username"]'));
  await input('Tên đăng nhập', process.env.KT_JOURNEY_USER);
  await input('Mật khẩu', process.env.KT_JOURNEY_PASSWORD);
  await click('Đăng nhập');
  await wait(() => !!document.querySelector('.capture-compose'));
  assert.equal((await api('/items')).data.results.length, 0, 'Use a new empty QA account');
  await route('#/thu-vien');
  await click('Thêm kho con');
  await input('Tên nhánh', 'Khoa học');
  await click('Lưu nhánh');
  await wait(() => document.body.textContent.includes('Khoa học') && !document.querySelector('.knowledge-node-editor'));
  let tree = (await api('/knowledge-tree')).data.nodes;
  const root = tree.find((row) => row.name === 'Khoa học'); assert.ok(root);
  await route('#/thu-vien?node=' + root.id);
  await click('Thêm thư mục con');
  await input('Tên nhánh', 'Bộ sách nghiên cứu');
  await click('Lưu nhánh');
  await wait(() => !document.querySelector('.knowledge-node-editor'));
  tree = (await api('/knowledge-tree')).data.nodes;
  const folder = tree.find((row) => row.name === 'Bộ sách nghiên cứu'); assert.equal(folder.parent_id, root.id);
  await route('#/thu-vien?node=' + folder.id);
  await click('Thêm ghi chú tại đây');
  await input('Tiêu đề ghi chú mới', 'Giáo trình tri thức');
  const raw = '# Giáo trình\n\nTiếng Việt nguyên văn.\n\n## Luận điểm\n\n### Đối chiếu\n\n#### Thực hành\n\n##### Ghi nhớ\n\n###### Kết luận\n';
  await input('Nội dung ghi chú mới', raw);
  await click('Tạo ghi chú');
  await wait(() => /^#\/muc\/[\da-f-]{36}$/.test(location.hash));
  const parent = await page.eval(() => location.hash.split('/').at(-1));
  assert.equal((await api('/items/' + parent)).data.note, raw);
  assert.equal((await api('/items/' + parent + '/placement')).data.home_topic_id, folder.id);
  await click('Tạo ghi chú con');
  await input('Tiêu đề bài con', 'Chương Một');
  await input('Nội dung bài con', '# Chương Một\n\nLuận điểm cần đối chiếu.\n');
  await click('Tạo bài con');
  await wait((parent) => location.hash.startsWith('#/muc/') && !location.hash.endsWith(parent), parent);
  const child = await page.eval(() => location.hash.split('/').at(-1));
  assert.equal((await api('/items/' + child + '/structure')).data.parent_item_id, parent);
  const originalEvents = (await api('/items/' + child + '/captures')).data.results;
  await summary('Chuyển thư mục / thêm lối tắt');
  await wait(() => document.querySelector('[aria-label="Cấu trúc bài cha và bài con"] select')?.options.length > 1);
  await select('Thư mục cho bài', String(root.id), '[aria-label="Cấu trúc bài cha và bài con"]');
  await click('Thêm vào nhánh khác', '[aria-label="Cấu trúc bài cha và bài con"]');
  await wait(() => document.body.textContent.includes('Phiên bản 1'));
  let placement = (await api('/items/' + child + '/placement')).data;
  assert.equal(placement.home_topic_id, folder.id); assert.equal(placement.memberships.length, 2);
  assert.deepEqual((await api('/items/' + child + '/captures')).data.results, originalEvents);
  report.journeys.push({ id: 'J1', status: 'PASS', actual: 'UI folder/subfolder→home-note→child-note→shortcut; sameUUID/rawEvent' });
  await route('#/muc/' + parent);
  await click('Chỉnh sửa');
  await page.eval(() => { const t = document.querySelector('.markdown-editor textarea'); t.focus(); t.setSelectionRange(t.value.length, t.value.length); });
  await page.send('Input.insertText', { text: '\n[[' });
  await wait(() => !!document.querySelector('.wiki-completion [role="option"]'));
  await wait(() => document.querySelector('.wiki-completion').textContent.includes('Chương Một'));
  await page.eval(() => [...document.querySelectorAll('.wiki-completion button')].find((node) => node.textContent.includes('Chương Một')).click());
  await click('Lưu thay đổi');
  await wait(() => !document.querySelector('.markdown-editor'));
  let note = (await api('/items/' + parent)).data;
  assert.ok(note.note.includes('#/muc/' + child));
  const backlinks = (await api('/items/' + child + '/links')).data;
  assert.ok(backlinks.incoming.some((row) => row.item_id === parent));
  const childState = (await api('/items/' + child)).data;
  await api('/items/' + child, 'PATCH', { title: 'Chương Một — đổi tên', expected_edit_version: childState.user_edit_version });
  await page.send('Page.reload', { ignoreCache: true });
  await wait(() => !!document.querySelector('a[href="#/muc/' + child + '"]'));
  assert.ok(await page.eval((child) => !!document.querySelector('a[href="#/muc/' + child + '"]'), child));
  for (const selector of ['h1','h2','h3','h4','h5','h6']) assert.ok(await page.eval((selector) => !!document.querySelector('.knowledge-text ' + selector + '[id]'), selector));
  await page.eval(() => document.body.focus());
  await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'k', code: 'KeyK', windowsVirtualKeyCode: 75, modifiers: 2 });
  await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'k', code: 'KeyK', modifiers: 2 });
  await wait(() => !!document.querySelector('dialog[open]'));
  await page.send('Input.insertText', { text: 'Chương Một' });
  await wait(() => document.querySelector('dialog').textContent.includes('Chương Một — đổi tên'));
  await page.eval(() => [...document.querySelectorAll('dialog [role="option"]')].find((node) => node.textContent.includes('Chương Một — đổi tên')).click());
  await wait((child) => location.hash === '#/muc/' + child, child);
  report.journeys.push({ id: 'J2', status: 'PASS', actual: 'Wiki authoring→UUID target rename→backlink→H1–H6 outline→CtrlK actualnote' });
  await select('Cách thu thập', 'article', '.research-clipper');
  await input('URL nguồn công khai', 'https://docs.python.org/3/library/json.html', '.research-clipper');
  const beforeClip = (await api('/items/' + child)).data.note;
  await click('Xem trước nguồn / đoạn trích', '.research-clipper');
  await wait(() => !!document.querySelector('.clip-preview'));
  assert.ok(await page.eval(() => document.querySelector('.clip-preview').textContent.includes('Khớp văn bản nguồn')));
  assert.equal((await api('/items/' + child)).data.note, beforeClip);
  await click('Lưu trích dẫn vào bài này', '.research-clipper');
  await wait(() => !!document.querySelector('.clip-annotations blockquote'));
  const clips = (await api('/items/' + child + '/clips')).data.results;
  assert.equal(clips.length, 1); assert.equal(clips[0].state, 'current');
  await click('Xem đúng đoạn trong văn bản nguồn', '.clip-annotations');
  await wait(() => !!document.querySelector('.clip-annotations mark'));
  assert.equal((await api('/items/' + child)).data.note, beforeClip);
  report.journeys.push({ id: 'J3', status: 'PASS', actual: 'Actualpublic article preview→save quote/source→verifiedtext highlight; authorednoteunchanged' });
  await click('Thêm yêu thích');
  await route('#/thu-vien?collection=new');
  await wait(() => !!document.querySelector('.saved-collection-form'));
  await input('Tên bộ sưu tập', 'Bài yêu thích đang nghiên cứu', '.saved-collection-form');
  await select('Yêu thích', 'true', '.saved-collection-form');
  await click('Lưu bộ sưu tập', '.saved-collection-form');
  await wait(() => location.hash.includes('collection=') && !location.hash.endsWith('new') && !document.querySelector('.saved-collection-form'));
  const collection = await page.eval(() => new URLSearchParams(location.hash.split('?')[1]).get('collection'));
  let members = (await api('/collections/' + collection + '/items')).data;
  assert.deepEqual(members.results.map((row) => row.item_id), [child]);
  await api('/items/' + child, 'PATCH', { favorite: false });
  await click('Cập nhật kết quả');
  await wait(() => document.querySelector('.saved-collection-screen').textContent.includes('0 bài khớp'));
  report.journeys.push({ id: 'J4', status: 'PASS', actual: 'UIsavedfavoritequery→membershipupdateswithoutcopyingItem' });
  for (const width of [1920, 1440, 768, 390]) {
    await page.setViewport({ width, height: width === 1920 ? 1080 : 900 });
    await route('#/thu-vien?node=' + folder.id);
    await wait(() => !!document.querySelector('.knowledge-explorer a[href="#/muc/' + parent + '"]'));
    assert.equal(await page.eval(() => document.documentElement.scrollWidth > innerWidth), false);
    assert.equal(await page.eval(() => document.querySelector('.library-tree-content').getBoundingClientRect().height > 0), true);
    let baseline;
    for (const mode of ['list', 'table', 'card', 'timeline']) {
      await select('Cách xem', mode);
      await wait((mode) => document.querySelector('.library-view-toolbar select')?.value === mode, mode);
      const ids = await page.eval(() => [...new Set([...document.querySelectorAll('.knowledge-library-content a[href^="#/muc/"]')].map((node) => node.getAttribute('href')))].sort());
      assert.equal(ids.length, 2); baseline ??= ids; assert.deepEqual(ids, baseline);
      assert.equal(await page.eval(() => document.documentElement.scrollWidth > innerWidth), false);
    }
    await page.screenshot({ path: resolve(out, 'library-' + width + '.png'), format: 'png' });
    report.viewports.push({ width, tree_visible: true, four_views_same_ids: true, overflow: false });
  }
  report.journeys.push({ id: 'J7', status: 'PASS', actual: 'Actualmixedexplorer+views sameUUID and visibleat4widths, reducedmotion' });
  report.item_ids = { parent, child }; report.folder_ids = { root: root.id, folder: folder.id };
  report.status = 'PASS';
} catch (error) { report.status = 'FAIL'; report.error = String(error.stack ?? error); throw error; }
finally { writeFileSync(resolve(out, 'journeys.json'), JSON.stringify(report, null, 2) + '\n'); await browser.close(); }
