# KT-009/106 · Đối soát Drive và kiểm chứng mapping

- Nhánh `codex/kt-009-drive-reconcile`, gốc `ea315f7c3e6559ff79725665022e8ad86abcaa64`.
- Trạng thái IN_PROGRESS. Việc tiếp theo là đọc metadata bằng OAuth hiện có và kiểm tra `appProperties`, xử lý trạng thái có bằng chứng và chạy test PostgreSQL.
- Giữ UUID, tên/tệp gốc đã xác minh, CaptureEvent và ghi chú người dùng. Phân biệt đưa vào thùng rác có bằng chứng với 404/403 khó xác định.
- Kiểm thử bằng OAuth thật khi chuyển host và kiểm Client/Project thật chưa chạy.
