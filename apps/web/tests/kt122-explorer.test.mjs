import assert from 'node:assert/strict';
import {before,after,beforeEach,afterEach,test} from 'node:test';
import {createServer} from 'vite';
import {JSDOM,VirtualConsole} from 'jsdom';
import {setImmediate as settle} from 'node:timers/promises';
let server,ui,dom,root,container,calls,mutations,fail;
const originalFetch=globalThis.fetch;
const id='12345678-1234-4567-89ab-123456789abc',child='22345678-1234-4567-89ab-123456789abc';
const folder={id:1,name:'Sách tiếng Việt',node_kind:'book',parent_id:null,sort_order:0,direct_count:1,item_count:1,child_count:0,depth:0,path:'Sách tiếng Việt',path_ids:[1]};
const note={item_id:id,title:'Bài Tiếng Việt',kind:'text',home_topic_id:1,parent_item_id:null,sort_order:0,structure_version:0,child_count:1,shortcut:false,source_fetch:'not_applicable',asset_storage:'not_applicable'};
before(async()=>{
 dom=new JSDOM('<html><body></body></html>',{url:'http://127.0.0.1/#/thu-vien',pretendToBeVisual:true,virtualConsole:new VirtualConsole()});
 for(const name of ['window','document','navigator','HTMLElement','Element','Node','Event','MouseEvent','KeyboardEvent','CustomEvent','MutationObserver','getComputedStyle'])Object.defineProperty(globalThis,name,{value:name==='getComputedStyle'?dom.window[name].bind(dom.window):dom.window[name],configurable:true,writable:true});
 window.matchMedia=()=>({matches:false,addEventListener(){},removeEventListener(){}});
 globalThis.ResizeObserver=class{observe(){}unobserve(){}disconnect(){}};
 Object.defineProperty(document,'fonts',{value:new dom.window.EventTarget(),configurable:true});
 globalThis.requestAnimationFrame=window.requestAnimationFrame.bind(window);globalThis.cancelAnimationFrame=window.cancelAnimationFrame.bind(window);globalThis.IS_REACT_ACT_ENVIRONMENT=true;
 server=await createServer({server:{middlewareMode:true,hmr:false},appType:'custom',logLevel:'silent'});ui=await server.ssrLoadModule('/tests/kt122-explorer-entry.tsx');
});
beforeEach(()=>{
 calls=[];mutations=[];fail=false;window.location.hash='#/thu-vien';
 container=document.createElement('div');document.body.append(container);root=ui.createRoot(container);
 globalThis.fetch=async(path,options={})=>{
  calls.push(String(path));const url=new URL(path,'http://127.0.0.1');
  if(options.method && options.method!=='GET'){mutations.push({path,body:JSON.parse(options.body??'{}'),headers:options.headers});if(fail)return Response.json({code:'structure_conflict'},{status:409});if(path.endsWith('/explorer/notes'))return Response.json({item_id:child,capture_id:'synthetic',received_at:'2026-11-21T00:00:00Z',state:'received'});return Response.json({});}
  if(url.pathname.endsWith('/explorer/children')){
   if(url.searchParams.has('parent_item_id'))return Response.json({folders:[],notes:[{...note,item_id:child,title:'Chương con',parent_item_id:id,child_count:0}],next_offset:null});
   if(url.searchParams.get('folder_id')==='1')return Response.json({folders:[],notes:[note],next_offset:null});
   return Response.json({folders:[folder],notes:[],next_offset:null});
  }
  if(url.pathname.endsWith('/structure'))return Response.json({item_id:id,parent_item_id:null,home_topic_id:1,sort_order:0,structure_version:0,origin:'user',ancestors:[],children:[{...note,item_id:child,title:'Chương con',parent_item_id:id,child_count:0}]});
  if(url.pathname.endsWith('/knowledge-tree'))return Response.json({nodes:[folder]});
  if(url.pathname.endsWith('/collections'))return Response.json({results:[]});
  if(url.pathname.endsWith('/navigation'))return Response.json({items:[{item_id:id,title:note.title,saved_at:'2026-11-21T00:00:00Z'}],folders:[{id:1,name:folder.name,parent_id:null}],next_offset:null});
  if(url.pathname.endsWith('/explorer/find'))return Response.json({results:[{...note,item_id:child,title:'Bài cha đã chọn'}]});
  return Response.json({user_edit_version:4});
 };
});
afterEach(async()=>{await ui.act(async()=>root.unmount());container.remove();});
after(async()=>{globalThis.fetch=originalFetch;await server.close();dom.window.close();});
async function render(component=ui.KnowledgeExplorer,props={data:{nodes:[folder]},onRetry(){},selectedId:null,unfiled:false,csrf:'fixture-csrf',onSaved(){}}){await ui.act(async()=>{root.render(ui.createElement(ui.MantineProvider,null,ui.createElement(component,props)));await settle();});}
async function click(label){const element=[...container.querySelectorAll('button,summary')].find((node)=>node.textContent===label||node.getAttribute('aria-label')===label);assert.ok(element,label);await ui.act(async()=>{element.click();await new Promise(r=>setTimeout(r,20));});}
async function input(selector,value){const field=container.querySelector(selector);assert.ok(field,selector);await ui.act(async()=>{Object.getOwnPropertyDescriptor(field.tagName==='TEXTAREA'?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype,'value').set.call(field,value);field.dispatchEvent(new window.Event('input',{bubbles:true}));await settle();});}
test('initial mixed navigator loads one bounded page and lazy-loads notes/children only on expand',async()=>{
 await render();assert.equal(calls.filter(path=>path.includes('/explorer/children')).length,1);assert.equal(container.querySelectorAll('[role=treeitem]').length,1);
 await click('Mở Sách tiếng Việt');assert.ok(container.querySelector('a[href="#/muc/'+id+'"]'));assert.equal(container.querySelectorAll('select').length,0);
 await click('Mở bài con Bài Tiếng Việt');assert.ok(container.querySelector('a[href="#/muc/'+child+'"]'));
 assert.equal(mutations.length,0);
});
test('note menu moves main folder with structure precondition and CSRF, no capture',async()=>{
 await render();await click('Mở Sách tiếng Việt');await click('Thao tác ghi chú Bài Tiếng Việt');await click('Chuyển vị trí chính');
 assert.equal(mutations.length,1);assert.deepEqual(mutations[0].body,{action:'move',folder_id:null,expected_version:0});assert.equal(mutations[0].headers.get('X-CSRFToken'),'fixture-csrf');
 assert.ok(!mutations.some(row=>row.path.endsWith('/explorer/notes')));
});
test('create-at-folder keeps Vietnamese draft and uses one idempotency key on failed retry',async()=>{
 await render();await click('Thêm ghi chú tại đây');await input('.explorer-note-form textarea','Nguyên văn Tiếng Việt\n');
 fail=true;await click('Tạo ghi chú');const first=mutations.at(-1);assert.equal(container.querySelector('.explorer-note-form textarea').value,'Nguyên văn Tiếng Việt\n');
 fail=false;await click('Tạo ghi chú');const second=mutations.at(-1);assert.equal(first.headers.get('Idempotency-Key'),second.headers.get('Idempotency-Key'));assert.equal(second.body.text,'Nguyên văn Tiếng Việt\n');assert.equal(window.location.hash,'#/muc/'+child);
});
test('desktop drop uses move; Ctrl-drop adds a shortcut to same note UUID',async()=>{
 await render();
 for(const ctrlKey of [false,true]){
  await ui.act(async()=>{const event=new window.Event('drop',{bubbles:true,cancelable:true});Object.defineProperties(event,{ctrlKey:{value:ctrlKey},dataTransfer:{value:{getData(){return JSON.stringify({kind:'note',id,version:0});}}}});container.querySelector('.explorer-row').dispatchEvent(event);await settle();});
 }
 assert.deepEqual(mutations.map(row=>row.body.action),['move','add']);assert.ok(mutations.every(row=>row.path.endsWith('/items/'+id+'/placement')));
});
test('keyboard arrows/Space expand folder while IME composition does not intercept keys',async()=>{
 await render();const row=container.querySelector('[role=treeitem]');
 await ui.act(async()=>{row.dispatchEvent(new window.KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true,isComposing:true}));await settle();});assert.equal(row.getAttribute('aria-expanded'),'false');
 await ui.act(async()=>{row.dispatchEvent(new window.KeyboardEvent('keydown',{key:' ',bubbles:true}));await settle();});assert.equal(row.getAttribute('aria-expanded'),'true');
});
test('move command opens and focuses placement controls in real structure panel',async()=>{
 await render(ui.ItemStructurePanel,{id,csrf:'fixture-csrf'});
 await ui.act(async()=>{window.dispatchEvent(new window.CustomEvent('knowledge-command',{detail:{action:'move',itemId:id}}));await new Promise(r=>setTimeout(r,20));});
 const details=[...container.querySelectorAll('details')].find(node=>node.textContent.includes('Chuyển thư mục / thêm lối tắt'));assert.equal(details.open,true);assert.equal(document.activeElement,details.querySelector('select'));
 assert.match(container.textContent,/Bài con \(1\)/);assert.ok(container.querySelector('a[href="#/muc/'+child+'"]'));
});
test('create command opens note composer at current selected folder',async()=>{
 await render(ui.KnowledgeExplorer,{data:{nodes:[folder]},onRetry(){},selectedId:1,unfiled:false,csrf:'fixture-csrf',onSaved(){}});
 await ui.act(async()=>{window.dispatchEvent(new window.CustomEvent('knowledge-command',{detail:{action:'create'}}));await settle();});assert.match(container.querySelector('.explorer-note-form h2').textContent,/Sách tiếng Việt/);
 await input('.explorer-note-form textarea','Nội dung');await click('Tạo ghi chú');assert.equal(mutations.at(-1).body.home_topic_id,1);
});

