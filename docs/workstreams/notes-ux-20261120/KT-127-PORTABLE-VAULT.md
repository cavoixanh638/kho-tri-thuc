# KT-127 — Portable Markdown Vault & Roundtrip

**Phân loại:** CORE DATA + UX HIGH. **Ngày lập:** 20/11/2026. **Trạng thái:** SPEC_READY / IMPLEMENTATION_NOT_RUN. **Nguồn:** [G00 traceability audit](G00-FEATURE-TRACEABILITY.md), PR #30–47, PR #57. Đây là đề xuất có thể giao, **không phải tính năng đã triển khai**.

**Nhiệm vụ:** Khả năng di chuyển toàn bộ ghi chú giữa Kho Tri Thức và Obsidian/editor khác mà không phụ thuộc app. Hiện `KnowledgeExportPanel` xuất một Item và backup PG/Drive có manifest, **chưa có vault dạng folder–notes–links và import đối ứng**.

1. Export folder hierarchy + note Markdown UTF-8 theo cấu trúc dễ hiểu, frontmatter tối thiểu với `item_id, version, source reference, saved_at, published_at`, manifest JSON kiểm hash/ItemTopic M:N (home vs shortcut), directed Item hierarchy KT123, backlinks, asset mapping UUID, CaptureEvent history **trong manifest riêng**, không nhét token/Drive signed URLs/PII vô ý.
2. Vì một note nhiều folder, chỉ xuất **một file Markdown canonical** và shortcut/manifest mapping; đừng tạo 3 nội dung có UUID khác. Path collisions, Unicode NFC/NFD, filename unsafe, headings and wiki links phải có policy rõ.
3. Import dưới dạng **dry-run preview**: new/update/conflict/missing asset/unknown version, xem before/after và lựa chọn bỏ qua; không overwrite `Item.note` khi DB version cao hơn; không tạo duplicate Event trên retry, không tự tải media hàng trăm GB.
4. So sánh 2–3 định dạng Markdown phổ biến (standard links, wiki links, Obsidian frontmatter), chọn portable fallback. Import Obsidian vault **chỉ** đối với định dạng chứng minh được; không hứa plugin/theme/canvas sẽ giữ nguyên.
5. Tách snapshot portable khỏi `pg_dump`/Drive backup — không giả export Markdown là full disaster recovery; có báo cáo thiếu file hoặc không có quyền.

**Acceptance:** 100 Item Việt, 30 folder 5 tầng, Item ở 3 folder, directed parent edges, 200 wiki links, nhiều CaptureEvent, 5 media sample/locator; export/import DB test rỗng, `count/items/edges/sha` khớp phạm vi hỗ trợ, `unresolved=0` trên dữ liệu chuẩn. Fail cases có báo rõ. Không tạo production backup/data leak. Chạy migration/restore tests & report SHA. **Base PR57** và thích ứng sau KT122/123; PR riêng không merge/deploy.

**Bàn giao:** Mỗi agent đọc AGENTS.md, CURRENT_STATE.md, code HEAD và các PR đang mở, ghi Code SHA/Tested SHA, lệnh kiểm, PASS/FAIL/NOT_RUN, dependency, rollback; commit/push/PR riêng. Không merge hay deploy. Không được tự sửa hợp đồng data gốc, CURRENT_STATE đồng thời hoặc dữ liệu sản xuất.
