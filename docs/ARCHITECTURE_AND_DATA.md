# KIẾN TRÚC, DỮ LIỆU VÀ LỘ TRÌNH NÂNG CẤP — V4.7 (CAPTURE VÀ TỰ TỔ CHỨC)

**Ngày:** 18/11/2026 · **Dựa trên:** `MASTER_PLAN.md` v4.7 · **Đối tượng:** một người dùng lúc đầu, Google Drive là kho file chính; phát triển thêm tính năng AI và có thể nhiều dữ liệu/worker về sau.  
**Trạng thái:** quyết định thiết kế, **chưa triển khai hoặc benchmark** tại baseline 18/11/2026. Trạng thái thực tế sau này xem [CURRENT_STATE.md](CURRENT_STATE.md); cách bố trí tệp và ranh giới Git/Drive/runtime xem [REPOSITORY_LAYOUT.md](REPOSITORY_LAYOUT.md). Mọi số liệu hiệu năng và điều kiện nâng cấp dưới đây là mục tiêu/trigger để đo, không phải kết quả đo.

## 1. Quyết định về mức độ thiết kế

### 1.1. Quy tắc cân bằng

- **Thiết kế ngay**: định danh, model dữ liệu, hợp đồng API, ranh giới đọc/ghi Drive, bản gốc vs dữ liệu trích xuất vs chỉnh sửa người dùng, giao diện tìm kiếm, idempotent job, backup/restore.
- **Lập trình ngay**: một Django monolith, PostgreSQL một máy, một worker, một Drive adapter, thư viện PWA, tìm kiếm từ khóa, trích xuất nhẹ.
- **Chưa lập trình**: B2/R2 adapters, bảng embeddings, OCR/ASR, Redis, Procrastinate, MCP server, hệ thống đa người dùng đầy đủ, streaming/CDN, OCR/Playwright workers, microservices.
- **Không bảo đảm bằng suy đoán**: quota Drive, video từ cloud IP, Share Target Android, chất lượng AI tiếng Việt, khả năng ChatGPT đọc từng định dạng file. Đều có test gate.

### 1.2. Bảng quyết định đã đối chiếu phương án thay thế

| Phần | Lựa chọn | 2–3 phương án khác | Lý do phù hợp hiện tại **và** tương lai |
| --- | --- | --- | --- |
| Kho file | **Google Drive/My Drive** | Backblaze B2, Cloudflare R2, Dropbox | Người dùng đã có 500 GB và quen thao tác Drive; lưu file gốc trực tiếp, ChatGPT có app Drive. Thêm nhà cung cấp sau qua adapter, không ép mua B2/R2 |
| Drive integration | **Drive API v3 + OAuth `drive.file`** | rclone, Apps Script, service account | Ghi chính xác file ID/metadata, resumable upload, đọc/xác minh khi có lỗi; Apps Script không chạy yt-dlp, rclone dùng tốt cho backup, service account không sở hữu quota My Drive cá nhân |
| CSDL chính | **PostgreSQL local container — ĐÃ CHỐT** | SQLite + FTS5, Supabase Postgres, Google Sheets | Người dùng chọn PostgreSQL. Dùng cùng một CSDL cho local/prod, search và worker, tránh migration SQLite→PostgreSQL; không cần managed DB riêng |
| Backend | **Django 5.2 LTS + Django Ninja** | Django 6.1 + Ninja, FastAPI, Django + DRF | LTS hỗ trợ tới 04/2028, auth/admin/migrations sẵn, Ninja có OpenAPI; thuận đường lên Django 6.2 LTS. FastAPI mạnh nhưng thêm bộ phận auth/admin/ORM; DRF nặng hơn cho API nhỏ |
| Frontend | **React + TypeScript + Vite** | Django + HTMX, Vue 3, SvelteKit | Lọc nhiều điều kiện, upload/preview, PWA responsive; static deploy và API độc lập cho Android native sau. Không cần Next SSR hoặc server Node production |
| UI | **Mantine** | shadcn/ui, MUI, Ant Design | Nhiều biểu mẫu/multiselect/date/filter sẵn, giúp Codex ra UI nhanh. Không trộn hai UI framework khi chưa có lý do |
| Search | **Hai nhóm GIN index riêng cho `Item` và `DerivedContent`** qua `SearchService`, dùng `kt_vi`/unaccent/pg_trgm | Một `Item.search_vector` tổng hợp; Typesense; Meilisearch | Không lập expression index xuyên bảng; tách metadata và văn bản dài để tránh xây lại vector khi sửa note, giữ locator trích xuất và mở đường OCR/ASR |
| Queue | **PostgreSQL `jobs` + 1 worker** | Procrastinate, Chancy, Celery+Redis | Vẫn gọn khi ít tác vụ; bảng job có lease/retry/idempotency, về sau worker tăng được. Không viết framework queue chung đa năng; nếu vượt khả năng, thay worker adapter |
| AI phân loại | **Rule-based + `ClassifierPort`**, provider sau benchmark | Gemini Flash-Lite, OpenAI model nhỏ, model local | Không khóa nhãn đã chốt với output AI; thay model/prompt mà không xáo dữ liệu |
| Parsing/thumbnail PDF | **`pypdfium2` render thumbnail PDF, `pypdf` baseline text extraction**; python-docx, openpyxl, Trafilatura | PyMuPDF, Docling, LibreOffice/Crawl4AI | `pypdf` không render PDF; KT-102 so 3 thư viện pypdf/pypdfium2/PyMuPDF trên tiếng Việt và giấy phép trước khi chọn extractor chữ chính |
| Video | **yt-dlp + ffprobe/FFmpeg** | Cobalt, gallery-dl, Streamlink | Đã có benchmark tương đối, xử lý nhiều nguồn, fallback link-only; giao downloader qua interface để không phụ thuộc một extractor |
| Auth app | **Django Auth một account + HTTPS** | Google login/OIDC, Auth0, Keycloak | Không cần đa role, dịch vụ identity; chỉ giữ token Drive phía backend, chuẩn bị `owner_id` nếu về sau nhiều user |
| ChatGPT | **Thử Google Drive app + bản xuất tri thức từ PostgreSQL** | MCP custom, gửi file bằng tay, GPT Actions | Connector không thấy PostgreSQL; pilot per-item text/Google Docs/TXT/Markdown đồng bộ theo phiên bản. Nếu không đọc được ổn định thì dùng MCP read-only, không giả định 100% |
| Triển khai | **Docker Compose một máy**: Django/API, Postgres, worker, HTTPS/static | systemd+venv, Railway/Render, Kubernetes | Có thể clone/chạy ở Windows qua Docker và chuyển VPS ít sửa; số dịch vụ tối thiểu. Không cần k8s |
| Backup | **pg_dump + export JSON/manifest + bản sao ngoài Drive** | snapshot máy chủ, R2/S3, Google Takeout | Phục hồi được metadata lẫn mapping Drive file; mất một máy chủ vẫn restore được. Không cần multi-cloud đồng bộ mọi media v1 |

