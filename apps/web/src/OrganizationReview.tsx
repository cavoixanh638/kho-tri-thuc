import { Button } from '@mantine/core';
import { useCallback, useEffect, useState } from 'react';
import { request } from './api';
import './OrganizationReview.css';

type Kind = 'topic' | 'project' | 'tag';
type Proposal = { kind: Kind; group_id: number; group_name: string; field: string; excerpt: string; processor: string; processor_version: string; confidence: number; method_version: string; source_version: string; receipt: string };
type Existing = { kind: Kind; group_id: number; group_name: string; origin: string; user_pinned: boolean; receipt: string };
type ReviewPage = { evidence_status: 'available' | 'metadata_only' | 'missing_text'; current: Existing[]; proposals: Proposal[]; confidence_note: string };
type Result = { state: string; writes: number; undo_receipt?: string };
const labels: Record<Kind, string> = { topic: 'Chủ đề', tag: 'Nhãn', project: 'Dự án' };

export function OrganizationReview({ id, csrf, refreshKey, onSaved }: { id: string; csrf: string; refreshKey?: string | number; onSaved?: () => void }) {
  const [page, setPage] = useState<ReviewPage>();
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [undoReceipt, setUndoReceipt] = useState<string>();

  const reload = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    try {
      const response = await request<ReviewPage>('/items/' + encodeURIComponent(id) + '/organization-review', { signal });
      if (!signal?.aborted) { setPage(response); setError(''); }
    } catch {
      if (!signal?.aborted) setError('Không tải được chứng cứ. Hãy thử lại.');
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    const controller = new AbortController();
    setPage(undefined);
    setUndoReceipt(undefined);
    void reload(controller.signal);
    return () => controller.abort();
  }, [reload, refreshKey]);

  async function act(receipt: string, action: 'accept' | 'pin' | 'reject' | 'undo') {
    if (busy) return;
    setBusy(true);
    setError('');
    setUndoReceipt(undefined);
    try {
      const response = await request<Result>('/items/' + encodeURIComponent(id) + '/organization-review/' + action, {
        method: 'POST', body: { receipt }, csrf,
      });
      setUndoReceipt(response.undo_receipt);
      setMessage(action === 'accept' ? 'Đã áp dụng phân loại.' :
        action === 'pin' ? 'Đã cố định nhóm.' :
        action === 'reject' ? 'Đã bỏ qua trong phiên này.' : 'Đã hoàn tác.');
      await reload();
      onSaved?.();
    } catch {
      setError('Không thực hiện được. Chứng cứ hoặc nhóm có thể đã thay đổi. Hãy tải lại.');
    } finally {
      setBusy(false);
    }
  }

  return <section className="panel org-review" aria-labelledby="org-review-title">
    <div className="panel-heading">
      <h2 id="org-review-title">Duyệt phân loại</h2>
      <Button variant="default" size="compact-sm" disabled={busy || loading} onClick={() => void reload()}>Làm mới</Button>
    </div>
    <p>Đề xuất dựa trên nhóm đã có và chứng cứ văn bản, không gọi AI hoặc tự sửa ghi chú.</p>
    {loading && <p role="status">Đang tải chứng cứ…</p>}
    {error && <p role="alert" className="org-review-error">{error}</p>}
    {page && <>
      <h3>Đang ở / Người dùng cố định</h3>
      {page.current.length === 0 ? <p>Chưa có nhóm.</p> : <ul className="org-review-list">
        {page.current.map((entry) => <li key={entry.kind + entry.group_id}>
          <div><strong>{labels[entry.kind]}: {entry.group_name}</strong>
            <div className="org-review-meta">{entry.user_pinned ? 'Người dùng cố định' : entry.origin === 'auto' ? 'Tự xếp' : 'Đã áp dụng'}</div>
          </div>
          {!!entry.receipt && <Button variant="default" size="compact-sm" disabled={busy} onClick={() => void act(entry.receipt, 'pin')}>Cố định</Button>}
        </li>)}
      </ul>}
      <h3>Được hệ thống đề xuất</h3>
      {page.evidence_status !== 'available' && <p role="status">{page.evidence_status === 'missing_text'
        ? 'Thiếu văn bản làm chứng cứ; không suy nội dung của video hoặc tệp.'
        : 'Chỉ có metadata; cần kiểm chứng nội dung nguồn.'}</p>}
      {page.proposals.length === 0 ? <p>Không có đề xuất đủ chứng cứ.</p> : <ul className="org-review-list">
        {page.proposals.map((p) => <li key={p.kind + p.group_id}>
          <div><strong>{labels[p.kind]}: {p.group_name}</strong>
            <blockquote>{p.excerpt}</blockquote>
            <div className="org-review-meta">Nguồn: {p.field} · {p.processor} {p.processor_version} · Điểm quy tắc: {p.confidence.toFixed(2)}</div>
            <div className="org-review-meta">Phương pháp: {p.method_version} · Phiên bản: {p.source_version.slice(0, 12)}…</div>
          </div>
          <div className="org-review-actions">
            <Button size="compact-sm" disabled={busy} onClick={() => void act(p.receipt, 'accept')}>Áp dụng</Button>
            <Button variant="default" size="compact-sm" disabled={busy} onClick={() => void act(p.receipt, 'pin')}>Cố định</Button>
            <Button variant="subtle" size="compact-sm" disabled={busy} onClick={() => void act(p.receipt, 'reject')}>Bỏ qua</Button>
          </div>
        </li>)}
      </ul>}
      <p className="org-review-meta">{page.confidence_note} Bỏ qua chỉ áp dụng cho phiên đăng nhập hiện tại.</p>
    </>}
    {message && <p role="status">{message}</p>}
    {undoReceipt && <Button variant="default" disabled={busy} onClick={() => void act(undoReceipt, 'undo')}>Hoàn tác</Button>}
  </section>;
}
