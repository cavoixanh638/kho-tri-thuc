import { useId, useRef, useState } from 'react';
import { Button } from '@mantine/core';
import { KnowledgeText } from './KnowledgeText';
import './MarkdownEditor.css';

/** Textarea normalizes CR/CRLF. Map only the changed span back to the raw source. */
export function editRawMarkdown(raw: string, next: string) {
  const displayed = raw.replace(/\r\n?/g, '\n');
  if (displayed === next) return raw;
  let start = 0, tail = 0;
  while (start < displayed.length && start < next.length && displayed[start] === next[start]) start++;
  while (tail < displayed.length - start && tail < next.length - start && displayed[displayed.length - 1 - tail] === next[next.length - 1 - tail]) tail++;
  const offsets = [0];
  for (let i = 0; i < raw.length; i++) {
    if (raw[i] === '\r' && raw[i + 1] === '\n') i++;
    offsets.push(i + 1);
  }
  const newline = raw.match(/\r\n|\r|\n/)?.[0] ?? '\n';
  const inserted = next.slice(start, next.length - tail).replace(/\n/g, newline);
  return raw.slice(0, offsets[start]) + inserted + raw.slice(offsets[displayed.length - tail]);
}

export function MarkdownEditor({ value, title, disabled, onChange, onSave, onCompositionChange }: {
  value: string; title: string; disabled: boolean; onChange: (value: string) => void;
  onSave: () => void; onCompositionChange: (composing: boolean) => void;
}) {
  const [mode, setMode] = useState<'edit' | 'split' | 'read'>('edit');
  const composing = useRef(false);
  const [isComposing, setIsComposing] = useState(false);
  const id = useId();
  return <div className="markdown-editor" onKeyDown={(event) => {
    if (composing.current || event.nativeEvent.isComposing || event.keyCode === 229) return;
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
      event.preventDefault();
      if (!disabled) onSave();
    }
  }}>
    <div className="markdown-editor-modes" role="group" aria-label="Chế độ Markdown">
      {([['edit', 'Soạn thảo'], ['split', 'Soạn + Xem trước'], ['read', 'Đọc bản nháp']] as const).map(([key, label]) =>
        <Button key={key} type="button" variant="default" aria-pressed={mode === key} disabled={disabled || isComposing} onClick={() => setMode(key)}>{label}</Button>)}
    </div>
    <p id={`${id}-help`} className="markdown-editor-help">Markdown: # tiêu đề, - danh sách, &gt; trích dẫn, **đậm**, [tên](https://…), `mã`. Ctrl/⌘ + Enter để lưu.</p>
    <div className={`markdown-editor-panes markdown-editor-${mode}`}>
      <div hidden={mode === 'read'}>
        <label htmlFor={id}>Nội dung tri thức (Markdown)</label>
        <textarea id={id} aria-describedby={`${id}-help`} value={value} rows={14} disabled={disabled}
          onCompositionStart={() => { composing.current = true; setIsComposing(true); onCompositionChange(true); }}
          onCompositionEnd={(event) => { composing.current = false; setIsComposing(false); onCompositionChange(false); onChange(editRawMarkdown(value, event.currentTarget.value)); }}
          onChange={(event) => onChange(editRawMarkdown(value, event.currentTarget.value))} />
      </div>
      {mode !== 'edit' && <section className="markdown-editor-preview" aria-label="Xem trước bản nháp">
        {value ? <KnowledgeText text={value} title={title} /> : <p>Chưa có nội dung trong bản nháp.</p>}
      </section>}
    </div>
  </div>;
}
