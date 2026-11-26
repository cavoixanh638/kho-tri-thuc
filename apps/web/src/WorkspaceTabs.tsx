import { useEffect, useRef, useState } from 'react';
import { itemHref } from './views';

export const TAB_NAVIGATION_EVENT='knowledge-before-tab-navigation';
export const TAB_TITLE_EVENT='knowledge-tab-title';
export const allowTabNavigation=()=>window.dispatchEvent(new Event(TAB_NAVIGATION_EVENT,{cancelable:true}));
const prefix='kt-workspace-tabs-v1:';
const validId=(id:unknown):id is string=>typeof id==='string'&&/^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$/i.test(id);
const MAX=20;
type Tab={id:string;pinned:boolean};
type Model={tabs:Tab[];closed:string[]};
function read(owner?:string|null):Model{
  try{
    const data=owner?JSON.parse(window.sessionStorage.getItem(prefix+owner)??'null'):null;
    const tabs:Tab[]=Array.isArray(data?.tabs)?data.tabs.filter((x:Tab)=>x&&validId(x.id)).slice(0,MAX).map((x:Tab)=>({id:x.id,pinned:x.pinned===true})):[];
    return {tabs:[...new Map(tabs.map(tab=>[tab.id,tab])).values()].sort((a,b)=>Number(b.pinned)-Number(a.pinned)),closed:Array.isArray(data?.closed)?data.closed.filter(validId).slice(0,10):[]};
  }catch{return {tabs:[],closed:[]};}
}
export function clearWorkspaceTabs(owner?:string|null){
  if(owner)try{window.sessionStorage.removeItem(prefix+owner);}catch{/* preference only */}
}

/** Route tabs never mount multiple Item editors. Session preference stores only
 * IDs/pin/order, not titles, snippets, raw text or credentials. */
