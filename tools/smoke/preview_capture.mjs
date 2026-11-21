#!/usr/bin/env node
/**
 * Browser screenshots of the REAL built App, NOT a UI mock.
 * Isolated ephemeral PostgreSQL/Compose only; no production or external source URL.
 * Browser screenshot artifacts never contain login credentials or private data.
 */
import assert from 'node:assert/strict';
import { randomUUID, createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { resolve, basename } from 'node:path';
import { Browser } from './p08_cdp.mjs';

const ORIGIN='http://127.0.0.1:5173';
const out=resolve(process.env.KT_PREVIEW_OUT || 'tmp/kt-preview-ui');
const evidence={kind:'REAL_BUILT_APP_BROWSER_CAPTURE', source:'React built App + Django + isolated PostgreSQL',
  code_sha:null, width_height:[], files:[], errors:[], synthetic_data_only:true,
  physical_android:'NOT_RUN', physical_ime:'NOT_RUN', real_google_drive:'NOT_RUN'};
try{evidence.code_sha=execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim();}catch{}
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const requireQA=()=>{
  assert.equal(process.env.KT_PREVIEW_ISOLATED,'YES','Explicit isolated QA confirmation required');
  assert.equal(process.env.KT_PREVIEW_URL,ORIGIN,'Only fixed QA origin allowed');
  assert.ok(/^(p08|kt)-[a-z0-9-]+$/.test(process.env.KT_PREVIEW_USER||''),'Synthetic QA username required');
  assert.ok(process.env.KT_PREVIEW_PASSWORD,'Synthetic QA password required');
};
let browser,page;
async function wait(fn,arg,label,limit=18000){
  const end=Date.now()+limit;
  while(Date.now()<end){try{if(await page.eval(fn,arg))return;}catch{}await sleep(140);}
  throw Error('UI_TIMEOUT: '+label);
}
async function gotoHash(hash,selector){
  await page.eval(h=>{location.hash=h;},hash);
  await wait(s=>!!document.querySelector(s),selector,hash+' '+selector);
  await sleep(650);
}
async function screenshot(name,width,height){
  await page.setViewport({width,height});
  await sleep(300);
  const path=resolve(out,name);
  await page.screenshot({path,format:'png'});
  const buf=readFileSync(path);
  assert.ok(buf.length>4096,'Browser screenshot unusually small: '+name);
  evidence.files.push({name:basename(path),width,height,bytes:buf.length,
    sha256:createHash('sha256').update(buf).digest('hex')});
}
async function api(path,method='GET',body){
  return page.eval(async({path,method,body})=>{
    const session=await fetch('/api/v1/session',{credentials:'same-origin'}).then(r=>r.json());
    const response=await fetch('/api/v1'+path,{
      method,credentials:'same-origin',
      headers:{'Content-Type':'application/json',...(session.csrf_token?{'X-CSRFToken':session.csrf_token}:{}),
        ...(method!=='GET'?{'Idempotency-Key':crypto.randomUUID()}:{} )},
      ...(body===undefined?{}:{body:JSON.stringify(body)})
    });
    let data;try{data=await response.json()}catch{data=null}
    return {status:response.status,data};
  },{path,method,body});
}
async function seed(){
  const existing=await api('/items');
  assert.equal(existing.status,200,'Library API');
  // Insert a short, clearly synthetic authored-note corpus even when the
  // earlier capture smoke already populated the disposable QA account. The
  // detail screenshot should display the Markdown editor, not an invalid URL.
  const samples=[
    {kind:'text',text:'# Hệ thống Kho Tri Thức\n\nLưu ghi chú, video và tài liệu nguồn trong một thư viện thống nhất.\n\n## Các bước\n- Thu thập thông tin\n- Xếp vào thư mục và gắn nhãn\n- Liên kết các ghi chú có liên quan\n- Tra cứu lại khi cần'},
    {kind:'text',text:'# Quản lý tư liệu học tập\n\nTổng hợp các video, bài học và trích dẫn có thể tìm kiếm.\n\n## Ghi nhớ\nGiữ nguyên nguồn, phân loại theo chủ đề, không làm mất lịch sử tiếp nhận.'},
    {kind:'text',text:'# Quy trình nghiên cứu\n\nTài liệu, nguồn web và video được theo dõi cùng một mã mục.\n\n- Ghi chú chính\n- Tài liệu tham khảo\n- Mối liên hệ và cây cha–con'}
  ];
  let id=null;
  for(const payload of samples){
    const v=await api('/captures','POST',payload);
    assert.equal(v.status,201,'Create synthetic note');id??=v.data?.item_id;
  }
  return id;
}
try{
  requireQA();
  mkdirSync(out,{recursive:true});
  const health=await fetch(ORIGIN+'/api/v1/health',{signal:AbortSignal.timeout(5000)});
  assert.equal(health.status,200,'Isolated QA backend health');
  browser=await Browser.launch({binary:process.env.KT_JOURNEY_CHROMIUM||'chromium'});
  page=await browser.newPage({width:1440,height:900,reducedMotion:true});
  await page.goto(ORIGIN);
  await wait(()=>!!document.querySelector('input[autocomplete="username"]'),undefined,'login form');
  const fill=async(sel,text)=>{
    const ok=await page.eval(s=>{const field=document.querySelector(s);if(!field)return false;field.focus();field.select?.();return true;},sel);
    assert.ok(ok,'Missing input '+sel);
    await page.send('Input.insertText',{text});
  };
  await fill('input[autocomplete="username"]',process.env.KT_PREVIEW_USER);
  await fill('input[autocomplete="current-password"]',process.env.KT_PREVIEW_PASSWORD);
  await page.eval(()=>[...document.querySelectorAll('button')].find(x=>x.textContent.trim()==='Đăng nhập')?.click());
  await wait(()=>!!document.querySelector('.capture-compose'),undefined,'logged in');
  const session=await api('/session');
  assert.equal(session.data.username,process.env.KT_PREVIEW_USER,'QA account');
  const first=await seed();
  assert.ok(first,'Synthetic note was not saved');
  await gotoHash('#/thu-vien','.knowledge-library-layout');
  await screenshot('01-thu-vien-desktop.png',1440,900);
  await page.setViewport({width:390,height:844});
  await wait(() => {
    const button=document.querySelector('.library-tree-toggle');
    const body=document.querySelector('.library-tree-content');
    return !!button && button.getAttribute('aria-expanded')==='false'
      && !!body && getComputedStyle(body).display==='none'
      && !!document.querySelector('.knowledge-library-content');
  },undefined,'mobile tree defaults collapsed and library remains visible');
  await screenshot('02-thu-vien-mobile.png',390,844);
  await gotoHash('#/gui','.capture-compose');
  await screenshot('03-gui-vao-kho-desktop.png',1440,900);
  await screenshot('04-gui-vao-kho-mobile.png',390,844);
  // Show the actual React paste/file queue on screen with a tiny synthetic
  // canvas image. This does NOT upload any file to the backend.
  await page.setViewport({width:1440,height:900});
  await page.eval(async () => {
    const canvas=document.createElement('canvas');
    canvas.width=320;canvas.height=180;
    const ctx=canvas.getContext('2d');
    if (!ctx) throw Error('No 2D canvas context');
    ctx.fillStyle='#e3f0fa';ctx.fillRect(0,0,320,180);
    ctx.fillStyle='#a3bdca';ctx.fillRect(0,115,320,65);
    ctx.fillStyle='#477b73';ctx.beginPath();ctx.moveTo(0,142);ctx.lineTo(120,48);ctx.lineTo(195,125);ctx.lineTo(265,65);ctx.lineTo(320,125);ctx.lineTo(320,180);ctx.lineTo(0,180);ctx.fill();
    ctx.fillStyle='#154f5d';ctx.font='bold 22px sans-serif';ctx.fillText('Ảnh mẫu (QA)',75,34);
    const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));
    if (!blob) throw Error('Could not encode synthetic image');
    const file=new File([blob],'anh-mau-qa.png',{type:'image/png'});
    const transfer=new DataTransfer();transfer.items.add(file);
    const chooser=document.querySelector('.capture-file-input');
    chooser.files=transfer.files;
    chooser.dispatchEvent(new Event('change',{bubbles:true}));
  });
  await wait(()=>!!document.querySelector('.capture-file-preview') && document.body.textContent.includes('anh-mau-qa.png'),
    undefined,'real React image attachment preview');
  await screenshot('08-gui-anh-mau-desktop.png',1440,900);
  await gotoHash('#/muc/'+first,'.detail-view');
  await screenshot('05-chi-tiet-ghi-chu-desktop.png',1440,900);
  await gotoHash('#/cai-dat','.settings-row');
  await screenshot('06-cai-dat-desktop.png',1440,900);
  await gotoHash('#/thu-vien','.knowledge-library-layout');
  await screenshot('07-thu-vien-tablet.png',768,1024);
  evidence.status='PASS';
  console.log('UI_PREVIEW_PASS '+evidence.files.length+' real screenshots');
}catch(error){
  evidence.status='FAIL';
  evidence.errors.push(String(error.message||error).slice(0,320).replace(/https?:\/\/\S+/g,'[URL]'));
  console.error('UI_PREVIEW_FAIL '+evidence.errors[0]);
  process.exitCode=1;
}finally{
  mkdirSync(out,{recursive:true});
  writeFileSync(resolve(out,'preview-evidence.json'),JSON.stringify(evidence,null,2)+'\n');
  try{await browser?.close()}catch{}
}
