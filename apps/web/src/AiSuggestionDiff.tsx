export type NoteDiff = { prefix: string; removed: string; added: string; suffix: string };

export function noteDiff(before: string, after: string): NoteDiff {
  // UTF-16 indices are used only to slice the unchanged original strings;
  // avoid cutting a surrogate pair at the changed region boundary.
  const a = Array.from(before), b = Array.from(after);
  let prefix = 0;
  while (prefix < a.length && prefix < b.length && a[prefix] === b[prefix]) prefix++;
  let suffix = 0;
  while (suffix < a.length - prefix && suffix < b.length - prefix && a[a.length - suffix - 1] === b[b.length - suffix - 1]) suffix++;
  return { prefix: a.slice(0, prefix).join(''), removed: a.slice(prefix, a.length - suffix).join(''), added: b.slice(prefix, b.length - suffix).join(''), suffix: suffix ? a.slice(a.length - suffix).join('') : '' };
}

export function AiSuggestionDiff({ before, after }: { before: string; after: string }) {
  const diff = noteDiff(before, after);
  return <div className="ai-suggestion-diff">
    <section><h3>Trước chỉnh sửa</h3><pre>{before}</pre></section>
    <section><h3>Sau chỉnh sửa đề xuất</h3><pre>{after}</pre></section>
    <section className="ai-suggestion-changes"><h3>Phần thay đổi</h3><pre>{diff.prefix}{diff.removed && <del>{diff.removed}</del>}{diff.added && <ins>{diff.added}</ins>}{diff.suffix}</pre></section>
  </div>;
}
