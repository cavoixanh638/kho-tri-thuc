# KIẾN TRÚC & QUYẾT ĐỊNH KỸ THUẬT — V4.3 DRIVE-FIRST, TINH GỌN

**Ngày:** 15/11/2026 · **Thay thế toàn bộ các đề xuất R1 trước đây trong file này.**  
**Phạm vi:** Một người dùng, nội dung không quá phức tạp, ít yêu cầu bảo mật nâng cao; **Google Drive là kho file chính**. Các lựa chọn dưới đây là **đề xuất thiết kế**, không phải code đã triển khai.

## 1. Chỉ làm những gì tạo giá trị

Ứng dụng này KHÔNG cần xây như hệ thống doanh nghiệp đa người dùng. Nhu cầu thật:
- Gửi link/ảnh/file/ghi chú từ Windows/Android.
- File lưu trên **Google Drive của chủ sở hữu**; video tải được thì lưu file, không tải được giữ link.
- Tự lấy thông tin, gợi ý phân nhóm theo lĩnh vực/dự án; xem theo ngày.
- Tìm kiếm trong metadata, ghi chú, văn bản tài liệu dễ trích xuất.
- ChatGPT nghiên cứu tài liệu **qua Google Drive app có sẵn trước**; MCP riêng chỉ nếu phát sinh nhu cầu truy vấn dữ liệu phân nhóm.

**Bỏ khỏi bản đầu:** Backblaze B2, Cloudflare R2, PostgreSQL server, Redis, Procrastinate, microservices, Elasticsearch/Typesense, dịch vụ OAuth riêng cho MCP, Storage Adapter đa provider, Kubernetes, ASR/OCR/embedding hàng loạt, captcha/RBAC/audit enterprise, hệ thống metrics lớn.

## 2. Kiến trúc tối giản đề xuất

```text
Android / Windows
        |
        v
  Web/PWA (React + Mantine; build static)
        |
        v
  Django + Django Ninja (1 backend; 1 user login)
       /            \
   SQLite         Google Drive API (OAuth drive.file)
   index & jobs   originals: video/photo/docs
       |
  Python worker đơn giản (1 tiến trình)
  -> yt-dlp -> upload Drive -> metadata/text -> AI gợi ý
       |
  Backup SQLite/JSON vào Drive, định kỳ copy snapshot ra PC

ChatGPT -> thử Google Drive app trực tiếp
       -> chỉ khi cần mới làm MCP đọc API/library index
```

- **Một codebase backend, một frontend build tĩnh**; không chạy Node server production.
- Có thể chạy local trong Windows/WSL trước; khi cần tự động 24/7 thì đưa lên một VPS nhỏ.
- Frontend và API dùng cùng origin HTTPS khi công khai, tránh cấu hình CORS rườm rà.
- Dữ liệu file và database tách: Drive giữ bản gốc, SQLite là chỉ mục. Tối thiểu phải xuất chỉ mục/snapshot khi mất server.
- **Không đặt SQLite đang mở trong Google Drive Desktop hoặc rclone mount**: có thể hỏng database khi đồng bộ file đang ghi. Chỉ đẩy snapshot đóng băng an toàn.

## 3. Bảng so sánh lựa chọn với 2–3 phương án cạnh tranh

**Tiêu chí:** phù hợp nhu cầu cá nhân; ít code phải duy trì; chi phí; độ tin cậy; khả năng dùng Android/ChatGPT. Không chấm điểm số giả khi chưa test.

