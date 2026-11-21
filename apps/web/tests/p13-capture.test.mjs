import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const read = (relative) => readFileSync(new URL(relative, import.meta.url), 'utf8');
const manifest = JSON.parse(read('../public/manifest.webmanifest'));
const fixture = JSON.parse(read('../../backend/ingestion/fixtures/kt117-fixtures.json'));
const capture = read('../src/CaptureScreen.tsx');
const share = read('../src/sharedCapture.ts');

test('P13 PWA target has GET title/text/url and no unsupported native file parameter', () => {
  assert.equal(manifest.share_target.action, '/');
  assert.equal(manifest.share_target.method, 'GET');
  assert.deepEqual(manifest.share_target.params,
    { title: 'shared_title', text: 'shared_text', url: 'shared_url' });
  assert.equal(manifest.share_target.enctype, undefined);
  assert.equal(manifest.share_target.params.files, undefined);
});
test('P13 30 unique share payloads include Unicode, Vietnamese and invalid link safety cases', () => {
  assert.equal(fixture.length, 30);
  assert.equal(new Set(fixture.map(row => row.name)).size, 30);
  for (const row of fixture) {
    assert.ok(['text', 'link'].includes(row.kind));
    assert.equal(typeof row.raw, 'string');
    assert.equal(typeof row.url, 'string');
    assert.ok(Object.keys(row.params).every(k => ['shared_title', 'shared_text', 'shared_url'].includes(k)));
  }
  assert.ok(fixture.some(x => x.name === 'unicode-combining'));
  assert.ok(fixture.some(x => x.name === 'emoji-cjk'));
  assert.ok(fixture.some(x => x.name === 'crlf'));
  assert.ok(fixture.some(x => x.name === 'credentials' && x.kind === 'text'));
  assert.ok(fixture.some(x => x.name === 'tiktok' && x.kind === 'link'));
});
test('P13 exact URL and note body do not get normalized at the share parser boundary', () => {
  assert.match(share, /searchParams\.get\('shared_text'\)/);
  assert.match(share, /searchParams\.get\('shared_url'\)/);
  assert.match(share, /join\('\\n'\)/);
  assert.match(share, /!url\.username && !url\.password/);
  assert.match(share, /const drafts = new Map/);
});
test('P13 retransmission preserves attempt key until server acknowledgment', () => {
  assert.match(capture, /attempt\.current\.body !== signature/);
  assert.match(capture, /idempotencyKey: attempt\.current\.key/);
  assert.match(capture, /attempt\.current = null/);
  assert.match(capture, /readCaptureDraft\(session\.username\)/);
  assert.match(capture, /clearCaptureDraft\(ownerRef\.current\)/);
  assert.match(capture, /Chưa xác nhận tiếp nhận/);
});
test('P13 textarea retains browser IME result, with native Gboard/Unikey gate not inferred', () => {
  assert.match(capture, /setNote\(event\.currentTarget\.value\)/);
  assert.match(capture, /Array\.from\(text\)\.length > 65_536/);
  assert.match(capture, /text\.includes\('\\0'\)/);
  assert.doesNotMatch(capture, /(?:onKeyDown|onKeyPress).*preventDefault/s);
});
test('P13 receipts distinguish accepted capture from verified Drive media', () => {
  assert.match(capture, /Đã tiếp nhận lúc/);
  assert.match(capture, /Chưa xác nhận tệp đã được lưu và kiểm tra trên Drive/);
});
