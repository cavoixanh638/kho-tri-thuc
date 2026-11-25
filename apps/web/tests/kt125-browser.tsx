import { createRoot } from 'react-dom/client';
import { useEffect, useState } from 'react';
import { MantineProvider } from '@mantine/core';
import '@mantine/core/styles.css';
import '../src/styles.css';
import { SavedCollectionsPanel, SavedCollectionScreen, collectionIdFromHash } from '../src/SavedCollections';
import './kt125-browser.css';

function Fixture() {
  const [csrf, setCsrf] = useState('');
  const [id, setId] = useState(() => collectionIdFromHash(location.hash) ?? 'new');
  useEffect(() => { void fetch('/api/v1/session').then((result) => result.json()).then((value) => setCsrf(value.csrf_token)); }, []);
  useEffect(() => { const change = () => setId(collectionIdFromHash(location.hash) ?? 'new'); window.addEventListener('hashchange', change); return () => window.removeEventListener('hashchange', change); }, []);
  return <><header className="site-header"><div className="shell header-inner"><strong>Kho Tri Thức · QA bộ sưu tập</strong></div></header>
    <main className="shell canvas"><div className="page-title"><h1>Bộ sưu tập thông minh</h1></div>
      <div className="kt125-fixture-layout"><aside className="panel"><SavedCollectionsPanel /></aside>
      {csrf && <SavedCollectionScreen key={id} id={id} csrf={csrf} />}</div>
    </main></>;
}
createRoot(document.getElementById('root')!).render(<MantineProvider forceColorScheme="light"><Fixture /></MantineProvider>);
