# Kho Tri Thức — Lưu khoa học, mở rộng bền vững

**Kế hoạch hiện hành: V4.7 (18/11/2026) — tiếp nhận tức thì, tự tổ chức và bảo toàn lịch sử; PostgreSQL đã chốt.**
**Trạng thái triển khai và kết quả kiểm thử:** [CURRENT_STATE.md](docs/CURRENT_STATE.md). **Chạy scaffold:** [LOCAL_SETUP.md](docs/operations/LOCAL_SETUP.md).

Kho Tri Thức lấy **văn bản/Markdown làm nội dung chính** để đọc, tìm kiếm và tổ chức. Media và tài liệu nguồn đi kèm để minh họa và truy nguyên. Có thể viết/dán bài văn bản hoặc gửi URL/tệp → **lưu ngay nội dung và thời điểm nhận** → thu thập nội dung khả dụng → **tự xếp vào nhóm hiện có khi đủ tin cậy và tìm các mục liên quan**. File gốc lưu Google Drive, danh mục/lịch sử trong PostgreSQL. Gửi lại link tạo lượt tiếp nhận mới nhưng không nhân đôi file; HTTP retry cùng request key không tạo lượt mới. [Đọc và viết Markdown](docs/operations/TEXT_KNOWLEDGE.md), [quy trình](docs/CAPTURE_AND_ORGANIZE.md).

## Giao AI tiếp tục sau nghiên cứu 17 sản phẩm (20/11/2026)

**[Bộ giao việc KT-114–KT-130 trên GitHub main](docs/workstreams/notes-ux-20261120/INDEX.md)**: có prompt một dòng, nhiệm vụ riêng, quyền sửa file, test acceptance và các gate an toàn dữ liệu/Android/10.000 mục. Đây là **định hướng triển khai có thể giao cho AI**, không phải bằng chứng tính năng mới đã được code hay nghiệm thu. **Bổ sung thiếu sót G00 (20/11/2026):** [KT-122 — cây folder + note](docs/workstreams/notes-ux-20261120/KT-122-FOLDER-EXPLORER.md) và [KT-123 — note cha–con](docs/workstreams/notes-ux-20261120/KT-123-NOTE-HIERARCHY.md); PR #57 **chưa có** hai tính năng đó, dù có cây Topic và backlinks. Báo cáo nghiên cứu 17 luồng và G00 được lưu tại PR #30–#47 **chưa merge**; xem [PR #47](https://github.com/cavoixanh638/kho-tri-thuc/pull/47) để đối chiếu nguồn và các đính chính.

**[G00 — ma trận 38 năng lực rút từ 17 nghiên cứu](docs/workstreams/notes-ux-20261120/G00-FEATURE-TRACEABILITY.md)**: kiểm lại code chính xác, phân loại MAIN/PR57/PARTIAL/GAP/HOÃN, nhiệm vụ KT-122–129 còn thiếu và KT-130 theo dõi các ý tưởng có điều kiện. PR #57 có UI candidate nhưng **chưa merge**, chưa phải trải nghiệm tổ chức/tìm kiếm/clip/export hoàn chỉnh.

Không thay nền tảng Django/PostgreSQL/Google Drive chỉ vì Obsidian/Notion/Heptabase có UX tốt. Giữ nguyên nguồn gốc, CaptureEvent, Item UUID và quyền Drive. An toàn và phục hồi dữ liệu đi trước mở rộng editor, backlinks hoặc canvas.

## Công nghệ đã lựa chọn

| Thành phần | Quyết định |
| --- | --- |
| File gốc | **Google Drive** là kho chính, kết nối Drive API OAuth `drive.file`; không cần B2/R2 bản đầu |
| Database | **PostgreSQL — ĐÃ CHỐT**, một container cùng backend, local/test/prod thống nhất; không dùng SQLite làm DB chính |
| Backend | **Django 5.2 LTS + Django Ninja**, phân module trong một codebase |
| Frontend | **React + TypeScript + Vite + Mantine**, PWA cho Android/Windows |
| Tác vụ | **Một Python/Django worker + bảng Job PostgreSQL**, idempotent, không Redis |
| Media | yt-dlp + FFmpeg, luôn giữ link khi video không tải được |
| PDF và trích chữ | **`pypdfium2` tạo thumbnail PDF**; đọc chữ PDF chọn sau benchmark **pypdf/pypdfium2/PyMuPDF** và rà giấy phép; python-docx, openpyxl, Trafilatura, phụ đề nguồn |
| Search | PostgreSQL FTS + `unaccent`/`kt_vi`, `pg_trgm`; **hai nhóm GIN index riêng Item và DerivedContent**, SearchService hợp nhất kết quả theo item ID, có test tiếng Việt |
| ChatGPT | Google Drive app **kết hợp thử bản xuất tri thức từ PostgreSQL lên Drive**; MCP chỉ đọc nếu thử nghiệm chưa đạt |
| Triển khai | Docker Compose một máy khi cần 24/7, backup `pg_dump` và manifest lên Drive + bản độc lập |

**Không cần lúc đầu:** PostgreSQL managed trả phí, microservices, B2/R2, Redis/Celery, vector DB, OCR/ASR hàng loạt, OAuth server MCP doanh nghiệp.

## Những điểm phải thực hiện đúng

