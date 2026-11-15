# KIẾN TRÚC VÀ DỮ LIỆU — BẢN THIẾT KẾ THẢO LUẬN

**Cập nhật:** 15/11/2026 · **Bám theo:** `MASTER_PLAN.md` v4.2. **Rà soát lựa chọn R1 (15/11/2026)** — đối chiếu 2–3 phương án thay thế cho mỗi thành phần tại Mục 14.  
**Phân loại quyết định:** **ĐỀ XUẤT CHỐT** = phương án ưu tiên để lập trình; **CẦN THỬ** = phải kiểm chứng trên môi trường thật; **CHƯA CHỐT** = cần người dùng/điều kiện thực tế quyết định. Không nhầm đề xuất thành chức năng đã hoàn thành.

## 1. Quyết định công nghệ tổng quan

| Mảng | Đề xuất | Trạng thái | Vì sao và phương án thay thế |
|---|---|---|---|
| Kiến trúc | Modular monolith + worker riêng từ cùng codebase | ĐỀ XUẤT CHỐT | Triển khai đơn giản, phân ranh module rõ, không microservice |
| Frontend | React + TypeScript + Vite | ĐỀ XUẤT CHỐT | PWA, UI nhiều bộ lọc, không cần Next.js/SSR |
| UI components | Mantine v9 + CSS Modules + Lucide/Tabler | ĐỀ XUẤT CHỐT SAU SO SÁNH | Có sẵn nhiều component/filter/form, giảm thời gian phát triển, không ghép thêm shadcn làm UI chính |
| Routing | React Router | ĐỀ XUẤT CHỐT | Trang Thêm/Thư viện/Chi tiết/Tìm kiếm/Cài đặt |
| Server state | TanStack Query | ĐỀ XUẤT CHỐT | Cache/invalidation, trạng thái loading/lỗi |
| Biểu mẫu | Mantine Form + Zod khi cần | ĐỀ XUẤT CHỐT SAU SO SÁNH | Đồng bộ Mantine, không thêm framework form thứ hai mặc định |
| PWA | vite-plugin-pwa + Web Share Target (nếu hỗ trợ) | CẦN THỬ | Kiểm tra thực tế trên Android; fallback dán link |
| Backend | Python 3.12+ / Django 6 + Django Ninja | ĐỀ XUẤT CHỐT SAU SO SÁNH | Django auth, admin, ORM, migration sẵn; Ninja tạo OpenAPI |
| ORM/migration | Django ORM + Django migrations | ĐỀ XUẤT CHỐT SAU SO SÁNH | Không phải bảo trì ORM/migration thứ hai |
| DB | PostgreSQL (phiên bản hỗ trợ, pin theo Docker) | ĐỀ XUẤT CHỐT | Nghiệp vụ + FTS + chỉ mục, không cần vector ngay |
| Search | PostgreSQL full text + unaccent + pg_trgm | CẦN THỬ | Đo chất lượng tiếng Việt, không mặc định FTS hiểu từ ghép |
| Queue | Procrastinate + Django integration (PostgreSQL-backed) | CẦN THỬ | Có Django migration/admin, nhưng phải kiểm thử crash/retry và rủi ro bảo trì |
| File chính | Backblaze B2 riêng tư, S3-compatible API + boto3 | ĐỀ XUẤT CHỐT | Giá thấp, file ID độc lập nhà cung cấp |
| Video | yt-dlp stable + ffprobe/FFmpeg; Cobalt adapter dự phòng | CẦN THỬ | Phụ thuộc nền tảng/IP; không bảo đảm mọi link |
| PDF text | pypdf mặc định; pdfplumber bổ sung nếu cần | CẦN THỬ | Giấy phép BSD/MIT thuận lợi; PyMuPDF AGPL cần duyệt giấy phép trước khi dùng |
| Word / Excel | python-docx / openpyxl | ĐỀ XUẤT CHỐT | Trích chữ, bảng, sheet ở mức cơ bản |
| Bài báo web | Trafilatura | CẦN THỬ | Không bắt buộc Playwright |
| AI phân loại | AI provider adapter, JSON có schema; manual/rule fallback | CHƯA CHỐT | Chọn dịch vụ sau bài kiểm thử giá/chất lượng/riêng tư |
| MCP | Official Python MCP SDK v2 (`MCPServer`), Streamable HTTP | ĐỀ XUẤT CHỐT SAU SO SÁNH | Bám spec mới, không dùng ví dụ official SDK v1 `FastMCP` |
| MCP auth | Django OAuth Toolkit >=3.4, OAuth2.1/PKCE, read scope | CẦN THỬ CHẤT LƯỢNG KẾT NỐI | Có hỗ trợ MCP metadata/CIMD/DCR; fallback Auth0/ZITADEL nếu không đạt |
| Host | 1 VPS Linux hoặc Oracle nếu cấp được tài nguyên | CHƯA CHỐT | Ưu tiên rẻ, ổn định, Docker Compose |
| HTTPS | Caddy reverse proxy, same-origin cho UI/API | ĐỀ XUẤT CHỐT | TLS, tránh CORS phức tạp |
| Backup | pg_dump + bản sao file/provider khác; restore drill | ĐỀ XUẤT CHỐT | Không phụ thuộc một kho/VM |
| Logging | Structured JSON logs + audit, không log secret | ĐỀ XUẤT CHỐT | Chẩn đoán job lỗi |

**Không chọn từ đầu:** Kubernetes, Redis, RabbitMQ, Celery, Next.js SSR, Elasticsearch, graph DB, pgvector, ASR/OCR server thường trực, Playwright/Chromium production, Cloudflare Workers phát video.

