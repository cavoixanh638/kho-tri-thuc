import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { request } from './api';
import { KnowledgeExplorer } from './KnowledgeExplorer';
import { knowledgeNodeHref, type KnowledgeTreeData } from './KnowledgeTree';
import { libraryLocationHref, parseLibraryLocation } from './LibraryViews';
import { SavedCollectionsPanel } from './SavedCollections';
import { useResource } from './views';
import './KnowledgeExplorer.css';

type TreeResource = ReturnType<typeof useResource<KnowledgeTreeData>>;
const WorkspaceContext = createContext<{tree: TreeResource; revision: number} | null>(null);
export const useKnowledgeWorkspace = () => useContext(WorkspaceContext);
export const EXPLORER_CHANGED = 'knowledge-explorer-changed';
type NoteLocation = {item_id: string; home_topic_id: number | null; ancestors: {item_id: string}[]};

/** Keep the same explorer instance, scroll position and expansion state while
 * routing between library, individual notes and other authenticated screens. */
export function KnowledgeWorkspace({path, csrf, children}: {path?: string; csrf: string; children: ReactNode}) {
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
  const tree = useResource<KnowledgeTreeData>('/knowledge-tree', {refreshKey: String(revision)});
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
  const unfiled = activeLocation?.home_topic_id != null ? false : scope.unfiled;
  // Desktop never hides the sidebar. On narrow touch screens a compact toggle
  // avoids covering the reading area; its choice persists across routes.
  const [narrowOpen, setNarrowOpen] = useState(() => {
    try { return sessionStorage.getItem('kt-explorer-visible') === '1'; }
    catch { return false; }
  });
  return <WorkspaceContext.Provider value={{tree, revision}}>
    <div className="knowledge-library-layout knowledge-workspace" onClick={event => {
      if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      const target = event.target instanceof Element ? event.target.closest('a') : null;
      const href = target?.getAttribute('href');
      if (href?.startsWith('#/thu-vien') && !href.includes('collection=') && !href.includes('view=')) {
        event.preventDefault();
        window.location.hash = libraryLocationHref({...parseLibraryLocation(href), view: scope.view});
      }
    }}>
      <aside className={'library-tree-shell' + (narrowOpen ? ' is-open' : '')}>
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
      <div className="workspace-content">{children}</div>
    </div>
  </WorkspaceContext.Provider>;
}
