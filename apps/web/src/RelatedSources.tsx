import { Button } from '@mantine/core';
import { useState } from 'react';
import { externalHttpUrl } from './api';
import { Empty, ErrorNotice, itemHref, Loading, useResource } from './views';
import './related-sources.css';

export type RelatedHit = { item_id: string; title: string; reason: string; relation_type: string; confidence: number | null; method_version: string; source_version: string };
export type Backlink = { item_id: string; title: string; source_version: string };
export type SameGroup = { item_id: string; title: string; groups: { kind: string; id: number; name: string }[] };
export type SourcePart = { id: number; kind: string; status: string; processor: string; processor_version: string; input_hash: string; has_text: boolean; source_id: number | null; asset_id: string | null; matches_current_asset: boolean | null; locator: { page?: number; start_seconds?: number; end_seconds?: number } };
export type SourceAsset = { asset_id: string; filename: string; mime: string; content_version: number; status: string; parts: SourcePart[] };
export type SourceCard = { source_id: number; original_url: string; asset_ids: string[]; parts: SourcePart[] };
export type Connections = {
  results: RelatedHit[]; backlinks?: Backlink[]; same_group?: SameGroup[];
  counts?: { related: number; backlinks: number; same_group: number };
  backlinks_scope?: string;
  evidence?: { sources: SourceCard[]; assets: SourceAsset[]; unassociated_parts: SourcePart[]; truncated: boolean };
};
const uuid = /^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$/i;
const safeHits = <T extends { item_id: string }>(rows: T[], current: string) => rows.filter((row) => uuid.test(row.item_id) && row.item_id !== current);
const storage: Record<string, string> = { verified: 'VERIFIED · Đã xác minh trên Drive', missing: 'MISSING · Không tìm thấy trên Drive', pending: 'PENDING · Đang chờ', failed: 'FAILED · Lưu thất bại', inaccessible: 'INACCESSIBLE · Chưa truy cập được' };

function PartEvidence({ part }: { part: SourcePart }) {
  const current = part.status === 'active' && part.matches_current_asset !== false;
  const locator = current ? part.locator : {};
  return <li>
    <span>{part.has_text ? 'Có văn bản trích' : 'Chưa có văn bản trích'} · {part.status === 'active' ? 'Hiện hành' : part.status === 'stale' ? 'Bản cũ' : 'Trích xuất lỗi'}</span>
    <span className="list-meta">{part.processor} · phiên bản {part.processor_version || 'chưa ghi'} · phần {part.id}</span>
    {part.matches_current_asset === false && <span className="list-meta">Hash đầu vào khác tệp hiện tại; chưa xác minh cho phiên bản này.</span>}
    {current && locator.page != null && <span className="list-meta">Trang {locator.page}</span>}
    {current && locator.start_seconds != null && <span className="list-meta">Mốc {locator.start_seconds}{locator.end_seconds != null ? `–${locator.end_seconds}` : ''} giây</span>}
    <details><summary>Phiên bản đầu vào</summary><code>{part.input_hash || 'Chưa có hash'}</code></details>
  </li>;
}

export function SourceEvidence({ evidence, onOpenAsset }: { evidence: NonNullable<Connections['evidence']>; onOpenAsset?: (id: string) => void }) {
  const assets = evidence.assets.filter((asset) => uuid.test(asset.asset_id));
  const byId = new Map(assets.map((asset) => [asset.asset_id, asset]));
  return <section className="related-sources" aria-label="Bằng chứng nguồn và tệp">
    <h3>Nguồn và phiên bản tệp</h3>
    {!evidence.sources.length && !assets.length && !evidence.unassociated_parts.length && <Empty>Chưa có nguồn hoặc tệp đính kèm.</Empty>}
    {evidence.sources.map((source) => {
      const url = externalHttpUrl(source.original_url);
      return <article className="related-source-card" key={source.source_id}>
        <h4>Nguồn {source.source_id}</h4>
        <p>{url ? <a href={url} target="_blank" rel="noopener noreferrer">{source.original_url}</a> : <span>{source.original_url || 'Chưa có URL gốc'}</span>}</p>
        {!url && source.original_url && <p className="list-meta">URL không được mở vì định dạng không an toàn.</p>}
        <ul className="related-asset-references">{source.asset_ids.filter((id) => byId.has(id)).map((id) => <li key={id}><a href={`#related-asset-${id}`} onClick={(event) => {
          event.preventDefault(); document.getElementById(`related-asset-${id}`)?.focus();
        }}>{byId.get(id)!.filename || 'Tệp đính kèm'}</a></li>)}</ul>
        {!source.asset_ids.length && <p className="list-meta">Chưa có bằng chứng nối nguồn này với một tệp.</p>}
        {source.parts.length ? <ul className="related-part-list">{source.parts.map((part) => <PartEvidence part={part} key={part.id} />)}</ul> : <p className="list-meta">Chưa có văn bản trích trực tiếp từ URL này.</p>}
      </article>;
    })}
    {assets.map((asset) => <article className="related-source-card" id={`related-asset-${asset.asset_id}`} tabIndex={-1} key={asset.asset_id}>
      <h4>{asset.filename || 'Tệp đính kèm'}</h4>
      <p>{storage[asset.status] || 'Chưa rõ trạng thái lưu trữ'} · tệp phiên bản {asset.content_version}</p>
      {onOpenAsset && <Button type="button" variant="subtle" onClick={() => onOpenAsset(asset.asset_id)}>Mở tệp</Button>}
      {asset.parts.length ? <ul className="related-part-list">{asset.parts.map((part) => <PartEvidence part={part} key={part.id} />)}</ul> : <p className="list-meta">Chưa có văn bản trích từ tệp.</p>}
    </article>)}
    {!!evidence.unassociated_parts.length && <details><summary>Phần trích chưa xác minh liên kết nguồn/tệp ({evidence.unassociated_parts.length})</summary>
      <ul className="related-part-list">{evidence.unassociated_parts.map((part) => <PartEvidence part={{ ...part, locator: {} }} key={part.id} />)}</ul>
    </details>}
    {evidence.truncated && <p className="notice">Danh sách nguồn đang được giới hạn; đây chưa phải toàn bộ bằng chứng.</p>}
  </section>;
}