**Tiêu chí đánh giá:** mức phù hợp 30%, đơn giản/bảo trì 25%, chi phí 20%, độ tin cậy 15%, chuyển đổi 10%. Trọng số chỉ là cách tranh luận, không tạo điểm số ảo.

### 1.3. Vì sao không giữ SQLite cho dữ liệu thật?

SQLite là lựa chọn hợp lý cho một prototype không cần server. Nhưng khi đã có **tác vụ tải/upload chạy nền, người dùng sửa phân nhóm, tìm kiếm trong extracted content, cần khả năng AI vector/MCP và kế hoạch sử dụng lâu dài**, việc đổi database sau đó có thể khiến phải chuyển FTS5, schema, job SQL, indexes và các test. Django cũng ghi rõ SQLite production có giới hạn migration/concurrency, và khuyến nghị PostgreSQL. Một container PostgreSQL dùng chung Docker Compose là **đầu tư kỹ thuật nhỏ nhưng giảm đáng kể chi phí đổi sau**.

**Không đồng nghĩa** phải cài Redis, Elasticsearch, pgvector hoặc Kubernetes. **Quyết định PostgreSQL đã được người dùng chốt cho cả local dev lẫn production.** Không triển khai SQLite làm DB thay thế, không có hai schema/backend song song.

## 2. Sơ đồ hệ thống

```text
PWA React (Android + Windows)
      |
      v
HTTPS / static + /api/v1/
      |
Django 5.2 LTS + Ninja
    +-- Auth / Items / Groups / Projects
    +-- CaptureService -> CaptureEvent -> Item/Source + JobRepository
    +-- IngestionService -> JobRepository
    +-- LibraryService -> Item, Source, Asset
    +-- SearchService -> Postgres full-text/trigram
    +-- StoragePort -> DriveStorage (OAuth drive.file)
    +-- ExtractionService -> DerivedContent (versioned)
    +-- ClassificationPort -> rules / AI provider
    +-- OrganizationService -> existing Topic/Project/Tag and RelatedItem
    +-- KnowledgeExportService -> Drive knowledge index (P1, pilot)
      |
PostgreSQL (metadata, relations, statuses, extracted text, versioned exports)
      |
One background worker (same Django source)
   yt-dlp / ffprobe -> temp file -> Drive upload -> verify
   PDF/DOCX/XLSX/HTML/subtitles -> extracted text -> index
      |
Backup: pg_dump + portable JSON/manifest -> Drive + PC copy

Future adapter only:
  StoragePort -> B2 / R2
  SearchService -> pgvector / search engine
  ReadKnowledgeService -> MCP read-only
  ProcessingPort -> OCR / ASR / vision workers
```

Frontend không chứa Google token. Dùng HTTP API có version và Django services; không gọi Google API tùy tiện từ view/controller khắp nơi.

## 3. Data model tối thiểu nhưng không khóa nâng cấp

Bảng nghiệp vụ **được phép tạo từ đầu**; chỉ làm CRUD khi có yêu cầu. “Tối thiểu” nghĩa là chưa tạo dữ liệu giả/CRUD cho embedding, không phải gộp tất cả thành một bảng.

| Model | Trường quan trọng | Cơ sở quyết định lâu dài |
| --- | --- | --- |
| `User` | id/email/login | Đăng nhập một người, FK/owner_id có thể dùng khi mở multiuser |
| `Item` | `id UUID`, owner_id, kind, title, description, note, saved_at, published_at nullable, favorite, deleted_at, user_edit_version, classification_status | Tri thức độc lập vị trí lưu; saved_at = thời điểm tiếp nhận **đầu tiên** của Item |
| `Source` | id, item_id, original_url, canonical_url, platform, platform_id nullable, captured_at, published_at nullable, source_metadata | Nguồn gốc có thể gắn nhiều URL vào Item; ngày đăng nguồn khác ngày gửi |
| `CaptureEvent` (P0) | id UUID, item_id, owner_id, source_channel, raw_kind, raw_text/original_url, server_received_at, client_sent_at nullable, idempotency_key, status | **Một lần gửi thực sự là một Event**; giờ server/raw input bất biến; gửi lại URL tạo Event mới, retry cùng key trả Event cũ |
| `Asset` | `id UUID`, item_id, role, mime, size, sha256, original_filename, content_version | File gốc/thumbnail/derivative được phân biệt |
| `StorageLocation` | id, asset_id, `provider='google_drive'`, provider_file_id, status, verified_at, provider_revision | Chỉ có 1 location lúc đầu; thêm location không sửa Item |
| `Topic` | id, parent_id nullable, name, archived | Lĩnh vực root/chủ đề con |
| `Project` | id, name, description, archived | Khác chủ đề, là công việc/dự án |
| `Tag` | id, name | Nhãn tự do |
| `ItemTopic / ItemProject / ItemTag` | item_id, reference_id, origin, user_pinned, confidence nullable, method_version nullable, source_version nullable | Tự gán nhóm **thực sự**, có nguồn/cơ sở; AI không ghi đè nhóm thủ công |
| `RelatedItem` | item_a_id, item_b_id, relation_type, confidence nullable, method_version, source_version, reason, status | Cặp hai Item khác nhau, thứ tự canonical và unique; **liên quan không tự đồng nhất/gộp dữ liệu** |
| `DerivedContent` | id, asset_id/item_id, type, text/ref, source_locator, processor, processor_version, input_hash, status, created_at | Text PDF/web/subtitles hiện tại; OCR/ASR phiên bản sau |
| `Job` | id, kind, item_id nullable, idempotency_key, state, attempt, lease_until, retry_at, error_code, input_ref | Không mất tác vụ; mở rộng worker sau |
| `DriveAccount` | user_id, google_sub, root_folder_id, oauth_state, connected_at | **Token lưu riêng và được bảo vệ**, không nằm trong record xuất công khai |
| `ExportRecord` (mức gọn) | id, file_ref, schema_version, sha256, created_at | Theo dõi bản portable export/restore |
| `KnowledgeExport` (**chỉ tạo khi pilot ChatGPT được triển khai**) | item_id, exported_drive_file_id, source_version, exported_version, content_hash, status, last_synced_at, error_code | Một file văn bản đại diện cho một item, update cùng file; phát hiện stale và retry idempotent |

