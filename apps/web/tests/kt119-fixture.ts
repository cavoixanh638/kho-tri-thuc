import corpus from '../../backend/catalog/fixtures/kt119-connections.json';
import type { Connections, SourcePart } from '../src/RelatedSources';
export { corpus };
const firstAsset = '20000000-0000-4000-8000-000000000001';
const secondAsset = '20000000-0000-4000-8000-000000000002';
const pendingAsset = '20000000-0000-4000-8000-000000000003';
const part = (id: number, overrides: Partial<SourcePart> = {}): SourcePart => ({ id, kind: 'document_text', status: 'active', processor: 'fixture-pdf', processor_version: 'v2', input_hash: 'a'.repeat(64), has_text: true, source_id: 1, asset_id: firstAsset, matches_current_asset: true, locator: { page: 3 }, ...overrides });
export const connections: Connections = {
  results: corpus.items.filter((item) => item.related).map((item) => ({ item_id: item.item_id, title: item.title, reason: item.reason, relation_type: item.relation_type, confidence: item.confidence, method_version: item.method_version, source_version: item.source_version })),
  backlinks: corpus.items.filter((item) => item.backlink).map((item, index) => ({ item_id: item.item_id, title: item.title, source_version: `note-edit:${index + 1}` })),
  same_group: corpus.items.filter((item) => item.same_group).map((item) => ({ item_id: item.item_id, title: item.title, groups: [{ kind: 'topic', id: 1, name: 'Nhóm đã cố định' }] })),
  counts: corpus.expected_counts,
  backlinks_scope: 'inline_markdown_only',
  evidence: {
    sources: [
      { source_id: 1, original_url: 'https://example.invalid/tri-thức', asset_ids: [firstAsset, secondAsset], parts: [] },
      { source_id: 2, original_url: 'https://example.invalid/text', asset_ids: [], parts: [part(4, { kind: 'web_text', source_id: 2, asset_id: null, matches_current_asset: null, locator: {} })] },
      { source_id: 3, original_url: 'javascript:alert(1)', asset_ids: [], parts: [] },
    ],
    assets: [
      { asset_id: firstAsset, filename: 'Tài liệu phiên bản 2.pdf', mime: 'application/pdf', content_version: 2, status: 'verified', parts: [part(1), part(2, { status: 'stale', processor_version: 'v1', input_hash: '0'.repeat(64), matches_current_asset: false, locator: {} })] },
      { asset_id: secondAsset, filename: 'Âm thanh nguồn.mp3', mime: 'audio/mpeg', content_version: 1, status: 'missing', parts: [part(3, { asset_id: secondAsset, kind: 'transcript', locator: { start_seconds: 12, end_seconds: 18 } })] },
      { asset_id: pendingAsset, filename: 'Tệp chờ xử lý.txt', mime: 'text/plain', content_version: 1, status: 'pending', parts: [] },
    ],
    unassociated_parts: [part(5, { source_id: null, asset_id: null, matches_current_asset: null, locator: {} })],
    truncated: false,
  },
};
