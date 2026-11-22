#!/usr/bin/env node
/**
 * Fail-closed G2 browser checkpoint. Runs in the EXISTING P08/P15 QA job,
 * after both diagnostic steps and evidence uploads. A green build is NOT a
 * completed user journey; synthetic QA is NOT production/native UAT.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { CASES } from './p08_report.mjs';

const REQUIRED_VIEWS = [390, 768, 1440, 1920];
const STATUS = new Set(['PASS', 'FAIL', 'BLOCKED', 'NOT_RUN']);
function headMatches(report, expected) {
  if (!expected) return true;
  return !!report && report.tested_sha === expected;
}
function selectReason(value) {
  if (typeof value !== 'string') return null;
  // Do not accidentally publish a private URL or disk path from an exception.
  return value.replace(/https?:\/\/\S+/gi, '[url]')
    .replace(/[A-Za-z]:\\[^\s]+/g, '[path]')
    .replace(/\/(?:home|tmp|mnt|Users)\/[^\s]+/g, '[path]')
    .slice(0, 120);
}
export function evaluateGate(p08, p15, { sha = null } = {}) {
  const issues = [];
  const byId = new Map();
  if (!Array.isArray(p08?.journeys)) issues.push('P08_REPORT_MISSING');
  else for (const item of p08.journeys) {
    if (!item || typeof item.id !== 'string' || !STATUS.has(item.status) || byId.has(item.id)) {
      issues.push('P08_INVALID_OR_DUPLICATE_CASE');
      continue;
    }
    byId.set(item.id, item);
  }
  const cases = CASES.map(({ id }) => {
    const row = byId.get(id);
    return { id, status: row?.status ?? 'NOT_RUN', reason: selectReason(row?.reason) };
  });
  if (byId.size !== CASES.length || cases.some(x => !byId.has(x.id))) {
    issues.push('P08_CASE_REGISTRY_INCOMPLETE');
  }
  const counts = Object.fromEntries(['PASS', 'FAIL', 'BLOCKED', 'NOT_RUN'].map(x =>
    [x, cases.filter(row => row.status === x).length]));
  if (p08?.status !== 'PASS' || cases.some(x => x.status !== 'PASS')) {
    issues.push('P08_JOURNEYS_NOT_ALL_PASS');
  }
  const expectedComplete = cases.every(x => x.status === 'PASS');
  if (p08?.metrics?.complete !== expectedComplete
      || p08?.metrics?.tested !== CASES.length
      || Object.entries(counts).some(([key, n]) => p08?.metrics?.counts?.[key] !== n)) {
    issues.push('P08_LEDGER_COUNTS_MISMATCH');
  }
  if (!headMatches(p08, sha)) issues.push('P08_TESTED_SHA_MISMATCH');

  if (!p15 || typeof p15 !== 'object') issues.push('P15_REPORT_MISSING');
  const p15Gate = p15?.summary?.gate || 'NOT_RUN';
  if (p15?.fatal) issues.push('P15_FATAL');
  if (p15Gate !== 'BROWSER_DOM_AND_KEYBOARD_PASS_SCREEN_READER_NOT_RUN') {
    issues.push('P15_KEYBOARD_OR_DOM_INCOMPLETE');
  }
  const keyboard = Array.isArray(p15?.keyboard) ? p15.keyboard : [];
  if (keyboard.length < 40 || keyboard.some(row => row.status !== 'PASS')) {
    issues.push('P15_KEYBOARD_ACTIONS_INCOMPLETE');
  }
  const blocked = Array.isArray(p15?.blocked) ? p15.blocked.length : -1;
  if (blocked !== 0) issues.push('P15_BROWSER_BLOCKED_CASES');
  const views = Array.isArray(p15?.viewports) ? p15.viewports : [];
  if (views.length !== REQUIRED_VIEWS.length
      || views.some(v => v.page_overflow === true || v.status !== 'DOM_CHECK_PASS_NOT_VISUAL')
      || !REQUIRED_VIEWS.every(width => views.some(v => v.width === width))) {
    issues.push('P15_RESPONSIVE_VIEWPORTS_INCOMPLETE');
  }
  if (!headMatches(p15, sha)) issues.push('P15_TESTED_SHA_MISMATCH');

  const uniqueIssues = [...new Set(issues)];
  return {
    gate: 'G2_CI_BROWSER_ACCEPTANCE',
    status: uniqueIssues.length ? 'NOT_READY' : 'PASS_SYNTHETIC_BROWSER_ONLY',
    ready: uniqueIssues.length === 0,
    tested_sha: sha || 'NOT_SPECIFIED',
    p08: {
      counts,
      required: CASES.length,
      completed: counts.PASS,
      executed: counts.PASS + counts.FAIL,
      pass_rate: (counts.PASS + counts.FAIL) ? counts.PASS / (counts.PASS + counts.FAIL) : null,
      completion: counts.PASS / CASES.length,
      incomplete_cases: cases.filter(x => x.status !== 'PASS'),
    },
    p15: {
      gate: p15Gate, keyboard_actions: keyboard.length,
      keyboard_failures: keyboard.filter(x => x.status !== 'PASS').length,
      blocked_cases: blocked, viewports: views.map(v => v.width),
      fatal: !!p15?.fatal,
    },
    issues: uniqueIssues,
    scope: 'Only isolated synthetic browser. Screen reader, native Android, real Drive, Gemini and production UAT remain separate.',
  };
}

function readJson(path) {
  try { return JSON.parse(readFileSync(resolve(path), 'utf8')); }
  catch { return null; }
}
const executable = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (executable) {
  const args = process.argv.slice(2);
  const valueFor = opt => { const i = args.indexOf(opt); return i >= 0 ? args[i + 1] : null; };
  if (!valueFor('--p08') || !valueFor('--p15')) {
    console.error('Usage: release_acceptance_gate.mjs --p08 <ledger.json> --p15 <browser-results.json>');
    process.exitCode = 2;
  } else {
    const result = evaluateGate(readJson(valueFor('--p08')), readJson(valueFor('--p15')), {
      sha: process.env.GITHUB_SHA || null,
    });
    console.log(JSON.stringify(result, null, 2));
    if (!result.ready) process.exitCode = 2;
  }
}
