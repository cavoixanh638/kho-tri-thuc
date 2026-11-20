# KT-126 — Research Clipper, Quotes & Source Anchors

**Phân loại:** CORE UX HIGH. **Ngày lập:** 20/11/2026. **Trạng thái:** SPEC_READY / IMPLEMENTATION_NOT_RUN. **Nguồn:** [G00 traceability audit](G00-FEATURE-TRACEABILITY.md), PR #30–47, PR #57. Đây là đề xuất có thể giao, **không phải tính năng đã triển khai**.

**Nhiệm vụ:** ghép capture URL đã có thành luồng nghiên cứu nguồn theo Evernote/OneNote/Capacities/Heptabase/Lark, không tự thêm browser extension hoặc OCR/AI billable.

1. Từ web article/selection/public URL, hỗ trợ capture **Link / Article (chỉ nội dung server trích thực) / Selection** và “Gửi vào bài đang có”. Màn preview hiển thị raw quote/URL/page title/metadata **đã kiểm được** và trạng thái chưa fetch; khi không có quyền thì chỉ lưu link, không bịa nội dung hay vượt DRM.
2. Chọn đoạn văn web/PDF/transcript, lưu `source_id/asset_id/processor_version/source_version/quote_hash/locator` và đoạn trích vào annotation độc lập; giữ `Item.note` gốc không bị thay. Trích câu trong page gắn URL và text offset/hash có kiểm; PDF bám page/rect khi parser có, chỉ page khi chưa có rect; video time khi từ ASR thật. Source thay đổi phải STALE/MISSING, không tự mở nhầm.
3. Nút **“Lưu trích dẫn vào bài đang có”** tạo CaptureEvent/Source theo hợp đồng transaction hiện có, một note/Item ID được giữ; người dùng duyệt trước khi chèn quote vào raw Markdown. Tách “gắn link” đang có `SourceLinks` khỏi “đã trích đúng đoạn”.
4. Bảo vệ HTML/sanitizer, SSRF, auth, server quotas, bản quyền/robots/quyền truy cập, upload file lớn, cross-origin. Không đưa OAuth token vào URL.
5. Nguồn chỉ có metadata/transcript thiếu phải có label rõ; không trộn auto-extracted text với authored text.

**Acceptance:** 20 trang/selection công khai và 10 PDF; 30 quote anchors với ground-truth, 95% anchors tới đúng đoạn trên bản nguồn không đổi, stale báo chính xác, không đoán mốc. 10 gửi vào note cũ: UUID/note gốc/CaptureEvent đúng; 2 gửi mới là 2 Event, retry cùng key không tăng. Windows Chromium browser thật + source-mocked network test; Drive/PDF/Android NOT_RUN nếu không có. **Base PR57**, tách adapter riêng tránh xung đột KT-116/122.

**Bàn giao:** Mỗi agent đọc AGENTS.md, CURRENT_STATE.md, code HEAD và các PR đang mở, ghi Code SHA/Tested SHA, lệnh kiểm, PASS/FAIL/NOT_RUN, dependency, rollback; commit/push/PR riêng. Không merge hay deploy. Không được tự sửa hợp đồng data gốc, CURRENT_STATE đồng thời hoặc dữ liệu sản xuất.
