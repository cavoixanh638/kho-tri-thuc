import { useEffect, useRef, useState, type ClipboardEvent, type DragEvent, type SubmitEvent } from 'react';
import { Button } from '@mantine/core';
import { clearCaptureDraft, readCaptureDraft, readCaptureFiles, readSharedCapture, saveCaptureDraft, saveCaptureFiles } from './sharedCapture';
import { detectInboxInput, inboxFileKind, validateInboxFiles } from './inboxInput';
import { ApiError, request, type Capture, type Page, type Receipt, type Session, type UploadReceipt } from './api';
import { CaptureList, Empty, ErrorNotice, itemHref, Loading, PageTitle, ServerTime, useResource } from './views';
import { ResearchClipper } from './ResearchClipper';
import './capture.css';

type PendingFile = { file: File; key: string; caption: string };
type CompletedFile = { filename: string; itemId: string; assetId: string; state: string };
type PreviousSend = { kind: 'link' | 'text'; url: string; text: string };

const fileTimeout = 10 * 60_000;

function requestKey() {
  return Array.from(crypto.getRandomValues(new Uint8Array(16)), byte => byte.toString(16).padStart(2, '0')).join('');
}

function previewableImage(file: File): boolean {
  // Never inline SVG, HTML or arbitrary browser-scriptable MIME types.
  return /^image\/(png|jpeg|gif|webp|bmp|avif)$/.test(file.type.toLowerCase());
}

function LocalImage({ file }: { file: File }) {
  const [src, setSrc] = useState('');
  useEffect(() => {
    if (!previewableImage(file) || typeof URL.createObjectURL !== 'function') return;
    const url = URL.createObjectURL(file);
    setSrc(url);
    return () => { URL.revokeObjectURL(url); };
  }, [file]);
  return src ? <img className="capture-file-preview" src={src} alt={'Xem trước ảnh ' + file.name} />
    : <span className="capture-file-fallback" aria-hidden="true">Ảnh</span>;
}

