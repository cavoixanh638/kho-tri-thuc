import { createContext, useEffect, type RefObject } from 'react';
import { ErrorNotice, Loading, ServerTime, itemHref, useResource } from './views';
export const WorkspacePreviewContext=createContext<((id:string,trigger:HTMLElement)=>void)|null>(null);
export const previewItemId=(id:string)=>/^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$/i.test(id);
type Preview={item_id:string;title:string;kind:string;excerpt:string;truncated:boolean;saved_at:string;content_extract:string;source_fetch:string};
export function WorkspaceReadPane({id,panelRef,layout,onLayout,onClose}:{id:string;panelRef:RefObject<HTMLElement|null>;layout:'side'|'below';onLayout:()=>void;onClose:()=>void}){
  const resource=useResource<Preview>('/items/'+encodeURIComponent(id)+'/preview');
  const data=resource.data;
  const valid=data?.item_id===id&&typeof data.excerpt==='string'&&typeof data.title==='string'&&typeof data.saved_at==='string'&&Number.isFinite(Date.parse(data.saved_at));
  useEffect(()=>{
    const escape=(event:KeyboardEvent)=>{if(event.key==='Escape'&&!event.defaultPrevented&&!event.isComposing&&panelRef.current?.contains(document.activeElement)){event.preventDefault();onClose();}};
    window.addEventListener('keydown',escape);return()=>window.removeEventListener('keydown',escape);
  },[onClose,panelRef]);
  return <aside ref={panelRef} className="workspace-preview-pane" aria-label="Xem bài bên cạnh" tabIndex={-1}>
    <header><strong>Xem cạnh · chỉ đọc</strong><div>
      <button type="button" aria-label="Đổi bố cục xem cạnh" onClick={onLayout}>{layout==='side'?'Xếp dưới':'Xếp cạnh'}</button>{' '}
      <button type="button" aria-label="Đóng xem cạnh" onClick={onClose}>Đóng ×</button>
    </div></header>
    {resource.error||(data&&!valid)?<ErrorNotice retry={resource.retry}>Không thể xem bài này. Có thể bài đã xóa hoặc không có quyền.</ErrorNotice>:!data?<Loading/>:<>
      <h2>{data.title||'Chưa đặt tên'}</h2><p className="list-meta">Nhận lần đầu <ServerTime value={data.saved_at}/></p>
      {data.excerpt?<pre>{data.excerpt}</pre>:<p>Chưa có văn bản do người dùng biên soạn. Hãy mở bài để kiểm tra nguồn và phần trích.</p>}
      {data.truncated&&<p className="list-meta">Xem trước tối đa 6000 ký tự; mở bài để đọc đầy đủ.</p>}
      <a href={itemHref(id)}>Mở bài đầy đủ</a>
    </>}
  </aside>;
}
