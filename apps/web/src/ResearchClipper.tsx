import { Button, NativeSelect, Textarea, TextInput } from '@mantine/core';
import { useRef, useState } from 'react';
import { request, type Item, type Page, type Receipt } from './api';
import { Empty, ErrorNotice, PageControls, useResource } from './views';
import { SourceLocatorCitation } from './SourceLocator';
import './ResearchClipper.css';

type Mode = 'link' | 'article' | 'selection';
type Preview = { receipt: string; quote: string; url: string; page_title: string; verification: string; locator: Record<string, unknown>; source_version: string };
type SourcePart = { id: number; kind: string; text: string; locator: Record<string, unknown> };
type Clip = { id: string; quote: string; state: string; source_url: string; page_title: string; source_id: number | null;
  part_id: number | null; asset_id: string | null; asset_mime: string | null; asset_version: number | null;
  source_version: string; processor_version: string; locator: Record<string, unknown>; inserted_edit_version: number | null };
const states: Record<string, string> = { current: 'Khớp văn bản nguồn đã trích', stale: 'Nguồn đã thay đổi', missing: 'Thiếu nguồn',
  unverified: 'Đoạn người dùng cung cấp, chưa xác minh trong nguồn', link_only: 'Chỉ có liên kết, chưa có văn bản' };