export function CaptureScreen({ csrf }: { csrf: string }) {
  const [shared, setShared] = useState(readSharedCapture);
  const [text, setText] = useState(shared.kind === 'link' ? shared.annotation : shared.note);
  const [sharedUrl, setSharedUrl] = useState(shared.kind === 'link' ? shared.url : '');
  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([]);
  const filesRef = useRef<PendingFile[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [owner, setOwner] = useState<string>();
  const ownerRef = useRef<string | undefined>(undefined);
  const ownerReady = useRef<Promise<void> | null>(null);
  const dirty = useRef(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string>();
  const [receipt, setReceipt] = useState<Receipt>();
  const [uploadReceipts, setUploadReceipts] = useState<CompletedFile[]>([]);
  const [ackMs, setAckMs] = useState<number>();
  const [lastSend, setLastSend] = useState<PreviousSend>();
  const inFlight = useRef(false);
  const attempt = useRef<{ body: string; key: string } | null>(null);
  const recent = useResource<Page<Capture>>('/captures?limit=5');

  useEffect(() => {
    if (!shared.shared) return;
    const page = new URL(window.location.href);
    for (const key of ['shared_title', 'shared_text', 'shared_url']) page.searchParams.delete(key);
    window.history.replaceState(null, '', page.href);
  }, [shared.shared]);

  useEffect(() => {
    let active = true;
    ownerReady.current = request<Session>('/session').then(session => {
      if (!active || !session.authenticated || !session.username) return;
      ownerRef.current = session.username;
      setOwner(session.username);
      const draft = readCaptureDraft(session.username);
      if (!shared.shared && !dirty.current && draft) {
        setText(draft.kind === 'link' ? draft.annotation : draft.note);
        setSharedUrl(draft.kind === 'link' ? draft.url : '');
        attempt.current = draft.attempt;
        const restored = readCaptureFiles(session.username);
        filesRef.current = restored;
        setPendingFiles(restored);
      }
    }).catch(() => { /* Authentication UI handles expired sessions. */ });
    return () => { active = false; };
  }, []);

  const decision = detectInboxInput(text, sharedUrl);

  function persistDraft(items = filesRef.current) {
    const user = ownerRef.current;
    if (!user) return;
    if (!text && !sharedUrl && !items.length && !attempt.current) {
      clearCaptureDraft(user);
      return;
    }
    const current = detectInboxInput(text, sharedUrl);
    saveCaptureDraft(user, {
      kind: items.length ? 'file' : current.kind,
      url: current.kind === 'link' ? current.url : '',
      note: current.kind === 'text' || items.length ? text : '',
      annotation: current.kind === 'link' ? current.text : '',
      shared: shared.shared,
      attempt: attempt.current,
    });
    saveCaptureFiles(user, items);
  }

  useEffect(() => { persistDraft(); }, [owner, text, sharedUrl, pendingFiles, shared.shared]);

  function markChanged() {
    dirty.current = true;
    attempt.current = null;
    setReceipt(undefined);
    setUploadReceipts([]);
    setError(undefined);
  }

  function onTextChange(value: string) {
    markChanged();
    setText(value);
    // A changed file caption is an intentional new request; never re-use the
    // old key for an altered payload after an ambiguous server acknowledgement.
    if (filesRef.current.length) {
      const updated = filesRef.current.map(row => ({ ...row, key: requestKey(), caption: value }));
      filesRef.current = updated;
      setPendingFiles(updated);
    }
  }

  function addFiles(incoming: File[]) {
    if (!incoming.length) return;
    const problem = validateInboxFiles(incoming, filesRef.current.length);
    if (problem) { setError(problem); return; }
    markChanged();
    const rows = incoming.map(file => ({ file, key: requestKey(), caption: text }));
    filesRef.current = [...filesRef.current, ...rows];
    setPendingFiles([...filesRef.current]);
  }

  function removeFile(key: string) {
    if (inFlight.current) return;
    markChanged();
    filesRef.current = filesRef.current.filter(row => row.key !== key);
    setPendingFiles([...filesRef.current]);
  }

  function handlePaste(event: ClipboardEvent<HTMLTextAreaElement>) {
    const files = Array.from(event.clipboardData?.items ?? [])
      .filter(item => item.kind === 'file')
      .map(item => item.getAsFile()).filter((file): file is File => !!file);
    if (!files.length) return; // Let the browser paste text/URLs normally.
    event.preventDefault();
    addFiles(files);
  }

  function handleDrop(event: DragEvent<HTMLElement>) {
    setDragging(false);
    const files = Array.from(event.dataTransfer?.files ?? []);
    if (!files.length) return; // Preserve ordinary text drag and drop.
    event.preventDefault();
    addFiles(files);
  }

  function errorForUpload(reason: unknown) {
    const status = reason instanceof ApiError ? reason.status : 0;
    if (status === 401) return 'Chưa xác nhận tiếp nhận. Đăng nhập lại rồi gửi lại tệp đang chờ.';
    if (status === 403) return 'Chưa tiếp nhận. Kiểm tra quyền hoặc phiên đăng nhập rồi thử lại.';
    if (status === 413) return 'Tệp được lớn tối đa 128 MiB.';
    if (status === 400 || status === 422) return 'Chưa tiếp nhận. Kiểm tra tệp hoặc chú thích.';
    return 'Chưa xác nhận tệp đã được tiếp nhận. Gửi lại với cùng mã lượt gửi.';
  }

  async function sendFiles() {
    if (!filesRef.current.length) return;
    const started = Date.now();
    setSaving(true);
    inFlight.current = true;
    setError(undefined);
    // Preserve receipts for files acknowledged before a partial batch failure.
    // The next retry only sends files that remain in the pending queue.
    await ownerReady.current;
    persistDraft();
    try {
      // Each original file is its own Item in the existing upload API. A note
      // typed in the single composer is saved on that same Item.
      while (filesRef.current.length) {
        const row = filesRef.current[0];
        const form = new FormData();
        form.append('file', row.file);
        form.append('note', row.caption);
        let received: UploadReceipt;
        try {
          received = await request<UploadReceipt>('/uploads', {
            method: 'POST', csrf, body: form, idempotencyKey: row.key, timeoutMs: fileTimeout,
          });
        } catch (reason) {
          setError(row.file.name + ': ' + errorForUpload(reason));
          persistDraft();
          return;
        }
        setUploadReceipts(previous => [...previous, {
          filename: row.file.name, itemId: received.item_id, assetId: received.asset_id,
          state: received.state,
        }]);
        setAckMs(Math.max(0, Date.now() - started));
        filesRef.current = filesRef.current.slice(1);
        setPendingFiles([...filesRef.current]);
        persistDraft();
      }
      setText('');
      setSharedUrl('');
      attempt.current = null;
      if (ownerRef.current) clearCaptureDraft(ownerRef.current);
      recent.retry();
    } finally {
      inFlight.current = false;
      setSaving(false);
    }
  }

  async function sendText() {
    if (decision.kind === 'link' && (Array.from(decision.url).length > 4096)) {
      setError('Liên kết được dài tối đa 4.096 ký tự.');
      return;
    }
    const content = decision.text;
    if (decision.kind === 'text' && !content.trim()) {
      setError('Dán một liên kết hoặc nhập văn bản, hoặc chọn tệp/ảnh.');
      return;
    }
    if (Array.from(content).length > 65_536) {
      setError('Nội dung được dài tối đa 65.536 ký tự.');
      return;
    }
    if (content.includes('\0')) {
      setError('Nội dung chứa ký tự không hợp lệ; bản nháp vẫn được giữ.');
      return;
    }
    const body = decision.kind === 'link'
      ? { kind: 'link', source_channel: shared.shared ? 'share' : 'web', url: decision.url, text: content }
      : { kind: 'text', source_channel: shared.shared ? 'share' : 'web', text: content };
    const signature = JSON.stringify(body);
    if (!attempt.current || attempt.current.body !== signature) {
      attempt.current = { body: signature, key: requestKey() };
    }
    const started = Date.now();
    setSaving(true);
    inFlight.current = true;
    setError(undefined);
    setReceipt(undefined);
    await ownerReady.current;
    persistDraft();
    try {
      const received = await request<Receipt>('/captures', {
        method: 'POST', csrf, body, idempotencyKey: attempt.current.key,
      });
      setReceipt(received);
      setAckMs(Math.max(0, Date.now() - started));
      setLastSend({ kind: decision.kind, url: decision.kind === 'link' ? decision.url : '', text: content });
      attempt.current = null;
      setText('');
      setSharedUrl('');
      if (ownerRef.current) clearCaptureDraft(ownerRef.current);
      recent.retry();
    } catch (reason) {
      const status = reason instanceof ApiError ? reason.status : undefined;
      setError(status === 401 ? 'Chưa xác nhận tiếp nhận. Đăng nhập lại rồi gửi lại cùng lượt gửi.'
        : status === 403 ? 'Chưa tiếp nhận. Kiểm tra quyền hoặc phiên đăng nhập rồi thử lại.'
          : status === 400 || status === 422 ? 'Chưa tiếp nhận. Kiểm tra liên kết hoặc văn bản.'
            : 'Chưa xác nhận tiếp nhận. Gửi lại với cùng mã lượt gửi.');
    } finally {
      inFlight.current = false;
      setSaving(false);
    }
  }

  async function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (inFlight.current) return;
    if (filesRef.current.length) await sendFiles();
    else await sendText();
  }

  function clearDraft() {
    if (inFlight.current) return;
    dirty.current = true;
    attempt.current = null;
    filesRef.current = [];
    setPendingFiles([]);
    setText('');
    setSharedUrl('');
    setShared(value => ({ ...value, shared: false }));
    setError(undefined);
    setReceipt(undefined);
    setUploadReceipts([]);
    if (ownerRef.current) clearCaptureDraft(ownerRef.current);
  }

  const inputLabel = pendingFiles.length
    ? pendingFiles.length + ' tệp/ảnh đang chờ gửi' : decision.kind === 'link'
      ? 'Đã nhận dạng liên kết' : text.trim() ? 'Đã nhận dạng văn bản' : 'Chờ nội dung';
  const hasContent = Boolean(text || sharedUrl || pendingFiles.length);

  return <>
    <PageTitle title="Gửi vào kho" description="Một ô cho mọi nguồn: dán link, viết ghi chú, dán ảnh, kéo-thả hoặc chọn tài liệu." />
    <div className="split-view">
      <section className="panel capture-compose" aria-labelledby="compose-title">
        <h2 id="compose-title">Thêm vào Kho Tri Thức</h2>
        <p className="capture-intro">Hệ thống tự nhận dạng cách tiếp nhận; bạn không cần chọn loại tài liệu trước.</p>
        <form className="form-stack" onSubmit={submit}>
          <div className={'capture-unified-box' + (dragging ? ' is-dragging' : '')}
            onDragOver={event => { if (event.dataTransfer?.types.includes('Files')) { event.preventDefault(); setDragging(true); } }}
            onDragLeave={event => { if (!event.currentTarget.contains(event.relatedTarget as Node)) setDragging(false); }}
            onDrop={handleDrop}>
            <label className="capture-unified-label" htmlFor="capture-input">Nhập hoặc thả nội dung vào đây</label>
            {sharedUrl && <div className="capture-share-source">
              <span className="capture-file-label">Liên kết đã chia sẻ: <span>{sharedUrl}</span></span>
              <button type="button" disabled={saving} aria-label="Bỏ liên kết đã chia sẻ" onClick={() => { markChanged(); setSharedUrl(''); }}>Bỏ link</button>
            </div>}
            <textarea id="capture-input" className="capture-unified-input" value={text}
              onChange={event => onTextChange(event.currentTarget.value)}
              onPaste={handlePaste} disabled={saving} autoFocus rows={6}
              aria-label="Văn bản, liên kết hoặc chú thích cho tệp và ảnh"
              aria-describedby="capture-input-hint"
              placeholder={'Dán một link YouTube, TikTok, trang web…\nHoặc nhập nội dung Markdown, dán ảnh Ctrl+V.\nKéo tệp, ảnh, PDF, Word, Excel vào cùng ô này.'} />
            <input ref={inputRef} className="capture-file-input" type="file" multiple
              aria-label="Chọn ảnh hoặc tài liệu" disabled={saving}
              onChange={event => {
                addFiles(Array.from(event.currentTarget.files ?? []));
                event.currentTarget.value = '';
              }} />
            {pendingFiles.length > 0 && <ul className="capture-file-list" aria-label="Danh sách tệp đã chọn">
              {pendingFiles.map(row => <li key={row.key} className="capture-file-row">
                {inboxFileKind(row.file) === 'image' ? <LocalImage file={row.file} />
                  : <span className="capture-file-fallback" aria-hidden="true">Tệp</span>}
                <span className="capture-file-info"><strong>{row.file.name || 'Ảnh từ bộ nhớ tạm'}</strong>
                  <small>{(row.file.size / 1024 / 1024).toFixed(2)} MiB · {inboxFileKind(row.file) === 'image' ? 'Ảnh' : inboxFileKind(row.file) === 'video' ? 'Video' : inboxFileKind(row.file) === 'audio' ? 'Âm thanh' : 'Tài liệu'}</small>
                </span>
                <button type="button" disabled={saving} aria-label={'Bỏ tệp ' + row.file.name}
                  onClick={() => removeFile(row.key)}>Bỏ</button>
              </li>)}
            </ul>}
            <div className="capture-unified-tools">
              <button type="button" disabled={saving} className="capture-pick-button" onClick={() => inputRef.current?.click()}>
                <span aria-hidden="true">＋</span> Chọn ảnh / tệp
              </button>
              <span className="capture-detected" role="status">{inputLabel}</span>
            </div>
          </div>
          <p className="capture-hint" id="capture-input-hint">Có thể Ctrl+V ảnh chụp màn hình, thả nhiều tệp hoặc dán một liên kết. Tối đa 10 tệp/lượt, 128 MiB/tệp. Nếu gửi nhiều tệp, mỗi tệp tạo một mục riêng và dùng chung phần ghi chú đã nhập.</p>
          {error && <ErrorNotice>{error}</ErrorNotice>}
          <div className="form-actions">
            <Button type="submit" loading={saving} disabled={!hasContent}>
              {saving ? 'Đang gửi…' : pendingFiles.length ? 'Gửi ' + pendingFiles.length + ' tệp vào kho' : 'Gửi vào kho'}
            </Button>
            <Button type="button" variant="subtle" disabled={saving || !hasContent} onClick={clearDraft}>Xóa bản nháp</Button>
          </div>
          <small>{owner ? 'Bản nháp trong tab này được giữ cho tài khoản hiện tại khi cần đăng nhập lại. ' : ''}
            Chỉ biên nhận xác nhận máy chủ đã nhận. Tệp chưa được xác minh trên Drive cho tới khi xử lý hoàn tất;
            phân loại dựa vào nội dung trích xuất hoặc chữ/tên tệp, không phải OCR ảnh. Đóng hẳn tab có thể mất bản nháp.</small>
        </form>
        {receipt && <div className="receipt" role="status">
          <p>Đã tiếp nhận lúc <ServerTime value={receipt.received_at} /></p>
          <p>Lượt gửi: {receipt.capture_id}</p>
          <p>Độ trễ biên nhận: {ackMs} ms (đo tại trình duyệt).</p>
          {lastSend?.kind === 'link' && <p>Liên kết đã được tiếp nhận. Tải nguồn và phân loại sẽ diễn ra sau.</p>}
          <a href={itemHref(receipt.item_id)}>Mở mục trong thư viện</a>
          {lastSend && <Button type="button" variant="subtle" disabled={saving} onClick={() => {
            markChanged();
            if (lastSend.kind === 'link') {
              setSharedUrl(lastSend.url); setText(lastSend.text);
            } else { setSharedUrl(''); setText(lastSend.text); }
            setReceipt(undefined);
          }}>Dùng lại nội dung</Button>}
        </div>}
        {uploadReceipts.length > 0 && <div className="receipt" role="status">
          <p>Máy chủ đã tiếp nhận {uploadReceipts.length} tệp để xử lý.</p>
          {ackMs !== undefined && <p>Thời gian tới biên nhận cuối: {ackMs} ms.</p>}
          <p>Chưa xác nhận các tệp đã được lưu và kiểm tra trên Drive.</p>
          <ul>{uploadReceipts.map(row => <li key={row.assetId}>
            {row.filename}: <a href={itemHref(row.itemId)}>Mở mục</a>
          </li>)}</ul>
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
    <ResearchClipper csrf={csrf} />
  </>;
}
