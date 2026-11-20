import { Button, TextInput } from '@mantine/core';
import { useRef, useState, type SubmitEvent } from 'react';
import { externalHttpUrl, request } from './api';
import { ErrorNotice } from './views';

export function SourceLinks({ id, csrf, deleted, onSaved }: { id: string; csrf: string; deleted: boolean; onSaved: () => void }) {
  const [editing, setEditing] = useState(false);
  const [url, setUrl] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const attempt = useRef<{ url: string; key: string } | null>(null);
  const inFlight = useRef(false);
  async function save(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (inFlight.current || !externalHttpUrl(url)) return;
    if (!attempt.current || attempt.current.url !== url) attempt.current = { url, key: crypto.randomUUID() };
    inFlight.current = true; setBusy(true); setError(false);
    try {
      await request(`/items/${encodeURIComponent(id)}/sources`, { method: 'POST', csrf, body: { url }, idempotencyKey: attempt.current.key });
      attempt.current = null; setUrl(''); setEditing(false); onSaved();
    } catch { setError(true); }
    finally { inFlight.current = false; setBusy(false); }
  }
  return <div className="source-attachment">
    {!editing ? <Button variant="subtle" disabled={deleted} onClick={() => setEditing(true)}>Gắn nguồn / video minh họa vào bài</Button>
      : <form className="form-stack" onSubmit={save}>
        <TextInput label="Liên kết nguồn hoặc video" description="Văn bản từ nguồn được trích vào cùng bài; phần bạn biên soạn được giữ nguyên." type="url" required maxLength={4096} value={url} disabled={busy} onChange={(event) => setUrl(event.currentTarget.value)} />
        <div className="form-actions"><Button type="submit" loading={busy}>Gắn nguồn</Button><Button variant="default" disabled={busy} onClick={() => setEditing(false)}>Hủy</Button></div>
      </form>}
    {error && <ErrorNotice>Chưa gắn được nguồn. Nguồn có thể đã thuộc bài khác hoặc chưa hợp lệ.</ErrorNotice>}
  </div>;
}
