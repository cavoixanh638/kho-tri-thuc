# LỘ TRÌNH VÀ NGHIỆM THU V4.4 — LÀM NHẸ, NÂNG CẤP ĐƯỢC

**Ngày:** 15/11/2026 · **Theo:** `MASTER_PLAN.md` v4.4 và `ARCHITECTURE_AND_DATA.md` v4.4.  
**Trạng thái:** chưa có app, chưa có môi trường chạy và chưa có test PASS. Mọi checklist dưới là yêu cầu nghiệm thu tương lai.

## 1. Thứ tự triển khai và phụ thuộc

| Mốc | Mục tiêu người dùng | Kết quả bắt buộc | Không cần làm |
| --- | --- | --- | --- |
| **A — Nền tảng & Google Drive** | Gửi file, link, ghi chú rồi xem lại được | Google OAuth, Drive, PostgreSQL, Item UUID, Asset/StorageLocation, API, 1 worker và backup | B2/R2, MCP, OCR/ASR |
| **B — Thư viện thông minh** | Tự phân nhóm và tìm theo lĩnh vực/dự án/ngày | Metadata, trích chữ nhẹ, phụ đề nguồn, AI nhẹ, search, Android PWA cơ bản | Vector/RAG, đa người dùng |
| **C — ChatGPT** | Yêu cầu ChatGPT nghiên cứu file Drive | Kiểm tra Google Drive app; chỉ tạo MCP nếu truy vấn tag/dự án nội bộ thực sự cần | OAuth MCP khi plugin Drive đã đủ |
| **D — Nâng cấp có điều kiện** | Mở rộng chức năng mà không viết lại lõi | OCR/ASR, pgvector, tăng worker, storage thứ hai, native Android theo nhu cầu | Không triển khai theo lịch cứng |

**Quy tắc:** Chỉ nghiệm thu mốc A/B trên dữ liệu thật và backup restore. Không ép test embedding hoặc chatbot trước mốc A.

## 2. Mốc A — Nền tảng vững nhưng vẫn nhanh

| ID | Công việc | Điều kiện PASS |
| --- | --- | --- |
| KT-001 | Scaffold Django **5.2 LTS + Ninja**, Postgres Docker, React/TS/Vite/Mantine, Django worker | Chạy local Windows/Docker, migration/reverse migration có test |
| KT-002 | Thiết kế schema UUID: Item/Source/Asset/StorageLocation, User FK, Groups/Projects/Tags, Job, DerivedContent | File ID Drive không làm PK; các bảng phục vụ đúng API |
| KT-003 | Google OAuth `drive.file`, tạo thư mục ứng dụng, reconnect khi `invalid_grant` | Tài khoản đúng, upload được 1 ảnh + 1 PDF thật, không lộ token |
| KT-004 | `DriveStorage` adapter và FakeStorage test | `save/open/stat/verify`; không có B2 code |
| KT-005 | Upload resumable, status rõ, thử pre-generated ID cho blob | Timeout không tạo hai Drive file; xác nhận file thật |
| KT-006 | UI Thêm, Thư viện, Chi tiết, Cài đặt; Django Auth 1 user | Android/Windows mở được, link-only rõ |
| KT-007 | JobRepository với `lease/retry/idempotency` và một worker | Kill/restart giữa download/upload không mất item/trùng file |
| KT-008 | `pg_dump` + JSON portable export mapping Drive ID, bản copy ngoài Drive | Restore DB/manifest mở lại file gốc và nhóm |
| KT-009 | Drive metadata `asset_id/item_id` ngắn, recovery test | Nếu DB bị mất, manifest + Drive file cho phép khôi phục liên kết |

**Gate A:** File lên đúng Drive; user mở được; job/bản sao không nhân trùng; backup/restore đã được chạy thật. PostgreSQL một container chứ không là managed DB phức tạp.

## 3. Mốc B — Tự động tổ chức, tìm kiếm

