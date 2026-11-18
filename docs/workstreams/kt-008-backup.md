# KT-008 — PostgreSQL backup và manifest

- Mục tiêu: tạo bộ `pg_dump` và JSON phiên bản hóa từ cùng snapshot, kiểm thử restore vào PostgreSQL 18 mới và đối chiếu lịch sử, nhóm, mapping Drive.
- Phạm vi: `tools/backup/`, checkpoint này và runbook sau khi thực thi. Chạy riêng trên dữ liệu tổng hợp. Upload Drive thật chờ cấu hình tài khoản.
- Baseline / SHA mã ở mốc này: `c51d39f3d3719a03760944145e9cf22b15c30cc6` (`codex/kt-003-005-drive`). So sánh GitHub với `main` cho thấy SHA chưa nằm trên `main`.
- Test **NOT_RUN**. Đã đọc quy tắc, hiện trạng và tiêu chí KT-008 tại SHA trên. Chưa có công cụ hay kết quả restore.
- Tiếp theo ở mốc khởi tạo: kiểm tra schema/OAuth, chuẩn bị DB tạm, triển khai công cụ và kiểm thử vòng đầy đủ.

## Mốc bàn giao công cụ và runbook

- SHA mã đã đọc lại trên GitHub `a435ba157a3c40d41a772c9756a92a876564e7bd`. Baseline hiện đã nằm trên `main`, dùng `main` làm base PR.
- **PASS** trên Windows, PostgreSQL 18.4, Python 3.13. `KT_BACKUP_TEST=1 python -m unittest discover -s tools/backup -v` chạy 3/3 test trên DB mới. Nội dung được đối chiếu đủ 14 nhóm, gồm UUID, nguyên văn có Unicode/xuống dòng, giờ và trigger bất biến, nhóm pinned, mapping Drive qua client giả, trạng thái Job và snapshot khi có ghi đã commit. Test cũng xác nhận phát hiện tệp bị sửa và từ chối DB đích đã có dữ liệu.
- **PASS** chạy trực tiếp `backup.py create`, sao chép thư mục ngoài Drive, `backup.py verify` và `backup.py restore` vào DB mới. Đầu ra restore `Database restored and manifest collections matched.`. `python -m pip check`, `makemigrations --check --dry-run` và `manage.py test` từ `apps/backend` (19/19) đều qua.
- **NOT_RUN** CLI qua Docker Compose và tài khoản Drive thật. Máy kiểm thử có bộ công cụ PostgreSQL native, thiếu Docker. Luồng manifest v1 dùng dump để khôi phục và JSON để đọc/đối chiếu. Upload Drive và xác minh mở file thật được kiểm thử khi có tài khoản.
- Tích hợp qua `tools/backup/backup.py` với `create`, `verify`, `restore --target-db` và tùy chọn `--compose`. Runbook ở `docs/operations/BACKUP_RESTORE.md`. Có thể rollback bằng revert PR. Các gói đã tạo ở ngoài repo.
