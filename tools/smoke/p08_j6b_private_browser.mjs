#!/usr/bin/env node
/** Real React + authenticated Django API + synthetic pinned PDF/MP4 bytes in a
 * second isolated WSGI process. App and sessions are NOT mocked; only the
 * external Google Drive byte adapter is replaced with SHA-verified QA files.
 * Browser must render the actual colored PDF page and seek video from UI.
 */
import assert from 'node:assert/strict';
import http from 'node:http';
import { inflateSync } from 'node:zlib';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { Browser } from './p08_cdp.mjs';
assert.equal(process.env.P08_J6B_ISOLATED, 'YES');
const backend = process.env.KT_J6B_BACKEND_IP || '';
assert.match(backend, /^(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})$/);
const data = JSON.parse(readFileSync(process.env.KT_J6B_MANIFEST, 'utf8'));
assert.equal(data.synthetic_only, true);
assert.equal(data.pdf_page_navigation_feature_flag, true);
assert.equal(data.owner, 'p08-fixture');
const web = 'http://127.0.0.1:62310';
const out = resolve('tmp/p08-j6b-private');
mkdirSync(out, { recursive: true });

function coloredPixels(png) {
  assert.equal(png.subarray(0,8).toString('hex'),'89504e470d0a1a0a');
  let pos=8,w=0,h=0,depth=0,type=0;const blocks=[];
  while(pos+12<=png.length){
    const len=png.readUInt32BE(pos),kind=png.toString('ascii',pos+4,pos+8);
    const bytes=png.subarray(pos+8,pos+8+len);pos+=len+12;
    if(kind==='IHDR'){w=bytes.readUInt32BE(0);h=bytes.readUInt32BE(4);depth=bytes[8];type=bytes[9];assert.equal(bytes[12],0);}
    if(kind==='IDAT')blocks.push(bytes);
    if(kind==='IEND')break;
  }
  assert.equal(depth,8);assert.ok(type===2||type===6);
  const n=type===2?3:4,stride=n*w,raw=inflateSync(Buffer.concat(blocks));
  let k=0,prev=Buffer.alloc(stride);const count={green:0,red:0,blue:0,total:0};
  for(let y=0;y<h;y++){
    const filter=raw[k++],row=Buffer.alloc(stride);
    for(let x=0;x<stride;x++){
      const v=raw[k++],left=x>=n?row[x-n]:0,above=prev[x],diag=x>=n?prev[x-n]:0;
      let f=0;
      if(filter===1)f=left;
      if(filter===2)f=above;
      if(filter===3)f=Math.floor((left+above)/2);
      if(filter===4){const p=left+above-diag,a=Math.abs(p-left),b=Math.abs(p-above),c=Math.abs(p-diag);f=a<=b&&a<=c?left:b<=c?above:diag;}
      assert.ok(filter>=0&&filter<=4);
      row[x]=(v+f)&255;
    }
    for(let x=0;x<w;x+=3){
      const i=n*x,R=row[i],G=row[i+1],B=row[i+2];count.total++;
      if(G>R*1.8&&G>B*1.8&&G>90)count.green++;
      if(R>G*1.8&&R>B*1.8&&R>90)count.red++;
      if(B>G*1.8&&B>R*1.8&&B>90)count.blue++;
    }
    prev=row;
  }
  count.ratio=count.green/Math.max(1,count.total);
  return count;
}
let proxy,browser;
function waitFor(page,fn,arg,reason,ms=12000){
  return (async()=>{
    const end=Date.now()+ms;
    do{
      const value=await page.eval(fn,arg);
      if(value)return value;
      await new Promise(resolve=>setTimeout(resolve,150));
    }while(Date.now()<end);
    throw Error('J6B_UI_TIMEOUT:'+reason);
  })();
}
async function openControl(page,text){
  await waitFor(page,t=>[...document.querySelectorAll('button')].some(x=>x.textContent.trim()===t&&!x.disabled),text,'button '+text);
  await page.eval(t=>[...document.querySelectorAll('button')].find(x=>x.textContent.trim()===t&&!x.disabled).click(),text);
}
async function getJson(page,path){
  return page.eval(async p=>{
    const response=await fetch('/api/v1'+p,{credentials:'same-origin'});
    return {status:response.status,body:await response.json()};
  },path);
}
const result={ task:'P08/J6B',status:'NOT_RUN',scope:'ISOLATED_APP_UI_PRIVATE_DJANGO_API',
  actual_drive:'NOT_RUN',native_android:'NOT_RUN', synthetic_byte_adapter:true, auth_api:true,
  backend_sha256_verified:false, real_browser_ui:false, pdf_displayed_page_verified:false,
  mp4_ui_seek_verified:false, checks:[] };
