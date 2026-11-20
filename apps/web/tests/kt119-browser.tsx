// Isolated Vite-only fixture. No backend, account, storage, AI or external fetch.
import '@mantine/core/styles.css';
import '../src/styles.css';
import { MantineProvider, createTheme } from '@mantine/core';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { RelatedSources } from '../src/RelatedSources';
import { connections, corpus } from './kt119-fixture';
import { PageTitle } from '../src/views';

window.fetch = async (input, options) => {
  if (String(input) !== `/api/v1/items/${corpus.target}/related` || (options?.method && options.method !== 'GET')) throw new Error('Fixture blocked request');
  return new Response(JSON.stringify(connections), { headers: { 'Content-Type': 'application/json' } });
};
createRoot(document.getElementById('root')!).render(<StrictMode><MantineProvider theme={createTheme({ fontFamily: 'Geist, system-ui, sans-serif', primaryColor: 'dark', primaryShade: 9, defaultRadius: 6 })} forceColorScheme="light">
  <header className="site-header"><div className="shell header-inner"><a className="brand" href="/tests/kt119-browser.html">Kho Tri Thức · KT-119 fixture</a></div></header>
  <main className="shell canvas"><PageTitle title="Liên hệ và nguồn" description="30 bài fixture cô lập: 15 backlinks trực tiếp, 10 liên quan, 5 cùng nhóm. Không có dữ liệu tài khoản thật." />
    <RelatedSources id={corpus.target} onOpenAsset={(id) => { document.documentElement.dataset.openedAsset = id; }} />
  </main>
</MantineProvider></StrictMode>);
