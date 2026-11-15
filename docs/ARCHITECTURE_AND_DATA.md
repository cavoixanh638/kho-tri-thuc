# KIẾN TRÚC, DỮ LIỆU VÀ LỘ TRÌNH NÂNG CẤP — V4.4

**Ngày:** 15/11/2026 · **Dựa trên:** `MASTER_PLAN.md` v4.4 · **Đối tượng:** một người dùng lúc đầu, Google Drive là kho file chính; phát triển thêm tính năng AI và có thể nhiều dữ liệu/worker về sau.  
**Trạng thái:** quyết định thiết kế, **chưa triển khai hoặc benchmark**. Mọi số liệu hiệu năng và điều kiện nâng cấp dưới đây là mục tiêu/trigger để đo, không phải kết quả đo.

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
| CSDL chính | **PostgreSQL local container** | SQLite + FTS5, Supabase Postgres, Google Sheets | Chỉ thêm một container nhưng tránh chuyển SQLite/FTS5/jobs sau khi có dữ liệu; Django chính thức khuyến nghị PostgreSQL cho production; có pgvector/GIN/trigram nếu mở rộng. Không trả phí managed DB riêng |
| Backend | **Django 5.2 LTS + Django Ninja** | Django 6.1 + Ninja, FastAPI, Django + DRF | LTS hỗ trợ tới 04/2028, auth/admin/migrations sẵn, Ninja có OpenAPI; thuận đường lên Django 6.2 LTS. FastAPI mạnh nhưng thêm bộ phận auth/admin/ORM; DRF nặng hơn cho API nhỏ |
| Frontend | **React + TypeScript + Vite** | Django + HTMX, Vue 3, SvelteKit | Lọc nhiều điều kiện, upload/preview, PWA responsive; static deploy và API độc lập cho Android native sau. Không cần Next SSR hoặc server Node production |
| UI | **Mantine** | shadcn/ui, MUI, Ant Design | Nhiều biểu mẫu/multiselect/date/filter sẵn, giúp Codex ra UI nhanh. Không trộn hai UI framework khi chưa có lý do |
| Search | **PostgreSQL + unaccent/pg_trgm/FTS** sau lớp `SearchService` | Typesense, Meilisearch, OpenSearch | Không vận hành search server; khi cần tìm ngữ nghĩa thêm pgvector hoặc provider search dưới interface, không thay API |
| Queue | **PostgreSQL `jobs` + 1 worker** | Procrastinate, Chancy, Celery+Redis | Vẫn gọn khi ít tác vụ; bảng job có lease/retry/idempotency, về sau worker tăng được. Không viết framework queue chung đa năng; nếu vượt khả năng, thay worker adapter |
| AI phân loại | **Rule-based + `ClassifierPort`**, provider sau benchmark | Gemini Flash-Lite, OpenAI model nhỏ, model local | Không khóa nhãn đã chốt với output AI; thay model/prompt mà không xáo dữ liệu |
| Parsing | **pypdf, python-docx, openpyxl, Trafilatura, phụ đề nguồn** | PyMuPDF, Docling, LibreOffice/Crawl4AI | Nhẹ, không OCR/ASR nền; kết quả version hóa để sau chạy lại bằng công cụ tốt hơn |
| Video | **yt-dlp + ffprobe/FFmpeg** | Cobalt, gallery-dl, Streamlink | Đã có benchmark tương đối, xử lý nhiều nguồn, fallback link-only; giao downloader qua interface để không phụ thuộc một extractor |
| Auth app | **Django Auth một account + HTTPS** | Google login/OIDC, Auth0, Keycloak | Không cần đa role, dịch vụ identity; chỉ giữ token Drive phía backend, chuẩn bị `owner_id` nếu về sau nhiều user |
| ChatGPT | **Google Drive app trước** | MCP custom, gửi file bằng tay, GPT Actions | Thử khả năng sẵn có. MCP riêng chỉ thêm khi cần tags/projects/ghi chú của database; có read API làm sẵn từ đầu |
| Triển khai | **Docker Compose một máy**: Django/API, Postgres, worker, HTTPS/static | systemd+venv, Railway/Render, Kubernetes | Có thể clone/chạy ở Windows qua Docker và chuyển VPS ít sửa; số dịch vụ tối thiểu. Không cần k8s |
| Backup | **pg_dump + export JSON/manifest + bản sao ngoài Drive** | snapshot máy chủ, R2/S3, Google Takeout | Phục hồi được metadata lẫn mapping Drive file; mất một máy chủ vẫn restore được. Không cần multi-cloud đồng bộ mọi media v1 |

