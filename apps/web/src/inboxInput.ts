import { captureHttpUrl } from './sharedCapture';

/** Pure routing for the single inbox input; never visits a pasted URL. */
export type InboxDecision =
  | { kind: 'link'; url: string; text: string; source: 'share' | 'pasted-link' }
  | { kind: 'text'; text: string; source: 'authored-text' };

export function detectInboxInput(raw: string, sharedUrl = ''): InboxDecision {
  if (sharedUrl && captureHttpUrl(sharedUrl)) {
    return { kind: 'link', url: sharedUrl, text: raw, source: 'share' };
  }
  const rows = raw.split(/\r\n|\r|\n/);
  const firstNonEmpty = rows.findIndex(row => row.trim().length > 0);
  const first = firstNonEmpty < 0 ? '' : rows[firstNonEmpty].trim();
  // Only an initial URL is an explicit link. A paragraph containing multiple
  // URLs stays verbatim text; never silently split or fetch a URL mid-paragraph.
  if (first && firstNonEmpty >= 0 && rows.slice(0, firstNonEmpty).every(row => !row.trim()) &&
    captureHttpUrl(first) && !rows.slice(firstNonEmpty + 1).some(row => captureHttpUrl(row.trim()))) {
    const match = [...raw.matchAll(/\r\n|\r|\n/g)][firstNonEmpty];
    const caption = match ? raw.slice(match.index! + match[0].length) : '';
    return { kind: 'link', url: first, text: caption, source: 'pasted-link' };
  }
  return { kind: 'text', text: raw, source: 'authored-text' };
}

export function inboxFileKind(file: Pick<File, 'type' | 'name'>) {
  const type = file.type.toLowerCase();
  const name = file.name.toLowerCase();
  if (/^image\/(jpeg|png|webp|gif|bmp|avif)$/.test(type) ||
    /\.(png|jpe?g|webp|gif|bmp|avif)$/.test(name)) return 'image' as const;
  if (type.startsWith('video/') || /\.(mp4|webm|mov|mkv)$/.test(name)) return 'video' as const;
  if (type.startsWith('audio/') || /\.(mp3|wav|m4a|ogg)$/.test(name)) return 'audio' as const;
  return 'document' as const;
}

export const INBOX_MAX_FILES = 10;
export const INBOX_MAX_FILE_BYTES = 128 * 1024 * 1024;

export function validateInboxFiles(files: readonly File[], existing = 0): string | undefined {
  if (files.length + existing > INBOX_MAX_FILES) return 'Mỗi lượt chọn tối đa 10 tệp hoặc ảnh.';
  if (files.some(file => file.size === 0)) return 'Có tệp rỗng. Hãy chọn tệp có nội dung.';
  if (files.some(file => file.size > INBOX_MAX_FILE_BYTES)) return 'Mỗi tệp tối đa 128 MiB.';
  return undefined;
}
