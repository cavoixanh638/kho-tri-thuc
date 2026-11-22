#!/usr/bin/env node
/** P08/J6B media preflight: 3-page generated PDF + actual Chrome MP4 seek.
 * Explicitly NOT full J6B: Chrome PDF page rendering, private Drive and UI
 * attribution need independent verification. No network outside loopback.
 */
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { inflateSync } from 'node:zlib';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
assert.equal(process.env.KT_J6B_ISOLATED, 'YES');
assert.ok(process.env.KT_JOURNEY_CHROMIUM);
const { Browser } = await import(pathToFileURL(path.resolve('tools/smoke/p08_cdp.mjs')).href);
const out = path.resolve('tmp/p08-j6b-native');
mkdirSync(out, {recursive:true});
const temp = mkdtempSync(path.join(tmpdir(), 'kt-j6b-'));
const sha = b => createHash('sha256').update(b).digest('hex');
function makePdf() {
  const objects = [ '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>', null ];
  const pageIds = [];
  for (let index = 1; index <= 3; index++) {
    // Encode a distinctive full-page color on each page. The screenshot
    // classifier checks rendered pixels rather than trusting a #page fragment.
    const shade = index === 1 ? '0.9 0.08 0.08' : index === 2 ? '0.08 0.85 0.08' : '0.08 0.08 0.9';
    const stream = shade + ' rg 0 0 612 792 re f\n0 0 0 rg BT /F1 28 Tf 60 650 Td (P08 PDF PAGE ' + index + ') Tj ET';
    const len = Buffer.byteLength(stream, 'ascii');
    objects.push('<< /Length ' + len + ' >>\nstream\n' + stream + '\nendstream');
    const contentId = objects.length;
    objects.push('<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 1 0 R >> >> /Contents ' + contentId + ' 0 R >>');
    pageIds.push(objects.length);
  }
  objects[1] = '<< /Type /Pages /Kids [' + pageIds.map(i=>i+' 0 R').join(' ') + '] /Count 3 >>';
  objects.push('<< /Type /Catalog /Pages 2 0 R >>');
  let body = '%PDF-1.4\n';
  const offsets = [0];
  for (let i = 0; i < objects.length; i++) {
    offsets.push(Buffer.byteLength(body, 'ascii'));
    body += (i+1) + ' 0 obj\n' + objects[i] + '\nendobj\n';
  }
  const xref = Buffer.byteLength(body, 'ascii');
  body += 'xref\n0 ' + (objects.length+1) + '\n0000000000 65535 f \n';
  for (let i=1; i<offsets.length; i++) body += String(offsets[i]).padStart(10,'0') + ' 00000 n \n';
  body += 'trailer\n<< /Size ' + (objects.length+1) + ' /Root ' + objects.length + ' 0 R >>\nstartxref\n' + xref + '\n%%EOF\n';
  return Buffer.from(body, 'ascii');
}
// Decode native PNG scanlines using built-in zlib. This is a sampling oracle,
// never OCR: the generated PDF has large uniquely colored pages.
function countGreenRenderedPixels(png) {
  assert.equal(png.subarray(0,8).toString('hex'), '89504e470d0a1a0a');
  let offset=8, width=0, height=0, depth=0, type=0;
  const idat=[];
  while(offset+12<=png.length){
    const size=png.readUInt32BE(offset);const kind=png.toString('ascii',offset+4,offset+8);
    const bytes=png.subarray(offset+8,offset+8+size);offset+=size+12;
    if(kind==='IHDR'){width=bytes.readUInt32BE(0);height=bytes.readUInt32BE(4);depth=bytes[8];type=bytes[9];assert.equal(bytes[12],0,'interlaced PNG unsupported');}
    if(kind==='IDAT')idat.push(bytes);
    if(kind==='IEND')break;
  }
  assert.equal(depth,8);assert.ok(type===2||type===6);
  const channels=type===2?3:4,stride=width*channels,raw=inflateSync(Buffer.concat(idat));
  let cursor=0, previous=Buffer.alloc(stride),total=0,green=0,red=0,blue=0;
  for(let y=0;y<height;y++){
    const filter=raw[cursor++],current=Buffer.alloc(stride);
    for(let k=0;k<stride;k++){
      const value=raw[cursor++],left=k>=channels?current[k-channels]:0,up=previous[k],upLeft=k>=channels?previous[k-channels]:0;
      let predict=0;
      if(filter===1)predict=left;
      else if(filter===2)predict=up;
      else if(filter===3)predict=Math.floor((left+up)/2);
      else if(filter===4){const p=left+up-upLeft,a=Math.abs(p-left),b=Math.abs(p-up),c=Math.abs(p-upLeft);predict=a<=b&&a<=c?left:b<=c?up:upLeft;}
      else if(filter!==0)throw Error('UNSUPPORTED_PNG_FILTER');
      current[k]=(value+predict)&255;
    }
    // Inside the PDF document region, away from frame scrollbars and toolbar.
    if(y>=170&&y<490){for(let x=160;x<630&&x<width;x+=3){
      const k=x*channels,R=current[k],G=current[k+1],B=current[k+2];
      total++;if(G>R*1.8&&G>B*1.8&&G>90)green++;
      if(R>G*1.8&&R>B*1.8&&R>90)red++;
      if(B>G*1.8&&B>R*1.8&&B>90)blue++;
    }}
    previous=current;
  }
  return {green,red,blue,total,green_ratio:Number((green/Math.max(1,total)).toFixed(4))};
}
function serve(req,res,bytes,mime) {
  res.setHeader('Content-Type',mime);
  res.setHeader('Accept-Ranges','bytes');
  res.setHeader('Cache-Control','no-store');
  let start=0,end=bytes.length-1,status=200;
  if (req.headers.range) {
    const m = /^bytes=(\d+)-(\d*)$/.exec(req.headers.range);
    if(!m){res.writeHead(416);res.end();return;}
    start=Number(m[1]); if(m[2])end=Math.min(end,Number(m[2]));
    if(start>=bytes.length||start>end){res.writeHead(416);res.end();return;}
    status=206; res.setHeader('Content-Range','bytes '+start+'-'+end+'/'+bytes.length);
  }
  res.setHeader('Content-Length',String(end-start+1));
  res.writeHead(status);
  res.end(req.method==='HEAD'?undefined:bytes.subarray(start,end+1));
}
let server,browser;
const report = {
  task:'P08/J6B',scope:'NATIVE_LOOPBACK_PREFLIGHT',status:'NOT_RUN',
  remote_network_calls:0,drive_calls:0,ai_calls:0,
  pdf_rendered_page_verified:false,private_django_viewer_verified:false,
  full_j6b_pass:false,mp4_seeks:[],
};
try {
  const mp4path=process.env.KT_J6B_MP4_PATH || path.join(temp,'fixture.mp4');
  if (!process.env.KT_J6B_MP4_PATH) {
    const ff=spawnSync('ffmpeg',['-nostdin','-hide_banner','-loglevel','error','-f','lavfi','-i','testsrc=size=320x180:rate=15','-t','12','-an','-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p','-movflags','+faststart','-y',mp4path],{timeout:60000,encoding:'utf8'});
    assert.equal(ff.status,0,'FFMPEG_MP4_GENERATION_FAILED '+String(ff.error?.code||ff.stderr).slice(0,200));
  }
  const mp4=readFileSync(mp4path),pdf=makePdf();
  if(process.env.KT_J6B_PDF_OUT) writeFileSync(process.env.KT_J6B_PDF_OUT,pdf,{mode:0o600});
  assert.ok(mp4.length>10000&&pdf.length>500);
  report.fixture={mp4_sha256:sha(mp4),pdf_sha256:sha(pdf),pdf_pages:3,mp4_duration_seconds:12};
  const html='<!doctype html><html><body><h1>J6B fixture</h1><iframe width="720" height="560" src="/fixture.pdf#page=2"></iframe><video src="/fixture.mp4" controls muted preload="auto" width="320" height="180"></video></body></html>';
  const requests=[];
  server=createServer((req,res)=>{
    const uri = req.url || '/';
    requests.push(uri.split('?')[0].split('#')[0]);
    if(uri.startsWith('/fixture.pdf'))return serve(req,res,pdf,'application/pdf');
    if(uri.startsWith('/fixture.mp4'))return serve(req,res,mp4,'video/mp4');
    if(uri==='/')return serve(req,res,Buffer.from(html),'text/html; charset=utf-8');
    res.writeHead(404);res.end();
  });
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  const origin='http://127.0.0.1:'+server.address().port;
  browser=await Browser.launch({width:1440,height:960});
  const page=await browser.newPage({width:1440,height:960});
  await page.goto(origin+'/',{settleMs:1000});
  const urls=await page.eval(()=>({
    page:new URL(document.querySelector('iframe').src).hash,
    pdf:new URL(document.querySelector('iframe').src).pathname,
    video:new URL(document.querySelector('video').src).pathname,
  }));
  assert.deepEqual(urls,{page:'#page=2',pdf:'/fixture.pdf',video:'/fixture.mp4'});
  for(const target of [.5,2.5,6.25,9.5]) {
    const result=await page.eval(async seconds=>{
      const video=document.querySelector('video');
      if(video.readyState<1)await new Promise((resolve,reject)=>{
        const timer=setTimeout(()=>reject(Error('metadata_timeout')),15000);
        video.addEventListener('loadedmetadata',()=>{clearTimeout(timer);resolve();},{once:true});
        video.addEventListener('error',()=>{clearTimeout(timer);reject(Error('decode_error'));},{once:true});
      });
      if(video.duration<11.9||video.duration>12.2)throw Error('wrong_duration');
      await new Promise((resolve,reject)=>{
        const timer=setTimeout(()=>reject(Error('seek_timeout')),12000);
        video.addEventListener('seeked',()=>{clearTimeout(timer);resolve();},{once:true});
        video.currentTime=seconds;
      });
      return {time:video.currentTime,duration:video.duration,width:video.videoWidth,height:video.videoHeight,seekable:video.seekable.length};
    },target);
    assert.ok(Math.abs(result.time-target)<=.25);
    assert.equal(result.width,320);assert.equal(result.height,180);
    report.mp4_seeks.push({target_seconds:target,actual_seconds:result.time,error_seconds:Math.abs(result.time-target)});
  }
  assert.ok(requests.includes('/fixture.pdf')&&requests.includes('/fixture.mp4'));
  // A rendered-color check is stronger than inspecting iframe.src. Capture
  // multiple frames to allow Chrome's PDF extension to finish first paint.
  const screenshot=path.join(out,'pdf-page2-and-mp4.png');
  let observed={green_ratio:0};
  for(let attempt=0;attempt<7;attempt++){
    await new Promise(resolve=>setTimeout(resolve,500));
    await page.screenshot({path:screenshot,format:'png'});
    observed=countGreenRenderedPixels(readFileSync(screenshot));
    if(observed.green_ratio>=0.04)break;
  }
  report.pdf_visual_color_observation=observed;
  report.pdf_rendered_page_verified=observed.green_ratio>=0.04 && observed.green>observed.red*5 && observed.green>observed.blue*5;
  report.status=report.pdf_rendered_page_verified?'PREFLIGHT_PASS_CHROMIUM_PDF_PAGE2_MP4_NATIVE':'PREFLIGHT_PASS_NATIVE_MP4_PDF_FRAGMENT_ONLY';
  report.pdf_fragment_requested=true;
  report.mp4_max_error_seconds=Math.max(...report.mp4_seeks.map(x=>x.error_seconds));
  report.browser_requests=requests.length;
  report.pdf_page_manual_check=report.pdf_rendered_page_verified?'AUTOMATED_COLOR_PAGE2_ONLY':'NOT_RUN';
  report.private_asset_ownership='NOT_RUN';
  writeFileSync(path.join(out,'results.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({status:report.status,mp4_seek_count:report.mp4_seeks.length,max_error_seconds:report.mp4_max_error_seconds,full_j6b_pass:false}));
} finally {
  await browser?.close();
  if(server)await new Promise(resolve=>server.close(resolve));
  rmSync(temp,{recursive:true,force:true});
}
