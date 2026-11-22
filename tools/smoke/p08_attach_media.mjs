#!/usr/bin/env node
/** Annotate only supplemental native-MP4 evidence; J6B release status stays NOT_RUN. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {findCase, saveReport} from './p08_report.mjs';

export function attachMediaProof(p08, proof) {
  assert.match(p08?.tested_sha || '', /^[a-f0-9]{40}$/);
  assert.equal(p08.qa_db_name, 'kt_p08_journeys');
  const j6b = findCase(p08, 'J6B');
  assert.equal(j6b.status, 'NOT_RUN', 'never overwrite J6B real end-to-end verdict');
  assert.equal(j6b.reason, 'PINNED_MEDIA_FIXTURES_ABSENT');
  assert.equal(proof.task, 'P08/J6B');
  assert.equal(proof.status, 'PASS_NATIVE_MP4_SUBPROOF_ONLY');
  assert.equal(proof.mime, 'video/mp4');
  assert.ok(proof.bytes > 1000);
  assert.match(proof.content_sha256 || '', /^[a-f0-9]{64}$/);
  assert.equal(proof.sample_count, 6);
  assert.equal(proof.samples.length, proof.sample_count);
  assert.ok(proof.samples.every(x => x.seeked === true
    && Math.abs(x.target - x.actual) <= 0.5));
  assert.ok(proof.max_error_seconds >= 0 && proof.max_error_seconds <= 0.5);
  for (const key of [
    'seeked_events_observed', 'cookie_authentication', 'http_range_206',
    'anonymous_blocked', 'invalid_range_416', 'stale_path_404',
  ]) assert.equal(proof[key], true, key);
  for (const key of ['pdf_exact_page','app_django_endpoint','actual_drive','j6b_full_gate'])
    assert.equal(proof[key], 'NOT_RUN', key);
  assert.ok(/^HeadlessChrome\/|^Chrome\//.test(proof.browser), 'actual Chromium required');

  p08.j6b_partial_media = {
    status: 'PASS_NATIVE_MP4_ONLY', generated_bytes: proof.bytes,
    sha256: proof.content_sha256, actual_seek_events: proof.sample_count,
    max_error_seconds: proof.max_error_seconds,
    authenticated_range: true, native_pdf_exact_page: 'NOT_RUN',
    real_django_private_viewer: 'NOT_RUN', real_drive: 'NOT_RUN',
  };
  assert.equal(j6b.status, 'NOT_RUN');
  return p08;
}
const executable = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (executable) {
  const [p08Path, mediaPath] = process.argv.slice(2);
  if (!p08Path || !mediaPath) { console.error('Usage: p08_attach_media.mjs <p08-results.json> <p08-j6b-native-media.json>'); process.exitCode = 2; }
  else try {
    const p08 = attachMediaProof(JSON.parse(readFileSync(p08Path, 'utf8')),
      JSON.parse(readFileSync(mediaPath, 'utf8')));
    saveReport(p08, p08Path);
    console.log(JSON.stringify({subproof:'P08_J6B_MP4_NATIVE_SEEK_PASS', j6b:findCase(p08,'J6B').status, metrics:p08.metrics.counts}));
  } catch (error) {
    console.error('P08_J6B_SUBPROOF_REJECTED', String(error?.message || error).slice(0,160));
    process.exitCode = 2;
  }
}
