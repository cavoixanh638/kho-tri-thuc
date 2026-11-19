import { Button } from '@mantine/core';
import { useState } from 'react';
import { Empty, ErrorNotice, Loading, useResource } from './views';
import { KnowledgeText } from './KnowledgeText';

type Part = { id: number; kind: string; text: string; processor?: string; locator: Record<string, unknown>; truncated: boolean };
type Content = { results: Part[]; next_offset: number | null };

function locationLabel(part: Part) {
  const { page, sheet, row, block } = part.locator;
  if (page !== undefined) return `Trang ${page}`;
  if (sheet !== undefined) return `Sheet ${sheet}${row === undefined ? '' : ` · dòng ${row}`}`;
  if (block !== undefined) return `Đoạn ${block}`;
  return part.kind === 'web_text' ? 'Văn bản nguồn web' : 'Văn bản đã trích';
}

export function ExtractedContent({ id, refreshKey }: { id: string; refreshKey?: string }) {
  const [offset, setOffset] = useState(0);
  const content = useResource<Content>(`/items/${encodeURIComponent(id)}/content?limit=5&offset=${offset}`, { refreshKey });
  return <section className="panel" aria-labelledby="extracted-content">
    <h2 id="extracted-content">Văn bản đã trích</h2>
    {content.error ? <ErrorNotice retry={content.retry}>Chưa tải được văn bản.</ErrorNotice>
      : !content.data ? <Loading />
        : content.data.results.length ? content.data.results.map((part, index) => <details key={part.id} className="content-part" open={index === 0}>
          <summary>{locationLabel(part)}</summary>
          {part.processor === 'utf-8-markdown' ? <KnowledgeText text={part.text} /> : <p className="prose-text">{part.text}</p>}
          {part.truncated && <p className="list-meta">Phần xem trước đã rút gọn. Mở tệp gốc để xem đầy đủ.</p>}
        </details>) : <Empty>Chưa có văn bản đã trích.</Empty>}
    {(offset > 0 || content.data?.next_offset != null) && <nav className="paging" aria-label="Các phần văn bản">
      <Button variant="default" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 5))}>Trang trước</Button>
      <Button variant="default" disabled={content.data?.next_offset == null} onClick={() => {
        if (content.data?.next_offset != null) setOffset(content.data.next_offset);
      }}>Trang sau</Button>
    </nav>}
  </section>;
}
