import { createRoot } from 'react-dom/client';
import { MantineProvider } from '@mantine/core';
import '@mantine/core/styles.css';
import '../src/styles.css';
import { ItemScreen } from '../src/ItemScreen';

// Local synthetic transport only. No API calls escape this fixture.
const item = { item_id: 'kt115-browser', kind: 'text', title: 'Ghi chép nghiên cứu tiếng Việt', description: '',
  note: '# Ghi chép nghiên cứu tiếng Việt\r\n\r\n## Ý chính\r\n\r\nGiữ **nguyên văn** khi biên soạn, đối chiếu nguồn trước khi lưu.\r\n\r\n- Nội dung do người dùng viết\r\n- Nguồn và media được giữ kèm\r\n\r\n| Nội dung | Trạng thái |\r\n| --- | --- |\r\n| Ghi chú | Đã đọc |\r\n\r\n> Kiểm tra lại nguồn.\r\n\r\n[Tài liệu công khai](https://example.org)\r\n\r\n```js\r\nconst triThuc = "nguyên văn";\r\n```',
  saved_at: '2026-11-20T00:00:00Z', updated_at: '2026-11-20T00:00:00Z', published_at: null, favorite: false, deleted: false,
  classification_status: 'unclassified', original_url: '', source_fetch: 'not_applicable', content_extract: 'done', asset_storage: 'not_applicable', assets: [] };
const fixture = { item, patches: [] as object[], failSave: false };
Object.assign(window, { kt115: fixture });
window.fetch = async (input, options) => {
  const path = String(input);
  if (path.endsWith('/items/kt115-browser')) {
    if (options?.method === 'PATCH') {
      if (fixture.failSave) return new Response('{}', { status: 503 });
      const patch = JSON.parse(String(options.body)); fixture.patches.push(patch); Object.assign(item, patch);
    }
    return Response.json(item);
  }
  if (path.includes('/organization')) return Response.json({ topics: [], projects: [], tags: [] });
  return Response.json({ results: [], next_offset: null });
};
createRoot(document.getElementById('root')!).render(<MantineProvider forceColorScheme="light">
  <header className="site-header"><div className="shell header-inner"><span className="brand">Kho Tri Thức · Kiểm thử KT-115</span></div></header>
  <main className="shell canvas"><ItemScreen id={item.item_id} csrf="synthetic-fixture" /></main>
</MantineProvider>);
const openEditor = window.setInterval(() => {
  const edit = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Chỉnh sửa');
  if (!edit) return;
  window.clearInterval(openEditor); edit.click();
  window.setTimeout(() => [...document.querySelectorAll('button')].find((button) => button.textContent === 'Soạn + Xem trước')?.click(), 50);
}, 50);