## 2. Sơ đồ triển khai

```text
Android/Windows Browser (PWA)
          |
          v
 HTTPS / Caddy [1 origin]
    /            /api/v1          /mcp (P1, riêng xác thực)
    |                |                 |
Frontend static   Django Ninja --- MCP adapter (official SDK v2)
                      |
             Service layer (quyền, nghiệp vụ)
                  /       \
            PostgreSQL   B2 Storage Adapter
               |
          Postgres queue -> Worker process (same Python code)
                              |
                    yt-dlp / ffprobe / parsers
                              |
                      AI Classification Adapter
Backup task: pg_dump encrypted + cross-provider copies
```

- Frontend không có B2 credentials; browser chỉ nhận quyền upload/download tạm, có giới hạn và xác minh kết quả trên backend.
- Worker không phục vụ web traffic; download/extraction/AI là tác vụ nền.
- MCP gọi cùng service layer với API và kiểm tra quyền; không có role toàn quyền trong DB.

## 3. Frontend — chốt chức năng và UI/UX

### 3.1. Information architecture

- `/`: điều hướng tới Thư viện (hoặc dashboard rất gọn).
- `/add`: dán URL, tải file/ảnh, ghi chú văn bản; có ô ghi chú tùy chọn, không bắt buộc phân loại.
- `/library`: toàn bộ mục; tab/bộ chọn *Lĩnh vực – Dự án – Theo ngày – Loại nội dung*; tìm kiếm và bộ lọc.
- `/items/:id`: file nguồn, video player, metadata, extracted text, ghi chú, nhóm/tag, thời gian và trạng thái job.
- `/search`: tìm toàn văn, lọc chồng, sắp xếp và lưu bộ lọc (nếu làm ở vòng nâng cấp).
- `/settings`: chủ đề/dự án, đăng nhập, sao lưu/trạng thái hệ thống, giới hạn AI.
- `/trash`: mục đã xóa mềm và khôi phục; có thể đặt dưới Cài đặt.

### 3.2. Bố cục desktop/mobile

- Desktop: thanh điều hướng trái thu gọn được; thanh tìm kiếm trên; danh sách/thumbnail ở giữa; drawer chi tiết nhanh. Content max-width hợp lý trên màn hình lớn, không trải ô quá rộng.
- Mobile: thanh điều hướng dưới hoặc menu ngắn; nút **Thêm** cố định; bộ lọc trong bottom sheet; chạm card xem chi tiết, hỗ trợ share link.
- Luồng chính: Share/dán -> hiển thị *Đã nhận* -> không chặn khi backend xử lý -> cập nhật trạng thái qua polling nhẹ; không yêu cầu giữ màn hình bật.
- Chế độ danh sách và lưới; media player HTML5 (video B2 có HTTP Range), xem PDF khi trình duyệt hỗ trợ, tải file nếu không preview được.
- Responsive, keyboard focus, semantic labels, contrast, aria, tránh click nhỏ trên điện thoại. Khả năng cài PWA/Share Target cần thử máy thật.

### 3.3. Component và state

- `AppShell`, `QuickAdd`, `LibraryToolbar`, `FacetFilters`, `ContentCard`, `ContentTable`, `ItemDetail`, `MediaPreview`, `SourceInfo`, `EditTagsProjects`, `JobStatus`, `BulkActions`, `Settings`.
- TanStack Query quản lý request cache/retry hợp lý; form state ở từng form; Zustand chỉ nếu nảy sinh state cross-page thực sự, không thêm mặc định.
- UI hiển thị độc lập trạng thái **storage**, **extraction**, **classification**, **backup**. Không gộp thành một nhãn *Hoàn tất* gây hiểu sai.
- Tìm không dấu, autocomplete lĩnh vực/dự án, thao tác đổi nhóm ngay từ card và ở bulk selection.
- Ưu tiên tốc độ nhận link: không bắt chọn lĩnh vực trước khi lưu.

### 3.4. Frontend quality

- Unit/component: Vitest + React Testing Library; E2E: Playwright **làm công cụ kiểm thử trên CI/dev**, không phải browser scraping worker production.
- Cần thử: Android share target, upload lớn, mất mạng, một URL gửi hai lần, tìm có/không dấu, phân nhóm thủ công giữ nguyên sau AI retry.
- Không render HTML nguồn từ website vào DOM app khi chưa sanitize.

## 4. Backend — module và API

### 4.1. Module

`auth`, `items`, `sources`, `assets`, `storage`, `taxonomy`, `projects`, `ingestion`, `extraction`, `search`, `classification`, `jobs`, `backups`, `mcp_adapter` (P1), `admin`.

Mỗi module gồm request/response schema, service, persistence/query, test. Không sinh hàng chục CRUD endpoint cho bảng nội bộ.

### 4.2. REST API đề xuất (v1)

| API | Mục đích |
|---|---|
| `POST /api/v1/ingest/links` | Nhận 1 hoặc nhiều URL, idempotency key |
| `POST /api/v1/items/notes` | Tạo ghi chú |
| `POST /api/v1/uploads/init` | Khởi tạo upload, quota/MIME/size |
| `POST /api/v1/uploads/complete` | Xác minh file thực sự có trên B2 |
| `GET /api/v1/items` | Danh sách và filter, cursor pagination |
| `GET /api/v1/items/{id}` | Chi tiết + trạng thái |
| `PATCH /api/v1/items/{id}` | Sửa title/mô tả/flag; audit |
| `POST /api/v1/items/{id}/groups` | Cập nhật lĩnh vực/dự án/tag |
| `DELETE /api/v1/items/{id}` | Xóa mềm |
| `POST /api/v1/items/{id}/restore` | Khôi phục |
| `GET /api/v1/search?q=...` | Search + filter + source locator |
| `GET /api/v1/items/{id}/content` | Văn bản đã trích, phân trang nếu dài |
| `GET /api/v1/assets/{id}/access` | Kiểm quyền, cấp URL thời hạn ngắn |
| `GET /api/v1/jobs/{id}` | Trạng thái job/step/lỗi |
| `GET /api/v1/topics` / `GET /api/v1/projects` | Phân nhóm, dự án |
| `GET /api/v1/health` | Liveness; readiness cần xác thực/quyền nội bộ |

