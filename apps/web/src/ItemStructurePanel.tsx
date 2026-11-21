import { Button, Textarea, TextInput } from '@mantine/core';
import { useEffect, useRef, useState } from 'react';
import { request, type Receipt } from './api';
import { ErrorNotice, itemHref, Loading, useResource } from './views';
import type { ExplorerNote } from './KnowledgeExplorer';
import type { KnowledgeTreeData } from './KnowledgeTree';
import './KnowledgeExplorer.css';

type Structure={item_id:string;home_topic_id:number|null;parent_item_id:string|null;sort_order:number;structure_version:number;origin:string;ancestors:{item_id:string;title:string}[];children:ExplorerNote[]};
export function StructureParentEditor({id,version,currentParent,onSaved,csrf}:{id:string;version:number;currentParent:string|null;onSaved:()=>void;csrf:string}){
  const [query,setQuery]=useState('');
  const [hits,setHits]=useState<ExplorerNote[]>([]);
  const [parent,setParent]=useState('');
  const [order,setOrder]=useState(0);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  useEffect(()=>{if(!query.trim()){setHits([]);return;}const controller=new AbortController();const timer=window.setTimeout(()=>{void request<{results:ExplorerNote[]}>('/explorer/find?q='+encodeURIComponent(query),{signal:controller.signal}).then((data)=>setHits(data.results.filter((row)=>row.item_id!==id))).catch(()=>{if(!controller.signal.aborted)setError('Chưa tìm được bài cha.');});},200);return()=>{controller.abort();window.clearTimeout(timer);};},[query,id]);
  async function apply(parentId:string|null){
    setBusy(true);setError('');
    try{await request('/items/'+id+'/structure',{method:'PATCH',csrf,body:{parent_item_id:parentId,sort_order:order,expected_version:version}});onSaved();setParent('');setQuery('');}
    catch{setError('Chưa đổi được cấu trúc. Có thể vị trí đã đổi, sai quyền hoặc tạo chu trình. Tải lại rồi thử lại.');}finally{setBusy(false);}
  }
  return <div className="explorer-menu">
    <label>Tìm bài cha<input value={query} maxLength={200} disabled={busy} onChange={(event)=>{setQuery(event.currentTarget.value);setParent('');}}/></label>
    {!!hits.length&&<label>Chọn bài cha<select value={parent} disabled={busy} onChange={(event)=>setParent(event.currentTarget.value)}><option value="">Chọn một bài</option>{hits.map((row)=><option key={row.item_id} value={row.item_id}>{row.title} · {row.item_id.slice(0,8)}</option>)}</select></label>}
    <label>Thứ tự bài<input type="number" min={0} max={1000000} value={order} onChange={(event)=>setOrder(Number(event.currentTarget.value))}/></label>
    <Button variant="default" size="compact-sm" disabled={busy||!parent} onClick={()=>void apply(parent)}>Đặt làm con của bài đã chọn</Button>
    {currentParent&&<Button variant="default" size="compact-sm" disabled={busy} onClick={()=>void apply(null)}>Đưa bài ra cấp thư mục</Button>}
    <Button variant="default" size="compact-sm" disabled={busy} onClick={()=>void apply(currentParent)}>Lưu thứ tự bài</Button>
    {error&&<ErrorNotice>{error}</ErrorNotice>}
  </div>;
}

