import test from 'node:test';
import assert from 'node:assert/strict';
import { CASES, qaUrl, qaDatabase, makeReport, findCase, record, unsatisfied, summarize, cleanError } from './p08_report.mjs';

test('exact loopback URL and isolated database guards', () => {
  assert.equal(qaUrl('http://127.0.0.1:62310'), 'http://127.0.0.1:62310');
  for (const url of ['https://example.org', 'http://localhost:62310', 'http://127.0.0.1:8000', 'http://127.0.0.1:62310/']) assert.throws(() => qaUrl(url));
  assert.equal(qaDatabase('kt_p08_synthetic'), 'kt_p08_synthetic');
  for (const name of ['', 'postgres', 'production', 'kt_prod', 'kt_user_test', 'kt_']) assert.throws(() => qaDatabase(name));
});
test('no fake PASS, dependencies blocked, correct denominator', () => {
  const report = makeReport({ codeSha: 'abc', baseSha: 'base', dbName: 'kt_p08_synthetic' });
  assert.equal(report.journeys.length, CASES.length);
  assert.deepEqual(unsatisfied(report, 'J1'), ['AUTH']);
  assert.equal(summarize(report).metrics.pass_rate, null);
  record(report, 'AUTH', 'PASS', 'authenticated');
  record(report, 'J1', 'FAIL', 'assertion failure', { durationMs: 21 });
  record(report, 'J2', 'BLOCKED', 'no seed', { reason: 'dependency:J1' });
  assert.equal(report.metrics.executed, 2);
  assert.equal(report.metrics.pass_rate, 0.5);
  assert.equal(report.status, 'FAIL');
  assert.deepEqual(unsatisfied(report, 'J2'), ['J1']);
  assert.equal(findCase(report, 'J2').reason, 'dependency:J1');
  assert.throws(() => record(report, 'AUTH', 'UNKNOWN', 'x'));
  assert.throws(() => record(report, 'WRONG', 'PASS', 'x'));
});
test('only all-journey-pass can be PASS; invalid evidence rejected', () => {
  const report = makeReport();
  for (const c of CASES) record(report, c.id, 'PASS', 'verified');
  assert.equal(report.status, 'PASS');
  record(report, 'J8', 'NOT_RUN', 'missing integration');
  assert.equal(report.status, 'NOT_RUN');
  assert.equal(report.metrics.pass_rate, 1); // not a release-complete pass
  assert.equal(report.metrics.complete, false);
  assert.throws(() => record(report, 'J8', 'PASS', 'x', { evidence: [1] }));
});
test('error sanitizer never writes private URLs or local paths', () => {
  assert.equal(cleanError(new Error('fetch https://secret.test/token?password=xyz')), 'fetch [url]');
  assert.equal(cleanError('open /home/qa/secret.txt failed'), 'open [path] failed');
});