| Quyết định | Chọn | 2–3 phương án thay thế | Vì sao phù hợp, vì sao không chọn khác lúc này |
| --- | --- | --- | --- |
| Kho file chính | **Google Drive cá nhân (My Drive)** | Backblaze B2; Cloudflare R2; Dropbox | Có sẵn ~500 GB trong năm đầu, quản lý trực tiếp trên Drive, xem file ngay, ChatGPT có plugin Drive. B2/R2 rẻ nhưng phải trả thêm và tự xây preview/cấp URL; chỉ xem xét khi Drive đầy/hết ưu đãi hoặc tải video liên tục rất lớn. |
| Kết nối Drive | **Google Drive API v3 + OAuth 2.0, scope `drive.file`** | Google Apps Script/DriveApp; rclone; service account | File do app tạo/ghi có ID ổn định, tải file lớn resumable, backend Python dùng trực tiếp. Apps Script dễ cấp quyền Drive nhưng khó chạy yt-dlp và giới hạn thời gian; rclone tốt để backup chứ không thuận tiện gắn metadata từng item; service account không có quota cá nhân để sở hữu file. |
| Metadata/database | **SQLite trên ổ backend** | Google Sheets; PostgreSQL; Supabase | 1 người dùng, vài nghìn đến vài chục nghìn mục, nhiều bộ lọc/quan hệ, FTS5, không thêm DB server/chi phí. Sheets dễ mở tay nhưng tìm toàn văn/quan hệ và cập nhật nhiều bước bất tiện; Postgres thừa; Supabase thêm phụ thuộc. **Backup lên Drive** để người dùng vẫn có dữ liệu. |
| Backend | **Django + Django Ninja** | FastAPI; Google Apps Script; Node/NestJS | Django có login/admin/ORM/migrations, Ninja REST typed/OpenAPI; backend Python dùng yt-dlp và thư viện tài liệu. FastAPI nhẹ hơn về framework nhưng tự ráp auth/admin/migration; Apps Script không chạy Python video downloader; NestJS lại cần worker Python riêng. |
| Frontend | **React + TypeScript + Vite (static build)** | Django templates + HTMX; Vue 3; Google Apps Script HTML Service | Người dùng cần thao tác nhanh, thư viện ảnh/video + bộ lọc mượt, cài PWA Android. React+Vite dùng static bundle, không cần SSR/Node runtime; HTMX đơn giản hơn và là fallback nếu MVP phình to; Apps Script HTML bị sandbox iframe và không tối ưu Share Target. |
| UI kit | **Mantine**, tối giản component | shadcn/ui; MUI; Ant Design | Form/tag/multiselect/date picker và responsive sẵn, hợp phần mềm quản lý. Không thêm nhiều hệ UI hoặc data grid trả phí. |
| Search | **SQLite FTS5 + trường normalized tiếng Việt** | SQL LIKE; Meilisearch; Typesense | Không thêm search server. FTS5 unicode61 remove_diacritics=2 hỗ trợ phần lớn dấu Latin nhưng cần chuẩn hóa `đ/Đ` và thử search chuỗi tiếng Việt. LIKE là fallback với dữ liệu ít; Typesense chỉ khi test FTS thật không đạt. |
| Tác vụ nền | **Bảng `jobs` SQLite + 1 Python worker** | Procrastinate/PostgreSQL; Celery+Redis; Apps Script triggers | Tải video/trích xuất tuần tự, ít tác vụ. DB có `status, attempts, next_run, error`; worker restart/retry. Không cần dịch vụ queue; nếu tải tăng mới chuyển thư viện. |
| Tải video | **yt-dlp stable + ffprobe/FFmpeg** | Cobalt; gallery-dl; Streamlink | yt-dlp đã có benchmark riêng và xử lý URL/metadata/phụ đề; không hứa mọi YouTube Shorts do hạn chế IP/bot. Cobalt chỉ là fallback sau khi được test lại; gallery-dl thiên ảnh; Streamlink thiên livestream. |
| Đọc tài liệu | **pypdf + python-docx + openpyxl + Trafilatura** | PyMuPDF; Docling; LibreOffice; Crawl4AI | PDF có chữ, DOCX/XLSX và bài web thông thường đủ cho phân loại; nhẹ, ít phụ thuộc. PyMuPDF AGPL/commercial cần xem giấy phép, Docling/LibreOffice nặng, Crawl4AI cần browser cho JS. |
| AI phân nhóm | **Quy tắc + một API mô hình nhẹ khi cần** | Gemini Flash-Lite; OpenAI mô hình nhỏ; mô hình local | Chưa khóa provider. Nếu tiêu đề/metadata rõ thì không cần gọi AI; trường hợp mơ hồ mới dùng AI ảnh/đoạn text. Mô hình local tăng RAM trên VPS, không hợp bản đầu. Chọn provider sau thử 30–50 mục. |
| ChatGPT đọc tài liệu | **Google Drive app có sẵn trong ChatGPT (thử trước)** | MCP riêng; Custom GPT Actions; thủ công gửi file | Không phải dựng server OAuth/tool nếu chỉ muốn ChatGPT nghiên cứu file Google Drive. MCP chỉ đáng làm khi cần ChatGPT tìm theo tags/projects của app; Actions thêm tích hợp thứ hai và không tối ưu chiến lược. |
| MCP nếu cần | **Official MCP Python SDK, chỉ đọc** | Framework FastMCP độc lập; tự viết; không triển khai MCP | Có thể gọi API tìm/đọc hiện có, tách hẳn khỏi phần quản lý chính; nhưng **hoãn cho đến khi đã thử Drive connector**. Với MCP công khai truy cập riêng phải có xác thực, không bỏ bảo vệ chỉ vì ít người dùng. |
| Đăng nhập | **Django Auth (một tài khoản) + HTTPS** | Google Sign-In; Auth0; Keycloak | Không tự viết login và không tạo nhiều role; dịch vụ đăng nhập thứ ba và Keycloak dư nhu cầu. Google OAuth để Drive là **kết nối lưu trữ**, không đồng nghĩa đã có đăng nhập website. |
| Hosting | **Chạy local trước; nếu muốn 24/7 thì 1 VPS nhỏ Linux** | Oracle Always Free; Render/Railway; Apps Script only | Phát triển local không cần trả tiền; VPS một máy đủ chạy Python downloader/SQLite. Oracle miễn phí nếu cấp được máy, có rủi ro hết capacity; Railway/Render đơn giản deploy nhưng phí worker/disk có thể phát sinh; Apps Script không tải video Python. |
| Triển khai | **Một backend + một worker, static frontend; Docker Compose tùy chọn** | systemd + venv; nhiều container/microservices; Kubernetes | Có thể dùng systemd khi đơn máy, Docker Compose nếu Codex cần môi trường lặp lại. Không triển khai PostgreSQL/Redis/Caddy/CDN như các service riêng khi không cần; HTTPS qua Caddy hoặc proxy hạ tầng. |
| Sao lưu | **Snapshot SQLite/JSON lên Drive + bản copy PC định kỳ** | B2; R2; AWS S3 | Mục tiêu giảm chi phí và thao tác. Drive vẫn chứa file gốc; backup SQLite lên cùng Drive giúp phục hồi khi VPS hỏng, nhưng KHÔNG bảo vệ nếu tài khoản Drive mất. Khi dữ liệu quan trọng phải có một bản ngoài Drive. |
| Test | **pytest Django + vài E2E browser quan trọng** | Test thủ công; Playwright toàn bộ; test stack chuyên nghiệp | Cần test upload, login, OAuth, retry, search, restore; không làm framework test khổng lồ hoặc CI hàng chục workflow. |

