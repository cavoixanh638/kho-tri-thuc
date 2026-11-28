import { createRoot } from 'react-dom/client';
import { MantineProvider } from '@mantine/core';
import '@mantine/core/styles.css';
import '../src/styles.css';
import { LibraryScreen } from '../src/LibraryScreen';
import type { Item } from '../src/api';
const rows:Item[]=Array.from({length:101},(_,i)=>({item_id:`00000000-0000-4000-8000-${String(i).padStart(12,'0')}`,kind:'text',title:['Giao dịch và tác vụ nền','Sách và chương trong cây thư viện','Ghi nhớ tiếng Việt nguyên văn'][i%3]+' '+i,note:'Nội dung thử riêng cho giao diện. Bài văn bản và nguồn minh họa giữ cùng định danh khi đổi cách xem.',description:'',saved_at:'2026-11-19T23:00:00Z',published_at:null,updated_at:'2026-11-20T00:00:00Z',favorite:i%2===0,deleted:false,classification_status:'user_assigned',original_url:'',source_fetch:'not_applicable',asset_storage:'not_applicable',content_extract:'not_available',assets:[]}));
window.fetch=async(input)=>{const url=new URL(String(input),location.origin);let data:unknown;if(url.pathname.endsWith('/knowledge-tree'))data={nodes:[]};else if(url.pathname.endsWith('/items')){const offset=Number(url.searchParams.get('offset')||0);const filtered=url.searchParams.get('favorite')==='true'?rows.filter(r=>r.favorite):rows;data={results:filtered.slice(offset,offset+50),next_offset:offset+50<filtered.length?offset+50:null};}else return new Response('{}',{status:404});return new Response(JSON.stringify(data),{status:200});};
createRoot(document.getElementById('root')!).render(<MantineProvider><header className="shell"><p><strong>Kho Tri Thức — KT118</strong> · Dữ liệu giao diện tổng hợp, không phải kho đang dùng</p></header><main className="shell"><LibraryScreen /></main></MantineProvider>);
