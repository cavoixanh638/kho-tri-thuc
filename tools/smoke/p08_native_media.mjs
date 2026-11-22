#!/usr/bin/env node
/** P08/J6B sub-proof: actual Chromium MP4 seek over private loopback 206 Range.
 * No Drive/AI, no production, no PDF-page PASS, no release-gate promotion.
 */
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash, randomBytes } from 'node:crypto';
import { readFileSync, writeFileSync, mkdtempSync, mkdirSync, rmSync } from 'node:fs';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { Browser } from './p08_cdp.mjs';

assert.equal(process.env.P08_NATIVE_MEDIA_ISOLATED, 'YES', 'isolated-only');
assert.ok(process.env.KT_JOURNEY_CHROMIUM, 'Chrome path required');
const out = resolve(process.env.KT_JOURNEY_OUT || 'tmp/p08-kt128');
mkdirSync(out, {recursive: true});
const temporary = mkdtempSync(join(tmpdir(), 'p08-j6b-media-'));
const cookie = randomBytes(20).toString('hex');
const hash = data => createHash('sha256').update(data).digest('hex');
let server, browser;
const requests = [];
try {
  const importedFixture = process.env.P08_NATIVE_MEDIA_FILE;
  const output = importedFixture ? resolve(importedFixture) : join(temporary, 'synthetic.mp4');
  if (importedFixture) {
    assert.equal(process.env.P08_NATIVE_MEDIA_GENERATED, 'YES');
    assert.ok(output.startsWith(out + '/p08-native-'), 'only the QA-generated fixture file is accepted');
  } else {
    execFileSync('ffmpeg', [
      '-hide_banner', '-loglevel', 'error', '-nostdin', '-f', 'lavfi',
      '-i', 'testsrc2=size=320x180:rate=10', '-t', '12', '-an',
      '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p',
      '-movflags', '+faststart', '-y', output,
    ], {timeout: 60000});
  }
  const body = readFileSync(output);
  assert.equal(body.toString('ascii', 4, 8), 'ftyp', 'MP4 binary');
  const sha256 = hash(body);
  const assetId = '22222222-2222-4222-8222-222222222222';
  const url = '/api/v1/assets/' + assetId + '/content/1/' + sha256;
  const maxRange = 4 * 1024 * 1024;
  const etag = '"' + assetId + ':1:' + sha256 + '"';
  server = createServer((req, res) => {
    res.setHeader('Cache-Control', 'private, no-store');
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Referrer-Policy', 'no-referrer');
    res.setHeader('Cross-Origin-Resource-Policy', 'same-origin');
    res.setHeader('Accept-Ranges', 'bytes');
    if (req.url === '/' && req.method === 'GET') {
      res.setHeader('Set-Cookie', 'p08_fixture=' + cookie + '; HttpOnly; SameSite=Strict; Path=/');
      res.writeHead(200, {'Content-Type': 'text/html; charset=utf-8'});
      res.end('<!doctype html><html><head><meta charset="utf-8"><title>Private native media QA</title></head><body><h1>P08 J6B generated MP4</h1><video id="source" controls preload="auto"></video></body></html>');
      return;
    }
    if (req.url !== url || !['GET','HEAD'].includes(req.method)) {
      res.writeHead(404); res.end(); return;
    }
    if (req.headers.cookie !== 'p08_fixture=' + cookie) {
      res.writeHead(401); res.end(); return;
    }
    if ((req.headers['if-match'] && ![etag,'*'].includes(req.headers['if-match']))
        || (req.headers['if-range'] && req.headers['if-range'] !== etag)) {
      res.writeHead(412); res.end(); return;
    }
    const range = req.headers.range;
    let start = 0, end = body.length - 1, partial = false;
    if (range != null) {
      const match = /^bytes=(\d{0,20})-(\d{0,20})$/.exec(range);
      if (!match || (!match[1] && !match[2])) {
        res.writeHead(416, {'Content-Range': 'bytes */' + body.length}); res.end(); return;
      }
      partial = true;
      if (match[1]) {
        start = Number(match[1]);
        end = match[2] ? Math.min(Number(match[2]), body.length - 1) : Math.min(body.length - 1, start + maxRange - 1);
      } else {
        const suffix = Number(match[2]);
        start = Math.max(0, body.length - suffix);
        if (!suffix) start = body.length;
      }
    }
    if (start >= body.length || end < start || end - start + 1 > maxRange) {
      res.writeHead(416, {'Content-Range': 'bytes */' + body.length}); res.end(); return;
    }
    requests.push({status: partial ? 206 : 200, from: start, to: end});
    res.writeHead(partial ? 206 : 200, {
      'Content-Type': 'video/mp4',
      'Content-Length': String(req.method === 'HEAD' && !range ? body.length : end - start + 1),
      ETag: etag,
      ...(partial ? {'Content-Range': 'bytes ' + start + '-' + end + '/' + body.length} : {}),
    });
    res.end(req.method === 'HEAD' ? undefined : body.subarray(start, end + 1));
  });
  await new Promise((ok, fail) => {server.once('error', fail); server.listen(0, '127.0.0.1', ok);});
  const origin = 'http://127.0.0.1:' + server.address().port;
  assert.equal((await fetch(origin + url, {redirect: 'manual'})).status, 401, 'anonymous denied');
  browser = await Browser.launch({extraArgs: ['--mute-audio','--autoplay-policy=no-user-gesture-required']});
  const browserVersion = (await browser.cdp.send('Browser.getVersion')).product;
  const page = await browser.newPage({width: 1440, height: 900, reducedMotion: true});
  await page.goto(origin + '/');
  const probe = await page.eval(async ({url, length}) => {
    const response = await fetch(url, {headers: {Range: 'bytes=0-31'}, credentials: 'same-origin'});
    return {status: response.status, content_range: response.headers.get('Content-Range'),
      size: (await response.arrayBuffer()).byteLength, expected: 'bytes 0-31/' + length};
  }, {url, length: body.length});
  assert.equal(probe.status, 206);
  assert.equal(probe.content_range, probe.expected);
  assert.equal(probe.size, 32);
  const denied = await page.eval(async url => {
    const stale = await fetch(url + '?stale=1', {credentials: 'same-origin'});
    return stale.status;
  }, url);
  assert.equal(denied, 404, 'stale path not served');
  const invalid = await page.eval(async ({url, length}) => {
    const r = await fetch(url, {headers: {Range: 'bytes=' + length + '-'}, credentials: 'same-origin'});
    return r.status;
  }, {url, length: body.length});
  assert.equal(invalid, 416);

  const media = await page.eval(async url => {
    const el = document.querySelector('video');
    el.src = url; el.load();
    const start = performance.now();
    while (performance.now() - start < 15000) {
      if (Number.isFinite(el.duration) && el.duration > 0 && el.seekable.length && el.readyState >= 2)
        return {duration: el.duration, videoWidth: el.videoWidth, videoHeight: el.videoHeight};
      if (el.error) throw Error('HTMLMediaElement decode ' + el.error.code);
      await new Promise(resolve => setTimeout(resolve, 25));
    }
    throw Error('native media load timeout');
  }, url);
  assert.ok(media.duration >= 11.5 && media.duration <= 12.5);
  assert.equal(media.videoWidth, 320);
  assert.equal(media.videoHeight, 180);
  const marks = [0.125, 1.25, 3.5, 6.25, 8.75, 10.5];
  const results = [];
  for (const mark of marks) {
    const result = await page.eval(async seconds => {
      const video = document.querySelector('video');
      if (!video.seekable.length || seconds > video.duration) throw Error('not seekable');
      let observed = false;
      const handler = () => { observed = true; };
      video.addEventListener('seeked', handler);
      const start = performance.now();
      try {
        video.pause();
        video.currentTime = seconds;
        while (performance.now() - start < 12000) {
          if (video.error) throw Error('decode failed');
          if (observed && !video.seeking && video.readyState >= 2 && Math.abs(video.currentTime - seconds) <= 0.5)
            return {target: seconds, actual: video.currentTime, seeked: true, elapsed_ms: Math.round(performance.now() - start)};
          await new Promise(resolve => setTimeout(resolve, 20));
        }
        throw Error('native seek timeout');
      } finally { video.removeEventListener('seeked', handler); }
    }, mark);
    assert.ok(Math.abs(result.actual - mark) <= 0.5);
    results.push(result);
  }
  assert.equal(results.length, 6);
  assert.ok(requests.some(row => row.status === 206));
  await page.screenshot({path: join(out, 'p08-j6b-native-media.png')});
  const report = {
    task: 'P08/J6B', status: 'PASS_NATIVE_MP4_SUBPROOF_ONLY',
    browser: browserVersion, mime: 'video/mp4', bytes: body.length,
    content_sha256: sha256, samples: results, sample_count: results.length,
    seeked_events_observed: results.every(row => row.seeked),
    max_error_seconds: Math.max(...results.map(row => Math.abs(row.target - row.actual))),
    cookie_authentication: true, http_range_206: true,
    anonymous_blocked: true, invalid_range_416: true, stale_path_404: true,
    pdf_exact_page: 'NOT_RUN', app_django_endpoint: 'NOT_RUN',
    actual_drive: 'NOT_RUN', j6b_full_gate: 'NOT_RUN',
    limitations: 'Generated MP4 + loopback isolated 206 byte range; not the app Django/Drive endpoint nor exact PDF page verification',
  };
  writeFileSync(join(out, 'p08-j6b-native-media.json'), JSON.stringify(report, null, 2) + '\n', {mode: 0o600});
  console.log(JSON.stringify({task:report.task,status:report.status,samples:report.sample_count,
    max_error_seconds:report.max_error_seconds, pdf_exact_page:report.pdf_exact_page}));
} finally {
  try { await browser?.close(); } catch {}
  if (server) await new Promise(resolve => server.close(resolve));
  rmSync(temporary, {recursive: true, force: true});
}
