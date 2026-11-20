import { useResource, Empty, ErrorNotice, Loading } from './views';
import { KnowledgeText } from './KnowledgeText';
import { SourceLocatorCitation, transcriptSegments, type SourcePart, type SourceViewer } from './SourceLocator';

type Part = SourcePart & { text: string; format: string };
type Knowledge = { origin: string; text: string; parts: Part[]; truncated: boolean; needs_review: boolean };

export function KnowledgeReading({ id, refreshKey, onIllustration, sourceViewers = [] }: { id: string; refreshKey?: string; onIllustration: (assetId: string) => void; sourceViewers?: SourceViewer[] }) {
  const content = useResource<Knowledge>(`/items/${encodeURIComponent(id)}/knowledge`, { refreshKey });
  if (content.error) return <ErrorNotice retry={content.retry}>Chưa đọc được tri thức từ nguồn.</ErrorNotice>;
  if (!content.data) return <Loading label="Đang đọc văn bản tri thức" />;
  const data = content.data;
  if (data.origin === 'missing') return <Empty>Chưa lấy được văn bản nguồn. Video chỉ trở thành nội dung đọc được sau khi có phụ đề hoặc bản chép lời; bạn cũng có thể biên soạn trực tiếp.</Empty>;
  return <div>
    {data.needs_review && <p className="notice">Bản chép lời tự động trên Windows. Cần đối chiếu video trước khi dùng làm kiến thức đã biên soạn.</p>}
    {data.text && <KnowledgeText text={data.text} />}
    {data.parts.map((part) => {
      const segments = transcriptSegments(part.locator);
      const viewer = sourceViewers.find((entry) => entry.assetId === part.asset_id);
      return <div className="reading-source-part" key={part.id}>
        {segments.length ? segments.map((segment, index) => <div key={index}>
          <p className="prose-text">{segment.text}</p>
          <SourceLocatorCitation part={{ ...part, locator: segment.locator }} viewer={viewer} onIllustration={onIllustration} />
        </div>) : <>
          {part.format === 'markdown' ? <KnowledgeText text={part.text} /> : <p className="prose-text">{part.text}</p>}
          <SourceLocatorCitation part={part} viewer={viewer} onIllustration={onIllustration} />
        </>}
      </div>;
    })}
    {data.truncated && <p className="notice">Văn bản đang xem đã rút gọn; mở tài liệu nguồn hoặc các phần trích để xem thêm.</p>}
  </div>;
}
