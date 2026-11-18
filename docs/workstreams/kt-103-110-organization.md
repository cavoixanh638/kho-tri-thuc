# KT-103 và KT-110

Nhánh `codex/kt-103-110-organization` bắt đầu từ `c51d39f3d3719a03760944145e9cf22b15c30cc6` trên `codex/kt-003-005-drive`.

## Mốc 1 · Baseline

- Mã nguồn: `c51d39f3d3719a03760944145e9cf22b15c30cc6`. Test nhánh: **NOT_RUN**. Đã đọc hợp đồng v4.7 tại SHA này và đối chiếu schema Item, taxonomy, Assignment, RelatedItem, DerivedContent.
- Mục tiêu: tự gán nhóm hiện có có chứng cứ, bảo toàn nhóm manual/pinned, nối Item theo cặp canonical và xử lý stale.
- Phạm vi: `catalog/organization.py`, `catalog/test_organization.py` và module con của organization nếu cần.
- Còn thiếu: service và test PostgreSQL, adapter KT-104 lúc tích hợp, eval KT-107 cho ngưỡng sản xuất. Bước tiếp theo là triển khai rule có bằng chứng và candidate provider có thể tiêm.

## Mốc 2 · Service và vòng CI đầu

- Mã nguồn vòng đầu: `7f31970fcbf856d73c460c8b470b951da06f6fd8`. Python biên dịch 3 tệp và kiểm quy tắc thuần bằng fixture: **PASS**.
- PostgreSQL: **FAIL** ở [Actions #44329614763](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44329614763), lệnh `docker compose exec -T api python manage.py test`. Chạy 29 test, 5 lỗi do `get_or_create` cần tham số `item` khi chèn Assignment.
- Bước tiếp theo: ghi rõ FK khi chèn và xác minh lại toàn bộ CI. Adapter KT-104 và eval KT-107 còn chờ tích hợp.

## Mốc 3 · PostgreSQL và bàn giao

- Mã nguồn: `26a29e514b7fd92f44106a076e400ab4070e93d1`. **PASS 29/29** tại [Actions #44330068306](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44330068306) trên Ubuntu/Docker Compose/PostgreSQL 18, merge thử `08200cede106b160e2c2e43513da19991fc6ebab`. Lệnh `docker compose exec -T api python manage.py test`. Django check, kiểm tra migration, rollback/reapply và smoke worker/API/web cũng PASS.
- Test fixture bao phủ N06, N09–N12, N16–N17, cách ly tài khoản và rollback khi provider lỗi. Với cặp đồng nghĩa không chung từ của N17, fixture truy hồi 0/1 ứng viên. Candidate recall của KT-104 và eval 30–50 mục của KT-107: **NOT_RUN**.
- [PR #7](https://github.com/cavoixanh638/kho-tri-thuc/pull/7). Điều phối gọi `OrganizationService(candidate_provider=..., similarity=...).organize(item_id)` từ worker sau khi ghi nội dung mới. Provider cục bộ nhận `(Item, tuple[str, ...])` với các trường text hiện hành và trả iterable UUID. Điền `LexicalSimilarity` khi dùng RelatedItem. Đọc các cặp `active` cho Chi tiết.
- Project yêu cầu một dòng `Dự án: <tên>` hoặc `Project: <tên>` trong `Item.note`. Topic/Tag một từ yêu cầu khai báo tương ứng. Điểm gán nhóm 1.0 biểu thị khớp rule. Hai ngưỡng similarity trong test chỉ dùng cho fixture. `classification_status` ghi kết quả tự động, còn bộ lọc Chưa phân loại trong Thư viện cần dựa vào các quan hệ nhóm thực tế, kể cả manual.
- Tiếp theo: nối KT-104 và worker ở nhánh điều phối, chạy eval KT-107 trước khi chốt ngưỡng sản xuất. Có thể revert mã sau tích hợp. Các quan hệ đã ghi cần được rà riêng nếu rollback sau khi bật job.
