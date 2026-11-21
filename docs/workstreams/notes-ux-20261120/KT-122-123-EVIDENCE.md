# KT-122/123 checkpoint — 21/11/2026

Status IN_PROGRESS / UI_BUILD_PASS / API_TEST_PENDING.
Branch codex/kt-122-123-explorer, base PR57 e00b3ca through e703e40.
Data/API contract code pushed1f0dd47; this checkpoint saves UI WIP before tests.
No merge, deployment, production DB/Drive/provider calls.

Implemented: Item home/parent/order/version FKs with migrations0005/0006;
bounded mixed children/read/placement/structure API; durable CaptureService
placement callback; folder archival preserves all notes; no auto-parent inference.
Mixed explorer now mounted in LibraryScreen; folder/note lazy pages, create at
folder, node menus, shortcuts, DnD folder/notes, keyboard arrows/Enter, and
ItemStructurePanel for root ItemScreen mounting. Existing views remain.

PASS: TypeScript/Vite build on current UI; diff check.
PENDING: PostgreSQL API/owner/cycle/concurrency/scale, explicit frontend tests,
actual browser4width/keyboard/DnD, migration checks and CI. Do not infer UX_DONE.
Next: run/repair tests, push evidence and create PR target PR57 branch.
Root owns final integrated browser journeys and backup/vault projection.
