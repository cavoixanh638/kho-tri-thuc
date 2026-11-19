import { Button, Select, TextInput } from '@mantine/core';
import { useEffect, useRef, useState, type SubmitEvent } from 'react';
import { ApiError, request } from './api';
import { Empty, ErrorNotice, Loading } from './views';

export type KnowledgeNode = {
  id: number; parent_id: number | null; name: string;
  node_kind: 'library' | 'field' | 'series' | 'book' | 'chapter' | 'folder';
  sort_order: number; depth: number; path_ids: number[]; path: string;
  direct_count: number; item_count: number; child_count: number;
};
export type KnowledgeTreeData = { nodes: KnowledgeNode[] };
export const nodeKindLabels: Record<KnowledgeNode['node_kind'], string> = {
  library: 'Kho con', field: 'Lĩnh vực', series: 'Bộ sách', book: 'Sách', chapter: 'Chương', folder: 'Nhánh',
};
export const knowledgeNodeHref = (id?: number | null) => id == null ? '#/thu-vien' : `#/thu-vien?node=${id}`;
type Editor = { node?: KnowledgeNode; parentId: number | null };

function NodeEditor({ nodes, editor, csrf, onCancel, onSaved }: {
  nodes: KnowledgeNode[]; editor: Editor; csrf: string; onCancel: () => void; onSaved: (node: KnowledgeNode) => void;
}) {
  const [name, setName] = useState(editor.node?.name ?? '');
  const [kind, setKind] = useState<KnowledgeNode['node_kind']>(editor.node?.node_kind ?? (editor.parentId == null ? 'library' : 'folder'));
  const [parentId, setParentId] = useState<string | null>(editor.parentId == null ? 'root' : String(editor.parentId));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const inFlight = useRef(false);
  const available = nodes.filter((node) => !editor.node || !node.path_ids.includes(editor.node.id));
  async function save(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (inFlight.current || !name.trim() || parentId == null) return;
    inFlight.current = true; setBusy(true); setError('');
    try {
      const node = await request<KnowledgeNode>(editor.node ? `/knowledge-tree/${editor.node.id}` : '/knowledge-tree', {
        method: editor.node ? 'PATCH' : 'POST', csrf,
        body: { name, node_kind: kind, parent_id: parentId === 'root' ? null : Number(parentId), sort_order: editor.node?.sort_order ?? 0 },
      });
      onSaved(node);
    } catch (failure) {
      setError(failure instanceof ApiError && failure.status === 422 ? 'Chưa lưu được. Kiểm tra tên trùng hoặc nhánh cha không còn hợp lệ.' : 'Chưa lưu được nhánh. Hãy thử lại.');
    } finally { inFlight.current = false; setBusy(false); }
  }
  return <section className="panel knowledge-node-editor" aria-label={editor.node ? 'Chỉnh nhánh mục lục' : 'Tạo nhánh mục lục'}>
    <h2>{editor.node ? 'Chỉnh nhánh mục lục' : 'Tạo nhánh mục lục'}</h2>
    <form className="form-stack" onSubmit={save}>
      <TextInput label="Tên nhánh" value={name} onChange={(event) => setName(event.currentTarget.value)} required maxLength={120} disabled={busy} autoFocus />
      <Select label="Loại nhánh" value={kind} disabled={busy} allowDeselect={false}
        data={Object.entries(nodeKindLabels).map(([value, label]) => ({ value, label }))}
        onChange={(value) => { if (value && Object.hasOwn(nodeKindLabels, value)) setKind(value as KnowledgeNode['node_kind']); }} />
      <Select label="Nằm trong" value={parentId} onChange={setParentId} searchable allowDeselect={false} disabled={busy}
        data={[{ value: 'root', label: 'Kho Tri Thức (cấp gốc)' }, ...available.map((node) => ({ value: String(node.id), label: node.path }))]} />
      <p className="list-meta">Loại nhánh giúp nhận biết mục lục. Bạn có thể chia nhỏ hoặc chuyển nhánh khi cần; bài tri thức giữ nguyên.</p>
      {error && <ErrorNotice>{error}</ErrorNotice>}
      <div className="form-actions"><Button type="submit" loading={busy} disabled={!name.trim() || parentId == null}>Lưu nhánh</Button><Button variant="default" onClick={onCancel} disabled={busy}>Hủy</Button></div>
    </form>
  </section>;
}