**Chưa tạo:** EmbeddingModel, ChunkEmbedding, Claim/Evidence, KnowledgeGraph, nhiều quyền người dùng, chat history, AI execution logs lớn. Khi thêm chúng chỉ FK vào Item/Asset/DerivedContent hiện có.

### 3.1. Quy tắc bất biến

- `item_id` và `asset_id` là UUID; **không dùng Drive ID, URL, tên file làm primary key**.
- `drive_file_id` là thuộc tính của `StorageLocation`, không hiện diện khắp code nghiệp vụ.
- Ngày hệ thống UTC/timezone-aware, hiển thị Asia/Bangkok (UTC+7); `published_at` thiếu thì NULL, không suy đoán. **`CaptureEvent.server_received_at` bất biến; `Item.saved_at` lấy từ Event đầu tiên, không sửa bởi gửi lại, AI/worker/restore**.
- Dữ liệu người dùng sửa là **curated**, không đồng nhất với AI suggestion; lần xử lý lại không thay ngầm. **Ghi chú thuần chữ là Item riêng, giữ nguyên văn; nội dung gần giống thì tạo RelatedItem, không auto-merge**.
- Dữ liệu trích xuất giữ `input_hash` + `processor_version`. Khi file trên Drive đổi nội dung thì đánh dấu stale hoặc tạo bản mới, không khẳng định văn bản cũ còn đúng.
- Nguồn bị xóa/mất quyền vẫn giữ metadata và trạng thái `missing/inaccessible`, không xóa Item không hỏi.

### 3.2. Drive metadata giúp phục hồi khi database mất

- Khi upload blob, có thể lưu `item_id`/`asset_id` vào `appProperties`; vì trường này gắn với OAuth client, **không coi là bản sao duy nhất**.
- Với ID không nhạy cảm, cân nhắc thêm `properties` công khai tối thiểu để có thể phục hồi khi thay OAuth client, nhưng kiểm thử với Google API và không lưu ghi chú cá nhân trong properties.
- Bắt buộc lưu portable manifest có `schema_version` gồm item, file, Drive ID, checksum, nguồn, nhóm, ghi chú, trạng thái; có thể tái nhập database từ manifest.
- Trường `contentHints.indexableText` của Drive có thể cải thiện tìm file không có văn bản khi cung cấp nội dung đại diện ngắn; **không thay cho database full-text hoặc cam kết ChatGPT index ngay**.

## 4. Google Drive adapter và đồng bộ hai chiều tối thiểu

### 4.1. Interface không overengineer

`StoragePort.save(asset, stream) -> StorageLocation`  
`StoragePort.open(asset, user) -> viewer_url / stream`  
`StoragePort.stat(asset) -> status/size/modifiedTime/checksum`  
`StoragePort.delete_or_trash(asset)`  
`StoragePort.verify(asset) -> verification_result`

Bản đầu chỉ viết **DriveStorage**, còn FakeStorage in-memory phục vụ unit test. Không viết factory/worker đa cloud hoặc migration tool sớm.

### 4.2. Drive OAuth và upload

- Scope `drive.file` đủ cho file do app tạo/file được user mở có chủ đích; muốn import file Drive có sẵn ngoài phạm vi này phải có Picker/thủ tục cấp quyền. **Nếu đổi OAuth Client/Google Cloud Project phải test lại quyền**: cùng Client/cùng Project/Project mới có thể hành xử khác nhau, không mặc định luôn 404.
- OAuth External + Testing thường làm refresh token hết hạn sau 7 ngày; lúc triển khai thật cần kiểm tra publishing state và nút kết nối lại khi `invalid_grant`, không hứa refresh token tồn tại mãi.
- Với file >5MB và kết nối không ổn định, dùng **resumable upload**. Google Drive có thể cấp pre-generated file ID cho upload blob để retry sau timeout không nhân file; **không áp dụng cách đó tùy tiện cho Google Docs/Sheets native**.
- Sau mỗi upload, xác nhận file tồn tại, trả Drive file ID và checksum nếu có. Ghi thành công vào DB sau xác minh, không gộp trạng thái `link_saved` với `file_uploaded`.
- Chống hạn mức/429 với backoff; nếu quota tài khoản hết, job chờ hoặc báo, file tạm được giữ có thời hạn để retry.
- Không xây media proxy/phát video nâng cao trước; ưu tiên mở bằng Drive viewer đã đăng nhập, có fallback tải xuống khi preview không đạt. **Trạng thái đã upload thành công không đồng nghĩa video đã sẵn sàng phát trên Drive**. Nếu cần xem ngay, thử cache cục bộ có giới hạn dung lượng/thời hạn, không giữ mọi video mặc định.

### 4.3. Người dùng sửa file ngay trên Drive thì sao?

