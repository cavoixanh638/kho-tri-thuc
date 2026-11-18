# KT-007 Worker PostgreSQL

**Trạng thái** Kiểm thử tích hợp worker cục bộ đã qua. Chờ CI và tích hợp các handler nghiệp vụ.
**Nhánh** `codex/kt-007-worker` · **Baseline** `c51d39f3d3719a03760944145e9cf22b15c30cc6` · **Mã đã thử** `a43919f7d69f334680fbb259c11be3e335184ef4`

- Repository nhận job bằng `SELECT FOR UPDATE SKIP LOCKED`. Claim tạo token riêng, tăng attempt và đặt lease 10 phút theo thời gian PostgreSQL. Lease hết hạn có thể được nhận lại. Token hoặc lease hết hạn không thể cập nhật kết quả.
- Lỗi tạm thời retry với khoảng chờ 5, 10, 20 và 40 giây, tối đa 5 lần chạy. Lỗi vĩnh viễn dừng ngay. Worker ngừng nhận thêm job sau SIGINT/SIGTERM và giữ job chưa hoàn tất cho lần khởi động sau.
- Handler được gọi sau khi commit claim. Handler phải đặt timeout I/O trong giới hạn lease và giữ thao tác có hiệu lực idempotent khi chạy lại.

## Bàn giao tích hợp

- `JobRepository.enqueue(kind=..., idempotency_key=..., item=..., input_ref=...)` trả job đầu tiên theo cặp kind/key và dùng được trong giao dịch tạo CaptureEvent.
- Đăng ký `jobs.handlers.HANDLERS[kind] = handler`. Handler nhận `Job`, trả về khi thành công hoặc ném `JobFailure("safe_code", retryable=...)`. Chỉ job có kind đã đăng ký được nhận.
- Lease token bảo vệ trạng thái hàng đợi. Handler vẫn phải dùng khóa idempotency của đích cho mọi thao tác có thể chạy lại, kể cả thực hiện lưu file trên Drive.

## Bằng chứng

- Windows, PostgreSQL 18.4, database thử riêng. `manage.py test` qua 28 test. Có test hai kết nối tranh job, tiến trình con thoát đột ngột sau commit claim, worker nhận lại và giữ nguyên Item/CaptureEvent, rollback Event/Item/Job và mô phỏng mất phản hồi upload sau khi FakeDrive đã ghi file.
- Migration lên, về `jobs 0001` và áp lại thành công. `makemigrations --check --dry-run`, `run_worker --check`, Ruff và `git diff --check` đều qua.
- Kiểm thử Google Drive thật và luồng HTTP tích hợp còn phụ thuộc handler nghiệp vụ. Khi rollback schema, dừng worker trước rồi chạy `manage.py migrate jobs 0001`. Giữ dữ liệu Job hiện có, chỉ bỏ cột token; các job đang chạy sẽ có thể được nhận lại theo lease khi triển khai lại.
