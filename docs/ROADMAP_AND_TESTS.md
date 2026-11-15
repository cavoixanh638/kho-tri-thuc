# LỘ TRÌNH VÀ NGHIỆM THU V4.6 — BASELINE TRIỂN KHAI ĐÃ CHỐT

**Ngày:** 15/11/2026 · **Theo:** `MASTER_PLAN.md` v4.6 và `ARCHITECTURE_AND_DATA.md` v4.6. **Đã chốt PostgreSQL** cho local/test/production; không dùng SQLite làm DB chính.  
**Trạng thái:** chưa có app, chưa có môi trường chạy và chưa có test PASS. Mọi checklist dưới là yêu cầu nghiệm thu tương lai.

## 1. Thứ tự triển khai và phụ thuộc

| Mốc | Mục tiêu người dùng | Kết quả bắt buộc | Không cần làm |
| --- | --- | --- | --- |
| **A — Nền tảng & Google Drive** | Gửi file, link, ghi chú rồi xem lại được | Google OAuth, Drive, **PostgreSQL đã chốt**, UUID, Asset/StorageLocation, API, 1 worker, thumbnail/cache, backup | B2/R2, MCP, OCR/ASR |
| **B — Thư viện thông minh** | Tự phân nhóm và tìm theo lĩnh vực/dự án/ngày | Metadata, trích chữ nhẹ, phụ đề nguồn, AI nhẹ, search, Android PWA cơ bản | Vector/RAG, đa người dùng |
| **C — ChatGPT** | ChatGPT nghiên cứu cả nội dung ghi chú/phụ đề khi có | Kiểm tra Google Drive app, pilot bản xuất tri thức từng Item có version; chỉ làm MCP nếu không đủ | Không hứa mọi định dạng được đọc/index hay ChatGPT hiểu MP4 thiếu transcript |
| **D — Nâng cấp có điều kiện** | Mở rộng chức năng mà không viết lại lõi | OCR/ASR, pgvector, tăng worker, storage thứ hai, native Android theo nhu cầu | Không triển khai theo lịch cứng |

**Quy tắc:** Chỉ nghiệm thu mốc A/B trên dữ liệu thật và backup restore. Không ép test embedding hoặc chatbot trước mốc A.

## 2. Mốc A — Nền tảng vững nhưng vẫn nhanh

| ID | Công việc | Điều kiện PASS |
| --- | --- | --- |
| KT-001 | Scaffold Django **5.2 LTS + Ninja**, **PostgreSQL** Docker, React/TS/Vite/Mantine, Django worker | Dùng chung Postgres local/test/prod, migration/reverse migration có test; không chuyển sang SQLite |
| KT-002 | Thiết kế schema UUID: Item/Source/Asset/StorageLocation, User FK, Groups/Projects/Tags, Job, DerivedContent | File ID Drive không làm PK; các bảng phục vụ đúng API |
| KT-003 | Google OAuth `drive.file`, tạo folder, reconnect khi `invalid_grant` | Giữ OAuth project/client ổn định; upload ảnh/PDF thật và đọc lại được; không lộ token |
| KT-004 | `DriveStorage` adapter và FakeStorage test | `save/open/stat/verify`; không có B2 code |
| KT-005 | Upload resumable, status rõ, thử pre-generated ID cho blob | Timeout không tạo hai Drive file; xác nhận file thật |
| KT-006 | UI Thêm, Thư viện, Chi tiết, Cài đặt; Django Auth 1 user | Android/Windows mở được, link-only rõ |
| KT-007 | JobRepository với `lease/retry/idempotency` và một worker | Kill/restart giữa download/upload không mất item/trùng file |
| KT-008 | `pg_dump` + JSON portable export mapping Drive ID, bản copy ngoài Drive | Restore DB/manifest mở lại file gốc và nhóm |
| KT-009 | Drive metadata và recovery quyền khi di chuyển host/client | Manifest + Drive khôi phục item/file, đổi host giữ Client phải PASS; lập P1 test Client mới cùng Project và Project mới, không mặc định lỗi 404 hoặc xin `drive.readonly` |

| KT-010 | Tạo thumbnail ảnh/video/PDF: **`pypdfium2` render trang đầu PDF**, Pillow **`ImageOps.exif_transpose()` trước resize ảnh Android**; lưu WebP/JPEG trong cache bền vững | PDF lỗi/khóa có placeholder; test đủ **8 EXIF Orientation**, không thay đổi ảnh gốc Drive; thumbnail đúng chiều, lazy load, không dùng trực tiếp Drive `thumbnailLink`, cache bị mất có thể tái tạo |

**Gate A:** File lên đúng Drive; user mở được, thumbnails chạy ổn, job không nhân bản; backup/restore thực tế đã PASS. PostgreSQL chạy một container, không cần managed DB.

## 3. Mốc B — Tự động tổ chức, tìm kiếm

