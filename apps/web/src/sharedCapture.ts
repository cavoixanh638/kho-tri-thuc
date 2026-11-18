type SharedCapture = { kind: 'link' | 'text'; url: string; note: string; annotation: string; shared: boolean };

export function readSharedCapture(): SharedCapture {
  const page = new URL(window.location.href);
  const title = page.searchParams.get('shared_title') ?? '';
  const text = page.searchParams.get('shared_text') ?? '';
  const url = page.searchParams.get('shared_url') ?? '';
  const shared = ['shared_title', 'shared_text', 'shared_url'].some((key) => page.searchParams.has(key));
  const content = [title, text].filter(Boolean).join('\n');
  const candidate = url || (/^https?:\/\/\S+$/i.test(text.trim()) ? text.trim() : '');
  return {
    kind: candidate ? 'link' : shared ? 'text' : 'link',
    url: candidate.slice(0, 4096),
    note: content.slice(0, 65536),
    annotation: candidate ? content.slice(0, 65536) : '',
    shared,
  };
}
