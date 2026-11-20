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

PASS initial TypeScript/Vite build. Unit/API/native-browser acceptance NOT_RUN
at this checkpoint. Next:100-note/200-link owner/rename/restore contracts,
30 Markdown AST fixtures,20 palette actions and actual Chromium acceptance,
push tests/evidence and create PR targeting codex/notes-ux-integration.
