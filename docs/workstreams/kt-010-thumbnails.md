# KT-010 — Dịch vụ thumbnail

- **DONE trong phạm vi dịch vụ**. Nhánh `codex/kt-010-thumbnails`, [PR #10](https://github.com/cavoixanh638/kho-tri-thuc/pull/10) vào `main`.
- Baseline `c51d39f3d3719a03760944145e9cf22b15c30cc6` từ `codex/kt-003-005-drive`. SHA mã đã kiểm `d8eb2a57c5c4bd907eeded0459f746c861900bd9`. Các file source/test trên GitHub đã được đối chiếu với bản chạy test.
- API `processing.thumbnail.ThumbnailService(cache_root)`, `get_cached(asset_id, content_sha256)` và `generate(asset_id=..., content_sha256=..., mime_type=..., source_path=..., force=False)`. Kết quả có `path` + `content_type` hoặc `placeholder_reason`; OSError có thể retry. Mặc định WebP 512 px. Cache có thể xóa và tạo lại.
- Cài `apps/backend/processing/requirements-thumbnail.txt` (Pillow 13.0.0, pypdfium2 5.15.2). FFmpeg local tùy chọn, xử lý một frame, timeout 15 giây, decode tối đa 33.554.432 pixel, trả fallback khi lỗi.
- **PASS**, Windows/Python 3.13.15/FFmpeg 9.0.2: từ `apps/backend`, `python -m unittest processing.test_thumbnail -v`, 11 test. Có 8 EXIF subtest bất đối xứng, PDF trang đầu/lỗi/khóa, cache miss/force, nguồn nguyên vẹn, ghi atomic, lỗi chia sẻ Windows và MP4 thật từ fixture tổng hợp.
- **PASS** 100 lượt lặp ca nhiều luồng (400 lần tạo bắt buộc). `ruff check processing`, `ruff format --check processing`, `python -m pip check` đều qua. Unittest discovery skip module trong môi trường thiếu dependencies tùy chọn.
- **NOT_RUN** worker/API/UI, lazy load Android, Drive thật và format video ngoài MP4. Điều phối gắn dependencies, volume cache, worker và UI; kiểm quyền đọc Asset trước khi phục vụ path.
- Rollback bằng PR revert sau tích hợp. Cache là dữ liệu phát sinh có thể tái tạo.
