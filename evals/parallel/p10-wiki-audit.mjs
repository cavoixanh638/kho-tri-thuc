#!/usr/bin/env node
// Run: node --experimental-strip-types evals/parallel/p10-wiki-audit.mjs
// Node 24+ supports native TypeScript type stripping without the flag.
import { wikiQuery } from '../../apps/web/src/WikiCompletion.ts';
const tick = String.fromCharCode(96);
const scenarios = [
  ['plain_prose', 'Ghi chú [[Bài', true],
  ['unicode_prose', 'Tài liệu [[Đầu tư', true],
  ['fence_backticks', tick.repeat(3) + 'md\n[[Bài', false],
  ['fence_tildes', '~~~md\n[[Bài', false],
  ['fence_closed', tick.repeat(3) + 'md\ncode\n' + tick.repeat(3) + '\n[[Bài', true],
  ['inline_unclosed', tick + 'code [[Bài', false],
  ['escaped_bracket', '\\[[Bài', false],
  ['indented_code', '    [[Bài', false],
  ['html', '<script>[[Bài', false],
  ['blockquote', '> [[Bài', false],
  ['ordinary_text_after_inline_code', tick + 'code' + tick + ' rồi [[Bài', true],
  ['nonclosing_fence_with_info', tick.repeat(3) + 'md\n' + tick.repeat(3) + 'not-closed\n[[Bài', false],
];
const cases = scenarios.map(([name, raw, expected]) => {
  const actual = Boolean(wikiQuery(raw, raw.length));
  return { case: name, status: actual === expected ? 'PASS' : 'FAIL', expected_trigger: expected, observed_trigger: actual };
});
const result = {
  suite: 'P10 actual WikiCompletion.ts parser (Node type stripping)',
  passed: cases.filter((c) => c.status === 'PASS').length,
  failed: cases.filter((c) => c.status === 'FAIL').length,
  cases,
};
console.log(JSON.stringify(result, null, 2));
if (process.argv.includes('--strict') && result.failed) process.exitCode = 1;
