# Kho Tri Thức — Lưu khoa học, mở rộng bền vững

**Kế hoạch hiện hành: V4.4 — 15/11/2026**  
**Trạng thái thực tế:** Mới có tài liệu và roadmap. Chưa xây frontend/backend, chưa kết nối Google Drive thật, chưa chạy test sản xuất.

Kho Tri Thức là ứng dụng cá nhân dùng trên Android/Windows để gửi link Facebook/TikTok/YouTube/web, ảnh, file, ghi chú, tự lưu file gốc trên **Google Drive**, trích xuất văn bản nhẹ, phân loại theo **lĩnh vực/chủ đề/dự án**, xem **theo ngày**, tìm kiếm và lọc. Khi cần nghiên cứu, thử Google Drive app của ChatGPT trước, MCP riêng chỉ nếu cần dữ liệu phân loại từ ứng dụng.

## Ưu tiên thực hiện

1. **Kết nối Drive và lưu đúng file thật**, có trạng thái, ID ổn định và backup.
2. **Thư viện cá nhân**: xem nhanh, mở gốc, sửa tên, ghi chú, nhóm, xóa mềm.
3. **Tự phân loại/tìm kiếm**: metadata, PDF/Word/Excel/Web text, phụ đề nguồn, AI nhẹ, bộ lọc.
4. **Thử ChatGPT đọc Drive**; custom MCP chỉ khi có câu hỏi cần tag/project riêng.
5. **Bổ sung khi dùng thật có nhu cầu**: OCR/ASR, embeddings, video stream nâng cao, provider thứ hai, nhiều worker/người dùng.

## Kiến trúc cân bằng giữa hiện tại và nâng cấp

| Thành phần | Chọn |
| --- | --- |
| File gốc | **Google Drive**, OAuth `drive.file` |
| Metadata/danh mục/job/search | **PostgreSQL một container**, backup `pg_dump`/JSON manifest lên Drive + bản ngoài Drive |
| Backend | **Django 5.2 LTS + Django Ninja**, một codebase |
| Frontend | **React + TypeScript + Vite + Mantine**, PWA |
| Tác vụ nền | **Một worker Django + job bền vững trong Postgres**, không Redis |
| Media và trích xuất | yt-dlp/FFmpeg; pypdf/python-docx/openpyxl/Trafilatura, phụ đề có sẵn |
| AI | Rule-based + provider nhẹ sau benchmark; chưa OCR/ASR toàn bộ |
| ChatGPT | Google Drive app trước; MCP tùy chọn qua read/search API |
| Triển khai | Docker Compose một VM khi cần 24/7; phát triển trên Windows qua Docker |

**Tại sao quay lại PostgreSQL?** Không phải vì dữ liệu cá nhân nhiều, mà vì đổi SQLite/FTS5/queue khi muốn thêm OCR, ASR, embeddings, nhiều worker hoặc các API chuyên sâu sẽ tốn công. Django khuyến nghị PostgreSQL ở production. Chỉ tăng **một container**, không tăng B2/R2, Redis hay microservice.

**Đầu tư đúng từ đầu, không lập trình sớm:** UUID nội bộ cho Item/Asset, StorageLocation tách Drive ID, nhiều-nhiều cho nhóm và dự án, DerivedContent có version, job idempotent, SearchService/ReadService, portable manifest. Chỉ cần DriveStorage implement thực tế.

## Tài liệu chính (giữ 5 file sống)

- [Kế hoạch v4.4](docs/MASTER_PLAN.md) — nhu cầu và các nguyên tắc lâu dài.
- [Kiến trúc và so sánh](docs/ARCHITECTURE_AND_DATA.md) — vì sao chọn, đối thủ, sơ đồ bảng/API, cách nâng cấp file/DB/AI/MCP.
- [Roadmap và nghiệm thu](docs/ROADMAP_AND_TESTS.md) — KT-xxx theo ưu tiên, test phục hồi/migration boundary và điều kiện mở rộng.
- [AGENTS.md](AGENTS.md) — quy tắc cho Codex/AI.
- [README.md](README.md) — trang này.

**Không commit file gốc cá nhân, Google OAuth token, secrets hoặc backup vào GitHub.** Benchmark video riêng: [video-download-benchmark](https://github.com/cavoixanh638/video-download-benchmark).

**Chưa chốt:** tài khoản Drive/expiry 500 GB, hosting 24/7, lựa chọn AI và phí, quyền Google Drive app của workspace ChatGPT. Tất cả phải được kiểm thử thật trước khi tuyên bố PASS.
