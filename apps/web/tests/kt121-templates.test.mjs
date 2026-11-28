import assert from 'node:assert/strict';
import { before, after, beforeEach, afterEach, test } from 'node:test';
import { createServer } from 'vite';
import { JSDOM, VirtualConsole } from 'jsdom';
import { setImmediate as settle } from 'node:timers/promises';

let server, ui, dom, root, container, applications, currentNote, accepted, pending;
before(async () => {
  dom = new JSDOM('<html><body></body></html>', { url: 'http://127.0.0.1/', pretendToBeVisual: true, virtualConsole: new VirtualConsole() });
  for (const name of ['window', 'document', 'navigator', 'HTMLElement', 'Element', 'Node', 'Event', 'MouseEvent', 'CustomEvent', 'MutationObserver', 'getComputedStyle']) {
    Object.defineProperty(globalThis, name, { value: name === 'getComputedStyle' ? dom.window[name].bind(dom.window) : dom.window[name], configurable: true, writable: true });
  }
  window.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
  globalThis.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
  Object.defineProperty(document, 'fonts', { value: new dom.window.EventTarget(), configurable: true });
  globalThis.requestAnimationFrame = window.requestAnimationFrame.bind(window);
  globalThis.cancelAnimationFrame = window.cancelAnimationFrame.bind(window);
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom', logLevel: 'silent' });
  ui = await server.ssrLoadModule('/tests/kt121-entry.tsx');
});
beforeEach(() => {
  applications = []; currentNote = ''; accepted = true; pending = undefined;
  container = document.createElement('div'); document.body.append(container); root = ui.createRoot(container);
});
afterEach(async () => { await ui.act(async () => root.unmount()); container.remove(); });
after(async () => { await server.close(); dom.window.close(); });
async function render(note = '', disabled = false) {
  currentNote = note;
  await ui.act(async () => {
    root.render(ui.createElement(ui.MantineProvider, null, ui.createElement(ui.NoteTemplatePicker, { note, disabled, onApply: async (proposal) => {
      applications.push(proposal); if (pending) await pending;
      const next = ui.acceptNoteTemplate(currentNote, proposal); if (!accepted || next === undefined) return false;
      currentNote = next; return true;
    } }))); await settle();
  });
}
async function click(label) {
  const button = [...container.querySelectorAll('button')].find((button) => button.textContent === label || button.querySelector('strong')?.textContent === label);
  assert.ok(button, label); await ui.act(async () => { button.click(); await settle(); });
}
async function input(label, text) {
  const id = [...container.querySelectorAll('label')].find((node) => node.textContent === label)?.htmlFor;
  const field = document.getElementById(id); assert.ok(field, label);
  await ui.act(async () => { Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(field, text); field.dispatchEvent(new window.Event('input', { bubbles: true })); await settle(); });
}
test('opening and selecting a template does not modify a draft or submit its outer form', async () => {
  await render('Ghi chú nguyên văn');
  for (const label of ['Bài học', 'Sách / Chương', 'Cuộc họp', 'Video nguồn']) { await click(label); assert.equal(currentNote, 'Ghi chú nguyên văn'); }
  assert.equal(applications.length, 0); assert.equal(container.querySelectorAll('button:not([type="button"])').length, 0);
  await click('Bỏ chọn'); assert.equal(container.querySelector('.note-template-preview'), null);
});
test('empty optional metadata is allowed and no template fields become required', async () => {
  await render(); await click('Bài học'); assert.equal(container.querySelectorAll('[required]').length, 0);
  await click('Dùng mẫu trong bản nháp'); assert.equal(currentNote, ui.noteTemplates[0].markdown);
  assert.match(container.textContent, /Chưa lưu lên máy chủ/); assert.equal(applications.length, 1);
});
for (const [id, label] of [['lesson', 'Bài học'], ['book', 'Sách / Chương'], ['meeting', 'Cuộc họp'], ['video', 'Video nguồn']]) {
  for (let index = 0; index < 10; index++) test(`${id} / Vietnamese item ${index + 1}: append, JSON save/reload/export exact`, async () => {
    const newline = ['\n', '\r\n', '\r'][index % 3];
    const raw = `  Ghi chú ${index + 1} tiếng Việt Tiếng 🧑‍🚀${newline}Dòng sau **nguyên văn**  `;
    await render(raw); await click(label); await input('Tác giả', `Nguyễn Thị Học ${index + 1}`);
    await input('Ngày nguồn', '2026-11-20'); await input('Liên kết nguồn', 'https://example.org/nguon');
    await click('Thêm mẫu vào cuối');
    assert.deepEqual(Buffer.from(currentNote.slice(0, raw.length)), Buffer.from(raw));
    assert.ok(currentNote.endsWith(ui.noteTemplates.find((entry) => entry.id === id).markdown.split('\n').slice(1).join(newline)));
    assert.ok(currentNote.includes(`Tác giả: Nguyễn Thị Học ${index + 1}`));
    const item = { item_id: `synthetic-${id}-${index}`, note: currentNote, asset_id: `asset-${index}`, capture_id: `capture-${index}` };
    const reloaded = JSON.parse(JSON.stringify(item));
    assert.deepEqual(reloaded, item); assert.deepEqual(Buffer.from(reloaded.note), Buffer.from(currentNote));
    assert.equal(applications[0].templateVersion, 1); assert.equal(applications[0].expectedNote, raw);
  });
}
test('stale host draft is rejected and preview remains available', async () => {
  await render('Gốc'); await click('Video nguồn'); currentNote = 'Vừa sửa trước khi thêm';
  await click('Thêm mẫu vào cuối'); assert.equal(currentNote, 'Vừa sửa trước khi thêm'); assert.match(container.textContent, /Bản nháp đã thay đổi/); assert.ok(container.querySelector('.note-template-preview'));
});
test('pending application accepts once and error keeps the draft and selection', async () => {
  let resolve; pending = new Promise((done) => { resolve = done; });
  await render('Gốc'); await click('Cuộc họp');
  await click('Thêm mẫu vào cuối'); assert.equal(applications.length, 1);
  assert.equal(container.querySelector('.note-template-actions button').disabled, true);
  await ui.act(async () => { resolve(); await settle(); }); assert.equal(applications.length, 1);
});
test('invalid or active metadata URL is rejected, while Markdown punctuation remains literal', async () => {
  await render(); await click('Bài học'); await input('Liên kết nguồn', 'javascript:alert(1)'); await click('Dùng mẫu trong bản nháp');
  assert.equal(applications.length, 0); assert.match(container.textContent, /HTTP hoặc HTTPS/);
  assert.throws(() => ui.proposeNoteTemplate('', 'lesson', { sourceDate: '2026-13-01' }), /Ngày nguồn/);
  assert.throws(() => ui.proposeNoteTemplate('', 'lesson', { sourceDate: '2026-02-30' }), /Ngày nguồn/);
  assert.throws(() => ui.proposeNoteTemplate('', 'lesson', { author: 'a\n# injection' }), /một dòng/);
  assert.throws(() => ui.proposeNoteTemplate('', 'lesson', { sourceUrl: 'https://example.org\n# injection' }), /HTTP hoặc HTTPS/);
  assert.match(ui.proposeNoteTemplate('', 'lesson', { author: '<script>**Việt**' }).nextNote, /\\<script\\>\\\*\\\*Việt/);
});
test('disabled and oversized drafts are preserved', async () => {
  await render('Gốc', true); assert.ok([...container.querySelectorAll('button')].every((button) => button.disabled));
  assert.throws(() => ui.proposeNoteTemplate('a'.repeat(ui.NOTE_TEMPLATE_MAX_LENGTH), 'lesson'), /quá dài/);
  assert.equal(ui.acceptNoteTemplate('thay đổi', ui.proposeNoteTemplate('gốc', 'lesson')), undefined);
});
