# KT-120 — UX-P1 CONDITIONAL: AI đề xuất chỉnh sửa có diff/accept/reject

**Trạng thái: HOLD / KHÔNG TỰ TRIỂN KHAI** khi chưa có người dùng giao task rõ ràng và phê duyệt provider/giới hạn phí/phạm vi dữ liệu. Đây là **yêu cầu thiết kế**, không phải lệnh bật AI thương mại.

## Nguyên tắc thiết kế khi được giao

- `Item.note` do người dùng viết là nguồn có thẩm quyền; AI tạo **suggestion riêng** có `item_id`, `source_version`, `base_edit_version`, prompt/model/provenance, changes preview. G00/AGENTS phải đánh giá data retention/permission trước khi gọi provider.
- Màn hình so sánh before/after, diff, chấp nhận/từ chối/hủy/undo; AI **không bao giờ tự PATCH** bản gốc. Bảo vệ conflict nếu người dùng sửa bản gốc sau lúc gợi ý.
- Giữ offline/no-AI mode; không thêm vector DB, chatbot riêng, background agent/queue nhiều tầng. Có thể PoC chỉ bằng fake suggestion trong DB test để đo UX trước khi có provider thật.
- Báo cáo khi có lựa chọn model/chi phí mới: ít nhất **2–3 phương án** theo latency/privacy/giấy phép/đơn giá; không lấy beta dịch vụ làm GA.

## Acceptance khi được phép

- 20 fixture edit tiếng Việt: **0 thay đổi `Item.note` khi chỉ preview/reject**, chỉ sau accept đúng version mới sửa; 20/20 diff đúng và rollback giữ raw note/asset/event. Không có provider thật thì `PROVIDER_NOT_RUN`, không báo AI đã được tích hợp.
- Files: tạo module `apps/web/src/AiSuggestion*.tsx`, `apps/backend/processing/*suggestion*` khi được giao; không đụng shared ItemScreen/KnowledgeReading cho tới giai đoạn tích hợp. Ghi migration/test, source version và PR riêng.