**Tiêu chí đánh giá:** mức phù hợp 30%, đơn giản/bảo trì 25%, chi phí 20%, độ tin cậy 15%, chuyển đổi 10%. Trọng số chỉ là cách tranh luận, không tạo điểm số ảo.

### 1.3. Vì sao không giữ SQLite cho dữ liệu thật?

SQLite là lựa chọn hợp lý cho một prototype không cần server. Nhưng khi đã có **tác vụ tải/upload chạy nền, người dùng sửa phân nhóm, tìm kiếm trong extracted content, cần khả năng AI vector/MCP và kế hoạch sử dụng lâu dài**, việc đổi database sau đó có thể khiến phải chuyển FTS5, schema, job SQL, indexes và các test. Django cũng ghi rõ SQLite production có giới hạn migration/concurrency, và khuyến nghị PostgreSQL. Một container PostgreSQL dùng chung Docker Compose là **đầu tư kỹ thuật nhỏ nhưng giảm đáng kể chi phí đổi sau**.

**Không đồng nghĩa** phải cài Redis, Elasticsearch, pgvector hoặc Kubernetes. Có thể dùng SQLite *chỉ cho POC* nếu chưa có Docker, nhưng **không có hai schema/backend chạy song song lâu dài**. Ngay trước khi nhập dữ liệu thật, thống nhất Postgres.

## 2. Sơ đồ hệ thống

