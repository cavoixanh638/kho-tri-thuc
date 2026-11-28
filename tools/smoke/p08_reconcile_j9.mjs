#!/usr/bin/env node
/**
 * Promote only P08/J9 when independent PostgreSQL 10k/1k seed, real REST
 * pagination, FTS, idempotency and checked custom-format backup restore agree.
 * Never interpret 10k synthetic notes as 10k real videos or 100GB media.
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { findCase, record, saveReport } from './p08_report.mjs';

export function reconcileJ9(p08, source, restored) {
  assert.equal(p08?.qa_db_name, 'kt_p08_journeys');
  assert.match(p08?.tested_sha || '', /^[a-f0-9]{40}$/);
  assert.equal(findCase(p08, 'J9').status, 'NOT_RUN');
  assert.equal(findCase(p08, 'J9').reason, 'SCALE_RESTORE_SEPARATE_ISOLATED_DB_REQUIRED');

  assert.equal(source?.task, 'P08/J9');
  assert.equal(source?.stage, 'source');
  assert.equal(source?.status, 'PASS');
  assert.equal(source?.source_database, 'kt_p08_scale');
  assert.equal(source?.restore_database, 'kt_p08_scale_restored');
  assert.equal(source?.synthetic_only, true);
  assert.equal(source?.external_calls, 0);
  assert.deepEqual(source?.counts, {
    items: 10000, topics: 1000, memberships: 10000,
    events: 2, sources: 1, jobs: 1, foreign_items: 1,
  });
  assert.equal(source.tree_nodes_verified, 1000);
  assert.equal(source.rest_pages_verified, 100);
  assert.equal(source.rest_page_size, 100);
  assert.equal(source.rest_unique_item_ids, 10000);
  assert.equal(source.first_page_stable, true);
  assert.equal(source.explorer_mixed_pagination, true);
  assert.equal(source.search_queries_verified, 10);
  assert.equal(source.search_owner_isolated, true);
  assert.equal(source.retry_same_key_same_event, true);
  assert.equal(source.retry_new_send_adds_one_event, true);
  assert.equal(source.retry_no_duplicate_source_job, true);
  assert.ok(Number.isFinite(source.page_http_p95_ms));
  assert.ok(Number.isFinite(source.search_service_p95_ms));
  assert.match(source.fingerprint_sha256 || '', /^[a-f0-9]{64}$/);

  assert.equal(restored?.task, 'P08/J9');
  assert.equal(restored?.stage, 'restored');
  assert.equal(restored?.status, 'PASS');
  assert.equal(restored?.source_database, source.source_database);
  assert.equal(restored?.restore_database, source.restore_database);
  assert.deepEqual(restored?.counts, source.counts);
  assert.equal(restored?.fingerprint_sha256, source.fingerprint_sha256);
  assert.equal(restored?.post_restore_digest_equal, true);
  assert.equal(restored?.post_restore_same_key_no_new_event, true);
  assert.match(restored?.backup_sha256 || '', /^[a-f0-9]{64}$/);
  assert.equal(restored?.backup_checksum_verified, true);
  assert.equal(restored?.postgres_custom_restore, true);
  assert.equal(restored?.synthetic_only, true);
  assert.equal(restored?.external_calls, 0);
  assert.equal(restored?.media_drive_verified, false);

  record(p08, 'J9', 'PASS',
    '10k synthetic Items / 1k folders: all 100 authenticated REST pages unique, '
      + '10 exact-token SearchService queries, tree/explorer, PostgreSQL dump '
      + 'SHA256 + clean restore identity digest, same-key retry no duplicate',
    { evidence: ['p08-j9-source.json', 'p08-j9-restored.json'] });
  p08.j9_scale = {
    status: 'PASS_SYNTHETIC_PG', items: 10000, topics: 1000,
    pages: 100, unique_items: source.rest_unique_item_ids,
    search_examples: source.search_queries_verified,
    page_http_p95_ms: source.page_http_p95_ms,
    search_service_p95_ms: source.search_service_p95_ms,
    backup_sha256: restored.backup_sha256,
    before_after_rows_sha256: source.fingerprint_sha256,
    has_real_media_or_drive: false, real_100gb_media_test: 'NOT_RUN',
  };
  return p08;
}

const executable = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (executable) {
  const [p08Path, sourcePath, restoredPath] = process.argv.slice(2);
  if (!p08Path || !sourcePath || !restoredPath) {
    console.error('Usage: p08_reconcile_j9.mjs <p08-results.json> <source.json> <restored.json>');
    process.exitCode = 2;
  } else {
    try {
      const p08 = JSON.parse(readFileSync(p08Path, 'utf8'));
      const source = JSON.parse(readFileSync(sourcePath, 'utf8'));
      const restored = JSON.parse(readFileSync(restoredPath, 'utf8'));
      const result = reconcileJ9(p08, source, restored);
      saveReport(result, p08Path);
      console.log(JSON.stringify({ result: 'P08_J9_SYNTHETIC_10K_PG_PASS',
        tested_sha: result.tested_sha, counts: result.metrics.counts,
        release_status: result.status, j9: result.j9_scale }));
    } catch (error) {
      console.error('P08_J9_RECONCILIATION_FAILED', String(error?.message || error).slice(0, 180));
      process.exitCode = 2;
    }
  }
}
