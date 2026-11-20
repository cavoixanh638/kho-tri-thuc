// Isolated, generated media only. Run: node tests/kt116-browser.test.mjs
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { spawn, execFileSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { createServer } from 'vite';
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const out = path.resolve(process.env.KT116_EVIDENCE_DIR ?? '../../tmp/kt116-evidence'); mkdirSync(out, { recursive: true });
const chrome = process.env.CHROME_PATH ?? 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const profile = mkdtempSync(path.join(tmpdir(), 'kt116-browser-'));
let media, mime = 'audio/wav', browser, socket, server;
const requests = [];
function wav() {
  const rate = 8000, size = 30 * rate * 2, bytes = Buffer.alloc(44 + size);
  bytes.write('RIFF'); bytes.writeUInt32LE(36 + size, 4); bytes.write('WAVEfmt ', 8); bytes.writeUInt32LE(16, 16);
  bytes.writeUInt16LE(1, 20); bytes.writeUInt16LE(1, 22); bytes.writeUInt32LE(rate, 24); bytes.writeUInt32LE(rate * 2, 28);
  bytes.writeUInt16LE(2, 32); bytes.writeUInt16LE(16, 34); bytes.write('data', 36); bytes.writeUInt32LE(size, 40);
  for (let index = 0; index < size / 2; index++) bytes.writeInt16LE(Math.round(Math.sin(index * 2 * Math.PI * 220 / rate) * 500), 44 + index * 2);
  return bytes;
}
function webmDuration(bytes) {
  const info = bytes.indexOf(Buffer.from([0x15, 0x49, 0xa9, 0x66])); assert.ok(info >= 0, 'WebM Segment Info');
  const pos = info + 4; let length = 1, mask = 0x80;
  while (!(bytes[pos] & mask)) { length++; mask >>= 1; }
  let size = BigInt(bytes[pos] & (mask - 1)); for (let index = 1; index < length; index++) size = (size << 8n) | BigInt(bytes[pos + index]);
  const end = pos + length + Number(size);
  const duration = Buffer.alloc(11); duration.set([0x44, 0x89, 0x88]); duration.writeDoubleBE(22000, 3);
  const head = Buffer.from(bytes.subarray(0, end)); let next = size + 11n;
  for (let index = length - 1; index >= 0; index--) { head[pos + index] = Number(next & 255n); next >>= 8n; } head[pos] |= mask;
  return Buffer.concat([head, duration, bytes.subarray(end)]);
}
media = wav();
try {
  server = await createServer({ logLevel: 'silent', server: { host: '127.0.0.1', port: 0 }, plugins: [{ name: 'kt116-private-fixture', configureServer(vite) {
    vite.middlewares.use(async (req, res, next) => {
      if (req.url === '/tests/kt116-browser.html') res.setHeader('Set-Cookie', 'kt116_fixture=isolated; HttpOnly; SameSite=Strict; Path=/');
      if (req.url === '/kt116-fixture-video' && req.method === 'POST') {
        const chunks = []; for await (const chunk of req) chunks.push(chunk);
        media = webmDuration(Buffer.concat(chunks)); mime = 'video/webm'; res.writeHead(204); res.end(); return;
      }
      if (!['/api/v1/assets/fixture-a/stream', '/api/v1/assets/fixture-video/stream'].includes(req.url)) return next();
      const authenticated = req.headers.cookie?.includes('kt116_fixture=isolated');
      if (!authenticated) { res.writeHead(403); res.end(); return; }
      const range = /^bytes=(\d+)-(\d*)$/.exec(req.headers.range ?? '');
      const start = range ? Number(range[1]) : 0, end = range && range[2] ? Math.min(Number(range[2]), media.length - 1) : media.length - 1;
      if (start > end || start >= media.length) { res.writeHead(416, { 'Content-Range': `bytes */${media.length}` }); res.end(); return; }
      const status = range ? 206 : 200;
      requests.push({ mime, range: req.headers.range ?? null, authenticated: Boolean(authenticated), status });
      res.writeHead(status, { 'Content-Type': mime, 'Content-Length': end - start + 1, 'Accept-Ranges': 'bytes', 'Cache-Control': 'no-store', ...(range ? { 'Content-Range': `bytes ${start}-${end}/${media.length}` } : {}) });
      res.end(media.subarray(start, end + 1));
    });
  } }] });
  await server.listen(); const base = server.resolvedUrls.local[0].replace(/\/$/, '');
  browser = spawn(chrome, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--no-first-run', '--no-default-browser-check', '--mute-audio', '--disable-background-timer-throttling', '--autoplay-policy=no-user-gesture-required', 'about:blank'], { windowsHide: true, stdio: ['ignore', 'ignore', 'pipe'] });
  const debug = await new Promise((resolve, reject) => { let stderr = ''; const timer = setTimeout(() => reject(new Error('Chrome startup timeout')), 20000); browser.stderr.on('data', data => { stderr += data; const found = stderr.match(/DevTools listening on (ws:\/\/[^\s]+)/); if (found) { clearTimeout(timer); resolve(found[1]); } }); browser.once('error', reject); });
  socket = new WebSocket(debug); await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
  let sequence = 0; const waiting = new Map(); const errors = [];
  socket.onmessage = event => { const response = JSON.parse(event.data); if (response.id) { const pending = waiting.get(response.id); if (pending) { clearTimeout(pending.timer); waiting.delete(response.id); response.error ? pending.reject(new Error(response.error.message)) : pending.resolve(response.result); } } else if (response.method === 'Runtime.exceptionThrown') errors.push(response.params.exceptionDetails); };
  const call = (method, params = {}, sessionId) => new Promise((resolve, reject) => { const id = ++sequence; const timer = setTimeout(() => reject(new Error('CDP timeout: ' + method)), 30000); waiting.set(id, { resolve, reject, timer }); socket.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) })); });
  const { targetId } = await call('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await call('Target.attachToTarget', { targetId, flatten: true });
  await call('Page.enable', {}, sessionId); await call('Runtime.enable', {}, sessionId);
  const evaluate = async expression => { const result = await call('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }, sessionId); if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails)); return result.result?.value; };
  await call('Page.navigate', { url: base + '/tests/kt116-browser.html' }, sessionId);
  for (let tries = 0; tries < 200; tries++) { if (await evaluate('!!window.kt116?.ready')) break; await delay(100); }
  assert.equal(await evaluate('window.kt116?.ready'), true);
  const report = { scope: 'synthetic same-origin cookie-authenticated Range fixture; no Drive/provider traffic', browser: (await call('Browser.getVersion')).product, device: process.platform + ' headless desktop', tolerance_seconds: 1, audio: [], video: [], http: requests, screenshots: [], console_errors: errors, production_private_stream: 'NOT_RUN', pdf_navigation: 'NOT_RUN', android: 'NOT_RUN' };
  const marks = [0, .125, .5, 1, 1.25, 2.5, 3, 4.125, 5, 6.5, 7.75, 8, 9.5, 10.25, 11, 12.5, 14, 16.25, 18, 20];
  for (const currentMime of ['audio/wav', 'video/webm']) {
    if (currentMime.startsWith('video')) { console.log('Recording isolated VP8 fixture (22 seconds)…'); await evaluate('window.kt116.record()'); }
    const assetId = currentMime.startsWith('video') ? 'fixture-video' : 'fixture-a';
    const streamPath = `/api/v1/assets/${assetId}/stream`;
    assert.equal((await fetch(base + streamPath)).status, 403, 'unauthenticated fixture request rejected');
    const probe = await evaluate(`fetch(${JSON.stringify(streamPath)}, { headers: { Range: 'bytes=0-31' } }).then(async response => ({ status: response.status, length: (await response.arrayBuffer()).byteLength, range: response.headers.get('Content-Range') }))`);
    assert.equal(probe.status, 206); assert.equal(probe.length, 32); assert.match(probe.range, /^bytes 0-31\//);
    const version = createHash('sha256').update(media).digest('hex');
    for (const seconds of marks) {
      await evaluate(`window.kt116.render(${seconds}, ${JSON.stringify(currentMime)}, ${JSON.stringify(version)})`); await delay(50);
      await evaluate(`Array.from(document.querySelectorAll('button')).find(button => button.textContent === 'Đến vị trí nguồn').click()`);
      const actual = await evaluate(`new Promise((resolve, reject) => { const started = performance.now(); const timer = setInterval(() => { const media = document.querySelector('audio,video'); const status = document.querySelector('.source-locator-viewer [role=status]')?.textContent; if (media && status?.startsWith('Đã đến')) { clearInterval(timer); resolve({ target: ${seconds}, actual: media.currentTime, duration: media.duration, tag: media.tagName, video_width: media.videoWidth ?? null, video_height: media.videoHeight ?? null, status }); } else if (performance.now() - started > 10000) { clearInterval(timer); reject(new Error(status || 'media timeout')); } }, 25); })`);
      assert.ok(Math.abs(actual.actual - seconds) <= 1, `${currentMime}: ${seconds} -> ${actual.actual}`);
      if (currentMime.startsWith('video')) { assert.equal(actual.tag, 'VIDEO'); assert.equal(actual.video_width, 320); assert.equal(actual.video_height, 180); assert.ok(actual.duration >= 20.5 && actual.duration <= 22.5, 'recorded VP8 duration differs from 30-second WAV'); }
      else { assert.equal(actual.tag, 'AUDIO'); assert.equal(actual.duration, 30); }
      actual.codec = currentMime === 'audio/wav' ? 'PCM signed 16-bit mono 8kHz WAV' : 'VP8 WebM 320x180 canvas capture 10fps';
      actual.source_version = version;
      report[currentMime.startsWith('audio') ? 'audio' : 'video'].push(actual);
    }
  }
  for (const width of [1440, 768, 390]) {
    await call('Emulation.setDeviceMetricsOverride', { width, height: width === 390 ? 844 : 1000, deviceScaleFactor: 1, mobile: false }, sessionId);
    await delay(150);
    const dimensions = await evaluate('({ viewport: innerWidth, scroll: document.documentElement.scrollWidth })'); assert.ok(dimensions.scroll <= width, `horizontal overflow ${width}`);
    const shot = await call('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false }, sessionId);
    const filename = `kt116-${width}.png`; writeFileSync(path.join(out, filename), Buffer.from(shot.data, 'base64')); report.screenshots.push({ width, filename, ...dimensions });
  }
  assert.equal(errors.length, 0, 'browser exceptions');
  assert.ok(requests.filter(request => request.status === 206 && request.authenticated).length >= 2, 'explicit browser Range probes verified for both codecs; media may download the entire small fixture');
  writeFileSync(path.join(out, 'kt116-browser-results.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ browser: report.browser, audio: report.audio.length, video: report.video.length, max_error: Math.max(...report.audio.concat(report.video).map(row => Math.abs(row.target - row.actual))), requests: requests.length, out }, null, 2));
  if (process.env.KT116_INSPECTOR) {
    await new Promise((resolve, reject) => {
      const inspection = spawn(process.execPath, [process.env.KT116_INSPECTOR, base + '/tests/kt116-browser.html', '--app', '--out', path.join(out, 'inspection')], { stdio: 'inherit', windowsHide: true });
      inspection.once('error', reject); inspection.once('exit', code => code === 0 ? resolve() : reject(new Error('Inspector exit ' + code)));
    });
  }
} finally {
  try { socket?.close(); } catch {}
  if (browser?.pid) { try { if (process.platform === 'win32') execFileSync('taskkill', ['/pid', String(browser.pid), '/T', '/F'], { stdio: 'ignore', windowsHide: true }); else browser.kill(); } catch {} }
  await server?.close();
}