**Thiết kế từ đầu, triển khai tối thiểu:**
1. Lưu `provider_file_id, modifiedTime, size, checksum/revision`.
2. Khi mở một item: nếu cache quá hạn thì kiểm tra `files.get`; Drive trả 404 phải phân biệt không còn file và không còn quyền.
3. Tác vụ reconcile định kỳ rà các file thuộc folder ứng dụng; đánh dấu rename/move/delete/changed.
4. Khi nhu cầu tăng: chuyển sang **Drive Changes API** và lưu `startPageToken/newStartPageToken`; chưa cần webhook `changes.watch` trong bản đầu.
5. Với thay đổi nội dung: đánh dấu DerivedContent stale, chọn trích xuất lại theo yêu cầu hoặc nền; không ghi đè ghi chú/thông tin người dùng.
6. Với Google Docs/Sheets/Slides native, thiết kế `mime_type` và xử lý qua export/Docs API riêng; không nghĩ blob PDF và Google-native file là cùng một dạng.

## 5. Tách các pipeline xử lý để nâng cấp OCR/ASR/AI

```text
Capture(URL/text) -> transaction: CaptureEvent + Item/Source + Job -> ACK immediately
     -> Link: metadata -> optional Download/Upload/Verify Asset on Drive
     -> Text-only: preserve note verbatim; no Drive asset needed
     -> Extract available PDF/web/subtitles -> DerivedContent [text, locator, version]
     -> Search candidate groups/items -> auto-assign when confident OR suggest/unclassified
     -> RelatedItem with provenance -> Search index (rebuildable)
```

- Mỗi bước idempotent theo `item_id/asset_id + processor_version + input_hash`.
- Trích xuất nặng sau này chỉ là processor mới; không sửa bảng Item hoặc xóa văn bản cũ.
- Video transcript có `timestamp`, PDF có `page`, Excel có `sheet/cell` khi công cụ hỗ trợ; không bịa locator.
- Khi có embedding, tạo **bảng riêng** có `model_id/version/dimension`, không nhét vector vào Item/DerivedContent; có thể lưu nhiều thế hệ vector và switch model sau khi nghiệm thu.
- **OrganizationService tự gán nhóm đang có** nếu đủ tin cậy (không chỉ gợi ý), hoặc đề xuất/đưa vào Chưa phân loại; AI không được sửa nhãn do người dùng chốt. Project cần bằng chứng cụ thể, không suy từ từ khóa chung. Có thể tắt AI ngoài và giới hạn phí. Chi tiết: [CAPTURE_AND_ORGANIZE.md](CAPTURE_AND_ORGANIZE.md).

## 6. Worker và khả năng tăng tải

### 6.1. Phiên bản đầu

- Chạy **một worker** (cùng codebase Django) nhận job qua PostgreSQL `jobs`.
- Trạng thái `queued/running/retry/failed/done`; lưu `lease_until`, `attempt`, `next_retry_at`, `idempotency_key`.
- Giao dịch DB chỉ dùng để claim/complete, **không giữ transaction SQL khi tải/upload media kéo dài**.
- Dùng khóa/lease PostgreSQL có test crash và worker restart; có timeout/download quotas/concurrency giới hạn.
- Sau upload timeout mơ hồ, **phải kiểm tra Drive file bằng pre-generated ID hoặc appProperties** trước khi tạo bản sao khác.

### 6.2. Khi mở rộng

- Nhiều worker cùng process queue qua PostgreSQL lock; job interface không đổi.
- Nếu số job/worker lớn hoặc cần workflow schedule, thử Procrastinate/Chancy rồi migrate worker adapter (không làm trước).
- ASR/OCR có thể chạy worker riêng với CPU/GPU thích hợp, backend API và metadata không đổi.
- Docker Compose vẫn có thể chạy ở một máy; tách worker sang máy khác mới khi đo CPU/RAM thật.

## 7. SearchService và đường lên AI nghiên cứu

- API v1 dùng `SearchService.search(filters, query, cursor)` và `ReadKnowledgeService.fetch(item_id, parts)`. `OrganizationService` dùng ứng viên từ SearchService để tự gán nhóm, tìm và ghi `RelatedItem` có provenance; dữ liệu metadata riêng không đủ kết luận đã hiểu toàn video.
- Version 1 có **hai nhóm GIN index riêng** cho metadata `Item` (title/description/note) và text `DerivedContent` hiện hành. `SearchService` hợp nhất kết quả theo `item_id`, chấm điểm/ranking, lọc Project/Topic/Tag theo bảng quan hệ và giữ provenance/locator. Không tạo expression index JOIN xuyên bảng.
- Migration cần tạo **cấu hình text search `kt_vi` dựa trên `simple`, dùng từ điển lọc `unaccent`** cho các token tiếng Việt. Dùng cùng config cho `SearchVector` và `SearchQuery`, chỉ mục GIN phải khớp với biểu thức/cấu hình. **Không bọc tùy tiện hàm STABLE bằng `IMMUTABLE`**; không nhầm `SearchVectorField` với generated column tự cập nhật. Dùng pg_trgm hoặc phép tìm chuỗi cho số hiệu văn bản/tên viết tắt; đo `EXPLAIN ANALYZE`, bộ truy vấn có dấu/không dấu kể cả `đ/Đ`.
- Khi tăng dữ liệu lớn, có thể thêm Typesense/Meilisearch như backend tìm kiếm nhưng **không làm nguồn gốc dữ liệu**.
- Khi cần semantic/RAG: thêm `EmbeddingModel`, `ContentChunk`, `ChunkEmbedding` riêng; sinh từ DerivedContent có provenance; dùng pgvector hoặc provider khác, đánh giá trước khi chuyển.
- ChatGPT Drive app có thể tìm và làm việc với file Drive nếu workspace hỗ trợ; **không thấy note/DerivedContent/projects chỉ nằm trong PostgreSQL và không hiểu MP4 thiếu transcript**. Thử một tài liệu văn bản đại diện/Item trên Drive rồi mới quyết định có dùng `KnowledgeExportService` hay không. Không cam kết định dạng Markdown/TXT/Google Docs đều được lập chỉ mục. Nếu cần truy vấn tag/project chính xác hoặc pilot không đạt, xây MCP sử dụng chính `SearchService`/`ReadKnowledgeService`.
- Câu trả lời trích nguồn dựa trên `item_id, drive_file_id, page/sheet/timestamp` có thật; file thiếu text phải báo rõ.

## 8. API và frontend: không phải làm lại khi có Android native/MCP

