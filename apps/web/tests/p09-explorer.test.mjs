import assert from 'node:assert/strict';
import {before, beforeEach, afterEach, after, test} from 'node:test';
import {createServer} from 'vite';
import {JSDOM, VirtualConsole} from 'jsdom';
import {setImmediate as tick} from 'node:timers/promises';
const ID='12345678-1234-4567-89ab-123456789abc';
const childId=i=>'22345678-1234-4567-89ab-'+String(i).padStart(12,'0');
const folder=id=>({id,name:'Folder '+id,node_kind:'folder',parent_id:null,sort_order:id,direct_count:1,item_count:1,child_count:0,path:'Folder '+id,path_ids:[id],depth:0});
const note=(id=ID,home=1,shortcut=false)=>({item_id:id,title:'Ghi chú Tiếng Việt',kind:'text',home_topic_id:home,parent_item_id:null,sort_order:0,structure_version:0,child_count:0,shortcut,source_fetch:'not_applicable',asset_storage:'not_applicable'});
const folders=[1,2,3].map(folder);
const originalFetch=globalThis.fetch;
let vite,ui,dom,root,container,calls,writes,mode;
before(async()=>{
 dom=new JSDOM('<html><body></body></html>',{url:'http://127.0.0.1/#/thu-vien',pretendToBeVisual:true,virtualConsole:new VirtualConsole()});
 for(const name of ['window','document','navigator','HTMLElement','Element','Node','Event','MouseEvent','KeyboardEvent','CustomEvent','MutationObserver','getComputedStyle'])
   Object.defineProperty(globalThis,name,{value:name==='getComputedStyle'?dom.window[name].bind(dom.window):dom.window[name],configurable:true,writable:true});
 window.matchMedia=()=>({matches:false,addEventListener(){},removeEventListener(){}});
 globalThis.ResizeObserver=class{observe(){}unobserve(){}disconnect(){}};
 Object.defineProperty(document,'fonts',{value:new dom.window.EventTarget(),configurable:true});
 globalThis.requestAnimationFrame=window.requestAnimationFrame.bind(window);
 globalThis.cancelAnimationFrame=window.cancelAnimationFrame.bind(window);
 globalThis.IS_REACT_ACT_ENVIRONMENT=true;
 vite=await createServer({server:{middlewareMode:true,hmr:false},appType:'custom',logLevel:'silent'});
 ui=await vite.ssrLoadModule('/tests/kt122-explorer-entry.tsx');
});
beforeEach(()=>{
 calls=[];writes=[];mode='normal';window.location.hash='#/thu-vien';
 container=document.createElement('div');document.body.append(container);root=ui.createRoot(container);
 globalThis.fetch=async(path,options={})=>{
  const url=new URL(path,'http://127.0.0.1');calls.push(url.pathname+url.search);
  if(options.method && options.method!=='GET'){
   writes.push({path:String(path),method:options.method,body:JSON.parse(options.body??'{}')});
   if(mode==='conflict')return Response.json({code:'structure_conflict'},{status:409});
   return Response.json({});
  }
  if(url.pathname.endsWith('/explorer/children')){
   const folderId=url.searchParams.get('folder_id');
   const offset=Number(url.searchParams.get('offset')||0);
   if(folderId)return Response.json({folders:[],notes:[note(ID,1,folderId!=='1')],next_offset:null});
   if(mode==='paged'){
    const rows=Array.from({length:55},(_,i)=>note(childId(i),null,false));
    return Response.json({folders:[],notes:rows.slice(offset,offset+50),next_offset:offset+50<rows.length?offset+50:null});
   }
   return Response.json({folders,notes:[],next_offset:null});
  }
  if(url.pathname.endsWith('/structure')){
   const children=Array.from({length:51},(_,i)=>note(childId(i)));
   return Response.json({item_id:ID,parent_item_id:null,home_topic_id:1,sort_order:0,structure_version:0,origin:'user',ancestors:[],children:mode==='over50'?children.slice(0,50):[]});
  }
  if(url.pathname.endsWith('/knowledge-tree'))return Response.json({nodes:folders});
  if(url.pathname.endsWith('/explorer/find'))return Response.json({results:[]});
  return Response.json({});
 };
});
afterEach(async()=>{await ui.act(async()=>root.unmount());container.remove();});
after(async()=>{globalThis.fetch=originalFetch;await vite.close();dom.window.close();});
async function render(component=ui.KnowledgeExplorer,props={data:{nodes:folders},onRetry(){},selectedId:null,unfiled:false,csrf:'p09-csrf',onSaved(){}}){
 await ui.act(async()=>{root.render(ui.createElement(ui.MantineProvider,null,ui.createElement(component,props)));await tick();});
}
async function click(label){
 const button=[...container.querySelectorAll('button,summary')].find(entry=>entry.textContent===label||entry.getAttribute('aria-label')===label);
 assert.ok(button,'Missing button '+label);
 await ui.act(async()=>{button.click();await new Promise(resolve=>setTimeout(resolve,20));});
}
test('P09 same UUID across three folder entries; no capture',async()=>{
 await render();
 for(const id of [1,2,3])await click('Mở Folder '+id);
 const anchors=[...container.querySelectorAll('a[href="#/muc/'+ID+'"]')];
 assert.equal(anchors.length,3);
 assert.equal(new Set(anchors.map(entry=>entry.getAttribute('href'))).size,1);
 assert.equal(container.textContent.split('Lối tắt · cùng một bài').length-1,2);
 assert.equal(writes.length,0);
});
test('P09 stale move surfaces conflict without new CaptureEvent',async()=>{
 await render();await click('Mở Folder 1');await click('Thao tác ghi chú Ghi chú Tiếng Việt');
 mode='conflict';await click('Chuyển vị trí chính');
 assert.equal(writes.length,1);
 assert.ok(writes[0].path.endsWith('/items/'+ID+'/placement'));
 assert.deepEqual(writes[0].body,{action:'move',folder_id:null,expected_version:0});
 assert.match(container.textContent,/Cấu trúc đã đổi ở phiên khác/);
 assert.equal(writes.filter(row=>row.path.endsWith('/explorer/notes')).length,0);
});
test('P09 paginates 55 notes with no duplicate IDs',async()=>{
 mode='paged';await render();
 assert.equal(container.querySelectorAll('a[href^="#/muc/"]').length,50);
 await click('Tải thêm thư mục / ghi chú');
 const hrefs=[...container.querySelectorAll('a[href^="#/muc/"]')].map(el=>el.getAttribute('href'));
 assert.equal(hrefs.length,55);
 assert.equal(new Set(hrefs).size,55);
 assert.ok(calls.some(row=>row.includes('offset=50')));
});
test('P09 known limitation: structure panel cannot reach child 51',async()=>{
 mode='over50';await render(ui.ItemStructurePanel,{id:ID,csrf:'p09-csrf'});
 assert.match(container.textContent,/Bài con \(50\)/);
 assert.equal(container.querySelectorAll('a[href^="#/muc/"]').length,50);
 assert.equal(container.textContent.includes('Tải thêm'),false);
 assert.equal(writes.length,0);
});
test('P09 IME composing ArrowRight never expands folder',async()=>{
 await render();const row=container.querySelector('[role="treeitem"]');
 assert.ok(row);
 await ui.act(async()=>{row.dispatchEvent(new window.KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true,isComposing:true}));await tick();});
 assert.equal(row.getAttribute('aria-expanded'),'false');
 assert.equal(writes.length,0);
});