| ID | Công việc | Điều kiện PASS |
| --- | --- | --- |
| KT-101 | Link/video ingest và yt-dlp + ffprobe, lưu nguồn | Tải thành công khi có thể; video lỗi vẫn còn link và trạng thái |
| KT-102 | Trích PDF/DOCX/XLSX/HTML/phụ đề; **benchmark 3 thư viện `pypdf` / `pypdfium2` / `PyMuPDF` trên 20–30 PDF tiếng Việt** | Đo dấu Unicode/độ chính xác, thứ tự đọc, trang/locator, RAM, thời gian, license và fallback; chốt extractor chữ dựa evidence. **KT-010 dùng `pypdfium2` thumbnail không phụ thuộc kết quả benchmark**; DerivedContent có version/hash |
| KT-103 | Taxonomy lĩnh vực/chủ đề, Project, Tag nhiều-nhiều, AI suggestion | Một item ở nhiều view; người dùng đổi nhóm không bị AI ghi đè |
| KT-104 | PostgreSQL `SearchService`: `kt_vi` + unaccent/simple/pg_trgm; **hai expression GIN index riêng trên `Item` và `DerivedContent`** | Migration đúng token config; `SearchVector`/`SearchQuery` khớp GIN từng bảng; tìm từ hai nguồn và hợp nhất `item_id`, lọc DerivedContent hiện hành/stale, lấy snippet/locator. Test sửa note/title, cập nhật text, dấu/không dấu, `đ/Đ`, số hiệu văn bản, `EXPLAIN ANALYZE`. Không dùng JOIN expression index hoặc một vector tổng hợp quá lớn |
| KT-105 | PWA Android Share Target smoke (nếu hỗ trợ) và fallback dán link | Share từ FB/TikTok/YouTube thử thực tế, không hứa kết quả chưa thử |
| KT-106 | Reconcile Drive rename/delete/modified file | Không hiển thị file mất quyền là “đã lưu”; DerivedContent stale khi thay nội dung |
| KT-107 | Đánh giá AI nhẹ trên 30–50 mục thực; cost cap và cho phép tắt AI | Có precision/coverage và tỷ lệ sửa nhóm; không dùng giả định |
| KT-108 | Thử tải nhiều loại file, trạng thái lỗi, bộ lọc và thay đổi có dấu | Cụm test nghiệp vụ B PASS |
| KT-109 (có điều kiện) | Thử Drive preview video và cache phát ngắn hạn | Đo playback sau upload; nếu cần giữ cache local có TTL, hạn ngạch, cleanup và quyền truy cập; không mặc định 24–48h/2GB |

**Gate B:** Dán link không cần chọn thư mục; được gợi ý nhóm và sửa, tìm lại bằng lĩnh vực/dự án/ngày, nội dung Drive có thể mở.

## 4. Mốc C — Tích hợp ChatGPT (KHÔNG xây mặc định)

| ID | Công việc | Tiêu chí |
| --- | --- | --- |
| KT-201 | Thử Google Drive app với file thật, ghi chú/DerivedContent chỉ ở PostgreSQL và MP4 thiếu transcript | Ghi rõ nội dung ChatGPT đọc được, phân biệt file Drive với metadata trong PostgreSQL, không tự suy đoán MP4 |
| KT-202E (pilot) | Xuất 5–10 Item làm bản văn bản đại diện trên Drive: Google Docs/TXT/Markdown | So khả năng ChatGPT tìm/đọc; 1 file/Item, update cùng file theo `source_version/exported_version`, `sync_status`, retry không trùng; không tự xuất cả kho |
| KT-202 | Dùng 5–10 câu hỏi cần tags/projects/note/transcript và đánh giá kết quả xuất Drive | Chỉ dùng MCP nếu kết quả Drive app + pilot chưa đáp ứng; không tuyên bố 100% coverage |
| KT-203 (có điều kiện) | Tạo MCP read-only dùng `SearchService/ReadKnowledgeService` | Trả ID/URL/locator, kiểm quyền và không cung cấp write tool |
| KT-204 (có điều kiện) | Auth/tunnel theo quyền workspace/ChatGPT | Test kết nối, hết hạn token, không lộ file hay credential |

**Gate C:** ChatGPT đọc được tài liệu Drive và **phần văn bản đại diện đã thử thành công** khi connector hỗ trợ; ghi rõ định dạng/độ trễ. MCP là tùy chọn, không phải cổng bắt buộc.

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
| U14 — Consistency export ChatGPT | KT-202E | Một Item/một file, sửa note/project/subtitle cập nhật bản xuất đúng version, lỗi thì báo stale, retry không trùng |
| U15 — Quyền OAuth mới | KT-009 + trước khi đổi Client thực | Giữ Client khi chuyển host, test Client khác cùng Project và Project khác; 403/404/invalid_grant có cách phục hồi |
| U16 — Thumbnail/PDF/EXIF | KT-010 (KT-109 nếu bật cache video) | `pypdfium2` render đúng trang đầu PDF, PDF hỏng/khóa xử lý được; 8 EXIF Orientation (xoay/lật) đúng, ảnh gốc giữ nguyên; lazy-load, cache regenerate, không lấy `thumbnailLink` Drive trực tiếp |
| U17 — PostgreSQL FTS đa nguồn | KT-104 | `kt_vi` và **hai nhóm GIN index Item/DerivedContent** được dùng, kết quả gộp theo ID đúng khi note sửa, text mới/stale và soft delete; có/không dấu, số hiệu, `EXPLAIN ANALYZE`; không tính vector xuyên JOIN mỗi lần gõ |
| U18 — PDF extractor evidence | KT-102 | So **3 thư viện** trên 20–30 PDF tiếng Việt, giấy phép pypdfium2/PDFium và PyMuPDF đã kiểm, quyết định extractor chữ và fallback có đo; không nhầm renderer thumbnail với text parser |

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
- **PostgreSQL là lựa chọn đã chốt**. Bản đầu không chạy SQLite thay thế; `KT-010` dùng `pypdfium2` render PDF và xử lý EXIF, `KT-102` chỉ quyết parser chữ sau benchmark 3 lựa chọn; `KT-104` dùng **hai GIN index riêng** qua `SearchService`. KT-202E chỉ là pilot, không cam kết toàn bộ Drive được ChatGPT lập chỉ mục.

**Thứ tự ưu tiên:** Drive lưu được → thư viện dùng được → tự phân nhóm/tìm kiếm → ChatGPT nghiên cứu → nâng cấp theo nhu cầu.
