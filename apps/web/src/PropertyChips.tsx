import type { Item } from './api';
import { kindLabels, ServerTime } from './views';
import './SavedCollections.css';

const states: Record<string, string> = { pending: 'Đang chờ', partial: 'Một phần', done: 'Hoàn tất', failed: 'Lỗi', not_available: 'Chưa có', not_applicable: 'Không áp dụng' };
/** Read-only existing properties. Markdown templates do not create a typed schema. */
export function PropertyChips({ item, groups = [] }: { item: Item; groups?: { kind: string; name: string }[] }) {
  return <ul className="property-chips" aria-label="Thuộc tính hiện có">
    <li>Loại: {kindLabels[item.kind]}</li>
    <li>Nhận: <ServerTime value={item.saved_at} /></li>
    {item.published_at && <li>Ngày nguồn: <ServerTime value={item.published_at} /></li>}
    <li>{item.favorite ? 'Yêu thích' : 'Chưa đánh dấu yêu thích'}</li>
    {item.source_fetch && item.source_fetch !== 'not_applicable' && <li>Thu thập: {states[item.source_fetch] ?? 'Chưa xác định'}</li>}
    {item.content_extract && item.content_extract !== 'not_available' && <li>Trích văn bản: {states[item.content_extract] ?? 'Chưa xác định'}</li>}
    {groups.map((group, index) => <li key={group.kind + ':' + index}>{group.kind}: {group.name}</li>)}
  </ul>;
}