try{
  proxy=http.createServer((req,res)=>{
    const isMedia=req.url?.startsWith('/api/v1/assets/');
    const target=isMedia?'http://'+backend+':8001':web;
    const url=new URL(req.url||'/',target);
    const upstream=http.request(url,{method:req.method,headers:{...req.headers},timeout:14000},back=>{
      res.writeHead(back.statusCode||502,back.headers);
      back.pipe(res);
    });
    upstream.on('error',()=>{if(!res.headersSent)res.writeHead(502);res.end();});
    upstream.on('timeout',()=>upstream.destroy());
    req.pipe(upstream);
  });
  await new Promise((ok,bad)=>{proxy.once('error',bad);proxy.listen(0,'127.0.0.1',ok);});
  const origin='http://127.0.0.1:'+proxy.address().port;
  assert.equal((await fetch(origin+'/api/v1/assets/'+data.items.pdf.asset_id+'/viewer')).status,401);
  browser=await Browser.launch({binary:process.env.KT_JOURNEY_CHROMIUM});
  const page=await browser.newPage({width:1440,height:1080});
  await page.goto(origin);
  const login=await page.eval(async credentials=>{
    const session=await fetch('/api/v1/session',{credentials:'same-origin'}).then(r=>r.json());
    return fetch('/api/v1/session',{method:'POST',credentials:'same-origin',
      headers:{'Content-Type':'application/json','X-CSRFToken':session.csrf_token},
      body:JSON.stringify(credentials)}).then(r=>r.status);
  },{username:'p08-fixture',password:process.env.KT_J6B_QA_PASSWORD});
  assert.equal(login,200,'QA login');
  result.checks.push('real Django authenticated session');
  // The App's React auth state was mounted before the programmatic QA login.
  // A real navigation reload is required to hydrate the newly authenticated
  // session before hash-route content or citations become visible.
  await page.goto(origin+'/#/muc/'+data.items.pdf.item_id);
  for(const kind of ['pdf','mp4']){
    const fixture=data.items[kind],id=fixture.item_id,asset=fixture.asset_id;
    const knowledge=await getJson(page,'/items/'+id+'/knowledge');
    assert.equal(knowledge.status,200);
    assert.equal(knowledge.body.parts.length,1);
    assert.equal(knowledge.body.parts[0].source.state,'current');
    assert.equal(knowledge.body.parts[0].source.version,fixture.sha256);
    assert.equal(knowledge.body.parts[0].asset_id,asset);
    const note=await getJson(page,'/items/'+id);
    assert.equal(note.status,200);
    const response=await page.eval(async f=>{
      const base='/api/v1/assets/'+f.asset_id+'/content/1/'+f.sha256;
      const ranged=await fetch(base,{headers:{Range:'bytes=10-19'}});
      const stale=await fetch(base.replace(f.sha256,'a'.repeat(64)),{headers:{Range:'bytes=0-5'}});
      return {range_status:ranged.status,range_header:ranged.headers.get('content-range'),
              bytes:(await ranged.arrayBuffer()).byteLength,stale_status:stale.status};
    },fixture);
    assert.equal(response.range_status,206);
    assert.equal(response.bytes,10);
    assert.equal(response.range_header,'bytes 10-19/'+fixture.length);
    assert.equal(response.stale_status,409);
    result.checks.push(kind+' 206 range and stale sha fail-closed');
    await page.eval(hash=>{location.hash=hash;},'#/muc/'+id);
    await waitFor(page,id=>location.hash.endsWith(id),id,kind+' route');
    try {
      await waitFor(page,()=>!!document.querySelector('.source-locator'),null,kind+' SourceLocator');
    } catch(error) {
      const debug=await page.eval(()=>({hash:location.hash,
        title:document.title,visible:document.body.innerText.slice(0,600),
        citations:document.querySelectorAll('.source-citations').length}));
      console.error('J6B_QA_REACT_DIAGNOSTIC',JSON.stringify(debug));
      throw error;
    }
    const label=kind==='pdf'?'Mở và định vị PDF riêng tư':'Mở và định vị nguồn riêng tư';
    await openControl(page,label);
    if(kind==='pdf'){
      await waitFor(page,()=>!!document.querySelector('.source-locator-viewer iframe[src*="#page=2"]'),null,'private pdf iframe',16000);
      await page.eval(()=>document.querySelector('.source-locator-viewer iframe').scrollIntoView({block:'center'}));
      let colors={ratio:0};
      for(let i=0;i<10;i++){
        await new Promise(resolve=>setTimeout(resolve,450));
        const filepath=join(out,'private-pdf-page2.png');
        await page.screenshot({path:filepath,format:'png'});
        colors=coloredPixels(readFileSync(filepath));
        if(colors.ratio>=0.035&&colors.green>10*colors.red&&colors.green>10*colors.blue)break;
      }
      result.pdf_color_pixels=colors;
      result.pdf_displayed_page_verified=colors.ratio>=0.035&&colors.green>10*colors.red&&colors.green>10*colors.blue;
      assert.equal(result.pdf_displayed_page_verified,true,'Rendered private PDF not visibly on green page 2');
    }else{
      const video=await waitFor(page,()=>{
        const v=document.querySelector('.source-locator-viewer video');
        const status=document.querySelector('.source-locator-viewer [role="status"]')?.textContent;
        return v&&status?.startsWith('Đã đến')?{currentTime:v.currentTime,duration:v.duration,width:v.videoWidth,height:v.videoHeight}:null;
      },null,'private MP4 native seek',20000);
      assert.ok(Math.abs(video.currentTime-2.5)<=.25);
      assert.equal(video.width,320);
      assert.equal(video.height,180);
      result.mp4_ui_seek=video;
      result.mp4_ui_seek_verified=true;
    }
    const noteAfter=await getJson(page,'/items/'+id);
    assert.equal(noteAfter.body.note,note.body.note);
  }
  result.backend_sha256_verified=true;
  result.real_browser_ui=true;
  result.status=result.pdf_displayed_page_verified&&result.mp4_ui_seek_verified?'PASS_SYNTHETIC_PRIVATE_FULL_UI':'FAIL';
  writeFileSync(join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
  assert.equal(result.status,'PASS_SYNTHETIC_PRIVATE_FULL_UI');
  console.log(JSON.stringify({task:result.task,status:result.status,
    pdf_actual_green_ratio:result.pdf_color_pixels.ratio,
    mp4_actual_seconds:result.mp4_ui_seek.currentTime,drive:'NOT_RUN'}));
}finally{
  await browser?.close();
  if(proxy)await new Promise(resolve=>proxy.close(resolve));
}
