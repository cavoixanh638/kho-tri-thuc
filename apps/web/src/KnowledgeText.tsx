import Markdown, { type Components } from 'react-markdown';
import { createContext, useContext, useLayoutEffect, useRef, useState } from 'react';
import remarkGfm from 'remark-gfm';
import { externalHttpUrl } from './api';
import { remarkNoteOutline } from './NoteOutline';
import './NoteNavigation.css';

const internalItemHref = (url: string) => url.length === 42 && /^#\/muc\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(url);

const foldPrefix='kt-heading-fold-v1:';
const validFoldId=(id:unknown):id is string=>typeof id==='string'&&/^kt-fold-kt-heading-[a-z0-9]+-\d+$/.test(id);
function readCollapsed(key?:string){
  try{const value=key?JSON.parse(window.sessionStorage.getItem(foldPrefix+key)??'[]'):[];return new Set<string>(Array.isArray(value)?value.filter(validFoldId).slice(0,500):[]);}
  catch{return new Set<string>();}
}

type FoldState={collapsed:Set<string>;toggle:(id:string,closed:boolean)=>void;follow:(href:string)=>void};
const FoldContext=createContext<FoldState|null>(null);
const FoldDetails:NonNullable<Components['details']>=({children,id,className})=>{
  const state=useContext(FoldContext);
  if(!state||!validFoldId(id))return <details>{children}</details>;
  return <details id={id} className={className} open={!state.collapsed.has(id)}
    onToggle={event=>state.toggle(id,!event.currentTarget.open)}>{children}</details>;
};
const NoteLink:NonNullable<Components['a']>=({href,children})=>{
  const state=useContext(FoldContext);
  return href ? href.startsWith('#kt-heading-') ? <a href={href} onClick={event=>{event.preventDefault();state?.follow(href);}}>{children}</a>
    : internalItemHref(href) ? <a href={href}>{children}</a> : <a href={href} target="_blank" rel="noopener noreferrer">{children}</a> : <span>{children}</span>;
};
// Stable component identities keep DOM/focus intact across fold state changes.
const noteComponents:Components={
        details: FoldDetails,
        h1: ({ children, id }) => <h2 id={id} tabIndex={-1}>{children}</h2>, h2: ({ children, id }) => <h3 id={id} tabIndex={-1}>{children}</h3>, h3: ({ children, id }) => <h4 id={id} tabIndex={-1}>{children}</h4>,
        h4: ({ children, id }) => <h4 id={id} tabIndex={-1}>{children}</h4>, h5: ({ children, id }) => <h5 id={id} tabIndex={-1}>{children}</h5>, h6: ({ children, id }) => <h6 id={id} tabIndex={-1}>{children}</h6>,
        a: NoteLink,
        img: ({ src, alt }) => typeof src === 'string' && src ? <a href={src} target="_blank" rel="noopener noreferrer">Ảnh minh họa: {alt || 'Mở ảnh'}</a> : <span>{alt}</span>,
        table: ({ children }) => <div className="knowledge-table"><table>{children}</table></div>,
};

 /** Source HTML is skipped; images require an explicit click. Fold state is
 * presentation only; no source, version or Markdown is changed. */
export function KnowledgeText({ text, title, foldKey }: { text: string; title?: string; foldKey?:string }) {
  const [collapsed,setCollapsed]=useState(()=>readCollapsed(foldKey));
  const collapsedRef=useRef(collapsed);
  const root=useRef<HTMLDivElement>(null);
  const [pending,setPending]=useState<string>();
  function changeCollapsed(value:Set<string>){
    collapsedRef.current=value;setCollapsed(value);
    if(foldKey){try{const key=foldPrefix+foldKey;if(value.size)window.sessionStorage.setItem(key,JSON.stringify([...value].slice(0,500)));else window.sessionStorage.removeItem(key);}catch{/* optional reading preference */}}
  }
  function focusHeading(href:string){
    const target=root.current?.querySelector<HTMLElement>(href);
    target?.scrollIntoView?.({behavior:window.matchMedia?.('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});
    target?.focus({preventScroll:true});
  }
  function followHeading(href:string){
    const target=root.current?.querySelector<HTMLElement>(href);
    if(!target)return;
    const next=new Set(collapsedRef.current);
    let changed=false;
    for(let parent=target.parentElement;parent&&parent!==root.current;parent=parent.parentElement){
      if(parent.matches('details.kt-fold-section')&&next.delete(parent.id))changed=true;
    }
    if(changed){changeCollapsed(next);setPending(href);}else focusHeading(href);
  }
  useLayoutEffect(()=>{if(pending){focusHeading(pending);setPending(undefined);}},[pending]);
  const heading = /^#[ \t]+([^\r\n]+)(?:\r?\n|$)/.exec(text);
  const body = heading && heading[1].trim() === title?.trim() ? text.slice(heading[0].length) : text;
  return <FoldContext.Provider value={{collapsed,follow:followHeading,toggle:(id,closed)=>{
    if(collapsedRef.current.has(id)===closed)return;
    const next=new Set(collapsedRef.current);if(closed)next.add(id);else next.delete(id);changeCollapsed(next);
  }}}><div className="knowledge-text" ref={root}>
    <Markdown skipHtml remarkPlugins={[remarkGfm, remarkNoteOutline]} urlTransform={(url, key) => key === 'href' && (internalItemHref(url) || /^#kt-heading-[a-z0-9]+-\d+$/.test(url)) ? url : externalHttpUrl(url) ?? ''}
      components={noteComponents}>{body}</Markdown>
  </div></FoldContext.Provider>;
}

export function knowledgePreview(text: string) {
  return text.replace(/^#[ \t]+[^\r\n]+(?:\r?\n|$)/, '').replace(/^#{1,6}\s+/gm, '').replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1').replace(/[`*~]/g, '').replace(/\s+/g, ' ').trim().slice(0, 220);
}
