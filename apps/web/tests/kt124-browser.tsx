import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { MantineProvider } from '@mantine/core';
import '@mantine/core/styles.css';
import '../src/styles.css';
import { MarkdownEditor } from '../src/MarkdownEditor';
import { KnowledgeText } from '../src/KnowledgeText';
import { KnowledgeCommandPalette, type KnowledgeCommand } from '../src/KnowledgeCommandPalette';
import { NoteLinkContext } from '../src/NoteLinkContext';
import { request } from '../src/api';
const fixture = { actions: [] as string[], note: '', itemId: '' };
Object.assign(window, { kt124: fixture });
function Screen() {
  const [note, setNote] = useState('');
  const [read, setRead] = useState(false);
  const [csrf, setCsrf] = useState('');
  const [title, setTitle] = useState('');
  useEffect(() => {
    const id = new URLSearchParams(location.search).get('item')!;
    fixture.itemId = id;
    void request<{ note: string; title: string }>('/items/' + id).then((item) => { setNote(item.note); fixture.note = item.note; setTitle(item.title); });
    void request<{ csrf_token: string }>('/session').then((data) => setCsrf(data.csrf_token));
  }, []);
  function update(value: string) { setNote(value); fixture.note = value; }
  return <><header className="site-header"><div className="shell header-inner"><span className="brand">Kho Tri Thức · Điều hướng QA</span></div></header>
    <main className="shell canvas">
      <h1>{title || 'Bài tri thức'}</h1>
      <KnowledgeCommandPalette currentItemId={fixture.itemId} onAction={(action: KnowledgeCommand) => fixture.actions.push(action)} />
      <section className="panel">
        <button type="button" id="toggle-reading" onClick={() => setRead((value) => !value)}>{read ? 'Soạn bài' : 'Đọc bài'}</button>
        <button type="button" id="save" onClick={() => void request('/items/' + fixture.itemId, { method: 'PATCH', csrf, body: { note } })}>Lưu bản QA</button>
        {read ? <KnowledgeText text={note} /> : <MarkdownEditor value={note} title={title} disabled={false} onChange={update} onSave={() => {}} onCompositionChange={() => {}} />}
      </section>
      <NoteLinkContext id={fixture.itemId} />
    </main>
  </>;
}
createRoot(document.getElementById('root')!).render(<MantineProvider forceColorScheme="light"><Screen /></MantineProvider>);
