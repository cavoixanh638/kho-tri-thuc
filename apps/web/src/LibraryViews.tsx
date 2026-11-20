import type { Item } from './api';
import { knowledgePreview } from './KnowledgeText';
import { itemHref, itemTitle, kindLabels, ServerTime } from './views';
import './LibraryViews.css';

export type LibraryMode = 'list' | 'table' | 'card' | 'timeline';
export type LibraryFilter = 'all' | 'unclassified' | 'favorite' | 'deleted';
export type LibraryLocation = { id: number | null; unfiled: boolean; filter: LibraryFilter; offset: number; view: LibraryMode };
export const libraryModes: { value: LibraryMode; label: string }[] = [
  { value: 'list', label: 'Danh sách' }, { value: 'table', label: 'Bảng' },
  { value: 'card', label: 'Thẻ' }, { value: 'timeline', label: 'Theo ngày' },
];

export function parseLibraryLocation(hash: string): LibraryLocation {
  const params = new URLSearchParams(hash.split('?')[1] ?? '');
  const node = params.get('node');
  const id = node && /^[1-9]\d{0,14}$/.test(node) ? Number(node) : null;
  const rawOffset = params.get('offset') ?? '0';
  const offset = /^\d{1,7}$/.test(rawOffset) && Number(rawOffset) <= 1_000_000 && Number(rawOffset) % 50 === 0 ? Number(rawOffset) : 0;
  const view = libraryModes.find((mode) => mode.value === params.get('view'))?.value ?? 'list';
  const filter = ['all', 'unclassified', 'favorite', 'deleted'].includes(params.get('filter') ?? '') ? params.get('filter') as LibraryFilter : 'all';
  return { id, unfiled: id == null && params.get('unfiled') === '1', filter, offset, view };
}

export function libraryLocationHref(state: LibraryLocation) {
  const params = new URLSearchParams();
  if (state.id != null) params.set('node', String(state.id));
  else if (state.unfiled) params.set('unfiled', '1');
  if (state.filter !== 'all') params.set('filter', state.filter);
  if (state.offset) params.set('offset', String(state.offset));
  if (state.view !== 'list') params.set('view', state.view);
  return '#/thu-vien' + (params.size ? '?' + params : '');
}

function EntryText({ item }: { item: Item }) {
  return <span className="library-entry-text">
    <span className="capture-kind">{kindLabels[item.kind]}</span>
    <span className="library-entry-title">{itemTitle(item)}</span>
    {(item.note || item.knowledge_excerpt) && <span className="library-knowledge-preview">{knowledgePreview(item.note || item.knowledge_excerpt || '')}</span>}
    {item.assets.length > 0 && <span className="list-meta">{item.assets.length} tệp nguồn / minh họa</span>}
  </span>;
}

export function LibraryViews({ items, mode }: { items: Item[]; mode: LibraryMode }) {
  // All modes consume this server page in its original stable saved_at/id order.
  // No additional fetch, browser sorting or mutation of Item/Asset is performed.
  if (mode === 'table') return <div className="library-table-frame" role="region" aria-label="Bảng tri thức" tabIndex={0}>
    <table className="library-table"><caption>Thứ tự nhận lần đầu, mới nhất trước</caption>
      <thead><tr><th scope="col">Bài tri thức</th><th scope="col">Loại</th><th scope="col">Nhận lần đầu</th><th scope="col">Ngày nguồn đăng</th><th scope="col" className="library-number">Tệp minh họa</th></tr></thead>
      <tbody>{items.map((item) => <tr key={item.item_id} data-library-item={item.item_id}>
        <td><a href={itemHref(item.item_id)}>{itemTitle(item)}</a><p>{knowledgePreview(item.note || item.knowledge_excerpt || '')}</p></td>
        <td>{kindLabels[item.kind]}</td><td><ServerTime value={item.saved_at} /></td>
        <td>{item.published_at ? <ServerTime value={item.published_at} /> : '—'}</td><td className="library-number">{item.assets.length}</td>
      </tr>)}</tbody>
    </table>
  </div>;
  if (mode === 'timeline') {
    const groups = new Map<string, Item[]>();
    for (const item of items) {
      const day = new Intl.DateTimeFormat('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh', day: '2-digit', month: '2-digit', year: 'numeric' }).format(new Date(item.saved_at));
      const rows = groups.get(day) ?? [];
      rows.push(item); groups.set(day, rows);
    }
    return <div className="library-timeline"><p className="list-meta">Theo ngày nhận lần đầu (giờ Việt Nam), chỉ các bài trên trang hiện tại.</p>
      {[...groups].map(([day, rows]) => <section key={day} aria-label={'Nhận ngày ' + day}><h3>{day}</h3>
        <ul>{rows.map((item) => <li key={item.item_id} data-library-item={item.item_id}><a href={itemHref(item.item_id)} className="library-entry"><EntryText item={item} /><ServerTime value={item.saved_at} /></a></li>)}</ul>
      </section>)}
    </div>;
  }
  return <ul className={mode === 'card' ? 'library-cards' : 'library-list'}>
    {items.map((item) => <li key={item.item_id} data-library-item={item.item_id}>
      <a href={itemHref(item.item_id)} className="library-entry"><EntryText item={item} />
        <span className="library-entry-time"><span className="list-meta">Nhận lần đầu</span><ServerTime value={item.saved_at} /></span>
      </a>
    </li>)}
  </ul>;
}