test('folder collapse releases DOM, reopening cached branch does not request it again',async()=>{
 await render();await click('Mở Sách tiếng Việt');
 const before=calls.filter(path=>path.includes('/explorer/children')).length;
 await click('Thu gọn Sách tiếng Việt');
 const closing=container.querySelector('.explorer-branch-reveal[aria-hidden="true"]');
 assert.ok(closing.hasAttribute('inert'));
 await ui.act(async()=>{await new Promise(r=>setTimeout(r,220));});
 assert.equal(container.querySelector('a[href="#/muc/'+id+'"]'),null);
 await click('Mở Sách tiếng Việt');
 assert.ok(container.querySelector('a[href="#/muc/'+id+'"]'));
 assert.equal(calls.filter(path=>path.includes('/explorer/children')).length,before);
});
test('workspace retains the same explorer DOM across library, note and other authenticated routes',async()=>{
 const draw=path=>render(ui.KnowledgeWorkspace,{path,csrf:'fixture-csrf',children:ui.createElement('article',null,'Content '+path)});
 await draw('#/thu-vien?node=1');
 const sidebar=container.querySelector('.library-tree-shell');
 const row=container.querySelector('.explorer-folder-item');
 assert.ok(sidebar&&row);
 assert.equal(row.getAttribute('aria-expanded'),'true');
 const before=calls.filter(path=>path.includes('/explorer/children')).length;
 await draw('#/muc/'+id);
 assert.equal(container.querySelector('.library-tree-shell'),sidebar);
 assert.equal(container.querySelector('.explorer-folder-item'),row);
 assert.equal(row.getAttribute('aria-expanded'),'true');
 assert.equal(container.querySelector('a[href="#/muc/'+id+'"]').getAttribute('aria-current'),'page');
 await draw('#/thu-vien?unfiled=1');
 assert.equal(container.querySelector('.library-tree-shell'),sidebar);
 assert.equal(container.querySelector('.explorer-folder-item'),row);
 assert.equal(row.getAttribute('aria-expanded'),'true');
 await draw('#/tim-kiem');
 assert.equal(container.querySelector('.library-tree-shell'),sidebar);
 assert.equal(row.getAttribute('aria-expanded'),'true');
 assert.equal(calls.filter(path=>path.includes('/explorer/children')).length,before);
});


