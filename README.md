# Kho Tri Thức — Lưu khoa học, mở rộng bền vững

**Kế hoạch hiện hành: V4.5 (15/11/2026) — PostgreSQL đã được người dùng chốt.**  
**Trạng thái:** mới có tài liệu, chưa có mã nguồn ứng dụng, kết nối Google Drive thật hoặc test triển khai.

Kho Tri Thức là ứng dụng cá nhân trên Android/Windows để gửi link Facebook/TikTok/YouTube/web, video, ảnh, file và ghi chú; lưu file gốc lên **Google Drive**; trích xuất chữ nhẹ và phân loại theo **lĩnh vực/chủ đề/dự án**, xem **theo ngày**, tìm kiếm tiếng Việt có/không dấu. Khi nghiên cứu bằng ChatGPT, thử Google Drive app trước; MCP riêng chỉ nếu cần.

## Công nghệ đã lựa chọn

| Thành phần | Quyết định |
| --- | --- |
| File gốc | **Google Drive** là kho chính, kết nối Drive API OAuth `drive.file`; không cần B2/R2 bản đầu |
| Database | **PostgreSQL — ĐÃ CHỐT**, một container cùng backend, local/test/prod thống nhất; không dùng SQLite làm DB chính |
| Backend | **Django 5.2 LTS + Django Ninja**, phân module trong một codebase |
| Frontend | **React + TypeScript + Vite + Mantine**, PWA cho Android/Windows |
| Tác vụ | **Một Python/Django worker + bảng Job PostgreSQL**, idempotent, không Redis |
| Media | yt-dlp + FFmpeg, luôn giữ link khi video không tải được |
| Trích chữ | pypdf làm baseline; **so với PyMuPDF trên PDF tiếng Việt và giấy phép** rồi mới chốt; python-docx, openpyxl, Trafilatura, phụ đề nguồn |
| Search | PostgreSQL FTS + `unaccent`/cấu hình `kt_vi`, GIN, `pg_trgm`; phải test tiếng Việt và index thực tế |
| ChatGPT | Google Drive app **kết hợp thử bản xuất tri thức từ PostgreSQL lên Drive**; MCP chỉ đọc nếu thử nghiệm chưa đạt |
| Triển khai | Docker Compose một máy khi cần 24/7, backup `pg_dump` và manifest lên Drive + bản độc lập |

**Không cần lúc đầu:** PostgreSQL managed trả phí, microservices, B2/R2, Redis/Celery, vector DB, OCR/ASR hàng loạt, OAuth server MCP doanh nghiệp.

## Những điểm phải thực hiện đúng

- **Giữ ID nội bộ:** `Item.id` và `Asset.id` là UUID; `drive_file_id` chỉ ở `StorageLocation`. Không đổi tên file gốc thành ID chỉ để định danh.
- **Thumbnail:** tạo/cache ảnh đại diện trong volume bền vững, lazy-load và regenerate; không dùng trực tiếp Google Drive `thumbnailLink` ngắn hạn trên toàn bộ lưới ảnh.
- **Video:** upload xong không đồng nghĩa Drive preview đã sẵn sàng; thử khả năng phát thật trước, cache video tạm có TTL/quota chỉ khi cần.
- **OAuth:** dùng quyền `drive.file`, giữ Cloud Project/Client ổn định khi di chuyển máy; có kịch bản thử khôi phục/cấp quyền lại nếu đổi Client/Project; không tự động xin `drive.readonly` rộng.
- **ChatGPT:** dữ liệu note/project/transcript chỉ nằm trong PostgreSQL sẽ **không tự xuất hiện** trên Drive. Pilot 5–10 Item thành Google Docs/TXT/Markdown, mỗi Item một file đại diện có version/status đồng bộ; không cam kết ChatGPT đọc 100% hoặc hiểu MP4 không có transcript.
- **Tìm kiếm:** migration `kt_vi` sử dụng text-search dictionary `unaccent`, kiểm tra vector/query/index đúng cấu hình, không tùy tiện đánh dấu `unaccent()` là `IMMUTABLE`.
- **Bảo toàn:** bản gốc không bị AI sửa, backup/manifest và thử restore trước khi nhập dữ liệu quan trọng.

## Lộ trình

1. **Lưu và xem lại được:** Drive, PostgreSQL, UUID, API, worker, backup, Thêm/Thư viện/Chi tiết, thumbnail.
2. **Tự sắp xếp/tìm kiếm:** metadata, trích chữ nhẹ, PDF benchmark, nhóm/dự án/tag/ngày, AI nhẹ, search tiếng Việt.
3. **ChatGPT:** thử Google Drive app và bản xuất tri thức có version; MCP chỉ đọc nếu phát sinh nhu cầu.
4. **Nâng cấp tùy thực tế:** Android share tốt hơn, OCR/ASR theo yêu cầu, vector search, nhà lưu trữ thứ hai.

## Bộ tài liệu chuẩn

- [MASTER_PLAN.md](docs/MASTER_PLAN.md) — phạm vi, quyết định v4.5, ưu tiên.
- [ARCHITECTURE_AND_DATA.md](docs/ARCHITECTURE_AND_DATA.md) — so sánh công nghệ, dữ liệu/API, thiết kế kỹ thuật và R2 phản biện.
- [ROADMAP_AND_TESTS.md](docs/ROADMAP_AND_TESTS.md) — nhiệm vụ KT-xxx, các cổng PASS và kiểm thử U01–U18.
- [AGENTS.md](AGENTS.md) — quy tắc cho Codex và AI.
- [README.md](README.md) — tổng quan này.

**Không commit OAuth token, .env, media gốc, PostgreSQL dump hoặc backup vào repository.**

[Video downloader benchmark riêng](https://github.com/cavoixanh638/video-download-benchmark) chỉ là tài liệu tham khảo, **không phải bằng chứng Kho Tri Thức đã hoạt động**.

**Còn phải kiểm chứng:** account/quota/hạn 500 GB Drive, host 24/7, AI provider và phí, browser Android Share Target, kết nối Google Drive app theo workspace ChatGPT, PDF parser và kết quả index tiếng Việt.
