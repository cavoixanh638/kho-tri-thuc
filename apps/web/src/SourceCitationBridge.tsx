import { useState } from 'react';
import { ErrorNotice, Loading, useResource } from './views';
import { resolveLocator, SourceLocatorCitation, type SourcePart, type SourceViewer } from './SourceLocator';

export type CitationPart = SourcePart & { text: string; format: string };
type Knowledge = { origin: string; text: string; parts: CitationPart[]; truncated: boolean; needs_review: boolean };
type CitationProps = {
  parts: CitationPart[];
  sourceViewers?: SourceViewer[];
  onIllustration?: (assetId: string) => void;
  truncated?: boolean;
};

// Keep source/asset association by immutable IDs and extraction versions, never
// match on note text, filenames or list order. Mismatched host viewers are not trusted.
export function mapCitationParts(parts: CitationPart[], sourceViewers: SourceViewer[] = []) {
  return parts.map((part) => {
    const viewer = sourceViewers.find((entry) => entry.assetId === part.asset_id
      && entry.version === part.source?.version && entry.assetVersion === part.source?.asset_version)
      ?? sourceViewers.find((entry) => entry.assetId === part.asset_id);
    return { part, viewer, resolution: resolveLocator(part, viewer) };
  });
}

function sourceName(part: CitationPart): string {
  if (['video_transcript', 'transcript', 'subtitle', 'subtitles', 'caption', 'captions'].includes(part.kind)) return 'Bản chép lời';
  if (part.kind === 'web_text') return 'Trang web';
  if (part.source?.mime === 'application/pdf') return 'Tài liệu PDF';
  return 'Tài liệu nguồn';
}

export function SourceCitationList({ parts, sourceViewers = [], onIllustration, truncated = false }: CitationProps) {
  const [visible, setVisible] = useState(20);
  if (!parts.length) return null;
  const entries = mapCitationParts(parts, sourceViewers);
  return <section className="source-citations" aria-label="Dẫn chứng nguồn cho ghi chú">
    <h3>Dẫn chứng và vị trí trong nguồn ({parts.length})</h3>
    <p>Ghi chú do bạn biên soạn được giữ nguyên. Các trích đoạn dưới đây là bằng chứng riêng, không tự động xác nhận nội dung ghi chú.</p>
    <ol className="source-citations-list">
      {entries.slice(0, visible).map(({ part, viewer, resolution }, index) => <li key={part.id} data-part-id={part.id} data-citation-state={resolution.state}>
        <div className="source-citation-head"><strong>Nguồn {index + 1}: {sourceName(part)}</strong><span>{resolution.label}</span></div>
        <details className="source-citation-excerpt"><summary>Xem đoạn trích từ nguồn</summary>
          <p>{part.text.slice(0, 320)}{part.text.length > 320 ? '…' : ''}</p>
        </details>
        {part.processor === 'faster-whisper' && <p className="notice">Bản chép lời tự động; cần đối chiếu với âm thanh gốc.</p>}
        <SourceLocatorCitation part={part} viewer={viewer} onIllustration={onIllustration} />
      </li>)}
    </ol>
    {visible < entries.length && <button className="source-citations-more" type="button" onClick={() => setVisible((count) => Math.min(count + 20, entries.length))}>Xem thêm dẫn chứng ({entries.length - visible} còn lại)</button>}
    {truncated && <p className="notice">Danh sách/văn bản trích đã rút gọn; mở tệp gốc để kiểm tra đầy đủ.</p>}
  </section>;
}

/**
 * P06 host contract: mount immediately after authored KnowledgeText in
 * ItemScreen, before raw Markdown / source details. No host code is changed in
 * this PR (ItemScreen belongs to P01). The authenticated endpoint enforces
 * owner/deleted checks; never accept a caller-supplied raw note or source URL.
 *
 * Example for G00:
 *   {item.note && !item.deleted && <SourceCitationBridge id={item.item_id}
 *     refreshKey={evidenceRevision} onIllustration={showIllustration} />}
 */
export function SourceCitationBridge({ id, refreshKey, onIllustration, sourceViewers = [] }: {
  id: string; refreshKey?: string; onIllustration?: (assetId: string) => void; sourceViewers?: SourceViewer[];
}) {
  const content = useResource<Knowledge>(`/items/${encodeURIComponent(id)}/knowledge`, { refreshKey });
  if (content.error) return <ErrorNotice retry={content.retry}>Không đọc được dẫn chứng nguồn. Nội dung ghi chú của bạn không bị ảnh hưởng.</ErrorNotice>;
  if (!content.data) return <Loading label="Đang tải dẫn chứng nguồn" />;
  // Never render a second copy of the authored note, or conflate an
  // unauthored source reading with the saved Item.note.
  if (content.data.origin !== 'authored') return null;
  return <SourceCitationList parts={content.data.parts} sourceViewers={sourceViewers} onIllustration={onIllustration} truncated={content.data.truncated} />;
}
