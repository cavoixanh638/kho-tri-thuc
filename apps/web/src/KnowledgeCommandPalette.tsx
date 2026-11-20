import { useEffect, useId, useRef, useState } from 'react';
import { request } from './api';
import './NoteNavigation.css';

type NavigationPage = { items: { item_id: string; title: string; saved_at: string }[]; folders: { id: number; name: string }[]; next_offset: number | null };
export type KnowledgeCommand = 'create' | 'move' | 'attach' | 'day';
type Choice = { id: string; label: string; href?: string; action?: KnowledgeCommand };

export function KnowledgeCommandPalette({ currentItemId, onAction }: { currentItemId?: string; onAction?: (action: KnowledgeCommand) => void }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [data, setData] = useState<NavigationPage>();
  const [error, setError] = useState('');
  const [active, setActive] = useState(0);
  const dialog = useRef<HTMLDialogElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const composing = useRef(false);
  const id = useId();
  const choices: Choice[] = [
    ...(data?.items ?? []).map((item) => ({ id: item.item_id, label: 'Bài · ' + item.title, href: '#/muc/' + item.item_id })),
    ...(data?.folders ?? []).map((folder) => ({ id: 'folder-' + folder.id, label: 'Thư mục · ' + folder.name, href: '#/thu-vien?node=' + folder.id })),
    ...([
      ['create', 'Tạo ghi chú mới'],
      ...(currentItemId ? [['move', 'Di chuyển bài đang mở'], ['attach', 'Gắn nguồn vào bài đang mở']] : []),
      ['day', 'Đi đến ngày nhận trong thư viện'],
    ] as [KnowledgeCommand, string][]).filter(([, label]) => !query || label.toLocaleLowerCase('vi').includes(query.toLocaleLowerCase('vi')))
      .map(([action, label]) => ({ id: 'command-' + action, label, action })),
  ];
  function close() { setOpen(false); trigger.current?.focus(); }
  function choose(choice: Choice) {
    close();
    if (choice.href) window.location.hash = choice.href;
    else if (choice.action) {
      if (onAction) onAction(choice.action);
      else if (choice.action === 'create') window.location.hash = '#/gui';
      else if (choice.action === 'day') window.location.hash = '#/thu-vien?view=timeline';
      else window.dispatchEvent(new CustomEvent('knowledge-command', { detail: { action: choice.action, itemId: currentItemId } }));
    }
  }
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== 'k' || event.isComposing || event.keyCode === 229) return;
      const target = event.target;
      if (target instanceof HTMLElement && (target.matches('input,textarea,select') || target.isContentEditable)) return;
      event.preventDefault(); setOpen((current) => !current);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);
  useEffect(() => {
    const node = dialog.current;
    if (!node) return;
    if (open) { node.showModal(); input.current?.focus(); }
    else if (node.open) node.close();
  }, [open]);
  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setData(undefined); setError(''); setActive(0);
    const timer = window.setTimeout(() => {
      void request<NavigationPage>('/navigation?q=' + encodeURIComponent(query), { signal: controller.signal })
        .then((value) => { if (!controller.signal.aborted) setData(value); })
        .catch(() => { if (!controller.signal.aborted) setError('Chưa tìm được dữ liệu. Các lệnh vẫn dùng được.'); });
    }, 120);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [open, query]);
  return <>
    <button ref={trigger} type="button" className="knowledge-palette-trigger" onClick={() => setOpen(true)}>Tìm và thao tác · Ctrl+K</button>
    <dialog ref={dialog} className="knowledge-palette" aria-labelledby={id} onCancel={(event) => { event.preventDefault(); close(); }}
      onKeyDown={(event) => {
        if (composing.current || event.nativeEvent.isComposing || event.keyCode === 229) return;
        if (event.key === 'Escape') { event.preventDefault(); close(); }
        else if (choices.length && ['ArrowDown', 'ArrowUp'].includes(event.key)) {
          event.preventDefault(); setActive((old) => (old + (event.key === 'ArrowDown' ? 1 : -1) + choices.length) % choices.length);
        } else if (event.key === 'Enter' && choices[active]) { event.preventDefault(); choose(choices[active]); }
      }}>
      <header><h2 id={id}>Tìm và thao tác</h2><button type="button" onClick={close}>Đóng</button></header>
      <label htmlFor={id + '-query'}>Tên bài, thư mục hoặc lệnh</label>
      <input ref={input} id={id + '-query'} value={query} autoComplete="off" role="combobox" aria-expanded={open} aria-controls={id + '-choices'} aria-activedescendant={choices[active] ? id + '-choice-' + active : undefined}
        onCompositionStart={() => { composing.current = true; }} onCompositionEnd={() => { composing.current = false; }}
        onChange={(event) => setQuery(event.currentTarget.value)} />
      <p>Dùng Arrow/Enter để chọn, Esc để đóng. Bài trùng tên vẫn được phân biệt bằng UUID.</p>
      {error && <p role="alert">{error}</p>}
      <div role="listbox" id={id + '-choices'} aria-label="Kết quả và lệnh">
        {choices.map((choice, index) => <button key={choice.id} type="button" role="option" id={id + '-choice-' + index} aria-selected={index === active} onClick={() => choose(choice)}>
          {choice.label}{choice.href?.startsWith('#/muc/') && <small>{choice.id}</small>}
        </button>)}
      </div>
      {data?.next_offset != null && <p>Đang hiển thị 20 bài đầu. Nhập thêm từ khóa để thu hẹp.</p>}
    </dialog>
  </>;
}
