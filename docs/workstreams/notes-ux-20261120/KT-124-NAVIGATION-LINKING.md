# KT-124 — Navigation, Wiki Links & Outline

**Phân loại:** CORE UX HIGH. **Ngày lập:** 20/11/2026. **Trạng thái:** SPEC_READY / IMPLEMENTATION_NOT_RUN. **Nguồn:** [G00 traceability audit](G00-FEATURE-TRACEABILITY.md), PR #30–47, PR #57. Đây là đề xuất có thể giao, **không phải tính năng đã triển khai**.

**Nhiệm vụ:** trải nghiệm tìm và nối tri thức kiểu Obsidian/Reflect, không chỉ render Markdown. Phải đọc [ma trận G00](G00-FEATURE-TRACEABILITY.md), KT-122/123 và code PR #57 trước khi thiết kế.

1. Hỗ trợ chèn `[[Tên bài]]` bằng autocomplete khi gõ và keyboard; sau khi chọn phải giữ **UUID đích**, không chỉ title. Thiết kế AST/adapter không làm hỏng plain Markdown, code fences, escape; cân nhắc cú pháp `[label](#/bai/uuid)` đang có và chuyển đổi an toàn. Preview/rename/same-title/delete phải rõ.
2. Panel tách **Outgoing / Incoming backlinks / Unlinked mentions (chỉ gợi ý) / Related similar / Structural parent/child**; không tự suy mọi lần nhắc tên thành liên kết thực, không ghi đè user links. Tận dụng `groups_api.py:_inline_item_links` ở PR57; không dùng `RelatedItem` undirected làm directed parent.
3. Command palette `Ctrl+K` và UI mobile để tìm/mở Item, folder, các lệnh “Tạo note”, “Di chuyển”, “Gắn nguồn”, “Đi đến ngày”, có filter owner và quyền truy cập; Esc/Enter/Arrow, không chặn IME đang composition và không kích hoạt trong field đang gõ nếu xung đột.
4. Trong note dài, hiện **TOC H1–H6** có heading anchor ổn định theo nội dung, chống trùng Unicode tiêu đề; nhảy đến vị trí và heading collapse/expand optional không thay raw Markdown. TOC không phải Item hierarchy mới.
5. Bố cục 1920/1440/768/390, sidebar có thể đóng nhưng trạng thái hiện rõ, keyboard không mất focus; không xây graph DB.

**Tệp chính:** `MarkdownEditor.tsx`, `KnowledgeText.tsx`, `RelatedSources.tsx`, `ItemScreen.tsx`, `App.tsx`, `SearchScreen.tsx`; tạo adapter/tests riêng; phần giao nhau KT-122/123 phải ghép qua props/callback, không hai agent cùng sửa file. **Base:** HEAD PR57 chưa merge, PR mới target integration, không merge/deploy.

**Acceptance:** 100 notes/200 links, đổi tên và hai notes trùng tiêu đề vẫn mở đúng UUID; A→B và B backlink đúng; A chỉ nhắc chữ B phải là “unlinked”, không thêm edge. 30 Markdown Unicode/GFM với H1..H6, heading duplicate, link/xss, TOC không đổi raw. 20 lệnh palette trên 1920/390, keyboard/IME test thật nếu có. DB ownership/cross-user, soft-delete, export/restore; PASS/FAIL/NOT_RUN theo SHA. Không tuyên bố COMPLETE nếu chỉ có helper unit test.

**Bàn giao:** Mỗi agent đọc AGENTS.md, CURRENT_STATE.md, code HEAD và các PR đang mở, ghi Code SHA/Tested SHA, lệnh kiểm, PASS/FAIL/NOT_RUN, dependency, rollback; commit/push/PR riêng. Không merge hay deploy. Không được tự sửa hợp đồng data gốc, CURRENT_STATE đồng thời hoặc dữ liệu sản xuất.
