import { Button, Checkbox, FileInput, Group, ScrollArea } from '@mantine/core';
import { useRef, useState } from 'react';
import './KnowledgeVaultPanel.css';

type Row = {
  item_id: string; title: string; status: 'new' | 'update' | 'unchanged' | 'conflict';
  reason: string; edited_markdown: boolean; version: number;
  before: string | null; after: string;
};
type Preview = {
  receipt: string; rows: Row[]; more_count: number;
  counts: Record<string, number>; media_missing: number;
  metadata: Record<string, number>; warnings: string[];
};
type Applied = {
  state: string; created: number; updated: number; events_created: number;
  assets_created: number; media_verified: number;
};
const labels = {
  new: 'Thêm mới', update: 'Cập nhật', unchanged: 'Không đổi', conflict: 'Xung đột',
};
const maximum = 32 * 1024 * 1024;

export function KnowledgeVaultPanel({ csrf }: { csrf: string }) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [applied, setApplied] = useState<Applied | null>(null);
  const lock = useRef(false);

  function reset(next: File | null) {
    setFile(next); setPreview(null); setSelected([]); setApplied(null); setError('');
  }

  async function call(path: string, body: FormData): Promise<Response> {
    const response = await fetch('/api/v1/vault/' + path, {
      method: 'POST', credentials: 'same-origin', cache: 'no-store',
      headers: { 'X-CSRFToken': csrf, Accept: 'application/json' }, body,
    });
    if (!response.ok) throw Error('HTTP ' + response.status);
    return response;
  }

  async function showPreview() {
    if (!file || lock.current) return;
    lock.current = true; setBusy(true); setError(''); setApplied(null);
    try {
      if (file.size > maximum) throw Error('vault_archive_limit');
      const form = new FormData(); form.set('file', file);
      const data = await (await call('import/preview', form)).json() as Preview;
      if (!Array.isArray(data.rows) || typeof data.receipt !== 'string') throw Error('invalid_preview');
      setPreview(data);
      setSelected(data.rows.filter((row) => row.status === 'new' || row.status === 'update').map((row) => row.item_id));
    } catch {
      setPreview(null); setSelected([]);
      setError('Không đọc được ZIP. Kiểm tra giới hạn 32 MB, phiên đăng nhập hoặc nội dung tệp.');
    } finally { lock.current = false; setBusy(false); }
  }

  async function apply() {
    if (!file || !preview || !selected.length || lock.current) return;
    lock.current = true; setBusy(true); setError('');
    try {
      const form = new FormData();
      form.set('file', file); form.set('receipt', preview.receipt);
      form.set('selected', JSON.stringify(selected));
      const data = await (await call('import', form)).json() as Applied;
      setApplied(data); setPreview(null); setSelected([]);
    } catch {
      setError('Không thể nhập. Dữ liệu hoặc phiên duyệt có thể đã thay đổi; xem trước lại, không có thay đổi một phần.');
      setPreview(null); setSelected([]);
    } finally { lock.current = false; setBusy(false); }
  }

  async function exportZip() {
    if (lock.current) return;
    lock.current = true; setBusy(true); setError('');
    try {
      const response = await fetch('/api/v1/vault/export', {
        credentials: 'same-origin', cache: 'no-store', headers: { Accept: 'application/zip' },
      });
      if (!response.ok) throw Error('HTTP ' + response.status);
      const blob = await response.blob();
      if (blob.size > maximum) throw Error('vault_archive_limit');
      const objectUrl = URL.createObjectURL(blob);
      try {
        const anchor = document.createElement('a');
        anchor.href = objectUrl;
        anchor.download = 'kho-tri-thuc-vault.zip';
        document.body.append(anchor); anchor.click(); anchor.remove();
      } finally { URL.revokeObjectURL(objectUrl); }
    } catch {
      setError('Chưa tạo được bản xuất. Kiểm tra kết nối, dung lượng hoặc thông tin nhạy cảm.');
    } finally { lock.current = false; setBusy(false); }
  }

  const eligible = preview?.rows.filter((row) => row.status === 'new' || row.status === 'update') ?? [];
  return <section className="vault-panel" aria-labelledby="vault-title">
    <h2 id="vault-title">Kho Markdown di động (KT127)</h2>
    <p>Xuất một tệp Markdown cho mỗi ghi chú, giữ UUID, thời gian nhận, thư mục, quan hệ cha–con và lối tắt trong manifest. ZIP không chứa tệp media gốc, Drive ID hay khóa truy cập.</p>
    <p>Đây là gói di chuyển tri thức, <strong>không thay thế backup PostgreSQL hoặc Google Drive</strong>. Chỉ nhập sau khi xem trước và chọn từng mục.</p>
    <Group align="end" gap="sm" wrap="wrap">
      <Button onClick={() => void exportZip()} disabled={busy}>Xuất Markdown Vault (.zip)</Button>
      <FileInput label="Chọn ZIP để xem trước" accept=".zip,application/zip" value={file}
        onChange={reset} clearable disabled={busy} />
      <Button variant="default" disabled={!file || busy} onClick={() => void showPreview()}>Xem trước nhập</Button>
    </Group>
    {error && <p className="vault-error" role="alert">{error}</p>}
    {applied && <p role="status">Đã nhập: {applied.created} mục mới, {applied.updated} mục cập nhật, {applied.events_created} lượt tiếp nhận lịch sử. Media xác minh: {applied.media_verified}.</p>}
    {preview && <div className="vault-preview">
      <h3>Đối chiếu trước khi nhập</h3>
      <p role="status">Thêm {preview.counts.new ?? 0} · Cập nhật {preview.counts.update ?? 0} · Không đổi {preview.counts.unchanged ?? 0} · Xung đột {preview.counts.conflict ?? 0}</p>
      <p>Media metadata không kèm tệp: {preview.media_missing}.</p>
      {preview.warnings.map((warning) => <p className="vault-warning" key={warning}>{warning}</p>)}
      {preview.more_count > 0 && <p className="vault-warning">Còn {preview.more_count} mục chưa hiển thị; không thể chọn từng mục ngoài danh sách. Chia nhỏ gói để nhập toàn bộ.</p>}
      <ScrollArea h={350} type="auto"><ul className="vault-entries">
        {preview.rows.map((row) => <li key={row.item_id}>
          <Checkbox label={row.title + ' · ' + labels[row.status]}
            disabled={busy || !['new', 'update'].includes(row.status)}
            checked={selected.includes(row.item_id)}
            onChange={(event) => {
              setSelected((previous) => event.currentTarget.checked
                ? [...previous, row.item_id]
                : previous.filter((id) => id !== row.item_id));
            }} />
          <small>{row.item_id}{row.edited_markdown ? ' · Markdown đã sửa' : ''}{row.reason ? ' · ' + row.reason : ''}</small>
          {row.status === 'update' && <details>
            <summary>So sánh trước / sau (320 ký tự đầu)</summary>
            <div className="vault-diff"><div><b>Trước</b><pre>{row.before}</pre></div><div><b>Sau</b><pre>{row.after}</pre></div></div>
          </details>}
        </li>)}
      </ul></ScrollArea>
      <Group mt="sm">
        <Button variant="default" disabled={busy} onClick={() => setSelected(eligible.map((row) => row.item_id))}>Chọn mục hợp lệ</Button>
        <Button variant="default" disabled={busy} onClick={() => setSelected([])}>Bỏ chọn</Button>
        <Button color="red" disabled={busy || !selected.length} onClick={() => void apply()}>Xác nhận nhập {selected.length} mục</Button>
      </Group>
    </div>}
  </section>;
}
