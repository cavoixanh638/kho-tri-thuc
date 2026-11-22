/** Reconcile real built-App J6B proof without claiming production Drive UAT. */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { findCase, record, saveReport } from './p08_report.mjs';

export function reconcileJ6B(report, fixture, proof) {
  assert.equal(report?.qa_db_name,'kt_p08_journeys');
  assert.match(report?.tested_sha||'',/^[a-f0-9]{40}$/);
  const old=findCase(report,'J6B');
  assert.equal(old.status,'NOT_RUN');
  assert.equal(old.reason,'PINNED_MEDIA_FIXTURES_ABSENT');
  assert.equal(fixture?.status,'prepared');
  assert.equal(fixture?.no_external_provider,true);
  assert.equal(fixture?.pdf_pages,3);
  assert.equal(proof?.status,'PASS_SYNTHETIC_PRIVATE_END_TO_END');
  assert.equal(proof?.scope,'REAL_APP_DJANGO_ISOLATED_SYNTHETIC_STORAGE');
  assert.equal(proof?.synthetic_only,true);
  assert.equal(proof?.external_calls,0);
  assert.equal(proof?.provider_drive,'NOT_RUN');
  assert.equal(proof?.native_android,'NOT_RUN');
  assert.equal(proof?.pdf?.state,'AVAILABLE');
  assert.equal(proof?.pdf?.page,2);
  assert.equal(proof?.pdf?.source_sha256,fixture.items.pdf.sha256);
  assert.ok(proof?.pdf?.width>200&&proof?.pdf?.height>200);
  assert.deepEqual(proof?.pdf?.color.length,3);
  assert.ok(proof.pdf.color[1]>230&&proof.pdf.color[0]<30&&proof.pdf.color[2]<30);
  assert.equal(proof?.pdf?.alt,'Nội dung trang PDF số 2');
  assert.equal(proof?.mp4?.state,'AVAILABLE');
  assert.equal(proof?.mp4?.source_sha256,fixture.items.mp4.sha256);
  assert.equal(proof?.mp4?.target_seconds,2.5);
  assert.ok(Math.abs(proof?.mp4?.currentTime-2.5)<=0.3);
  assert.equal(proof?.mp4?.width,320);
  assert.equal(proof?.mp4?.height,180);
  assert.equal(proof?.mp4?.range?.status,206);
  assert.equal(proof?.mp4?.range?.bytes,256);
  assert.equal(proof?.mp4?.range?.range,'bytes 0-255/'+fixture.items.mp4.size);
  assert.equal(proof?.mp4?.range?.cache,'private, no-store');
  assert.equal(proof?.note_preserved,true);
  assert.equal(proof?.foreign_owner_rejected,true);
  assert.equal(proof?.pdf?.source_sha256.length,64);
  record(report,'J6B','PASS',
    'Real React UI -> session-authenticated Django -> synthetic StoragePort: PDFium exact page 2 decoded GREEN pixels, pinned SHA; native MP4 seek 2.5s with 206 Range, wrong owner 404; no Drive traffic',
    {evidence:['p08-j6b-private/results.json','p08-j6b-private/pdf-page2.png','p08-j6b-private/video-seek2_5.png']});
  report.j6b_private={
    status:'PASS_QA_SYNTHETIC_END_TO_END',
    pdf_page:2,pdf_color:proof.pdf.color,mp4_time:proof.mp4.currentTime,
    mp4_target:2.5,error_seconds:proof.mp4.error_seconds,
    source_version_pinned:true,auth_and_owner_verified:true,
    original_notes_unchanged:true,production_drive:'NOT_RUN',
    android_native:'NOT_RUN',
  };
  return report;
}
const executable=process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url);
if(executable) {
  const [reportPath,fixturePath,proofPath]=process.argv.slice(2);
  if(!reportPath||!fixturePath||!proofPath){console.error('Usage: p08_reconcile_j6b.mjs <p08.json> <fixture.json> <proof.json>');process.exitCode=2;}
  else try {
    const report=JSON.parse(readFileSync(reportPath,'utf8'));
    const fixture=JSON.parse(readFileSync(fixturePath,'utf8'));
    const proof=JSON.parse(readFileSync(proofPath,'utf8'));
    const result=reconcileJ6B(report,fixture,proof);
    saveReport(result,reportPath);
    console.log(JSON.stringify({result:'P08_J6B_PRIVATE_QA_PASS',
      counts:result.metrics.counts,status:result.status,j6b:result.j6b_private}));
  } catch(err){
    console.error('P08_J6B_RECONCILIATION_FAILED',String(err?.message||err).slice(0,170));process.exitCode=2;
  }
}