| ID | Công việc | Điều kiện PASS |
| --- | --- | --- |
| KT-101 | Link/video ingest và yt-dlp + ffprobe, lưu nguồn | Tải thành công khi có thể; video lỗi vẫn còn link và trạng thái |
| KT-102 | Parser PDF có chữ, DOCX, XLSX, HTML, phụ đề nguồn | DerivedContent có processor version/input hash, không sửa file gốc |
| KT-103 | Taxonomy lĩnh vực/chủ đề, Project, Tag nhiều-nhiều, AI suggestion | Một item ở nhiều view; người dùng đổi nhóm không bị AI ghi đè |
| KT-104 | `SearchService` PostgreSQL fulltext + unaccent/pg_trgm | Tìm có dấu/không dấu, lọc ngày/source/projects; API độc lập SQL |
| KT-105 | PWA Android Share Target smoke (nếu hỗ trợ) và fallback dán link | Share từ FB/TikTok/YouTube thử thực tế, không hứa kết quả chưa thử |
| KT-106 | Reconcile Drive rename/delete/modified file | Không hiển thị file mất quyền là “đã lưu”; DerivedContent stale khi thay nội dung |
| KT-107 | Đánh giá AI nhẹ trên 30–50 mục thực; cost cap và cho phép tắt AI | Có precision/coverage và tỷ lệ sửa nhóm; không dùng giả định |
| KT-108 | Thử tải nhiều loại file, trạng thái lỗi, bộ lọc và thay đổi có dấu | Cụm test nghiệp vụ B PASS |

**Gate B:** Dán link không cần chọn thư mục; được gợi ý nhóm và sửa, tìm lại bằng lĩnh vực/dự án/ngày, nội dung Drive có thể mở.

## 4. Mốc C — Tích hợp ChatGPT (KHÔNG xây mặc định)

| ID | Công việc | Tiêu chí |
| --- | --- | --- |
| KT-201 | Thử Google Drive app trong ChatGPT với file PDF, Doc/Sheet, video có hoặc không transcript | ChatGPT tìm/đọc/so sánh đúng file khi connector hỗ trợ; ghi limitation |
| KT-202 | Dùng 5–10 câu hỏi cần tags, projects, note riêng của hệ thống | Nếu Drive app không đáp ứng và metadata nội bộ giải quyết được, chấp nhận làm MCP |
| KT-203 (có điều kiện) | Tạo MCP read-only dùng `SearchService/ReadKnowledgeService` | Trả ID/URL/locator, kiểm quyền và không cung cấp write tool |
| KT-204 (có điều kiện) | Auth/tunnel theo quyền workspace/ChatGPT | Test kết nối, hết hạn token, không lộ file hay credential |

**Gate C:** Hỏi ChatGPT nghiên cứu tài liệu Drive thành công; MCP là tùy chọn thật, không phải cổng bắt buộc.

## 5. Nghiệm thu KHẢ NĂNG NÂNG CẤP — phải chuẩn bị ngay nhưng không build tính năng sau

| Test | Thời điểm | Kết quả mong đợi |
| --- | --- | --- |
| U01 — StoragePort | Gate A | Thay FakeStorage/DriveStorage trong test không sửa Item/Group/REST contract |
| U02 — Restore mất Postgres | Gate A | Từ `pg_dump` hoặc export+manifest khôi phục các Item/Drive mapping, không mất ghi chú/nhóm |
| U03 — File trùng & upload timeout | Gate A | Retry idempotent, không thêm asset/location trùng |
| U04 — Đổi tên/xóa file trên Drive | Gate B | Phát hiện mất/đổi; Item vẫn còn và báo trạng thái đúng |
| U05 — Trích lại parser | Gate B | Version mới từ cùng Asset không xóa ghi chú người dùng/cũ |
| U06 — AI phân nhóm lại | Gate B | Gán/đặt tên thủ công vẫn được giữ |
| U07 — Search backend | Gate B | Tất cả UI/API gọi `SearchService`, không SQL tìm kiếm rải trong view |
| U08 — Nhiều worker | Trước khi tăng từ 1 lên 2 worker | Cùng job không xử lý 2 lần không kiểm soát; lease, retry/pass |
| U09 — Drive→B2/R2 thử | Khi bắt đầu làm provider mới | Copy/verify mới, update StorageLocation; Item ID/Group/API giữ nguyên |
| U10 — Thêm OCR/ASR | Khi được giao tính năng | Tạo DerivedContent mới với provenance/locator; không migrate Item schema lớn |
| U11 — pgvector hai thế hệ | Khi được giao semantic search | Model/version/dimension tách; rollback được khi đổi model |
| U12 — ChatGPT MCP | Khi thật sự cần | Search/read của ứng dụng được tái sử dụng; auth chuẩn, read-only |
| U13 — Google-native exports | Khi bắt đầu import Google Docs/Sheets | Phân biệt MIME blob/native, export phù hợp; handle file lớn/giới hạn |

