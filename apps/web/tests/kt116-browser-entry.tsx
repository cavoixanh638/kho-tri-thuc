import React from 'react';
import { MantineProvider, createTheme } from '@mantine/core';
import '@mantine/core/styles.css';
import { createRoot } from 'react-dom/client';
import { SourceLocatorCitation, type SourcePart, type SourceViewer } from '../src/SourceLocator';
import { locatorCases, materialize } from './kt116-fixtures.mjs';
import '../src/styles.css';

declare global { interface Window { kt116: { render: (seconds: number, mime?: string, version?: string) => void; ready: boolean; record: () => Promise<void> } } }
const root = createRoot(document.getElementById('root')!);
const part: SourcePart = { id: 100, kind: 'transcript', asset_id: 'fixture-a', processor: 'synthetic-fixture', processor_version: 'v1', locator: { start_seconds: 0 }, source: { state: 'current', version: 'synthetic-v1', source_id: null, source_url: null, mime: 'audio/wav', asset_version: 1 } };
const viewer: SourceViewer = { kind: 'media', assetId: 'fixture-a', version: 'synthetic-v1', assetVersion: 1, url: '/api/v1/assets/fixture-a/stream', rangeVerified: true };
window.kt116 = { ready: true, render(seconds, mime = 'audio/wav', version = 'synthetic-v1') {
  const assetId = mime.startsWith('video/') ? 'fixture-video' : 'fixture-a';
  root.render(<MantineProvider forceColorScheme="light" theme={createTheme({ fontFamily: 'Geist, system-ui, sans-serif', primaryColor: 'dark' })}><div className="shell canvas" style={{ maxWidth: 900 }}>
    <h1 style={{ fontSize: 24 }}>Kho Tri Thức · Đọc nguồn</h1><p>Fixture tổng hợp KT-116: kiểm tra mốc nguồn, quyền và phiên bản.</p>
    <section><h2 style={{ fontSize: 20 }}>Bản chép lời</h2><p>Đoạn trích tại mốc đã chọn trong file tổng hợp, không có dữ liệu cá nhân.</p>
      <SourceLocatorCitation key={`${seconds}:${mime}`} part={{ ...part, asset_id: assetId, locator: { start_seconds: seconds }, source: { ...part.source!, mime, version } }} viewer={{ ...viewer, assetId, url: `/api/v1/assets/${assetId}/stream`, version }} /></section>
    <section><h2 style={{ fontSize: 20 }}>Khi thiếu nguồn định vị</h2>
      {[locatorCases[0], locatorCases[23], locatorCases[20]].map((row, index) => { const fixture = materialize(row, index); return <SourceLocatorCitation key={index} part={fixture.part as SourcePart} />; })}
    </section><p>Đây là kiểm tra cô lập. Drive, PDF private và Android thật chưa được nghiệm thu ở đây.</p>
  </div></MantineProvider>);
}, async record() {
  const canvas = document.createElement('canvas'); canvas.width = 320; canvas.height = 180;
  const ctx = canvas.getContext('2d')!;
  const stream = canvas.captureStream(10);
  const recorder = new MediaRecorder(stream, { mimeType: 'video/webm;codecs=vp8', videoBitsPerSecond: 100000 });
  const chunks: BlobPart[] = []; recorder.ondataavailable = (event) => chunks.push(event.data);
  const finished = new Promise<void>((resolve) => { recorder.onstop = () => resolve(); });
  const started = performance.now();
  const timer = setInterval(() => { ctx.fillStyle = '#165e48'; ctx.fillRect(0, 0, 320, 180); ctx.fillStyle = '#fff'; ctx.font = '30px sans-serif'; ctx.fillText(((performance.now() - started) / 1000).toFixed(1) + ' s', 60, 95); }, 100);
  recorder.start(); await new Promise(resolve => setTimeout(resolve, 22000)); recorder.stop(); await finished;
  clearInterval(timer); stream.getTracks().forEach(track => track.stop());
  const response = await fetch('/kt116-fixture-video', { method: 'POST', body: new Blob(chunks, { type: recorder.mimeType }) });
  if (!response.ok) throw new Error('fixture upload failed');
} };
window.kt116.render(1.25);
