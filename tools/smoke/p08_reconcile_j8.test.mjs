import test from 'node:test';
import assert from 'node:assert/strict';
import { CASES, makeReport, record, findCase } from './p08_report.mjs';
import { reconcileJ8 } from './p08_reconcile_j8.mjs';

const hash = 'a'.repeat(64);
const sha = 'b'.repeat(40);
function fixture() {
  const p08 = makeReport({ codeSha: sha, baseSha: sha });
  p08.qa_db_name = 'kt_p08_journeys';
  for (const { id } of CASES) record(p08, id, id === 'J8' ? 'NOT_RUN' : 'PASS',
    id === 'J8' ? 'Browser partial checked' : 'synthetic pass',
    id === 'J8' ? { reason: 'CLEAN_DATABASE_IMPORT_AND_RELATIONS_ROUNDTRIP_NOT_RUN' } : {});
  p08.j8_partial = { original_markdown_unchanged: true,
    preview_counts: { conflict: 0 }, synthetic_items: 2, exported_zip_bytes: 2791 };
  const counts = { items: 2, topics: 2, item_topics: 3, events: 2, assets: 1, sources: 1 };
  const source = { status: 'PASS', source_database: 'kt_p08_journeys',
    browser_seeded_items: 2, synthetic_metadata_only: true,
    external_drive_calls: 0, external_ai_calls: 0, archive_sha256: hash, counts };
  const target = { status: 'PASS', task: 'P08/J8', source_database: source.source_database,
    target_database: 'kt_p08_vault_clean', archive_sha256: hash, counts,
    created: 2, events_created: 2, assets_created: 1, replay_unchanged: true,
    note_sha256_verified: true, uuid_parent_verified: true,
    folder_hierarchy_verified: true, home_shortcut_verified: true,
    source_identity_verified: true, capture_time_verified: true,
    asset_metadata_sha256_verified: true, media_verified: 0,
    metadata_only: true, external_drive_calls: 0, external_ai_calls: 0 };
  return { p08, source, target };
}
test('Only J8 is promoted with actual independent clean PostgreSQL evidence', () => {
  const { p08, source, target } = fixture();
  record(p08, 'J9', 'NOT_RUN', 'Not seeded', { reason: 'SCALE_TEST_REQUIRED' });
  const before = p08.journeys.map(x => ({ ...x }));
  const next = reconcileJ8(p08, source, target);
  assert.equal(findCase(next, 'J8').status, 'PASS');
  assert.equal(findCase(next, 'J9').status, 'NOT_RUN');
  assert.equal(next.status, 'NOT_RUN');
  assert.deepEqual(next.journeys.filter(x => x.id !== 'J8'),
    before.filter(x => x.id !== 'J8'));
  assert.equal(next.j8_clean_database.actual_media_and_drive, 'NOT_RUN');
});
test('Missing browser evidence, mismatched archive digest, unsupported media PASS fail closed', () => {
  let f = fixture(); delete f.p08.j8_partial;
  assert.throws(() => reconcileJ8(f.p08, f.source, f.target));
  f = fixture(); f.target.archive_sha256 = 'c'.repeat(64);
  assert.throws(() => reconcileJ8(f.p08, f.source, f.target));
  f = fixture(); f.target.media_verified = 1;
  assert.throws(() => reconcileJ8(f.p08, f.source, f.target));
});
test('Never replace a previously failed J8 or declare clean import without replay', () => {
  let f = fixture(); record(f.p08, 'J8', 'FAIL', 'Browser failed');
  assert.throws(() => reconcileJ8(f.p08, f.source, f.target));
  f = fixture(); f.target.replay_unchanged = false;
  assert.throws(() => reconcileJ8(f.p08, f.source, f.target));
});
