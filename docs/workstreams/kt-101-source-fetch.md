# KT-101 — Thu nhận nguồn

## Khởi tạo · 18/11/2026

- Nhánh `codex/kt-101-source-fetch` được tạo từ `c51d39f3d3719a03760944145e9cf22b15c30cc6` trên `codex/kt-003-005-drive`.
- Bàn giao hàm thu nhận URL web, metadata và văn bản khả dụng, bằng chứng nguồn và lý do truy xuất thất bại. Kiểm soát SSRF cả khi DNS đổi hoặc nguồn chuyển hướng. Giữ URL gốc và thời điểm thử khi nguồn 404 hoặc yêu cầu quyền.
- Phạm vi `apps/backend/processing/source_*.py`, `apps/backend/processing/test_source_*.py` và checkpoint này. Chat điều phối sẽ gắn Job và cập nhật hiện trạng chung.
- SHA mã nguồn hiện tại là baseline trên. Test **NOT_RUN**. Đã đối chiếu AGENTS, hiện trạng, kiến trúc và tiêu chí KT-101 tại baseline. Bước tiếp theo là triển khai web và test transport giả. Phụ đề/video chỉ xuất hiện khi có bằng chứng; nếu chưa có đường yt-dlp an toàn, ghi rõ phần thiếu.
