import { Button, TextInput } from '@mantine/core';
import { useEffect, useState, type SubmitEvent } from 'react';
import { ApiError, request, type Item, type Page } from './api';
import { LibraryViews, libraryModes, type LibraryMode } from './LibraryViews';
import { Empty, ErrorNotice, Loading, PageControls, useResource } from './views';
import './SavedCollections.css';

type GroupCondition = { any: number[]; all: number[]; exclude: number[] };
type Bounds = { from: string | null; to: string | null };
export type CollectionQuery = {
  schema_version: 1; q: string; topics: GroupCondition; projects: GroupCondition; tags: GroupCondition;
  received: Bounds; published: Bounds; timezone: string; favorite: boolean | null;
  source_fetch: string; content_extract: string; sort: string;
};
export type SavedCollection = { id: string; name: string; query: CollectionQuery; view: LibraryMode; version: number };
type Groups = { topics: { id: number; name: string }[]; projects: { id: number; name: string }[]; tags: { id: number; name: string }[] };
type Results = Page<Item> & { count: number };
const changed = 'saved-collections-changed';
const emptyGroup = (): GroupCondition => ({ any: [], all: [], exclude: [] });
export const emptyCollectionQuery = (): CollectionQuery => ({ schema_version: 1, q: '', topics: emptyGroup(), projects: emptyGroup(), tags: emptyGroup(),
  received: { from: null, to: null }, published: { from: null, to: null }, timezone: 'Asia/Ho_Chi_Minh', favorite: null,
  source_fetch: '', content_extract: '', sort: 'saved_desc' });
export function collectionIdFromHash(hash: string) {
  const value = new URLSearchParams(hash.split('?')[1]).get('collection');
  return value === 'new' || /^[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}$/i.test(value ?? '') ? value! : undefined;
}
export const collectionHref = (id: string) => '#/thu-vien?collection=' + encodeURIComponent(id);
const notify = () => window.dispatchEvent(new Event(changed));

export function SavedCollectionsPanel() {
  const data = useResource<{ results: SavedCollection[] }>('/collections');
  useEffect(() => { window.addEventListener(changed, data.retry); return () => window.removeEventListener(changed, data.retry); }, [data.retry]);
  return <section className="saved-collections-panel" aria-labelledby="saved-collections-title">
    <h2 id="saved-collections-title">Bộ sưu tập thông minh</h2>
    <p className="list-meta">Bộ lọc động; không di chuyển hay nhân bản bài.</p>
    {data.error || (data.data !== undefined && !Array.isArray(data.data?.results)) ? <ErrorNotice retry={data.retry}>Chưa tải được bộ sưu tập.</ErrorNotice> : !data.data ? <Loading /> :
      data.data.results.length ? <ul>{data.data.results.map((entry) => <li key={entry.id}><a href={collectionHref(entry.id)}><span aria-hidden="true">⌕ </span>{entry.name}<small>Bộ lọc đã lưu</small></a></li>)}</ul> : <p>Chưa có bộ lọc đã lưu.</p>}
    <a href={collectionHref('new')}>Tạo bộ sưu tập thông minh</a>
  </section>;
}

