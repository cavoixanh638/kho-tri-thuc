import test from 'node:test';
import assert from 'node:assert/strict';
import { CASES } from './p08_report.mjs';
import { evaluateGate } from './release_acceptance_gate.mjs';

const sha = 'a'.repeat(40);
function passingP08() {
  return {
    tested_sha: sha, status: 'PASS',
    journeys: CASES.map(({ id }) => ({ id, status: 'PASS', reason: null })),
    metrics: { complete: true, tested: CASES.length,
      counts: { PASS: CASES.length, FAIL: 0, BLOCKED: 0, NOT_RUN: 0 } },
  };
}
function passingP15() {
  return {
    tested_sha: sha, fatal: null,
    summary: { gate: 'BROWSER_DOM_AND_KEYBOARD_PASS_SCREEN_READER_NOT_RUN' },
    blocked: [],
    keyboard: Array.from({ length: 40 }, (_, i) => ({ id: i, status: 'PASS' })),
    viewports: [1920, 1440, 768, 390].map(width =>
      ({ width, status: 'DOM_CHECK_PASS_NOT_VISUAL', page_overflow: false })),
  };
}
test('all browser checks pass only with complete, same-SHA evidence', () => {
  const verdict = evaluateGate(passingP08(), passingP15(), { sha });
  assert.equal(verdict.ready, true);
  assert.equal(verdict.status, 'PASS_SYNTHETIC_BROWSER_ONLY');
  assert.equal(verdict.p08.completion, 1);
  assert.deepEqual(verdict.issues, []);
});
test('nine passes and four not-run must fail release despite 100% executed pass-rate', () => {
  const p08 = passingP08();
  const missing = ['J3', 'J6B', 'J8', 'J9'];
  for (const row of p08.journeys) if (missing.includes(row.id)) {
    row.status = 'NOT_RUN'; row.reason = 'REQUIRES_INDEPENDENT_EVIDENCE';
  }
  p08.status = 'NOT_RUN';
  p08.metrics = { complete: false, tested: CASES.length,
    counts: { PASS: 9, FAIL: 0, BLOCKED: 0, NOT_RUN: 4 } };
  const verdict = evaluateGate(p08, passingP15(), { sha });
  assert.equal(verdict.ready, false);
  assert.equal(verdict.p08.pass_rate, 1);
  assert.equal(verdict.p08.completion, 9 / 13);
  assert.deepEqual(verdict.p08.incomplete_cases.map(x => x.id), missing);
  assert.ok(verdict.issues.includes('P08_JOURNEYS_NOT_ALL_PASS'));
});
test('fatal P15 focus is not hidden by success in another workflow job', () => {
  const p15 = passingP15();
  p15.fatal = 'Cannot focus hidden clipper select';
  delete p15.summary;
  const verdict = evaluateGate(passingP08(), p15, { sha });
  assert.equal(verdict.ready, false);
  assert.ok(verdict.issues.includes('P15_FATAL'));
  assert.ok(verdict.issues.includes('P15_KEYBOARD_OR_DOM_INCOMPLETE'));
});
test('missing reports, wrong SHA and malformed counts fail closed', () => {
  const p08 = passingP08();
  p08.tested_sha = 'b'.repeat(40);
  p08.metrics.counts.PASS--;
  const first = evaluateGate(p08, passingP15(), { sha });
  assert.ok(first.issues.includes('P08_TESTED_SHA_MISMATCH'));
  assert.ok(first.issues.includes('P08_LEDGER_COUNTS_MISMATCH'));
  const absent = evaluateGate(null, null, { sha });
  assert.equal(absent.ready, false);
  assert.ok(absent.issues.includes('P08_REPORT_MISSING'));
  assert.ok(absent.issues.includes('P15_REPORT_MISSING'));
});
test('responsive viewport or blocked keyboard work makes G2 incomplete', () => {
  const p15 = passingP15();
  p15.viewports[3].page_overflow = true;
  p15.blocked.push({ feature: 'tree', status: 'NOT_RUN' });
  const verdict = evaluateGate(passingP08(), p15, { sha });
  assert.equal(verdict.ready, false);
  assert.ok(verdict.issues.includes('P15_RESPONSIVE_VIEWPORTS_INCOMPLETE'));
  assert.ok(verdict.issues.includes('P15_BROWSER_BLOCKED_CASES'));
});
test('report reasons are redacted and never printed unescaped', () => {
  const p08 = passingP08();
  p08.journeys[0].status = 'FAIL';
  p08.journeys[0].reason = 'https://internal.invalid/token?key=secret';
  p08.status = 'FAIL';
  p08.metrics = { complete: false, tested: CASES.length,
    counts: { PASS: CASES.length - 1, FAIL: 1, BLOCKED: 0, NOT_RUN: 0 } };
  const verdict = evaluateGate(p08, passingP15(), { sha });
  assert.ok(!JSON.stringify(verdict).includes('internal.invalid'));
  assert.ok(JSON.stringify(verdict).includes('[url]'));
});
