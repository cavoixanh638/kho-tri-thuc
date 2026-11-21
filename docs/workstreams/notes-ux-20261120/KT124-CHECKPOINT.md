# KT124 — navigation/linking checkpoint

IN_PROGRESS. Branch codex/kt-124-navigation, baseline e703e40 / PR57 e00b3ca.
No merge/deploy/production data. Owner kt124; root mounts App/router glue.

Implemented initial code: [[ autocomplete inserts canonical UUID Markdown;
AST heading TOC; visible/mobile command dialog with Ctrl+K/keyboard/IME guards;
owner-scoped navigation and outgoing/incoming/unlinked APIs; context panel.
The existing palette shell/palette/type are retained; no dependency or service.

Host contracts: mount KnowledgeCommandPalette(currentItemId?, onAction?) in
authenticated App; action create/move/attach/day. Mount catalog.navigation_api
router at API root. Existing MarkdownEditor/KnowledgeText/RelatedSources are
connected automatically. Root retains structural parent/child host integration.

PASS TypeScript/Vite build;81 targeted frontend tests (34 KT124 +47 editor),
including30 Markdown AST fixtures and20 palette actions. PostgreSQL3 tests
PASS with100 notes/200 UUID links, rename, duplicate titles, ownership/deletion,
pagination and exact-microsecond JSON roundtrip. No new relations on mentions.
Native Chromium actualAPI acceptance IN_PROGRESS; earlier invocation was blocked
by automatic approval usage limit, resumed21/11. Harness initialURL404 corrected.
Next: finish four-width native acceptance, full frontend suite/lint, final
evidence/PR targeting codex/notes-ux-integration. Production/Android NOT_RUN.
