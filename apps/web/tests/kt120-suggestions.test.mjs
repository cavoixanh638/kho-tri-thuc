import assert from 'node:assert/strict';
import { before, after, test } from 'node:test';
import { setImmediate as settle } from 'node:timers/promises';
import { JSDOM } from 'jsdom';
import { createServer } from 'vite';

let ui,server,dom;
const originalFetch=globalThis.fetch;
before(async()=>{
  dom=new JSDOM('<!doctype html><html><body></body></html>',{url:'http://127.0.0.1:8120/',pretendToBeVisual:true});
  for(const name of ['window','document','navigator','HTMLElement','Element','Node','Event','MouseEvent'])Object.defineProperty(globalThis,name,{value:dom.window[name],configurable:true,writable:true});
  globalThis.IS_REACT_ACT_ENVIRONMENT=true;
  server=await createServer({server:{middlewareMode:true,hmr:false},appType:'custom',logLevel:'silent'});
  ui=await server.ssrLoadModule('/tests/kt120-entry.tsx');
});
after(async()=>{globalThis.fetch=originalFetch;await server?.close();dom?.window.close();});
const suggestion=(index)=>({item_id:'00000000-0000-4000-8000-000000000020',source_version:'source-v1',base_edit_version:index,before:`# Bài ${index}\r\nĐ/đ e\u0302\u0301 🧠\n`,after:`# Bài ${index}\r\nĐ/đ e\u0302\u0301 🧠\n> Đề xuất ${index}\n`,receipt:'signed-'+index,expires_in:900,provenance:{provider:'none',model:'none',method:'user_supplied_poc',prompt_version:'not_run'}});

for(let i=0;i<20;i++)test(`Vietnamese diff ${i}: exact before/after and inert preview/reject`,async()=>{
  const s=suggestion(i),d=ui.noteDiff(s.before,s.after);
  assert.equal(d.prefix+d.removed+d.suffix,s.before);assert.equal(d.prefix+d.added+d.suffix,s.after);
  const snapshot=JSON.stringify(s);const html=ui.renderToStaticMarkup(ui.createElement(ui.AiSuggestionDiff,{before:s.before,after:s.after}));
  assert.match(html,/Đề xuất/);assert.equal(JSON.stringify(s),snapshot);
  let calls=0,applied=0;globalThis.fetch=async(url,options)=>{calls++;assert.match(url,/\/reject$/);assert.equal(JSON.parse(options.body).receipt,s.receipt);return new Response(JSON.stringify({state:'rejected',writes:0}),{status:200});};
  const element=document.createElement('div');document.body.append(element);const root=ui.createRoot(element);
  await ui.act(async()=>{root.render(ui.createElement(ui.AiSuggestionReview,{suggestion:s,csrf:'fixture',currentNote:s.before,onApplied:()=>applied++,onClose(){}}));await settle();});
  assert.equal(calls,0);assert.equal(applied,0);
  const reject=[...element.querySelectorAll('button')].find(b=>b.textContent==='Từ chối');
  await ui.act(async()=>{reject.click();await settle();});assert.equal(calls,1);assert.equal(applied,0);assert.match(element.textContent,/Nội dung bài không đổi/);
  await ui.act(async()=>root.unmount());element.remove();
});
test('accept/undo need explicit clicks and exact receipt; repeated clicks do not duplicate request',async()=>{
  const s=suggestion(1),results=[];let resolve,calls=0;
  globalThis.fetch=async(url,options)=>{calls++;if(url.endsWith('/accept'))return new Promise(r=>{resolve=()=>r(new Response(JSON.stringify({note:s.after,edit_version:2,source_version:'source-v1',undo_receipt:'undo-signed'}),{status:200}));});assert.match(url,/\/undo$/);assert.equal(JSON.parse(options.body).receipt,'undo-signed');return new Response(JSON.stringify({note:s.before,edit_version:3,source_version:'source-v1',undo_receipt:''}),{status:200});};
  const element=document.createElement('div');document.body.append(element);const root=ui.createRoot(element);
  await ui.act(async()=>{root.render(ui.createElement(ui.AiSuggestionReview,{suggestion:s,csrf:'fixture',currentNote:s.before,onApplied:r=>results.push(r),onClose(){}}));await settle();});
  const button=[...element.querySelectorAll('button')].find(b=>b.textContent==='Chấp nhận');
  await ui.act(async()=>{button.click();button.click();await settle();});assert.equal(calls,1);assert.equal(results.length,0);
  await ui.act(async()=>{resolve();await settle();});assert.equal(results[0].note,s.after);
  const undo=[...element.querySelectorAll('button')].find(b=>b.textContent==='Hoàn tác đề xuất');await ui.act(async()=>{undo.click();await settle();});assert.equal(results[1].note,s.before);assert.equal(calls,2);
  await ui.act(async()=>root.unmount());element.remove();
});
test('draft conflict blocks acceptance and injected HTML remains escaped',()=>{
  const s={...suggestion(0),after:'<img src=x onerror=alert(1)><script>evil()</script>'};
  const html=ui.renderToStaticMarkup(ui.createElement(ui.AiSuggestionReview,{suggestion:s,csrf:'x',currentNote:'Người dùng đã sửa',onApplied(){},onClose(){}}));
  assert.doesNotMatch(html,/<img|<script/);assert.match(html,/Bản nháp đang khác/);assert.match(html,/disabled=""/);
});
