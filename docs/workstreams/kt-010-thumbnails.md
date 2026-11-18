# KT-010 — Dịch vụ thumbnail

- Trạng thái **IN_PROGRESS**, nhánh `codex/kt-010-thumbnails`. Baseline `c51d39f3d3719a03760944145e9cf22b15c30cc6` từ `codex/kt-003-005-drive`.
- SHA mã đang kiểm `e0ce457a71371419f12df9a3919fc1c5b9e4e847`. Phạm vi `thumbnail*.py`, `test_thumbnail*.py`, `requirements-thumbnail.txt` trong `apps/backend/processing` và checkpoint này.
- **FAIL**, Windows/Python 3.13.15, `python -m unittest processing.test_thumbnail -v` với FFmpeg 9.0.2. Bộ test đang soạn trong môi trường tạm, 9/10 ca qua (gồm 8 subtest EXIF, PDF thật/lỗi/khóa, video MP4 thật). `test_concurrent_pdf_writers_leave_a_single_complete_cache_entry` gặp `PermissionError [WinError 5]` khi nhiều luồng cùng `os.replace` một đích.
- **PASS**: `ruff check processing`; smoke PNG/PDF → WebP 64×32, byte gốc giữ nguyên.
- Kế tiếp xử lý retry giới hạn cho lỗi chia sẻ file trên Windows, chạy lại bộ test và lặp test đồng thời, rồi lưu bản đã kiểm và mở PR.
