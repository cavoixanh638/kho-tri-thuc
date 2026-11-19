import { knowledgePreview } from './KnowledgeText';
import { KnowledgeTree, knowledgeNodeHref, nodeKindLabels, type KnowledgeNode, type KnowledgeTreeData } from './KnowledgeTree';
import { Button, SegmentedControl } from '@mantine/core';
import { useEffect, useState } from 'react';
import type { Item, Page } from './api';
import { itemNeedsRefresh } from './itemProcessing';
import { Empty, ErrorNotice, itemHref, itemTitle, kindLabels, Loading, PageControls, PageTitle, ServerTime, useResource } from './views';

type Filter = 'all' | 'unclassified' | 'favorite' | 'deleted';

function locationScope() {
  const params = new URLSearchParams(window.location.hash.split('?')[1] ?? '');
  const node = params.get('node');
  const id = node && /^[1-9]\d{0,14}$/.test(node) ? Number(node) : null;
  return { id, unfiled: id == null && params.get('unfiled') === '1' };
}

export function LibraryScreen({ csrf = '' }: { csrf?: string }) {
  const [filter, setFilter] = useState<Filter>('all');
  const [offset, setOffset] = useState(0);
  const [scope, setScope] = useState(locationScope);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    function changeScope() { setScope(locationScope()); setOffset(0); setFilter('all'); }
    window.addEventListener('hashchange', changeScope);
    return () => window.removeEventListener('hashchange', changeScope);
  }, []);
  const tree = useResource<KnowledgeTreeData>('/knowledge-tree', { refreshKey: String(revision) });
  const nodes = tree.data?.nodes ?? [];
  const selected = nodes.find((node) => node.id === scope.id);
  const ancestors = selected?.path_ids.map((id) => nodes.find((node) => node.id === id)).filter((node): node is KnowledgeNode => !!node) ?? [];
  const children = nodes.filter((node) => node.parent_id === scope.id);
  const query = new URLSearchParams({ limit: '50', offset: String(offset), deleted: String(filter === 'deleted') });
  if (scope.id != null) query.set('node_id', String(scope.id));
  if (scope.unfiled) query.set('unfiled', 'true');
  if (filter === 'unclassified') query.set('unclassified', 'true');
  if (filter === 'favorite') query.set('favorite', 'true');
  const library = useResource<Page<Item>>(`/items?${query}`, { pollWhile: (page) => page.results.some(itemNeedsRefresh), refreshKey: String(revision) });

  function saved(node: KnowledgeNode) {
    setRevision((value) => value + 1);
    setScope({ id: node.id, unfiled: false }); setOffset(0); setFilter('all');
    window.location.hash = knowledgeNodeHref(node.id);
  }

  return <>
    <PageTitle title="Thư viện" description="Đi từ kho con, lĩnh vực đến bộ sách, chương và từng bài tri thức. Một bài có thể xuất hiện trong nhiều nhánh." />
    <div className="knowledge-library-layout">
    <KnowledgeTree data={tree.data} error={tree.error} onRetry={tree.retry} selectedId={scope.id} unfiled={scope.unfiled} csrf={csrf} onSaved={saved} />
    <section className="panel knowledge-library-content" aria-label="Danh sách mục">
      <nav className="knowledge-breadcrumb" aria-label="Đường dẫn mục lục">
        <a href={knowledgeNodeHref()}>Kho Tri Thức</a>
        {ancestors.map((node) => <span key={node.id}><span aria-hidden="true"> / </span><a href={knowledgeNodeHref(node.id)} aria-current={node.id === scope.id ? 'page' : undefined}>{node.name}</a></span>)}
        {scope.unfiled && <span> / Chưa xếp mục lục</span>}
      </nav>
      <div className="panel-heading"><h2>{selected?.name ?? (scope.id != null ? (tree.data ? 'Nhánh không còn truy cập được' : 'Đang tải nhánh') : scope.unfiled ? 'Chưa xếp mục lục' : 'Tất cả bài tri thức')}</h2>
        {selected && <span className="list-meta">{selected.item_count} bài trong nhánh · {selected.direct_count} bài xếp trực tiếp</span>}
      </div>
      {selected && <p className="list-meta">Bao gồm bài ở các nhánh con. Để xếp bài, mở bài và chọn Chỉnh nhóm.</p>}
      {!scope.unfiled && children.length > 0 && <nav className="knowledge-child-branches" aria-label="Các nhánh con">
        {children.map((node) => <a key={node.id} href={knowledgeNodeHref(node.id)}><span><small>{nodeKindLabels[node.node_kind]}</small>{node.name}</span><span className="list-meta">{node.item_count} bài <span aria-hidden="true">›</span></span></a>)}
      </nav>}
      <div className="filters">
        <SegmentedControl value={filter} aria-label="Lọc thư viện" onChange={(value) => {
          setOffset(0);
          setFilter(value as Filter);
        }} data={[{ label: 'Tất cả', value: 'all' }, { label: 'Chưa phân loại', value: 'unclassified' }, { label: 'Yêu thích', value: 'favorite' }, { label: 'Thùng rác', value: 'deleted' }]} />
      </div>
      {library.data && library.refreshError && <ErrorNotice retry={library.retry}>Chưa cập nhật được danh sách mới. Các mục đang hiển thị là lần kiểm tra trước.</ErrorNotice>}
      {library.data && library.pollingPaused && !library.refreshError && <div className="notice" role="status">
        <span>Tạm dừng cập nhật tự động.</span>
        <Button variant="default" size="compact-sm" onClick={library.retry}>Cập nhật danh sách</Button>
      </div>}
      {library.error ? <ErrorNotice retry={library.retry}>Chưa tải được thư viện.</ErrorNotice>
        : !library.data ? <Loading />
          : library.data.results.length ? <ul className="library-list">
            {library.data.results.map((item) => <li key={item.item_id}>
              <a href={itemHref(item.item_id)} className="library-entry">
                <span className="library-entry-text">
                  <span className="capture-kind">{kindLabels[item.kind]}</span>
                  <span className="library-entry-title">{itemTitle(item)}</span>
                  {(item.note || item.knowledge_excerpt) && <span className="library-knowledge-preview">{knowledgePreview(item.note || item.knowledge_excerpt || '')}</span>}
                  {item.assets.length > 0 && <span className="list-meta">{item.assets.length} tệp nguồn / minh họa</span>}
                </span>
                <span className="library-entry-time"><span className="list-meta">Nhận lần đầu</span><ServerTime value={item.saved_at} /></span>
              </a>
            </li>)}
          </ul>
            : <Empty>{filter === 'favorite' ? 'Chưa có mục yêu thích.' : filter === 'deleted' ? 'Thùng rác trống.' : <span>Chưa có mục nào. <a href="#/gui">Gửi vào kho</a></span>}</Empty>}
      {library.data && <PageControls offset={offset} nextOffset={library.data.next_offset} onChange={setOffset} />}
    </section>
    </div>
  </>;
}
