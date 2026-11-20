import { Button, Textarea } from '@mantine/core';
import { useEffect, useRef, useState } from 'react';
import { ApiError, request, type Item } from './api';
import { AiSuggestionReview, type AppliedSuggestion, type NoteSuggestion } from './AiSuggestionReview';

type Capabilities = { enabled: boolean; provider_configured: boolean; mode: string };

/** Opt-in manual review host. No provider, automatic generation or background writes. */
export function ItemSuggestionPanel({ item, csrf, editing, draftDirty, onUpdated, onBusyChange }: {
  item: Item; csrf: string; editing: boolean; draftDirty: boolean;
  onUpdated: (item: Item) => void; onBusyChange?: (busy: boolean) => void;
}) {
  const [capabilities, setCapabilities] = useState<Capabilities>();
  const [proposed, setProposed] = useState(item.note);
  const [suggestion, setSuggestion] = useState<NoteSuggestion>();
  const [busy, setBusy] = useState(false);
  const [reviewBusy, setReviewBusy] = useState(false);
  const reviewInFlight = useRef(false);
  const [error, setError] = useState('');
  const inFlight = useRef(false);
  const current = useRef(item);
  current.current = item;
  const revision = useRef(0);
  const disabled = editing || draftDirty || item.deleted;

  useEffect(() => {
    const controller = new AbortController();
    revision.current += 1;
    inFlight.current = false;
    setBusy(false); setCapabilities(undefined); setSuggestion(undefined); setError(''); setProposed(item.note);
    void request<Capabilities>(`/items/${encodeURIComponent(item.item_id)}/suggestions/capabilities`, { signal: controller.signal })
      .then((result) => { if (!controller.signal.aborted) setCapabilities(result); })
      .catch(() => { /* An unavailable or old API leaves the optional feature hidden. */ });
    return () => { controller.abort(); revision.current += 1; };
  }, [item.item_id]);

  async function preview() {
    if (inFlight.current || reviewInFlight.current || disabled || !capabilities?.enabled) return;
    const selected = revision.current;
    inFlight.current = true; setBusy(true); setError('');
    try {
      const result = await request<NoteSuggestion>(`/items/${encodeURIComponent(item.item_id)}/suggestions/preview`, {
        method: 'POST', csrf, body: { proposed_note: proposed },
      });
      if (selected === revision.current) setSuggestion(result);
    } catch (reason) {
      if (selected === revision.current) setError(reason instanceof ApiError && reason.status === 409
        ? 'Bài đã thay đổi. Văn bản đề xuất vẫn được giữ; tải lại bài để đối chiếu.'
        : 'Chưa tạo được bản so sánh. Văn bản đề xuất vẫn được giữ để thử lại.');
    } finally {
      if (selected === revision.current) { inFlight.current = false; setBusy(false); }
    }
  }

  function applied(result: AppliedSuggestion) {
    const latest = current.current;
    if (latest.item_id !== suggestion?.item_id || latest.deleted) return;
    // A newer poll or edit must not be replaced by a late acknowledgement.
    if ((latest.user_edit_version ?? -1) > result.edit_version) return;
    const updated = { ...latest, note: result.note, user_edit_version: result.edit_version, updated_at: result.updated_at || latest.updated_at };
    current.current = updated;
    onUpdated(updated);
  }

  if (!capabilities?.enabled || capabilities.mode !== 'manual_review_poc' || item.deleted) return null;
  return <details className="panel">
    <summary>So sánh đề xuất thủ công (thử nghiệm)</summary>
    <div className="form-stack">
      <p>Nhập một bản văn bản thay thế để xem khác biệt trước khi duyệt. Chưa kết nối AI; nội dung không được gửi đến nhà cung cấp bên ngoài.</p>
      <p>Bản so sánh hết hạn sau 15 phút. Từ chối hoặc hủy chỉ bỏ bản xem trong phiên này.</p>
      {disabled && <p role="status">Lưu hoặc hủy bản nháp đang soạn trước khi duyệt đề xuất.</p>}
      <Textarea label="Văn bản đề xuất thủ công" value={proposed} minRows={5} autosize maxLength={100_000}
        disabled={busy || reviewBusy || disabled} onChange={(event) => setProposed(event.currentTarget.value)} />
      <div className="form-actions">
        <Button type="button" variant="default" disabled={busy || reviewBusy || disabled || proposed === item.note} onClick={() => void preview()}>Xem khác biệt</Button>
        <Button type="button" variant="subtle" disabled={busy || reviewBusy || disabled} onClick={() => { setProposed(item.note); setSuggestion(undefined); setError(''); }}>Dùng văn bản hiện tại</Button>
      </div>
      {error && <p role="alert">{error}</p>}
      {suggestion && <AiSuggestionReview key={suggestion.receipt} suggestion={suggestion} csrf={csrf} currentNote={item.note}
        disabled={disabled || busy} onApplied={applied} onClose={() => setSuggestion(undefined)} onBusyChange={(value) => {
          reviewInFlight.current = value; setReviewBusy(value); onBusyChange?.(value);
        }} />}
    </div>
  </details>;
}
