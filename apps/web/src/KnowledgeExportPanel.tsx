import { Button, Select } from '@mantine/core';
import { useRef, useState } from 'react';
import { ApiError, externalHttpUrl, request } from './api';
import { ErrorNotice, Loading, ServerTime, useResource } from './views';

type ExportStatus = {
  enabled: boolean; format: 'markdown' | 'text'; status: string; stale: boolean;
  source_version: string; exported_version: string; truncated: boolean;
  last_error: string; last_synced_at: string | null; url: string | null;
};
const labels: Record<string, string> = {
  disabled: 'Đang tắt', pending: 'Đang chờ đồng bộ', synced: 'Đã đồng bộ',
  stale: 'Cần cập nhật', failed: 'Chưa đồng bộ được',
};

export function KnowledgeExportPanel({ id, csrf, deleted, refreshKey }: {
  id: string; csrf: string; deleted: boolean; refreshKey: string;
}) {
  const path = `/items/${encodeURIComponent(id)}/knowledge-export`;
  const resource = useResource<ExportStatus>(path, { refreshKey, pollWhile: (data) => data.status === 'pending' });
  const [formatChoice, setFormat] = useState<'markdown' | 'text'>();
  const [busy, setBusy] = useState(false);
  const inFlight = useRef(false);
  const [error, setError] = useState('');
  const data = resource.data;
  const format = formatChoice ?? data?.format ?? 'markdown';
  const url = data?.url && externalHttpUrl(data.url);

  async function update(enabled: boolean, retry = false) {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    setError('');
    try {
      const result = await request<ExportStatus>(path + (retry ? '/retry' : ''), {
        method: 'POST', csrf, ...(retry ? {} : { body: { enabled, format } }),
      });
      resource.replace(result);
      setFormat(undefined);
    } catch (problem) {
      setError(problem instanceof ApiError && problem.status === 409
        ? 'Pilot cho phép tối đa 10 mục đang bật. Tắt một bản xuất trước khi thêm mục khác.'
        : 'Chưa lưu được yêu cầu. Kiểm tra kết nối rồi thử lại.');
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }

  return <section className="panel" aria-labelledby="knowledge-export-title">
    <h2 id="knowledge-export-title">Bản xuất tri thức</h2>
    <p className="muted">Bật riêng cho mục này để lưu ghi chú, nhóm, nguồn và văn bản đã trích vào thư mục ChatGPT_Index trên Drive. Tối đa 10 mục trong pilot.</p>
    <p className="muted">Khả năng ChatGPT tìm và đọc bản xuất vẫn cần kiểm thử. Video chưa có transcript sẽ được ghi rõ.</p>
    {resource.error ? <ErrorNotice retry={resource.retry}>Chưa tải được trạng thái bản xuất.</ErrorNotice>
      : !data ? <Loading /> : <div className="form-stack">
        <dl className="status-list">
          <div><dt>Trạng thái</dt><dd>{labels[data.status] ?? 'Chưa xuất'}</dd></div>
          {data.last_synced_at && <div><dt>Đồng bộ lần cuối</dt><dd><ServerTime value={data.last_synced_at} /></dd></div>}
        </dl>
        {data.stale && <p className="notice" role="status">Bản trên Drive chưa theo kịp dữ liệu nguồn. Chọn đồng bộ lại nếu cần.</p>}
        {data.truncated && <p className="notice">Nội dung dài: bản xuất có giới hạn, cần mở nguồn để đọc đầy đủ.</p>}
        {data.last_error === 'knowledge_sensitive_input' && <ErrorNotice>Phát hiện chuỗi giống thông tin đăng nhập. Đã chặn xuất; kiểm tra lại nội dung trước khi thử lại.</ErrorNotice>}
        {data.last_error && data.last_error !== 'knowledge_sensitive_input' && <ErrorNotice>Chưa đồng bộ được. Kiểm tra kết nối Drive trong Cài đặt rồi thử lại.</ErrorNotice>}
        <Select label="Định dạng bản xuất" value={format} allowDeselect={false} disabled={busy || deleted}
          data={[{ value: 'markdown', label: 'Markdown (.md)' }, { value: 'text', label: 'Văn bản (.txt)' }]}
          onChange={(value) => { if (value === 'markdown' || value === 'text') setFormat(value); }} />
        <div className="item-actions">
          {!deleted && (!data.enabled || format !== data.format) && <Button variant="default" loading={busy} onClick={() => void update(true)}>{data.enabled ? 'Lưu định dạng' : 'Bật xuất tri thức'}</Button>}
          {data.enabled && !deleted && <Button variant="default" disabled={busy} onClick={() => void update(true, true)}>Đồng bộ lại</Button>}
          {data.enabled && <Button variant="subtle" disabled={busy} onClick={() => void update(false)}>Tắt và thu hồi bản xuất</Button>}
          {url && <a href={url} target="_blank" rel="noopener noreferrer">Mở bản trên Drive</a>}
        </div>
        {resource.pollingPaused && <Button variant="subtle" onClick={resource.retry}>Kiểm tra trạng thái</Button>}
      </div>}
    {error && <ErrorNotice>{error}</ErrorNotice>}
    {resource.refreshError && <ErrorNotice retry={resource.retry}>Chưa cập nhật được trạng thái mới.</ErrorNotice>}
  </section>;
}
