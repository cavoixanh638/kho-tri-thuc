# KT-101 — Thu nhận nguồn

## Khởi tạo · 18/11/2026

- Nhánh `codex/kt-101-source-fetch` được tạo từ `c51d39f3d3719a03760944145e9cf22b15c30cc6` trên `codex/kt-003-005-drive`.
- Bàn giao hàm thu nhận URL web, metadata và văn bản khả dụng, bằng chứng nguồn và lý do truy xuất thất bại. Kiểm soát SSRF cả khi DNS đổi hoặc nguồn chuyển hướng. Giữ URL gốc và thời điểm thử khi nguồn 404 hoặc yêu cầu quyền.
- Phạm vi `apps/backend/processing/source_*.py`, `apps/backend/processing/test_source_*.py` và checkpoint này. Chat điều phối sẽ gắn Job và cập nhật hiện trạng chung.
- SHA mã nguồn hiện tại là baseline trên. Test **NOT_RUN**. Đã đối chiếu AGENTS, hiện trạng, kiến trúc và tiêu chí KT-101 tại baseline. Bước tiếp theo là triển khai web và test transport giả. Phụ đề/video chỉ xuất hiện khi có bằng chứng; nếu chưa có đường yt-dlp an toàn, ghi rõ phần thiếu.

## Bàn giao web · 18/11/2026

- Mã nguồn `6eaaba1d20f6aa8d77318d01cda1b8eb7ec83a15`, [PR nháp #8](https://github.com/cavoixanh638/kho-tri-thuc/pull/8) vào `main`. Baseline được xác nhận là tổ tiên của `main` khi mở PR. Diff có bốn tệp source/test và checkpoint này.
- **PASS 19/19** trên Windows, Python 3.13.15, thư mục tạm. Lệnh `python -B -m unittest discover -v -s . -p 'test_source_*.py'`. Transport/socket/DNS giả kiểm tra DNS rebinding, chuyển hướng tới mạng nội bộ, IP ghim và hostname TLS, giữ link/giờ khi HTTP lỗi, giới hạn thời gian và kích thước. Cú pháp, thụt lề và khoảng trắng cuối dòng đều đã kiểm tra. Lần chạy đầu FAIL 1 ca vì fixture chạm trần số phản hồi HTTP tạm của Python trước trần byte; fixture mới đã đo trúng giới hạn và chạy lại PASS.
- **PASS 38/38** trên Ubuntu GitHub Actions và PostgreSQL trong Docker Compose. [Run #44330164763](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44330164763) thử commit merge tạm `65059ef15392562d3f1ccfea5fa37256a42b48f2` bằng `docker compose exec -T api python manage.py test`. Smoke Django/worker/API/frontend trong cùng run đều PASS.
- **NOT_RUN** với DNS/TLS từ website thật, Job KT-101 tích hợp, yt-dlp/ffprobe và thu phụ đề/video. Bản web đọc HTML/XHTML tĩnh và plain text; body cần có MIME phù hợp với encoding identity. Web text là văn bản quan sát được trên trang. Kết quả hỗ trợ ghi riêng phần metadata hoặc web text đã lấy, và chưa sinh kết quả phụ đề/video.

### Tích hợp Job

Gọi `processing.source_fetch.fetch_source(url) -> SourceResult` sau khi lưu lượt nhận. `result.available` là tập phần dữ liệu đã thu thực tế, `metadata` và `text` chứa giá trị tương ứng. `provenance.source_url` giữ đầu vào, `attempted_at` ghi giờ thử UTC tách với giờ CaptureEvent; `response_url` và `http_status` là phản hồi đã quan sát cuối cùng. Nếu chuyển hướng bị chặn, các trường đó mô tả phản hồi chuyển hướng trước khi chặn. `body_sha256` có khi đã đọc đủ thân hợp lệ để xử lý. Khi ghi DerivedContent cho web text, dùng `processor`, `processor_version`, `body_sha256` và URL phản hồi làm provenance. Giờ provenance cần chuyển ISO 8601 nếu ghi vào JSON.

Giữ link cho mọi kết quả. `access_denied` ghi HTTP 401/403, `not_found` ghi 404/410. Job quyết định retry dựa trên `error_code` và `provenance.http_status`, ví dụ timeout hoặc 503. Mặc định tối đa 5 redirect, 10 giây và 1 MiB body. Hướng tiếp theo là nối Job ở chat điều phối, sau đó kiểm chứng egress cho các yêu cầu phụ của extractor trước khi bật tải video/phụ đề. Nếu cần rollback sau khi tích hợp, revert PR; nhánh này không có migration.
