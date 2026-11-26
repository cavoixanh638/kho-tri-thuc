import { useRef, useState, type ReactNode } from 'react';
import type { Item } from './api';
import { knowledgePreview } from './KnowledgeText';
import { itemHref,itemTitle,itemKindLabel,ServerTime } from './views';
type ColumnId='title'|'kind'|'saved'|'published'|'assets'|'updated'|'status';
const definitions:{id:ColumnId;label:string;width:number;defaultVisible:boolean;render:(item:Item)=>ReactNode}[]=[
 {id:'title',label:'Bài tri thức',width:310,defaultVisible:true,render:item=><><a href={itemHref(item.item_id)}>{itemTitle(item)}</a><p>{knowledgePreview(item.note||item.knowledge_excerpt||'')}</p></>},
 {id:'kind',label:'Loại',width:110,defaultVisible:true,render:itemKindLabel},
 {id:'saved',label:'Nhận lần đầu',width:160,defaultVisible:true,render:item=><ServerTime value={item.saved_at}/>},
 {id:'published',label:'Ngày nguồn đăng',width:160,defaultVisible:true,render:item=>item.published_at?<ServerTime value={item.published_at}/>:'—'},
 {id:'assets',label:'Tệp minh họa',width:125,defaultVisible:true,render:item=>item.assets.length},
 {id:'updated',label:'Cập nhật gần nhất',width:165,defaultVisible:false,render:item=>item.updated_at&&Number.isFinite(Date.parse(item.updated_at))?<ServerTime value={item.updated_at}/>:'—'},
 {id:'status',label:'Phân loại',width:150,defaultVisible:false,render:item=>(({user_assigned:'Đã xếp nhóm',auto_assigned:'Đã tự xếp nhóm',suggested:'Có đề xuất',pending:'Đang chờ',unclassified:'Chưa phân loại',needs_review:'Cần xem lại'} as Record<string,string>)[item.classification_status]||'—')},
];
type Column={id:ColumnId;visible:boolean;width:number};
const defaults=()=>definitions.map(d=>({id:d.id,visible:d.defaultVisible,width:d.width}));
const width=(value:number)=>Math.min(600,Math.max(100,Math.round(value)));
const getDefinition=(id:ColumnId)=>definitions.find(d=>d.id===id)!;
function readColumns(key?:string):Column[]{
 try{
  const stored=key?JSON.parse(window.sessionStorage.getItem(key)||'null'):null;
  if(!Array.isArray(stored))return defaults();
  const seen=new Set<ColumnId>(),rows:Column[]=[];
  for(const entry of stored){
   const def=definitions.find(d=>d.id===entry?.id);
   if(!def||seen.has(def.id))continue;
   seen.add(def.id);rows.push({id:def.id,visible:def.id==='title'||entry.visible===true,width:typeof entry.width==='number'&&Number.isFinite(entry.width)?width(entry.width):def.width});
  }
  for(const column of defaults())if(!seen.has(column.id))rows.push(column);
  return [rows.find(c=>c.id==='title')!,...rows.filter(c=>c.id!=='title')];
 }catch{return defaults();}
}
export function LibraryTable({items,caption,preferenceKey}:{items:Item[];caption:string;preferenceKey?:string}){
 const storageKey=preferenceKey?'kt-table-layout-v1:'+preferenceKey:undefined;
 const [columns,setColumns]=useState(()=>readColumns(storageKey));
 const current=useRef(columns);
 const drag=useRef<{id:ColumnId;pointer:number;x:number;w:number}|null>(null);
 function commit(next:Column[]){
  current.current=next;setColumns(next);
  if(storageKey)try{window.sessionStorage.setItem(storageKey,JSON.stringify(next));}catch{/* preference only */}
 }
 function adjust(id:ColumnId,next:number){commit(current.current.map(c=>c.id===id?{...c,width:width(next)}:c));}
 function move(id:ColumnId,delta:number){
  const next=[...current.current],index=next.findIndex(c=>c.id===id),target=index+delta;
  if(index<1||target<1||target>=next.length)return;
  [next[index],next[target]]=[next[target],next[index]];commit(next);
 }
 const visible=columns.filter(c=>c.visible);
 return <div className="library-configurable-table">
   <details className="library-column-options"><summary>Tùy chọn cột</summary>
    <ul>{columns.map((column,index)=><li key={column.id}>
     <label><input type="checkbox" checked={column.visible} disabled={column.id==='title'} onChange={event=>commit(current.current.map(c=>c.id===column.id?{...c,visible:event.currentTarget.checked}:c))}/>{getDefinition(column.id).label}</label>
     <button type="button" aria-label={'Đưa '+getDefinition(column.id).label+' lên'} disabled={index<=1} onClick={()=>move(column.id,-1)}>↑</button>
     <button type="button" aria-label={'Đưa '+getDefinition(column.id).label+' xuống'} disabled={index===0||index===columns.length-1} onClick={()=>move(column.id,1)}>↓</button>
    </li>)}</ul>
    <button type="button" onClick={()=>commit(defaults())}>Khôi phục cột mặc định</button>
   </details>
   <div className="library-table-frame" role="region" aria-label="Bảng tri thức" tabIndex={0}>
    <table className="library-table is-configurable" style={{width:visible.reduce((sum,c)=>sum+c.width,0)}}><caption>{caption}</caption>
     <colgroup>{visible.map(c=><col key={c.id} style={{width:c.width}}/>)}</colgroup>
     <thead><tr>{visible.map(c=><th scope="col" key={c.id} data-column={c.id}><span>{getDefinition(c.id).label}</span>
      <span className="library-column-resizer" role="separator" tabIndex={0} aria-orientation="vertical" aria-label={'Điều chỉnh cột '+getDefinition(c.id).label}
       aria-valuemin={100} aria-valuemax={600} aria-valuenow={c.width} title="Kéo hoặc dùng phím mũi tên; nhấp đúp để đặt lại"
       onPointerDown={event=>{if(event.button!==0)return;drag.current={id:c.id,pointer:event.pointerId,x:event.clientX,w:c.width};event.currentTarget.setPointerCapture?.(event.pointerId);event.preventDefault();}}
       onPointerMove={event=>{const d=drag.current;if(d&&d.id===c.id&&d.pointer===event.pointerId)adjust(c.id,d.w+event.clientX-d.x);}}
       onPointerUp={()=>{drag.current=null;}} onPointerCancel={()=>{drag.current=null;}} onLostPointerCapture={()=>{drag.current=null;}}
       onDoubleClick={()=>adjust(c.id,getDefinition(c.id).width)}
       onKeyDown={event=>{if(event.key==='ArrowLeft'||event.key==='ArrowRight'){event.preventDefault();adjust(c.id,c.width+(event.key==='ArrowLeft'?-20:20));}}}/>
     </th>)}</tr></thead>
     <tbody>{items.map(item=><tr key={item.item_id} data-library-item={item.item_id}>{visible.map(c=><td key={c.id} data-column={c.id} className={c.id==='assets'?'library-number':undefined}>{getDefinition(c.id).render(item)}</td>)}</tr>)}</tbody>
    </table>
   </div>
 </div>;
}
