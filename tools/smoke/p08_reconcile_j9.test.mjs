import test from 'node:test';
import assert from 'node:assert/strict';
import { CASES, makeReport, record, findCase } from './p08_report.mjs';
import { reconcileJ9 } from './p08_reconcile_j9.mjs';

function fixtures() {
  const p08 = makeReport({codeSha: 'a'.repeat(40), baseSha:'a'.repeat(40)});
  p08.qa_db_name = 'kt_p08_journeys';
  for (const {id} of CASES) {
    record(p08, id, id === 'J9' || id === 'J3' || id === 'J6B' ? 'NOT_RUN' : 'PASS',
      'synthetic test',
      id === 'J9' ? {reason:'SCALE_RESTORE_SEPARATE_ISOLATED_DB_REQUIRED'}
        : id === 'J3' || id === 'J6B' ? {reason:'EXTERNAL_PROVIDER_REQUIRED'} : {});
  }
  const source={
    task:'P08/J9',stage:'source',status:'PASS',
    source_database:'kt_p08_scale',restore_database:'kt_p08_scale_restored',
    synthetic_only:true,external_calls:0,
    counts:{items:10000,topics:1000,memberships:10000,
      events:2,sources:1,jobs:1,foreign_items:1},
    tree_nodes_verified:1000,rest_pages_verified:100,rest_page_size:100,
    rest_unique_item_ids:10000,first_page_stable:true,explorer_mixed_pagination:true,
    search_queries_verified:10,search_owner_isolated:true,retry_same_key_same_event:true,
    retry_new_send_adds_one_event:true,retry_no_duplicate_source_job:true,
    page_http_p95_ms:10.3,search_service_p95_ms:15.2,
    fingerprint_sha256:'b'.repeat(64),
  };
  const restored={
    task:'P08/J9',stage:'restored',status:'PASS',
    source_database:source.source_database,restore_database:source.restore_database,
    counts:source.counts,fingerprint_sha256:source.fingerprint_sha256,
    post_restore_digest_equal:true,post_restore_same_key_no_new_event:true,
    backup_sha256:'c'.repeat(64),backup_checksum_verified:true,
    postgres_custom_restore:true,synthetic_only:true,external_calls:0,
    media_drive_verified:false,
  };
  return {p08,source,restored};
}

test('Promote J9 only, preserve remaining public/media test omissions',()=>{
  const f=fixtures();
  const old = f.p08.journeys.filter(j=>j.id!=='J9').map(x=>({...x}));
  const result = reconcileJ9(f.p08,f.source,f.restored);
  assert.equal(findCase(result,'J9').status,'PASS');
  assert.equal(findCase(result,'J3').status,'NOT_RUN');
  assert.equal(findCase(result,'J6B').status,'NOT_RUN');
  assert.equal(result.metrics.counts.PASS,11);
  assert.equal(result.status,'NOT_RUN');
  assert.deepEqual(result.journeys.filter(j=>j.id!=='J9'), old);
  assert.equal(result.j9_scale.real_100gb_media_test,'NOT_RUN');
});

test('Missing 10k unique pages, 1k nodes or replay proof never grants PASS',()=>{
  let f=fixtures();f.source.rest_unique_item_ids=9999;
  assert.throws(()=>reconcileJ9(f.p08,f.source,f.restored));
  f=fixtures();f.source.counts.topics=999;
  assert.throws(()=>reconcileJ9(f.p08,f.source,f.restored));
  f=fixtures();f.restored.post_restore_same_key_no_new_event=false;
  assert.throws(()=>reconcileJ9(f.p08,f.source,f.restored));
});

test('Fingerprint mismatch, fake provider verification and failed backup fail closed',()=>{
  let f=fixtures();f.restored.fingerprint_sha256='e'.repeat(64);
  assert.throws(()=>reconcileJ9(f.p08,f.source,f.restored));
  f=fixtures();f.restored.media_drive_verified=true;
  assert.throws(()=>reconcileJ9(f.p08,f.source,f.restored));
  f=fixtures();f.restored.backup_checksum_verified=false;
  assert.throws(()=>reconcileJ9(f.p08,f.source,f.restored));
});

test('Do not overwrite FAIL; require real counted browser report',()=>{
  let f=fixtures();record(f.p08,'J9','FAIL','previous assert failed');
  assert.throws(()=>reconcileJ9(f.p08,f.source,f.restored));
  f=fixtures();delete f.p08.tested_sha;
  assert.throws(()=>reconcileJ9(f.p08,f.source,f.restored));
});
