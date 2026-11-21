# P15 — Independent accessibility / responsive audit evidence

**Source:** `coord/notes-parallel-20261121-frozen` at `9716a6a876d6ec41e10b3c3dcbdc095ab4ddd84d`; code snapshot `91fe93950224e688471032313367bc5961385b59`. **Date:** 2026-11-21.

## Evidence boundary

This document is **source inspection**, not browser, zoom, assistive-technology or visual acceptance. The independently replayable harness is `tools/smoke/p15_accessibility.mjs`; running with `--static` creates `static-results.json`; `--browser` creates `browser-results.json` and local screenshot PNGs, but the latter has **NOT_RUN** without a dedicated synthetic QA server, CDP helper and data. No private screenshots are committed.

Twelve targeted regex inspections were executed against GitHub-fetched source; **12/12 patterns matched expected source**. A matched issue pattern establishes a code-level concern, not a demonstrated real-user failure. Existing positive indicators include a semantic main landmark, labelled dialog/listbox, CSS focus styles and reduced-motion override. No global accessibility compliance claim follows.

## Findings for G00 triage

| ID | Severity / status | Exact location and source evidence | User repro / expected | Proposed owner |
| --- | --- | --- | --- | --- |
| A11Y-01 | P2 / SOURCE_FINDING | `apps/web/src/KnowledgeExplorer.tsx:88,100`: each folder/note `role="treeitem"` has `tabIndex={0}`, while the same tree handles ArrowUp/Down at lines 148–156. | At 1920, 1440, 768 and 390, build a synthetic tree with 10+ rows. Tab through tree from its preceding control and count row stops. Expected: tree navigation uses one roving focus entry or aria-activedescendant, Arrow keys travel; not every tree row in the global Tab order. Confirm with keyboard + screen reader. | G00 coordinates P04 or later a11y fix |
| A11Y-02 | P2 / SOURCE_FINDING | `apps/web/src/KnowledgeText.tsx:16–17`: Markdown `h1` and `h2` both render as `h3`; `h3` and `h4` both render as `h4`. `NoteOutline.ts` uses original Markdown depth. | Open synthetic note containing H1..H6 in the item view; inspect accessibility headings and skip heading navigation. Expected: meaningful nested semantic heading sequence (page H1 and article headings) preserving logical hierarchy. | G00 with P06/P10 coordination |
| A11Y-03 | P2 / SOURCE_FINDING | `apps/web/src/SavedCollections.tsx:80`: native `select multiple` has `aria-label={kind + '-' + operator}`; these strings resolve to English internal tokens such as `topics-any` despite a visible Vietnamese `label`. | On New Collection, expand “Điều kiện nhóm, thời gian và trạng thái”; navigate to Chủ đề / thư mục -> Bất kỳ and inspect accessible name via browser accessibility tree and NVDA/TalkBack. Expected: contextual Vietnamese label, e.g. “Chủ đề / thư mục — Bất kỳ”; keyboard multi-select guidance audible. | G00 with P11 |
| A11Y-04 | P2 / SOURCE_FINDING limited to App | `apps/web/src/App.tsx:22–47,168`: brand/navigation and main landmark are rendered but no skip-to-main control appears in App.tsx. | At each viewport reload authenticated page, press Tab from browser chrome. Expected: visible “Bỏ qua điều hướng” leading to focusable main/article landmark; assess whether Mantine injected any global skip control before accepting as real defect. | G00 / App owner P01 |
| A11Y-05 | P3 / NEEDS_BROWSER_CONFIRMATION | `apps/web/src/KnowledgeCommandPalette.tsx:86`: each `role=option` is also a tabbable `button`; combobox uses active-descendant and Arrow/Enter on input. | With results, Ctrl+K; press repeated Tab then Shift+Tab and ArrowDown/Enter/Esc. Verify no unintended extra tab stops, correct focus containment and return; capture accessibility tree. | G00 / P10 |
| A11Y-06 | P3 / NEEDS_VISUAL_CONFIRMATION | `apps/web/src/LibraryViews.css:3` and `SavedCollections.css:10`: select/input 1px border `#b8b8b8` on `#fff`. Calculated sRGB contrast **1.98:1**, below 3:1 for necessary control boundaries unless other visual cues suffice. | At 390 px and 200% zoom, inspect normal, focus, hover and disabled boundaries, sample computed color including backgrounds and browser semantics. Expected: perceivable input boundary; verify WCAG 1.4.11 applicability rather than asserting a violation solely from CSS. | G00 / UI design |

## Real-browser reproduction matrix

- **Viewport:** 1920×1080, 1440×900, 768×900, 390×900; synthetic tree with nested folder, note, shortcut and 2+ headings; synthetic saved collection and clipper. Prefer Chromium native keyboard dispatch; screenshots for each major feature. 200% *native browser zoom* and horizontal scrolling checked separately (CSS zoom is not a substitute).
- **Keyboard:** global forward/reverse Tab, command palette Ctrl+K / ArrowUp / ArrowDown / Enter / Esc, tree ArrowUp/Down/Left/Right and Enter, collection native select/options/fieldset, clipper select, article TOC Enter. Harness runs **80 core key actions** across viewports even when fixture-gated tree/TOC checks are unavailable; gated checks report `NOT_RUN`, not invented PASS.
- **Focus/AT:** visible focus indicator and logical return, modal trap, spoken names for tree and collections, headings hierarchy and live regions. DOM/CDP AX tree snapshots are *not* NVDA, VoiceOver or TalkBack testing.
- **Layout:** `documentElement.scrollWidth` at each viewport, element spill candidates, no horizontal page overflow, readable Vietnamese combining marks and font fallback, text contrast/labels, `prefers-reduced-motion`. Internal horizontal scroll for tables can be acceptable; examine clipped actions manually.
- **Required acceptance:** 40+ native key interactions without blocking errors; no page overflow; meaningful accessible names; no critical focus trap or inaccessible controls; screen reader and visual pass only when actually run.

## Re-run without secrets in Git

```bash
node tools/smoke/p15_accessibility.mjs --static
P15_QA_URL=http://127.0.0.1:62315 P15_SYNTHETIC_QA=1 \
  P15_CDP_MODULE=/absolute/path/to/qa-browser.mjs \
  P15_QA_USER=synthetic-user P15_QA_PASSWORD='<local-test-only>' \
  P15_QA_ITEM_ID='<synthetic-note-uuid>' \
  node tools/smoke/p15_accessibility.mjs --browser
```

The browser mode refuses any host other than the fixed QA localhost URL, requires explicit synthetic data acknowledgement, logs no credentials, does not save/delete data or modify app source. Screenshots/results default to ignored `tmp/p15-accessibility`; copy only sanitized results to `evals/parallel/p15-assets` if necessary. **Current execution:** browser mode NOT_RUN; no screenshot, real-device, physical keyboard, AT, Drive, prod or full CI results claimed.

## Remaining decisions

G00 should assign remediation in the relevant owner PR after confirming issues in an isolated real browser. Source-only defects above may have downstream dependencies on P01/P04/P06/P10/P11. This PR intentionally includes only independent test/evidence; **INTEGRATION_REQUIRED** for any source fix. Rollback is deleting the new P15-owned paths, with no database or user data impact.