Các API thay đổi dữ liệu cần đăng nhập, CSRF/session protection, rate limit. File lớn nên upload trực tiếp qua presigned PUT có kiểm soát thay vì proxy toàn bộ qua Django Ninja.

### 4.3. Quy tắc ingest

- Phân biệt original URL, canonical URL, platform + platform item ID; chỉ hợp nhất khi ID/checksum đủ chắc chắn.
- Khi URL tương tự không chắc trùng, đề xuất thay vì tự gộp.
- Không giả định video public luôn tải được bằng một địa chỉ cloud.
- Mỗi stage có trạng thái độc lập; tải lỗi không chặn hiển thị mục thư viện.
- Có idempotency key, unique constraints và transaction để retry không tạo bản ghi/file trùng.
- Chống SSRF: chỉ cho HTTP(S), chặn IP loopback/private/link-local/metadata; kiểm tra redirect và DNS lại ở mỗi hop; download subprocess bị cô lập quyền mạng/tệp.

### 4.4. Trích xuất nhẹ

- Parser Adapter interface: `extract(asset) -> {text, locator, status, extractor_version}`.
- PDF: pypdf trước; trả văn bản có trang nếu khả thi. Nếu thiếu chữ thì `not_extractable_without_ocr`.
- DOCX: text + bảng, giới hạn số ký tự; XLSX: sheet + ô hữu ích, tránh nạp Excel cực lớn vào RAM; Web: Trafilatura (URL, ngày, title, body).
- Phụ đề video: yt-dlp tự nhận diện/cố tải các phụ đề cho phép, giữ ngôn ngữ và nhãn nguồn; không tự ASR.
- Văn bản lấy được cần làm sạch ở mức vừa phải, giữ raw text, metadata, locator; indexing không phụ thuộc AI.
- Mặc định không xử lý macro/file thực thi, không mở file tải lên với quyền hệ thống.

### 4.5. AI phân loại nhẹ

- Đầu vào: title + description + metadata + những đoạn tiêu biểu giới hạn độ dài + (nếu được phép) thumbnail.
- Đầu ra có schema: `suggested_title`, `topics[]`, `projects[]`, `tags[]`, `confidence`, `reasons[]`.
- Dùng taxonomy đã có; tạo nhóm mới chỉ ở trạng thái đề xuất, giới hạn số nhóm.
- Tôn trọng field sửa thủ công; AI không được overwrite lựa chọn người dùng.
- Phân loại có thể tắt và chạy lại; lưu provider/model/prompt version, chi phí, trạng thái; thất bại đưa vào *Chưa phân loại*.
- **CHƯA CHỐT** provider (OpenAI/Gemini/Groq cho từng tác vụ), mức chi và chính sách gửi dữ liệu; cần chạy bộ 30–50 mục thật, có consent với tài liệu nhạy cảm.

## 5. Database — sơ đồ quan hệ tối thiểu

### 5.1. Bảng lõi đề xuất

| Bảng | Trường chính | Ghi chú |
|---|---|---|
| `users` | id, login, password_hash, active | Single-user trước, không public signup |
| `knowledge_items` | id (UUID), title, description, kind, saved_at, source_published_at nullable, favorite, deleted_at, version | Mục tri thức không chứa đường dẫn kho vật lý |
| `sources` | id, item_id, original_url, canonical_url, platform, external_id nullable, author, metadata_json | Định danh nguồn và thời gian lấy |
| `assets` | id, item_id, role, mime, bytes, sha256, version, available | File gốc/thumbnail/bản thay thế |
| `storage_locations` | id, asset_id, provider, bucket_or_drive, object_key, role, verified_at, status | Nhiều vị trí cho một asset |
| `topics` | id, parent_id nullable, name, slug, archived | Lĩnh vực là root; chủ đề là node con |
| `item_topics` | item_id, topic_id, origin, pinned | Many-to-many; phân biệt gán bằng AI/thủ công |
| `projects` | id, name, description, status, created_at | Không nhập dự án như folder cứng |
| `item_projects` | item_id, project_id, origin, pinned | Một item có thể ở nhiều dự án |
| `tags` / `item_tags` | id/name; item_id/tag_id | Tag tự do có chống trùng tên |
| `extracted_contents` | id, item_id, asset_id nullable, kind, text, locator_json, extractor, version, status, updated_at | Có thể tạo nhiều phiên bản; không nhét vào mô tả |
| `jobs` hoặc queue backend | id, item_id, step, status, attempts, error, heartbeat, next_run | Quan sát, retry, idempotency |
| `item_revisions` | id, item_id, change_json, author, created_at | Audit tối thiểu với sửa ghi chú/metadata |
| `backup_runs` | id, started_at, completed_at, provider, manifest, status, verified_at | Không đánh đồng uploaded với verified |

Có thể triển khai các bảng theo bước (Bước 1 lõi/source/assets/jobs; Bước 2 taxonomy/extraction/classification). Không cần CRUD API cho mọi bảng; không thêm `chunk_embedding`/`claim` khi chưa dùng.

