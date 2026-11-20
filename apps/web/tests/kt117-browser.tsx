// Isolated Vite-only QA fixture. Every API request is intercepted in memory.
// This entry is absent from the production bundle and never contacts a backend.
import '@mantine/core/styles.css';
import '../src/styles.css';
import { MantineProvider, createTheme } from '@mantine/core';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { CaptureScreen } from '../src/CaptureScreen';

const receipts = new Map<string, object>();
const submissions: object[] = [];
const failureMode = new URL(location.href).searchParams.get('fixture') === 'failure';
let failed = false;
window.fetch = async (input, options) => {
  const path = String(input);
  let data: object;
  if (path === '/api/v1/session') data = { authenticated: true, username: 'KT117 fixture', csrf_token: 'fixture-only' };
  else if (options?.method === 'POST' && path === '/api/v1/captures') {
    submissions.push(JSON.parse(String(options.body)));
    if (failureMode && !failed) { failed = true; throw new TypeError('Fixture network failure'); }
    const key = new Headers(options.headers).get('Idempotency-Key')!;
    if (!receipts.has(key)) receipts.set(key, {
      capture_id: `00000000-0000-4000-8000-${String(receipts.size + 1).padStart(12, '0')}`,
      item_id: '00000000-0000-4000-8000-000000000002', received_at: new Date().toISOString(), state: 'received',
    });
    data = receipts.get(key)!;
  } else if (path.startsWith('/api/v1/captures?')) data = { results: [], next_offset: null };
  else throw new Error('Fixture blocked unexpected request: ' + path);
  document.documentElement.dataset.fixtureRequests = String(submissions.length);
  return new Response(JSON.stringify(data), { headers: { 'Content-Type': 'application/json' } });
};

createRoot(document.getElementById('root')!).render(<StrictMode>
  <MantineProvider theme={createTheme({ fontFamily: 'Geist, system-ui, sans-serif', primaryColor: 'dark', primaryShade: 9, defaultRadius: 6 })} forceColorScheme="light">
    <header className="site-header"><div className="shell header-inner"><a className="brand" href="/tests/kt117-browser.html">Kho Tri Thức · KT-117 fixture</a></div></header>
    <main className="shell canvas"><p role="note">Dữ liệu fixture cô lập. Không kết nối tài khoản, Drive hay cơ sở dữ liệu.</p><CaptureScreen csrf="fixture-only" /></main>
  </MantineProvider>
</StrictMode>);
