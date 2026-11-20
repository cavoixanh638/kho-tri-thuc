# KT-118 — UX-P1: nhiều chế độ xem Thư viện trên một nguồn Item

**Trạng thái:** READY_TO_ASSIGN / NOT_RUN. Thực hiện sau khi bảo đảm Item/Tree/count không mất dữ liệu; có thể lập PoC với dữ liệu fixture độc lập.

## Baseline

`LibraryScreen.tsx` đã có cây, lọc `all/unclassified/favorite/deleted`, paging và danh sách. `Topic.parent`, `ItemTopic` hỗ trợ nhiều nhánh, một Item một ID. **Chưa có Bảng/Thẻ/Timeline native** trong màn này; không mở thêm database hoặc nhân bản Item.

## Yêu cầu

- Xây mode **List / Table / Card / Timeline** trong khu vực results; `Tree` vẫn là bộ lọc/điều hướng nhánh. Cùng một query/URL state và `Item.item_id` cho mọi mode; giữ favorite/deleted/unclassified, logic descendant và paging.
- Phân biệt `saved_at` (lần nhận đầu) với `published_at` (nguồn), nếu timeline cần chọn mốc thì ghi rõ ở UI. Không lấy ngày đăng làm ngày lưu.
- Tìm trong list và sort chỉ khi API có chứng cứ; không tạo fetch 10.000 bản ghi về browser để sort; nếu cần backend query, đề xuất contract/perf/index và test trước.
- Responsive Windows Full HD và Android, không có layout jump bất thường; keyboard/focus có thể dùng.

## Phạm vi file

- Sở hữu `apps/web/src/LibraryScreen.tsx`, component view mới `apps/web/src/LibraryViews*.tsx`, test `apps/web/tests/kt118-*.test.mjs`.
- Backend `catalog/api.py` chỉ sửa nếu chứng minh cần server-side pagination/sort; migration không mở khi không cần. Tránh sửa `KnowledgeTree.tsx`/ItemOrganization nếu luồng khác sở hữu. `styles.css` là file ghép G00.

## Acceptance

- Fixture **10.000 Item** ở DB test (nếu không có PostgreSQL, ghi giới hạn mock); một ID thuộc nhiều nhánh nhưng trong danh sách kết quả mỗi ID hiển thị đúng một lần.
- Cùng filter/scope, `set(list_ids) = set(table_ids) = set(card_ids) = set(timeline_ids)` sau khi đi hết các page, không đánh đồng 1 trang với toàn bộ; không tự đếm trùng khi Item nhiều nhánh.
- Không thay row count/Item ID/source/Drive mapping khi chuyển view; sort stable khi cùng timestamp.
- Test DOM + browser responsive nếu có; JSDOM **không đủ** để xác nhận CSS/layout; nêu viewport thật/NOT_RUN. PR gồm phép đo và rollback.