**Các quyết định tạm thời có căn cứ:** Google Drive chính, SQLite, Django/Ninja, React/Vite/Mantine, 1 worker, yt-dlp, trích xuất nhẹ. **Chưa chốt:** máy chủ thật, giới hạn upload, AI provider và quyền/điều kiện plugin Drive của ChatGPT.

## 4. Drive — cách làm đúng và những giới hạn bắt buộc biết

### 4.1. Thiết kế một thư mục người dùng hiểu được

- Tạo thư mục `Kho Tri Thuc` trong **My Drive** bằng app.
- Có thể tạo thư mục con theo **loại file** (Video/Tai lieu/Hinh anh/He thong). Không tạo thư mục theo mọi lĩnh vực, dự án hoặc ngày; một item có thể ở nhiều nhóm.
- Bản gốc giữ file thường có thể tải bằng Drive; metadata SQLite giữ link/id, tên gốc, nguồn và ngày.
- App cần quyền `drive.file` để làm việc với file do app tạo; **không mặc định xem được tất cả file Google Drive có sẵn**. Import tài liệu sẵn có làm sau, có thể bổ sung Google Picker.
- Upload file lớn qua **resumable upload**; retry lỗi API/quota/429; hạn chế concurrent video jobs.
- Link xem video/tài liệu: ưu tiên **Drive viewer/webViewLink** trên trình duyệt đã đăng nhập; không xây HLS/streaming proxy v1. Kiểm tra preview MP4 thật trước khi hứa player nhúng trong app.
- Không dùng service account trần để ghi file vào My Drive cá nhân: Google nói service account không có quota và không sở hữu file; phải OAuth thay mặt user.

