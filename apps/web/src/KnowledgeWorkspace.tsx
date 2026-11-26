import { createContext, useContext, useEffect, useRef, useState, type ReactNode, type CSSProperties } from 'react';
import { request } from './api';
import { KnowledgeExplorer } from './KnowledgeExplorer';
import type { KnowledgeTreeData } from './KnowledgeTree';
import { libraryLocationHref, parseLibraryLocation } from './LibraryViews';
import { SavedCollectionsPanel } from './SavedCollections';
import { WorkspaceTabs, allowTabNavigation } from './WorkspaceTabs';
import { useResource } from './views';
import './KnowledgeExplorer.css';

type TreeResource = ReturnType<typeof useResource<KnowledgeTreeData>>;
const WorkspaceContext = createContext<{tree: TreeResource; revision: number} | null>(null);
export const useKnowledgeWorkspace = () => useContext(WorkspaceContext);
export const EXPLORER_CHANGED = 'knowledge-explorer-changed';
type NoteLocation = {item_id: string; home_topic_id: number | null; ancestors: {item_id: string}[]};
const DEFAULT_WIDTH=286, MIN_WIDTH=240, MAX_WIDTH=480;
const widthKey='kt-explorer-width';
const clampWidth=(value:number)=>Math.max(MIN_WIDTH,Math.min(MAX_WIDTH,Math.round(value)));
function initialWidth(){
  try { const raw=window.sessionStorage.getItem(widthKey); const value=raw===null?NaN:Number(raw); return Number.isFinite(value)?clampWidth(value):DEFAULT_WIDTH; }
  catch { return DEFAULT_WIDTH; }
}

/** Keep the same explorer instance, scroll position and expansion state while
 * routing between library, individual notes and other authenticated screens. */
