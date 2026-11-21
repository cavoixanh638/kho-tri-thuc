# KT-122/123 checkpoint — 21/11/2026

Status CODE_AND_TASK_QA_PASS / FINAL_DOCS_AND_PR_PENDING. Saved21/11/2026.
Branch codex/kt-122-123-explorer, base PR57 e00b3ca through e703e40.
Data/API contract code pushed1f0dd47; this checkpoint saves UI WIP before tests.
No merge, deployment, production DB/Drive/provider calls.

Implemented: Item home/parent/order/version FKs with migrations0005/0006;
bounded mixed children/read/placement/structure API; durable CaptureService
placement callback; folder archival preserves all notes; no auto-parent inference.
Mixed explorer now mounted in LibraryScreen; folder/note lazy pages, create at
folder, node menus, shortcuts, DnD folder/notes, keyboard arrows/Enter, and
ItemStructurePanel for root ItemScreen mounting. Existing views remain.

Verified work already saved before the agent's usage interruption:
- Contract/API code1f0dd47; UI9dd7586; API safety/scale21bb54c.
- Native UI/DOM code3603db9; final native drag test/import-only codef13add5.
- Agent ran15 PostgreSQL test methods with30 API subcases, owner/CSRF/deleted/
  cycles/concurrent moves,10 creates/retries;10k Items/1000 folders,30 samples,
  P95=42.995ms and max3queries/page on loopback QA62224.
-7 new frontend +19 legacy targeted PASS; full frontend238PASS0skip;
  backend274 discovered:272PASS2 existing native opt-in skips.
- Actual Chromium build/Django/PostgreSQL: folder/subfolder/note/child/menu
  shortcut and native drag placement; same ItemUUID/Event, tree visible and
  no overflow at1920/1440/768/390, native Arrow navigation PASS.
- Migration0006→0004→latest on isolated QA PASS with raw Item rows retained.
  Removing schema columns intentionally loses structural relations; do not
  reverse production without a matching backup/restore plan.

Machine report KT-122-123-BROWSER.json names3603db9, while the final drag
test extension isf13add5; do not mislabel the report as a new full-suite run
at the later evidence-only commit. Screenshots are synthetic QA only.
This is module acceptance, not KT128 integrated UAT or production acceptance.
Root mounts ItemStructurePanel in the combined candidate and must reconcile
home/unfiled filtering in catalog/api.py with canonical explorer semantics.
Backup/vault preservation of all new fields and the complete combined user
journeys remain open. Android/nativeIME/productionDrive/100GB NOT_RUN.
Next: create own PR target PR57 and follow CI; finish root KT127/128.