**Versioned REST** `/api/v1/`. Nhóm tối thiểu: 
- **`POST /captures`** nhận URL/text, idempotency key, ACK gồm `capture_id/item_id/server_received_at` sau commit; `GET /captures` và `GET /items/{id}/captures` cho lịch sử. `POST /ingest/links`/`POST /items/notes` chỉ là adapter mỏng nếu giữ API cũ, không có hai quy trình nhận cạnh tranh; `POST /uploads` cho file,
- `GET /items`, `GET /items/{id}`, `PATCH /items/{id}`,
- `GET /search`, `GET /items/{id}/content`,
- `GET /groups`, `POST /groups`, `GET /items/{id}/related`, `GET /items/{id}/organization` (auto-assigned/suggested/unclassified, nguồn quyết định),
- `GET /jobs/{id}`, `GET /assets/{id}/open`,
- `GET /integrations/drive/status`, `GET /integrations/drive/connect`, OAuth callback.

- Không gọi Drive API trực tiếp từ React với token toàn quyền; React chỉ dùng backend API.
- React + Mantine: Thêm, Thư viện, Chi tiết, Tìm kiếm (có thể cùng Thư viện), Cài đặt. **Thumbnail phải qua endpoint/cache nội bộ**, không dùng URL `thumbnailLink` ngắn hạn của Drive trực tiếp cho 30–50 cards.
- Mỗi card/chi tiết hiển thị **trạng thái nhận link / lưu file / trích văn bản / tự phân nhóm** riêng, không chỉ một nút “Hoàn tất”. Có **Lịch sử tiếp nhận theo Event** (mỗi lượt gửi một dòng) và **Thư viện theo Item** (một card/nội dung), lọc theo ngày gửi. Chi tiết Item có nhóm đã gán, đề xuất và mục liên quan.
- Android PWA Share Target thử trên thiết bị thật; fallback dán link là bắt buộc. Nếu về sau cần native push/share thì dùng API sẵn.
- Không làm UI admin đa role, streaming player riêng, thiết kế bảng nhiều trăm cột.

## 9. Triển khai, bảo mật và sao lưu theo mức vừa đủ

- Docker Compose trên 1 máy: `web (Django)`, `worker (same image)`, `postgres` và `caddy/HTTPS` khi có domain, frontend bundle tĩnh. Thêm volume nhỏ cho **cache thumbnail bền vững qua deploy**; đây là cache có thể tạo lại, không phải kho file gốc. Cache video là tùy chọn có quota/TTL sau phép thử.
- Dùng Django Auth một tài khoản, mật khẩu/session/HTTPS, token Drive phía backend; không cần Auth0/Keycloak/RBAC.
- Chuẩn bị `owner_id` ngay trong model để sau có thể cho nhiều người kết nối Drive khác nhau mà không gắn nhầm file.
- Tiền xử lý URL để chống SSRF và không cho worker tự do tải địa chỉ nội bộ; giới hạn tệp, tổng dung lượng temp và timeout.
- `pg_dump` + versioned JSON manifest định kỳ lên Drive, bản tải về Windows hoặc kho khác (độc lập Drive) theo lịch; thử phục hồi từ file dump và manifest.
- Không đưa OAuth token, dữ liệu media cá nhân, backup hoặc file .env lên GitHub; không dùng GitHub Actions làm nơi lưu file video.
- CI tối thiểu: Django migrations/tests + frontend build/typecheck + integration tests với fake Drive; kiểm thử thật trên Drive test folder trước khi bật production.
- Không bật Prometheus/Grafana/Sentry enterprise lúc đầu; log lỗi job, upload, Drive OAuth, backup và cảnh báo khi không thể lưu.

## 10. Kịch bản nâng cấp và chi phí thay đổi

| Kịch bản | Giữ nguyên | Phần bổ sung | Mức độ nếu theo v4.6 |
| --- | --- | --- | --- |
| Drive 500GB hết hạn, cần B2/R2 | Item/Asset/Groups/Search/API | StorageAdapter + move/verify | **Trung bình**, tránh sửa dữ liệu nghiệp vụ |
| Drive file bị xóa/đổi tên thủ công | Item/group/notes | Reconcile, Drive changes feed | **Thấp–trung bình** |
| Thêm OCR/ASR | Originals, asset refs, API | Processor, DerivedContent + search indexing | **Thấp–trung bình** |
| Thêm vector search/RAG | File, text, item ID | pgvector, chunk/model tables, search backend | **Trung bình**, không phải di chuyển DB |
| Tăng số worker | Job schema + ingest flow | Worker concurrency/queue library | **Thấp–trung bình** |
| Thêm ChatGPT MCP | Search/Read services | MCP endpoints + auth/tunnel | **Trung bình**, không làm lại API |
| Thêm Android native | API/services | Capacitor/Flutter/React Native shell | **Trung bình**, không viết lại backend |
| Thêm 2–5 người dùng | owner FK và API | Quyền, per-user Drive connect, UI user mgmt | **Trung bình**, phải thử access boundaries |
| Tăng tới rất nhiều dữ liệu | Postgres | Index/partition/search engine, scaling workers | **Trung bình–cao**, có thể đo rồi làm |
| Đổi Python/Django | Domain services/models | Dependency bumps, migrations và test | **Thấp–trung bình** khi pin LTS |

Các mức là **ước lượng kiến trúc**, không có bảo đảm phần mềm sẽ nâng cấp bằng một nút. Phải viết test với tài liệu và file thật để xác minh.

## 11. Các lỗi v4.3 phải tránh

1. Không nhét trực tiếp `drive_file_id` vào mọi bảng và coi nó là item ID.
2. Không dùng SQLite FTS5 riêng rồi cho rằng chuyển PostgreSQL FTS là tự động.
3. Không ghi đè output AI lên ghi chú và nhóm đã do người dùng chỉnh.
4. Không lưu duy nhất danh mục trong DB mà không có portable manifest.
5. Không đặt DB live trong thư mục Drive sync.
6. Không cho file Drive bị sửa mà bản trích xuất tiếp tục được coi là mới nhất.
7. Không xem link đã lưu = video đã tải = file đã sao lưu.
8. Không để job retry tạo file Google Drive trùng do phản hồi timeout.
9. Không hứa Google Drive ChatGPT app tự hiểu phụ đề/video hoặc metadata riêng của ứng dụng.
10. Không mặc định scope `drive.file` xem được mọi file cũ trong Drive.
11. Không code sẵn API/microservices/provider/storage/CDN không dùng.
12. Không yêu cầu bảo mật enterprise nhưng cũng không mở Google OAuth token trên frontend/public endpoint.