export function KnowledgeWorkspace({path, csrf, children, owner}: {path?: string; csrf: string; children: ReactNode; owner?:string|null}) {
  const [localPath, setLocalPath] = useState(() => window.location.hash || '#/thu-vien');
  useEffect(() => {
    const change = () => setLocalPath(window.location.hash || '#/thu-vien');
    window.addEventListener('hashchange', change);
    return () => window.removeEventListener('hashchange', change);
  }, []);
  const route = path ?? localPath;
  const inLibrary = route.split('?', 1)[0] === '#/thu-vien';
  const itemId = /^#\/muc\/([a-f\d-]{36})$/i.exec(route)?.[1];
  const lastLibrary = useRef(parseLibraryLocation(route));
  const scope = inLibrary ? parseLibraryLocation(route) : lastLibrary.current;
  useEffect(() => { if (inLibrary) lastLibrary.current = parseLibraryLocation(route); }, [route, inLibrary]);
  const [revision, setRevision] = useState(0);
  const [location, setLocation] = useState<NoteLocation>();
  const rawTree = useResource<KnowledgeTreeData>('/knowledge-tree', {refreshKey: String(revision)});
  // A failed optional sidebar payload must not take down unrelated authenticated routes.
  const tree: TreeResource = rawTree.data !== undefined && !Array.isArray(rawTree.data?.nodes)
    ? {...rawTree, data: undefined, error: true} : rawTree;
  const refresh = () => setRevision(value => value + 1);
  useEffect(() => {
    window.addEventListener(EXPLORER_CHANGED, refresh);
    return () => window.removeEventListener(EXPLORER_CHANGED, refresh);
  }, []);
  useEffect(() => {
    if (!itemId) { setLocation(undefined); return; }
    const controller = new AbortController();
    void request<NoteLocation>('/items/' + encodeURIComponent(itemId) + '/structure', {signal: controller.signal})
      .then(value => {
        if (!controller.signal.aborted && value.item_id === itemId && Array.isArray(value.ancestors)) setLocation(value);
      }).catch(() => { if (!controller.signal.aborted) setLocation(undefined); });
    return () => controller.abort();
  }, [itemId, revision]);
  const activeLocation = location?.item_id === itemId ? location : undefined;
  const selectedId = activeLocation ? activeLocation.home_topic_id : scope.id;
  const unfiled = activeLocation ? activeLocation.home_topic_id == null : scope.unfiled;
  // Desktop never hides the sidebar. On narrow touch screens a compact toggle
  // avoids covering the reading area; its choice persists across routes.
  const [narrowOpen, setNarrowOpen] = useState(() => {
    try { return sessionStorage.getItem('kt-explorer-visible') === '1'; }
    catch { return false; }
  });
  const [sidebarWidth,setSidebarWidth]=useState(initialWidth);
  const sidebarRef=useRef<HTMLElement>(null);
  const resize=useRef<{pointerId:number;startX:number;startWidth:number}|undefined>(undefined);
  // Persist the preference in the event itself, not a passive effect that can
  // still be pending if the user immediately reloads after dragging.
  const widthRef=useRef(sidebarWidth);
  function applySidebarWidth(value:number){
    const next=clampWidth(value);
    widthRef.current=next;
    try{window.sessionStorage.setItem(widthKey,String(next));}catch{/* optional preference */}
    setSidebarWidth(next);
  }
  // Observe only the navigator until the canonical note arrives through lazy
  // branches. Scroll the sidebar, never the reading page or the editor focus.
  useEffect(()=>{
    const shell=sidebarRef.current;
    if(!itemId||!shell)return;
    const compact=window.matchMedia?.('(max-width:900px)').matches??false;
    if(compact&&!narrowOpen)return;
    let timer:number|undefined,done=false;
    const seek=()=>{
      if(done||timer!==undefined)return;
      const anchor=shell.querySelector<HTMLElement>('a[data-explorer-primary="true"][aria-current="page"]');
      if(!anchor||anchor.closest('[inert]'))return;
      timer=window.setTimeout(()=>{
        timer=undefined;
        if(!anchor.isConnected||anchor.getAttribute('aria-current')!=='page'||anchor.closest('[inert]')){seek();return;}
        const area=compact?shell.querySelector<HTMLElement>('.library-tree-content'):shell;
        if(!area)return;
        const viewport=area.getBoundingClientRect(),row=anchor.getBoundingClientRect();
        if(viewport.height<=0||row.height<=0)return;
        const pad=8;
        if(row.top<viewport.top+pad)area.scrollTop+=row.top-viewport.top-pad;
        else if(row.bottom>viewport.bottom-pad)area.scrollTop+=row.bottom-viewport.bottom+pad;
        done=true;observer.disconnect();
      },window.matchMedia?.('(prefers-reduced-motion: reduce)').matches?0:210);
    };
    const observer=new window.MutationObserver(seek);
    observer.observe(shell,{childList:true,subtree:true,attributes:true,attributeFilter:['aria-current','aria-hidden','class']});
    seek();
    return()=>{done=true;observer.disconnect();window.clearTimeout(timer);};
  },[itemId,narrowOpen]);
  const style={'--kt-explorer-width':sidebarWidth+'px'} as CSSProperties;
  return <WorkspaceContext.Provider value={{tree, revision}}>
    <div className="knowledge-library-layout knowledge-workspace" style={style} onClick={event => {
      if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      const target = event.target instanceof Element ? event.target.closest('a') : null;
      const href = target?.getAttribute('href');
      if(href&&href!==route&&(href.startsWith('#/muc/')||href.startsWith('#/thu-vien'))&&!allowTabNavigation()){event.preventDefault();return;}
      if (href?.startsWith('#/thu-vien') && !href.includes('collection=') && !href.includes('view=')) {
        event.preventDefault();
        window.location.hash = libraryLocationHref({...parseLibraryLocation(href), view: scope.view});
      }
    }}>
      <aside ref={sidebarRef} className={'library-tree-shell' + (narrowOpen ? ' is-open' : '')}>
        <button className="library-tree-toggle" type="button" aria-expanded={narrowOpen} aria-controls="library-tree-content"
          onClick={() => setNarrowOpen(value => {
            try { sessionStorage.setItem('kt-explorer-visible', value ? '0' : '1'); } catch { /* optional */ }
            return !value;
          })}>{narrowOpen ? 'Thu gọn thư mục và ghi chú' : 'Mở thư mục và ghi chú'}</button>
        <div className="library-tree-content" id="library-tree-content">
          <KnowledgeExplorer data={tree.data} error={tree.error} onRetry={refresh} selectedId={selectedId}
            selectedNoteId={itemId} selectedNoteAncestors={activeLocation?.ancestors.map(node => node.item_id)}
            refreshRevision={revision} unfiled={unfiled} csrf={csrf} onSaved={node => {
              window.location.hash = libraryLocationHref({...scope, id:node.id, unfiled:false, offset:0, filter:'all'});
            }} />
          <SavedCollectionsPanel />
        </div>
      </aside>
      <div className="workspace-divider" role="separator" tabIndex={0} aria-label="Điều chỉnh độ rộng mục lục"
        aria-orientation="vertical" aria-valuemin={MIN_WIDTH} aria-valuemax={MAX_WIDTH} aria-valuenow={sidebarWidth}
        title="Kéo để đổi độ rộng; dùng phím mũi tên hoặc nhấp đúp để đặt lại"
        onPointerDown={event=>{
          if(event.button!==0)return;
          resize.current={pointerId:event.pointerId,startX:event.clientX,startWidth:sidebarRef.current?.getBoundingClientRect().width||sidebarWidth};
          event.currentTarget.setPointerCapture?.(event.pointerId);event.preventDefault();
        }}
        onPointerMove={event=>{
          const drag=resize.current;
          if(drag&&drag.pointerId===event.pointerId)applySidebarWidth(drag.startWidth+event.clientX-drag.startX);
        }}
        onPointerUp={()=>{resize.current=undefined;}} onPointerCancel={()=>{resize.current=undefined;}} onLostPointerCapture={()=>{resize.current=undefined;}}
        onDoubleClick={()=>applySidebarWidth(DEFAULT_WIDTH)}
        onKeyDown={event=>{
          if(event.key==='ArrowLeft'||event.key==='ArrowRight'){event.preventDefault();applySidebarWidth(widthRef.current+(event.key==='ArrowLeft'?-20:20));}
          else if(event.key==='Home'||event.key==='End'){event.preventDefault();applySidebarWidth(event.key==='Home'?MIN_WIDTH:MAX_WIDTH);}
        }} />
      <div className="workspace-content"><WorkspaceTabs activeId={itemId} owner={owner} fallbackHref={libraryLocationHref(lastLibrary.current)}/>{children}</div>
    </div>
  </WorkspaceContext.Provider>;
}
