import { Button, SegmentedControl, Textarea, TextInput } from '@mantine/core';
import { useRef, useState, type SubmitEvent } from 'react';
import { ApiError, request, type Capture, type Page, type Receipt } from './api';
import { CaptureList, Empty, ErrorNotice, itemHref, Loading, PageTitle, ServerTime, useResource } from './views';

type Kind = Capture['raw_kind'];

export function CaptureScreen({ csrf }: { csrf: string }) {
  const [kind, setKind] = useState<Kind>('link');
  const [url, setUrl] = useState('');
  const [note, setNote] = useState('');
  const [annotation, setAnnotation] = useState('');
  const [receipt, setReceipt] = useState<Receipt>();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string>();
  const inFlight = useRef(false);
  const attempt = useRef<{ body: string; key: string } | null>(null);
  const recent = useResource<Page<Capture>>('/captures?limit=5');

  function clearAttempt() {
    attempt.current = null;
    setError(undefined);
  }

  async function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (inFlight.current) return;
    const text = kind === 'link' ? annotation : note;
    const link = url.trim();
    if ((kind === 'link' && !link) || (kind === 'text' && !text.trim())) {
      setError(kind === 'link' ? 'Nhập liên kết cần gửi.' : 'Nhập nội dung ghi chú.');
      return;
    }
    if (Array.from(text).length > 65_536) {
      setError('Ghi chú được dài tối đa 65.536 ký tự.');
      return;
    }
    if (kind === 'link' && !/^https?:\/\//i.test(link)) {
      setError('Liên kết phải bắt đầu bằng https:// hoặc http://.');
      return;
    }

    const body = { kind, source_channel: 'web', ...(kind === 'link' ? { url: link, text } : { text }) };
    const signature = JSON.stringify(body);
    if (!attempt.current || attempt.current.body !== signature) {
      const key = Array.from(crypto.getRandomValues(new Uint8Array(16)), (byte) => byte.toString(16).padStart(2, '0')).join('');
      attempt.current = { body: signature, key };
    }
    inFlight.current = true;
    setSaving(true);
    setError(undefined);
    setReceipt(undefined);
    try {
      const received = await request<Receipt>('/captures', {
        method: 'POST',
        body,
        csrf,
        idempotencyKey: attempt.current.key,
      });
      setReceipt(received);
      attempt.current = null;
      if (kind === 'link') {
        setUrl('');
        setAnnotation('');
      } else {
        setNote('');
      }
      recent.retry();
    } catch (error) {
      const invalid = error instanceof ApiError && (error.status === 400 || error.status === 422);
      setError(invalid
        ? 'Chưa tiếp nhận. Kiểm tra liên kết hoặc nội dung ghi chú rồi gửi lại.'
        : 'Chưa xác nhận tiếp nhận. Gửi lại để kiểm tra cùng lượt gửi.');
    } finally {
      inFlight.current = false;
      setSaving(false);
    }
  }

  return <>
    <PageTitle title="Gửi vào kho" description="Lưu liên kết hoặc ghi chú cùng thời điểm tiếp nhận." />
    <div className="split-view">
      <section className="panel" aria-labelledby="compose-title">
        <h2 id="compose-title">Lượt gửi mới</h2>
        <form className="form-stack" onSubmit={submit}>
          <SegmentedControl aria-label="Loại nội dung" value={kind} disabled={saving} onChange={(value) => {
            clearAttempt();
            setKind(value as Kind);
          }} data={[{ label: 'Liên kết', value: 'link' }, { label: 'Ghi chú', value: 'text' }]} />
          {kind === 'link' ? <>
            <TextInput label="Liên kết" type="url" inputMode="url" placeholder="https://…" value={url} disabled={saving} required maxLength={4096}
              onChange={(event) => { clearAttempt(); setUrl(event.currentTarget.value); }} />
            <Textarea label="Ghi chú kèm theo" description="Tùy chọn" value={annotation} disabled={saving} minRows={3} autosize maxRows={8}
              onChange={(event) => { clearAttempt(); setAnnotation(event.currentTarget.value); }} />
          </> : <Textarea label="Nội dung ghi chú" value={note} disabled={saving} required minRows={7} maxRows={18} autosize
            onChange={(event) => { clearAttempt(); setNote(event.currentTarget.value); }} />}
          {error && <ErrorNotice>{error}</ErrorNotice>}
          <div className="form-actions">
            <Button type="submit" loading={saving}>Gửi vào kho</Button>
          </div>
        </form>
        {receipt && <div className="receipt" role="status">
          <p>Đã tiếp nhận lúc <ServerTime value={receipt.received_at} /></p>
          <a href={itemHref(receipt.item_id)}>Mở mục trong thư viện</a>
        </div>}
      </section>
      <section className="panel" aria-labelledby="recent-title">
        <div className="panel-heading">
          <h2 id="recent-title">Vừa tiếp nhận</h2>
          <a href="#/lich-su">Xem lịch sử</a>
        </div>
        {recent.error ? <ErrorNotice retry={recent.retry}>Chưa tải được lịch sử tiếp nhận.</ErrorNotice>
          : !recent.data ? <Loading />
            : recent.data.results.length ? <CaptureList rows={recent.data.results} compact />
              : <Empty>Lượt gửi đầu tiên sẽ xuất hiện ở đây.</Empty>}
      </section>
    </div>
  </>;
}
