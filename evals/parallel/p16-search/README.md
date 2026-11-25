# P16 — Vietnamese SearchService relevance/provenance benchmark

Scope: **synthetic evaluation only**, against the frozen P16 base. Neither production SearchService nor DB indexes/migrations are changed.

## Dataset and gold

- `corpus.json`: 28 synthetic Items across two owners (A/B), 86 gold queries; 73 positive and 13 empty-gold negative queries.
- Cases: accented/unaccented/NFD uppercase, title/description/note, active vs stale derived content, latest link CaptureEvent, Source.metadata hallucination traps, M:N Topics, Project/Tag filter, Item UUID duplication, soft delete, owner isolation, identifiers/typos, lexical-vs-semantic gap.
- Human relevance signoff: **NOT_RUN**. Do not market these synthetic metrics as external search quality.
- Empty-gold queries are **safety/false-positive checks**, excluded from micro recall/precision denominators; positives with no results have recall 0 and undefined precision if *all* positives have no results.
- `recall@5 = sum(|top5(q) ∩ gold(q)|) / sum(|gold(q)|)`; `precision@5 = sum(|top5(q) ∩ gold(q)|) / sum(|top5(q)|)`, over positive-gold queries. Denominators = 0 => `null`. Some deliberately challenge lexical-only FTS; a FAIL is not retrofitted into gold.

## Local offline validation (stdlib; no DB)

From repository root:

```bash
python tools/search/p16_eval.py --validate
python -m unittest discover -s evals/parallel/p16-search -p 'test_*.py' -v
```

Offline validation verifies corpus/gold invariants and metric math. It does **not** run SearchService, prove permission safety, or measure PostgreSQL P95.

## PostgreSQL live benchmark (only isolated disposable test database)

Start an **isolated** PostgreSQL instance and a fully migrated Django database whose name starts with `test_` or `p16_`; never point to real data. Install backend requirements. The runner refuses other database names and requires explicit opt-in. From repository root:

```bash
export DJANGO_SECRET_KEY='local-p16-nonproduction'
export POSTGRES_HOST='127.0.0.1'
export POSTGRES_DB='p16_search_eval'
export POSTGRES_USER='p16_eval'
export POSTGRES_PASSWORD='local-test-only'
export PYTHONPATH="$PWD/apps/backend"
python apps/backend/manage.py migrate --noinput
P16_ALLOW_TEST_DB=1 python apps/backend/manage.py shell -c "exec(open('tools/search/p16_eval.py',encoding='utf-8').read()); run_live()"
```

The runner wraps fixture creation and all 86 synchronous `SearchService.search(limit=5)` calls in a transaction, then rolls back. It prints actual matches, relevance scores, empty-gold violations, evidence provenance errors, and a **nearest-rank P95 of in-process warm service-call latency**, in milliseconds. It verifies each returned Item belongs to the requesting owner and is not soft-deleted; validates evidence IDs against the live matching DerivedContent/CaptureEvent rows; checks that Source.metadata alone does not become evidence. No third-party websites, AI embeddings, credentials, Drive, or personal data.

The live result is only valid if `status=MEASURED_SYNTHETIC_PG`, `latency_count=86` and `fixture_transaction=ROLLBACK`; otherwise P95 and service recall/precision are **NOT_RUN**, not zero or PASS. In a full CI pipeline, G00 can call this runner as a separate test job with a disposable PostgreSQL DB. Baseline PR58 frontend-unit failure means an independent successful P16 evaluation would not certify whole-app CI.

## Known constraints / reporting

1. The fixture is deliberately small, author-generated and may not predict performance on 10,000 videos; EXPLAIN/ANALYZE and 10k+ scale are **NOT_RUN** until populated in an isolated DB.
2. Source metadata can supply unsupported claims; only authenticated matching `derived_content_id` / `capture_event_id` and stored Item text count as search evidence. A source locator alone is insufficient to assert a verified PDF passage or citation.
3. `RelatedItem` semantic relationships are currently *not* part of `SearchService.search`; semantic challenge cases quantify that gap without suggesting embeddings by default.
4. `CaptureEvent` search is constrained to recent 1,000 link annotations; a full-history recall claim is unsupported.
5. `Item` has independent UUIDs even when titles are duplicates; both may be relevant.
6. Because fixture queries may have ambiguous relevance, independent human review of gold is required before treating this as an acceptance gate.
7. **INTEGRATION_REQUIRED:** G00 wires the optional job into disposable Postgres CI, reviews failures and decides any SearchService/index patch on a separate, authorized task.

Rollback of this PR: remove `evals/parallel/p16-search/`, `tools/search/p16_eval.py` and the P16 checkpoint. No migrations or application behavior changed.
