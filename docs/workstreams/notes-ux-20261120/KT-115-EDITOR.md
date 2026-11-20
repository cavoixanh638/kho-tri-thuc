# KT-115 — UX-P0: soạn thảo Markdown Live Preview (không thay lõi)

**Trạng thái:** READY_TO_ASSIGN / NOT_RUN. **Lý do:** `ItemScreen.tsx` hiện có Mantine `Textarea` để sửa `Item.note`; `KnowledgeText.tsx` là renderer đọc, **chưa có split editor hay Live Preview**.

## Quyết định và phạm vi

- So sánh **ít nhất 3 hướng** ở thời điểm triển khai: (A) Textarea hiện có **+ split preview cần xây** (baseline đơn giản), (B) CodeMirror 6, (C) một hướng ProseMirror/Tiptap/Milkdown. Trình bày lựa chọn theo tiếng Việt/Unikey/EVKey, Markdown GFM, tables, undo/redo, keyboard, dependency size, license, XSS, chi phí và khả năng giữ nguyên raw Markdown. **Không tự mặc định CodeMirror/Tiptap đã chốt**, không nhúng nguyên Obsidian/AFFiNE.
- PoC một màn: **Edit**, **Edit+Preview**, **Read**; hỗ trợ heading, list, table, links, code, trích dẫn và shortcut vừa phải. Cấu trúc raw `Item.note` **giữ nguyên** ngoài sửa chủ ý; React markdown renderer hiện tại tiếp tục sanitize HTML/URL như trước.
- Bảo vệ unsaved draft và luồng PATCH `/items/:id`, `user_edit_version`/conflict nếu có; kiểm đặt dấu Unikey/EVKey/composition, phím mũi tên, backspace, copy-paste, chữ tiếng Việt NFC/NFD, màn hình Windows 1920x1080 và Android; `prefers-reduced-motion` không bị lạm dụng animation.
- Không đổi schema, Drive export, CaptureEvent, Source/Asset, backend search/organization. Nếu cần API riêng phải lập proposal + test trước khi đụng file ngoài sở hữu.

## File sở hữu và phối hợp

- Sở hữu: `apps/web/src/ItemScreen.tsx`, file editor/toolbar mới `apps/web/src/MarkdownEditor*.tsx`, `apps/web/tests/kt115-*.test.mjs`.
- Chỉ đọc, **không tự chỉnh cùng luồng khác:** `KnowledgeText.tsx`, `api.ts`, `styles.css`, `ui.test.mjs`, `ui-entry.tsx`, `package.json`. Nếu cần CSS riêng thì tạo module/class riêng hoặc ghi yêu cầu ghép vào PR G00. Không dùng CDN/script bên thứ ba.
- Run `npm test`, `npm run build`, các test mới bằng `node --test ...`. Cài dependency chỉ khi có bảng so sánh license và size, lockfile được review; nếu chưa được phép, ưu tiên phương án A không thêm package.

## Acceptance

- **40/40** fixture Markdown có tiếng Việt, bảng, liên kết, mã, linebreak, ký tự Unicode/chữ đặc biệt: mở → sửa chủ ý → lưu → reload → so raw/HTML expected; `unexpected_changed_bytes = 0`.
- Với IME, không rơi ký tự ở backspace/undo/redo và không tự submit khi đang composition; kiểm phím tắt sử dụng bàn phím; bảo vệ XSS và URL nguy hiểm.
- Cả ba chế độ hiển thị không nhân bản Item/Asset/Drive, không đổi `CaptureEvent`; draft lỗi mạng không mất. Browser/thiết bị thật không có → **NOT_RUN**, không gọi jsdom là “Windows/Android PASS”.
- Code/tests/build/PR có **Code SHA, Tested SHA, PASS/FAIL/NOT_RUN** và phương án rollback editor mà không mất note.