### 4.2. Điểm OAuth không thể “cắt” dù app đơn giản

- Dùng thư viện OAuth chuẩn, lưu refresh token ở server (không commit hay gửi ra frontend).
- Dùng `drive.file` để giới hạn quyền; không yêu cầu `drive` rộng nếu không thật sự cần.
- Google OAuth **External + Testing** thường có refresh token hết hạn sau **7 ngày**. Khi triển khai lâu dài, đánh giá chuyển app sang `In production`; trạng thái Production không bảo đảm token không bao giờ bị thu hồi.
- Có nút/kịch bản **Kết nối lại Google Drive** khi `invalid_grant`.
- Một trang trạng thái phải phân biệt *đã nhận nội dung*, *đã upload lên Drive*, *chưa có file do link lỗi*.

### 4.3. Vì sao không chọn Apps Script làm toàn hệ thống?

| Lợi | Hạn chế |
| --- | --- |
| Dùng DriveApp và Google login thuận tiện, ít hạ tầng | Apps Script bị giới hạn 6 phút/execution; UrlFetch ~50MB/call; không chạy yt-dlp, FFmpeg |
| Dễ làm form + Sheets lưu metadata | UI PWA Share Target/iframe sandbox không thuận tiện; tải video phải có Python worker bên ngoài |
| Phù hợp demo chỉ gồm ghi chú, liên kết, PDF nhỏ | Với video và MCP về sau lại phải tạo backend riêng |

**Kết luận:** Apps Script là lựa chọn hợp lý nếu bỏ nhu cầu tự động tải video; hiện không ưu tiên vì video nằm trong nhu cầu chính.

## 5. Data model giảm xuống mức cần thiết

Đề xuất SQLite các bảng nghiệp vụ (không sinh CRUD cho mọi bảng):

| Bảng | Nội dung |
| --- | --- |
| `items` | id, kind, title, description, note, source_url, published_at (nullable), saved_at, favorite, deleted_at |
| `files` | id, item_id, drive_file_id, filename, mime, size, status, checksum nullable |
| `groups` | id, type `field/topic/project`, name, parent_id nullable |
| `item_groups` | item_id, group_id, origin `user/ai`, pinned |
| `extracted_text` | item_id, text, kind, status, source_locator, updated_at |
| `jobs` | id, item_id, kind, state, attempts, next_run, error, updated_at |

- Tag đơn giản có thể lưu JSON/text trong `items` rồi chuẩn hóa sau nếu cần; ngày là **cách xem**, không phải thư mục.
- FTS5 là chỉ mục của title/description/note/extracted_text; dữ liệu thật là bảng nguồn, có thể rebuild FTS.
- Ban đầu chưa cần `storage_locations`, `revisions`, `backup_runs`, `AIExecution`, `EmbeddingModel`, `ChunkEmbedding`, `Claim`...
- `drive_file_id` là tham chiếu; không gán toàn quyền Drive để đọc mọi file khác.
- Với dữ liệu nhẹ, SQLite có thể nhiều chục nghìn mục; khi phát sinh concurrency/khối lượng mới benchmark rồi cân nhắc PostgreSQL.

## 6. Backend và API tối thiểu

Django cung cấp login/session/admin/migration, Django Ninja làm API khoảng 8–10 endpoints:
- `POST /api/ingest`: dán 1 URL, trả item ID/status.
- `POST /api/notes`: tạo ghi chú.
- `POST /api/upload`: file nhỏ; với video lớn dùng chunked/resumable trong backend, lưu tạm lên ổ và upload Drive.
- `GET /api/items`, `GET /api/items/{id}`: danh sách/chi tiết.
- `PATCH /api/items/{id}`: sửa metadata/tag/nhóm.
- `GET /api/search`: keyword + faceted filters.
- `GET /api/groups` / `POST /api/groups`: chủ đề/dự án.
- `GET /api/jobs/{id}`: theo dõi download/upload/extract.
- `GET /api/drive/connect`, `GET /api/drive/callback`, `GET /api/drive/status`: OAuth/Drive.

