# KT-011 · Tiếp nhận và lịch sử

- Nhánh `codex/kt-011-capture` từ `c51d39f3d3719a03760944145e9cf22b15c30cc6`.
- Trạng thái PASS phạm vi luồng. SHA code đã thử `bb6bc1cd0c2593d987ca86bd1067cee2d8568466`. Root tích hợp router sau review.
- API dùng Django session và CSRF. Mount `ingestion.api.router` tại gốc Ninja `/api/v1`.
- `POST /captures` nhận `kind`, `url`, `text`, `source_channel`, `client_sent_at` và header tùy chọn `Idempotency-Key`. Trả 201 cho lượt mới, 200 cho retry, cùng cấu trúc `capture_id`, `item_id`, `received_at`, `state`.
- `GET /captures` và `GET /items/{item_id}/captures` trả `results` và `next_offset`. Bộ lọc có `limit`, `offset`, `received_from` bao gồm mốc, `received_before` loại mốc. Mốc lọc dùng ISO 8601 kèm múi giờ.
- Giao dịch gồm Event, Item, Source nếu có và Job cần thiết. Job `fetch_source` nhận `capture_id` dạng chuỗi UUID và `source_id` dạng số. Job `organize` nhận `capture_id`.
- PostgreSQL 18.4 tạm trên Windows, `manage.py test` PASS 31/31. Kiểm thử gồm Unicode/ngắt dòng, giờ server và input thiết bị, rollback khi insert Job lỗi, retry và hai ca gửi đồng thời, scope chủ sở hữu, session/CSRF và các URL private.
- `manage.py makemigrations --check --dry-run` PASS. Ruff format và lint E4/E7/E9/F/I PASS cho các tệp mới. Không có migration KT-011.
- Chưa thử tải nguồn hoặc Drive thật, backup/restore KT-008, tìm chú thích KT-104. Tiếp nhận kiểm URL cú pháp và địa chỉ IP/hostname private đã rõ; bước fetch kiểm địa chỉ DNS, kết nối và redirect.
- Hoàn tác bằng revert PR. Không cần đảo schema; dữ liệu lượt gửi đã nhận vẫn được giữ.
