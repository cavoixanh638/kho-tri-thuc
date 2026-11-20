# KT-119 — UX-P1: backlinks, nội dung liên quan và thẻ nguồn có chứng cứ

**Trạng thái:** READY_TO_ASSIGN / NOT_RUN. **Không xây graph DB** và không tự chạy phân nhóm AI mới.

## Baseline

`ItemOrganization.tsx` đã có `RelatedItems` gọi `/items/:id/related`, trả `item_id/title/reason`; `RelatedItem` trong PostgreSQL giữ một cặp 2 item có reason/method_version/source_version. `Topic`/Tag/Project và curated pinned đã có. **Panel hiện hữu không phải đầy đủ backlinks từ mọi kiểu liên kết.**

## Công việc

- Hiện “Liên quan đến bài này” và “Bài này được nhắc từ” (chỉ nếu có link thật từ Markdown/Source hoặc API đã xác minh); không gắn nhãn backlink với kết quả lexical không có liên kết thực.
- Làm rõ nguồn/lý do/phiên bản/loại liên hệ (same group vs RelatedItem vs explicit link), chỉ mở đến item ID hợp lệ và cùng quyền user; cho phép báo/ẩn gợi ý sai không tự xóa curated.
- Thẻ nguồn nhỏ: URL gốc đã sanitize, asset/file trạng thái VERIFIED/MISSING/PENDING, derived text hiện có/thiếu, PDF page/timestamp chỉ nếu locator đủ. Tránh trùng Source/Asset khi một nguồn có nhiều phiên bản/tệp.
- Không tự merge hai note gần nghĩa, không ghi đè `user_pinned`, không xem related score là fact; nếu chưa có API inverse backlinks thì ghi chính xác “chưa hỗ trợ” hoặc PoC adapter với test.

## Quyền sửa

- `apps/web/src/ItemOrganization.tsx`, `apps/web/src/RelatedSources*.tsx`, `apps/web/tests/kt119-*.test.mjs`. Có thể mở rộng `catalog/groups_api.py` hoặc `catalog/api.py` cho dữ liệu related source khi cần, **không** thay đổi OrganizationService semantics.
- `ItemScreen.tsx` do KT-115 sở hữu; `KnowledgeReading.tsx` do KT-116 sở hữu. Tích hợp qua component/callback độc lập, G00 nối khi merge.
- Không sửa shared `styles.css`, `api.ts`, `ui-entry.tsx` nếu luồng khác đang chạy.

## Acceptance

- Fixture 30 Item, 15 explicit backlinks, 10 RelatedItem có reason/version, 5 cùng nhóm; **tính separate counts** theo loại và kiểm 100% liên kết dẫn đúng item/scope, không tự bịa nguồn.
- Nếu số mẫu = 0, accuracy = **NOT_RUN**, không ghi 100%; tôn trọng quyền owner/ID khác quyền không rò nội dung.
- Mỗi source card gắn đúng source/asset/version; không áp quan hệ giả “1 source = 1 asset”. Test read-only, permission, keyboard và viewport nhỏ; migration/AI ngoài không được ngầm bật.
