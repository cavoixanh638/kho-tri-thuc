# KT-125 saved smart collections

Status: CODE_AND_NATIVE_QA_PASS, parent integration/CI follow-up pending.
Branch codex/kt-125-collections, base e703e40 / PR57.
No merge, deployment, production database, Drive or AI-provider access.

Implemented query-definition model, CRUD/preview/paged dynamic results API,
sidebar SavedCollectionsPanel and main SavedCollectionScreen, existing-field
PropertyChips. Query schema is strict/allowlisted, SQL values are parameters,
group predicates use EXISTS to avoid duplicate Item IDs. No membership writes.

SavedCollection registers through CatalogConfig.import_models in apps.py.
The application API mounts collection_api.router. Root owns final LibraryScreen/
ItemScreen host glue in the combined branch; no duplicate models.py import needed.
Migration0007 depends0004 on this isolated branch; root will reconcile it after
KT122/123 migrations0005/0006. UI: collectionIdFromHash(hash) returns UUID/new;
LibraryScreen main renders SavedCollectionScreen csrf/id when selected, sidebar
renders SavedCollectionsPanel. Folder navigation must not strip collection=.

## Validation and code binding

- Final code SHA:754710b47b04988411e221aaeb81e0e6a4f92255. Full backend:
  267 discovered,264 PASS/3 opt-in SKIP,0 failure,48.366s. Skips are native
  KT116/KT125 browser and KT121 native restore. KT125 native browser separately
  executed and passed below; inherited PR57 evidence is not re-labelled as new.
- Behavioral native/scale code:d85bd90cf71c4030b645e0350b9e859d13a9922b.
  8/8 targeted tests (7 backend+1 native Chrome),43.505s. Includes30 independent
  AND/OR/EXCLUDE/timezone combinations, owner/anonymous/CSRF/invalid DSL/archived/
  deleted scopes, version409, Unicode names, preview no mutation, dynamic note/tag
  membership, and query-definition deletion retaining every Item/pinned relation.
- Full frontend npm test:238 PASS,0 FAIL,0 SKIP,42.929s;7 new KT125 DOM tests.
  TypeScript/Vite build PASS, existing >500kB main bundle warning unchanged.
- Fresh QA DB migration forward, catalog reverse0007→0004→0007, reapply/check
  PASS with no schema drift. Registration fix9543e9c separately checked via
  ordinary manage.py check/makemigrations and6 API regression cases.
- New Python check/format PASS from repo root; own delta diff-check vs e703e40
  PASS. Four trailing-whitespace findings in inherited main task docs are
  reported to root for combined cleanup, not hidden or rewritten by this worker.

### Scale measurement

Actual PostgreSQL18, loopback62224, Python3.13/Django5.2 on Windows, synthetic
10000 owned Items+1 other-owner Item,100 Topic groups,5 saved definitions;
301 actual HTTP testclient pages. All IDs/order/counts match independent
queryset expectations without duplicate rows. Final full-run P95=117.28ms,
median=38.29ms, max7 DB queries/page. P95 uses sorted samples[ceil(.95*n)-1].
No production latency/SLA is claimed.

The initial bulk-fixture measurement had stale PostgreSQL planner statistics
(P95=6165.65ms,446.655s suite). TestCase bulk inserts are uncommitted, so
autovacuum cannot update them. The benchmark now explicitly ANALYZEs the four
synthetic tables before timing, keeping real GIN/EXISTS query plans measurable.
An intermediate run measured106.1ms; final evidence uses the later117.28ms
run above. No production DB setting/index was silently changed.

### Native user workflow

Chrome157.0.8103.79, actual Django session/CSRF+PostgreSQL via a temporary Vite
focused component host, **no mocked fetch**. Native Vietnamese/NFD input and
Enter submit; preview creates0 definitions; explicit save persists query/view;
four modes keep identical IDs; actual browser reload keeps Table; actual Item
favorite PATCH changes membership; explicit delete removes only the definition.
1920×1080,1440,768,390:0 document overflow. Browser console has0 errors.
[Machine report](KT125-BROWSER.json), [desktop](kt125-collections-1920.png),
[narrow](kt125-collections-390.png). These are focused component screenshots,
not a claim that parent LibraryScreen integration is already accepted.

Inspector has0 FAIL at all widths. Three WARNs are intentional: the short
navigation sidebar ends before the table at1920/1440, and the1920 empty lower
screen reflects only2 matching synthetic notes. We retain truthful small data
instead of adding filler rows or stretching a navigation panel. Source UI lint:
0 FAIL/0 WARN. Existing achromatic ledger direction/palette/type retained,
no new fonts/assets/dependencies.

## Decisions and limits

SavedCollection stores a strict versioned JSON query, not raw SQL/DSL or a
materialized member list. Compared alternatives: SQL text has unsafe migration/
permission semantics; storing Item-membership snapshots would become stale
and confuse physical folder membership. The allowlisted JSON form is portable,
validated on writes and dynamically evaluated by bound SQL values/EXISTS.
FTS uses exactly the existing KT104 GIN expressions and public.kt_vi functions.
Source-state conditions match the existing note-only display policy. Missing/
archived groups produce no matches on inclusive conditions; invalid group IDs
are rejected on save. Published sort places missing dates last.

Read-only metadata only: real type, received/published timestamps, source state,
favorite and actual Topic/Project/Tag names. No author or typed custom fields
are fabricated from Markdown. Kanban/calendar/arbitrary workflows/custom typed
schema remain optional phase2, requiring an actual usage need and separate ADR.
No copied Items/Assets/Events/ItemTopic relationships, Drive moves or provider.
Parent KT127 owns portable-vault/backup inclusion of SavedCollection definitions.
Android, native Unikey/EVKey, production Drive and deployed Windows are NOT_RUN.

## Reproduction and rollback

From apps/web: npm test; npm run build. From apps/backend with QA DSN:
python manage.py test catalog.test_collections --noinput -v1.
Opt-in native browser additionally sets KT125_BROWSER_NATIVE=1 and
KT125_CDP_HELPER to the installed design-taste CDP helper, then runs
catalog.test_collections_browser. Native guard requires QA62224 and a
test_kt_125* database. QA passwords are environment-only; no secrets/media/dumps
or personal data are committed.

Before deployment, omit this branch to roll back. Removing the UI/API preserves
definitions in DB. Reversing migration0007 drops saved filters, so export/backup
them first; the tested reverse/reapply proof used a new empty QA schema only.
No production migration, merge, auto-merge or deployment was performed.