export function ItemStructurePanel({id,csrf,refreshKey,onChanged}:{id:string;csrf:string;refreshKey?:string;onChanged?:()=>void}){
  const info=useResource<Structure>('/items/'+encodeURIComponent(id)+'/structure',{refreshKey});
  const [creating,setCreating]=useState(false);
  const [title,setTitle]=useState('');
  const [text,setText]=useState('');
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const key=useRef<string|undefined>(undefined);
  const placementDetails=useRef<HTMLDetailsElement>(null);
  const folderField=useRef<HTMLSelectElement>(null);
  const [folders,setFolders]=useState<KnowledgeTreeData>();
  const [folder,setFolder]=useState('');
  useEffect(()=>{const command=(event:Event)=>{const detail=(event as CustomEvent).detail;if(detail?.action==='move'&&detail.itemId===id&&placementDetails.current){placementDetails.current.open=true;folderField.current?.focus();}};window.addEventListener('knowledge-command',command);return()=>window.removeEventListener('knowledge-command',command);},[id]);
  async function loadFolders(){try{setFolders(await request<KnowledgeTreeData>('/knowledge-tree'));}catch{setError('Chưa tải được danh sách thư mục.');}}
  async function place(action:'move'|'add'|'remove'){
    if(!info.data)return;setBusy(true);setError('');
    try{await request('/items/'+id+'/placement',{method:'PATCH',csrf,body:{action,folder_id:folder?Number(folder):null,expected_version:info.data.structure_version}});changed();}
    catch{setError('Chưa đổi được thư mục. Cấu trúc có thể đã đổi; tải lại rồi thử lại.');}finally{setBusy(false);}
  }
  const changed=()=>{info.retry();onChanged?.();};
  async function create(){
    if(busy||!text.trim())return;setBusy(true);setError('');key.current??=crypto.randomUUID();
    try{const result=await request<Receipt>('/explorer/notes',{method:'POST',csrf,idempotencyKey:key.current,body:{text,title,parent_item_id:id,home_topic_id:info.data?.home_topic_id??null}});setCreating(false);changed();window.location.hash=itemHref(result.item_id);}
    catch{setError('Chưa xác nhận tạo bài con. Bản nháp vẫn được giữ; thử lại cùng lượt gửi.');}finally{setBusy(false);}
  }
  return <section className="panel" aria-label="Cấu trúc bài cha và bài con"><h2>Cấu trúc bài</h2>
    {info.error?<ErrorNotice retry={info.retry}>Chưa tải được cấu trúc bài.</ErrorNotice>:!info.data?<Loading/>:<>
      <nav className="explorer-placement-path" aria-label="Đường dẫn bài cha">{info.data.ancestors.length?info.data.ancestors.map((entry)=><span key={entry.item_id}><a href={itemHref(entry.item_id)}>{entry.title}</a><span aria-hidden="true"> / </span></span>):'Bài ở cấp thư mục, chưa thuộc bài cha.'}</nav>
      <h3>Bài con ({info.data.children.length})</h3><ul>{info.data.children.map((entry)=><li key={entry.item_id}><a href={itemHref(entry.item_id)}>{entry.title}</a></li>)}</ul>
      <p className="list-meta">Quan hệ do bạn sắp xếp; khác với liên kết ngược và gợi ý liên quan. Phiên bản {info.data.structure_version}.</p>
      <p className="explorer-placement-path">Thư mục chính: {folders?.nodes.find((node)=>node.id===info.data?.home_topic_id)?.path??(info.data.home_topic_id?'Mã '+info.data.home_topic_id:'Chưa xếp thư mục')}</p>
      <details ref={placementDetails} onToggle={(event)=>{if(event.currentTarget.open&&!folders)void loadFolders();}}><summary>Chuyển thư mục / thêm lối tắt</summary><div className="explorer-menu">
        <label>Thư mục cho bài<select ref={folderField} value={folder} disabled={busy} onChange={(event)=>setFolder(event.currentTarget.value)}><option value="">Chưa xếp thư mục</option>{folders?.nodes.map((node)=><option key={node.id} value={node.id}>{node.path}</option>)}</select></label>
        <Button variant="default" disabled={busy} onClick={()=>void place('move')}>Chuyển vị trí chính</Button>
        <Button variant="default" disabled={busy||!folder} onClick={()=>void place('add')}>Thêm vào nhánh khác</Button>
        <Button variant="default" disabled={busy||!folder} onClick={()=>void place('remove')}>Bỏ khỏi nhánh đã chọn</Button>
      </div></details>
      <Button variant="default" size="compact-sm" onClick={()=>{setCreating(true);setText('');setTitle('');key.current=undefined;}}>Tạo ghi chú con</Button>
      <details><summary>Đổi bài cha / sắp thứ tự</summary><StructureParentEditor id={id} version={info.data.structure_version} currentParent={info.data.parent_item_id} csrf={csrf} onSaved={changed}/></details>
      {creating&&<form className="form-stack" onSubmit={(event)=>{event.preventDefault();void create();}}>
        <TextInput label="Tiêu đề bài con" value={title} disabled={busy} maxLength={512} onChange={(event)=>{setTitle(event.currentTarget.value);key.current=undefined;}}/>
        <Textarea label="Nội dung bài con" value={text} required minRows={4} disabled={busy} onChange={(event)=>{setText(event.currentTarget.value);key.current=undefined;}}/>
        <div className="form-actions"><Button type="submit" loading={busy}>Tạo bài con</Button><Button type="button" variant="default" disabled={busy} onClick={()=>setCreating(false)}>Hủy tạo bài con</Button></div>
      </form>}
    </>}{error&&<ErrorNotice>{error}</ErrorNotice>}
  </section>;
}
