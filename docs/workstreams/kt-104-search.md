# KT-104 — SearchService

- Baseline mã nguồn `c51d39f3d3719a03760944145e9cf22b15c30cc6` từ `codex/kt-003-005-drive`. Nhánh `codex/kt-104-search`.
- Phạm vi `apps/backend/search/**` và checkpoint này. Django app, hai chỉ mục GIN theo bảng cho FTS tiếng Việt, fallback pg_trgm cho số hiệu, phạm vi owner/nhóm và truy vấn riêng cho chú thích lượt gửi.
- Kiểm thử **NOT_RUN**. Chưa có mã KT-104.
- Tiếp theo kiểm tra model/migration tại baseline, triển khai và chạy test trên PostgreSQL tạm với settings riêng.
