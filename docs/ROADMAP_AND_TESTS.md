# LỘ TRÌNH VÀ NGHIỆM THU V4.7 — TIẾP NHẬN NGAY VÀ TỰ TỔ CHỨC

**Ngày:** 15/11/2026 · **Theo:** `MASTER_PLAN.md` v4.7 và `ARCHITECTURE_AND_DATA.md` v4.7. **Đã chốt PostgreSQL** cho local/test/production; không dùng SQLite làm DB chính.  
**Trạng thái tại baseline 18/11/2026:** chưa có app, môi trường hay runtime test PASS; **trạng thái cập nhật duy nhất** được theo dõi ở [CURRENT_STATE.md](CURRENT_STATE.md). Checklist ở đây là tiêu chí nghiệm thu, không tự chứng minh PASS.

## 0. Chuẩn bị repository trước KT-001 — hoàn thành ở cấp tài liệu

| Đầu việc | Kết quả kiểm tra | Ranh giới |
| --- | --- | --- |
| Quy định nơi đặt code, dữ liệu, tests/evals | [REPOSITORY_LAYOUT.md](REPOSITORY_LAYOUT.md) từ khảo sát read-only QLVB, áp dụng chọn lọc cho Django/Drive | Chỉ quy chuẩn, chưa phải code | 
| Báo cáo hiện trạng | [CURRENT_STATE.md](CURRENT_STATE.md), có trạng thái NOT_STARTED/NOT_RUN và task kế tiếp | Không giả PASS runtime | 
| Điều hướng AI và người dùng | [docs/README.md](README.md), `../AGENTS.md`, `../README.md` | Không tạo workboard/orchestrator khi chưa cần |
| Thao tác vận hành | Chỉ tạo LOCAL_SETUP khi KT-001 đã chạy, BACKUP_RESTORE khi KT-008 đã thử thật | **Không soạn runbook giả định thành kết quả** |

**Cổng vào KT-001:** Codex đọc `docs/CURRENT_STATE.md`, `docs/REPOSITORY_LAYOUT.md` và thiết kế v4.6; chỉ tạo thư mục có mã nguồn thật. Thực trạng/test sau khi chạy phải ghi về CURRENT_STATE, không đánh dấu PASS bằng sửa roadmap.

## 1. Thứ tự triển khai và phụ thuộc

| Mốc | Mục tiêu người dùng | Kết quả bắt buộc | Không cần làm |
| --- | --- | --- | --- |
| **A — Tiếp nhận nhanh & Google Drive** | Gửi URL/ghi chú chữ, lưu nguyên văn cùng giờ server ngay | CaptureEvent/ACK/Job, PostgreSQL, lịch sử theo Event, Drive, thumbnail, backup | B2/R2, MCP, OCR/ASR |
| **B — Thư viện tự tổ chức** | Tự xếp vào nhóm đã có và nối các Item liên quan | Metadata, SearchService, OrganizationService, RelatedItem, đánh giá AI/FTS tiếng Việt | Vector/RAG, đa người dùng |
| **C — ChatGPT** | ChatGPT nghiên cứu cả nội dung ghi chú/phụ đề khi có | Kiểm tra Google Drive app, pilot bản xuất tri thức từng Item có version; chỉ làm MCP nếu không đủ | Không hứa mọi định dạng được đọc/index hay ChatGPT hiểu MP4 thiếu transcript |
| **D — Nâng cấp có điều kiện** | Mở rộng chức năng mà không viết lại lõi | OCR/ASR, pgvector, tăng worker, storage thứ hai, native Android theo nhu cầu | Không triển khai theo lịch cứng |

**Quy tắc:** Chỉ nghiệm thu mốc A/B trên dữ liệu thật và backup restore. Không ép test embedding hoặc chatbot trước mốc A.

## 2. Mốc A — Nền tảng vững nhưng vẫn nhanh

