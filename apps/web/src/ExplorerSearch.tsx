import { useEffect, useId, useRef, useState } from 'react';
import { request } from './api';
import { knowledgeNodeHref, type KnowledgeNode } from './KnowledgeTree';
import { itemHref } from './views';

type Result = { items:{item_id:string;title:string;saved_at:string}[]; folders:{id:number;name:string;parent_id:number|null}[]; next_offset:number|null };

/** Bounded owner-scoped navigation; never filters out or remounts the tree. */
export function ExplorerSearch({nodes}:{nodes:KnowledgeNode[]}){
  const [query,setQuery]=useState('');
  const [composing,setComposing]=useState(false);
  const [response,setResponse]=useState<{term:string;data:Result}>();
  const [failure,setFailure]=useState<string>();
  const [retry,setRetry]=useState(0);
  const input=useRef<HTMLInputElement>(null);
  const results=useRef<HTMLElement>(null);
  const id=useId(),term=query.trim();
  const data=response?.term===term&&!composing?response.data:undefined;
  const clear=()=>{setQuery('');setResponse(undefined);setFailure(undefined);};
  useEffect(()=>{
    if(!term||composing)return;
    const controller=new AbortController();
    setFailure(undefined);
    const timer=window.setTimeout(()=>{
      void request<Result>('/navigation?q='+encodeURIComponent(term),{signal:controller.signal})
        .then(value=>{
          if(controller.signal.aborted)return;
          if(!Array.isArray(value?.items)||!Array.isArray(value?.folders))throw Error('invalid_navigation_payload');
          setResponse({term,data:value});
        }).catch(()=>{if(!controller.signal.aborted)setFailure(term);});
    },120);
    return()=>{window.clearTimeout(timer);controller.abort();};
  },[term,composing,retry]);
  return <div className="explorer-search">
    <label htmlFor={id}>Tìm nhanh trong cây</label>
    <input ref={input} id={id} type="search" aria-label="Tìm nhanh trong cây" aria-controls={term&&!composing?id+'-results':undefined}
      maxLength={200} value={query} placeholder="Tên thư mục hoặc bài…" autoComplete="off"
      onChange={e=>setQuery(e.currentTarget.value)}
      onCompositionStart={()=>setComposing(true)} onCompositionEnd={()=>setComposing(false)}
      onKeyDown={e=>{
        if(composing||e.nativeEvent.isComposing||e.keyCode===229)return;
        if(e.key==='Escape'){e.preventDefault();clear();}
        else if(e.key==='ArrowDown'){const first=results.current?.querySelector('a');if(first){e.preventDefault();first.focus();}}
        else if(e.key==='Enter'){const first=results.current?.querySelector('a');if(first){e.preventDefault();first.click();}}
      }}/>
    {term&&!composing&&<nav ref={results} id={id+'-results'} className="explorer-search-results" aria-label="Kết quả tìm trong cây"
      onKeyDown={e=>{if(e.key==='Escape'){e.preventDefault();clear();input.current?.focus();}}}>
      {failure===term?<p role="alert">Chưa tìm được dữ liệu. <button type="button" onClick={()=>setRetry(n=>n+1)}>Thử lại</button></p>:!data?<p role="status">Đang tìm…</p>:<>
        <ul>
          {data.folders.map(row=><li key={'folder:'+row.id}><a href={knowledgeNodeHref(row.id)} onClick={e=>{if(!e.ctrlKey&&!e.metaKey&&!e.shiftKey&&!e.altKey)clear();}}>Thư mục · {row.name}<small>{nodes.find(n=>n.id===row.id)?.path||row.name}</small></a></li>)}
          {data.items.map(row=><li key={'note:'+row.item_id}><a href={itemHref(row.item_id)} onClick={e=>{if(!e.ctrlKey&&!e.metaKey&&!e.shiftKey&&!e.altKey)clear();}}>Bài · {row.title||'Chưa đặt tên'}</a></li>)}
        </ul>
        {!data.items.length&&!data.folders.length?<p>Không thấy bài hoặc thư mục phù hợp.</p>:<p>Hiển thị tối đa 20 bài và 20 thư mục; nhập thêm từ khóa để thu hẹp.</p>}
      </>}
    </nav>}
  </div>;
}