function DefinitionForm({ initial, csrf, onSaved }: { initial?: SavedCollection; csrf: string; onSaved: (value: SavedCollection) => void }) {
  const [name, setName] = useState(initial?.name ?? '');
  const [query, setQuery] = useState(initial?.query ?? emptyCollectionQuery());
  const [view, setView] = useState<LibraryMode>(initial?.view ?? 'list');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [preview, setPreview] = useState<Results>();
  const groups = useResource<Groups>('/groups');
  async function save(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault(); if (busy) return; setBusy(true); setError('');
    try {
      const value = await request<SavedCollection>(initial ? '/collections/' + initial.id : '/collections', {
        method: initial ? 'PATCH' : 'POST', csrf,
        body: { name, query, view, ...(initial ? { expected_version: initial.version } : {}) },
      });
      notify(); onSaved(value);
    } catch (reason) { setError(reason instanceof ApiError && reason.status === 409 ? 'Tên bộ sưu tập trùng hoặc đã có phiên khác sửa. Điều kiện bạn nhập vẫn được giữ.' : 'Chưa lưu được bộ sưu tập. Kiểm tra tên, nhóm và điều kiện.'); }
    finally { setBusy(false); }
  }
  async function showPreview() {
    if (busy) return; setBusy(true); setError('');
    try { setPreview(await request<Results>('/collections/preview', { method: 'POST', csrf, body: { query, limit: 50, offset: 0 } })); }
    catch { setError('Chưa xem trước được. Kiểm tra điều kiện và thử lại.'); }
    finally { setBusy(false); }
  }
  const change = (patch: Partial<CollectionQuery>) => { setQuery((current) => ({ ...current, ...patch })); setPreview(undefined); };
  return <form className="form-stack saved-collection-form" onSubmit={save}>
    <TextInput label="Tên bộ sưu tập" value={name} required maxLength={120} disabled={busy} onChange={(event) => setName(event.currentTarget.value)} />
    <TextInput label="Từ khóa trong tri thức" value={query.q} maxLength={300} disabled={busy} onChange={(event) => change({ q: event.currentTarget.value })} />
    <div className="saved-collection-fields">
      <label>Yêu thích<select value={query.favorite === null ? '' : String(query.favorite)} disabled={busy} onChange={(event) => change({ favorite: event.currentTarget.value === '' ? null : event.currentTarget.value === 'true' })}><option value="">Tất cả</option><option value="true">Có</option><option value="false">Không</option></select></label>
      <label>Cách xem mặc định<select value={view} disabled={busy} onChange={(event) => setView(event.currentTarget.value as LibraryMode)}>{libraryModes.map((entry) => <option key={entry.value} value={entry.value}>{entry.label}</option>)}</select></label>
      <label>Sắp xếp<select value={query.sort} disabled={busy} onChange={(event) => change({ sort: event.currentTarget.value })}><option value="saved_desc">Ngày nhận mới nhất</option><option value="saved_asc">Ngày nhận cũ nhất</option><option value="published_desc">Ngày nguồn mới nhất</option><option value="title">Tiêu đề</option></select></label>
    </div>
    <details><summary>Điều kiện nhóm, thời gian và trạng thái</summary>
      <p>Các loại điều kiện kết hợp bằng AND. Trong mỗi ô “Bất kỳ”, chọn một hoặc nhiều nhóm bằng Ctrl/⌘ hoặc Shift.</p>
      {groups.error && <ErrorNotice retry={groups.retry}>Chưa tải được nhóm.</ErrorNotice>}
      {(['topics', 'projects', 'tags'] as const).map((kind) => <fieldset key={kind}><legend>{({ topics: 'Chủ đề / thư mục', projects: 'Dự án', tags: 'Nhãn' })[kind]}</legend><div className="saved-collection-fields">
        {(['any', 'all', 'exclude'] as const).map((operator) => <label key={operator}>{({ any: 'Bất kỳ', all: 'Tất cả', exclude: 'Loại trừ' })[operator]}<select multiple aria-label={({ topics: 'Chủ đề / thư mục', projects: 'Dự án', tags: 'Nhãn' })[kind] + ' — ' + ({ any: 'Bất kỳ', all: 'Tất cả', exclude: 'Loại trừ' })[operator]} value={query[kind][operator].map(String)} disabled={busy || !groups.data}
          onChange={(event) => change({ [kind]: { ...query[kind], [operator]: [...event.currentTarget.selectedOptions].map((option) => Number(option.value)) } })}>
          {groups.data?.[kind].map((entry) => <option key={entry.id} value={entry.id}>{entry.name}</option>)}
        </select></label>)}
      </div></fieldset>)}
      <div className="saved-collection-fields">
        {(['received', 'published'] as const).map((kind) => <fieldset key={kind}><legend>{kind === 'received' ? 'Ngày nhận' : 'Ngày nguồn đăng'}</legend>
          {(['from', 'to'] as const).map((bound) => <label key={bound}>{bound === 'from' ? 'Từ ngày' : 'Đến hết ngày'}<input type="date" disabled={busy} value={query[kind][bound] ?? ''} onChange={(event) => change({ [kind]: { ...query[kind], [bound]: event.currentTarget.value || null } })} /></label>)}
        </fieldset>)}
        <label>Múi giờ<input value={query.timezone} maxLength={64} disabled={busy} onChange={(event) => change({ timezone: event.currentTarget.value })} /></label>
        <label>Thu thập nguồn<select value={query.source_fetch} disabled={busy} onChange={(event) => change({ source_fetch: event.currentTarget.value })}>{[['', 'Tất cả'], ['pending', 'Đang chờ'], ['partial', 'Một phần'], ['done', 'Đã thu thập'], ['failed', 'Lỗi'], ['not_applicable', 'Không áp dụng']].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        <label>Trích văn bản<select value={query.content_extract} disabled={busy} onChange={(event) => change({ content_extract: event.currentTarget.value })}>{[['', 'Tất cả'], ['pending', 'Đang chờ'], ['partial', 'Một phần'], ['done', 'Đã trích'], ['failed', 'Lỗi'], ['not_available', 'Chưa có']].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      </div>
    </details>
    {error && <ErrorNotice>{error}</ErrorNotice>}
    <div className="form-actions"><Button type="submit" disabled={busy || !name.trim()}>Lưu bộ sưu tập</Button><Button type="button" variant="default" disabled={busy} onClick={() => void showPreview()}>Xem trước kết quả</Button></div>
    {preview && <section aria-label="Kết quả xem trước"><p role="status">{preview.count} bài khớp; đang hiển thị tối đa 50 bài.</p><LibraryViews items={preview.results} mode={view} sort={query.sort} /></section>}
  </form>;
}

export function SavedCollectionScreen({ csrf, id, owner }: { csrf: string; id?: string; owner?:string|null }) {
  const isNew = !id || id === 'new';
  const data = useResource<SavedCollection>(isNew ? '/collections' : '/collections/' + id);
  const [editing, setEditing] = useState(false);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState(false);
  const results = useResource<Results>(isNew ? '/collections' : '/collections/' + id + '/items?limit=50&offset=' + offset);
  useEffect(() => { setEditing(false); setOffset(0); setError(''); setDeleting(false); }, [id]);
  const value = isNew ? undefined : data.data;
  const saved = (entry: SavedCollection) => {
    setEditing(false); setOffset(0); data.replace(entry); results.retry();
    window.location.hash = collectionHref(entry.id);
  };
  async function remove() {
    if (!value) return;
    try { await request('/collections/' + value.id, { method: 'DELETE', csrf }); notify(); window.location.hash = '#/thu-vien'; }
    catch { setError('Chưa xóa được bộ sưu tập. Các bài tri thức vẫn được giữ.'); }
  }
  return <section className="panel saved-collection-screen" aria-label="Bộ sưu tập thông minh">
    <a href="#/thu-vien">‹ Toàn bộ thư viện</a><h2>{isNew ? 'Tạo bộ sưu tập thông minh' : value?.name ?? 'Bộ sưu tập thông minh'}</h2>
    <p>Danh sách cập nhật theo điều kiện đã lưu. Bài gốc và thư mục không bị thay đổi.</p>
    {error && <ErrorNotice>{error}</ErrorNotice>}
    {isNew ? <DefinitionForm csrf={csrf} onSaved={saved} /> : data.error ? <ErrorNotice retry={data.retry}>Không tìm thấy bộ sưu tập hoặc bạn chưa có quyền.</ErrorNotice> : !value ? <Loading /> : <>
      <div className="form-actions"><Button variant="default" onClick={() => setEditing((old) => !old)}>{editing ? 'Đóng điều kiện' : 'Xem điều kiện / chỉnh sửa'}</Button><Button variant="default" onClick={results.retry}>Cập nhật kết quả</Button><Button variant="subtle" onClick={() => setDeleting(true)}>Xóa bộ sưu tập</Button></div>
      {deleting && <div role="group" aria-label="Xác nhận xóa bộ sưu tập"><p>Chỉ xóa bộ lọc đã lưu; giữ tất cả bài và nhóm.</p><Button variant="default" onClick={() => void remove()}>Xác nhận xóa bộ lọc</Button><Button variant="subtle" onClick={() => setDeleting(false)}>Hủy</Button></div>}
      {editing && <DefinitionForm key={value.id + ':' + value.version} initial={value} csrf={csrf} onSaved={saved} />}
      <p className="list-meta">Cách xem: {libraryModes.find((entry) => entry.value === value.view)?.label}. Đổi cách xem trong “Xem điều kiện / chỉnh sửa” rồi lưu.</p>
      {results.error ? <ErrorNotice retry={results.retry}>Chưa tải được kết quả.</ErrorNotice> : !results.data ? <Loading /> : <>
        <p role="status">{results.data.count} bài khớp điều kiện.</p>
        {results.data.results.length ? <LibraryViews items={results.data.results} mode={value.view} sort={value.query.sort} preferenceKey={owner?owner+':collection:'+value.id:undefined} /> : <Empty>Chưa có bài khớp điều kiện.</Empty>}
        <PageControls offset={offset} nextOffset={results.data.next_offset} onChange={setOffset} />
      </>}
    </>}
  </section>;
}
