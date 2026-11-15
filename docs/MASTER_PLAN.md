# KHO TRI THỨC — KẾ HOẠCH TỔNG THỂ V4.4
## Nhỏ khi vận hành, sẵn đường nâng cấp dài hạn

**Ngày:** 15/11/2026 · **Thay thế v4.3** · **Trạng thái:** thiết kế, chưa có mã nguồn ứng dụng.  
**Nguồn quyết định:** người dùng muốn **Google Drive là kho file chính**, sử dụng cá nhân, tự sắp xếp theo lĩnh vực/dự án/xem theo ngày, có thể kết nối ChatGPT và mở rộng AI trong tương lai. Tránh cả overengineering lẫn làm quá sơ sài dẫn đến viết lại hệ thống.

## 1. Mục tiêu của bản đầu

- Tiếp nhận URL FB/TikTok/YouTube/web, video, ảnh, tài liệu PDF/DOCX/XLSX và ghi chú bằng Android/Windows.
- Lưu file gốc trên Google Drive My Drive do chủ sở hữu kết nối, video chỉ tải khi nền tảng cho phép và công cụ hoạt động; link thất bại vẫn được giữ.
- Thu thập metadata và văn bản dễ lấy (PDF có chữ, DOCX, XLSX, HTML, phụ đề có sẵn); chạy nền, không làm nghẽn lưu file.
- Gợi ý lĩnh vực, chủ đề, dự án, nhãn bằng AI nhẹ, có thể sửa; xem theo ngày mà không nhân bản file.
- Tìm kiếm từ khóa và lọc; quản lý đánh dấu quan trọng, xóa mềm, khôi phục.
- Đọc/nghiên cứu file qua **ChatGPT Google Drive app trước**. MCP riêng là tính năng có điều kiện nếu cần tìm bằng phân loại/ghi chú riêng của Kho Tri Thức.

**Không triển khai trong bản đầu:** OAuth server riêng cho MCP, ASR/OCR hàng loạt, embeddings, chatbot nội bộ, graph, CDN, kho S3 thứ hai, microservices, Kubernetes, multi-tenant UI hoặc hệ thống bảo mật doanh nghiệp.

## 2. Những quyết định PHẢI thiết kế đúng từ đầu

1. **Hai loại định danh:** mỗi mục có `item_id` UUID, mỗi file có `asset_id` UUID; Google Drive `drive_file_id` chỉ là **mã vị trí lưu**, không được làm khóa nghiệp vụ. Tách `Asset` và `StorageLocation` (bản đầu chỉ một location Drive).
2. **Tách các tầng dữ liệu:** bản gốc và nguồn; dữ liệu trích xuất/AI có thể tái tạo; thông tin người dùng sửa/chốt **không được AI tự ghi đè**.
3. **Nhóm là quan hệ many-to-many** cho lĩnh vực/chủ đề/dự án/tag; ngày là thuộc tính lọc, không phải đường dẫn thư mục.
4. **Backend có API ổn định `/api/v1/`**, các nghiệp vụ lưu/truy xuất/tìm kiếm nằm trong service để sau này phục vụ PWA, Android native và MCP mà không viết lại.
5. **Storage driver nhỏ ngay từ đầu:** `DriveStorage` hiện thực giao diện `save/open/verify/delete/locate`. Chưa cần hiện thực B2/R2 hoặc migration engine.
6. **Job trạng thái bền vững, idempotent:** lỗi Google API/worker restart không được làm mất item hoặc tạo nhiều bản sao do retry.
7. **Trích xuất được version hóa:** lưu tên parser/phiên bản, hash file đầu vào, thời điểm, nội dung/locator và trạng thái; sau này thay parser, OCR, ASR không làm mất bản gốc và chỉnh sửa thủ công.
8. **Tìm kiếm qua `SearchService`:** PostgreSQL FTS/trigram ban đầu; có thể bổ sung Typesense/pgvector sau mà không đổi API/UX.
9. **Portable export:** xuất danh mục/nhóm/ghi chú/quan hệ và mapping `item_id ↔ asset_id ↔ drive_file_id` thành JSON có `schema_version`, kèm file manifest và một bản DB backup. Người dùng có đường khôi phục khi đổi máy/chuyển lưu trữ.
10. **Lựa chọn công nghệ không khóa nâng cấp:** một Django monolith phân module, frontend React tĩnh; khi cần ASR/AI nặng tách worker thành tiến trình/máy khác, không thiết kế microservice sớm.