export function ResearchClipper({ id, csrf, onSaved }: { id?: string; csrf: string; onSaved?: () => void }) {
  const [mode, setMode] = useState<Mode>('link');
  const [url, setUrl] = useState('');
  const [quote, setQuote] = useState('');
  const [derived, setDerived] = useState('');
  const [sources, setSources] = useState<SourcePart[]>([]);
  const [sourceOffset, setSourceOffset] = useState(0);
  const [sourceNext, setSourceNext] = useState<number | null>(null);
  const [query, setQuery] = useState('');
  const [targets, setTargets] = useState<{ item_id: string; title: string }[]>([]);
  const [target, setTarget] = useState('');
  const [preview, setPreview] = useState<Preview>();
  const [receipt, setReceipt] = useState<Receipt>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const attempt = useRef<{ receipt: string; key: string } | undefined>(undefined);
  const inFlight = useRef(false);
  const changed = () => { setPreview(undefined); setReceipt(undefined); attempt.current = undefined; setError(''); };
  async function act(action: () => Promise<void>) {
    if (inFlight.current) return;
    inFlight.current = true; setBusy(true); setError('');
    try { await action(); } catch { setError('Chưa xác nhận được thao tác. Nội dung vẫn được giữ; nguồn có thể chưa truy cập được hoặc đã đổi phiên bản.'); }
    finally { inFlight.current = false; setBusy(false); }
  }
  async function loadSources(offset: number) {
    const result = await request<Page<SourcePart>>(`/items/${id}/clip-sources?offset=${offset}`);
    setSources(result.results); setSourceOffset(offset); setSourceNext(result.next_offset);
  }
  return <section className="panel research-clipper" aria-label="Thu thập nguồn và trích dẫn">
    <h2>Thu thập nguồn và trích dẫn</h2>
    <p>Lưu liên kết, bài viết lấy được từ website công khai hoặc một đoạn trích. Bản bạn biên soạn được giữ riêng.</p>
    <NativeSelect label="Cách thu thập" value={mode} disabled={busy} data={[
      { value: 'link', label: 'Liên kết — chưa trích nội dung' }, { value: 'article', label: 'Bài viết — văn bản máy chủ lấy được' },
      { value: 'selection', label: 'Đoạn trích — đối chiếu với nguồn' },
    ]} onChange={(event) => { changed(); setMode(event.currentTarget.value as Mode); setDerived(''); }} />
    {!id && <details><summary>Gửi vào bài đang có (tùy chọn)</summary>
      <TextInput label="Tìm bài nhận trích dẫn" value={query} disabled={busy} onChange={(event) => setQuery(event.currentTarget.value)} />
      <Button variant="default" disabled={busy} onClick={() => void act(async () => {
        const result = await request<{ items: typeof targets }>(`/navigation?kind=items&q=${encodeURIComponent(query)}`); setTargets(result.items);
      })}>Tìm bài nhận</Button>
      <NativeSelect label="Bài nhận" value={target} disabled={busy} data={[{ value: '', label: 'Tạo mục nguồn mới' }, ...targets.map((row) => ({ value: row.item_id, label: row.title }))]}
        onChange={(event) => { changed(); setTarget(event.currentTarget.value); }} />
    </details>}
    {id && mode === 'selection' && <details><summary>Chọn từ văn bản PDF / web / transcript đã trích của bài</summary>
      <Button variant="default" disabled={busy} onClick={() => void act(() => loadSources(0))}>Tải danh sách văn bản nguồn</Button>
      <NativeSelect label="Phần nguồn" value={derived} disabled={busy} data={[{ value: '', label: 'Đối chiếu URL công khai bên dưới' }, ...sources.map((row) => ({
        value: String(row.id), label: `Phần ${row.id} · ${row.kind}${row.locator.page ? ' · trang ' + row.locator.page : ''}`,
      }))]} onChange={(event) => { changed(); setDerived(event.currentTarget.value); }} />
      {derived && <pre className="clip-source-text">{sources.find((row) => String(row.id) === derived)?.text}</pre>}
      <PageControls offset={sourceOffset} nextOffset={sourceNext} onChange={(offset) => void act(() => loadSources(offset))} />
      <p className="list-meta">Văn bản tối đa 60.000 ký tự mỗi phần. PDF chỉ ghi trang khi parser có; không suy tọa độ hoặc mốc video.</p>
    </details>}
    {!derived && <TextInput label="URL nguồn công khai" type="url" value={url} disabled={busy}
      onChange={(event) => { changed(); setUrl(event.currentTarget.value); }} />}
    {mode === 'selection' && <>
      <Textarea label="Đoạn trích nguyên văn" value={quote} minRows={4} autosize maxRows={12} disabled={busy} maxLength={60_000}
        onChange={(event) => { changed(); setQuote(event.currentTarget.value); }} />
      <Button variant="subtle" disabled={busy} onClick={() => { const selected = window.getSelection()?.toString(); if (selected) { changed(); setQuote(selected); } }}>Dùng đoạn văn đang chọn</Button>
    </>}
    <Button variant="default" disabled={busy || (!url && !derived) || (mode === 'selection' && !quote)} onClick={() => void act(async () => {
      const result = await request<Preview>('/clips/preview', { method: 'POST', csrf, body: { mode, url, quote,
        ...(id || target ? { target_item_id: id || target } : {}), ...(derived ? { derived_id: Number(derived) } : {}) } });
      setPreview(result); setReceipt(undefined);
    })}>Xem trước nguồn / đoạn trích</Button>
    {preview && <div className="clip-preview" aria-label="Xem trước trích dẫn">
      <h3>{preview.page_title || 'Bản xem trước nguồn'}</h3>
      <p>{states[preview.verification] || preview.verification}</p>
      {preview.url && <p className="clip-url">{preview.url}</p>}
      {preview.quote && <pre>{preview.quote}</pre>}
      <p>Chưa lưu lượt gửi. Bản xem trước hết hạn sau 5 phút; không ghi đè nội dung bài.</p>
      <Button disabled={busy} onClick={() => void act(async () => {
        if (attempt.current?.receipt !== preview.receipt) attempt.current = { receipt: preview.receipt, key: crypto.randomUUID() };
        const result = await request<Receipt>('/clips', { method: 'POST', csrf, body: { receipt: preview.receipt }, idempotencyKey: attempt.current.key });
        setReceipt(result); setPreview(undefined); attempt.current = undefined; onSaved?.();
      })}>{id || target ? 'Lưu trích dẫn vào bài này' : 'Lưu nguồn mới vào kho'}</Button>
    </div>}
    {receipt && <p role="status">Đã tiếp nhận trích dẫn. <a href={`#/muc/${receipt.item_id}`}>Mở bài nhận</a></p>}
    {error && <ErrorNotice>{error}</ErrorNotice>}
  </section>;
}