```text
PWA React (Android + Windows)
      |
      v
HTTPS / static + /api/v1/
      |
Django 5.2 LTS + Ninja
    +-- Auth / Items / Groups / Projects
    +-- IngestionService -> JobRepository
    +-- LibraryService -> Item, Source, Asset
    +-- SearchService -> Postgres full-text/trigram
    +-- StoragePort -> DriveStorage (OAuth drive.file)
    +-- ExtractionService -> DerivedContent (versioned)
    +-- ClassificationPort -> rules / AI provider
      |
PostgreSQL (metadata, relations, statuses, extracted text)
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
| `Item` | `id UUID`, owner_id, kind, title, description, note, saved_at, published_at nullable, favorite, deleted_at, user_edit_version | Tri thức độc lập vị trí lưu |
| `Source` | id, item_id, original_url, canonical_url, platform, platform_id nullable, captured_at, source_metadata | Một item có thể có nhiều nguồn, giữ provenance |
| `Asset` | `id UUID`, item_id, role, mime, size, sha256, original_filename, content_version | File gốc/thumbnail/derivative được phân biệt |
| `StorageLocation` | id, asset_id, `provider='google_drive'`, provider_file_id, status, verified_at, provider_revision | Chỉ có 1 location lúc đầu; thêm location không sửa Item |
| `Topic` | id, parent_id nullable, name, archived | Lĩnh vực root/chủ đề con |
| `Project` | id, name, description, archived | Khác chủ đề, là công việc/dự án |
| `Tag` | id, name | Nhãn tự do |
| `ItemTopic / ItemProject / ItemTag` | item_id, reference_id, origin, user_pinned | Many-to-many; AI không ghi đè các gán thủ công |
| `DerivedContent` | id, asset_id/item_id, type, text/ref, source_locator, processor, processor_version, input_hash, status, created_at | Text PDF/web/subtitles hiện tại; OCR/ASR phiên bản sau |
| `Job` | id, kind, item_id nullable, idempotency_key, state, attempt, lease_until, retry_at, error_code, input_ref | Không mất tác vụ; mở rộng worker sau |
| `DriveAccount` | user_id, google_sub, root_folder_id, oauth_state, connected_at | **Token lưu riêng và được bảo vệ**, không nằm trong record xuất công khai |
| `ExportRecord` (mức gọn) | id, file_ref, schema_version, sha256, created_at | Theo dõi bản portable export/restore |

**Chưa tạo:** EmbeddingModel, ChunkEmbedding, Claim/Evidence, KnowledgeGraph, nhiều quyền người dùng, chat history, AI execution logs lớn. Khi thêm chúng chỉ FK vào Item/Asset/DerivedContent hiện có.

### 3.1. Quy tắc bất biến

- `item_id` và `asset_id` là UUID; **không dùng Drive ID, URL, tên file làm primary key**.
- `drive_file_id` là thuộc tính của `StorageLocation`, không hiện diện khắp code nghiệp vụ.
- Ngày hệ thống UTC, hiển thị Asia/Bangkok; `published_at` thiếu thì NULL, không suy đoán.
- Dữ liệu người dùng sửa là **curated**, không đồng nhất với AI suggestion; lần xử lý lại không thay ngầm.
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

- Scope `drive.file` đủ cho file do app tạo/file được user mở có chủ đích; muốn import file Drive có sẵn ngoài phạm vi này phải có Picker/thủ tục cấp quyền.
- OAuth External + Testing thường làm refresh token hết hạn sau 7 ngày; lúc triển khai thật cần kiểm tra publishing state và nút kết nối lại khi `invalid_grant`, không hứa refresh token tồn tại mãi.
- Với file >5MB và kết nối không ổn định, dùng **resumable upload**. Google Drive có thể cấp pre-generated file ID cho upload blob để retry sau timeout không nhân file; **không áp dụng cách đó tùy tiện cho Google Docs/Sheets native**.
- Sau mỗi upload, xác nhận file tồn tại, trả Drive file ID và checksum nếu có. Ghi thành công vào DB sau xác minh, không gộp trạng thái `link_saved` với `file_uploaded`.
- Chống hạn mức/429 với backoff; nếu quota tài khoản hết, job chờ hoặc báo, file tạm được giữ có thời hạn để retry.
- Không xây media proxy/phát video nâng cao trước; ưu tiên mở bằng Drive viewer đã đăng nhập, có fallback tải xuống khi preview không đạt.

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
Receive -> Item + Source + Job
     -> Download/Upload -> Asset + StorageLocation (original)
     -> Extract -> DerivedContent [text, subtitle, locator, version]
     -> Classify -> suggestions (can reject/override)
     -> Search index (rebuildable)
```

- Mỗi bước idempotent theo `item_id/asset_id + processor_version + input_hash`.
- Trích xuất nặng sau này chỉ là processor mới; không sửa bảng Item hoặc xóa văn bản cũ.
- Video transcript có `timestamp`, PDF có `page`, Excel có `sheet/cell` khi công cụ hỗ trợ; không bịa locator.
- Khi có embedding, tạo **bảng riêng** có `model_id/version/dimension`, không nhét vector vào Item/DerivedContent; có thể lưu nhiều thế hệ vector và switch model sau khi nghiệm thu.
- AI gợi ý nhóm không được tự sửa nhãn do người dùng chốt. Có setting cho phép/tắt AI bên ngoài và hạn mức chi phí.

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

