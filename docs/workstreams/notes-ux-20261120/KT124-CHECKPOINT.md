# KT124 — navigation/linking checkpoint

CODE_DONE / MODULE_BROWSER_PASS, combined host UAT owned by KT128.
Branch codex/kt-124-navigation, baseline e703e40 / PR57 e00b3ca.
No merge/deploy/production data. Owner kt124; root mounts App/router glue.

Implemented initial code: [[ autocomplete inserts canonical UUID Markdown;
AST heading TOC; visible/mobile command dialog with Ctrl+K/keyboard/IME guards;
owner-scoped navigation and outgoing/incoming/unlinked APIs; context panel.
The existing palette shell/palette/type are retained; no dependency or service.

Host contracts: mount KnowledgeCommandPalette(currentItemId?, onAction?) in
authenticated App; action create/move/attach/day. Mount catalog.navigation_api
router at API root. Existing MarkdownEditor/KnowledgeText/RelatedSources are
connected automatically. Root retains structural parent/child host integration.

Behavior code/tested52efd9ef4b75c57fccb657716f11d8c226de357c.
Final visual/native code/testedc5acff27ed6cc61cd31e050828e3a26f089ec357.
PASS full frontend265 tests (34 KT124 +231 existing),0fail/0skip; build/Ruff.
PostgreSQL3 tests PASS:100 notes/200 UUID links, rename, duplicate titles,
ownership/deletion, pagination and exact-microsecond JSON roundtrip.
Native Chromium actualAPI:6headingfocusjumps,UUIDautocomplete+PATCH,
20nativekeyboardcommands at1920/1440/768/390,nohorizontaloverflow.
Action callbacks create/move/attach/day execute in the isolated fixture;
actual structural/source action host and whole-app journeys remain KT128.
Evidence KT124-BROWSER.json +2synthetic screenshots. PR59 targetPR57branch.
No relations created from mentions; unavailable/private target labels stay
generic. Production/Android/nativeUnikey/EVKey NOT_RUN.
Next: root integrates host/router glue and follows exact-head CI on PR59;
do not merge/deploy. No more feature work remains in this isolated scope.

## Decisions and limits

Stored syntax is ordinary [label](#/muc/UUID) Markdown after explicit [[
completion. Raw title-based [[name]] alone is ambiguous after rename and for
duplicate titles; a separate link registry would require schema/export syncing.
Chosen UUID Markdown reuses the approved renderer, parser and portable text,
with no dependency/model change. Unresolved typed [[ text stays verbatim.
AST outline uses parsed headings (including GFM/setext), excludes code and
source HTML, and does not rewrite raw notes. Heading IDs normalize NFC and
append occurrence; TOC focus is scoped to the current rendered note.
Mention candidates are bounded lexical name matches, explicitly not edges;
rich hover/source sidepane is a later phase, not claimed here.
