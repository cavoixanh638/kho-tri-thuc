# KT-008 — PostgreSQL backup và manifest

- Mục tiêu: tạo bộ `pg_dump` và JSON phiên bản hóa từ cùng snapshot, kiểm thử restore vào PostgreSQL 18 mới và đối chiếu lịch sử, nhóm, mapping Drive.
- Phạm vi: `tools/backup/`, checkpoint này và runbook sau khi thực thi. Chạy riêng trên dữ liệu tổng hợp. Upload Drive thật chờ cấu hình tài khoản.
- Baseline / SHA mã ở mốc này: `c51d39f3d3719a03760944145e9cf22b15c30cc6` (`codex/kt-003-005-drive`). So sánh GitHub với `main` cho thấy SHA chưa nằm trên `main`.
- Test **NOT_RUN**. Đã đọc quy tắc, hiện trạng và tiêu chí KT-008 tại SHA trên. Chưa có công cụ hay kết quả restore.
- Tiếp theo: kiểm tra schema/OAuth, chuẩn bị DB tạm, triển khai công cụ và kiểm thử vòng đầy đủ.