### 5.2. Các quy tắc dữ liệu

- UUID ổn định. Tất cả ngày hệ thống lưu UTC, hiển thị theo múi giờ người dùng (mặc định Việt Nam).
- Dữ liệu không biết = NULL, không thay bằng 0 hoặc chuỗi trống suy đoán.
- Unique/checksum giúp phát hiện file trùng; unique theo platform/external_id khi đáng tin, có ngoại lệ đối với nguồn không chắc.
- Index theo saved_at, kind, project/topic join, platform/id, checksum, trash; tạo search vector/index riêng cho text; kiểm thử accent-insensitive.
- Mọi thay đổi DB qua Django migrations và có rollback strategy; nếu migration không thể rollback, phải có backup và runbook.
- Không có cascade delete phá file/bản sao ngay khi xóa UI. Xóa mềm trước; hard-delete là tác vụ riêng có xác nhận.

## 6. Search

- Hợp nhất title (trọng số cao), tags/topics/projects, description, author và extracted text.
- PostgreSQL tsvector/GIN phù hợp + pg_trgm để tìm tương đối và không dấu; với tiếng Việt cần normalization theo search field có ghi rõ nguyên bản.
- Bộ lọc AND/OR phải chốt theo UX; mặc định AND giữa các loại facet, OR trong cùng facet.
- Kết quả trả metadata + snippet + locator (file/page/sheet/timestamp nếu có); không bịa locator.
- Đối với tài liệu dài, có thể lưu các text span theo trang/section đơn giản để fetch một phần; chưa cần semantic chunking.
- Pagination và stable sort; kiểm thử tối thiểu 1.000 mục.

## 7. Storage và backup

### 7.1. B2 Storage Adapter

Giao diện nội bộ:
`put(asset_id, stream)`, `get_access(asset_id, user, TTL)`, `stat(asset_id)`, `verify(asset_id, sha256)`, `copy(asset_id, provider)`, `soft_delete(asset_id)`.

- B2 S3 compatible + boto3; bucket private, unique key theo asset ID/version, không phụ thuộc title.
- Upload hoàn tất sau khi backend xác thực object metadata (size, MIME đáng tin một phần, checksum do server xác minh).
- Presigned URLs ngắn, giới hạn thao tác; thận trọng cache/CDN và lộ URL.
- Các file cần giữ gốc không tự transcode/resize bản gốc; thumbnail là derivative.

### 7.2. Google Drive và backup

- Drive 500GB là kho **backup/tài liệu bổ sung**, không phải điều kiện hoạt động của app.
- Có thể sử dụng rclone/CLI một chiều khi cấu hình được OAuth; không xây Picker/reconnect UI v1.
- Database dump mã hóa định kỳ, lưu off-host, kiểm tra restore. File không thể tái tạo phải có bản sao ở provider khác.
- Cần chốt retention/chi phí/điểm khôi phục; đề xuất tạm: DB hằng ngày; file mirror sau khi upload; restore thử theo chu kỳ; báo động khi backup trễ.
- Khi Drive có lỗi/token hết hạn: báo backup degraded, không xóa file B2, cho người dùng sửa cấu hình.
- Export toàn bộ metadata/notes/link bằng JSON/CSV và file manifest định danh độc lập storage.

## 8. Tác vụ nền

Ưu tiên Django + Procrastinate trên PostgreSQL để không phải dựng Redis và tận dụng Django migrations/admin của Procrastinate. **CẦN THỬ:** chạy song song 2 worker, retry/backoff, crash trước/sau commit, idempotency, resume, giám sát trạng thái. Dự án Procrastinate đang tìm maintainer bổ sung; nếu không phù hợp, đánh giá Chancy hoặc PgQueuer trước khi cân nhắc tự viết queue PostgreSQL có lease/SKIP LOCKED.

Hàng đợi phân luồng: `download`, `metadata`, `extract`, `classify`, `backup`. Đặt concurrency thấp; giới hạn size, time, CPU/RAM; từng stage độc lập.

## 9. Xác thực, bảo mật và riêng tư

### 9.1. Ứng dụng web (Bước 1)

- Single admin account qua `createsuperuser`/setup có kiểm soát của Django; không public sign-up.
- Dùng Django Auth và Django session; ưu tiên password hasher Argon2id, cookie HttpOnly Secure SameSite, CSRF của Django cho thao tác có thay đổi, rate limit đăng nhập.
- Audit thao tác xóa/sửa/đổi quyền, quyền file trong mọi request.
- Secrets qua environment/secret manager; TLS HTTPS; không đưa B2 key vào frontend.
- URL từ người dùng phải qua SSRF protections; sandbox/giới hạn tải video và xử lý tài liệu.

### 9.2. MCP (Bước 3)

- Remote endpoint `/mcp` qua HTTPS **hoặc** Secure MCP Tunnel nếu môi trường hỗ trợ.
- MCP server chỉ cấp `knowledge:read`, không expose tool sửa/xóa trong phiên bản đầu.
- Cho phép ChatGPT kết nối bằng OAuth2.1 Authorization Code + PKCE (thử Django OAuth Toolkit >=3.4, kiểm tra MCP discovery/CIMD/DCR ở Bước 3); token kiểm audience/issuer/expiry/scope; không dùng public API key tĩnh làm bảo vệ duy nhất của kho riêng tư.
- Công cụ mặc định: `search`, `fetch`, `list_items`, `get_item`; `get_asset` chỉ sau khi kiểm tra hành vi tải file/ quyền truy cập.
- Các MCP tool phải dùng cùng service layer và ACL với REST API; giới hạn số bản ghi, kích thước text và loại dữ liệu được đọc.
- `search`/`fetch` **không bắt buộc cho mọi custom MCP**, nhưng **nên có để tương thích company knowledge/deep research**. Phải kiểm thử result schema và nguồn dẫn trong ChatGPT thật.
- ChatGPT plugin nối từ web và tùy thuộc quyền workspace. Không tự hứa thao tác cài MCP trực tiếp trên app ChatGPT Android.
- Nội dung từ file/web là dữ liệu không đáng tin, không được thực thi câu lệnh hoặc prompt injection trong tài liệu.

