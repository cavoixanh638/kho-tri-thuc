import { Button, FileInput, SegmentedControl, Textarea, TextInput } from '@mantine/core';
import { useRef, useState, type SubmitEvent } from 'react';
import { ApiError, request, type Capture, type Page, type Receipt, type UploadReceipt } from './api';
import { CaptureList, Empty, ErrorNotice, itemHref, Loading, PageTitle, ServerTime, useResource } from './views';

type Kind = Capture['raw_kind'] | 'file';

const uploadLimit = 128 * 1024 * 1024;
const uploadTimeout = 10 * 60_000;

function requestKey() {
  return Array.from(crypto.getRandomValues(new Uint8Array(16)), (byte) => byte.toString(16).padStart(2, '0')).join('');
}

export function CaptureScreen({ csrf }: { csrf: string }) {
  const [kind, setKind] = useState<Kind>('link');
  const [url, setUrl] = useState('');
  const [note, setNote] = useState('');
  const [annotation, setAnnotation] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [receipt, setReceipt] = useState<Receipt>();
  const [uploadReceipt, setUploadReceipt] = useState<UploadReceipt>();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string>();
  const inFlight = useRef(false);
  const attempt = useRef<{ body: string; key: string } | null>(null);
  const fileAttempt = useRef<{ file: File; key: string } | null>(null);
  const recent = useResource<Page<Capture>>('/captures?limit=5');

  function clearAttempt() {
    attempt.current = null;
    setError(undefined);
  }

  async function submitFile() {
    if (!file || file.size === 0) {
      setError('Chọn một tệp có nội dung.');
      return;
    }
    if (file.size > uploadLimit) {
      setError('Tệp được lớn tối đa 128 MiB.');
      return;
    }

    if (fileAttempt.current?.file !== file) {
      fileAttempt.current = { file, key: requestKey() };
    }
    const body = new FormData();
    body.append('file', file);
    inFlight.current = true;
    setSaving(true);
    setError(undefined);
    setUploadReceipt(undefined);
    try {
      const received = await request<UploadReceipt>('/uploads', {
        method: 'POST',
        csrf,
        body,
        idempotencyKey: fileAttempt.current.key,
        timeoutMs: uploadTimeout,
      });
      setUploadReceipt(received);
      fileAttempt.current = null;
      setFile(null);
    } catch (error) {
      const status = error instanceof ApiError ? error.status : undefined;
      setError(status === 413 ? 'Chưa tiếp nhận. Tệp được lớn tối đa 128 MiB.'
        : status === 400 || status === 422 ? 'Chưa tiếp nhận. Kiểm tra lại tệp.'
          : 'Chưa xác nhận tiếp nhận tệp. Gửi lại để kiểm tra cùng lượt gửi.');
    } finally {
      inFlight.current = false;
      setSaving(false);
    }
  }

  async function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (inFlight.current) return;
    if (kind === 'file') {
      await submitFile();
      return;
    }

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
      attempt.current = { body: signature, key: requestKey() };
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

  function changeKind(value: string) {
    clearAttempt();
    setReceipt(undefined);
    setUploadReceipt(undefined);
    setKind(value as Kind);
  }

  return <>
    <PageTitle title="Gửi vào kho" description="Tiếp nhận liên kết, ghi chú hoặc tệp." />
    <div className="split-view">
      <section className="panel" aria-labelledby="compose-title">
        <h2 id="compose-title">Lượt gửi mới</h2>
        <form className="form-stack" onSubmit={submit}>
          <SegmentedControl aria-label="Loại nội dung" value={kind} disabled={saving} onChange={changeKind}
            data={[{ label: 'Liên kết', value: 'link' }, { label: 'Ghi chú', value: 'text' }, { label: 'Tệp', value: 'file' }]} />
          {kind === 'link' ? <>
            <TextInput label="Liên kết" type="url" inputMode="url" placeholder="https://…" value={url} disabled={saving} required maxLength={4096}
              onChange={(event) => { clearAttempt(); setUrl(event.currentTarget.value); }} />
            <Textarea label="Ghi chú kèm theo" description="Tùy chọn" value={annotation} disabled={saving} minRows={3} autosize maxRows={8}
              onChange={(event) => { clearAttempt(); setAnnotation(event.currentTarget.value); }} />
          </> : kind === 'text' ? <Textarea label="Nội dung ghi chú" value={note} disabled={saving} required minRows={7} maxRows={18} autosize
            onChange={(event) => { clearAttempt(); setNote(event.currentTarget.value); }} />
            : <FileInput label="Tệp gửi vào kho" description="Tối đa 128 MiB" placeholder="Chọn tệp" value={file} disabled={saving}
              clearable clearButtonProps={{ 'aria-label': 'Bỏ chọn tệp' }} onChange={(value) => {
                if (value !== file) fileAttempt.current = null;
                setFile(value);
                setUploadReceipt(undefined);
                setError(undefined);
              }} />}
          {error && <ErrorNotice>{error}</ErrorNotice>}
          <div className="form-actions">
            <Button type="submit" loading={saving}>{saving && kind === 'file' ? 'Đang gửi tệp' : 'Gửi vào kho'}</Button>
          </div>
        </form>
        {receipt && <div className="receipt" role="status">
          <p>Đã tiếp nhận lúc <ServerTime value={receipt.received_at} /></p>
          <a href={itemHref(receipt.item_id)}>Mở mục trong thư viện</a>
        </div>}
        {uploadReceipt && <div className="receipt" role="status">
          <p>Đã tiếp nhận tệp để xử lý.</p>
          <a href={itemHref(uploadReceipt.item_id)}>Mở mục trong thư viện</a>
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
