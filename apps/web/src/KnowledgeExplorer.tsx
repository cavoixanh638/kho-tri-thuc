import { Button, Textarea, TextInput } from '@mantine/core';
import { useEffect, useId, useRef, useState, type DragEvent, type KeyboardEvent, type ReactNode } from 'react';
import { ApiError, request, type Receipt } from './api';
import { NodeEditor, knowledgeNodeHref, nodeKindLabels, type Editor, type KnowledgeNode, type KnowledgeTreeData } from './KnowledgeTree';
import { Empty, ErrorNotice, itemHref, Loading } from './views';
import './KnowledgeExplorer.css';
import { StructureParentEditor } from './ItemStructurePanel';

export type ExplorerNote = { item_id: string; title: string; kind: string; home_topic_id: number | null; parent_item_id: string | null; sort_order: number; structure_version: number; child_count: number; shortcut: boolean; source_fetch: string; asset_storage: string };
type Folder = Pick<KnowledgeNode, 'id' | 'name' | 'node_kind' | 'parent_id' | 'sort_order' | 'direct_count'>;
type Page = { folders: Folder[]; notes: ExplorerNote[]; next_offset: number | null };
type CreateAt = { folder: number | null; parent?: string; label: string };
type Context = { csrf: string; nodes: KnowledgeNode[]; selected: number | null; selectedNote?: string; revision: number; cache: Map<string, Page>; onChanged: () => void; editFolder: (node: KnowledgeNode) => void; create: (at: CreateAt) => void; expanded: Set<string>; toggle: (key: string, open?: boolean) => void; selectedPath: number[] };
const failure = (error: unknown) => error instanceof ApiError && error.status === 409 ? 'Cấu trúc đã đổi ở phiên khác. Tải lại cây rồi thử lại.' : 'Chưa thực hiện được. Kiểm tra quyền, vị trí hoặc chu trình; nội dung vẫn được giữ.';

function NoteMenu({ note, context }: { note: ExplorerNote; context: Context }) {
  const removeHint = useId();
  const [menuOpen, setMenuOpen] = useState(false);
  const [folder, setFolder] = useState('');
  const [title, setTitle] = useState(note.title);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function move(action: 'move' | 'add' | 'remove') {
    setBusy(true); setError('');
    try {
      await request('/items/' + note.item_id + '/placement', { method:'PATCH', csrf:context.csrf, body:{action, folder_id:folder ? Number(folder) : null, expected_version:note.structure_version} });
      context.onChanged();
    } catch(error) { setError(failure(error)); } finally { setBusy(false); }
  }
  async function rename() {
    setBusy(true); setError('');
    try {
      const latest = await request<{user_edit_version:number}>('/items/' + note.item_id);
      await request('/items/' + note.item_id, {method:'PATCH',csrf:context.csrf,body:{title,expected_edit_version:latest.user_edit_version}});
      context.onChanged();
    } catch(error) { setError(failure(error)); } finally { setBusy(false); }
  }
  return <details className="explorer-note-menu" onToggle={(event)=>setMenuOpen(event.currentTarget.open)}><summary aria-label={'Thao tác ghi chú ' + note.title}>Thao tác</summary>{menuOpen && <div className="explorer-menu">
    <a href={itemHref(note.item_id)}>Mở ghi chú</a>
    <label>Đổi tên ghi chú<input value={title} maxLength={512} disabled={busy} onChange={(event)=>setTitle(event.currentTarget.value)}/></label>
    <Button size="compact-sm" variant="default" disabled={busy || !title.trim()} onClick={()=>void rename()}>Lưu tên</Button>
    <label>Thư mục đích<select value={folder} disabled={busy} onChange={(event)=>setFolder(event.currentTarget.value)}><option value="">Chưa xếp thư mục</option>{context.nodes.map((node)=><option key={node.id} value={node.id}>{node.path}</option>)}</select></label>
    <Button size="compact-sm" variant="default" disabled={busy} onClick={()=>void move('move')}>Chuyển vị trí chính</Button>
    <Button size="compact-sm" variant="default" disabled={busy || !folder} onClick={()=>void move('add')}>Thêm vào nhánh khác</Button>
    <Button size="compact-sm" variant="default" disabled={busy || !folder} aria-describedby={removeHint} onClick={()=>void move('remove')}>Bỏ khỏi nhánh đã chọn</Button>
    <small id={removeHint}>Sau khi gỡ, hệ thống sẽ đợi bạn thêm lại ghi chú vào nhánh đó.</small>
    <Button size="compact-sm" variant="default" disabled={busy} onClick={()=>context.create({folder:note.home_topic_id,parent:note.item_id,label:note.title})}>Tạo ghi chú con</Button>
    <StructureParentEditor id={note.item_id} version={note.structure_version} currentParent={note.parent_item_id} csrf={context.csrf} onSaved={context.onChanged}/>
    {error && <ErrorNotice>{error}</ErrorNotice>}
  </div>}</details>;
}

