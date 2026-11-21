import { useEffect, useId, useRef, useState } from 'react';
import { Button } from '@mantine/core';
import { KnowledgeText } from './KnowledgeText';
import './MarkdownEditor.css';
import { request } from './api';
import { wikiInsertion, wikiQuery, type WikiQuery } from './WikiCompletion';

type WikiTarget = { item_id: string; title: string; saved_at: string };

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
  const textarea = useRef<HTMLTextAreaElement>(null);
  const [query, setQuery] = useState<WikiQuery>();
  const [targets, setTargets] = useState<WikiTarget[]>([]);
  const [active, setActive] = useState(0);
  const [wikiError, setWikiError] = useState('');
  useEffect(() => {
    if (!query || isComposing || disabled) { setTargets([]); return; }
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      void request<{ items: WikiTarget[] }>(`/navigation?kind=items&q=${encodeURIComponent(query.query)}`, { signal: controller.signal })
        .then((data) => { if (!controller.signal.aborted) { setTargets(data.items ?? []); setActive(0); setWikiError(''); } })
        .catch(() => { if (!controller.signal.aborted) { setTargets([]); setWikiError('Chưa tìm được bài. Bạn có thể tiếp tục soạn.'); } });
    }, 120);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [query?.query, query?.start, isComposing, disabled]);
  function complete(target: WikiTarget) {
    const field = textarea.current;
    if (!field || !query || composing.current || disabled) return;
    const result = wikiInsertion(field.value, query, target);
    if (!result) return;
    onChange(editRawMarkdown(value, result.text));
    setQuery(undefined); setTargets([]);
    window.requestAnimationFrame(() => { field.focus(); field.setSelectionRange(result.caret, result.caret); });
  }
  return <div className="markdown-editor" onKeyDown={(event) => {
    if (composing.current || event.nativeEvent.isComposing || event.keyCode === 229) return;
    if (query) {
      if (event.key === 'Escape') { event.preventDefault(); setQuery(undefined); return; }
      if (targets.length && (event.key === 'ArrowDown' || event.key === 'ArrowUp')) {
        event.preventDefault(); setActive((old) => (old + (event.key === 'ArrowDown' ? 1 : -1) + targets.length) % targets.length); return;
      }
      if (targets.length && event.key === 'Enter' && !event.ctrlKey && !event.metaKey) {
        event.preventDefault(); complete(targets[active]); return;
      }
    }
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
        <textarea ref={textarea} id={id} aria-describedby={`${id}-help`} value={value} rows={14} disabled={disabled}
          aria-autocomplete="list" aria-controls={query ? id + '-wiki' : undefined} aria-activedescendant={query && targets[active] ? id + '-wiki-' + active : undefined}
          onCompositionStart={() => { composing.current = true; setIsComposing(true); onCompositionChange(true); }}
          onCompositionEnd={(event) => { composing.current = false; setIsComposing(false); onCompositionChange(false); onChange(editRawMarkdown(value, event.currentTarget.value)); setQuery(wikiQuery(event.currentTarget.value, event.currentTarget.selectionStart)); }}
          onChange={(event) => { onChange(editRawMarkdown(value, event.currentTarget.value)); if (!composing.current) setQuery(wikiQuery(event.currentTarget.value, event.currentTarget.selectionStart)); }} />
        {query && !isComposing && <div className="wiki-completion">
          <p>Chọn bài để tạo liên kết cố định; Arrow/Enter để chọn, Esc để đóng.</p>
          <div id={id + '-wiki'} role="listbox" aria-label="Gợi ý liên kết bài">
            {targets.map((target, index) => <button key={target.item_id} id={id + '-wiki-' + index} type="button" role="option" aria-selected={active === index}
              onMouseDown={(event) => event.preventDefault()} onClick={() => complete(target)}>{target.title}<small>{target.item_id} · {new Date(target.saved_at).toLocaleDateString('vi-VN')}</small></button>)}
          </div>
          {!targets.length && <p role="status">{wikiError || 'Chưa có bài phù hợp. Liên kết chưa được tạo.'}</p>}
        </div>}
      </div>
      {mode !== 'edit' && <section className="markdown-editor-preview" aria-label="Xem trước bản nháp">
        {value ? <KnowledgeText text={value} title={title} /> : <p>Chưa có nội dung trong bản nháp.</p>}
      </section>}
    </div>
  </div>;
}