- **Giữ ID/lịch sử và giờ:** CaptureEvent/Item/Asset có UUID, Drive ID chỉ ở StorageLocation; `CaptureEvent.server_received_at` bất biến, `Item.saved_at` là giờ nhận đầu. Ngày xuất bản và xử lý riêng, ghi chú chỉ chữ lưu nguyên văn và không cần Drive asset.
- **Thumbnail:** `pypdfium2` render trang đầu PDF; ảnh Android dùng Pillow `ImageOps.exif_transpose()` **trước resize** để xử lý hướng EXIF (test 8 trường hợp), không sửa ảnh gốc. Cache WebP/JPEG trong volume bền vững, lazy-load và regenerate; không dùng trực tiếp Drive `thumbnailLink` ngắn hạn.
- **Video:** upload xong không đồng nghĩa Drive preview đã sẵn sàng; thử khả năng phát thật trước, cache video tạm có TTL/quota chỉ khi cần.
- **OAuth:** dùng quyền `drive.file`, giữ Cloud Project/Client ổn định khi di chuyển máy; có kịch bản thử khôi phục/cấp quyền lại nếu đổi Client/Project; không tự động xin `drive.readonly` rộng.
- **ChatGPT:** dữ liệu note/project/transcript chỉ nằm trong PostgreSQL sẽ **không tự xuất hiện** trên Drive. Pilot 5–10 Item thành Google Docs/TXT/Markdown, mỗi Item một file đại diện có version/status đồng bộ; không cam kết ChatGPT đọc 100% hoặc hiểu MP4 không có transcript.
- **Tìm kiếm và tự nhóm:** PostgreSQL hai GIN index Item/DerivedContent với `kt_vi`/unaccent/pg_trgm; `SearchService` tìm ứng viên, `OrganizationService` tự gán nhóm hiện có khi đủ chứng cứ, lưu `RelatedItem` có lý do; khi không chắc dùng Chưa phân loại/Đề xuất, không sửa curated.
- **Bảo toàn:** bản gốc không bị AI sửa, backup/manifest và thử restore trước khi nhập dữ liệu quan trọng.

## Lộ trình

1. **Nhận và xem lại được:** `CaptureEvent` và receipt giờ server ngay cho URL/chữ, PostgreSQL/Drive, Job, backup, Lịch sử/Thư viện/Chi tiết, thumbnail.
2. **Tự sắp xếp/tìm kiếm:** metadata, trích chữ nhẹ, benchmark PDF; **tự gán nhóm sẵn có và nối các Item liên quan**, AI/FTS tiếng Việt kiểm tra trên bộ đánh giá.
3. **ChatGPT:** thử Google Drive app và bản xuất tri thức có version; MCP chỉ đọc nếu phát sinh nhu cầu.
4. **Nâng cấp tùy thực tế:** Android share tốt hơn, OCR/ASR theo yêu cầu, vector search, nhà lưu trữ thứ hai.

## Bộ tài liệu chuẩn

**Bắt đầu từ [docs/README.md](docs/README.md) để chọn đúng tài liệu theo câu hỏi.**

- [CURRENT_STATE.md](docs/CURRENT_STATE.md) — trạng thái có bằng chứng, test đã/chưa chạy, việc kế tiếp.
- [REPOSITORY_LAYOUT.md](docs/REPOSITORY_LAYOUT.md) — nơi đặt file, ranh giới Git/Drive/Postgres và cách bố trí Django/React.
- [CAPTURE_AND_ORGANIZE.md](docs/CAPTURE_AND_ORGANIZE.md) — quy trình nhận URL/chữ, mốc thời gian, duplicate, tự nhóm và related items.
- [MASTER_PLAN.md](docs/MASTER_PLAN.md) — phạm vi, quyết định v4.7, ưu tiên.
- [ARCHITECTURE_AND_DATA.md](docs/ARCHITECTURE_AND_DATA.md) — so sánh công nghệ, dữ liệu/API, thiết kế kỹ thuật và R2 phản biện.
- [ROADMAP_AND_TESTS.md](docs/ROADMAP_AND_TESTS.md) — nhiệm vụ KT-xxx, các cổng PASS và kiểm thử; [INDEX AI handoff](docs/workstreams/notes-ux-20261120/INDEX.md) — task triển khai mới.
- [AGENTS.md](AGENTS.md) — quy tắc cho Codex và AI.
- [README.md](README.md) — tổng quan này.

**Không commit OAuth token, .env, media gốc, PostgreSQL dump hoặc backup vào repository.** Mã ứng dụng và kiểm thử nằm trong `apps/`, bộ đánh giá nằm trong `evals/`; xem hiện trạng để phân biệt tính năng đã kiểm chứng và các cổng còn mở. Không sao chép mã hoặc dữ liệu từ repo QLVB.

[Video downloader benchmark riêng](https://github.com/cavoixanh638/video-download-benchmark) chỉ là tài liệu tham khảo, **không phải bằng chứng Kho Tri Thức đã hoạt động**.

**Còn phải kiểm chứng:** account/quota/hạn 500 GB Drive, host 24/7, AI provider và phí, Android Share Target, kết nối Drive app trong ChatGPT, chất lượng 3 PDF extractor, thumbnail/EXIF thực tế và kết quả hai chỉ mục GIN tiếng Việt.
