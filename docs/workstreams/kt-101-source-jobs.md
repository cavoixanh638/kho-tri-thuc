# KT-101 Job thu thập nguồn

**Trạng thái** Handler và bộ kiểm thử PostgreSQL đã sẵn sàng tích hợp. Chat điều phối gắn đăng ký handler vào worker chung.
**Nhánh** `codex/kt-101-source-jobs` · **Mã đã thử** `1d1342d08983e0d0371f30ad6df2b0159bdcc09a` · **Baseline tích hợp** `f8ceec9` + thu thập nguồn thuần `83e78a8`

- Đăng ký `processing.source_jobs.fetch_source_job` cho kind `fetch_source`. Job nhận `input_ref.source_id` (int), `input_ref.capture_id` (UUID dạng chuỗi) và `job.item_id` để xác minh phạm vi Item và owner.
- Đọc mạng qua `processing.source_fetch.fetch_source` ngoài transaction. Transaction ngắn kiểm tra lease đang hoạt động, ghi trạng thái Item/Source cùng provenance và phiên bản `DerivedContent` loại `web_text` khi có văn bản mới. Lượt fetch lỗi hoặc rỗng vẫn giữ văn bản đã xác minh trước đó. Item.saved_at, CaptureEvent và chỉnh sửa thủ công được giữ.
- Enqueue `organize` theo key `source:<source_id>:evidence:<revision>`, với `item_id`, `source_id`, `capture_id` trong payload. Cùng bằng chứng chỉ dựng một job. HTTP tạm lỗi hoặc timeout retry có giới hạn. 404, thiếu quyền và URL bị chặn được ghi thất bại vĩnh viễn cho lượt xử lý.
- Trang video ghi nhận phần HTML/metadata có thật. Trạng thái file chưa áp dụng cho link chưa có Asset. Tích hợp này chỉ lấy dữ liệu web, chưa xác minh tải video/phụ đề.

## Bằng chứng

PostgreSQL 18.4 trên Windows, database thử riêng, 77 test qua. Sáu ca job riêng bao gồm mạng giả bên ngoài transaction, versioning qua retry, lease cũ, 404, phạm vi Item/owner và chuyển hướng video. Ruff lint/format và kiểm tra diff qua. Không thêm migration. Rollback mã bằng cách bỏ đăng ký handler trước; các job đang chờ được giữ trong PostgreSQL.
