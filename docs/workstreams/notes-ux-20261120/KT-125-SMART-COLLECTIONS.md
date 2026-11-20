# KT-125 — Smart Collections, Saved Views & Properties

**Phân loại:** CORE UX HIGH. **Ngày lập:** 20/11/2026. **Trạng thái:** SPEC_READY / IMPLEMENTATION_NOT_RUN. **Nguồn:** [G00 traceability audit](G00-FEATURE-TRACEABILITY.md), PR #30–47, PR #57. Đây là đề xuất có thể giao, **không phải tính năng đã triển khai**.

**Nhiệm vụ:** những ưu điểm Notion/Coda/Tana/Apple Notes mà KT-118 List/Table/Card/Timeline **chưa cung cấp**. Đọc G00 traceability và code SearchScreen/LibraryViews/GroupEditor trong PR57.

1. **Lưu tìm kiếm** theo owner: tên, điều kiện q/any-all/exclude Topic/Tag/Project, ngày nhận vs ngày nguồn, trạng thái fetch/text, favorite và sort. Smart collection **chỉ lưu query**, Item thành viên cập nhật động, không copy Item/Asset, không sửa ItemTopic.
2. Sidebar folder tree phân biệt **thư mục thật (Topic)** và **bộ sưu tập thông minh (filter)** bằng icon/nhãn và quyền; saved view chọn Table/Card/List/Timeline và filter state sống qua reload. Phải có “Xem điều kiện”/sửa tên/xóa saved filter; không chấp nhận query DSL nguy hiểm do client tự đưa vào SQL.
3. **Metadata/property chips**: tác giả, ngày nguồn, source type, status, Topic/Tag/Project và user-defined fields theo loại bài nếu có nhu cầu; phân biệt **template Markdown KT121** với typed metadata cần schema/version thật. Đầu tiên làm read-only/chips từ field hiện có; nếu thêm typed props phải có ADR 2–3 schema choices và migration/rollback.
4. Giao diện Kanban/calendar/row inline action là optional pha sau, chỉ khi có nhu cầu thực chứng, không nhân hệ database kiểu Notion hoặc trigger workflow tùy ý.

**Acceptance:** fixture 10k Item + 100 nhóm, 5 saved searches, 2 user; mọi view cùng filter trả cùng `set(item_id)` qua pagination; thay tag/nội dung thì membership tự phản ánh. AND/OR/EXCLUDE/TimeZone test đúng 30 tổ hợp và xác minh `COUNT(DISTINCT item_id)`. 0 Item mới khi lưu/xóa collection; update preserved saved user groups. Đo query count/P95 nêu môi trường, mobile 390/768 và Windows 1920, keyboard & owner tests. **Base PR57**, PR độc lập, không merge/deploy.

**Bàn giao:** Mỗi agent đọc AGENTS.md, CURRENT_STATE.md, code HEAD và các PR đang mở, ghi Code SHA/Tested SHA, lệnh kiểm, PASS/FAIL/NOT_RUN, dependency, rollback; commit/push/PR riêng. Không merge hay deploy. Không được tự sửa hợp đồng data gốc, CURRENT_STATE đồng thời hoặc dữ liệu sản xuất.