export function ClipAnnotations({ item, csrf, disabled, onUpdated, refreshKey, onIllustration }: {
  item: Item; csrf: string; disabled: boolean; onUpdated: (item: Item) => void; refreshKey?: string; onIllustration: (id: string) => void;
}) {
  const [offset, setOffset] = useState(0);
  const rows = useResource<Page<Clip>>(`/items/${item.item_id}/clips?offset=${offset}`, { refreshKey });
  const [excerpt, setExcerpt] = useState<{ id: string; before: string; quote: string; after: string }>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const inFlight = useRef(false);
  async function action(fn: () => Promise<void>) {
    if (inFlight.current) return;
    inFlight.current = true; setBusy(true); setError('');
    try { await fn(); } catch { setError('Nguồn hoặc bài đã thay đổi. Nội dung hiện tại được giữ; tải lại để đối chiếu.'); }
    finally { inFlight.current = false; setBusy(false); }
  }
  return <section className="panel clip-annotations" aria-label="Trích dẫn đã lưu">
    <h2>Trích dẫn đã lưu</h2>
    {rows.error ? <ErrorNotice retry={rows.retry}>Chưa tải được trích dẫn.</ErrorNotice>
      : !rows.data?.results.length ? <Empty>Chưa có trích dẫn. Bạn có thể thu thập đoạn nguồn vào bài này.</Empty>
        : rows.data.results.map((row) => <article key={row.id}>
          <h3>{row.page_title || 'Trích dẫn nguồn'}</h3>
          <p>{states[row.state] || row.state}</p>
          <blockquote className="prose-text">{row.quote || 'Liên kết chưa có văn bản trích.'}</blockquote>
          {row.state === 'current' && <div className="form-actions">
            <Button variant="default" disabled={busy} onClick={() => void action(async () => {
              const result = await request<{ before: string; quote: string; after: string }>(`/clips/${row.id}/source`); setExcerpt({ id: row.id, ...result });
            })}>Xem đúng đoạn trong văn bản nguồn</Button>
            <Button variant="default" disabled={busy || disabled || row.inserted_edit_version != null || item.user_edit_version == null}
              onClick={() => void action(async () => {
                const result = await request<Pick<Item, 'note' | 'user_edit_version' | 'updated_at'>>(`/clips/${row.id}/insert`, {
                  method: 'POST', csrf, body: { expected_edit_version: item.user_edit_version },
                }); onUpdated({ ...item, ...result }); rows.retry();
              })}>{row.inserted_edit_version == null ? 'Duyệt chèn vào bản biên soạn' : 'Đã chèn vào bản biên soạn'}</Button>
          </div>}
          {excerpt?.id === row.id && row.state === 'current' && <pre className="clip-source-text">{excerpt.before}<mark>{excerpt.quote}</mark>{excerpt.after}</pre>}
          <SourceLocatorCitation onIllustration={onIllustration} part={{ id: row.part_id ?? 0, kind: 'quote', asset_id: row.asset_id,
            locator: row.locator, processor: 'Trích dẫn đã duyệt', processor_version: row.processor_version,
            source: { state: row.state === 'current' ? 'current' : row.state === 'stale' ? 'stale' : 'unverified', version: row.source_version,
              source_id: row.source_id, source_url: row.source_url || null, mime: row.asset_mime, asset_version: row.asset_version },
          }} />
        </article>)}
    {rows.data && <PageControls offset={offset} nextOffset={rows.data.next_offset} onChange={setOffset} />}
    {error && <ErrorNotice>{error}</ErrorNotice>}
  </section>;
}
