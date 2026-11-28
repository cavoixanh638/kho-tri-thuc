import assert from 'node:assert/strict';
import { after, before, test } from 'node:test';
import { setImmediate as settle } from 'node:timers/promises';
import { createServer } from 'vite';
import { JSDOM, VirtualConsole } from 'jsdom';
import { readFileSync } from 'node:fs';

let server, ui, dom;
const originalFetch = globalThis.fetch;
before(async () => {
  dom = new JSDOM('<!doctype html><html><body></body></html>', { url:'http://127.0.0.1:5173/#/thu-vien', pretendToBeVisual:true, virtualConsole:new VirtualConsole() });
  for (const name of ['window','document','navigator','HTMLElement','Element','Node','Event','MouseEvent','CustomEvent','MutationObserver','getComputedStyle']) Object.defineProperty(globalThis,name,{value:name==='getComputedStyle'?dom.window[name].bind(dom.window):dom.window[name],configurable:true,writable:true});
  window.matchMedia = () => ({matches:false,addEventListener(){},removeEventListener(){}});
  globalThis.ResizeObserver = class {observe(){} unobserve(){} disconnect(){}};
  Object.defineProperty(document,'fonts',{value:new dom.window.EventTarget(),configurable:true});
  globalThis.requestAnimationFrame=window.requestAnimationFrame.bind(window); globalThis.cancelAnimationFrame=window.cancelAnimationFrame.bind(window);
  globalThis.IS_REACT_ACT_ENVIRONMENT=true;
  server=await createServer({server:{middlewareMode:true,hmr:false},appType:'custom',logLevel:'silent'});
  ui=await server.ssrLoadModule('/tests/kt118-entry.tsx');
});
after(async()=>{globalThis.fetch=originalFetch;await server?.close();dom?.window.close();});

const item=(i)=>({item_id:`00000000-0000-4000-8000-${String(i).padStart(12,'0')}`,kind:'text',title:`Bài tiếng Việt ${i}`,note:`Nội dung Đ/đ e\u0302\u0301 ${i}`,description:'',saved_at:'2026-11-19T23:00:00Z',published_at:i%2?'2020-01-01T00:00:00Z':null,updated_at:'2026-11-20T00:00:00Z',favorite:i%7===0,deleted:false,classification_status:'user_assigned',original_url:'',source_fetch:'not_applicable',asset_storage:'not_applicable',content_extract:'not_available',assets:[]});
const ids=(html)=>[...html.matchAll(/data-library-item="([^"]+)"/g)].map(m=>m[1]);

test('all 10000+ IDs remain equal across four modes after every page, including equal timestamps',()=>{
  const databasePages = process.env.KT118_DB_FIXTURE ? JSON.parse(readFileSync(process.env.KT118_DB_FIXTURE,'utf8')).pages : null;
  const corpus=databasePages ? databasePages.flat().map(Object.freeze) : Array.from({length:10000},(_,i)=>Object.freeze(item(10000-i)));
  assert.ok(corpus.length>=10000);
  const original=JSON.stringify(corpus);
  const sets={};
  for (const mode of ['list','table','card','timeline']) {
    const collected=[];
    for(let offset=0;offset<corpus.length;offset+=50) collected.push(...ids(ui.renderToStaticMarkup(ui.createElement(ui.LibraryViews,{items:corpus.slice(offset,offset+50),mode}))));
    assert.equal(collected.length,corpus.length); assert.equal(new Set(collected).size,corpus.length);
    assert.deepEqual(collected,corpus.map(r=>r.item_id)); sets[mode]=new Set(collected);
  }
  assert.deepEqual(sets.list,sets.table);assert.deepEqual(sets.list,sets.card);assert.deepEqual(sets.list,sets.timeline);
  assert.equal(JSON.stringify(corpus),original,'rendering never mutates notes, IDs or asset mappings');
});
test('URL state roundtrips branch, filters, paging and mode; unsafe offsets/modes are bounded',()=>{
  const state={id:7,unfiled:false,filter:'favorite',offset:100,view:'table'};
  assert.deepEqual(ui.parseLibraryLocation(ui.libraryLocationHref(state)),state);
  assert.deepEqual(ui.parseLibraryLocation('#/thu-vien?unfiled=1&filter=deleted&view=timeline&offset=50'),{id:null,unfiled:true,filter:'deleted',offset:50,view:'timeline'});
  for(const hash of ['#/thu-vien?offset=-50&view=evil&node=NaN','#/thu-vien?offset=1000001','#/thu-vien?offset=51']) assert.equal(ui.parseLibraryLocation(hash).offset,0);
});
test('timeline uses first-received Vietnam day, not published_at; text stays escaped',()=>{
  const row={...item(1),title:'<img src=x onerror=alert(1)>',note:'<script>alert(1)</script>'};
  const html=ui.renderToStaticMarkup(ui.createElement(ui.LibraryViews,{items:[row],mode:'timeline'}));
  assert.match(html,/20\/11\/2026/); assert.doesNotMatch(html,/01\/01\/2020/); assert.doesNotMatch(html,/<script|<img/);
  const table=ui.renderToStaticMarkup(ui.createElement(ui.LibraryViews,{items:[row],mode:'table'}));
  assert.match(table,/Ngày nguồn đăng/); assert.match(table,/Nhận lần đầu/);
});
test('changing mode preserves query/page and issues no new fetch; filter and branch reset paging only',async()=>{
  window.history.replaceState(null,'','/#/thu-vien?node=7&filter=favorite&offset=50');
  const calls=[];
  globalThis.fetch=async(url)=>{calls.push(String(url));return new Response(JSON.stringify(String(url).includes('knowledge-tree')?{nodes:[{id:7,parent_id:null,name:'Kho thử',node_kind:'library',sort_order:0,depth:0,path_ids:[7],path:'Kho thử',direct_count:150,item_count:150,child_count:0}]}:{results:[item(1)],next_offset:100}),{status:200});};
  const container=document.createElement('div');document.body.append(container);const root=ui.createRoot(container);
  await ui.act(async()=>{root.render(ui.createElement(ui.MantineProvider,null,ui.createElement(ui.LibraryScreen,{})));await settle();});
  const initial=calls.filter(c=>c.includes('/items?')).length;
  const select=container.querySelector('select[aria-label="Cách xem thư viện"]');assert.ok(select);
  await ui.act(async()=>{select.value='table';select.dispatchEvent(new window.Event('change',{bubbles:true}));await settle();});
  assert.equal(calls.filter(c=>c.includes('/items?')).length,initial);
  assert.match(locationSafe(),/node=7/);assert.match(locationSafe(),/filter=favorite/);assert.match(locationSafe(),/offset=50/);assert.match(locationSafe(),/view=table/);
  assert.ok(container.querySelector('table'));
  const node=container.querySelector('a[href="#/thu-vien"]');assert.ok(node);
  await ui.act(async()=>{node.dispatchEvent(new window.MouseEvent('click',{bubbles:true,button:0,cancelable:true}));await settle();});
  assert.equal(ui.parseLibraryLocation(window.location.hash).view,'table');assert.equal(ui.parseLibraryLocation(window.location.hash).offset,0);assert.equal(ui.parseLibraryLocation(window.location.hash).filter,'all');
  await ui.act(async()=>root.unmount());container.remove();
});
function locationSafe(){return window.location.hash;}
