/** Promote only J6B when a real authenticated Django/React browser exercised
 * both synthetic verified binary fixtures, native PDF rendered page, MP4 seek,
 * private HTTP range, session isolation and version pinning. No Drive claims.
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { findCase, record, saveReport } from './p08_report.mjs';

export function reconcileJ6B(p08, result) {
  assert.equal(p08.qa_db_name, 'kt_p08_journeys');
  assert.match(p08.tested_sha || '', /^[a-f0-9]{40}$/);
  const entry = findCase(p08,'J6B');
  assert.equal(entry.status, 'NOT_RUN', 'Never override a previously executed verdict');
  assert.equal(entry.reason, 'PINNED_MEDIA_FIXTURES_ABSENT');
  assert.equal(result?.task, 'P08/J6B');
  assert.equal(result?.status, 'PASS_SYNTHETIC_PRIVATE_FULL_UI');
  assert.equal(result?.scope, 'ISOLATED_APP_UI_PRIVATE_DJANGO_API');
  assert.equal(result?.synthetic_byte_adapter, true);
  assert.equal(result?.actual_drive, 'NOT_RUN');
  assert.equal(result?.native_android, 'NOT_RUN');
  assert.equal(result?.auth_api, true);
  assert.equal(result?.backend_sha256_verified, true);
  assert.equal(result?.real_browser_ui, true);
  assert.equal(result?.pdf_displayed_page_verified, true);
  assert.equal(result?.mp4_ui_seek_verified, true);
  assert.ok(result?.pdf_color_pixels?.ratio >= .035);
  assert.ok(result.pdf_color_pixels.green > 10*result.pdf_color_pixels.red);
  assert.ok(result.pdf_color_pixels.green > 10*result.pdf_color_pixels.blue);
  assert.ok(Math.abs(result?.mp4_ui_seek?.currentTime-2.5) <= .25);
  assert.equal(result.mp4_ui_seek.width,320);
  assert.equal(result.mp4_ui_seek.height,180);
  assert.ok(result.checks.includes('real Django authenticated session'));
  assert.ok(result.checks.includes('pdf 206 range and stale sha fail-closed'));
  assert.ok(result.checks.includes('mp4 206 range and stale sha fail-closed'));
  record(p08,'J6B','PASS',
    'Actual React/Chromium + authenticated Django API and version-pinned synthetic PDF/MP4; green page 2 rendered; native video seeks to 2.5s; 206/401/409 verified; real Drive/Android not covered',
    {evidence:['p08-j6b-private/result.json','p08-j6b-private/private-pdf-page2.png']});
  p08.j6b_private = {
    scope:'SYNTHETIC_PINNED_BINARY_REAL_APP', pdf_page:2,
    rendered_pixel_ratio:result.pdf_color_pixels.ratio,
    video_actual_seconds:result.mp4_ui_seek.currentTime,
    real_google_drive:'NOT_RUN', native_android:'NOT_RUN',
  };
  return p08;
}
const direct=process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url);
if(direct){
  const [reportPath,proofPath]=process.argv.slice(2);
  if(!reportPath||!proofPath){console.error('Usage: p08_reconcile_j6b.mjs <p08.json> <private.json>');process.exitCode=2;}
  else{
    try{
      const p08=JSON.parse(readFileSync(reportPath,'utf8'));
      const proof=JSON.parse(readFileSync(proofPath,'utf8'));
      const report=reconcileJ6B(p08,proof);
      saveReport(report,reportPath);
      console.log(JSON.stringify({task:'P08/J6B',status:'PASS_SYNTHETIC_QA',
        counts:report.metrics.counts,release_scope:'G2 isolated synthetic only'}));
    }catch(err){console.error('J6B_FAIL_CLOSED',String(err?.message||err).slice(0,200));process.exitCode=2;}
  }
}
