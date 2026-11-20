# KT-119 checkpoint — WIP, 20/11/2026

Branch `codex/kt-119-related`, base `7044b4a0f50a7c831a391f27b1f90cc4aaa21d8b`.
No merge or deploy. Final Code SHA/Tested SHA and browser evidence will be recorded
before the review PR is completed.

Implemented: separate explicit backlinks / RelatedItem / same-group counts,
relation reason/method/source versions, display-only reversible hiding of similar
suggestions, source and asset cards with actual DerivedContent associations,
version/hash checks before locator labels. No schema, OrganizationService,
curated group, common API client/runner/style or CURRENT_STATE changes.

Initial validation: 13 new frontend tests PASS, existing 19 frontend tests PASS,
TypeScript/Vite build PASS (existing large-chunk warning), 7 new PostgreSQL tests
+ 3 existing group API tests PASS on unique disposable `test_kt119`, Ruff PASS.
The shared corpus lives inside backend/catalog/fixtures so backend Docker tests
can read it without frontend files. It has 30 synthetic Items, 15 explicit note
backlinks, 10 RelatedItem and 5 same-group peers; one Item belongs to two relation
types, intentionally demonstrating independent counts.

Pending: adversarial boundary checks and browser/keyboard/mobile fixture review,
final test run, final checkpoint, commit/push/PR attachment. No production data,
Drive, credentials or AI requests. Zero-sample accuracy remains NOT_RUN.
