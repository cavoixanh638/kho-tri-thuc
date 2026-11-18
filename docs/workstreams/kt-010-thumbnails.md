# KT-010 — Dịch vụ thumbnail

- Trạng thái **IN_PROGRESS**. Nhánh `codex/kt-010-thumbnails`.
- Baseline và SHA mã hiện tại `c51d39f3d3719a03760944145e9cf22b15c30cc6` từ `codex/kt-003-005-drive`.
- Phạm vi `apps/backend/processing/thumbnail*.py`, `test_thumbnail*.py`, `requirements-thumbnail.txt` nếu cần, và checkpoint này.
- Đích bàn giao là API Python tạo thumbnail WebP/JPEG cho ảnh và trang đầu PDF, cache theo Asset và SHA-256, ghi atomic, có thể tạo lại sau cache miss. PDF lỗi hoặc khóa trả thông tin để hiển thị placeholder. Frame video local cần giới hạn thời gian/kích thước và có fallback.
- Kiểm thử **NOT_RUN**. Chưa có thay đổi mã. Cần test ảnh bất đối xứng đủ tám hướng EXIF, PDF lỗi/khóa, cache miss và nguồn giữ nguyên, cùng giới hạn video nếu triển khai.
- Kế tiếp đọc source tại baseline, triển khai và chạy test trên fixture tổng hợp, rồi mở PR cho điều phối đăng ký dependencies, worker và UI.