function ExplorerIcon({ kind, open = false }: {kind: 'folder' | 'note' | 'link' | 'chevron'; open?: boolean}) {
  return <svg className={'explorer-icon explorer-icon-' + kind + (open ? ' is-open' : '')}
    width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {kind === 'chevron' ? <path d="m9 6 6 6-6 6"/> :
      kind === 'folder' ? (open ? <path d="M3 7h7l2 2h9l-3 11H3z M3 7V4h7l2 3h8v2"/> : <path d="M3 6h7l2 2h9v12H3z"/>) :
      kind === 'link' ? <path d="M7 17 17 7M7 7h10v10"/> : <path d="M6 3h8l4 4v14H6z M14 3v5h4 M9 12h6 M9 16h6"/>}
  </svg>;
}

/** Animate intrinsic height, never a guessed max-height. Unmount a closed
 * branch after the transition; the bounded in-memory page cache makes reopening
 * immediate. Closing content cannot receive focus or keyboard navigation. */
function BranchReveal({ open, children }: {open: boolean; children: ReactNode}) {
  const [retained, setRetained] = useState(open);
  useEffect(() => {
    if (open) { setRetained(true); return; }
    if (!retained) return;
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
      setRetained(false); return;
    }
    const timer = window.setTimeout(() => setRetained(false), 190);
    return () => window.clearTimeout(timer);
  }, [open, retained]);
  return <div className={'explorer-branch-reveal' + (open ? ' is-open' : '')} aria-hidden={!open} inert={!open}>
    <div className="explorer-branch-inner">{(open || retained) && children}</div>
  </div>;
}