## 10. Deployment và vận hành

### 10.1. Docker Compose đích

- `caddy`: TLS, static frontend, reverse proxy /api và /mcp.
- `api`: Django ASGI + Django Ninja.
- `worker`: cùng image Python, process worker.
- `postgres`: volume durable, backup.
- Tùy chọn job scheduler dựa queue/cron; không thêm Redis/Elasticsearch lúc đầu.
- Health/readiness; limit RAM/CPU worker; log rotation, cron backup; image pin versions.

### 10.2. CI/CD

- Frontend: typecheck, ESLint, unit, build.
- Backend: Ruff, kiểm tra kiểu phù hợp, pytest/pytest-django, `makemigrations --check` và migration validation.
- E2E: Playwright browser tests trên dữ liệu giả (không lưu test data lên production).
- Docker build + smoke compose + dependency/license scan.
- Staging với bucket DB tách riêng; deploy production chỉ sau PASS, có rollback.
- Không tự deploy khi chưa có hạ tầng, secret hoặc quyền được xác minh.

## 11. Chỉ tiêu chất lượng đề xuất để kiểm thử

- 1.000 mục: filter/search metadata p95 khoảng <= 1 giây trên hạ tầng chọn, cần đo.
- Dán link/ghi chú: xác nhận đã nhận trong vài giây, media không buộc đồng bộ.
- 100% job hoàn thành/failed đều có trạng thái; retry không nhân đôi mục; restart không mất job.
- Bản gốc mở lại và checksum khớp; xóa mềm có thể khôi phục trước kỳ purge.
- 30–50 nội dung thật dùng đánh giá phân nhóm (precision/coverage) trước khi bật AI auto-assignment.
- MCP: 20 truy vấn có bộ đáp án, trích dẫn đúng ID, không có access trái quyền.
- Backup: có ít nhất một restore drill được ghi nhận trước sử dụng dữ liệu quan trọng.

## 12. Danh sách quyết định CHƯA CHỐT — chỉ cần người dùng xác nhận khi có căn cứ

| ID | Câu hỏi | Phương án mặc định đề xuất | Hệ quả |
|---|---|---|---|
| D01 | Máy chủ đặt ở đâu? | VPS Linux nhỏ (hoặc Oracle nếu có tài nguyên) | Chi phí và độ ổn định |
| D02 | Có domain/subdomain chưa? | Dùng domain HTTPS riêng, 1 origin | PWA/MCP/TLS |
| D03 | Ngân sách vận hành/tháng? | Thiết kế thấp, đo sau 100 mục | VPS/B2/AI |
| D04 | Dùng API AI nào cho phân loại? | Adapter đa provider, quyết sau test | Privacy/cost |
| D05 | Dữ liệu nội bộ/công việc có được gửi AI ngoài? | Mặc định KHÔNG | Phân nhóm AI trên dữ liệu nhạy cảm |
| D06 | Backup thứ hai dùng Drive hay khác? | Drive qua rclone nếu kết nối ổn; có phương án thay | Bảo vệ dữ liệu |
| D07 | Đăng nhập single-user cục bộ hay SSO? | Django Auth + session bảo mật, không public signup | Vận hành/độ phức tạp |
| D08 | UX Android Share Target có đạt không? | Test thực; fallback dán link | Kênh tiếp nhận |
| D09 | Video bị chặn tải xử lý thế nào? | Giữ link, cho upload file riêng | Kỳ vọng |
| D10 | ChatGPT workspace có quyền custom MCP? | Kiểm tra khi đến Bước 3 | Có thể cần admin |
| D11 | Thời gian giữ thùng rác và bản sao? | 30 ngày thùng rác (đề xuất) | Dung lượng/an toàn |
| D12 | Trích toàn văn Excel và file lớn tới đâu? | Giới hạn kích thước/tổng ô, có trạng thái partial | RAM, search chất lượng |

**Quyết định nên chốt ngay để bắt đầu code:** React/TS/Vite + Mantine; Django 6 + Django Ninja; PostgreSQL; B2; mô hình mục tri thức/nguồn/file; API contract; luồng nhập & nhóm; chính sách an toàn dữ liệu. Các quyết định D01–D12 còn mở không được viện làm lý do trì hoãn giao diện demo và test local, nhưng thông số liên quan bảo mật và backup phải chốt trước sản xuất.

## 13. Tham chiếu kỹ thuật (kiểm tra lại khi pin phiên bản)