Khi mới phát triển, ưu tiên **upload qua backend** cho đơn giản; nếu file lớn thường xuyên và cần performance, tách upload session/resumable nhưng không phức tạp hóa UI ngay. Tệp tạm worker phải được dọn sau khi Drive đã xác nhận upload thành công.

## 7. Frontend MVP chỉ 4 màn hình

1. **Thêm**: dán link, nhập ghi chú, kéo/thả file, nút Gửi; xác nhận nhận link nhanh, tiến trình thực tế không bị che.
2. **Thư viện**: card/list, xem theo *Lĩnh vực — Dự án — Ngày — Loại*, bộ lọc.
3. **Chi tiết**: mở Drive, hiện metadata, tóm tắt/trích chữ có sẵn, sửa nhóm/tag, trạng thái.
4. **Cài đặt**: Google Drive đã kết nối chưa, dung lượng còn, trạng thái job, sao lưu, xuất danh mục.

- React + Mantine nhưng **chỉ dùng state cơ bản/natives fetch** trước; không tự cài Redux, React Query, React Hook Form, TanStack Table và thư viện khác khi chưa có điểm nghẽn.
- Build thành static bundle. Điều hướng React Router chỉ nếu cần deep link phức tạp; vài màn hình có thể dùng router tối giản.
- Android Share Target chỉ bật sau thử trên máy thật; nếu chưa hỗ trợ, dán link bằng web là luồng đầy đủ.
- Thumbnail, danh sách và video Drive viewer; không build custom video streaming.

## 8. Worker siêu gọn nhưng không để mất job

- Một `manage.py process_jobs` chạy process riêng từ cùng mã Django; polling SQLite, xử lý tối đa 1 tác vụ media tại một thời điểm.
- Trạng thái: `queued → running → done/failed`, có `attempts` và `next_run`; khi process chết, job chạy dở quá hạn có thể quay về queue.
- Idempotency bằng normalized URL/platform ID và `drive_file_id` đã lưu; upload thất bại có thể retry mà không tự tạo nhiều file nếu đã có.
- Không bắt buộc cài Redis, Celery, Procrastinate, RabbitMQ hoặc dịch vụ scheduler riêng.
- Giới hạn dung lượng URL/file, thời gian tải, tổng dung lượng lưu tạm; không cho yt-dlp truy cập địa chỉ nội bộ/localhost.

## 9. ChatGPT — không tự xây MCP nếu đã có giải pháp

**Tầng 1 (làm ngay khi có file):** ChatGPT có Google Drive app chính thức; khi tài khoản/workspace hỗ trợ và đã kết nối, có thể tìm và làm việc với tài liệu Drive. Thử 3–5 tài liệu thật trước khi tự code.

**Tầng 2 (chỉ khi cần):** Nếu ChatGPT phải hỏi *“tìm tất cả mục đã gắn dự án A, tag B, theo ngày lưu”* thì Google Drive có thể không biết metadata riêng của SQLite. Lúc đó xây MCP chỉ đọc với `search` và `fetch` dùng lại Django service API.

**Giới hạn:** File MP4 không có transcript không tự thành dữ liệu văn bản cho ChatGPT chỉ vì đã nằm trên Drive; cần phụ đề hoặc xử lý theo yêu cầu.

**Nếu MCP riêng:** ưu tiên SDK chính thức, thử Secure MCP Tunnel trong ChatGPT khi quyền workspace/Platform cho phép, tránh triển khai OAuth server riêng quá sớm; nếu phải public endpoint truy cập dữ liệu riêng thì dùng xác thực chuẩn. Không mở endpoint read Drive nặc danh.

## 10. Chi phí, sao lưu và chọn máy chủ

