import type { Item } from './api';
import { kindLabels, ServerTime } from './views';
import './SavedCollections.css';

/** Read-only existing properties. Markdown templates do not create a typed schema. */
export function PropertyChips({ item, groups = [] }: { item: Item; groups?: { kind: string; name: string }[] }) {
  return <ul className="property-chips" aria-label="Thuộc tính hiện có">
    <li>Loại: {kindLabels[item.kind]}</li>
    <li>Nhận: <ServerTime value={item.saved_at} /></li>
    {item.published_at && <li>Ngày nguồn: <ServerTime value={item.published_at} /></li>}
    <li>{item.favorite ? 'Yêu thích' : 'Chưa đánh dấu yêu thích'}</li>
    {item.source_fetch && item.source_fetch !== 'not_applicable' && <li>Thu thập: {item.source_fetch}</li>}
    {item.content_extract && item.content_extract !== 'not_available' && <li>Trích văn bản: {item.content_extract}</li>}
    {groups.map((group, index) => <li key={group.kind + ':' + index}>{group.kind}: {group.name}</li>)}
  </ul>;
}
