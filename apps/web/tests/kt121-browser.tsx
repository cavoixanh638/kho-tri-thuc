import { useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { createTheme, MantineProvider, Button } from '@mantine/core';
import '@mantine/core/styles.css';
import '../src/styles.css';
import { NoteTemplatePicker } from '../src/NoteTemplatePicker';
import { acceptNoteTemplate } from '../src/NoteTemplateConfig';
import './kt121-browser.css';

const original = '# Ghi chép nghiên cứu\r\n\r\nBản nháp tiếng Việt Tiếng 🧑‍🚀 được giữ nguyên.  ';
const fixture = { applications: 0, reject: false, original };
Object.assign(window, { kt121: fixture });
function Demo() {
  const [note, setNote] = useState(() => sessionStorage.getItem('kt121-fixture') ?? original);
  const draft = useRef(note);
  const [saved, setSaved] = useState(false);
  return <>
    <header className="site-header"><div className="shell header-inner"><span className="brand">Kho Tri Thức · Kiểm thử KT-121</span></div></header>
    <main className="shell canvas">
      <div className="page-title"><h1>Mẫu cho bản nháp</h1><p>Chọn một cấu trúc ghi chép, giữ nguyên phần bạn đã viết.</p></div>
      <div className="kt121-fixture-grid">
        <div className="panel"><NoteTemplatePicker note={note} onApply={(proposal) => {
          const next = acceptNoteTemplate(draft.current, proposal);
          if (fixture.reject || next === undefined) return false;
          draft.current = next; setNote(next); setSaved(false); fixture.applications++; return true;
        }} /></div>
        <section className="panel kt121-fixture-draft" aria-labelledby="draft-heading">
          <h2 id="draft-heading">Bản nháp tổng hợp</h2>
          <label htmlFor="fixture-note">Markdown hiện có</label>
          <textarea id="fixture-note" value={note} rows={18} onChange={(event) => { draft.current = event.currentTarget.value; setNote(draft.current); setSaved(false); }} />
          <Button variant="default" onClick={() => { sessionStorage.setItem('kt121-fixture', draft.current); setSaved(true); }}>Lưu vào phiên kiểm thử</Button>
          {saved && <p role="status">Đã lưu fixture trong tab này.</p>}
        </section>
      </div>
    </main>
  </>;
}
const theme = createTheme({ fontFamily: 'Geist, system-ui, sans-serif', primaryColor: 'dark', primaryShade: 9, defaultRadius: 6 });
createRoot(document.getElementById('root')!).render(<MantineProvider theme={theme} forceColorScheme="light"><Demo /></MantineProvider>);
if (new URL(location.href).searchParams.get('preview') === 'book') {
  const timer = window.setInterval(() => {
    const choice = [...document.querySelectorAll('.note-template-options button')].find((button) => button.querySelector('strong')?.textContent === 'Sách / Chương');
    if (choice) { window.clearInterval(timer); (choice as HTMLButtonElement).click(); }
  }, 50);
}
