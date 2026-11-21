# P09 — Independent KT122/123 hierarchy audit

**Snapshot:** `coord/notes-parallel-20261121-frozen` HEAD `9716a6a876d6ec41e10b3c3dcbdc095ab4ddd84d`, code candidate from PR58 `91fe93950224e688471032313367bc5961385b59`. Independent reference: draft PR61 (`4566aa67684f564066977bf8cf968e6729dd018b`). P09 does **not** cherry-pick PR61 or other Pxx.

## Evidence-backed observations (frozen snapshot; not claimed as executed failures)

| ID | Severity | Reproduction / source | Finding | Owner / proposal |
| --- | --- | --- | --- | --- |
| P09-01 | HIGH | One Item, home Folder A + an ItemTopic shortcut to B; PATCH placement move to `null`, then GET `/explorer/children?unfiled=true` versus `/items?unfiled=true`. | `explorer.children` uses `home_topic IS NULL`, while `catalog.api.list_items` excludes any active `ItemTopic`. The same unfiled note can be visible in the tree but absent from the main list. | P04: align both filters on canonical home+live structural-parent policy; test both endpoints. P09 regression uses `@expectedFailure` until fixed. |
| P09-02 | HIGH | Parent Item with 51 or more direct note children, GET `/items/{id}/structure`; view `ItemStructurePanel`. | `structure_info` calls `children(...)` with default `limit=50` and discards `next_offset`. The panel presents the returned array length as total child count, with no pagination. Child 51+ cannot be reached via this panel. | P04 or G00: use paged `/explorer/children?parent_item_id=...` and a total count/load more contract. |
| P09-03 | HIGH (restore portability) | Inspect `tools/backup/backup.py`, `COLLECTIONS["items"]`. | Portable `items` projection omits `home_topic_id,parent_item_id,outline_order,structure_version,structure_origin`. `database.dump` still captures full PostgreSQL tables; the **portable projection**, not necessarily the full pg_dump, loses hierarchy. | P03: extend portable schema/export/import and test stable UUID + edges + parent/orphans. Do not claim full PostgreSQL backup fails solely from this omission. |
| P09-04 | MEDIUM | Root `explorer.children` retrieves folders and notes using the **same offset** separately. | `limit=25` bounds each list independently; combined result may have 50 entries. `next_offset` is shared, so no globally interleaved mixed ordering. Can be acceptable if intentionally specified, but must clarify API/UI contract and count. | P04/G00: document dual-stream pagination or implement one stable mixed cursor; exercise sparse/dense branches. |
| P09-05 | MEDIUM | `ItemStructurePanel` only displays `ancestors` and `children`; `item_query` returns `child_count`. | `structure_info` assumes 50 direct children for display; source links, related notes, and folder shortcuts must remain distinct; cannot use length of first page as a total. | G00: combine separate relationship panes and independently counted child list. |
| P09-06 | MEDIUM | `KnowledgeExplorer` folder row note count uses `context.nodes.find(...).item_count` and note list per folder via ItemTopic. | A deeply placed note with multiple memberships is counted once per ancestor by `tree()`, but may display at several shortcut paths. Counts are per-scope distinct, not a globally deduplicated rendered count. | G00: communicate direct/descendant and shortcut semantics in UI, check four viewport sizes. |

## Test coverage introduced
- `apps/backend/catalog/test_parallel_explorer.py`: 43 invalid API cases incl. 404/409/422, immutable failure state, five-level folder/note paths, 1 UUID/3 folders/1 note parent, CaptureEvent retry semantics, owner boundaries, soft deletion, five-level archive, versioned move/rename, 125/115 pagination, deep 64-node chain and parallel reverse moves. The known cross-API unfiled conflict is `expectedFailure` (must not be counted as PASS).
- `apps/web/tests/p09-explorer.test.mjs`: three-folder same-UUID display, 409 move error, pagination 50+5, bounded 50-child panel (a **limitation assertion**, not acceptance), IME-safe navigation. Uses synthetic JSDOM data.
- Optional `P09_SCALE=1`: 10,000 Items + 1,000 folders, 30 measured pages; P95 formula = 95th percentile of 30 elapsed-millisecond samples, queries/page captured via Django. No fabricated latency claim.

## Reproduction commands
```bash
docker compose up --detach --build --wait
docker compose exec -T api python manage.py test catalog.test_parallel_explorer -v 2
docker compose exec -T web node --test tests/p09-explorer.test.mjs
# Explicit opt-in, isolated QA PostgreSQL only:
docker compose exec -T -e P09_SCALE=1 api python manage.py test catalog.test_parallel_explorer -v 2
```

## Execution status
- **PASS (source inspection):** compared frozen `explorer.py`, `explorer_api.py`, `knowledge_tree.py`, `catalog/api.py`, `models.py`, `migrations/0005/0006`, `tools/backup/backup.py`, PR61 evidence/spec, and frontend explorer/panel code.
- **NOT_RUN (runtime):** full backend Django/PostgreSQL, Node/Vite/JSDOM integration, optional 10k Item benchmark, actual browser/device, restore roundtrip, full CI until GitHub Actions publishes result. Local execution environment has no Django, PostgreSQL or full repo checkout; no credentials or private resources used.
- **Baseline:** PR58 frontend-unit CI failure, later jobs skipped as recorded in frozen INDEX. Not an acceptance pass for P09.

**No production changes.** Findings require independent runtime confirmation before being treated as reproduced incidents. Only G00 merges/integrates; P09 is QA-only.
