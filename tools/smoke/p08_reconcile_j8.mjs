#!/usr/bin/env node
/**
 * Reconcile P08/J8 from a real Chromium export/preview plus a separately
 * migrated clean PostgreSQL import, without turning any other NOT_RUN to PASS.
 */
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { record, saveReport, findCase } from './p08_report.mjs';

export function reconcileJ8(p08, source, target) {
  assert.equal(p08?.qa_db_name, 'kt_p08_journeys');
  assert.ok(/^[a-f0-9]{40}$/.test(p08.tested_sha || ''), 'Test SHA required');
  assert.ok(p08.j8_partial?.original_markdown_unchanged === true,
    'Browser ZIP export/preview and authored-note preservation must have been exercised');
  assert.equal(p08.j8_partial.preview_counts?.conflict, 0);
  assert.ok(p08.j8_partial.exported_zip_bytes > 100);
  assert.ok(p08.j8_partial.synthetic_items >= 2);
  assert.equal(findCase(p08, 'J8').status, 'NOT_RUN', 'Do not overwrite a real previous verdict');
  assert.equal(findCase(p08, 'J8').reason, 'CLEAN_DATABASE_IMPORT_AND_RELATIONS_ROUNDTRIP_NOT_RUN');

  assert.equal(source?.status, 'PASS');
  assert.equal(source.source_database, 'kt_p08_journeys');
  assert.equal(source.browser_seeded_items, p08.j8_partial.synthetic_items);
  assert.equal(source.synthetic_metadata_only, true);
  assert.equal(source.external_drive_calls, 0);
  assert.equal(source.external_ai_calls, 0);
  assert.equal(target?.status, 'PASS');
  assert.equal(target.task, 'P08/J8');
  assert.equal(target.source_database, source.source_database);
  assert.equal(target.target_database, 'kt_p08_vault_clean');
  assert.match(source.archive_sha256 || '', /^[a-f0-9]{64}$/);
  assert.equal(target.archive_sha256, source.archive_sha256);
  assert.deepEqual(target.counts, source.counts);
  assert.equal(target.counts.items, source.browser_seeded_items);
  assert.ok(target.counts.item_topics >= 3 && target.counts.events >= 1
    && target.counts.sources >= 1 && target.counts.assets >= 1);
  assert.equal(target.created, target.counts.items);
  assert.equal(target.events_created, target.counts.events);
  assert.equal(target.assets_created, target.counts.assets);
  assert.equal(target.replay_unchanged, true);
  for (const key of [
    'note_sha256_verified', 'uuid_parent_verified', 'folder_hierarchy_verified',
    'home_shortcut_verified', 'source_identity_verified', 'capture_time_verified',
    'asset_metadata_sha256_verified',
  ]) assert.equal(target[key], true, key);
  assert.equal(target.media_verified, 0);
  assert.equal(target.metadata_only, true);
  assert.equal(target.external_drive_calls, 0);
  assert.equal(target.external_ai_calls, 0);

  record(p08, 'J8', 'PASS',
    'Browser ZIP export+preview and independent clean PostgreSQL import: UUID, Markdown hashes, hierarchy, shortcut, source/event/asset metadata and retry preserved (no media bytes)',
    { evidence: ['p08-j8-clean-result.json', 'p08-j8-source.json'] });
  p08.j8_clean_database = {
    archive_sha256: target.archive_sha256,
    database: 'kt_p08_vault_clean', counts: target.counts,
    metadata_only: true, actual_media_and_drive: 'NOT_RUN',
  };
  return p08;
}

const executable = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (executable) {
  const [reportPath, sourcePath, targetPath] = process.argv.slice(2);
  if (!reportPath || !sourcePath || !targetPath) {
    console.error('Usage: p08_reconcile_j8.mjs <p08-results.json> <source.json> <result.json>');
    process.exitCode = 2;
  } else {
    try {
      const p08 = JSON.parse(readFileSync(reportPath, 'utf8'));
      const source = JSON.parse(readFileSync(sourcePath, 'utf8'));
      const target = JSON.parse(readFileSync(targetPath, 'utf8'));
      const result = reconcileJ8(p08, source, target);
      saveReport(result, reportPath);
      console.log(JSON.stringify({ status: 'P08_J8_CLEAN_DB_PASS',
        sha: result.tested_sha, report_status: result.status, metrics: result.metrics }));
    } catch (error) {
      console.error('P08_J8_RECONCILIATION_FAILED', String(error.message || error).slice(0, 140));
      process.exitCode = 2;
    }
  }
}
