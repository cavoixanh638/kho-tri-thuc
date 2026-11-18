# Tải file gốc và xử lý bằng worker

**Trạng thái** Kiểm thử endpoint và worker đã qua trên nhánh riêng. Chờ gắn router, handler và volume vào ứng dụng tích hợp.
**Nhánh** `codex/kt-005-upload-api` · **Baseline** `f17a7992ca4fc464ed5d3041945bcdfb0fd880f4` · **Mã đã thử** `858698ae81369e8b22909d646a8ed250743e690c`

- `POST /api/v1/uploads` nhận multipart `file` và tùy chọn `Idempotency-Key`. Yêu cầu session Django và CSRF. Trả 201 khi tạo mới, 200 khi replay cùng key trong phạm vi owner. Cả hai trả `{item_id, asset_id, state}`; `state` là trạng thái Job hiện tại.
- Kiểm tra kích thước 128 MiB trước khi ghi bản ghi. Ghi file theo UUID của Asset trong thư mục staging, tính SHA-256 và đồng bộ file trước transaction ngắn tạo Item, Asset và Job. Tên tải lên chỉ dùng làm metadata.
- Worker xử lý kind `upload_asset`. Lỗi tạm thời giữ file staging để retry. Sau khi StorageLocation đã xác minh, worker có thể dọn staging ở lần sau mà vẫn dùng đúng ID file Drive ban đầu.

## Bàn giao

- Gắn `storage.uploads.router` ở prefix `/uploads` của Ninja API v1.
- Đặt `jobs.handlers.HANDLERS["upload_asset"] = storage.upload_job.upload_asset`.
- Cấu hình `UPLOAD_STAGING_ROOT` với đường dẫn tuyệt đối trên một volume chia sẻ giữa API và worker, dùng cùng quyền ghi. Chỉ dọn file của job sau khi xác minh hoặc theo quy trình vận hành có đối chiếu DB. Một process chết trước commit có thể để lại file staging chưa có bản ghi.
- Receipt upload file dùng Item/Asset/Job. Lịch sử gửi URL/ghi chú tiếp tục đi qua CaptureEvent. Mở Drive thật cần tích hợp OAuth và xác minh trong môi trường thử có tài khoản.

## Bằng chứng

- PostgreSQL 18.4 trên Windows, DB thử riêng, 34 test qua. Có test session/CSRF, replay cùng owner và song song, giới hạn kích thước khai báo và khi đọc, nhận lại sau khi mất phản hồi mà FakeDrive đã ghi file, xác minh và dọn staging.
- Ruff lint/format và `git diff --check` qua. Thay đổi này không thêm migration. Rollback mã phải dừng nhận upload mới và giữ volume staging cho đến khi job còn mở được xử lý.
