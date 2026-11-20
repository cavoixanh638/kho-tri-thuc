import React from 'react';
import { createRoot } from 'react-dom/client';
import { SourceLocatorCitation } from '../src/SourceLocator';
import '../src/styles.css';
const root = createRoot(document.getElementById('root')!);
const fixture = { render(asset: { assetId: string; version: string; mime: string }, seconds: number) {
  root.render(<main className="shell canvas" style={{ maxWidth: 900 }}>
    <h1>Kho Tri Thức · Đọc nguồn</h1><p>Kiểm tra dữ liệu tổng hợp qua API riêng tư; không có tệp cá nhân hoặc kết nối Drive thật.</p>
    <section className="panel"><h2>Bản chép lời minh họa</h2><p>Đối chiếu đoạn văn với mốc nguồn đã chọn.</p>
      <SourceLocatorCitation key={`${asset.assetId}:${seconds}`} part={{ id: 1, kind: 'transcript', asset_id: asset.assetId,
        processor: 'synthetic-browser-fixture', locator: { start_seconds: seconds }, source: { state: 'current', version: asset.version,
          mime: asset.mime, asset_version: 1, source_id: null, source_url: null } }} />
    </section></main>);
} };
Object.assign(window, { ktPrivateViewer: fixture });
