import test from 'node:test';
import assert from 'node:assert/strict';
import {CASES, makeReport, record, findCase} from './p08_report.mjs';
import {attachMediaProof} from './p08_attach_media.mjs';
function fixture(){
  const p08=makeReport({codeSha:'a'.repeat(40)});
  p08.qa_db_name='kt_p08_journeys';
  for(const {id} of CASES) record(p08,id,id==='J3'||id==='J6B'?'NOT_RUN':'PASS','synthetic',id==='J6B'?{reason:'PINNED_MEDIA_FIXTURES_ABSENT'}:{});
  const proof={
    task:'P08/J6B',status:'PASS_NATIVE_MP4_SUBPROOF_ONLY',
    mime:'video/mp4',bytes:12345,content_sha256:'b'.repeat(64),
    samples:[.125,1.25,3.5,6.25,8.75,10.5].map(x=>({target:x,actual:x+.1,seeked:true})),
    sample_count:6,max_error_seconds:.1,
    seeked_events_observed:true,cookie_authentication:true,http_range_206:true,
    anonymous_blocked:true,invalid_range_416:true,stale_path_404:true,
    pdf_exact_page:'NOT_RUN',app_django_endpoint:'NOT_RUN',
    actual_drive:'NOT_RUN',j6b_full_gate:'NOT_RUN',browser:'HeadlessChrome/145.0',
  };
  return {p08,proof};
}
test('Valid native seek proof preserves 11/13 ledger with J6B NOT_RUN',()=>{
  const {p08,proof}=fixture();
  const before=p08.journeys.map(x=>({...x}));
  const result=attachMediaProof(p08,proof);
  assert.equal(findCase(result,'J6B').status,'NOT_RUN');
  assert.equal(result.j6b_partial_media.actual_seek_events,6);
  assert.deepEqual(result.journeys,before);
  assert.equal(result.metrics.counts.PASS,11);
});
test('Reject fake browser, missing seeked events, media payload or PDF PASS claims',()=>{
  let f=fixture(); f.proof.browser='fake'; assert.throws(()=>attachMediaProof(f.p08,f.proof));
  f=fixture(); f.proof.samples[0].seeked=false; assert.throws(()=>attachMediaProof(f.p08,f.proof));
  f=fixture(); f.proof.max_error_seconds=4; assert.throws(()=>attachMediaProof(f.p08,f.proof));
  f=fixture(); f.proof.pdf_exact_page='PASS'; assert.throws(()=>attachMediaProof(f.p08,f.proof));
});
test('Previously failed or blocked J6B must not be overwritten',()=>{
  const f=fixture(); record(f.p08,'J6B','FAIL','native failure');
  assert.throws(()=>attachMediaProof(f.p08,f.proof));
});
