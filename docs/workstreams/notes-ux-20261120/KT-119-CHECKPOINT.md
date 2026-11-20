# KT-119 checkpoint — 20/11/2026

**Code SHA / Tested SHA:** `218da95bb37d9782991915d5e67c9e77293c02fb`.
Frontend/browser was validated at `334a1e3363e8cdea30662fd50b3da66ca1bf763c`;
the final backend-only nested-markup hardening reran all 34 catalog tests.
Branch `codex/kt-119-related`, base `7044b4a0f50a7c831a391f27b1f90cc4aaa21d8b`.
This checkpoint update changes documentation only. No merge or deploy.

## Result

The existing RelatedItems integration now renders three independent disclosures:
RelatedItem with reason/method/source versions, explicit incoming Markdown links,
and same-group membership. Their counts are separate; an Item may appear in
multiple categories. Similar suggestions can be hidden and restored in the
current component view only. No request mutates RelatedItem or curated groups.

Source cards keep sources and assets as separate lists. Only a DerivedContent
row's actual `asset_id` and validated `source_locator.source_id` associate them.
One source can reference several assets; each asset appears once. Unproven
associations remain explicit. Cards expose file content_version, Drive location
status and derived processor/input versions. A stale derived row or mismatched
input hash cannot provide a current file locator. PDF pages and finite ordered
ASR segments normalize into labels, without inventing seek behavior.

## Read-only API contract extension

`GET /api/v1/items/{UUID}/related` retains `results` and adds:

- `results[].method_version`, `results[].source_version` alongside reason,
  relation_type and confidence. Active same-owner/non-deleted peers only.
- `backlinks[]`: item_id, title, note-edit source_version. Only authored,
  supported inline `[label](#/muc/UUID)` links to the requested Item count.
- `same_group[]`: item_id, title and shared groups (kind/id/name), scoped to
  owned active groups and active owned Items.
- `counts`: exact related/backlinks/same_group totals. Each result list caps at
  30, with the UI disclosing the difference from its total.
- `backlinks_scope: inline_markdown_only` and `evidence`: separate sources,
  assets and unassociated_parts plus `truncated`. Source/asset lists cap at 100,
  derived evidence at 1000; no derived body or provider/Drive file ID is exposed.
  Locator data is limited to validated positive page or finite time range.

The endpoint remains session authenticated and read-only. Foreign/deleted targets
return 404; foreign/deleted/stale peers and foreign group assignments are omitted.
No schema, OrganizationService, ingestion, worker or permission changes.

## Validation

Windows / Node 24.15.0 / Python 3.13 / project virtualenv / PostgreSQL on loopback.
Synthetic data only; unique disposable database `test_kt119` created/destroyed.

| Check | Result | Evidence |
| --- | --- | --- |
| `node --test tests/kt119-related.test.mjs` from apps/web | PASS, 13/13 | 30-Item fixture and exact destination sets; hide/undo stays local; source/file status/version; XSS/unsafe IDs; stale locator protection; zero samples; 401/403/404/500; refresh and truncation disclosure |
| `npm test` from apps/web | PASS, 19/19 | Existing UI suite; new file was run explicitly because the shared runner does not discover it |
| `npm run build` from apps/web | PASS | TypeScript/Vite production build; existing >500 kB chunk warning remains |
| Django runner `catalog` | PASS, 34/34 | Nine new KT-119 tests plus existing catalog tests; exact separate corpus counts, permission/deleted/stale exclusions, read-only snapshots, version/asset association, malformed locators, bounded lists with full counts |
| Ruff check and format-check on groups_api.py and test_kt119_connections.py | PASS | No schema/migration changes |
| `git diff --check` | PASS | Only task-owned files changed |
| Source design lint | PASS, 0 FAIL / 0 WARN | RelatedSources.tsx + isolated CSS |
| Chrome 1440 / 768 / 390 px | PASS | Native keyboard Enter opens disclosure and hides suggestion; undo restores; source link focuses exact asset card; callback receives its asset UUID; no overflow or JS exceptions |
| App inspector, all three widths | PASS, 0 FAIL / 3 WARN | Dev fixture only; desktop void/unused canvas reflect a single isolated component rendered at full shell width. Six final fold/page screenshots and three expanded-source screenshots inspected |
| Live personal corpus, Drive readback, physical Android | NOT_RUN | Not authorized/needed for this read-only fixture task; no live storage claim |
| Accuracy when samples = 0 | NOT_RUN | Empty case reports zeros and no accuracy claim |

