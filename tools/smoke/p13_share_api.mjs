#!/usr/bin/env node
/** Isolated P13 ack/idempotency probe through the real Django frontend proxy. */
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

const ORIGIN = 'http://127.0.0.1:5173';
const reportPath = resolve('tmp/p13-share-api-results.json');
const report = { task: 'P13', mode: 'ISOLATED_REAL_API', outcomes: [], synthetic: true,
  android_physical: 'NOT_RUN', unikey_evkey_physical: 'NOT_RUN', drive_real: 'NOT_RUN' };
const record = (name, status, detail = {}) => report.outcomes.push({ name, status, ...detail });
const save = () => {
  mkdirSync(dirname(reportPath), { recursive: true });
  writeFileSync(reportPath, JSON.stringify(report, null, 2) + '\n', { mode: 0o600 });
};
const requireQA = () => {
  assert.equal(process.env.P13_QA_ISOLATED, 'YES', 'Synthetic isolated QA flag required');
  assert.ok(/^kt-[a-z0-9-]+$/.test(process.env.P13_QA_USER || ''), 'Synthetic kt- account required');
  assert.ok(process.env.P13_QA_PASSWORD, 'Synthetic QA password required');
  assert.equal(process.env.P13_QA_ORIGIN || ORIGIN, ORIGIN, 'Only loopback frontend proxy permitted');
};
const jar = new Map();
function cookies(response) {
  for (const value of response.headers.getSetCookie?.() ?? []) {
    const [part] = value.split(';'); const eq = part.indexOf('=');
    if (eq > 0) jar.set(part.slice(0, eq), part.slice(eq + 1));
  }
}
async function request(method, path, { body, csrf, key, omitCookies = false, expected } = {}) {
  const headers = new Headers({ Accept: 'application/json', Origin: ORIGIN });
  if (body !== undefined) headers.set('Content-Type', 'application/json');
  if (csrf) headers.set('X-CSRFToken', csrf);
  if (key) headers.set('Idempotency-Key', key);
  if (!omitCookies && jar.size) headers.set('Cookie', [...jar].map(([k, v]) => `${k}=${v}`).join('; '));
  const response = await fetch(ORIGIN + '/api/v1' + path, {
    method, headers, redirect: 'manual', signal: AbortSignal.timeout(15000),
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  cookies(response);
  if (expected !== undefined) assert.equal(response.status, expected, `${method} ${path} HTTP status`);
  const type = response.headers.get('content-type') || '';
  const data = type.includes('application/json') ? await response.json() : null;
  return { status: response.status, data };
}
async function main() {
  requireQA();
  const pre = (await request('GET', '/session', { expected: 200 })).data;
  const login = (await request('POST', '/session', {
    body: { username: process.env.P13_QA_USER, password: process.env.P13_QA_PASSWORD },
    csrf: pre.csrf_token, expected: 200,
  })).data;
  assert.equal(login.authenticated, true);
  assert.equal(login.username, process.env.P13_QA_USER);
  record('session_and_csrf', 'PASS');
  const key = randomUUID();
  const payload = { kind: 'link', source_channel: 'share',
    url: `https://smoke-fixture.invalid/p13-${randomUUID()}`,
    text: 'P13 synthetic Android share — tiếng Việt 🌿' };
  const first = (await request('POST', '/captures', { body: payload, csrf: login.csrf_token, key, expected: 201 })).data;
  assert.ok(first.capture_id && first.item_id);
  const historyPath = `/items/${first.item_id}/captures`;
  const before = (await request('GET', historyPath, { expected: 200 })).data.results;
  assert.equal(before.filter(e => e.capture_id === first.capture_id).length, 1);
  const retry = (await request('POST', '/captures', { body: payload, csrf: login.csrf_token, key, expected: 200 })).data;
  assert.deepEqual(retry, first, 'Same key must return identical acknowledgement');
  const repeated = (await request('GET', historyPath, { expected: 200 })).data.results;
  assert.equal(repeated.length, before.length, 'Retry must produce +0 CaptureEvents');
  record('same_idempotency_key', 'PASS', { event_delta: repeated.length - before.length });
  const second = (await request('POST', '/captures', { body: { ...payload, text: 'P13 gửi lần hai' },
    csrf: login.csrf_token, key: randomUUID(), expected: 201 })).data;
  assert.equal(second.item_id, first.item_id, 'Same normalized URL must map to one item');
  assert.notEqual(second.capture_id, first.capture_id, 'New share must create new capture');
  const newer = (await request('GET', historyPath, { expected: 200 })).data.results;
  assert.equal(newer.length, repeated.length + 1, 'New send must produce +1 CaptureEvent');
  record('new_send', 'PASS', { event_delta: newer.length - repeated.length });
  const anonymous = await request('POST', '/captures', { body: payload, key: randomUUID(), omitCookies: true });
  assert.ok([401, 403].includes(anonymous.status), 'Unauthenticated write must be rejected');
  const csrfDenied = await request('POST', '/captures', { body: payload, key: randomUUID() });
  assert.equal(csrfDenied.status, 403, 'Missing CSRF on authenticated POST must be denied');
  const afterDenied = (await request('GET', historyPath, { expected: 200 })).data.results;
  assert.equal(afterDenied.length, newer.length, 'Unauthorized requests must produce +0 events');
  record('anonymous_and_csrf', 'PASS', { anonymous_http: anonymous.status, missing_csrf_http: csrfDenied.status,
    event_delta: afterDenied.length - newer.length });
  record('android_native_390_768_ime', 'NOT_RUN', { reason: 'Physical Android device and native IME required' });
  save();
  console.log(`P13 isolated API PASS: ${report.outcomes.filter(x => x.status === 'PASS').length} gates; PostgreSQL CaptureEvents +0 retry / +1 new send; ${reportPath}`);
}
try { await main(); } catch (error) {
  record('api_probe', process.env.P13_QA_ISOLATED === 'YES' ? 'FAIL' : 'NOT_RUN',
    { reason: String(error?.message || error).slice(0, 180).replace(/https?:\/\/\S+/g, '[redacted-url]') });
  save();
  console.error(`P13 ${report.outcomes.at(-1).status}: ${report.outcomes.at(-1).reason}; ${reportPath}`);
  process.exitCode = process.env.P13_QA_ISOLATED === 'YES' ? 1 : 2;
}
