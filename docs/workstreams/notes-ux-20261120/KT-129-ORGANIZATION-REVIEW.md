# KT-129 — Organization Evidence, Triage & Auto-group Review

**Phân loại:** CORE UX CONDITIONAL. **Ngày lập:** 20/11/2026. **Trạng thái:** SPEC_READY / IMPLEMENTATION_NOT_RUN. **Nguồn:** [G00 traceability audit](G00-FEATURE-TRACEABILITY.md), PR #30–47, PR #57. Đây là đề xuất có thể giao, **không phải tính năng đã triển khai**.

**Nhiệm vụ:** biến `OrganizationService` có quy tắc gán nhóm thành UX minh bạch để người dùng hiểu/bảo vệ việc sắp xếp, học từ Lark/Coda/Tana/OneNote/Gemini Notebook.

- Trong Note và Inbox, hiển thị **Đang ở / Được hệ thống đề xuất / Người dùng cố định**; mỗi đề xuất có `candidate Topic/Tag/Project + source excerpt + processor/source version + confidence/method`. Chỉ auto-gán khi policy đủ rõ; người dùng có quyền `Áp dụng/Bỏ qua/Hoàn tác` và chốt pinned; không tự tạo nhiều nhóm mới.
- Giải thích tại sao Item được đưa vào folder và cách chuyển sang folder khác, kết hợp `home` của KT122 mà không ghi đè vị trí chính.
- Tự cập nhật quan hệ khi derived source stale nhưng không xóa manual/pinned assignment; đề xuất low-confidence ở queue có phân trang, không tạo task AI nền mới.
- **Acceptance:** 50 Item tiếng Việt gán nhãn chuẩn, báo `precision = correct_auto / audited_auto`, `coverage = auto_assigned / eligible_with_evidence`, `false_positive = wrong_auto / audited_auto`; mẫu số 0 = NOT_RUN. Test 0 pinned overrides, owner/access, 10k queue paging, no auto merge. Không thêm provider nếu chưa có permission/chi phí. **Base PR57**, phụ thuộc API/UX KT122.

**Bàn giao:** Mỗi agent đọc AGENTS.md, CURRENT_STATE.md, code HEAD và các PR đang mở, ghi Code SHA/Tested SHA, lệnh kiểm, PASS/FAIL/NOT_RUN, dependency, rollback; commit/push/PR riêng. Không merge hay deploy. Không được tự sửa hợp đồng data gốc, CURRENT_STATE đồng thời hoặc dữ liệu sản xuất.