export function KnowledgeTree({ data, error, onRetry, selectedId, unfiled, csrf, onSaved }: {
  data?: KnowledgeTreeData; error?: boolean; onRetry: () => void; selectedId: number | null; unfiled: boolean; csrf: string; onSaved: (node: KnowledgeNode) => void;
}) {
  const [collapsed, setCollapsed] = useState<Set<number>>(() => new Set());
  const [editor, setEditor] = useState<Editor>();
  const nodes = data?.nodes ?? [];
  const selected = nodes.find((node) => node.id === selectedId);
  const ancestorPath = selected?.path_ids.join(':') ?? '';
  useEffect(() => {
    const ids = new Set(ancestorPath.split(':').filter(Boolean).map(Number));
    setCollapsed((previous) => previous.size ? new Set([...previous].filter((id) => !ids.has(id))) : previous);
  }, [ancestorPath]);
  const visible = nodes.filter((node) => !node.path_ids.slice(0, -1).some((id) => collapsed.has(id)));
  return <aside className="knowledge-tree-column" aria-label="Mục lục kho tri thức">
    <section className="panel knowledge-tree-panel">
      <div className="panel-heading"><h2>Mục lục</h2>{data && <Button variant="default" size="compact-sm" onClick={() => setEditor({ parentId: null })}>Thêm kho con</Button>}</div>
      <nav className="knowledge-tree" aria-label="Cây thư viện">
        <a className="knowledge-tree-root" href={knowledgeNodeHref()} aria-current={selectedId == null && !unfiled ? 'page' : undefined}>Toàn bộ tri thức</a>
        <a className="knowledge-tree-root" href="#/thu-vien?unfiled=1" aria-current={unfiled ? 'page' : undefined}>Chưa xếp mục lục</a>
        {error ? <ErrorNotice retry={onRetry}>Chưa tải được mục lục.</ErrorNotice> : !data ? <Loading /> : nodes.length ? <ul className="knowledge-tree-list">
          {visible.map((node) => <li key={node.id} style={{ paddingInlineStart: `${Math.min(node.depth, 12) * 14}px` }}>
            {node.child_count > 0 ? <button className="knowledge-tree-toggle" type="button" aria-label={`${collapsed.has(node.id) ? 'Mở' : 'Thu gọn'} ${node.name}`} aria-expanded={!collapsed.has(node.id)} onClick={() => setCollapsed((previous) => {
              const next = new Set(previous); if (next.has(node.id)) next.delete(node.id); else next.add(node.id); return next;
            })}>{collapsed.has(node.id) ? '›' : '⌄'}</button> : <span className="knowledge-tree-toggle" aria-hidden="true" />}
            <a href={knowledgeNodeHref(node.id)} aria-current={node.id === selectedId ? 'page' : undefined} title={node.path}><span>{node.name}<small>{nodeKindLabels[node.node_kind]}</small></span><span className="knowledge-tree-count">{node.item_count}</span></a>
          </li>)}
        </ul> : <Empty>Chưa có kho con. Tạo mục lục rồi xếp các bài vào nhánh phù hợp.</Empty>}
      </nav>
      {selected && <div className="knowledge-tree-actions"><Button variant="default" size="compact-sm" onClick={() => setEditor({ parentId: selected.id })}>Thêm nhánh con</Button><Button variant="subtle" size="compact-sm" onClick={() => setEditor({ node: selected, parentId: selected.parent_id })}>Đổi tên / chuyển nhánh</Button></div>}
    </section>
    {editor && <NodeEditor key={`${editor.node?.id ?? 'new'}:${editor.parentId}`} nodes={nodes} editor={editor} csrf={csrf} onCancel={() => setEditor(undefined)} onSaved={(node) => {
      setEditor(undefined); setCollapsed((previous) => new Set([...previous].filter((id) => !node.path_ids.includes(id)))); onSaved(node);
    }} />}
  </aside>;
}