- Django 6: https://docs.djangoproject.com/en/6.0/
- Django Ninja: https://django-ninja.dev/
- Django OAuth Toolkit MCP: https://django-oauth-toolkit.readthedocs.io/en/latest/
- Mantine: https://mantine.dev/
- React: https://react.dev/ · Vite: https://vite.dev/
- PostgreSQL: https://www.postgresql.org/docs/
- Procrastinate: https://procrastinate.readthedocs.io/
- B2 S3-compatible: https://www.backblaze.com/docs/cloud-storage-s3-compatible-api
- pypdf (BSD-3-Clause): https://pypdf.readthedocs.io/
- PyMuPDF licensing (AGPL/commercial): https://pymupdf.io/licensing
- python-docx: https://python-docx.readthedocs.io/
- openpyxl: https://openpyxl.readthedocs.io/
- Trafilatura: https://trafilatura.readthedocs.io/
- yt-dlp: https://github.com/yt-dlp/yt-dlp
- MCP SDK: https://github.com/modelcontextprotocol/python-sdk
- OpenAI MCP / Plugins: https://developers.openai.com/api/docs/mcp
- OpenAI MCP authentication: https://developers.openai.com/plugins/build/auth
- MCP official Python SDK v2: https://github.com/modelcontextprotocol/python-sdk

---

## 14. RÀ SOÁT ĐỐI CHIẾU CÔNG NGHỆ R1 — 15/11/2026

**Nguyên tắc quyết định:** Mỗi nhóm dưới đây có **ít nhất 2–3 lựa chọn cạnh tranh** được cân nhắc. So sánh dựa trên *đúng nhu cầu sản phẩm (30%), tốc độ phát triển/dễ bảo trì bằng Codex (25%), chi phí (20%), bảo mật/độ ổn định (15%), mở rộng/di chuyển (10%)*. Đây là **trọng số định hướng**, không phải điểm benchmark tự tạo. Chỉ xem lựa chọn là mặc định triển khai; những vấn đề cần kiểm chứng vẫn phải qua gate tương ứng trong ROADMAP_AND_TESTS.

### 14.1. Frontend và Android

| Thành phần | Chọn cho Kho Tri Thức | 2–3 lựa chọn khác đã xét | Đánh giá & lý do |
| --- | --- | --- | --- |
| Framework frontend | **React + TypeScript + Vite** | Vue 3 + Vite; SvelteKit; Next.js | React có thư viện UI/agent hỗ trợ rộng. Vite xây SPA/PWA tĩnh, không phải vận hành SSR Node. Next.js chỉ vượt trội nếu cần SEO/SSR; Vue và Svelte đều tốt nhưng không có lợi ích quyết định với một app quản lý tư nhân |
| Bộ UI | **Mantine v9 + CSS Modules** | shadcn/ui + Tailwind; MUI; Ant Design | Mantine có nhiều component đã hoàn thiện, form, filter, multiselect, modal, date range, tiết kiệm công ghép UI. shadcn hợp thiết kế tùy biến đặc biệt nhưng AI phải duy trì nhiều component copy-in; MUI/Ant có hệ thiết kế riêng, một số data grid nâng cao có phí |
| Router | **React Router** | TanStack Router; Wouter; Next.js App Router | React Router đã đủ cho 4–6 trang và các filter URL. TanStack Router có type safety tốt hơn với ứng dụng nhiều route; Wouter nhẹ nhưng ít tính năng; App Router kéo theo Next stack |
| Server-state/API client | **TanStack Query** | SWR; RTK Query; Apollo Client | REST, cache, retry, invalidation; RTK Query nếu dùng Redux, Apollo nếu GraphQL. Không cần Redux để lưu mọi state |
| Forms | **Mantine Form**, Zod khi dữ liệu phức tạp | React Hook Form + Zod; Formik; Final Form | Đồng bộ UI kit; React Hook Form mạnh cho biểu mẫu nhiều trường, nhưng không có lợi ích rõ ràng ở v1 |
| Điện thoại | **PWA cài trên Android + Share Target nếu đạt test** | Capacitor (bọc web); Flutter native; React Native | Một app dùng Android/Windows, triển khai nhanh. Share Target cần cài PWA và URL từ Android thường xuất hiện trong field text; phải thử với FB/TikTok/YouTube. Nếu không ổn, dùng Capacitor làm vỏ chứ không viết lại |
| Table/list | **Mantine + TanStack Table khi cần** | Ant Design Table; MUI Data Grid; AG Grid | Bản đầu là thư viện card/lưới, không cần grid phức tạp. Khi làm bulk sorting/filter table mới thêm headless table; tránh dùng bản Enterprise phải mua giấy phép |

### 14.2. Backend, CSDL, tìm kiếm và tác vụ

| Thành phần | Chọn cho Kho Tri Thức | 2–3 lựa chọn khác đã xét | Đánh giá & lý do |
| --- | --- | --- | --- |
| Backend | **Django 6 + Django Ninja** | FastAPI; Django REST Framework; NestJS | Django dựng sẵn auth/admin/ORM/migrations; Ninja tạo API có schema, thuận lợi khi dùng chung Python media parser. FastAPI async/API-first tốt nhưng phải ghép nhiều chức năng lõi; DRF đa năng nhưng boilerplate hơn; NestJS buộc chuyển backend TS |
| ORM + migration | **Django ORM + migrations** | SQLAlchemy + Alembic; SQLModel + Alembic; Tortoise + Aerich | Không vận hành 2 hệ ORM/migration trong cùng một dự án Django; có admin hỗ trợ quản lý ban đầu |
| Database | **PostgreSQL tự quản lý** | SQLite + FTS5; Supabase Postgres managed; MariaDB | Tương thích transaction, search, nhiều worker và queue PostgreSQL. SQLite nhẹ cho demo nhưng concurrency/queue không thuận lợi; Supabase free giới hạn 500 MB DB và pause sau 1 tuần không hoạt động; managed paid thường cao hơn VPS nhỏ |
| Search | **PostgreSQL FTS + unaccent + pg_trgm** | Typesense; Meilisearch; OpenSearch | Không thêm search service và đồng bộ index. **Không đánh đồng Postgres FTS mặc định với tìm kiếm tiếng Việt tối ưu**; Typesense có locale vi, là fallback nếu kết quả thử từ ghép và gõ không dấu không đạt; OpenSearch nặng hơn |
| Queue | **Procrastinate tích hợp Django — CẦN THỬ** | Chancy (Postgres); PgQueuer (Postgres); Dramatiq + Redis | Procrastinate có Django migrations/admin và worker riêng, không đòi Redis; nhưng dự án đang tìm maintainer. Test multi-worker, crash/retry, duplicate, dead jobs trước khi chốt thực tế; không tự code queue khi có thư viện phù hợp |
| API contract | **REST + Django Ninja OpenAPI** | DRF + drf-spectacular; FastAPI OpenAPI; Strawberry GraphQL | REST đủ cho app và MCP read tools; GraphQL làm tăng mô hình schema/quyền/truy vấn chưa cần thiết |

