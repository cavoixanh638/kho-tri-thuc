export type WikiQuery = { start: number; end: number; query: string };
/** Only offer a trigger in ordinary prose; fenced/inline code and escaped brackets stay raw. */
export function wikiQuery(text: string, caret: number): WikiQuery | undefined {
  const before = text.slice(0, caret);
  let fence: string | undefined;
  for (const line of before.split('\n')) {
    const marker = /^ {0,3}(`{3,}|~{3,})/.exec(line)?.[1];
    if (marker) { if (!fence) fence = marker; else if (marker[0] === fence[0] && marker.length >= fence.length) fence = undefined; }
  }
  if (fence) return;
  const lineStart = before.lastIndexOf('\n') + 1;
  const line = before.slice(lineStart);
  if (/^( {4}|\t|\s*<|\s*>)/.test(line)) return;
  const match = /(?<![\\\[])\[\[([^\[\]\n]{0,120})$/.exec(line);
  if (!match || /[`]/.test(line.slice(0, match.index))) return;
  return { start: lineStart + match.index, end: caret, query: match[1] };
}
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export function wikiInsertion(text: string, query: WikiQuery, target: { item_id: string; title: string }) {
  if (!uuid.test(target.item_id) || wikiQuery(text, query.end)?.start !== query.start) return;
  const label = (target.title || 'Chưa đặt tên').replace(/[\[\]<>\\\r\n]/g, ' ').trim().slice(0, 200) || 'Mở bài';
  const link = '[' + label + '](#/muc/' + target.item_id + ')';
  const end = text.slice(query.end).startsWith(']]') ? query.end + 2 : query.end;
  return { text: text.slice(0, query.start) + link + text.slice(end), caret: query.start + link.length };
}