function Branch({ context, folder, parent, unfiled = false }: { context: Context; folder?: number | null; parent?: string; unfiled?: boolean }) {
  const scope = JSON.stringify([folder,parent,unfiled,context.revision]);
  const [page, setPage] = useState<Page>(() => context.cache.get(scope)!);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const current = useRef(0);
  async function load(offset = 0, signal?: AbortSignal) {
    const run = ++current.current; setBusy(true); setError('');
    const query = new URLSearchParams({offset:String(offset),limit:'50'});
    if(folder != null) query.set('folder_id',String(folder));
    if(parent) query.set('parent_item_id',parent);
    if(unfiled) query.set('unfiled','true');
    try {
      const next = await request<Page>('/explorer/children?' + query, {signal});
      if(!Array.isArray(next.folders)||!Array.isArray(next.notes))throw Error('invalid_explorer_page');
      if(run === current.current) setPage(previous => {
        const value = offset && previous ? {folders:[...previous.folders,...next.folders],notes:[...previous.notes,...next.notes],next_offset:next.next_offset} : next;
        context.cache.set(scope,value);
        if (context.cache.size > 160) {
          const first = context.cache.keys().next().value;
          if (first !== undefined) context.cache.delete(first);
        }
        return value;
      });
    } catch(error) { if(!signal?.aborted && run === current.current) setError(failure(error)); }
    finally { if(run === current.current) setBusy(false); }
  }
  useEffect(()=>{const controller=new AbortController();const cached=context.cache.get(scope);if(cached)setPage(cached);else void load(0,controller.signal);return()=>{controller.abort();current.current++;};},[scope]);
  async function drop(event: DragEvent, target: Folder) {
    event.preventDefault(); event.stopPropagation(); setError('');
    try {
      const value = JSON.parse(event.dataTransfer.getData('application/x-kho-tri-thuc'));
      if(value.kind === 'note' && typeof value.id === 'string') {
        await request('/items/' + encodeURIComponent(value.id) + '/placement',{method:'PATCH',csrf:context.csrf,body:{action:event.ctrlKey?'add':'move',folder_id:target.id,expected_version:value.version}});
      } else if(value.kind === 'folder' && Number.isInteger(value.id)) {
        const node=context.nodes.find((node)=>node.id===value.id);if(!node)throw Error();
        await request('/knowledge-tree/' + node.id,{method:'PATCH',csrf:context.csrf,body:{name:node.name,node_kind:node.node_kind,parent_id:target.id,sort_order:node.sort_order}});
      } else throw Error();
      context.onChanged();
    }catch(error){setError(failure(error));}
  }
  if(!page && !error) return <Loading label="Đang tải thư mục và ghi chú"/>;
  return <>{error && <ErrorNotice retry={()=>void load()}>{error}</ErrorNotice>}<ul className="explorer-list" role="group">
    {page?.folders.map((node)=>{
      const key='folder:'+node.id,open=context.expanded.has(key);
      return <li key={key} role="treeitem" aria-expanded={open} className="explorer-tree-item explorer-folder-item" tabIndex={0}>
        <div className="explorer-row" onDragOver={(event)=>event.preventDefault()} onDrop={(event)=>void drop(event,node)} draggable onDragStart={(event)=>{event.stopPropagation();event.dataTransfer.setData('application/x-kho-tri-thuc',JSON.stringify({kind:'folder',id:node.id}));}}>
          <button type="button" aria-label={(open?'Thu gọn ':'Mở ')+node.name} onClick={()=>context.toggle(key,!open)}><ExplorerIcon kind="chevron" open={open}/></button>
          <a href={knowledgeNodeHref(node.id)} aria-current={context.selected===node.id&&!context.selectedNote?'page':undefined} title={node.name + " · " + nodeKindLabels[node.node_kind]}><ExplorerIcon kind="folder" open={open}/><span className="explorer-name">{node.name}</span></a>
          <span className="explorer-count">{context.nodes.find((entry)=>entry.id===node.id)?.item_count??node.direct_count}</span>
          <button type="button" aria-label={'Chỉnh thư mục '+node.name} onClick={()=>{const full=context.nodes.find((entry)=>entry.id===node.id);if(full)context.editFolder(full);}} className="explorer-edit">⋯</button>
        </div>
        <BranchReveal open={open}><Branch context={context} folder={node.id}/></BranchReveal>
      </li>;
    })}
    {page?.notes.map((note)=>{
      const key='note:'+note.item_id,open=context.expanded.has(key);
      return <li key={key} role="treeitem" aria-expanded={note.child_count ? open : undefined} className="explorer-tree-item explorer-note-item" tabIndex={0}>
        <div className="explorer-row" draggable onDragStart={(event)=>{event.stopPropagation();event.dataTransfer.setData('application/x-kho-tri-thuc',JSON.stringify({kind:'note',id:note.item_id,version:note.structure_version}));}}>
          {note.child_count>0?<button type="button" aria-label={(open?'Thu gọn bài ':'Mở bài con ')+note.title} onClick={()=>context.toggle(key)}><ExplorerIcon kind="chevron" open={open}/></button>:<span className="explorer-leaf-spacer" aria-hidden="true"/>}
          <a href={itemHref(note.item_id)} aria-current={context.selectedNote===note.item_id?'page':undefined} title={note.title + (note.shortcut?' · Lối tắt':'') }><ExplorerIcon kind={note.kind==='link'?'link':'note'}/><span className="explorer-name">{note.title}</span>{note.shortcut&&<span className="explorer-shortcut" aria-label="Lối tắt">↗</span>}</a>
        </div>
        <NoteMenu note={note} context={context}/>
        {note.child_count>0 && <BranchReveal open={open}><Branch context={context} parent={note.item_id}/></BranchReveal>}
      </li>;
    })}
    {page && !page.folders.length && !page.notes.length && <li><Empty>Chưa có thư mục hoặc ghi chú tại đây.</Empty></li>}
    {page?.next_offset != null && <li><Button variant="subtle" disabled={busy} onClick={()=>void load(page.next_offset!)}>Tải thêm thư mục / ghi chú</Button></li>}
  </ul></>;
}