function ConnectionsContent({ id, data, onOpenAsset }: { id: string; data: Connections; onOpenAsset?: (id: string) => void }) {
  const [hidden, setHidden] = useState<Set<string>>(() => new Set());
  const related = safeHits(data.results ?? [], id);
  const backlinks = safeHits(data.backlinks ?? [], id);
  const sameGroup = safeHits(data.same_group ?? [], id);
  const shown = related.filter((entry) => !hidden.has(entry.item_id));
  return <>
    <section className="related-section" aria-labelledby="item-related-title">
      <h2 id="item-related-title">Liên quan đến bài này ({data.counts?.related ?? related.length})</h2>
      <p className="list-meta">Gợi ý liên quan có lý do; không phải liên kết ngược hay kết luận hai bài là một.</p>
      {shown.length ? <ul className="search-list related-items">{shown.map((entry) => <li className="search-result" key={entry.item_id}>
        <h3><a href={itemHref(entry.item_id)}>{entry.title || 'Mở bài liên quan'}</a></h3>
        <p>{entry.reason || 'Chưa ghi lý do'}</p>
        <p className="list-meta">{entry.relation_type === 'similar' ? 'Gợi ý tương đồng' : `Quan hệ: ${entry.relation_type || 'chưa ghi'}`} · phương pháp {entry.method_version || 'chưa ghi'} · nguồn {entry.source_version || 'chưa ghi'}</p>
        {entry.confidence != null && Number.isFinite(entry.confidence) && <p className="list-meta">Điểm {entry.confidence.toLocaleString('vi-VN', { maximumFractionDigits: 3 })}; không phải xác suất đã kiểm chứng.</p>}
        {entry.relation_type === 'similar' && <Button type="button" variant="subtle" size="compact-sm" onClick={() => setHidden((old) => new Set(old).add(entry.item_id))}>Ẩn gợi ý trong lần xem này</Button>}
      </li>)}</ul> : <Empty>Chưa có gợi ý liên quan đang hiển thị.</Empty>}
      {!!hidden.size && <div role="status"><p>Đã ẩn {hidden.size} gợi ý trong lần xem này. Dữ liệu và nhóm đã cố định vẫn được giữ.</p><Button type="button" variant="subtle" onClick={() => setHidden(new Set())}>Hiện lại gợi ý</Button></div>}
      {data.counts && data.counts.related > related.length && <p className="list-meta">Đang hiển thị tối đa {related.length} trong {data.counts.related} mục.</p>}
    </section>
    <section className="related-section" aria-labelledby="item-backlinks-title">
      <h2 id="item-backlinks-title">Bài này được nhắc từ ({data.counts?.backlinks ?? backlinks.length})</h2>
      <p className="list-meta">Hiện nhận liên kết trực tiếp trong Markdown. Liên kết tham chiếu, HTML và các kiểu liên kết khác chưa được hỗ trợ.</p>
      {backlinks.length ? <ul className="related-link-list">{backlinks.map((entry) => <li key={entry.item_id}><a href={itemHref(entry.item_id)}>{entry.title || 'Mở bài nhắc đến mục này'}</a><span className="list-meta">Liên kết Markdown trực tiếp · {entry.source_version}</span></li>)}</ul> : <Empty>Chưa tìm thấy liên kết trực tiếp được hỗ trợ.</Empty>}
      {data.counts && data.counts.backlinks > backlinks.length && <p className="list-meta">Đang hiển thị {backlinks.length} trong {data.counts.backlinks} bài.</p>}
    </section>
    <section className="related-section" aria-labelledby="item-samegroup-title">
      <h2 id="item-samegroup-title">Cùng nhóm ({data.counts?.same_group ?? sameGroup.length})</h2>
      <p className="list-meta">Chung nhóm đang có; chưa xác nhận tương đồng nội dung.</p>
      {sameGroup.length ? <ul className="related-link-list">{sameGroup.map((entry) => <li key={entry.item_id}><a href={itemHref(entry.item_id)}>{entry.title || 'Mở bài cùng nhóm'}</a><span className="list-meta">{entry.groups.map((group) => group.name).join(' · ')}</span></li>)}</ul> : <Empty>Chưa có bài cùng nhóm.</Empty>}
      {data.counts && data.counts.same_group > sameGroup.length && <p className="list-meta">Đang hiển thị {sameGroup.length} trong {data.counts.same_group} bài.</p>}
    </section>
    {data.evidence ? <SourceEvidence evidence={data.evidence} onOpenAsset={onOpenAsset} /> : <p className="list-meta">Chưa tải được bằng chứng nguồn/phiên bản từ API này.</p>}
  </>;
}

export function RelatedSources({ id, refreshKey, onOpenAsset }: { id: string; refreshKey?: string; onOpenAsset?: (id: string) => void }) {
  const related = useResource<Connections>(`/items/${encodeURIComponent(id)}/related`, { refreshKey });
  return <section className="panel related-connections" aria-label="Liên hệ và bằng chứng nguồn">
    {related.error ? <ErrorNotice retry={related.retry}>Chưa tải được liên hệ và bằng chứng nguồn.</ErrorNotice>
      : !related.data ? <Loading /> : <ConnectionsContent key={id} id={id} data={related.data} onOpenAsset={onOpenAsset} />}
  </section>;
}
