import { captureHttpUrl, clearCaptureDraft, readCaptureDraft, readCaptureFile, readSharedCapture, saveCaptureDraft, saveCaptureFile } from './sharedCapture';
import { Button, FileInput, SegmentedControl, Textarea, TextInput } from '@mantine/core';
import { useEffect, useRef, useState, type SubmitEvent } from 'react';
import { ApiError, request, type Capture, type Page, type Receipt, type Session, type UploadReceipt } from './api';
import { CaptureList, Empty, ErrorNotice, itemHref, Loading, PageTitle, ServerTime, useResource } from './views';
import './capture.css';

type Kind = Capture['raw_kind'] | 'file';

const uploadLimit = 128 * 1024 * 1024;
const uploadTimeout = 10 * 60_000;

function requestKey() {
  return Array.from(crypto.getRandomValues(new Uint8Array(16)), (byte) => byte.toString(16).padStart(2, '0')).join('');
}

export function CaptureScreen({ csrf }: { csrf: string }) {
  const [shared, setShared] = useState(readSharedCapture);
  const [kind, setKind] = useState<Kind>(shared.kind);
  const [url, setUrl] = useState(shared.url);
  const [note, setNote] = useState(shared.note);
  const [annotation, setAnnotation] = useState(shared.annotation);
  const [file, setFile] = useState<File | null>(null);
  const [receipt, setReceipt] = useState<Receipt>();
  const [uploadReceipt, setUploadReceipt] = useState<UploadReceipt>();
  const [ackMs, setAckMs] = useState<number>();
  const [lastSend, setLastSend] = useState<{ kind: 'link' | 'text'; url: string; text: string }>();
  const [owner, setOwner] = useState<string>();
  const ownerRef = useRef<string>(undefined);
  const ownerReady = useRef<Promise<void> | null>(null);
  const dirty = useRef(false);
  useEffect(() => {
    if (shared.shared) {
      const page = new URL(window.location.href);
      for (const key of ['shared_title', 'shared_text', 'shared_url']) page.searchParams.delete(key);
      window.history.replaceState(null, '', page.href);
    }
  }, [shared.shared]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string>();
  const inFlight = useRef(false);
  const attempt = useRef<{ body: string; key: string } | null>(null);
  const fileAttempt = useRef<{ file: File; key: string } | null>(null);
  const recent = useResource<Page<Capture>>('/captures?limit=5');

  useEffect(() => {
    let active = true;
    ownerReady.current = request<Session>('/session').then((session) => {
      if (!active || !session.authenticated || !session.username) return;
      ownerRef.current = session.username;
      setOwner(session.username);
      const draft = readCaptureDraft(session.username);
      if (!shared.shared && !dirty.current && draft) {
        setKind(draft.kind);
        setUrl(draft.url);
        setNote(draft.note);
        setAnnotation(draft.annotation);
        setShared((value) => ({ ...value, shared: draft.shared }));
        attempt.current = draft.attempt;
        fileAttempt.current = readCaptureFile(session.username) ?? null;
        setFile(fileAttempt.current?.file ?? null);
      }
    }).catch(() => { /* The existing authenticated form remains usable. */ });
    return () => { active = false; };
  }, []);

  function keepDraft() {
    if (!ownerRef.current) return;
    saveCaptureDraft(ownerRef.current, { kind, url, note, annotation, shared: shared.shared, attempt: attempt.current });
    saveCaptureFile(ownerRef.current, fileAttempt.current);
  }

  useEffect(keepDraft, [owner, kind, url, note, annotation, file, shared.shared]);

  function clearAttempt() {
    dirty.current = true;
    attempt.current = null;
    setError(undefined);
    setReceipt(undefined);
    setUploadReceipt(undefined);
  }

  async function submitFile() {
    const started = Date.now();
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
    await ownerReady.current;
    keepDraft();
    try {
      const received = await request<UploadReceipt>('/uploads', {
        method: 'POST',
        csrf,
        body,
        idempotencyKey: fileAttempt.current.key,
        timeoutMs: uploadTimeout,
      });
      setUploadReceipt(received);
      setAckMs(Math.max(0, Date.now() - started));
      fileAttempt.current = null;
      if (ownerRef.current) clearCaptureDraft(ownerRef.current);
      setFile(null);
    } catch (error) {
      const status = error instanceof ApiError ? error.status : undefined;
      setError(status === 401 ? 'Chưa xác nhận tiếp nhận. Đăng nhập lại rồi gửi lại cùng lượt gửi.'
        : status === 403 ? 'Chưa tiếp nhận. Kiểm tra quyền hoặc phiên đăng nhập rồi thử lại; bản nháp vẫn được giữ.'
        : status === 413 ? 'Chưa tiếp nhận. Tệp được lớn tối đa 128 MiB.'
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
    const started = Date.now();
    if (kind === 'file') {
      await submitFile();
      return;
    }

    const text = kind === 'link' ? annotation : note;
    const link = url;
    if ((kind === 'link' && !link) || (kind === 'text' && !text.trim())) {
      setError(kind === 'link' ? 'Nhập liên kết cần gửi.' : 'Nhập nội dung ghi chú.');
      return;
    }
    if (Array.from(text).length > 65_536) {
      setError('Ghi chú được dài tối đa 65.536 ký tự.');
      return;
    }
    if (kind === 'link' && (Array.from(link).length > 4096 || !captureHttpUrl(link))) {
      setError('Dùng liên kết HTTP(S) hợp lệ, không có thông tin đăng nhập, tối đa 4.096 ký tự.');
      return;
    }
    if (text.includes('\0')) { setError('Nội dung chứa ký tự không hợp lệ; bản nháp vẫn được giữ.'); return; }

    const body = { kind, source_channel: shared.shared ? 'share' : 'web', ...(kind === 'link' ? { url: link, text } : { text }) };
    const signature = JSON.stringify(body);
    if (!attempt.current || attempt.current.body !== signature) {
      attempt.current = { body: signature, key: requestKey() };
    }
    inFlight.current = true;
    setSaving(true);
    setError(undefined);
    setReceipt(undefined);
    await ownerReady.current;
    keepDraft();
    try {
      const received = await request<Receipt>('/captures', {
        method: 'POST',
        body,
        csrf,
        idempotencyKey: attempt.current.key,
      });
      setReceipt(received);
      setAckMs(Math.max(0, Date.now() - started));
      setLastSend({ kind, url: link, text });
      attempt.current = null;
      if (ownerRef.current) clearCaptureDraft(ownerRef.current);
      if (kind === 'link') {
        setUrl('');
        setAnnotation('');
      } else {
        setNote('');
      }
      recent.retry();
    } catch (error) {
      const invalid = error instanceof ApiError && (error.status === 400 || error.status === 422);
      setError(error instanceof ApiError && error.status === 401
        ? 'Chưa xác nhận tiếp nhận. Đăng nhập lại rồi gửi lại cùng lượt gửi.'
        : error instanceof ApiError && error.status === 403
          ? 'Chưa tiếp nhận. Kiểm tra quyền hoặc phiên đăng nhập rồi thử lại; bản nháp vẫn được giữ.'
        : invalid
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

  function clearDraft() {
    clearAttempt();
    fileAttempt.current = null;
    setUrl(''); setNote(''); setAnnotation(''); setFile(null);
    setShared((value) => ({ ...value, shared: false }));
    if (ownerRef.current) clearCaptureDraft(ownerRef.current);
  }

  return <>
    <PageTitle title="Gửi vào kho" description="Lưu tri thức bằng văn bản hoặc Markdown; thêm liên kết, tài liệu và media làm nguồn." />
    <div className="split-view">
      <section className="panel capture-compose" aria-labelledby="compose-title">
        <h2 id="compose-title">Lượt gửi mới</h2>
        <form className="form-stack" onSubmit={submit} onChange={() => { dirty.current = true; }}>
          <SegmentedControl aria-label="Loại nội dung" value={kind} disabled={saving} onChange={changeKind}
            data={[{ label: 'Văn bản / Markdown', value: 'text' }, { label: 'Liên kết', value: 'link' }, { label: 'Tệp', value: 'file' }]} />
          {kind === 'link' ? <>
            <TextInput label="Liên kết" type="url" inputMode="url" placeholder="https://…" value={url} disabled={saving} required
              onChange={(event) => { clearAttempt(); setUrl(event.currentTarget.value); }} />
            <Textarea label="Ghi chú kèm theo" description="Tùy chọn" value={annotation} disabled={saving} minRows={3} autosize maxRows={8}
              onChange={(event) => { clearAttempt(); setAnnotation(event.currentTarget.value); }} />
          </> : kind === 'text' ? <Textarea label="Nội dung tri thức (Markdown)" description="Có thể dùng tiêu đề #, danh sách, bảng và liên kết. Văn bản được giữ nguyên khi lưu." value={note} disabled={saving} required minRows={5} maxRows={24} autosize autoFocus
            onChange={(event) => { clearAttempt(); setNote(event.currentTarget.value); }} />
            : <FileInput label="Tệp gửi vào kho" description="Tối đa 128 MiB" placeholder="Chọn tệp" value={file} disabled={saving}
              clearable clearButtonProps={{ 'aria-label': 'Bỏ chọn tệp' }} onChange={(value) => {
                clearAttempt();
                if (value !== file) fileAttempt.current = value ? { file: value, key: requestKey() } : null;
                setFile(value);
              }} />}
          {error && <ErrorNotice>{error}</ErrorNotice>}
          <div className="form-actions">
            <Button type="submit" loading={saving}>{saving && kind === 'file' ? 'Đang gửi tệp' : 'Gửi vào kho'}</Button>
            <Button type="button" variant="subtle" disabled={saving || !(url || note || annotation || file)} onClick={clearDraft}>Xóa bản nháp</Button>
          </div>
          <small>{owner ? 'Bản nháp được giữ trong tab này khi cần đăng nhập lại cùng tài khoản. ' : ''}Chỉ biên nhận mới xác nhận máy chủ đã nhận. Tải lại hoặc đóng tab sẽ mất bản nháp.</small>
        </form>
        {receipt && <div className="receipt" role="status">
          <p>Đã tiếp nhận lúc <ServerTime value={receipt.received_at} /></p>
          <p>Lượt gửi: {receipt.capture_id}</p>
          <p>Độ trễ biên nhận: {ackMs} ms (đo tại trình duyệt).</p>
          {lastSend?.kind === 'link' && <p>Liên kết đã được tiếp nhận; việc tải nguồn và xác minh tệp trên Drive được xử lý sau.</p>}
          <a href={itemHref(receipt.item_id)}>Mở mục trong thư viện</a>
          {lastSend && <Button type="button" variant="subtle" disabled={saving} onClick={() => {
            clearAttempt(); setKind(lastSend.kind); setUrl(lastSend.url);
            if (lastSend.kind === 'link') setAnnotation(lastSend.text); else setNote(lastSend.text);
            setReceipt(undefined);
          }}>Dùng lại nội dung</Button>}
        </div>}
        {uploadReceipt && <div className="receipt" role="status">
          <p>Đã tiếp nhận tệp để xử lý.</p>
          <p>Độ trễ biên nhận: {ackMs} ms (đo tại trình duyệt). Chưa xác nhận tệp đã được lưu và kiểm tra trên Drive.</p>
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
