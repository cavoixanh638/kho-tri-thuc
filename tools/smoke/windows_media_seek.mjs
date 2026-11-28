import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const { Browser } = await import(pathToFileURL(resolve(process.argv[2], 'tools/smoke/p08_cdp.mjs')).href);
const { origin, url, cookie } = JSON.parse(readFileSync(0, 'utf8'));
if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(origin)) throw Error('Loopback origin required');
const browser = await Browser.launch();
try {
  const page = await browser.newPage({});
  await page.send('Network.enable');
  await page.send('Network.setCookie', {name:'sessionid',value:cookie,url:origin,httpOnly:true});
  await page.goto(origin + '/api/v1/health');
  const result = await page.eval(async url => {
    const media = document.createElement('video');
    const wait = event => new Promise((resolve,reject) => {
      const timer = setTimeout(() => reject(Error('Media timeout ' + event)), 20000);
      media.addEventListener(event, () => {clearTimeout(timer); resolve();}, {once:true});
      media.addEventListener('error', () => { clearTimeout(timer); reject(Error('Media decode')); }, {once:true});
    });
    const ready = wait('loadedmetadata');
    media.preload='auto'; media.muted=true; media.src=url;
    document.body.append(media);
    await ready;
    const seeks=[];
    for (const seconds of [2.5, 9.5]) {
      const settled = wait('seeked');
      const start = performance.now();
      media.currentTime=seconds;
      await settled;
      if (Math.abs(media.currentTime-seconds)>0.25) throw Error('Seek out of tolerance');
      seeks.push({target_s:seconds,actual_s:media.currentTime,elapsed_ms:Math.round(performance.now()-start)});
    }
    return {duration_s:media.duration,seeks};
  }, url);
  console.log(JSON.stringify(result));
} finally {
  await browser.close();
}
