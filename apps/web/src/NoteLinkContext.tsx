import { Empty, ErrorNotice, useResource } from './views';
import './NoteNavigation.css';
type Hit = { item_id: string; title: string };
type Links = { outgoing?: Hit[]; unlinked?: Hit[]; truncated?: boolean; unavailable_outgoing_count?: number };
export function NoteLinkContext({ id, refreshKey }: { id: string; refreshKey?: string }) {
  const resource = useResource<Links>(`/items/${encodeURIComponent(id)}/links`, { refreshKey });
  const data = resource.data;
  if (resource.error) return <ErrorNotice retry={resource.retry}>Chưa tải được liên kết và các lần nhắc tên.</ErrorNotice>;
  if (!data) return null;
  return <section className="note-link-context" aria-label="Liên kết đi và nhắc tên chưa liên kết">
    <h2>Liên kết do bạn tạo</h2>
    <h3>Liên kết đi</h3>
    {data.outgoing?.length ? <ul>{data.outgoing.map((hit) => <li key={hit.item_id}><a href={'#/muc/' + hit.item_id}>{hit.title || 'Mở bài'}</a><small>{hit.item_id}</small></li>)}</ul> : <Empty>Chưa có liên kết trực tiếp đến bài khác.</Empty>}
    {!!data.unavailable_outgoing_count && <p role="status">{data.unavailable_outgoing_count} liên kết có đích đã xóa, không tồn tại hoặc không có quyền truy cập. Markdown gốc vẫn được giữ.</p>}
    <h3>Nhắc tên chưa liên kết — chỉ là gợi ý</h3>
    <p>Các bài này có nhắc tên bài hiện tại. Chưa tạo liên kết hay quan hệ cha–con.</p>
    {data.unlinked?.length ? <ul>{data.unlinked.map((hit) => <li key={hit.item_id}><a href={'#/muc/' + hit.item_id}>{hit.title || 'Mở bài'}</a><small>{hit.item_id}</small></li>)}</ul> : <Empty>Chưa tìm thấy ứng viên nhắc tên.</Empty>}
    {data.truncated && <p>Danh sách đang giới hạn; dùng tìm kiếm để xem thêm.</p>}
  </section>;
}