## 12. Nguồn kiểm chứng chính thức và điểm phải thử

- Django LTS hỗ trợ tới April 2028 và khuyến nghị PostgreSQL production: https://www.djangoproject.com/download/ · https://docs.djangoproject.com/en/6.0/faq/install/
- Django 5.2 migration và PostgreSQL: https://docs.djangoproject.com/en/5.2/topics/migrations/ · https://docs.djangoproject.com/en/5.2/ref/databases/
- Drive scope `drive.file`: https://developers.google.com/workspace/drive/api/guides/api-specific-auth
- Drive file properties/appProperties: https://developers.google.com/workspace/drive/api/guides/properties
- Drive resumable upload / pre-generated IDs: https://developers.google.com/workspace/drive/api/guides/manage-uploads
- Drive Changes API: https://developers.google.com/workspace/drive/api/guides/manage-changes
- Drive native export và giới hạn: https://developers.google.com/workspace/drive/api/guides/manage-downloads
- Drive error/quota: https://developers.google.com/workspace/drive/api/guides/handle-errors · https://developers.google.com/workspace/drive/api/guides/limits
- OAuth testing 7 days: https://developers.google.com/identity/protocols/oauth2
- PostgreSQL vector sau: https://github.com/pgvector/pgvector
- ChatGPT Drive app: https://help.openai.com/en/articles/10929079-google-drive-app-and-setup-in-chatgpt
- Django Ninja/Mantine/Vite: https://django-ninja.dev/ · https://mantine.dev/ · https://vite.dev/

**Cần thử thật**: Drive OAuth/connections, metadata recovery, upload timeout, sync edits, Django/Postgres restore, tiếng Việt không dấu, video/cloud IP, React PWA trên Samsung/Windows, ChatGPT Drive app theo workspace. Chưa có test nào đã được thực hiện trong repo này.


## 13. Điều chỉnh sau phản biện kỹ thuật (R2) — không mở rộng hệ thống vô ích

### 13.1. Đồng bộ văn bản tri thức cho ChatGPT: pilot trước, sản xuất sau

**Khoảng trống thật:** Google Drive app không tự thấy `Item.note`, `DerivedContent.text`, Project/Topic/Tag trong PostgreSQL. Một MP4 trên Drive cũng không có nghĩa ChatGPT đã nghe/xem được nó.

**Đề xuất tối thiểu:** `KnowledgeExportService` xuất **một file đại diện cho mỗi Item** lên thư mục `Kho Tri Thuc/ChatGPT_Index` theo phiên bản. Chỉ nội dung có thật: ID/tiêu đề, nguồn + link file, lĩnh vực/chủ đề/dự án, ghi chú, văn bản web, phụ đề/transcript khi có, thời điểm cập nhật. Giới hạn kích thước; văn bản rất dài được chia/trích rõ ràng, không khẳng định đã xuất đủ khi bị cắt. **Đừng tự tạo thêm một bản tổng hợp cho mọi dự án nếu chưa có yêu cầu**.

- **Pilot 5–10 Items**: tạo lần lượt Markdown, TXT và Google Docs; kiểm tra trên chính Google Drive app của ChatGPT được phép dùng. Ưu tiên định dạng có kết quả thực tế tốt nhất, không mặc định mọi file được lập chỉ mục/đọc.
- Khi bật: mỗi Item có `source_version/content_hash`, `exported_version`, `exported_drive_file_id`, `sync_status`, `last_synced_at`. Tạo file một lần; các lần thay đổi *update cùng file*, dùng job idempotent, debounce sửa liên tiếp; chỉ báo synced sau Drive xác nhận.
- Khi bản xuất cũ hơn PostgreSQL, hiện trạng thái **chưa đồng bộ** trong Settings/job; không ngầm xem Drive là nguồn chân lý. Nếu xóa mềm, xử lý trạng thái bản xuất theo quy tắc nhất quán để ChatGPT không tiếp tục đọc nhầm bản đang bị xóa.
- Không gửi thông tin nhạy cảm/secret lên index; dữ liệu người dùng đã cho phép xuất. Video không có phụ đề phải ghi **chưa có transcript**, không tự diễn giải nội dung.
- Nếu plugin Drive không hỗ trợ nội dung/metadata cần thiết: **bỏ qua xuất hàng loạt và chuyển sang MCP read-only** khi người dùng yêu cầu, dùng SearchService/ReadKnowledgeService đã có.

### 13.2. Drive OAuth khi đổi máy hoặc Client ID

- **Di chuyển host nhưng giữ Google Cloud Project và OAuth Client hiện hành**: cấu hình redirect URI/secret/refresh token theo quy trình, kiểm thử upload/đọc; không tạo project mới chỉ để đổi máy.
- Kiểm thử riêng **(a) giữ nguyên Client, (b) Client mới cùng Project, (c) Project mới**, đối chiếu trên file thực và truy vấn `files.get`; phân biệt `403`, `404`, `invalid_grant` và file đã bị xóa. Không khẳng định mọi đổi Client đều gây lỗi.
- Portable manifest + `appProperties/properties` không tự cấp quyền ứng dụng mới. Khi quyền không đủ, cân nhắc Google Picker/cho chọn lại file phù hợp. **Không tự nâng scope lên `drive.readonly`**: đây là scope restricted, chỉ cân nhắc sau đánh giá yêu cầu và quy trình xác minh.
- Ghi hướng dẫn phục hồi đơn giản cho một tài khoản; chỉ triển khai công cụ cấp quyền lại hàng loạt nếu có tình huống thật.

### 13.3. Thumbnail và video: tách trải nghiệm khỏi giới hạn Drive Viewer

