# KT-103 và KT-110

Nhánh `codex/kt-103-110-organization` bắt đầu từ `c51d39f3d3719a03760944145e9cf22b15c30cc6` trên `codex/kt-003-005-drive`.

## Mốc 1 · Baseline

- Mã nguồn: `c51d39f3d3719a03760944145e9cf22b15c30cc6`. Test nhánh: **NOT_RUN**. Đã đọc hợp đồng v4.7 tại SHA này và đối chiếu schema Item, taxonomy, Assignment, RelatedItem, DerivedContent.
- Mục tiêu: tự gán nhóm hiện có có chứng cứ, bảo toàn nhóm manual/pinned, nối Item theo cặp canonical và xử lý stale.
- Phạm vi: `catalog/organization.py`, `catalog/test_organization.py` và module con của organization nếu cần.
- Còn thiếu: service và test PostgreSQL, adapter KT-104 lúc tích hợp, eval KT-107 cho ngưỡng sản xuất. Bước tiếp theo là triển khai rule có bằng chứng và candidate provider có thể tiêm.