- API v1 dùng `SearchService.search(filters, query, cursor)` và `ReadKnowledgeService.fetch(item_id, parts)`.
- Version 1 tìm metadata, tag, dự án, ghi chú, DerivedContent bằng PostgreSQL GIN/FTS, unaccent và pg_trgm; index có thể tái tạo, test tiếng Việt không dấu.
- Khi tăng dữ liệu lớn, có thể thêm Typesense/Meilisearch như backend tìm kiếm nhưng **không làm nguồn gốc dữ liệu**.
- Khi cần semantic/RAG: thêm `EmbeddingModel`, `ContentChunk`, `ChunkEmbedding` riêng; sinh từ DerivedContent có provenance; dùng pgvector hoặc provider khác, đánh giá trước khi chuyển.
- ChatGPT Drive app có thể tìm và làm việc với file Drive nếu workspace hỗ trợ; app này không tự biết tag/project trong PostgreSQL. Nếu cần những facet đó, xây MCP sử dụng chính `SearchService`/`ReadKnowledgeService` (không lặp nghiệp vụ).
- Câu trả lời trích nguồn dựa trên `item_id, drive_file_id, page/sheet/timestamp` có thật; file thiếu text phải báo rõ.

## 8. API và frontend: không phải làm lại khi có Android native/MCP

**Versioned REST** `/api/v1/`. Nhóm tối thiểu: 
- `POST /ingest/links`, `POST /items/notes`, `POST /uploads`,
- `GET /items`, `GET /items/{id}`, `PATCH /items/{id}`,
- `GET /search`, `GET /items/{id}/content`,
- `GET /groups`, `POST /groups`,
- `GET /jobs/{id}`, `GET /assets/{id}/open`,
- `GET /integrations/drive/status`, `GET /integrations/drive/connect`, OAuth callback.

- Không gọi Drive API trực tiếp từ React với token toàn quyền; React chỉ dùng backend API.
- React + Mantine: Thêm, Thư viện, Chi tiết, Tìm kiếm (có thể cùng Thư viện), Cài đặt.
- Mỗi card/chi tiết hiển thị **trạng thái nhận link / lưu file / trích văn bản / phân nhóm** riêng, không chỉ một nút “Hoàn tất”.
- Android PWA Share Target thử trên thiết bị thật; fallback dán link là bắt buộc. Nếu về sau cần native push/share thì dùng API sẵn.
- Không làm UI admin đa role, streaming player riêng, thiết kế bảng nhiều trăm cột.

## 9. Triển khai, bảo mật và sao lưu theo mức vừa đủ

- Docker Compose trên 1 máy: `web (Django)`, `worker (same image)`, `postgres` và `caddy/HTTPS` khi có domain, frontend bundle tĩnh.
- Dùng Django Auth một tài khoản, mật khẩu/session/HTTPS, token Drive phía backend; không cần Auth0/Keycloak/RBAC.
- Chuẩn bị `owner_id` ngay trong model để sau có thể cho nhiều người kết nối Drive khác nhau mà không gắn nhầm file.
- Tiền xử lý URL để chống SSRF và không cho worker tự do tải địa chỉ nội bộ; giới hạn tệp, tổng dung lượng temp và timeout.
- `pg_dump` + versioned JSON manifest định kỳ lên Drive, bản tải về Windows hoặc kho khác (độc lập Drive) theo lịch; thử phục hồi từ file dump và manifest.
- Không đưa OAuth token, dữ liệu media cá nhân, backup hoặc file .env lên GitHub; không dùng GitHub Actions làm nơi lưu file video.
- CI tối thiểu: Django migrations/tests + frontend build/typecheck + integration tests với fake Drive; kiểm thử thật trên Drive test folder trước khi bật production.
- Không bật Prometheus/Grafana/Sentry enterprise lúc đầu; log lỗi job, upload, Drive OAuth, backup và cảnh báo khi không thể lưu.

## 10. Kịch bản nâng cấp và chi phí thay đổi

| Kịch bản | Giữ nguyên | Phần bổ sung | Mức độ nếu theo v4.4 |
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
