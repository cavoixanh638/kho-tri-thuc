/** KT128/P08 run ledger. Contains no user content, credentials, or private URLs. */
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

export const CASES = Object.freeze([
  { id: 'AUTH', name: 'Browser login / Django session / CSRF', expected: 'Browser login succeeds for a fresh QA account; authenticated session and CSRF token are real.', requires: [] },
  { id: 'J1', name: 'Folder -> note -> child -> shortcut', expected: 'Two nested folders, parent/child notes, persistent home folder and M:N shortcut; UUID, authored Markdown and capture events remain unchanged.', requires: ['AUTH'] },
  { id: 'J2', name: 'Wiki / backlinks / rename / outline / Ctrl+K', expected: 'Autocomplete inserts stable target UUID; backlink survives title change, H1-H6 anchors exist; command palette navigates to target.', requires: ['J1'] },
  { id: 'J3', name: 'Public clip preview / quote / source preservation', expected: 'A public article is previewed before persistence, the quotation is stored and highlighted; the user-authored note remains byte-identical.', requires: ['J1'] },
  { id: 'J4', name: 'Saved smart collection', expected: 'A saved favorite and topic filter recomputes after Item changes and never clones an Item.', requires: ['J1'] },
  { id: 'J4B', name: 'Topic + tag + received-date dynamic collection', expected: 'A saved AND filter on folder/topic, user tag, and receipt day matches once, then updates when tag removed.', requires: ['J1'] },
  { id: 'J5A', name: 'Template draft isolation', expected: 'Template changes only the draft until explicit save, preserving original Markdown.', requires: ['J1'] },
  { id: 'J5B', name: 'Manual review provider OFF', expected: 'A manual proposal can be previewed and rejected without mutating the original note; no AI provider is called.', requires: ['J1'] },
  { id: 'J6A', name: 'Source link honesty', expected: 'Link-only reference retains the author note and does not invent PDF page or MP4 timestamp locator.', requires: ['J1'] },
  { id: 'J6B', name: 'Native PDF page / MP4 time', expected: 'Verified private source and pinned-version asset seek correctly to actual page/time, not inferred metadata.', requires: ['AUTH'] },
  { id: 'J7', name: 'Real browser responsiveness and 4 views', expected: '1920/1440/768/390 screenshots; visible folder affordance, no horizontal overflow, same distinct Item IDs in list/table/card/timeline.', requires: ['AUTH'] },
  { id: 'J8', name: 'Portable vault roundtrip', expected: 'Export and re-import to clean PostgreSQL preserve parent/home/shortcut/link/asset/event identities and hashes.', requires: ['AUTH'] },
  { id: 'J9', name: '10k/1k scale / backup / retry', expected: 'Isolated PostgreSQL 10k Items/1k nodes paginates/searches unique IDs; backup hash verifies and retry never duplicates CaptureEvent.', requires: ['AUTH'] },
]);
const VALID = new Set(['PASS', 'FAIL', 'BLOCKED', 'NOT_RUN']);
const BY_ID = new Map(CASES.map((c) => [c.id, c]));

export function qaUrl(raw) {
  // Do not point automated destructive smoke journeys at deployed or production sites.
  if (raw !== 'http://127.0.0.1:62310') throw Error('QA_URL_MUST_BE_LOOPBACK_62310');
  return raw;
}
export function qaDatabase(raw) {
  if (!/^kt_[a-z0-9_]{3,50}$/.test(raw || '') || /prod|live|real|user/.test(raw)) throw Error('ISOLATED_QA_DATABASE_REQUIRED');
  return raw;
}
export function makeReport({ codeSha = null, baseSha, dbName = null, browser = 'Chromium CDP', environment = 'local synthetic QA', now = new Date() } = {}) {
  return {
    schema_version: 1, code_sha: codeSha, tested_sha: codeSha, base_sha: baseSha || null,
    checked_at: now.toISOString(), environment, browser, qa_db_name: dbName,
    credentials_saved: false, private_data_saved: false, real_drive: false, real_ai_provider: false,
    viewports: [], journeys: CASES.map(({ id, name, expected, requires }) => ({ id, name, expected, requires, status: 'NOT_RUN', actual: null, reason: 'not_attempted', evidence: [] })),
    metrics: {}, status: 'NOT_RUN',
  };
}
export function findCase(report, id) {
  const found = report.journeys.find((row) => row.id === id);
  if (!found || !BY_ID.has(id)) throw Error('unknown journey: ' + id);
  return found;
}
export function record(report, id, status, actual, { reason = null, evidence = [], durationMs = null } = {}) {
  if (!VALID.has(status)) throw Error('invalid status: ' + status);
  if (!Array.isArray(evidence) || evidence.some((x) => typeof x !== 'string')) throw Error('invalid evidence');
  const found = findCase(report, id);
  Object.assign(found, { status, actual: String(actual ?? ''), reason, evidence, duration_ms: durationMs });
  return summarize(report);
}
export function unsatisfied(report, id) {
  const entry = BY_ID.get(id);
  if (!entry) throw Error('unknown journey: ' + id);
  return entry.requires.filter((required) => findCase(report, required).status !== 'PASS');
}
export function summarize(report) {
  const counts = { PASS: 0, FAIL: 0, BLOCKED: 0, NOT_RUN: 0 };
  for (const item of report.journeys) counts[item.status]++;
  const executed = counts.PASS + counts.FAIL;
  report.metrics = { counts, executed, passed: counts.PASS, pass_rate: executed ? Number((counts.PASS / executed).toFixed(4)) : null,
    pass_rate_formula: 'PASS / (PASS + FAIL); BLOCKED, NOT_RUN excluded from denominator',
    tested: report.journeys.length, complete: counts.PASS === report.journeys.length };
  report.status = counts.FAIL ? 'FAIL' : counts.BLOCKED ? 'BLOCKED' : counts.NOT_RUN ? 'NOT_RUN' : 'PASS';
  return report;
}
export function cleanError(error) {
  // Exception messages can contain temporary paths and URLs. Never commit stack dumps.
  const message = String(error instanceof Error ? error.message : error);
  return message.replace(/https?:\/\/\S+/gi, '[url]').replace(/[A-Za-z]:\\[^\s]+/g, '[path]').replace(/\/(?:home|tmp|mnt|Users)\/[^\s]+/g, '[path]').slice(0, 350);
}
export function saveReport(report, file) {
  summarize(report);
  const path = resolve(file);
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, JSON.stringify(report, null, 2) + '\n', { mode: 0o600 });
}
