# KT-011 · Tiếp nhận và lịch sử

- Nhánh `codex/kt-011-capture` từ `c51d39f3d3719a03760944145e9cf22b15c30cc6`.
- Phạm vi gồm CaptureService, router đã xác thực và kiểm thử trong `apps/backend/ingestion/`.
- Tiêu chí gồm một giao dịch Event/Item/Source/Job, ACK sau commit, nội dung bản gốc và giờ bất biến, retry trả cùng Event, gửi lại URL chắc danh tính giữ Item riêng với Event, lịch sử cách ly theo chủ sở hữu.
- Trạng thái IN_PROGRESS. Tiếp theo triển khai và kiểm thử trên PostgreSQL 18.
