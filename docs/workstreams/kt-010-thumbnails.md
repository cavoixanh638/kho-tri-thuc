# KT-010 — Dịch vụ thumbnail

- Trạng thái **IN_PROGRESS**, nhánh `codex/kt-010-thumbnails`.
- Baseline `c51d39f3d3719a03760944145e9cf22b15c30cc6` từ `codex/kt-003-005-drive`. SHA mã đã kiểm `e0ce457a71371419f12df9a3919fc1c5b9e4e847`.
- Phạm vi `apps/backend/processing/thumbnail*.py`, `test_thumbnail*.py`, `requirements-thumbnail.txt` và checkpoint này.
- Đã lưu API `ThumbnailService.get_cached()` và `generate()`. Cache theo UUID/SHA-256/định dạng/kích thước, xác minh byte staging khi miss, ghi file tạm cùng thư mục rồi replace. PDFium render trang đầu. FFmpeg đọc một frame local, giới hạn 15 giây và số pixel giải mã, trả lý do fallback nếu thất bại.
- **PASS** trên Windows/Python 3.13.15: `ruff check processing`, `ruff format processing`, smoke Python tạo PNG/PDF tổng hợp 100×50, gọi `generate()` và xác nhận WebP 64×32 cùng byte nguồn nguyên vẹn.
- **NOT_RUN**: bộ unit test EXIF, PDF khóa/lỗi, cache miss/force/concurrency và video.
- Kế tiếp thêm và chạy test với fixture tổng hợp, xác minh HEAD/base và mở PR cho điều phối tích hợp worker/UI.
