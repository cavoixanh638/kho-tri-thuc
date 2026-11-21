export type SharedCapture = { kind: 'link' | 'text'; url: string; note: string; annotation: string; shared: boolean };

export function captureHttpUrl(value: string): boolean {
  if (!/^https?:\/\//i.test(value.trim()) || /[\s\\\u0000-\u001f\u007f]/u.test(value.trim())) return false;
  try {
    const url = new URL(value);
    return Boolean(url.hostname) && !url.username && !url.password;
  } catch {
    return false;
  }
}

export function readSharedCapture(): SharedCapture {
  const page = new URL(window.location.href);
  const title = page.searchParams.get('shared_title') ?? '';
  const text = page.searchParams.get('shared_text') ?? '';
  const url = page.searchParams.get('shared_url') ?? '';
  const shared = ['shared_title', 'shared_text', 'shared_url'].some((key) => page.searchParams.has(key));
  const content = [title, text].filter(Boolean).join('\n');
  // An explicit URL wins; a paragraph containing several links stays one note.
  // Invalid schemes are retained as inert text, never navigated or previewed.
  const candidate = url ? (captureHttpUrl(url) ? url : '') : captureHttpUrl(text) ? text : '';
  return {
    kind: candidate ? 'link' : 'text',
    url: candidate,
    note: !candidate && url ? [content, url].filter(Boolean).join('\n') : content,
    annotation: candidate ? content : '',
    shared,
  };
}

export type CaptureDraft = Omit<SharedCapture, 'kind'> & {
  kind: SharedCapture['kind'] | 'file';
  attempt: { body: string; key: string } | null;
};

// Tab memory survives the login screen replacing CaptureScreen. It is scoped to
// the authenticated account and is never an offline queue or an acknowledgement.
const drafts = new Map<string, CaptureDraft>();
const files = new Map<string, { file: File; key: string }>();
export function readCaptureDraft(owner: string) { return drafts.get(owner); }
export function saveCaptureDraft(owner: string, draft: CaptureDraft) { drafts.set(owner, draft); }
export function clearCaptureDraft(owner: string) { drafts.delete(owner); files.delete(owner); }
export function readCaptureFile(owner: string) { return files.get(owner); }
export function saveCaptureFile(owner: string, value: { file: File; key: string } | null) {
  if (value) files.set(owner, value);
  else files.delete(owner);
}
