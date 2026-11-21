#!/usr/bin/env node
/**
 * P15 independent accessibility/responsive QA; does not import or modify production code.
 * --static: reproducible source checks, never a visual/accessibility PASS.
 * --browser: real built React+Django QA host, native CDP key events and screenshots.
 * Never run --browser against production or with real user data.
 */
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const out = resolve(root, process.env.P15_OUT || 'tmp/p15-accessibility');
const baseline = '9716a6a876d6ec41e10b3c3dcbdc095ab4ddd84d';
const code = '91fe93950224e688471032313367bc5961385b59';
const rev = () => {
  try { return execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(); }
  catch { return 'UNKNOWN'; }
};
function write(name, value) {
  mkdirSync(out, { recursive: true });
  writeFileSync(resolve(out, name), JSON.stringify(value, null, 2) + '\n');
}
function staticAudit() {
  const files = ['App.tsx', 'KnowledgeExplorer.tsx', 'KnowledgeText.tsx',
    'SavedCollections.tsx', 'KnowledgeCommandPalette.tsx', 'styles.css',
    'LibraryViews.css', 'SavedCollections.css', 'NoteNavigation.css'];
  const src = Object.fromEntries(files.map(f => [f, readFileSync(resolve(root, 'apps/web/src', f), 'utf8')]));
  const specs = [
    ['S01', 'App.tsx', /<main id="main-content" className="shell canvas" tabIndex=\{-1\}>/, 'present', 'Semantic named main landmark'],
    ['S02', 'App.tsx', /skip[- ]link|Bỏ qua.*(?:điều hướng|nội dung)|href=["']#(?:main|content|main-content)["']/i, 'present', 'Skip-to-main keyboard link implemented'],
    ['S03', 'KnowledgeExplorer.tsx', /<li key=\{key\} role="treeitem"[^>]*tabIndex=\{0\}/g, 'multiple', 'Two treeitem templates tabIndex=0; no roving Tab index'],
    ['S04', 'SavedCollections.tsx', /<select multiple aria-label=\{kind \+ '-' \+ operator\}/, 'absent', 'Vietnamese multi-select labels replace technical English'],
    ['S05', 'KnowledgeText.tsx', /h1:.*<h3.*h2:.*<h3/, 'absent', 'Markdown H1 and H2 no longer flatten together'],
    ['S06', 'KnowledgeCommandPalette.tsx', /<dialog[^>]*aria-labelledby/, 'present', 'Named native dialog'],
    ['S07', 'KnowledgeCommandPalette.tsx', /role="listbox"[^>]*aria-label/, 'present', 'Named listbox'],
    ['S08', 'KnowledgeCommandPalette.tsx', /<button key=\{choice.id\}[^>]*role="option"/, 'present', 'Focusability of options warrants keyboard review'],
    ['S09', 'styles.css', /:focus-visible\s*\{\s*outline:\s*2px/, 'present', 'Global focus outline'],
    ['S10', 'LibraryViews.css', /border:1px solid #b8b8b8/, 'present', 'Select border color needs 3:1 boundary review'],
    ['S11', 'SavedCollections.css', /border:1px solid #b8b8b8/, 'present', 'Collection control boundary needs 3:1 review'],
    ['S12', 'NoteNavigation.css', /@media \(prefers-reduced-motion: reduce\)/, 'present', 'Reduced motion CSS override'],
  ];
  const results = specs.map(([id, f, pattern, expected, note]) => {
    const s = src[f];
    const regex = new RegExp(pattern.source, pattern.flags.includes('g') ? pattern.flags : pattern.flags + 'g');
    const matches = [...s.matchAll(regex)];
    const seen = matches.length;
    const found = seen > 0;
    const pass = expected === 'absent' ? !found : expected === 'multiple' ? seen >= 2 : found;
    const line = found ? s.slice(0, matches[0].index).split('\n').length : null;
    const kind = ['S03'].includes(id) ? 'SOURCE_FINDING'
      : ['S08', 'S10', 'S11'].includes(id) ? 'NEEDS_BROWSER_CONFIRMATION' : 'POSITIVE_SOURCE_EVIDENCE';
    return { id, file: 'apps/web/src/' + f, line, matches: seen, expected, matched: pass,
      status: pass ? kind : 'SOURCE_PATTERN_CHANGED', note };
  });
  const report = {
    task: 'P15', mode: 'static', baseline_sha: baseline, code_snapshot_sha: code,
    tested_sha: rev(), results,
    conclusion: 'Source inspection only. Browser, zoom, focus order, screen reader and visual outcomes NOT_RUN in static mode.'
  };
  write('static-results.json', report);
  console.log(JSON.stringify({ checked: results.length, matched: results.filter(x=>x.matched).length, source_findings: results.filter(x => x.status === 'SOURCE_FINDING').map(x=>x.id), out: resolve(out, 'static-results.json') }, null, 2));
  if (results.some(x => !x.matched)) process.exitCode = 1;
}
function eventData(k) {
  const keymap = { Tab: [9, 'Tab'], Enter: [13, 'Enter'], Escape: [27, 'Escape'],
    ArrowUp: [38, 'ArrowUp'], ArrowDown: [40, 'ArrowDown'],
    ArrowLeft: [37, 'ArrowLeft'], ArrowRight: [39, 'ArrowRight'],
    Space: [32, 'Space'], CtrlK: [75, 'KeyK'] };
  const shift = k === 'ShiftTab';
  const name = shift ? 'Tab' : k;
  const [windowsVirtualKeyCode, code] = keymap[name];
  return { key: name === 'Space' ? ' ' : name === 'CtrlK' ? 'k' : name, code,
    windowsVirtualKeyCode, modifiers: shift ? 8 : name === 'CtrlK' ? 2 : 0 };
}
async function browserAudit() {
  const origin = process.env.P15_QA_URL || 'http://127.0.0.1:62315';
  assert.ok(['http://127.0.0.1:62315', 'http://127.0.0.1:62310'].includes(origin), 'P15 must use a fixed isolated loopback QA port');
  assert.equal(process.env.P15_SYNTHETIC_QA, '1', 'A private synthetic QA account only');
  assert.ok(process.env.P15_CDP_MODULE, 'Absolute path to existing CDP Browser helper required');
  assert.ok(process.env.P15_QA_USER && process.env.P15_QA_PASSWORD, 'QA credentials are required');
  const { Browser } = await import(pathToFileURL(resolve(process.env.P15_CDP_MODULE)).href);
  const report = { task: 'P15', mode: 'REAL_BROWSER', baseline_sha: baseline,
    tested_sha: rev(), transport: 'Isolated synthetic-account real Chromium/React/Django QA',
    screenshots: [], keyboard: [], viewports: [], blocked: [],
    native_screen_reader: 'NOT_RUN', native_browser_zoom: 'NOT_RUN',
    manual_visual_review: 'NOT_RUN', android_hardware: 'NOT_RUN' };
  mkdirSync(out, { recursive: true });
  let browser;
  try {
    browser = await Browser.launch({ extraArgs: ['--no-proxy-server'] });
    const page = await browser.newPage({ width: 1920, height: 1080, reducedMotion: true });
    const sleep = (ms = 80) => new Promise(done => setTimeout(done, ms));
    async function waitFor(fn, arg, label) {
      for (let i = 0; i < 100; ++i) {
        if (await page.eval(fn, arg)) return;
        await sleep(100);
      }
      throw Error('Browser wait timeout: ' + label);
    }
    async function key(k) {
      const e = eventData(k);
      await page.send('Input.dispatchKeyEvent', { type: 'keyDown', ...e });
      await page.send('Input.dispatchKeyEvent', { type: 'keyUp', ...e });
      await sleep();
    }
    async function focus(selector) {
      const ok = await page.eval(s => {
        const el = document.querySelector(s);
        if (!el || !el.getClientRects().length) return false;
        el.focus(); return document.activeElement === el;
      }, selector);
      assert.ok(ok, 'Cannot focus ' + selector);
    }
    async function route(hash, selector) {
      await page.eval(value => { location.hash = value; }, hash);
      await waitFor(s => !!document.querySelector(s), selector, selector);
    }
    let width = 1920;
    async function record(area, which, verify) {
      const id = 'K' + String(report.keyboard.length + 1).padStart(3, '0');
      try {
        await key(which);
        assert.ok(await verify(), 'Expected keyboard interaction was not observed');
        report.keyboard.push({ id, viewport: width, area, key: which, status: 'PASS' });
      } catch (e) {
        report.keyboard.push({ id, viewport: width, area, key: which, status: 'FAIL', error: String(e.message || e).slice(0, 160) });
      }
    }
    const visibleFocus = () => page.eval(() => {
      const el = document.activeElement, r = el?.getBoundingClientRect();
      return !!r && r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight && el.tagName !== 'BODY';
    });
    const shot = async (area) => {
      const name = 'p15-' + area + '-' + width + '.png';
      await page.screenshot({ path: resolve(out, name), format: 'png' });
      report.screenshots.push(name);
    };
    await page.goto(origin);
    await waitFor(() => !!document.querySelector('input[autocomplete="username"]'), undefined, 'login');
    await focus('input[autocomplete="username"]');
    await page.send('Input.insertText', { text: process.env.P15_QA_USER });
    await focus('input[autocomplete="current-password"]');
    await page.send('Input.insertText', { text: process.env.P15_QA_PASSWORD });
    await page.eval(() => [...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'Đăng nhập')?.click());
    await waitFor(() => !!document.querySelector('.knowledge-palette-trigger'), undefined, 'authenticated UI');
    for (const w of [1920, 1440, 768, 390]) {
      width = w;
      await page.setViewport({ width, height: width === 1920 ? 1080 : 900 });
      await route('#/thu-vien', '.knowledge-library-layout');
      await focus('a.brand');
      for (let i = 0; i < 6; i++) await record('global-tab', 'Tab', visibleFocus);
      for (let i = 0; i < 2; i++) await record('global-reverse-tab', 'ShiftTab', visibleFocus);
      await focus('a.brand');
      await record('palette-open', 'CtrlK', () => page.eval(() => !!document.querySelector('dialog.knowledge-palette[open]') && document.activeElement?.matches('dialog input')));
      await record('palette-next', 'ArrowDown', () => page.eval(() => document.querySelector('dialog input')?.getAttribute('aria-activedescendant')?.endsWith('-choice-1') === true));
      await record('palette-previous', 'ArrowUp', () => page.eval(() => document.querySelector('dialog input')?.getAttribute('aria-activedescendant')?.endsWith('-choice-0') === true));
      await shot('palette');
      await record('palette-tab-trap', 'Tab', () => page.eval(() => !!document.activeElement?.closest('dialog.knowledge-palette')));
      await record('palette-esc-return', 'Escape', () => page.eval(() => !document.querySelector('dialog.knowledge-palette')?.open && document.activeElement?.classList.contains('knowledge-palette-trigger')));
      await route('#/thu-vien?collection=new', '.saved-collection-form');
      await focus('.saved-collection-form details > summary');
      await record('collection-open', 'Enter', () => page.eval(() => !!document.querySelector('.saved-collection-form details[open]')));
      await shot('collection');
      await record('collection-tab', 'Tab', visibleFocus);
      await record('collection-reverse-tab', 'ShiftTab', visibleFocus);
      await record('collection-close', 'Space', () => page.eval(() => !document.querySelector('.saved-collection-form details')?.open));
      await route('#/gui', '.research-clipper');
      await focus('.research-clipper select');
      await record('clipper-select-down', 'ArrowDown', () => page.eval(() => document.querySelector('.research-clipper select')?.value === 'article'));
      await record('clipper-select-up', 'ArrowUp', () => page.eval(() => document.querySelector('.research-clipper select')?.value === 'link'));
      await record('clipper-tab', 'Tab', visibleFocus);
      await shot('clipper');
      await route('#/thu-vien', '.knowledge-explorer');
      await page.eval(() => {
        const toggle=document.querySelector('.library-tree-toggle');
        if(toggle && getComputedStyle(toggle).display !== 'none' && toggle.getAttribute('aria-expanded')==='false') toggle.click();
      });
      const nodes = await page.eval(() => document.querySelectorAll('.knowledge-explorer [role="treeitem"]').length);
      if (nodes >= 2) {
        await focus('.knowledge-explorer [role="treeitem"]');
        await record('tree-down', 'ArrowDown', () => page.eval(() => document.activeElement?.getAttribute('role') === 'treeitem' && document.activeElement !== document.querySelector('.knowledge-explorer [role="treeitem"]')));
        await record('tree-up', 'ArrowUp', () => page.eval(() => document.activeElement === document.querySelector('.knowledge-explorer [role="treeitem"]')));
      } else report.blocked.push({ viewport: w, feature: 'tree ArrowUp/Down', status: 'NOT_RUN', reason: 'Need >=2 synthetic folder/note rows' });
      const expandable = await page.eval(() => !!document.querySelector('.knowledge-explorer [role="treeitem"][aria-expanded="false"]'));
      if (expandable) {
        await focus('.knowledge-explorer [role="treeitem"][aria-expanded="false"]');
        await record('tree-expand', 'ArrowRight', () => page.eval(() => document.activeElement?.getAttribute('aria-expanded') === 'true'));
        await record('tree-collapse', 'ArrowLeft', () => page.eval(() => document.activeElement?.getAttribute('aria-expanded') === 'false'));
      } else report.blocked.push({ viewport: w, feature: 'tree expand/collapse', status: 'NOT_RUN', reason: 'Need expandable synthetic row' });
      const qaItemId = process.env.P15_QA_ITEM_ID || await page.eval(async () => {
        const r=await fetch('/api/v1/items?limit=100', {credentials:'same-origin'});
        if(!r.ok)return null;
        const data=await r.json();
        return data.results?.find(x => x.title === 'P08 Giáo trình')?.item_id || null;
      });
      if (qaItemId && /^[0-9a-f-]{36}$/i.test(qaItemId)) {
        await route('#/muc/' + qaItemId, '.markdown-item-detail');
        await shot('note');
        if (await page.eval(() => !!document.querySelector('.note-outline a'))) {
          await focus('.note-outline a');
          const anchor = await page.eval(() => document.querySelector('.note-outline a').getAttribute('href').slice(1));
          await record('toc-enter', 'Enter', () => page.eval(id => document.activeElement?.id === id, anchor));
        } else report.blocked.push({ viewport: w, feature: 'TOC', status: 'NOT_RUN', reason: 'Need synthetic note with >=2 headings' });
      } else report.blocked.push({ viewport: w, feature: 'note/TOC', status: 'NOT_RUN', reason: 'Provide P15_QA_ITEM_ID (synthetic UUID)' });
      await route('#/thu-vien', '.knowledge-library-layout');
      const metrics = await page.eval(() => {
        const shown = [...document.querySelectorAll('body *')].filter(el => {
          const s = getComputedStyle(el);
          return el.getClientRects().length && s.display !== 'none' && s.visibility !== 'hidden';
        });
        const spill = shown.filter(el => getComputedStyle(el).position !== 'fixed' && el.getBoundingClientRect().right > innerWidth + 2)
          .slice(0, 15).map(el => el.tagName.toLowerCase() + (typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).slice(0,2).join('.') : ''));
        const controls = shown.filter(el => el.matches('button,a[href],input,select,textarea,summary'));
        const unnamed = controls.filter(el => {
          if (el.hasAttribute('aria-label') || el.hasAttribute('aria-labelledby') || el.getAttribute('title')) return false;
          if (el.labels && [...el.labels].some(l => l.textContent.trim())) return false;
          return !el.textContent.trim();
        }).map(el => el.outerHTML.slice(0, 160)).slice(0, 12);
        const controlsWithoutFocus = controls.filter(el => {
          const style = getComputedStyle(el);
          return style.outlineStyle === 'none' && !el.matches(':focus-visible');
        }).length;
        return { page_overflow: document.documentElement.scrollWidth > innerWidth + 2, spill,
          controls: controls.length, unnamed_controls: unnamed, controls_without_focus_style_sample: controlsWithoutFocus,
          reduced_motion: matchMedia('(prefers-reduced-motion: reduce)').matches,
          vietnamese_font_check: document.fonts.check('14px Geist', 'Tiếng Việt Ắ Ậ ễ Đ Ư') };
      });
      report.viewports.push({ width: w, ...metrics, status: metrics.page_overflow ? 'FAIL' : 'DOM_CHECK_PASS_NOT_VISUAL' });
      await shot('library');
    }
    try {
      const tree = await page.send('Accessibility.getFullAXTree');
      report.cdp_ax_tree = { status: 'SNAPSHOT_ONLY_NOT_SCREEN_READER', node_count: tree.nodes?.length ?? 0 };
    } catch { report.cdp_ax_tree = 'NOT_RUN_CDP_UNSUPPORTED'; }
    report.summary = {
      actions: report.keyboard.length,
      passed: report.keyboard.filter(x => x.status === 'PASS').length,
      failed: report.keyboard.filter(x => x.status === 'FAIL').length,
      blocked: report.blocked.length,
      gate: report.keyboard.length >= 40 && report.keyboard.every(x => x.status === 'PASS') &&
        report.viewports.every(x => !x.page_overflow) && report.blocked.length === 0
          ? 'BROWSER_DOM_AND_KEYBOARD_PASS_SCREEN_READER_NOT_RUN' : 'INCOMPLETE_OR_FAIL'
    };
    if (report.summary.gate === 'INCOMPLETE_OR_FAIL') process.exitCode = 1;
    console.log(JSON.stringify(report.summary));
  } catch (err) {
    report.fatal = String(err.stack || err);
    process.exitCode = 1;
    console.error(report.fatal);
  } finally {
    write('browser-results.json', report);
    await browser?.close();
  }
}
const arg = process.argv[2];
if (arg === '--static') staticAudit();
else if (arg === '--browser') await browserAudit();
else if (arg === '--help' || !arg) console.log('Usage: node tools/smoke/p15_accessibility.mjs --static|--browser\nBrowser: P15_QA_URL=http://127.0.0.1:62315 P15_SYNTHETIC_QA=1 P15_CDP_MODULE=/absolute/path/to/helper.mjs P15_QA_USER=... P15_QA_PASSWORD=... P15_QA_ITEM_ID=<synthetic-uuid>. Output under tmp/p15-accessibility unless P15_OUT set.');
else { console.error('Unknown mode:', arg); process.exitCode = 2; }