export function WorkspaceTabs({activeId,owner,fallbackHref}:{activeId?:string;owner?:string|null;fallbackHref:string}){
  const [model,setModel]=useState(()=>read(owner)),current=useRef(model);
  const [labels,setLabels]=useState<Record<string,string>>({});
  const [notice,setNotice]=useState('');
  function commit(next:Model){
    current.current=next;setModel(next);
    if(owner)try{window.sessionStorage.setItem(prefix+owner,JSON.stringify(next));}catch{/* UI still works in memory */}
  }
  useEffect(()=>{
    const title=(event:Event)=>{
      const value=(event as CustomEvent<{id?:unknown;title?:unknown}>).detail;
      if(validId(value?.id)&&typeof value?.title==='string'){
        const id=value.id,label=value.title.slice(0,160);
        setLabels(old=>old[id]===label?old:{...Object.fromEntries(Object.entries(old).slice(-MAX*2)),[id]:label});
      }
    };
    const expiry=()=>{clearWorkspaceTabs(owner);current.current={tabs:[],closed:[]};setModel(current.current);setLabels({});};
    window.addEventListener(TAB_TITLE_EVENT,title);window.addEventListener('session-expired',expiry);
    return()=>{window.removeEventListener(TAB_TITLE_EVENT,title);window.removeEventListener('session-expired',expiry);};
  },[owner]);
  useEffect(()=>{
    setNotice('');
    if(!validId(activeId)||current.current.tabs.some(tab=>tab.id===activeId))return;
    const old=current.current;
    let tabs=old.tabs,closed=old.closed.filter(id=>id!==activeId);
    if(tabs.length>=MAX){
      const evict=tabs.find(tab=>!tab.pinned);
      if(!evict){setNotice('Đã ghim tối đa 20 tab. Bỏ ghim một tab để theo dõi thêm bài.');return;}
      tabs=tabs.filter(tab=>tab.id!==evict.id);closed=[evict.id,...closed.filter(id=>id!==evict.id)].slice(0,10);
      setNotice('Đã đưa một tab cũ vào danh sách mở lại; nội dung và bản nháp không bị xóa.');
    }
    commit({tabs:[...tabs,{id:activeId,pinned:false}],closed});
  },[activeId]);
  const title=(id:string)=>labels[id]||'Bài '+id.slice(0,8);
  function guard(){
    if(allowTabNavigation()){setNotice('');return true;}
    setNotice('Chưa chuyển tab. Hoàn tất nhập liệu hoặc lưu bản nháp trước.');return false;
  }
  function navigate(id:string){if(id!==activeId&&guard())window.location.hash=itemHref(id);}
  function close(tab:Tab){
    if(tab.pinned)return;
    if(tab.id===activeId&&!guard())return;
    const old=current.current,index=old.tabs.findIndex(t=>t.id===tab.id);
    const tabs=old.tabs.filter(t=>t.id!==tab.id);
    commit({tabs,closed:[tab.id,...old.closed.filter(id=>id!==tab.id)].slice(0,10)});
    if(tab.id===activeId)window.location.hash=tabs[Math.min(index,tabs.length-1)]?itemHref(tabs[Math.min(index,tabs.length-1)].id):fallbackHref;
  }
  function pin(tab:Tab){
    const old=current.current,tabs=old.tabs.map(t=>t.id===tab.id?{...t,pinned:!t.pinned}:t);
    commit({...old,tabs:tabs.sort((a,b)=>Number(b.pinned)-Number(a.pinned))});
  }
  function move(id:string,targetId:string){
    const old=current.current,tabs=[...old.tabs],from=tabs.findIndex(t=>t.id===id),to=tabs.findIndex(t=>t.id===targetId);
    if(from<0||to<0||from===to||tabs[from].pinned!==tabs[to].pinned)return;
    const [tab]=tabs.splice(from,1);tabs.splice(to,0,tab);commit({...old,tabs});
  }
  function reopen(){
    const id=current.current.closed[0];if(!id||!guard())return;
    if(current.current.tabs.length>=MAX&&!current.current.tabs.some(t=>!t.pinned)){setNotice('Bỏ ghim một tab trước khi mở lại.');return;}
    window.location.hash=itemHref(id);
  }
  if(!model.tabs.length&&!model.closed.length&&!notice)return null;
  return <nav aria-label="Các bài đang mở" className="workspace-tabs">
    <div className="workspace-tabs-header"><span>{model.tabs.length} bài đang mở · Alt + mũi tên để đổi vị trí</span>
      {model.closed.length>0&&<button type="button" onClick={reopen}>Mở lại tab đã đóng</button>}</div>
    <div className="workspace-tab-strip">
      {model.tabs.map((tab,index)=><div key={tab.id} data-tab-id={tab.id} className={'workspace-tab'+(activeId===tab.id?' is-active':'')} draggable
        onDragStart={e=>{e.stopPropagation();e.dataTransfer.setData('application/x-kt-tab',tab.id);e.dataTransfer.effectAllowed='move';}}
        onDragOver={e=>{if(e.dataTransfer.types.includes('application/x-kt-tab'))e.preventDefault();}}
        onDrop={e=>{const id=e.dataTransfer.getData('application/x-kt-tab');if(id){e.preventDefault();e.stopPropagation();move(id,tab.id);}}}>
        <button className="workspace-tab-open" type="button" aria-current={tab.id===activeId?'page':undefined} title={title(tab.id)} onClick={()=>navigate(tab.id)}
          onKeyDown={e=>{
            if(e.altKey&&!e.nativeEvent.isComposing&&(e.key==='ArrowLeft'||e.key==='ArrowRight')){
              e.preventDefault();const next=model.tabs[index+(e.key==='ArrowLeft'?-1:1)];if(next)move(tab.id,next.id);
            }
          }}>{title(tab.id)}</button>
        <button className="workspace-tab-icon" type="button" aria-label={(tab.pinned?'Bỏ ghim ':'Ghim ')+title(tab.id)} aria-pressed={tab.pinned} title={tab.pinned?'Bỏ ghim':'Ghim tab'} onClick={()=>pin(tab)}>{tab.pinned?'◆':'◇'}</button>
        {!tab.pinned&&<button className="workspace-tab-icon" type="button" aria-label={'Đóng tab '+title(tab.id)} title="Đóng tab, không xóa ghi chú" onClick={()=>close(tab)}>×</button>}
      </div>)}
    </div>
    {notice&&<p className="tab-notice" role="status">{notice}</p>}
  </nav>;
}