### 14.3. File, nội dung và AI

| Thành phần | Chọn cho Kho Tri Thức | 2–3 lựa chọn khác đã xét | Đánh giá & lý do |
| --- | --- | --- | --- |
| Kho file chính | **Backblaze B2 private, S3-compatible adapter** | Cloudflare R2; Wasabi; Supabase Storage | B2 rẻ theo GB, giá công bố từ $6.95/TB-tháng, 10 GB đầu miễn phí, free egress tới 3× dung lượng trung bình. R2 không tính egress nhưng giá tiêu chuẩn $0.015/GB-tháng; chọn R2 làm kho chính nếu tần suất xem cao/egress B2 vượt hạn mức. Không thay nếu chưa đo |
| Sao lưu ngoài nhà cung cấp chính | **Cloudflare R2 cho bản sao quan trọng + pg_dump/restic** | Google Drive 500 GB qua rclone; AWS S3; IDrive e2 | R2 tách nhà cung cấp khỏi B2, có 10 GB free; Drive 500 GB rất đáng tận dụng cho bản sao khối lượng lớn nhưng OAuth cần giám sát. Không giữ tất cả file không thể tái tạo chỉ trên một provider. Backup đạt PASS chỉ sau kiểm thử restore |
| Downloader | **yt-dlp stable + ffprobe/FFmpeg** | Cobalt; gallery-dl; Streamlink | yt-dlp bao phủ nhiều nền tảng, có metadata và phụ đề, đã thử trong benchmark riêng. Cobalt dự phòng có điều kiện, gallery-dl cho album/ảnh, Streamlink cho live; không có giải pháp bảo đảm Shorts từ cloud IP |
| PDF có chữ | **pypdf**; pdfplumber cho trang/bảng khó | pdfplumber; PyMuPDF; pypdfium2 | pypdf dễ tích hợp và giấy phép BSD; pdfplumber hỗ trợ bố cục/bảng nhưng tốn hơn; PyMuPDF mạnh và nhanh nhưng cần kiểm tra nghĩa vụ AGPL hoặc giấy phép thương mại |
| DOCX | **python-docx** | Mammoth; Docling; LibreOffice headless | Lấy paragraph, table đủ cho phân loại/tìm kiếm; không cần cài bộ Office chạy nền. Mammoth phù hợp chuyển HTML, Docling dành cấu trúc sâu |
| XLSX | **openpyxl** | python-calamine; pandas; LibreOffice headless | Giữ sheet/toạ độ ô và công thức/giá trị khi cần; đọc theo streaming với file lớn. pandas thiên phân tích và làm mất ngữ cảnh tọa độ nếu dùng trực tiếp |
| Bài viết web | **Trafilatura** | readability-lxml; newspaper4k; Crawl4AI | CPU nhẹ, loại boilerplate và thu metadata. Benchmark công bố 2026 cho kết quả cao nhưng là phép đo của tác giả, vẫn phải thử trên trang web Việt. Không cài browser/Playwright production ngay |
| AI phân nhóm | **Rule-based trước; Gemini 2.5 Flash-Lite trả phí khi được phép** | OpenAI GPT-6 Luna; Gemini 3.1 Flash-Lite; mô hình mở nhỏ chạy local | Phân loại chi phí thấp, có schema và taxonomy. Gemini Flash-Lite được công bố giá tham chiếu $0.10 input/$0.40 output /1M token cho 2.5 (paid); free-tier có chính sách sử dụng dữ liệu khác, **không gửi tài liệu công việc cá nhân nhạy cảm**. Phải đo chất lượng tiếng Việt bằng mẫu 30–50 item trước khi tự gắn nhóm |

### 14.4. MCP, xác thực, hạ tầng và kiểm thử

