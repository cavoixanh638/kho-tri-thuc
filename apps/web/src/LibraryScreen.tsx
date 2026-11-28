import { LibraryViews, libraryModes, libraryLocationHref, parseLibraryLocation, type LibraryLocation, type LibraryFilter } from './LibraryViews';
import { knowledgeNodeHref, nodeKindLabels, type KnowledgeNode } from './KnowledgeTree';
import { SavedCollectionScreen, collectionIdFromHash } from './SavedCollections';
import { Button, SegmentedControl } from '@mantine/core';
import { useEffect, useState } from 'react';
import type { Item, Page } from './api';
import { itemNeedsRefresh } from './itemProcessing';
import { Empty, ErrorNotice, Loading, PageControls, PageTitle, useResource } from './views';
import { KnowledgeWorkspace, useKnowledgeWorkspace } from './KnowledgeWorkspace';

export function LibraryScreen({ csrf = '' }: { csrf?: string }) {
  const workspace = useKnowledgeWorkspace();
  return workspace ? <LibraryContent csrf={csrf} /> : <KnowledgeWorkspace csrf={csrf}><LibraryContent csrf={csrf} /></KnowledgeWorkspace>;
}

function LibraryContent({ csrf }: { csrf: string }) {
  const [scope, setScope] = useState(() => parseLibraryLocation(window.location.hash));
  const { filter, offset, view } = scope;
  const collectionId = collectionIdFromHash(window.location.hash);
  const { tree, revision } = useKnowledgeWorkspace()!;
  useEffect(() => {
    function changeScope() { setScope(parseLibraryLocation(window.location.hash)); }
    window.addEventListener('hashchange', changeScope);
    return () => window.removeEventListener('hashchange', changeScope);
  }, []);
  function navigate(patch: Partial<LibraryLocation>) {
    const next = { ...scope, ...patch };
    setScope(next);
    window.location.hash = libraryLocationHref(next);
  }
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

  return <>
    <PageTitle title="Thư viện" description="Đi từ kho con, lĩnh vực đến bộ sách, chương và từng bài tri thức. Một bài có thể xuất hiện trong nhiều nhánh." />
    {collectionId ? <SavedCollectionScreen csrf={csrf} id={collectionId === 'new' ? undefined : collectionId} /> : <section className="panel knowledge-library-content" aria-label="Danh sách mục">
      <nav className="knowledge-breadcrumb" aria-label="Đường dẫn mục lục">
        <a href={knowledgeNodeHref()}>Kho Tri Thức</a>
        {ancestors.map((node) => <span key={node.id}><span aria-hidden="true"> / </span><a href={knowledgeNodeHref(node.id)} aria-current={node.id === scope.id ? 'page' : undefined}>{node.name}</a></span>)}
        {scope.unfiled && <span> / Chưa xếp mục lục</span>}
      </nav>
      <div className="panel-heading"><h2>{selected?.name ?? (scope.id != null ? (tree.data ? 'Nhánh không còn truy cập được' : 'Đang tải nhánh') : scope.unfiled ? 'Chưa xếp mục lục' : 'Tất cả bài tri thức')}</h2>
        {selected && <span className="list-meta">{selected.item_count} bài trong nhánh · {selected.direct_count} bài xếp trực tiếp</span>}
      </div>
      {selected && <p className="list-meta">Bao gồm bài ở các nhánh con. Tạo hoặc chuyển ghi chú ngay trong cây thư mục; các lối tắt vẫn mở cùng một bài.</p>}
      {!scope.unfiled && children.length > 0 && <nav className="knowledge-child-branches" aria-label="Các nhánh con">
        {children.map((node) => <a key={node.id} href={knowledgeNodeHref(node.id)}><span><small>{nodeKindLabels[node.node_kind]}</small>{node.name}</span><span className="list-meta">{node.item_count} bài <span aria-hidden="true">›</span></span></a>)}
      </nav>}
      <div className="filters library-view-toolbar">
        <SegmentedControl value={filter} aria-label="Lọc thư viện" onChange={(value) => {
          navigate({ offset: 0, filter: value as LibraryFilter });
        }} data={[{ label: 'Tất cả', value: 'all' }, { label: 'Chưa phân loại', value: 'unclassified' }, { label: 'Yêu thích', value: 'favorite' }, { label: 'Thùng rác', value: 'deleted' }]} />
        <label>Cách xem <select aria-label="Cách xem thư viện" value={view} onChange={(event) => {
          const mode = libraryModes.find((entry) => entry.value === event.currentTarget.value);
          if (mode) navigate({ view: mode.value });
        }}>{libraryModes.map((mode) => <option key={mode.value} value={mode.value}>{mode.label}</option>)}</select></label>
      </div>
      {library.data && library.refreshError && <ErrorNotice retry={library.retry}>Chưa cập nhật được danh sách mới. Các mục đang hiển thị là lần kiểm tra trước.</ErrorNotice>}
      {library.data && library.pollingPaused && !library.refreshError && <div className="notice" role="status">
        <span>Tạm dừng cập nhật tự động.</span>
        <Button variant="default" size="compact-sm" onClick={library.retry}>Cập nhật danh sách</Button>
      </div>}
      {library.error ? <ErrorNotice retry={library.retry}>Chưa tải được thư viện.</ErrorNotice>
        : !library.data ? <Loading />
          : library.data.results.length ? <LibraryViews items={library.data.results} mode={view} />
            : <Empty>{filter === 'favorite' ? 'Chưa có mục yêu thích.' : filter === 'deleted' ? 'Thùng rác trống.' : <span>Chưa có mục nào. <a href="#/gui">Gửi vào kho</a></span>}</Empty>}
      {library.data && <PageControls offset={offset} nextOffset={library.data.next_offset} onChange={(value) => navigate({ offset: value })} />}
    </section>}
  </>;
}