| ID | Công việc | Điều kiện PASS |
| --- | --- | --- |
| KT-001 | Scaffold Django **5.2 LTS + Ninja**, **PostgreSQL** Docker, React/TS/Vite/Mantine, **một worker cùng codebase Django** | Bố trí đúng `REPOSITORY_LAYOUT.md`, local/test/prod thống nhất Postgres, migration/reverse migration và frontend build test; **sau khi chạy thật** ghi lệnh vào `docs/operations/LOCAL_SETUP.md` và checkpoint vào `CURRENT_STATE.md` |
| KT-002 | Schema UUID: **CaptureEvent**/Item/Source/Asset/StorageLocation, Topic/Project/Tag, **RelatedItem**, Job/DerivedContent | Giờ server/raw input bất biến, Item.saved_at từ Event đầu, idempotency unique; provenance và manual/pinned, Drive ID không làm PK |
| KT-003 | Google OAuth `drive.file`, tạo folder, reconnect khi `invalid_grant` | Giữ OAuth project/client ổn định; upload ảnh/PDF thật và đọc lại được; không lộ token |
| KT-004 | `DriveStorage` adapter và FakeStorage test | `save/open/stat/verify`; không có B2 code |
| KT-005 | Upload resumable, status rõ, thử pre-generated ID cho blob | Timeout không tạo hai Drive file; xác nhận file thật |
| KT-006 | UI Thêm URL/chữ, **Lịch sử theo CaptureEvent**, Thư viện theo Item, Chi tiết/Cài đặt, Django Auth | ACK/giờ server rõ; ghi chú nguyên văn, xem từng lần gửi lại link mà không nhân đôi card thư viện; Android/Windows dùng được |
| KT-007 | JobRepository với lease/retry/idempotency, 1 worker | Kill/restart không mất Item/**CaptureEvent**, không nhân bản Drive asset; Event+Job transaction nhất quán |
| KT-008 | `pg_dump` + JSON portable export mapping Drive ID, bản copy ngoài Drive | Restore DB/manifest mở lại file gốc và nhóm; **sau khi thực hiện kiểm chứng** viết `docs/operations/BACKUP_RESTORE.md`, ghi lệnh/đầu ra và hạn chế tại `CURRENT_STATE.md` |
| KT-009 | Drive metadata và recovery quyền khi di chuyển host/client | Manifest + Drive khôi phục item/file, đổi host giữ Client phải PASS; lập P1 test Client mới cùng Project và Project mới, không mặc định lỗi 404 hoặc xin `drive.readonly` |

| KT-010 | Tạo thumbnail ảnh/video/PDF: **`pypdfium2` render trang đầu PDF**, Pillow **`ImageOps.exif_transpose()` trước resize ảnh Android**; lưu WebP/JPEG trong cache bền vững | PDF lỗi/khóa có placeholder; test đủ **8 EXIF Orientation**, không thay đổi ảnh gốc Drive; thumbnail đúng chiều, lazy load, không dùng trực tiếp Drive `thumbnailLink`, cache bị mất có thể tái tạo |

| KT-011 | **CaptureService**, `POST /api/v1/captures`: URL/chữ, transaction Event/Item/Job, ACK giờ server, idempotency, xử lý link trùng | N01–N05, N13–N15 theo [CAPTURE_AND_ORGANIZE.md](CAPTURE_AND_ORGANIZE.md); text không tạo asset giả, giờ không đổi sau job/retry/restore |

**Gate A:** Receipt giờ server/URL/text bất biến, gửi lại URL khác HTTP retry, plain note không Drive asset, file thật lên Drive được verify, backup/restore Event/Item/mapping và restart worker đúng.

## 3. Mốc B — Tự động tổ chức, tìm kiếm

| ID | Công việc | Điều kiện PASS |
| --- | --- | --- |
| KT-101 | Link/video ingest và yt-dlp + ffprobe, lưu nguồn | Tải thành công khi có thể; video lỗi vẫn còn link và trạng thái |
| KT-102 | Trích PDF/DOCX/XLSX/HTML/phụ đề; **benchmark 3 thư viện `pypdf` / `pypdfium2` / `PyMuPDF` trên 20–30 PDF tiếng Việt** | Đo dấu Unicode/độ chính xác, thứ tự đọc, trang/locator, RAM, thời gian, license và fallback; chốt extractor chữ dựa evidence. **KT-010 dùng `pypdfium2` thumbnail không phụ thuộc kết quả benchmark**; DerivedContent có version/hash |
| KT-103 | Topic/Project/Tag many-to-many; **OrganizationService tự gán nhóm đang có** nếu đủ tin cậy; origin/confidence/method/user_pinned | Tự ghi quan hệ nhóm, không chỉ suggestion; không gán Project vô căn cứ, không tạo nhóm tràn lan, không sửa nhóm curated; N09–N11 |
| KT-104 | PostgreSQL `SearchService`: `kt_vi` + unaccent/simple/pg_trgm; **hai expression GIN index riêng trên `Item` và `DerivedContent`**, lấy ứng viên cho auto-group và RelatedItem | Migration đúng token config; `SearchVector`/`SearchQuery` khớp GIN từng bảng; tìm từ hai nguồn và hợp nhất `item_id`, lọc DerivedContent hiện hành/stale, lấy snippet/locator. Test sửa note/title, cập nhật text, dấu/không dấu, `đ/Đ`, số hiệu văn bản, `EXPLAIN ANALYZE`. Không dùng JOIN expression index hoặc một vector tổng hợp quá lớn |
| KT-105 | PWA Android Share Target smoke (nếu hỗ trợ) và fallback dán link | Share từ FB/TikTok/YouTube thử thực tế, không hứa kết quả chưa thử |
| KT-106 | Reconcile Drive rename/delete/modified file | Không hiển thị file mất quyền là “đã lưu”; DerivedContent stale khi thay nội dung |
| KT-107 | Đánh giá **auto-group và RelatedItem** với 30–50 mục thực có đánh giá thủ công; AI có cost cap/cho phép tắt | Precision/coverage/false-auto-assign, Project sai, tỷ lệ unclassified, related precision/candidate recall; ngưỡng từ số đo thật |
| KT-108 | Thử tải nhiều loại file, trạng thái lỗi, bộ lọc và thay đổi có dấu | Cụm test nghiệp vụ B PASS |
| KT-109 (có điều kiện) | Thử Drive preview video và cache phát ngắn hạn | Đo playback sau upload; nếu cần giữ cache local có TTL, hạn ngạch, cleanup và quyền truy cập; không mặc định 24–48h/2GB |
| KT-110 | **RelatedItem**: tìm mục tương tự qua SearchService, lưu cặp unique có reason/confidence/version, hiển thị ở Chi tiết | N06/N12/N16/N17: hai note tương tự vẫn hai Item, xử lý stale, metadata không chứng minh hiểu video, test lexical recall |

**Gate B:** Tự xếp đúng **nhóm đã có** khi đủ tin cậy, thiếu thông tin thì Chưa phân loại/Đề xuất, không sửa pinned/manual; có RelatedItem kèm lý do, tìm theo giờ CaptureEvent, nhóm/dự án/tag, nguồn đã lưu có thể mở.

## 4. Mốc C — Tích hợp ChatGPT (KHÔNG xây mặc định)

### KT-113 — cây kho tri thức và nguồn minh họa (19/11/2026)

Kiểm cây nhiều tầng, đổi tên/chuyển nhánh, cycle/owner/CSRF, count và lọc toàn
nhánh không nhân Item. Gán một bài vào nhiều nhánh, bảo toàn pinned; đường dẫn
đi theo bản xuất và backup/restore. Gắn URL vào bài giữ note/giờ gốc; nguồn được
trích text vào phần đọc, lỗi phải hiện rõ. Bỏ chỉ số tương tác từ dữ liệu nguồn.
Video có lời nói chuyển thành transcript timed cục bộ, hash/version/idempotency/
lease và lỗi/timeout được kiểm; có nhãn tự động cần rà soát. Nghiệm thu bằng
Reel đã giao và bài công khai, không suy fixture thành chất lượng ngữ nghĩa.

### KT-112 — văn bản/Markdown là nội dung chính (người dùng chốt 19/11/2026)

Nhận bài Markdown trong luồng text hoặc file, hiển thị có cấu trúc ngay trong
thư viện/Chi tiết, chỉnh sửa nguyên văn và tìm kiếm được; nguồn/media đứng sau
phần tri thức. Không tự ghi đè bài người dùng bằng DerivedContent. Kiểm HTML/
URL độc hại, Unicode/xuống dòng, import retry không nhân Item/CaptureEvent,
không ghi đè chỉnh sửa và `.md` UTF-8 được trích vào search có nguồn/version.
Nghiệm thu thực bằng bài công khai đã biên soạn trong kho đang dùng; fixture
thử riêng không thay bước này. Bản xuất Drive vẫn một Item/một tệp có version.

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
| U19 — Lịch sử bất biến | KT-002/006/011 Gate A | Event giờ server không đổi; Item.saved_at đầu tiên; gửi lại tạo Event mới, worker/restore không sửa giờ; N01/N04/N13/N14 |
| U20 — HTTP retry vs gửi lại | KT-007/011 Gate A | Cùng idempotency key trả Event cũ; lượt gửi mới tạo Event mới nhưng Item/asset không nhân bản khi xác thực cùng nguồn; N04/N05 |
| U21 — Note và link lỗi | KT-006/011/101 Gates A/B | Note nguyên văn không Drive asset; URL private/404 giữ Event, AI tắt vẫn lưu; N03/N07/N08/N15/N16 |
| U22 — Tự gán nhóm | KT-103/107 Gate B | Auto-assignment **thật** vào nhóm đã có, Project có chứng cứ, không ghi đè pinned/manual; N09–N11 |
| U23 — Item liên quan | KT-104/107/110 Gate B | RelatedItem unique + reason/version, không auto-merge note, đo recall/precision; N06/N12/N17 |

**Không ngụy tạo U09–U13 đã PASS ngay từ đầu.** Chỉ thiết kế ID và cổng interface để sau có đường thực hiện.

### Cổng nghiệp vụ v4.7

**17 ca N01–N17 tại [CAPTURE_AND_ORGANIZE.md](CAPTURE_AND_ORGANIZE.md)**: Gate A kiểm N01–N05, N13–N15; Gate B N06–N12, N16–N17. PASS/FAIL/NOT_RUN chỉ dựa test thật gắn SHA, không dựa commit tài liệu.

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

- Tại **baseline 18/11/2026**, repo mới chỉ có tài liệu: chưa có app, database thật, Google OAuth credential, deployment hoặc runtime PASS. Trạng thái sau baseline phải tra `CURRENT_STATE.md` và GitHub live, không mặc định câu này đúng mãi.
- Mỗi nhiệm vụ khi hoàn tất phải có commit SHA, test đã chạy, test chưa chạy, rủi ro, rollback.
- Trước khi chọn/thay công nghệ, so với **2–3 lựa chọn cạnh tranh**, nêu vì sao phù hợp với Kho Tri Thức hiện tại và bảo đảm đường nâng cấp.
- Đừng biến một bài nghiên cứu tương lai (pgvector, Drive migration) thành blocker của bản đầu.
- **PostgreSQL là lựa chọn đã chốt**. Bản đầu không chạy SQLite thay thế; `KT-010` dùng `pypdfium2` render PDF và xử lý EXIF, `KT-102` chỉ quyết parser chữ sau benchmark 3 lựa chọn; `KT-104` dùng **hai GIN index riêng** qua `SearchService`. KT-202E chỉ là pilot, không cam kết toàn bộ Drive được ChatGPT lập chỉ mục.

**Thứ tự ưu tiên:** **nhận URL/chữ và giữ giờ/đầu vào không mất** → Drive lưu file khi có → **tự nhóm và tìm Item liên quan** → ChatGPT nghiên cứu → nâng cấp.

## 9. Các task giao AI sau khảo sát 17 ứng dụng — 20/11/2026

**Nguồn chuẩn triển khai:** [INDEX KT-114–KT-121](workstreams/notes-ux-20261120/INDEX.md) — có prompt một dòng, phạm vi file/độc lập và evidence/PR G00. **Task chưa giao hoặc chưa chạy = NOT_RUN**, không suy khảo sát thị trường là đã implement. Ưu tiên **CORE GATE** của hệ thống khác với **UX-P0** trong riêng nhóm cải tiến giao diện.

| Task | Chức năng/đầu ra chính | Thứ tự/điều kiện | Acceptance và nơi đo |
| --- | --- | --- | --- |
| **KT-114** [Core readiness](workstreams/notes-ux-20261120/KT-114-READINESS.md) | Script/fixture kiểm Drive integrity, restore, nguồn và quy mô Item; báo cáo giới hạn | **CORE, trước phát hành/nhập lớn**, có thể làm cùng PoC UI độc lập | 10.000 Item **fixture ở DB test**, count distinct, Event new vs retry, SHA/restore trong phạm vi được phép; 100GB/Android thật không chạy => NOT_RUN |
| **KT-115** [Markdown editor](workstreams/notes-ux-20261120/KT-115-EDITOR.md) | Chọn phương án sau 3-way comparison; PoC Edit/Split/Read, giữ raw `Item.note` | UX-P0, không phá CORE | 40/40 Markdown Unicode/GFM sau save/reload, IME, undo, XSS; không chuyển toàn bộ sang HTML |
| **KT-116** [Source locators](workstreams/notes-ux-20261120/KT-116-LOCATORS.md) | Citation → PDF page/web section/audio-video time khi có locator và byte stream | UX-P0; cần asset+permission+viewer thật | 30/30 mapping đúng; seek video sai lệch <=1 s với thiết bị/codec/HTTP Range có evidence; không đủ => NOT_RUN |
| **KT-117** [Quick capture Android](workstreams/notes-ux-20261120/KT-117-QUICK-CAPTURE.md) | Hoàn thiện PWA share **đã có**, giữ draft/receipt, test Android | CORE Android + UX-P0 | 30/30 share text/link Unicode; gửi mới +1 Event/retry +0; thiết bị thật không có => ANDROID_NOT_RUN |
| **KT-118** [Multi-view](workstreams/notes-ux-20261120/KT-118-LIBRARY-VIEWS.md) | List/Table/Card/Timeline là các projection cùng Item UUID và tree filter | UX-P1; sau data contract ổn | Các tập distinct Item ID theo view/filter giống nhau trên corpus có nhiều nhánh, paging ổn; đo với 10k fixture |
| **KT-119** [Related/backlinks](workstreams/notes-ux-20261120/KT-119-RELATED.md) | Phân biệt explicit backlinks, RelatedItem có reason, same-group, source cards | UX-P1, không auto merge, không graph DB | Fixture 30 Item có link và reasons; 100% liên kết được đối chiếu có quyền/nguồn; thiếu nhãn → NOT_RUN |
| **KT-120** [AI diff review](workstreams/notes-ux-20261120/KT-120-AI-REVIEW.md) | Suggestion versioned, diff/accept/reject, không tự PATCH note | **HOLD** tới khi người dùng giao và cho phép model/chi phí | 20/20 case reject không đổi note; provider thật chưa có => NOT_RUN |
| **KT-121** [Templates](workstreams/notes-ux-20261120/KT-121-TEMPLATES.md) | Template Markdown/type metadata nhẹ | **HOLD**, UX-P2 | 3 mẫu × 10 Item, stable ID và restore raw note; không đòi schema graph |
| **KT-122** [Folder + notes mixed explorer](workstreams/notes-ux-20261120/KT-122-FOLDER-EXPLORER.md) | Cây chung thư mục/ghi chú, tạo note trong folder, move/add shortcut không duplicate Item | **CORE UX / HIGH**; base trên PR #57 chưa merge | 10.000 Item fixture/lazy, một note ở 3 folder vẫn 1 UUID, 10 lần tạo note có receipt hợp lệ, thử keyboard/drag/drop/cycle/backup |
| **KT-123** [Note hierarchy](workstreams/notes-ux-20261120/KT-123-NOTE-HIERARCHY.md) | Directed Note→Note cha–con tách khỏi RelatedItem/backlink, outline Heading trong note | **CORE UX / HIGH**; phụ thuộc API/UX explorer KT-122 | 30 tests owner/cycle/lock/concurrent; parent-child trong giao diện, export/restore edges không mất; không tự suy relation từ AI |

**Ràng buộc chung khi chấm PASS:**
1. Có **Code SHA, Tested SHA, environment, command, expected vs actual, PASS/FAIL/NOT_RUN, rollback**, kiểm diff/branch/PR. Nếu chỉ có script/test mock, kết quả chỉ là MOCK_PASS trong phạm vi đó; thử Android thật, Drive thật hoặc 10.000 mục trên DB thật cần ghi riêng.
2. `npm test` theo package tại ngày 20/11/2026 chỉ chạy `apps/web/tests/ui.test.mjs`. Agent thêm test `tests/ktXXX-*.test.mjs` phải **chạy tường minh** `node --test` và nói runner chung chưa bao gồm; G00 review tích hợp runner.
3. Nhiều AI song song không cùng sửa `CURRENT_STATE.md`, `api.ts`, `styles.css`, test runner hay chung file của task khác; G00 tích hợp khi PR sẵn sàng. Không tự merge PR nghiên cứu.
4. **Đo tỷ lệ cần mẫu số**: `precision = correct / audited`; `false_assignment_rate = wrong / audited_auto_assignments`; `seek_error_s = abs(actual-target)`; `result_count = COUNT(DISTINCT item_id)`. Nếu mẫu số 0, không tính 0% hay 100%, ghi **NOT_RUN** và nguyên nhân.
5. **Giữ dữ liệu gốc**: file Drive và metadata, `CaptureEvent`, `Item.note`, `user_pinned`; không nhân bản Item theo view hoặc chuyển ASR/AI suggestion thành bản người viết.

**Các điều chỉnh sau rà soát lần hai:** Capacities audio recording/transcribe/summary đã phát hành theo gói Pro (11/2026), Reflect Open có Windows/Linux experimental unsigned, Android chưa hỗ trợ; không sao chép thông tin cũ nói “audio coming soon” hay “Reflect không có Windows”. Các ghi nhận này chỉ là nguồn tham khảo UX, không phải lý do thay nền tảng hoặc mua license.

**Trạng thái ban đầu toàn bộ KT-114–KT-121:** `DOCS_READY / IMPLEMENTATION_NOT_RUN`. Đến khi AI khác thực sự chạy, không ghi PASS vào [CURRENT_STATE.md](CURRENT_STATE.md).

## 10. G00 bổ sung thiếu sót thiết kế Obsidian-style — 20/11/2026

Người dùng yêu cầu **tổ chức folder như Obsidian và mối quan hệ cha–con của cả thư mục lẫn nội dung**. Đây là khoảng trống mà KT-114–121/PR #57 chưa khép lại: cây `Topic.parent` lưu folder→folder, `ItemTopic` lưu folder→note, nhưng UI `KnowledgeTree` **chỉ render folder**; `RelatedItem` là gợi ý tương đồng (undirected unique pair), chưa có **note→note directed parent**. Trong PR #57, LibraryViews list/table/card/timeline chỉ thay cách xem danh sách, không phải explorer hỗn hợp. Task [KT-122](workstreams/notes-ux-20261120/KT-122-FOLDER-EXPLORER.md) giải quyết file explorer, [KT-123](workstreams/notes-ux-20261120/KT-123-NOTE-HIERARCHY.md) giải quyết cấu trúc bài. Hai mã này **SPEC_READY/IMPLEMENTATION_NOT_RUN**; không được gắn PASS từ CI #57.

**Ưu tiên:** giải quyết KT-122/123 trước khi tuyên bố UI tổ chức tri thức đạt yêu cầu người dùng, nhưng **không tự chặn** mọi kiểm thử dữ liệu độc lập và không thay thế gate Drive/Android. Codex chạy branch riêng từ HEAD `codex/notes-ux-integration`, tạo PR target branch integration để G00 review, **không merge/deploy**. Số liệu test, migration/backup, tham chiếu UUID và không mất dữ liệu gốc đều phải được kiểm chứng thực.