## 3. Lựa chọn công nghệ cân bằng

| Thành phần | Lựa chọn cho bản chạy thực tế | Vì sao |
| --- | --- | --- |
| File gốc | **Google Drive API + OAuth `drive.file`** | Tận dụng ~500 GB hiện có; file xem được trong Drive và ChatGPT khi được cấp quyền |
| Danh mục/tìm kiếm/job | **PostgreSQL** trong một Docker Compose nhỏ | Chỉ thêm một dịch vụ nhưng tránh đổi SQLite/FTS5/queue khi nâng cấp; Django khuyến nghị PostgreSQL cho production |
| Backend | **Django 5.2 LTS + Django Ninja** | Auth/admin/migration và API theo kiểu dữ liệu; LTS được hỗ trợ tới 04/2028, có đường lên 6.2 LTS |
| Frontend | **React + TypeScript + Vite + Mantine** | Trải nghiệm bộ lọc và thư viện trên PC/Android; build tĩnh, không SSR |
| Tác vụ | **Một worker Python + bảng job PostgreSQL** | Vận hành đơn giản, job bền vững; có thể tăng worker/chuyển queue khi tải tăng |
| Search | **PostgreSQL keyword/FTS + unaccent/pg_trgm** | Không cần service search; sau có thể thêm vector mà giữ API |
| AI nhẹ | **Rule-based + API provider adapter tùy chọn** | Đủ để gợi ý nhóm; chưa chọn nhà cung cấp trước benchmark |
| ChatGPT | **Google Drive app**, MCP tùy nhu cầu | Không xây cầu nối mới khi ứng dụng Drive sẵn có đáp ứng |

**SQLite vẫn hợp cho prototype/demo rất nhỏ**, nhưng KHÔNG đưa dữ liệu dùng thật vào SQLite rồi dự định chuyển PostgreSQL “dễ dàng” mà chưa có bài thử migration. Với ưu tiên không muốn làm lại, đề xuất dùng cùng PostgreSQL từ lúc bắt đầu code và bản chạy thật. Không thuê managed database riêng; chạy Postgres trong cùng máy chủ và sao lưu đúng cách.

## 4. Google Drive là kho chính, nhưng không được trở thành khóa

- Thư mục vật lý theo **loại file** (video/ảnh/tài liệu/hệ thống) hoặc đơn giản hơn; nhóm/dự án/ngày quản lý bằng database.
- Mỗi file do app tạo có `item_id`/`asset_id` trong metadata Drive (chỉ là dấu vết tìm lại), đồng thời ghi trong manifest có thể mang sang Google API client mới; metadata ngắn chứ không nhét toàn bộ nhóm/tag vào Drive.
- Sử dụng resumable upload, xét pre-generated Drive IDs cho file nhị phân để chống duplicate khi timeout; phân biệt nhận URL, lưu file và kiểm tra file thật.
- Lưu trạng thái `modifiedTime/revision/size/checksum` nếu có; khi người dùng đổi tên/xóa/sửa file trực tiếp trên Drive, có cơ chế **kiểm tra lại / đối chiếu định kỳ** (sau có thể dùng Drive Changes API).
- Khi nhập Google Docs/Sheets/Slides native: coi là một dạng nguồn riêng; export ra định dạng phổ biến **khi cần** để bảo đảm portability; không hứa Google API xuất mọi file cực lớn bằng cùng một cách.
- OAuth `drive.file` chỉ quản lý file ứng dụng tạo/mở hợp lệ; nếu nhập file đã có từ Drive sẽ cần Google Picker hoặc cơ chế cấp quyền tương ứng.
- Khi ưu đãi 500 GB sắp hết: xuất manifest, chọn mua thêm Drive hoặc viết provider mới, di chuyển **từng file** và xác minh checksum; `item_id`, dự án, tìm kiếm và MCP không đổi.

## 5. Các đường nâng cấp cần bảo đảm (KHÔNG triển khai tất cả ngay)