**Không ngụy tạo U09–U13 đã PASS ngay từ đầu.** Chỉ thiết kế ID và cổng interface để sau có đường thực hiện.

## 6. Điểm kích hoạt nâng cấp dựa trên tình trạng thực tế

| Tín hiệu | Việc nên xem xét | Không nên tự động làm |
| --- | --- | --- |
| Drive gần đầy hoặc ưu đãi sắp hết (mốc cảnh báo gợi ý: 80% dung lượng hoặc 90 ngày trước hạn) | Chọn nâng Drive hay thêm StorageProvider; ước tính nhu cầu video | Chuyển kho hàng loạt khi chưa verify |
| Tìm kiếm chậm/không tìm ra từ khóa trên bộ thử | Benchmark Postgres/index rồi Typesense hoặc ngữ nghĩa | Cài Elasticsearch sẵn |
| Người dùng thường xuyên yêu cầu tra nội dung scan/video thiếu phụ đề | Làm OCR/ASR theo yêu cầu trước, cache kết quả | Chạy OCR/ASR tất cả media |
| AI thường xuyên đề xuất sai nhóm | Tối ưu taxonomy/prompt/model với bộ đánh giá | Đổi mô hình tự động thiếu benchmark |
| Hàng đợi thường xuyên ùn hoặc cần >1 worker | Tăng concurrency, thử Procrastinate/Chancy khi cần | Dựng Redis/Celery ngay |
| ChatGPT Drive không tìm đúng metadata/dự án | MCP read-only từ service hiện có | Xây chatbot riêng |
| Thêm người dùng hoặc phân quyền | Mở account/workspace per-user + Drive connection | Áp RBAC enterprise trước |
| Muốn phát video rất nhiều lượt | Đo thực tế Drive playback/quota, cân nhắc derivative/streaming khác | Xây CDN khi chỉ mình xem |

**Ngưỡng 80%/90 ngày chỉ là cảnh báo dự phòng, không phải yêu cầu tài chính hoặc số liệu sử dụng đã quan sát.**

## 7. Phạm vi bảo mật đủ dùng và những điều không được cắt

- Single-user Django Auth, HTTPS khi public, CSRF/session, ẩn Drive token trong backend.
- Chặn URL private/localhost/metadata network và giới hạn upload/tải file để tránh SSRF/DoS.
- Không cho worker copy/xóa Drive file ngoài thư mục/đúng phạm vi.
- Không để API/MCP cho phép đọc toàn bộ Drive nặc danh.
- Backup Postgres/manifest độc lập; không đẩy media cá nhân lên GitHub.
- Không mở multi-user/RBAC/audit enterprise, cấu hình monitoring đắt tiền.

## 8. Trạng thái và phạm vi AI/Codex

- Repo mới chỉ có tài liệu: **chưa có app, database thật, Google OAuth credential, deployment hoặc các PASS về runtime**.
- Mỗi nhiệm vụ khi hoàn tất phải có commit SHA, test đã chạy, test chưa chạy, rủi ro, rollback.
- Trước khi chọn/thay công nghệ, so với **2–3 lựa chọn cạnh tranh**, nêu vì sao phù hợp với Kho Tri Thức hiện tại và bảo đảm đường nâng cấp.
- Đừng biến một bài nghiên cứu tương lai (pgvector, Drive migration) thành blocker của bản đầu.

**Thứ tự ưu tiên:** Drive lưu được → thư viện dùng được → tự phân nhóm/tìm kiếm → ChatGPT nghiên cứu → nâng cấp theo nhu cầu.