- Drive API `thumbnailLink` **ngắn hạn và không thiết kế dùng trực tiếp trong web app vì CORS/auth**. Worker sinh ảnh WebP/JPEG từ ảnh/video/PDF khi có thể; thumbnail nội bộ được phục vụ bởi Django/web server và lưu ở **volume cache bền vững**, key theo asset_id + content hash.
- **KT-010 PDF:** dùng `pypdfium2` render **trang đầu** ra Pillow rồi lưu WebP/JPEG; `pypdf` không render. Kiểm thử PDF lỗi/khóa, giới hạn trang/chiều ảnh/RAM; xác minh wheel và notices của binary PDFium trên Windows/Linux trước khi đóng gói.
- **KT-010 ảnh điện thoại:** dùng `PIL.ImageOps.exif_transpose()` **trước khi resize/crop** để xử lý EXIF Orientation (xoay/lật gương), thử cả **8 orientation**. Chỉ xử lý bản thumbnail; giữ nguyên ảnh gốc trên Drive. Với HEIC chưa có decoder, sử dụng placeholder/lỗi rõ, không làm sai ảnh. Thumbnail xuất không giữ metadata EXIF riêng tư không cần thiết.
- Lười tải/lazy-load ảnh ở danh sách, placeholder khi chưa có thumbnail; có chính sách regenerate sau khi cache bị mất. Không phải lưu thêm thumbnail gốc trên B2/R2.
- Google Drive có thể đang xử lý video sau upload. Phân biệt `file_saved` và `preview_ready`/unknown; không hứa chắc độ trễ cụ thể. **Cache video cục bộ ngắn hạn** (có TTL và giới hạn tổng dung lượng/LRU) chỉ bật nếu thử playback và ổ đĩa thật cho thấy đáng giá. Cache không phải bản sao vĩnh viễn, phải bảo vệ endpoint và giới hạn Range/size.

### 13.4. Chọn parser PDF dựa trên benchmark và nghĩa vụ giấy phép

- **Tách thumbnail và đọc chữ:** `pypdfium2` được chọn cho thumbnail PDF ở `KT-010`; ở `KT-102` so sánh **ba thư viện `pypdf`, `pypdfium2`, `PyMuPDF` trên 20–30 PDF tiếng Việt thực** (quyết định/quy hoạch/pháp luật, bảng biểu, dấu Unicode, file scan).
- Đo **chất lượng trích chữ Unicode/dấu, thứ tự đọc, đúng trang/locator, thời gian cùng máy, RAM và khả năng render thumbnail**. Với `pypdfium2` cần dùng đúng API trích Unicode (ví dụ `get_text_bounded()` tùy trường hợp), không mặc định mọi API trả text đủ ký tự.
- Kiểm tra giấy phép: **`pypdfium2` Apache-2.0/BSD-3-Clause** cùng binary/dependencies cần notice phù hợp, **PyMuPDF AGPL hoặc thương mại**. Không chọn extractor chỉ vì `pip install` dễ hoặc tuyên bố nhanh hơn 20–30 lần. Chốt extractor trong KT-102 sau phép thử, không tự coi thumbnail renderer là thư viện đọc text tốt nhất.

### 13.5. Tìm kiếm tiếng Việt PostgreSQL: tránh sai migration/index

- Tạo extension `unaccent` và `pg_trgm`, cấu hình `kt_vi` sao chép `pg_catalog.simple`; thiết lập mapping với từ điển lọc `unaccent` trước `simple` cho các token cần thiết. Mẫu tham khảo (phải thử trên Postgres được pin phiên bản):

```sql
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE TEXT SEARCH CONFIGURATION kt_vi (COPY = pg_catalog.simple);
ALTER TEXT SEARCH CONFIGURATION kt_vi
  ALTER MAPPING FOR hword, hword_part, word
  WITH unaccent, simple;
```

- Rà các token type `asciiword/asciihword/hword_asciipart` và các trường hợp số hiệu văn bản, rồi bổ sung mapping đúng; không chỉ dùng ba loại token trên và tuyên bố bao phủ tiếng Việt.
- `SearchVector(..., config='kt_vi')` và `SearchQuery(..., config='kt_vi')` phải đồng nhất; GIN expression index hoặc tsvector được duy trì phải khớp truy vấn; `SearchVectorField` tự nó không đồng nghĩa generated column.
- **Thiết kế đã chọn cho KT-104:** dùng **hai expression GIN index riêng** trên các cột thuộc cùng bảng: (1) `Item.title/description/note` và (2) `DerivedContent.text`. Không thể tạo expression index JOIN xuyên `Item` và `DerivedContent`; cũng không mặc định dồn vô hạn PDF/transcript vào một `Item.search_vector`.
- Expression GIN index được PostgreSQL cập nhật khi hàng nguồn thay đổi. `SearchService` dùng hai truy vấn index, lấy các `item_id` phù hợp (ví dụ `UNION`/subquery), xếp hạng gộp và **lọc chỉ phiên bản `DerivedContent` hiện hành**; giữ snippet/locator. Sửa Item không cần lập lại vector từ toàn PDF. Nếu văn bản cực dài vượt giới hạn `tsvector`, phải giới hạn/chia bản ghi theo trang/đoạn khi cần, không làm chunk/RAG sớm.
- Test sửa title/note, thêm phiên bản trích xuất mới, đổi active/stale, xóa mềm, lọc nhóm và hiển thị nguồn trúng; `EXPLAIN (ANALYZE, BUFFERS)` chứng minh index được dùng. Chỉ cân nhắc `SearchVectorField`/bảng search hợp nhất sau khi benchmark cho thấy hai chỉ mục không đủ; nếu dùng vector lưu vật lý phải có cơ chế cập nhật, vì field không tự đồng bộ.
- Không tạo wrapper `IMMUTABLE` thiếu chứng cứ cho `unaccent()` vốn có những phụ thuộc cấu hình. Sử dụng từ điển filter trong text search config khi phù hợp; nếu cần normalization khác, thiết kế index và rebuild với kiểm thử.
- Test có dấu/không dấu, `đ/Đ`, tên người, tên KCN, luật/số hiệu văn bản, typo/trigram; dùng `EXPLAIN (ANALYZE, BUFFERS)` để xác nhận index được dùng. Không ghi KPI mili-giây như kết quả đã đạt.