test('TREE-07 collapse all and reopen cached expanded branches without duplicate fetch',async()=>{
 await render();await click('Mở Sách tiếng Việt');await click('Mở bài con Bài Tiếng Việt');
 const before=calls.filter(path=>path.includes('/explorer/children')).length;
 await click('Thu gọn tất cả');
 await ui.act(async()=>{await new Promise(r=>setTimeout(r,220));});
 assert.equal(container.querySelector('.explorer-folder-item').getAttribute('aria-expanded'),'false');
 assert.equal(container.querySelector('a[href="#/muc/'+child+'"]'),null);
 await click('Mở lại nhánh vừa thu gọn');
 assert.equal(container.querySelector('.explorer-folder-item').getAttribute('aria-expanded'),'true');
 assert.ok(container.querySelector('a[href="#/muc/'+child+'"]'));
 assert.equal(calls.filter(path=>path.includes('/explorer/children')).length,before);
});
test('TREE-08 malformed optional sidebar payloads do not crash current route; retry recovers',async()=>{
 const fetchValid=globalThis.fetch;let incompatible=true;
 globalThis.fetch=async(path,options)=>{
  const url=new URL(path,'http://127.0.0.1');
  if(incompatible&&(url.pathname.endsWith('/knowledge-tree')||url.pathname.endsWith('/collections')))return Response.json({unexpected:true});
  return fetchValid(path,options);
 };
 await render(ui.KnowledgeWorkspace,{path:'#/gui',csrf:'fixture-csrf',children:ui.createElement('article',null,'Current capture content')});
 assert.equal(container.querySelector('.workspace-content article').textContent,'Current capture content');
 assert.match(container.querySelector('.knowledge-explorer').textContent,/Chưa tải được mục lục/);
 assert.match(container.querySelector('.saved-collections-panel').textContent,/Chưa tải được bộ sưu tập/);
 incompatible=false;
 await ui.act(async()=>{
  container.querySelector('.knowledge-explorer [role=alert] button').click();
  container.querySelector('.saved-collections-panel [role=alert] button').click();
  await new Promise(r=>setTimeout(r,40));
 });
 assert.ok(container.querySelector('.explorer-folder-item'));
 assert.match(container.querySelector('.saved-collections-panel').textContent,/Chưa có bộ lọc đã lưu/);
 assert.equal(container.querySelector('.workspace-content article').textContent,'Current capture content');
});
test('WS-02 sidebar resize by keyboard, pointer, reset and persistence across reload',async()=>{
 window.sessionStorage.removeItem('kt-explorer-width');
 const props={path:'#/thu-vien',csrf:'fixture-csrf',children:ui.createElement('article',null,'Content')};
 await render(ui.KnowledgeWorkspace,props);
 const divider=container.querySelector('.workspace-divider');
 const width=()=>container.querySelector('.knowledge-workspace').style.getPropertyValue('--kt-explorer-width');
 assert.equal(width(),'286px');
 const press=async key=>ui.act(async()=>{divider.dispatchEvent(new window.KeyboardEvent('keydown',{key,bubbles:true}));await settle();});
 await press('ArrowRight');assert.equal(width(),'306px');
 await press('End');assert.equal(width(),'480px');await press('ArrowRight');assert.equal(width(),'480px');
 await press('Home');assert.equal(width(),'240px');
 await ui.act(async()=>{
  for(const [type,x] of [['pointerdown',100],['pointermove',160],['pointerup',160]]){
   const event=new window.MouseEvent(type,{clientX:x,button:0,bubbles:true,cancelable:true});
   Object.defineProperty(event,'pointerId',{value:1});divider.dispatchEvent(event);
  }
  await settle();
 });
 assert.equal(width(),'300px');
 await render(ui.KnowledgeWorkspace,{...props,key:'remounted'});assert.equal(width(),'300px');
 await ui.act(async()=>{container.querySelector('.workspace-divider').dispatchEvent(new window.MouseEvent('dblclick',{bubbles:true}));await settle();});
 assert.equal(width(),'286px');window.sessionStorage.removeItem('kt-explorer-width');
});


