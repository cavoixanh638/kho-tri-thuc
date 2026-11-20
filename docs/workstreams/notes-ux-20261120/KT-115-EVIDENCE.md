# KT-115 — editor evidence and checkpoint

Scope: isolated Markdown editor PoC; no merge, deploy, schema/API contract change,
or personal-data writes. Baseline `7044b4a0f50a7c831a391f27b1f90cc4aaa21d8b`.
Code/Tested SHA and CI are recorded on the PR after the final commit (a file
cannot truthfully contain its own commit hash).

## Decision, checked 20 November 2026

| Direction | Vietnamese input, keyboard, history | Markdown/raw, GFM, security | Cost, dependencies, replacement |
| --- | --- | --- | --- |
| A: native textarea + existing react-markdown/remark-gfm preview | Native text selection, arrows, backspace, copy/paste and undo/redo; composition guards around save. Unikey/EVKey and Android require device checks. | Source string remains authoritative; no document serialization. Existing renderer supports heading/list/table/link/code/quote; skips HTML and only allows safe HTTP(S) URLs. Map normalized textarea edits back to raw CRLF/CR, preserving untouched spans and Unicode. | Chosen: zero added packages/bytes of third-party dependencies, no paid service. Small React component can be replaced while Item.note/API remain unchanged. |
| B: CodeMirror 6 | Editor transactions/history/keymaps, composition-aware view; still requires Vietnamese device checks. | Source-oriented editor suits raw Markdown; needs Markdown language/configuration and the existing safe preview renderer. | MIT. Adds state/view/commands/language/Markdown packages and adapter integration. Exact bundle size NOT_MEASURED, since not installed. More integration than needed for this PoC; replaceable around a raw string. Official GitHub dev mirror is archived; do not infer runtime support from its metadata. |
| C: Tiptap/ProseMirror + Markdown | Rich structured editing, extension keymaps/history; IME and table behavior need device checks. | Official Markdown extension is beta and parses into JSON then serializes back; whitespace/markers/extensions cannot be assumed byte-lossless. HTML input support requires explicit security review. | Core MIT, optional hosted/paid products unnecessary here. More extensions and conversion logic; exact size NOT_MEASURED. Replacing requires careful source/JSON boundary. |

Primary sources read at decision time:
[native textarea API](https://developer.mozilla.org/en-US/docs/Web/API/HTMLTextAreaElement),
[composition events](https://developer.mozilla.org/en-US/docs/Web/API/Element/compositionstart_event),
[react-markdown security](https://github.com/remarkjs/react-markdown#security),
[CodeMirror official development repository](https://github.com/codemirror/dev),
[CodeMirror MIT license](https://github.com/codemirror/dev/blob/main/LICENSE),
[Tiptap Markdown beta/conversion](https://tiptap.dev/docs/editor/markdown),
[Tiptap license](https://github.com/ueberdosis/tiptap/blob/main/LICENSE.md).
CodeMirror website docs returned HTTP 403 in this environment; no benchmark or
device support claim is made from documentation alone.

## Behavior and boundaries

Three modes: Soạn thảo, Soạn + Xem trước, Đọc bản nháp. Mode buttons retain the
same textarea node so browser history is not intentionally replaced. Native
undo/redo is left to the browser; Ctrl/⌘+Enter is the sole save shortcut and is
ignored during composition. No animation is added. Split panes become stacked
on narrow screens. Existing source/media/history/export panels remain.

Dirty title/description/note drafts are stored in same-tab sessionStorage per
Item ID, recovered after route/remount/reload, removed on successful save,
explicit discard or session-expired event. Storage failure is visible; beforeunload
warns. Closing the tab clears sessionStorage by browser policy. This is a local
same-tab recovery feature, not a server/offline queue; browser storage remains
readable to same-origin scripts. Explicit logout currently does not emit the
session-expired event; cross-account Item access still requires server auth.

Only changed text fields are PATCHed. A fresh GET compares those fields with the
draft base, blocks observed drift/deletion, and retains the draft. Backend
user_edit_version is internal and absent from ItemSummary/ItemPatch. There is
still a GET/PATCH race: atomic concurrent-write protection is NOT_IMPLEMENTED;
adding an API precondition is a separate core-owned proposal. Worker changes to
untouched fields are not overwritten. No fake expected-version field is sent.

## Verification checkpoint

- PASS: existing `npm test`, 19 tests.
- PASS: `npm run build`; existing >500 kB chunk warning remains.
- PASS: `node --test tests/kt115-editor.test.mjs`, 46 checks including 40/40
  independent fixture raw-byte/HTML round trips, `unexpected_changed_bytes = 0`.
  Transport is mocked: open → intentional edit → PATCH JSON → remount/reload;
  this does not prove PostgreSQL persistence.
- PASS: design skill source lint, 0 FAIL/0 WARN.
- Browser/visual QA: in progress at this checkpoint; final PR records result.
- NOT_RUN: native Unikey/EVKey, real Android, production writes, real DB
  editor round trips. Synthetic composition dispatch is not native IME proof.

Repeatable browser fixture: `node tests/kt115-browser-server.mjs` (loopback only,
production-built synthetic transport, no actual API access). Run
`node --test tests/kt115-browser.test.mjs` with `KT115_CDP_MODULE` pointing to the
design skill's `scripts/lib/cdp.mjs` and optional `KT115_BROWSER_URL`.
The browser test skips explicitly if the CDP adapter is unavailable. It must be
invoked separately; `npm test` only runs the shared legacy suite.

Design application: existing brand/type/palette kept, no direction redraw for a
single component. Screen question: “Can I edit this note and inspect the result
before saving?” The raw/preview pair carries that job. Synthetic Vietnamese note,
table, link, code and quote are test-only, never production content. Tablet rail
panels are independent sections, so they need not stretch to the editor height.

Rollback: revert the editor change and keep Item.note/DB/Drive intact. Export or
copy any dirty tab-local drafts before reverting; old UI cannot recover these
drafts automatically. No destructive migration or Drive action is necessary.