- Bản đầu tự phát triển trên Windows/local có thể không tốn VPS; cần cloud 24/7 mới thuê một VPS nhỏ.
- Drive đã có 500 GB: không phát sinh phí kho B2/R2 ban đầu, nhưng vẫn có giới hạn upload/quota/API và chi phí tiếp tục khi hết khuyến mại.
- SQLite backup bằng snapshot nhất quán (SQLite Backup API/VACUUM INTO) và JSON export lên thư mục `He thong/Backup` trong Drive. **Không copy file SQLite đang mở bằng đồng bộ live.**
- Bản sao SQLite trên Drive giúp phục hồi khi VPS hỏng, nhưng nếu Drive bị mất/xóa thì cả file và backup có thể mất. Để có an toàn tối thiểu, tải bản ZIP/thư mục quan trọng về Windows định kỳ, hoặc thêm kho khác khi dữ liệu thật sự quan trọng.
- Không cần Prometheus, Grafana, Sentry, audit log cho mọi thao tác; chỉ cần màn hình lỗi job/Drive, log có giới hạn và cảnh báo backup thất bại.

## 11. Điều kiện phải kiểm thử trước khi coi là chốt thật

1. Google OAuth `drive.file`: tạo folder, upload ảnh/PDF/video lên chính tài khoản, mở webViewLink; 7-day refresh token testing vs production, `invalid_grant` reconnect.
2. File >5MB: resumable upload, bị mất mạng giữa upload, retry không nhân đôi file.
3. Android: dán/chia sẻ link vào PWA, mở file Drive với tài khoản đang đăng nhập.
4. yt-dlp trên host thực: FB/TikTok/YouTube cụ thể, file thật, subtitle khi có; thất bại link-only không chặn.
5. SQLite search: tiếng Việt có/không dấu kể cả `đ`, 1.000 mục và 20 truy vấn.
6. Worker restart/duplicate/rate limit; không xác nhận lưu khi Drive chưa có file.
7. Backup/restore SQLite vào máy thử và mở được tài liệu qua drive_file_id.
8. ChatGPT Google Drive app: thử đọc/so sánh file thật, nếu tính năng này đáp ứng thì **không tạo MCP**.

## 12. Những quyết định còn mở (không chặn thiết kế UI)

- Drive account nào là chủ sở hữu thực, quota hiện còn và hạn 500 GB?
- Có cần dùng hệ thống 24/7 hay có thể chạy local ban đầu?
- Có bao nhiêu video/ngày, trung bình bao nhiêu MB; dung lượng ổ tạm cần bao nhiêu?
- Chọn API AI (sau test chất lượng tiếng Việt) và giới hạn chi phí/ngày.
- ChatGPT workspace có kết nối Google Drive app và đọc được file do hệ thống tạo hay không?
- Khi Drive gần hết 500 GB: nâng dung lượng hay chuyển video sang kho khác?
- Kích thước file tối đa, chu kỳ backup ra PC.

## 13. Nguồn kỹ thuật cần giữ để Codex xác minh lại khi triển khai

- Google Drive scope `drive.file`: https://developers.google.com/workspace/drive/api/guides/api-specific-auth
- Google Drive resumable upload: https://developers.google.com/workspace/drive/api/guides/manage-uploads
- Google Drive download/preview: https://developers.google.com/workspace/drive/api/guides/manage-downloads
- Google OAuth testing 7 days: https://developers.google.com/identity/protocols/oauth2
- Google Apps Script limits: https://developers.google.com/apps-script/guides/services/quotas
- Service account and Drive ownership: https://developers.google.com/workspace/drive/api/guides/folder
- SQLite FTS5: https://www.sqlite.org/fts5.html
- Django: https://docs.djangoproject.com/en/6.0/
- Django Ninja: https://django-ninja.dev/
- React/Vite/Mantine: https://react.dev/ · https://vite.dev/ · https://mantine.dev/
- ChatGPT Google Drive: https://help.openai.com/en/articles/10929079-google-drive-app-and-setup-in-chatgpt
- Secure MCP Tunnel: https://developers.openai.com/api/docs/guides/secure-mcp-tunnels
- yt-dlp: https://github.com/yt-dlp/yt-dlp

**Trạng thái:** quyết định thiết kế sau rà soát overengineering; chưa triển khai code hoặc đo hiệu năng trong repo.