test('TREE-09 quick search uses bounded navigation and keeps the original tree mounted',async()=>{
 await render();await click('Mở Sách tiếng Việt');
 const row=container.querySelector('.explorer-folder-item');
 await input('input[aria-label="Tìm nhanh trong cây"]','Tiếng Việt');
 await ui.act(async()=>{await new Promise(r=>setTimeout(r,180));});
 assert.ok(calls.some(path=>path.includes('/navigation?')&&decodeURIComponent(path).includes('Tiếng Việt')));
 const results=container.querySelector('.explorer-search-results');
 assert.ok(results.querySelector('a[href="#/muc/'+id+'"]'));
 assert.ok(results.querySelector('a[href="#/thu-vien?node=1"]'));
 assert.equal(container.querySelector('.explorer-folder-item'),row);
 assert.equal(row.getAttribute('aria-expanded'),'true');
 assert.equal(mutations.length,0);
 await ui.act(async()=>{container.querySelector('input[aria-label="Tìm nhanh trong cây"]').dispatchEvent(new window.KeyboardEvent('keydown',{key:'Escape',bubbles:true}));await settle();});
 assert.equal(container.querySelector('.explorer-search-results'),null);
 assert.equal(container.querySelector('.explorer-folder-item'),row);
});
test('TREE-06 active canonical note scrolls the navigator only after lazy expansion',async()=>{
 const draw=path=>render(ui.KnowledgeWorkspace,{path,csrf:'fixture-csrf',children:ui.createElement('article',null,'Content')});
 await draw('#/thu-vien?node=1');
 await draw('#/muc/'+id);
 const shell=container.querySelector('.library-tree-shell');
 const anchor=shell.querySelector('a[data-explorer-primary="true"][aria-current="page"]');
 assert.ok(anchor);
 shell.getBoundingClientRect=()=>({top:0,bottom:100,height:100});
 anchor.getBoundingClientRect=()=>({top:230,bottom:250,height:20});
 shell.scrollTop=0;
 await ui.act(async()=>{await new Promise(r=>setTimeout(r,240));});
 assert.equal(shell.scrollTop,158);
 assert.equal(container.querySelector('.workspace-content article').textContent,'Content');
});


test('malformed optional structure response shows retry without crashing the note shell',async()=>{
 const validFetch=globalThis.fetch;let invalid=true;
 globalThis.fetch=async(path,options)=>String(path).endsWith('/structure')&&invalid?Response.json({item_id:id}):validFetch(path,options);
 await render(ui.ItemStructurePanel,{id,csrf:'fixture-csrf'});
 assert.match(container.textContent,/Chưa tải được cấu trúc bài/);assert.equal(container.querySelector('details'),null);
 invalid=false;await click('Thử lại');
 assert.match(container.textContent,/Bài con \(1\)/);assert.ok(container.querySelector('a[href="#/muc/'+child+'"]'));
 assert.equal(mutations.length,0);
});