Canonical corpus: `apps/backend/catalog/fixtures/kt119-connections.json`.
Thirty Items yield 15 explicit backlinks, 10 RelatedItem, and 5 same-group peers;
one peer is both backlink and related. All 30 relationship destinations match
the expected owned active Item IDs. This is fixture correctness, not semantic
quality measured on a personal corpus. Corpus is packaged inside the backend
Docker COPY; the frontend fixture reads that same file.

Backend test runner from apps/backend, with environment values supplied outside
Git and the project virtualenv Python:

```python
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
import django
from django.conf import settings
settings.DATABASES['default']['TEST'] = {'NAME': 'test_kt119'}
django.setup()
from django.test.utils import get_runner
raise SystemExit(bool(get_runner(settings)(interactive=False).run_tests(['catalog'])))
```

For browser reproduction run Vite on loopback and open
`/tests/kt119-browser.html`. Its fetch interceptor only permits the fixture's GET
and uses no backend, account, Drive or AI. This test entry is absent from the
production bundle. Local screenshot/report/interactions JSON artifacts remain
outside Git in sibling `kt119-browser-evidence`. Inspector ran on the development
fixture; production output was built but not separately inspected in Chrome.

Visual review: preserve existing neutral palette/type; all three category counts
and the source disclosure fit the 390 px overview. Expanding the chosen category
avoids a long list obscuring the other types. Source sublabels increased to 13px.
The full-width desktop fixture intentionally has spare space; the component uses
the existing ItemScreen slot without restyling that screen.

## Explicit limits and integration

- Backlink recognition is a conservative adapter, not a complete Markdown parser.
  It omits reference-style links, images, HTML/comments, code, blockquotes, link
  titles, absolute URLs, mixed/nested markup lines and Source URL inverse backlinks.
  A supported link starts at a line/whitespace boundary. The UI says other types
  are unsupported. Derived lexical matches never become backlinks. Note edits
  are read directly, so removing a supported link removes its backlink next read.
- Existing KnowledgeText forward rendering sanitizes relative hash links. This
  task does not change that owned renderer; the reverse panel itself opens valid
  Item routes. G00 assigned a supplementary consumer-contract PR to KT-115 for
  forward authored links and atomic editing. Review that consumer on the same
  base before claiming end-to-end forward/reverse linking is complete.
- Source/asset associations are not inferred from Item co-membership, filenames
  or a 1-source/1-asset assumption. Existing model evidence is incomplete for
  some captured media, shown as unproven association rather than guessed.
- Page/time labels identify provenance only. Precise media seek belongs to KT-116.
  RelatedSources exposes an optional `onOpenAsset(UUID)` callback for that owner;
  the existing RelatedItems slot does not wire it, so no fake file-open control
  appears there. Original safe HTTP(S) source links and asset-card focus work.
- Counts scan owned candidate notes/shared groups with bounded returned lists;
  no 10,000-Item latency or scalability claim is made. Such a benchmark remains
  the readiness gate. No new index or graph database was added.

G00 must run the new frontend test explicitly during integration and owns
CURRENT_STATE after review/merge. No ItemScreen, KnowledgeReading, common API
client/styles/runner or CURRENT_STATE changes. Rollback by reverting this branch's
implementation commits; there are no migrations, stored-data changes or external
writes to undo.
