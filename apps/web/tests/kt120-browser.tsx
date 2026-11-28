import { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { AiSuggestionReview, type NoteSuggestion } from '../src/AiSuggestionReview';
const before='# Ghi chép tiếng Việt\r\nĐây là nội dung người dùng.\n';
const after=before+'\n> Đề xuất tổng hợp, cần người dùng duyệt.\n';
const suggestion:NoteSuggestion={item_id:'00000000-0000-4000-8000-000000000020',source_version:'fixture-v1',base_edit_version:0,before,after,receipt:'fixture-only',expires_in:900,provenance:{provider:'none',model:'none',method:'fixture',prompt_version:'not_run'}};
// All calls terminate in memory. This entry is never imported by the application.
window.fetch=async(input)=>{const path=String(input);const data=path.endsWith('/accept')?{note:after,edit_version:1,source_version:'fixture-v1',undo_receipt:'fixture-undo'}:path.endsWith('/undo')?{note:before,edit_version:2,source_version:'fixture-v1',undo_receipt:''}:{state:'rejected',writes:0};return new Response(JSON.stringify(data),{status:200});};
function Fixture(){const[note,setNote]=useState(before),[open,setOpen]=useState(true);return <main style={{fontFamily:'system-ui,sans-serif',maxWidth:1100,margin:'24px auto',padding:16}}><h1>Kho Tri Thức — duyệt đề xuất</h1><p>Fixture PoC. Không có AI provider hoặc dữ liệu đang dùng.</p>{open&&<AiSuggestionReview suggestion={suggestion} csrf="fixture" currentNote={note} onApplied={r=>setNote(r.note)} onClose={()=>setOpen(false)}/>}<h2>Bài hiện tại</h2><pre style={{whiteSpace:'pre-wrap'}}>{note}</pre></main>;}
createRoot(document.getElementById('root')!).render(<Fixture/>);
