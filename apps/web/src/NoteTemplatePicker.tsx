import { Button, TextInput } from '@mantine/core';
import { useId, useRef, useState } from 'react';
import { KnowledgeText } from './KnowledgeText';
import { noteTemplates, proposeNoteTemplate, type NoteTemplateApplication, type NoteTemplateId, type NoteTemplateMetadata } from './NoteTemplateConfig';
import './NoteTemplatePicker.css';

export function NoteTemplatePicker({ note, disabled = false, onApply }: {
  note: string; disabled?: boolean; onApply: (proposal: NoteTemplateApplication) => boolean | Promise<boolean>;
}) {
  const [selected, setSelected] = useState<NoteTemplateId>();
  const [metadata, setMetadata] = useState<NoteTemplateMetadata>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const inFlight = useRef(false);
  const id = useId();
  const template = noteTemplates.find((entry) => entry.id === selected);

  async function apply() {
    if (!selected || disabled || inFlight.current) return;
    inFlight.current = true; setBusy(true); setError(''); setNotice('');
    try {
      const proposal = proposeNoteTemplate(note, selected, metadata);
      if (!await onApply(proposal)) { setError('Bản nháp đã thay đổi. Kiểm tra lại trước khi thêm mẫu.'); return; }
      setNotice('Đã thêm mẫu vào bản nháp. Chưa lưu lên máy chủ.'); setSelected(undefined); setMetadata({});
    } catch (error) { setError(error instanceof Error ? error.message : 'Chưa thêm được mẫu. Bản nháp vẫn được giữ.'); }
    finally { inFlight.current = false; setBusy(false); }
  }

  return <section className="note-template-picker" aria-labelledby={id}>
    <h2 id={id}>Mẫu ghi chú</h2>
    <p>Tùy chọn. Chọn mẫu rồi thêm vào bản nháp; bạn có thể sửa mọi nội dung sau đó.</p>
    <div className="note-template-options" role="group" aria-label="Chọn mẫu ghi chú">
      {noteTemplates.map((entry) => <button key={entry.id} type="button" aria-pressed={selected === entry.id} disabled={disabled || busy}
        onClick={() => { setSelected(entry.id); setError(''); setNotice(''); }}>
        <strong>{entry.label}</strong><span>{entry.description}</span>
      </button>)}
    </div>
    {template && <div className="note-template-selection">
      <details><summary>Thông tin bổ sung (tùy chọn)</summary>
        <div className="note-template-fields">
          <TextInput label="Tác giả" value={metadata.author ?? ''} maxLength={200} disabled={disabled || busy} onChange={(event) => setMetadata({ ...metadata, author: event.currentTarget.value })} />
          <TextInput label="Ngày nguồn" type="date" value={metadata.sourceDate ?? ''} disabled={disabled || busy} onChange={(event) => setMetadata({ ...metadata, sourceDate: event.currentTarget.value })} />
          <TextInput label="Liên kết nguồn" type="url" value={metadata.sourceUrl ?? ''} maxLength={4096} disabled={disabled || busy} onChange={(event) => setMetadata({ ...metadata, sourceUrl: event.currentTarget.value })} />
        </div>
      </details>
      <div className="note-template-preview" aria-label="Xem trước mẫu"><KnowledgeText text={template.markdown} /></div>
      {note && <p>Nội dung hiện có được giữ nguyên. Mẫu sẽ thêm vào cuối bản nháp.</p>}
      <div className="note-template-actions">
        <Button type="button" variant="default" disabled={disabled || busy} onClick={() => void apply()}>{busy ? 'Đang thêm…' : note ? 'Thêm mẫu vào cuối' : 'Dùng mẫu trong bản nháp'}</Button>
        <Button type="button" variant="subtle" disabled={busy} onClick={() => { setSelected(undefined); setError(''); setMetadata({}); }}>Bỏ chọn</Button>
      </div>
    </div>}
    {error && <p role="alert">{error}</p>}
    {notice && <p role="status">{notice}</p>}
  </section>;
}