export function KnowledgeExplorer({ data, error, onRetry, selectedId, selectedNoteId, selectedNoteAncestors, refreshRevision, unfiled, csrf, onSaved }: {
  data?:KnowledgeTreeData;error?:boolean;onRetry:()=>void;selectedId:number|null;selectedNoteId?:string;selectedNoteAncestors?:string[];refreshRevision?:number;unfiled:boolean;csrf:string;onSaved:(node:KnowledgeNode)=>void;
}) {
  const [expanded,setExpanded]=useState<Set<string>>(()=>new Set());
  const [editor,setEditor]=useState<Editor>();
  const [createAt,setCreateAt]=useState<CreateAt>();
  const [localRevision,setRevision]=useState(0);
  const revision=refreshRevision ?? localRevision;
  const cache=useRef(new Map<string, Page>());
  const [newTitle,setNewTitle]=useState('');
  const [text,setText]=useState('');
  const [busy,setBusy]=useState(false);
  const [notice,setNotice]=useState('');
  const [failureText,setFailure]=useState('');
  const attempt=useRef<string | undefined>(undefined);
  const selected=data?.nodes.find((node)=>node.id===selectedId);
  const nodes=data?.nodes??[];
  const ancestorKey=selected?.path_ids.join(':')??'';
  useEffect(()=>{if(!ancestorKey)return;setExpanded((old)=>new Set([...old,...ancestorKey.split(':').map((id)=>'folder:'+id)]));},[ancestorKey]);
  const noteAncestorKey=selectedNoteAncestors?.join(':')??'';
  useEffect(()=>{if(!noteAncestorKey)return;setExpanded(old=>new Set([...old,...noteAncestorKey.split(':').map(id=>'note:'+id)]));},[noteAncestorKey]);
  const changed=()=>{setRevision((value)=>value+1);onRetry();};
  const context:Context={csrf,nodes,selected:selectedId,selectedNote:selectedNoteId,revision,cache:cache.current,onChanged:changed,editFolder:(node)=>setEditor({node,parentId:node.parent_id}),create:(at)=>{setCreateAt(at);setText('');setNewTitle('');attempt.current=undefined;setFailure('');},expanded,toggle:(key,open)=>setExpanded((old)=>{const next=new Set(old);if(open??!next.has(key))next.add(key);else next.delete(key);return next;}),selectedPath:selected?.path_ids??[]};
  useEffect(()=>{const command=(event:Event)=>{const detail=(event as CustomEvent).detail;if(detail?.action==='create')context.create({folder:selectedId,label:selected?.name??'Chưa xếp thư mục'});};window.addEventListener('knowledge-command',command);return()=>window.removeEventListener('knowledge-command',command);},[selectedId,selected?.name]);
  async function submitNote() {
    if(busy||!createAt||!text.trim())return;
    setBusy(true);setFailure('');attempt.current??=crypto.randomUUID();
    try{
      const receipt=await request<Receipt>('/explorer/notes',{method:'POST',csrf,idempotencyKey:attempt.current,body:{text,title:newTitle,home_topic_id:createAt.folder,parent_item_id:createAt.parent??null}});
      setNotice('Đã tiếp nhận ghi chú.');setCreateAt(undefined);changed();window.location.hash=itemHref(receipt.item_id);
    }catch(error){setFailure(failure(error));}finally{setBusy(false);}
  }
  async function archive() {
    if(!selected)return;setBusy(true);setFailure('');
    try{await request('/explorer/folders/'+selected.id,{method:'DELETE',csrf});setNotice('Đã ẩn thư mục và các nhánh con. Ghi chú vẫn được giữ.');changed();window.location.hash='#/thu-vien';}
    catch(error){setFailure(failure(error));}finally{setBusy(false);}
  }
  function keyboard(event: KeyboardEvent) {
    if(event.nativeEvent.isComposing || event.keyCode===229)return;
    if(event.target instanceof HTMLElement && event.target.matches('input,textarea,select,button,summary'))return;
    const row=(event.target as HTMLElement).closest<HTMLElement>('[role="treeitem"]');if(!row)return;
    const rows=[...event.currentTarget.querySelectorAll<HTMLElement>('[role="treeitem"]')].filter(item=>!item.closest('[inert]'));
    const index=rows.indexOf(row);
    if(event.key==='ArrowDown'||event.key==='ArrowUp'){event.preventDefault();rows[Math.max(0,Math.min(rows.length-1,index+(event.key==='ArrowDown'?1:-1)))]?.focus();}
    if(event.key==='ArrowRight'||event.key==='ArrowLeft'){const expanded=row.getAttribute('aria-expanded');if(expanded!==null&&((event.key==='ArrowRight')!==(expanded==='true'))){event.preventDefault();row.querySelector<HTMLButtonElement>('.explorer-row > button')?.click();}}
    if(event.key===' '&&row.hasAttribute('aria-expanded')){event.preventDefault();row.querySelector<HTMLButtonElement>('.explorer-row > button')?.click();}
    if(event.key==='Enter'){event.preventDefault();row.querySelector<HTMLAnchorElement>('.explorer-row > a')?.click();}
  }
  return <aside className="knowledge-tree-column knowledge-explorer" aria-label="Thư mục và ghi chú">
    <section className="panel knowledge-tree-panel">
      <div className="panel-heading"><h2>Thư mục và ghi chú</h2><Button size="compact-sm" variant="default" onClick={()=>setEditor({parentId:null})}>Thêm kho con</Button></div>
      <a className="knowledge-tree-root" href="#/thu-vien" aria-current={selectedId==null&&!unfiled&&!selectedNoteId?'page':undefined}>Toàn bộ tri thức</a><a className="knowledge-tree-root" href="#/thu-vien?unfiled=1" aria-current={unfiled&&!selectedNoteId?'page':undefined}>Chưa xếp thư mục</a>
      <div className="explorer-actions"><Button size="compact-sm" variant="default" onClick={()=>context.create({folder:selectedId,label:selected?.name??'Chưa xếp thư mục'})}>Thêm ghi chú tại đây</Button>{selected && <><Button size="compact-sm" variant="default" onClick={()=>setEditor({parentId:selected.id})}>Thêm nhánh con</Button><Button size="compact-sm" variant="subtle" onClick={()=>setEditor({node:selected,parentId:selected.parent_id})}>Đổi tên / chuyển nhánh</Button><Button size="compact-sm" variant="subtle" disabled={busy} onClick={()=>void archive()}>Ẩn thư mục và nhánh con</Button></>}</div>
      <p className="list-meta">Kéo bài vào thư mục để chuyển vị trí chính; giữ Ctrl để thêm lối tắt. Menu Thao tác có các lựa chọn tương đương.</p>
      {error?<ErrorNotice retry={onRetry}>Chưa tải được mục lục.</ErrorNotice>:!data?<Loading/>:<nav aria-label="Cây thư mục và ghi chú" role="tree" onKeyDown={keyboard}><Branch context={context} unfiled={unfiled}/></nav>}
      {notice&&<p role="status">{notice}</p>}{failureText&&<ErrorNotice>{failureText}</ErrorNotice>}
    </section>
    {editor&&<NodeEditor nodes={nodes} editor={editor} csrf={csrf} onCancel={()=>setEditor(undefined)} onSaved={(node)=>{setEditor(undefined);changed();onSaved(node);}}/>}
    {createAt&&<section className="panel explorer-note-form"><h2>Thêm ghi chú vào {createAt.label}</h2><form className="form-stack" onSubmit={(event)=>{event.preventDefault();void submitNote();}}>
      <TextInput label="Tiêu đề ghi chú mới" value={newTitle} maxLength={512} disabled={busy} onChange={(event)=>{setNewTitle(event.currentTarget.value);attempt.current=undefined;}}/>
      <Textarea label="Nội dung ghi chú mới" value={text} required minRows={5} disabled={busy} onChange={(event)=>{setText(event.currentTarget.value);attempt.current=undefined;}}/>
      <div className="form-actions"><Button type="submit" loading={busy}>Tạo ghi chú</Button><Button type="button" variant="default" disabled={busy} onClick={()=>setCreateAt(undefined)}>Hủy tạo ghi chú</Button></div>
    </form></section>}
  </aside>;
}