| Thành phần | Chọn cho Kho Tri Thức | 2–3 lựa chọn khác đã xét | Đánh giá & lý do |
| --- | --- | --- | --- |
| MCP protocol/runtime | **Official Python MCP SDK v2 với `MCPServer` + Streamable HTTP** | FastMCP framework độc lập; fastapi-mcp; tự viết protocol | SDK chính thức theo spec MCP mới, không phụ thuộc FastAPI. **Không copy code official SDK v1 gọi `FastMCP`**; đọc tài liệu v2 tại thời điểm code |
| Xác thực ứng dụng | **Django Auth + session cookie + CSRF** | Supabase Auth; Auth0; Keycloak | Một người sử dụng, built-in đủ mạnh và tránh phí/dịch vụ mới; không public registration |
| OAuth cho MCP | **Django OAuth Toolkit >=3.4 — kiểm thử trước khi công bố** | Auth0; ZITADEL; Keycloak | DOT 3.4 hỗ trợ MCP authorization-server role, PKCE, protected resource metadata, CIMD/DCR. Chung Django user nên dễ vận hành; nếu ChatGPT interoperability/refresh không đạt, thử IdP managed thay thế. Không thay bằng static key public |
| HTTPS / reverse proxy | **Caddy** | Nginx; Traefik; Nginx Proxy Manager | Một domain và vài container, Caddy tự cấp/gia hạn TLS và file cấu hình ngắn; Traefik hợp nhiều dịch vụ auto discovery |
| Server/region | **Một VPS Linux Docker; ưu tiên Oracle A1 nếu cấp được, fallback VPS Singapore** | DigitalOcean Singapore; Hetzner Singapore; Render/Railway | Oracle Always Free 2 OCPU/12 GB tương đương nhưng có rủi ro không có capacity. DO tham chiếu 2GB $12/tháng, 4GB $24/tháng; Hetzner SG thay đổi giá 06/2026, không so bằng giá châu Âu. **Chọn nhà cung cấp thực sau khi biết tài khoản, ngân sách và thử độ trễ** |
| Deployment | **Docker Compose (Django ASGI + worker + Postgres + Caddy + frontend static)** | Railway; Render; Kubernetes | Chi phí tổng thấp và di chuyển dễ với 1 VM; Railway/Render giảm vận hành nhưng tính phí compute/worker/DB; Kubernetes dư cho một người |
| CI/E2E | **pytest-django + Vitest + React Testing Library + Playwright CI + GitHub Actions** | Jest + Cypress; Selenium; TestCafe | Trải nghiệm React và Django có test đơn vị đến E2E. Playwright ở CI không phải đưa Chromium vào worker xử lý website |
| Giám sát | **Structured logs, healthchecks, backup/job alarms; thêm Uptime Kuma khi cần** | Sentry; Prometheus/Grafana; Datadog | Ưu tiên phát hiện mất file, lỗi tác vụ và backup; không tạo stack monitoring nhiều dịch vụ trước khi có tải thực tế |

### 14.5. Kết luận quyết định và cổng kiểm chứng

**Thay đổi chủ yếu so với lựa chọn ban đầu:**
1. **Mantine thay shadcn/ui** cho UI kit chính; React/TS/Vite giữ nguyên.
2. **Django 6 + Django Ninja + Django ORM** thay FastAPI/SQLAlchemy/Alembic: có auth/admin/migrations sẵn, phù hợp hệ thống quản lý dữ liệu cá nhân.
3. **Django OAuth Toolkit >=3.4** là ứng viên đầu cho MCP OAuth sau khi thư viện hoạt động; cần test thật với ChatGPT.
4. **Official MCP SDK v2 (`MCPServer`)** thay mọi ví dụ lỗi thời của SDK v1.
5. B2 là kho chính; backup tối thiểu ở R2 độc lập, Google Drive 500 GB là nơi backup mở rộng khi cấu hình được.
6. Queue Procrastinate chưa coi là PASS: chỉ khóa sau các bài thử restart/retry/multi-worker.
7. Nơi đặt VM và AI provider chưa phải hợp đồng: chỉ chọn sau khi đo ngân sách/tài nguyên/chất lượng và quyền riêng tư.

**Thử trước khi khóa production:**
- 30–50 item thật: so tốc độ thao tác và phân nhóm Mantine UI, đo chất lượng AI/không dấu.
- B2↔R2: upload, verify SHA256, backup và restore.
- Procrastinate: crash giữa task, retry an toàn, dedup, restart worker, lỗi network.
- Android: cài PWA; chia sẻ link từ Facebook/TikTok/YouTube, lấy URL từ text/title khi cần.
- MCP: OAuth metadata/CIMD/DCR, token audience/scope/expiry, ChatGPT web thực tế.
- VPS: CPU/RAM trong tải lớn, độ trễ tới Việt Nam, egress, backup riêng.

### 14.6. Tài liệu gốc dùng khi đối chiếu

- React/Vite/Mantine: https://vite.dev/ · https://mantine.dev/
- Django/Django Ninja/DOT: https://docs.djangoproject.com/en/6.0/ · https://django-ninja.dev/ · https://django-oauth-toolkit.readthedocs.io/en/latest/
- PostgreSQL/Typesense: https://www.postgresql.org/docs/current/pgtrgm.html · https://typesense.org/docs/guide/locale.html
- Procrastinate/Chancy: https://procrastinate.readthedocs.io/en/stable/howto/django.html · https://pypi.org/project/chancy/
- B2/R2/Supabase: https://www.backblaze.com/cloud-storage/pricing · https://developers.cloudflare.com/r2/pricing/ · https://supabase.com/pricing
- yt-dlp/pypdf/Trafilatura: https://github.com/yt-dlp/yt-dlp · https://pypdf.readthedocs.io/ · https://trafilatura.readthedocs.io/en/latest/evaluation.html
- Gemini/OpenAI API: https://ai.google.dev/gemini-api/docs/pricing · https://developers.openai.com/api/docs/pricing
- MCP v2/OpenAI auth: https://github.com/modelcontextprotocol/python-sdk · https://developers.openai.com/plugins/build/auth
- Oracle/DO/Hetzner: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm · https://www.digitalocean.com/pricing/droplets · https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/
- Caddy/Android share: https://caddyserver.com/docs/automatic-https · https://developer.chrome.com/docs/capabilities/web-apis/web-share-target

**Đây là bản đánh giá công nghệ, chưa có test triển khai và không thay đổi phạm vi sản phẩm v4.2.** Khi phát hành phải kiểm lại giá, license, versions và kết quả test thực.