### 13.6. Ranh giới P0/P1 để tránh overengineering

**P0:** PostgreSQL đã chốt; Google Drive; ID nội bộ; frontend thư viện có thumbnail/cache; worker + video status; trích chữ nhẹ; search config/FTS test; auth đơn giản và backup.  
**P1 sớm:** thử ChatGPT Drive và bộ xuất văn bản theo phiên bản trên 5–10 item, thử OAuth recovery khác Project/Client.  
**P1 có điều kiện:** video cache tạm, per-item export số lượng lớn, MCP read-only nếu pilot Drive không đáp ứng.  
**Chưa làm:** OCR/ASR toàn kho, multi-cloud storage, vector DB, OAuth server MCP doanh nghiệp hoặc hệ thống realtime lớn.

**Nguồn chính thức:**  
- Drive file thumbnail/expiry/CORS: https://developers.google.com/workspace/drive/api/reference/rest/v3/files  
- Drive scopes: https://developers.google.com/workspace/drive/api/guides/api-specific-auth  
- Drive metadata/properties: https://developers.google.com/workspace/drive/api/guides/properties  
- Drive resumable upload/pre-generated IDs: https://developers.google.com/workspace/drive/api/guides/manage-uploads  
- Google Drive app ChatGPT: https://help.openai.com/en/articles/10929079-google-drive-app-and-setup-in-chatgpt  
- PostgreSQL unaccent/dictionaries: https://www.postgresql.org/docs/current/unaccent.html  
- Django full-text search: https://docs.djangoproject.com/en/5.2/ref/contrib/postgres/search/  
- PyMuPDF licensing: https://pymupdf.io/licensing

### 13.7. Quyết định chốt bổ sung cho Codex (v4.6)

| Task | Quyết định thực thi | Điều kiện nghiệm thu |
| --- | --- | --- |
| **KT-010** | `pypdfium2` render thumbnail trang đầu PDF; Pillow `ImageOps.exif_transpose` trước resize ảnh điện thoại | PDF lỗi/khóa không làm sập worker; đủ 8 hướng EXIF, ảnh gốc không đổi; cache WebP/JPEG bền vững, tạo lại được |
| **KT-102** | Benchmark **pypdf / pypdfium2 / PyMuPDF** để chọn extractor chữ tiếng Việt (độc lập renderer thumbnail) | 20–30 PDF thật, đo chữ/dấu/trang/tốc độ/RAM, kiểm giấy phép và fallback; không bịa kết quả |
| **KT-104** | Hai nhóm GIN index `Item` và `DerivedContent`, tìm bằng `SearchService` hợp nhất item ID | Tìm có/không dấu, đ/Đ, số hiệu, bản text mới/stale và `EXPLAIN ANALYZE` đều đúng |

**V4.6 là baseline tài liệu để triển khai**, không phải ứng dụng đã PASS. Giữ Google Drive chính, PostgreSQL đã chốt, một backend/worker, không thêm dịch vụ chỉ vì 3 điều chỉnh này.

## 14. Quyết định v4.7 về kỹ thuật tiếp nhận và tự tổ chức

**Nguồn chuẩn nghiệp vụ và 17 ca N01–N17:** [CAPTURE_AND_ORGANIZE.md](CAPTURE_AND_ORGANIZE.md). Phần này bổ sung hệ quả schema/migration, không lập hợp đồng nghiệp vụ khác.

### 14.1. Migration và tính nhất quán

1. Tạo `CaptureEvent`: UUID PK, FK owner/item, kênh, raw input URL/text, giờ server UTC timezone-aware bất biến, giờ client tham khảo, idempotency key unique theo requester/kênh khi key có giá trị. Giao dịch **Event + tìm/tạo Item + Job**; ACK sau commit. Test các request song song.
2. `Item.saved_at` lấy từ Event đầu tiên; Event nhiều-một với Item. Trùng URL sau một ngày tạo Event **mới**, nhưng HTTP retry cùng request key trả về Event **cũ**. Chỉ gộp Item khi có danh tính nguồn được chứng minh (provider canonical ID/hash), không vì cùng chủ đề.
3. Ghi chú thuần chữ lưu nguyên văn ở `Item.note`; hai ghi chú cùng chủ đề vẫn là hai Item. Gửi URL kèm chú thích thì bảo lưu chú thích **từng CaptureEvent**; không overwrite ghi chú curated; tìm được nội dung chú thích qua SearchService dù hai GIN index trên Item/DerivedContent không trực tiếp bao phủ Event.note.
4. `RelatedItem` là cặp Item khác nhau chuẩn hóa thứ tự để chống trùng hai chiều, có reason/confidence/method/source version và status. Assignment lưu origin/user_pinned/confidence/method/source version; thay model/source không được xóa nhãn thủ công.
5. `CaptureEvent` index B-tree theo (owner, server_received_at DESC, id), unique partial (owner, channel, idempotency_key) khi key khác NULL. Giữ hai nhóm GIN FTS v4.6 trên Item và DerivedContent, không thêm chỉ mục search server riêng.
6. Backup/portable manifest và restore phải giữ CaptureEvent/RelatedItem/assignment, giờ server và raw input, không chỉ Item/Asset. Event lưu được dù worker, Drive hoặc AI lỗi.

### 14.2. Phân chia trách nhiệm

`CaptureService` giữ transaction/ACK; `IngestionService` lấy nội dung nguồn sau commit; `OrganizationService` tìm nhóm đã có và tự gán/RelatedItem; `SearchService` trả ứng viên từ Postgres, `ClassificationPort` đánh giá rule/AI khi có quyền. **Không dùng một trạng thái DONE** cho tất cả các bước: source_fetch, asset_storage, content_extract, organization độc lập.

**Không phát triển sớm:** Redis, semantic/pgvector, Meilisearch, OCR/ASR hàng loạt, phần mềm Android native hoặc MCP chỉ vì nghiệp vụ mới. Gate A là lưu ngay, Gate B mới yêu cầu tự nhóm có chứng cứ. Không cam kết chất lượng AI trước benchmark.
