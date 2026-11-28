/** Minimal dependency-free Chromium DevTools driver for isolated KT128 QA. */
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

class DevTools {
  constructor(ws) {
    this.ws = ws;
    this.nextId = 1;
    this.pending = new Map();
    ws.addEventListener('message', (event) => {
      let incoming;
      try { incoming = JSON.parse(event.data); } catch { return; }
      if (!incoming.id) return;
      const entry = this.pending.get(incoming.id);
      if (!entry) return;
      clearTimeout(entry.timer); this.pending.delete(incoming.id);
      if (incoming.error) entry.reject(Error(`${entry.method}: ${incoming.error.message}`));
      else entry.resolve(incoming.result ?? {});
    });
    const failAll = () => {
      for (const item of this.pending.values()) { clearTimeout(item.timer); item.reject(Error('Chromium CDP disconnected')); }
      this.pending.clear();
    };
    ws.addEventListener('close', failAll);
    ws.addEventListener('error', failAll);
  }
  send(method, params = {}, sessionId, timeout = 20000) {
    if (this.ws.readyState !== WebSocket.OPEN) return Promise.reject(Error('Chromium CDP not connected'));
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { this.pending.delete(id); reject(Error(`${method} timed out`)); }, timeout);
      this.pending.set(id, { resolve, reject, timer, method });
      this.ws.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }));
    });
  }
}

class Page {
  constructor(devtools, targetId, sessionId) { this.cdp = devtools; this.targetId = targetId; this.sessionId = sessionId; }
  send(method, params) { return this.cdp.send(method, params, this.sessionId); }
  async eval(fn, argument) {
    const expression = `(${fn.toString()})(${JSON.stringify(argument)})`;
    const response = await this.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true, userGesture: true });
    if (response.exceptionDetails) {
      const text = response.exceptionDetails.exception?.description || response.exceptionDetails.text || 'unknown';
      throw Error('Browser JS: ' + String(text).slice(0, 400));
    }
    return response.result?.value;
  }
  async goto(url) {
    const response = await this.send('Page.navigate', { url });
    if (response.errorText) throw Error('Browser navigation: ' + response.errorText);
    for (let i = 0; i < 100; i++) {
      if (await this.eval(() => document.readyState === 'complete')) return;
      await sleep(100);
    }
    throw Error('Browser navigation timed out');
  }
  async setViewport({ width, height }) {
    await this.send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false });
  }
  async screenshot({ path, format = 'png' }) {
    if (format !== 'png') throw Error('Screenshots must use PNG');
    const result = await this.send('Page.captureScreenshot', { format, captureBeyondViewport: false, fromSurface: true });
    writeFileSync(path, Buffer.from(result.data, 'base64'), { mode: 0o600 });
    return path;
  }
  async close() { await this.cdp.send('Target.closeTarget', { targetId: this.targetId }); }
}

export class Browser {
  constructor(child, dir, cdp) { this.child = child; this.dir = dir; this.cdp = cdp; }
  static async launch({ extraArgs = [], binary = process.env.KT_JOURNEY_CHROMIUM || 'chromium', startupTimeoutMs = 12000 } = {}) {
    const dir = mkdtempSync(join(tmpdir(), 'kt128-p08-chromium-'));
    let child;
    try {
      child = spawn(binary, [
        '--headless=new', '--no-sandbox', '--disable-dev-shm-usage', '--no-first-run',
        '--no-default-browser-check', '--no-proxy-server', '--disable-background-networking',
        '--remote-allow-origins=*', '--remote-debugging-port=0', `--user-data-dir=${dir}`,
        'about:blank', ...extraArgs,
      ], { stdio: ['ignore', 'ignore', 'pipe'], env: process.env });
      let output = '';
      const wsUrl = await new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(Error('Chromium launch timed out')), startupTimeoutMs);
        const finish = (fn, value) => { clearTimeout(timer); fn(value); };
        child.once('error', (error) => finish(reject, error));
        child.once('exit', (code) => finish(reject, Error(`Chromium exited ${code}`)));
        child.stderr.on('data', (data) => {
          output += String(data);
          const match = output.match(/DevTools listening on (ws:\/\/127\.0\.0\.1:\d+\/devtools\/browser\/[^\s]+)/);
          if (match) finish(resolve, match[1]);
          if (output.length > 8192) output = output.slice(-4096);
        });
      });
      const ws = new WebSocket(wsUrl);
      await new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(Error('Chromium CDP websocket timed out')), 8000);
        ws.addEventListener('open', () => { clearTimeout(timer); resolve(); }, { once: true });
        ws.addEventListener('error', () => { clearTimeout(timer); reject(Error('Chromium CDP websocket error')); }, { once: true });
      });
      return new Browser(child, dir, new DevTools(ws));
    } catch (error) {
      child?.kill('SIGKILL');
      rmSync(dir, { recursive: true, force: true, maxRetries: 8, retryDelay: 100 });
      throw error;
    }
  }
  async newPage({ width = 1440, height = 900, reducedMotion = true } = {}) {
    const { targetId } = await this.cdp.send('Target.createTarget', { url: 'about:blank' });
    const { sessionId } = await this.cdp.send('Target.attachToTarget', { targetId, flatten: true });
    const page = new Page(this.cdp, targetId, sessionId);
    await page.send('Page.enable');
    await page.send('Runtime.enable');
    await page.setViewport({ width, height });
    if (reducedMotion) await page.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
    return page;
  }
  async close() {
    try { await this.cdp.send('Browser.close', {}, undefined, 1000); } catch { /* cleanup below */ }
    this.cdp.ws.close();
    this.child.kill('SIGKILL');
    if (this.child.exitCode === null && this.child.signalCode === null) await Promise.race([new Promise((resolve) => this.child.once('exit', resolve)), sleep(2000)]);
    for (let attempt = 0; attempt < 12; attempt++) {
      try { rmSync(this.dir, { recursive: true, force: true, maxRetries: 3, retryDelay: 100 }); break; }
      catch (error) { if (attempt === 11) throw error; await sleep(200); }
    }
  }
}