| Khi cần nâng cấp | Có thể làm mà không phải sửa phần nào | Tính năng chỉ bổ sung lúc đó |
| --- | --- | --- |
| Drive hết dung lượng | Giữ item, nhóm, tìm kiếm, ghi chú, API | Thêm B2/R2 storage driver, migration & verify |
| Nhiều tài liệu hơn / thêm người dùng | Giữ database schema, REST API, UI | Index tối ưu, thêm worker, phân quyền user |
| OCR PDF scan, ảnh viết tay | Giữ file gốc + Asset, lịch sử sửa | OCR extractor tạo `DerivedContent` phiên bản mới |
| ASR video, tóm tắt video | Giữ nguồn/video/ID | ASR processor, transcript có timestamp, derivative data |
| AI phân loại thay model | Giữ nhóm đã chốt, file và ghi chú | AIExecution/reprocessing có version & approval |
| Tìm kiếm ngữ nghĩa | Giữ API `SearchService.search` | `EmbeddingModel` + `ChunkEmbedding`, pgvector hoặc search service |
| ChatGPT cần tag/project nội bộ | Giữ API read/search + ID | MCP chỉ đọc/OAuth hoặc tunnel phù hợp |
| Android ứng dụng native | Giữ REST API | Capacitor hoặc native app, không viết lại backend |
| Nhiều worker chạy song song | Giữ job và trạng thái nghiệp vụ | Postgres locking, job library chuyên dụng nếu cần |
| Đổi hosting/mất máy chủ | Giữ Drive originals và bản export danh mục | Restore DB/manifest, triển khai app trên máy mới |

## 6. Sao lưu và độ an toàn vừa đủ

- Không cần RBAC enterprise; chỉ một tài khoản đăng nhập, HTTPS nếu chạy công khai và giữ Google OAuth token kín.
- Database và dữ liệu người dùng **không thể tái tạo** cần backup đều đặn. Drive gốc + DB backup trên Drive phục hồi khi VPS hỏng nhưng **không thay thế bản sao ở nơi khác** khi mất tài khoản Google.
- Tối thiểu: `pg_dump` + JSON manifest lên thư mục hệ thống trên Drive, bản sao ngoài Drive về Windows theo lịch đơn giản; định kỳ thử restore.
- Giữ file gốc và chú giải thủ công; mọi xóa đều xóa mềm trước.
- Chống SSRF cơ bản, giới hạn file/url và retry; không cần hệ thống quản lý khóa enterprise.

## 7. Thứ tự triển khai đã chốt

**Mốc A — Nền tảng đúng và lưu Drive được (P0):** Django LTS, PostgreSQL, API, ID ổn định, storage driver Drive/OAuth, upload–open–verify, đơn giản một worker, màn hình Thêm/Thư viện, backup đầu tiên.

**Mốc B — Dùng được hàng ngày (P0):** metadata video/web, trích chữ và phụ đề nguồn, AI gợi ý nhóm, lĩnh vực/dự án/ngày/tag, tìm kiếm và bộ lọc, Android dán/chia sẻ link khi nền tảng hỗ trợ.

**Mốc C — Khai thác ChatGPT (P1):** thử Google Drive app trước; MCP chỉ đọc nếu thật sự cần truy vấn tag/dự án/ghi chú riêng hoặc connector chưa đáp ứng.

**Mốc D — Mở rộng (theo nhu cầu):** OCR/ASR theo yêu cầu, đổi AI, search ngữ nghĩa, storage driver thứ hai, nhiều worker/người dùng, ứng dụng Android native.

Trước khi thông báo PASS từng mốc, phải có kiểm thử file Drive thật, restart worker, tìm kiếm tiếng Việt, bản sao và khôi phục, không chỉ green CI.

## 8. Phạm vi chưa chốt

- Máy chủ Windows luôn mở hay VPS chạy 24/7; tên miền chưa có.
- Ngân sách/vấn đề gửi nội dung lên AI bên ngoài; lựa chọn AI cần benchmark.
- Số lượng video và file lớn, tốc độ mạng khi tải lên Drive.
- Ngày hết hạn 500 GB Google Drive, quota thực tế; tài khoản Google sẽ được chủ sở hữu kết nối.
- ChatGPT có quyền sử dụng app Google Drive theo tài khoản/workspace không.
- Sau khi có dữ liệu thật, mới xác định điểm ngưỡng mở rộng ở `ROADMAP_AND_TESTS.md`.

**Quy ước tài liệu:** `MASTER_PLAN.md` quản lý mục tiêu/phạm vi, `ARCHITECTURE_AND_DATA.md` giải thích kỹ thuật và so sánh phương án, `ROADMAP_AND_TESTS.md` là backlog và nghiệm thu, `AGENTS.md` là quy tắc Codex. Không bổ sung 17 file tài liệu thiết kế.

**Trạng thái khi cập nhật:** Chỉ có tài liệu; chưa tạo frontend/backend, chưa thử Google Drive API với tài khoản của người dùng, chưa có production.
