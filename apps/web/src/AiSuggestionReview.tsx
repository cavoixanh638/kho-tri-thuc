import { useEffect, useRef, useState } from 'react';
import { request, ApiError } from './api';
import { AiSuggestionDiff } from './AiSuggestionDiff';
import './AiSuggestionReview.css';

export type NoteSuggestion = {
  item_id: string; source_version: string; base_edit_version: number; before: string; after: string;
  receipt: string; expires_in: number; provenance: { provider: string; model: string; method: string; prompt_version: string };
};
export type AppliedSuggestion = { note: string; edit_version: number; source_version: string; undo_receipt: string };

export function AiSuggestionReview({ suggestion, csrf, currentNote, onApplied, onClose, disabled = false, onBusyChange }: {
  suggestion: NoteSuggestion; csrf: string; currentNote: string;
  onApplied: (result: AppliedSuggestion) => void; onClose: () => void;
  disabled?: boolean; onBusyChange?: (busy: boolean) => void;
}) {
  const [state, setState] = useState<'preview' | 'accepted' | 'rejected' | 'undone'>('preview');
  const [applied, setApplied] = useState<AppliedSuggestion>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const inFlight = useRef(false);
  const activeReceipt = useRef(suggestion.receipt);
  activeReceipt.current = suggestion.receipt;
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  const staleDraft = state === 'preview' && currentNote !== suggestion.before;
  useEffect(() => { setState('preview'); setApplied(undefined); setError(''); }, [suggestion.receipt]);

  async function act(action: 'accept' | 'reject' | 'undo') {
    if (inFlight.current || (action !== 'reject' && disabled) || (action === 'accept' && staleDraft)) return;
    inFlight.current = true; setBusy(true); setError('');
    onBusyChange?.(true);
    const requestReceipt = suggestion.receipt;
    try {
      const result = await request<AppliedSuggestion>(`/items/${encodeURIComponent(suggestion.item_id)}/suggestions/${action}`, { method: 'POST', csrf, body: { receipt: action === 'undo' ? applied?.undo_receipt : suggestion.receipt } });
      if (!mounted.current || activeReceipt.current !== requestReceipt) return;
      if (action === 'reject') setState('rejected');
      else { setApplied(result); setState(action === 'accept' ? 'accepted' : 'undone'); onApplied(result); }
    } catch (reason) {
      if (!mounted.current || activeReceipt.current !== requestReceipt) return;
      setError(reason instanceof ApiError && reason.status === 409 ? 'Bài hoặc nguồn đã thay đổi. Giữ nguyên bản hiện tại và tạo lại đề xuất.' : 'Chưa xác nhận được thao tác. Giữ bản hiện tại và tải lại trạng thái trước khi thử tiếp.');
    } finally { inFlight.current = false; onBusyChange?.(false); if (mounted.current) setBusy(false); }
  }

  return <section className="ai-suggestion-review" aria-label="Duyệt đề xuất chỉnh sửa">
    <h2>Duyệt đề xuất chỉnh sửa</h2>
    <p>Đề xuất được giữ riêng. Chỉ thay văn bản sau khi bạn chọn Chấp nhận và phiên bản còn khớp.</p>
    <p className="ai-suggestion-meta">{suggestion.provenance.provider === 'none' ? 'PoC không có nhà cung cấp AI; nội dung thử do người dùng cung cấp.' : `Nguồn: ${suggestion.provenance.provider} · ${suggestion.provenance.model}`} Phiên bản bài: {suggestion.base_edit_version}.</p>
    <AiSuggestionDiff before={suggestion.before} after={suggestion.after} />
    {staleDraft && <p role="alert">Bản nháp đang khác lúc tạo đề xuất. Hãy giữ bản nháp và tạo lại đề xuất.</p>}
    {error && <p role="alert">{error}</p>}
    {state === 'preview' && <div className="ai-suggestion-actions">
      <button type="button" disabled={busy || disabled || staleDraft || suggestion.before === suggestion.after} onClick={() => void act('accept')}>Chấp nhận</button>
      <button type="button" disabled={busy} onClick={() => void act('reject')}>Từ chối</button>
      <button type="button" disabled={busy} onClick={onClose}>Hủy xem</button>
    </div>}
    {state === 'accepted' && <div className="ai-suggestion-actions"><p role="status">Đã áp dụng đề xuất.</p><button type="button" disabled={busy || disabled || !applied?.undo_receipt} onClick={() => void act('undo')}>Hoàn tác đề xuất</button></div>}
    {state === 'rejected' && <p role="status">Đã từ chối. Nội dung bài không đổi.</p>}
    {state === 'undone' && <p role="status">Đã hoàn tác về văn bản trước đề xuất.</p>}
  </section>;
}
