# KHO TRI THỨC — KẾ HOẠCH TỔNG THỂ V4.7 (TIẾP NHẬN VÀ TỰ TỔ CHỨC)
## Nhỏ khi vận hành, sẵn đường nâng cấp dài hạn

**Ngày baseline:** 18/11/2026 · **Thay thế v4.6** · **Trạng thái tại thời điểm lập v4.7:** thiết kế chưa có mã nguồn; **đến 20/11/2026 đã có mã và các nghiệm thu giới hạn** như [CURRENT_STATE.md](CURRENT_STATE.md), không được hiểu dòng lịch sử này là hiện trạng.  
**Nguồn quyết định:** người dùng muốn **Google Drive là kho file chính**, sử dụng cá nhân, tự sắp xếp theo lĩnh vực/dự án/xem theo ngày, có thể kết nối ChatGPT và mở rộng AI trong tương lai. Tránh cả overengineering lẫn làm quá sơ sài dẫn đến viết lại hệ thống.

## 1. Mục tiêu của bản đầu

**Bổ sung ngày 19/11/2026:** Kho Tri Thức tổ chức thành nhiều kho con, lĩnh vực,
bộ sách/sách/chương và nhánh nhỏ hơn khi cần. Đây là cây linh hoạt, không ép mỗi
lĩnh vực có cùng số tầng. Một bài có thể xuất hiện ở nhiều nhánh nhưng chỉ có
một nội dung/định danh. Liên kết phải đi qua trích text; video là nguồn minh họa
gắn vào bài hoặc mốc thời gian, không là đối tượng kiến thức đã hiểu chỉ nhờ
metadata. Lượt xem/thích/cảm xúc/chia sẻ không thuộc dữ liệu tri thức cần thu thập.
Người dùng đã yêu cầu phần chuyển video thành text; mở cổng ASR cục bộ giới hạn,
không triển khai OCR/embeddings/chatbot ngoài phạm vi này.

**Định hướng người dùng chốt ngày 19/11/2026:** tri thức được đọc, tìm kiếm và
tổ chức chủ yếu bằng **văn bản/Markdown**. Media và tài liệu nguồn giữ vai trò
minh họa, bằng chứng và truy nguyên. Bài văn bản phải xuất hiện ngay trong thư
viện đang dùng, không chỉ tồn tại dưới dạng bản xuất hoặc tập kiểm thử tách riêng.
Nguồn chưa có text phải hiện rõ thiếu nội dung; không suy kiến thức từ metadata video.

- Tiếp nhận URL FB/TikTok/YouTube/web, video, ảnh, tài liệu PDF/DOCX/XLSX và ghi chú bằng Android/Windows.
- Lưu file gốc trên Google Drive My Drive do chủ sở hữu kết nối, video chỉ tải khi nền tảng cho phép và công cụ hoạt động; link thất bại vẫn được giữ.
- Thu thập metadata và văn bản dễ lấy (PDF có chữ, DOCX, XLSX, HTML, phụ đề có sẵn); chạy nền, không làm nghẽn lưu file.
- **Mỗi lần gửi phải được lưu ngay** (URL hoặc ghi chú thuần chữ) kèm thời gian server nhận; quá trình tải/AI/Drive tiếp tục ở nền. Ghi chú chữ lưu nguyên văn, không bắt buộc lên Drive.
- **Tự phân loại thực sự vào nhóm đã tồn tại** khi đủ bằng chứng, không chỉ hiển thị gợi ý. Đồng thời tìm **các mục có nội dung liên quan** và lưu lý do; khi thiếu dữ kiện để Chưa phân loại/Đề xuất, không ghi đè nhóm đã chốt.
- Tìm kiếm từ khóa và lọc; quản lý đánh dấu quan trọng, xóa mềm, khôi phục.
- Đọc/nghiên cứu file qua **ChatGPT Google Drive app trước**, nhưng phải nhớ dữ liệu ghi chú, dự án, phụ đề và văn bản trích xuất đang nằm trong PostgreSQL thì ChatGPT **không tự thấy**. Thử xuất văn bản đại diện lên Drive (Google Docs/TXT/Markdown, định dạng nào thực sự đọc được) rồi mới quyết định có cần MCP riêng.

**Không triển khai trong bản đầu:** OAuth server riêng cho MCP, ASR/OCR hàng loạt, embeddings, chatbot nội bộ, graph, CDN, kho S3 thứ hai, microservices, Kubernetes, multi-tenant UI hoặc hệ thống bảo mật doanh nghiệp.

## 2. Những quyết định PHẢI thiết kế đúng từ đầu

1. **Hai loại định danh:** mỗi mục có `item_id` UUID, mỗi file có `asset_id` UUID; Google Drive `drive_file_id` chỉ là **mã vị trí lưu**, không được làm khóa nghiệp vụ. Tách `Asset` và `StorageLocation` (bản đầu chỉ một location Drive).
2. **Tách các tầng dữ liệu:** bản gốc và nguồn; dữ liệu trích xuất/AI có thể tái tạo; thông tin người dùng sửa/chốt **không được AI tự ghi đè**.
3. **Nhóm là quan hệ many-to-many** cho lĩnh vực/chủ đề/dự án/tag; ngày là thuộc tính lọc, không phải đường dẫn thư mục. Hệ thống **tự gán nhóm đang có** nếu đủ tin cậy, không tạo hàng loạt nhóm mới.
3a. **Lịch sử nhận thông tin bất biến:** `CaptureEvent` tách khỏi Item, giữ nguyên giờ server nhận và đầu vào gốc **cho từng lần gửi**. Gửi lại cùng link là Event mới (khi đã nhận được request mới), tái sử dụng Item khi nhận diện nguồn chắc chắn; retry cùng idempotency key là **cùng Event**.
3b. **Liên quan không có nghĩa là trùng:** `RelatedItem` ghi cặp nội dung tương tự có provenance; hai ghi chú tự viết gần nghĩa vẫn được giữ thành **hai Item riêng**. Người dùng chỉnh sửa nội dung/nhóm có quyền ưu tiên.
4. **Backend có API ổn định `/api/v1/`**, các nghiệp vụ lưu/truy xuất/tìm kiếm nằm trong service để sau này phục vụ PWA, Android native và MCP mà không viết lại.
5. **Storage driver nhỏ ngay từ đầu:** `DriveStorage` hiện thực giao diện `save/open/verify/delete/locate`. Chưa cần hiện thực B2/R2 hoặc migration engine.
6. **Job trạng thái bền vững, idempotent:** lỗi Google API/worker restart không được làm mất item hoặc tạo nhiều bản sao do retry.
7. **Trích xuất được version hóa:** lưu tên parser/phiên bản, hash file đầu vào, thời điểm, nội dung/locator và trạng thái; sau này thay parser, OCR, ASR không làm mất bản gốc và chỉnh sửa thủ công.
8. **Tìm kiếm qua `SearchService`:** PostgreSQL FTS/trigram ban đầu; **hai chỉ mục GIN riêng cho `Item` metadata và `DerivedContent` văn bản**, hợp nhất kết quả theo `item_id`, chỉ dùng bản trích xuất hiện hành. Thử cấu hình từ điển tiếng Việt có `unaccent` và fallback cho số hiệu/tên viết tắt; có thể bổ sung Typesense/pgvector sau mà không đổi API/UX.
9. **Portable export:** xuất danh mục/nhóm/ghi chú/quan hệ và mapping `item_id ↔ asset_id ↔ drive_file_id` thành JSON có `schema_version`, kèm file manifest và một bản DB backup. Người dùng có đường khôi phục khi đổi máy/chuyển lưu trữ.
10. **Lựa chọn công nghệ không khóa nâng cấp:** một Django monolith phân module, frontend React tĩnh; khi cần ASR/AI nặng tách worker thành tiến trình/máy khác, không thiết kế microservice sớm.
11. **Trải nghiệm đa phương tiện đúng từ đầu:** thumbnail sinh/cached riêng cho thư viện (không dùng trực tiếp URL thumbnail Drive hết hạn); **PDF render bằng `pypdfium2`, ảnh Android xử lý `ImageOps.exif_transpose()` trước resize**, không sửa bản gốc; phát video từ Drive khi sẵn sàng, cache file cục bộ ngắn hạn **chỉ nếu test chứng minh cần**.
12. **Kênh đọc cho ChatGPT có kiểm chứng:** nếu xuất văn bản từ PostgreSQL ra Drive, phải xuất theo phiên bản, cập nhật cùng file và đo độ trễ; không cam kết ChatGPT lập chỉ mục hoặc đọc 100% nội dung.

## 3. Lựa chọn công nghệ cân bằng

| Thành phần | Lựa chọn cho bản chạy thực tế | Vì sao |
| --- | --- | --- |
| File gốc | **Google Drive API + OAuth `drive.file`** | Tận dụng ~500 GB hiện có; file xem được trong Drive và ChatGPT khi được cấp quyền |
| Danh mục/tìm kiếm/job | **PostgreSQL — ĐÃ CHỐT** trong một Docker Compose nhỏ | Người dùng đã quyết định dùng PostgreSQL; giữ đồng nhất ORM, full-text search, job và khả năng nâng cấp; không dùng SQLite làm database triển khai chính |
| Backend | **Django 5.2 LTS + Django Ninja** | Auth/admin/migration và API theo kiểu dữ liệu; LTS được hỗ trợ tới 04/2028, có đường lên 6.2 LTS |
| Frontend | **React + TypeScript + Vite + Mantine** | Trải nghiệm bộ lọc và thư viện trên PC/Android; build tĩnh, không SSR |
| Tác vụ | **Một worker Python + bảng job PostgreSQL** | Vận hành đơn giản, job bền vững; có thể tăng worker/chuyển queue khi tải tăng |
| Search | **PostgreSQL keyword/FTS + unaccent/pg_trgm** | Không cần service search; sau có thể thêm vector mà giữ API |
| AI nhẹ | **Rule-based + API provider adapter tùy chọn** | Đủ để gợi ý nhóm; chưa chọn nhà cung cấp trước benchmark |
| ChatGPT | **Google Drive app**, MCP tùy nhu cầu | Không xây cầu nối mới khi ứng dụng Drive sẵn có đáp ứng |

**SQLite vẫn hợp cho prototype rất nhỏ**, nhưng **quyết định của dự án đã chốt PostgreSQL cho cả local development và bản chạy thật**. Không tạo hai hệ database song song, không đưa dữ liệu thật vào SQLite rồi chuyển sau khi đã có FTS/job. Không thuê managed database riêng; chạy Postgres trong cùng máy chủ và sao lưu đúng cách.

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

**Mốc A — Nhận ngay và lưu chắc chắn (P0):** Django/PostgreSQL; `CaptureEvent` + Item/Source/Job transaction, API trả ACK ngay cho URL/ghi chú; lịch sử giờ nhận, gửi lại link khác với retry, không cần Drive asset cho ghi chú thuần chữ; Drive/OAuth, thumbnail, backup và thử khôi phục.

**Mốc B — Thư viện tự tổ chức (P0):** metadata video/web, trích chữ/phụ đề nguồn, benchmark ba parser PDF; **SearchService tìm nhóm/mục hiện có, OrganizationService tự gán nhóm khi đủ tin cậy và tạo RelatedItem**, tôn trọng nhãn người dùng, đánh giá AI/tìm kiếm tiếng Việt, lọc theo lịch sử `CaptureEvent`, Android Share Target thử thật.

**Mốc C — Khai thác ChatGPT (P1):** thử Google Drive app với file gốc **và** bản xuất tri thức từ PostgreSQL; nếu định dạng không đọc được, metadata nhóm không đủ hoặc cần truy vấn tag/dự án chính xác, triển khai MCP chỉ đọc. Không ngầm tuyên bố ChatGPT hiểu file MP4 chỉ vì lưu trên Drive.

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

**Chú thích lịch sử:** V4.6 từng là **baseline giao Codex** lúc chưa có frontend/backend hoặc Drive live. Trạng thái này đã lỗi thời tại 20/11/2026; dùng [CURRENT_STATE.md](CURRENT_STATE.md) để biết code, nghiệm thu Windows/Drive và các mục NOT_RUN.


## 8a. Hợp đồng sử dụng đã chốt ngày 18/11/2026

**Nguồn chuẩn chi tiết:** [CAPTURE_AND_ORGANIZE.md](CAPTURE_AND_ORGANIZE.md). Các tình huống N01–N17 là tiêu chí nghiệp vụ cần kiểm thử, không phải chức năng đã chạy.

- **Gửi một lần, nhận ngay:** khi backend/DB sẵn sàng, tạo `CaptureEvent` với `server_received_at`, giữ bản gốc; sau commit trả receipt mà không đợi tải video hoặc AI.
- **Lịch sử ≠ Thư viện:** lịch sử mỗi lần gửi (kể cả gửi lại cùng link) theo thời điểm server; Thư viện mỗi nội dung một Item để tránh nhân đôi file. Ngày đăng của nguồn và ngày hoàn tất worker nằm ở các trường riêng.
- **Text-only và nguồn lỗi:** ghi chú thuần chữ lưu nguyên văn; link không tải được vẫn tồn tại và báo chính xác phần thiếu. Không giả đã có video/phụ đề.
- **Tự phân loại là hành động:** tìm các nhóm hiện có, gán quan hệ thật nếu đủ tin cậy; chưa chắc thì suggested/unclassified, không auto sửa curated. Tìm và ghi RelatedItem, **không tự hợp nhất các mục gần nghĩa**.
- **Giữ lựa chọn công nghệ:** PostgreSQL, Drive file gốc, một worker và hai nhóm GIN index đã chốt; AI ngoài có thể tắt, không thêm Redis/semantic/vector DB chỉ vì yêu cầu này.

## 9. Bổ sung sau phản biện kỹ thuật — các quyết định có điều kiện

| Điểm | Quyết định áp dụng | Điều chưa được khẳng định |
| --- | --- | --- |
| ChatGPT và PostgreSQL | Thiết kế `KnowledgeExportService`: thử xuất **mỗi Item một tài liệu văn bản đại diện** lên Drive (tiêu đề, chủ đề, dự án, ghi chú, văn bản/phụ đề có sẵn, nguồn). Worker cập nhật theo phiên bản, không tạo file trùng. Chỉ bật rộng khi ChatGPT đọc/tìm được định dạng đã thử. | Không hứa connector lập chỉ mục mọi TXT/Markdown/Google Docs, cũng không hứa hiểu video thiếu phụ đề. |
| Khôi phục quyền Drive | Giữ Google Cloud Project/Client ổn định khi đổi máy. Kiểm thử lại quyền khi đổi OAuth Client cùng project hoặc project mới; ưu tiên Picker/cấp quyền lại theo từng file khi phù hợp. | Không mặc định đổi Client là lỗi 404; không yêu cầu `drive.readonly` rộng một cách vô điều kiện. |
| Thumbnail | **`pypdfium2` render trang đầu PDF tại KT-010**, Pillow `ImageOps.exif_transpose()` xử lý 8 trường hợp EXIF trước resize ảnh Android; cache WebP/JPEG trên volume bền vững, tạo lại được. Không ghi đè file gốc. | Không dùng `pypdf` để render; không nhúng Drive `thumbnailLink` trực tiếp vào card. |
| Video mới tải | Trạng thái upload và trạng thái Drive preview tách biệt; có thể giữ video cache local có hạn ngạch/TTL khi phép thử cho thấy cần. | Không ấn định chậm 3–15 phút, không mặc định cache mọi video 48 giờ. |
| PDF tiếng Việt | `KT-102` benchmark **pypdf/pypdfium2/PyMuPDF** trên 20–30 PDF tiếng Việt; đo chữ/dấu/trang/tốc độ/RAM, rà Apache-2.0/BSD-3-Clause của pypdfium2/PDFium và AGPL/thương mại của PyMuPDF. | KT-010 đã chọn pypdfium2 để render thumbnail; **chưa chốt** thư viện đọc chữ chính trước benchmark. |
| PostgreSQL tiếng Việt | Migration `kt_vi`/unaccent/pg_trgm; **hai expression GIN index riêng** cho Item và DerivedContent, `SearchService` gộp item ID, bỏ bản text stale và giữ provenance. | Không tạo expression index JOIN xuyên bảng; không dồn PDF/transcript dài vào một `Item.search_vector`, không tự gắn `IMMUTABLE` cho hàm thiếu căn cứ. |

Các công việc và mã kiểm thử chi tiết nằm trong `docs/ROADMAP_AND_TESTS.md`; giải pháp kỹ thuật chi tiết nằm trong `docs/ARCHITECTURE_AND_DATA.md`. Không thêm nhà cung cấp cloud/Redis/ASR/AI sâu trong bản đầu.

## 10. Bổ sung định hướng sau 17 nghiên cứu ứng dụng ghi chú — 20/11/2026

**Phạm vi, không đổi lựa chọn nền tảng đã chốt:** Khảo sát G01–G17 cho thấy có nhiều UX đáng học ở Obsidian, Notion, Heptabase, OneNote, Capacities, Lark, v.v. nhưng **chưa có chứng cứ** sản phẩm nào thay được hợp đồng dữ liệu CaptureEvent/Item/Asset/Drive, khôi phục và tự tổ chức hiện có. Tiếp tục **Django + PostgreSQL + Google Drive**, không fork nguyên hệ thống ghi chú bên thứ ba. [PR #47 — G00 thẩm định lần hai](https://github.com/cavoixanh638/kho-tri-thuc/pull/47) là tài liệu nghiên cứu **chưa merge**, không phải trạng thái chạy thật.

**Thứ tự giá trị người dùng:**
1. **Cổng an toàn trước khi phổ biến/nhập quy mô:** giữ file gốc và hash/restore, chống trùng Event, xử lý nguồn FB/TikTok/YT an toàn, Android thực, đo 10.000 Item/khối lượng media đại diện. Không suy pilot nhỏ thành xác nhận hàng trăm GB.
2. **UX ưu tiên PoC:** soạn/đọc văn bản Markdown Live Preview; mở trích dẫn về đúng trang/timestamp có chứng cứ; gửi nhanh PWA/Android, không mất nội dung.
3. **UX sau gate:** panel backlinks/related có lý do, Table/Card/Timeline dùng chung Item ID, thẻ nguồn; AI suggestions có diff/accept **chỉ khi được cho phép**; template theo loại tài liệu tùy chọn.
4. **Hoãn:** Canvas/whiteboard lớn, tích hợp Mem/Superpowered làm lõi, fork Obsidian/AFFiNE, graph DB, xây MCP/AI trả phí/ASR hàng loạt hoặc đổi Drive chỉ vì ý tưởng nghiên cứu.

**Không tự triển khai tất cả:** Danh sách trên là **định hướng đề xuất** để người dùng giao từng mã KT-114–KT-121; nhiệm vụ, giới hạn quyền sửa và test acceptance ở [INDEX triển khai](workstreams/notes-ux-20261120/INDEX.md); chi tiết mã/cổng PASS thuộc [ROADMAP_AND_TESTS.md](ROADMAP_AND_TESTS.md), kết quả chạy thật thuộc CURRENT_STATE. Các ghi nhận phát hành cần tính theo mốc thời gian; Capacities **đã có ghi âm/phiên âm/tóm tắt ở Pro từ 11/2026** và Reflect Open Windows/Linux mới chỉ là build thử nghiệm chưa ký.

## 11. Khôi phục yêu cầu còn thiếu: File Explorer và quan hệ cha–con giữa bài (20/11/2026)

**Chỉnh thiếu sót phạm vi:** Người dùng yêu cầu rõ cách sắp xếp **thư mục như Obsidian**, gồm “thư mục chứa thư mục/ghi chú”, và quan hệ **cha–con giữa nội dung**. KT-113 mới có `Topic.parent` + `ItemTopic` trong DB, giao diện `KnowledgeTree` chỉ chứa nhánh; KT-118 (trong PR #57 chưa merge) chỉ thêm List/Table/Card/Timeline. Không được coi các nhiệm vụ này đã tạo được mixed explorer hoặc note→note hierarchy.

**Thứ tự mục tiêu chính thức để giao code, không thay core:** 
1. **KT-122** — Cây chung folder/note (nhiều cấp, tạo/chuyển/đổi tên, shortcut qua M:N, folder home rõ ràng) và thao tác desktop/mobile không cần mở từng Item để “Chỉnh nhóm”. Thư mục ảo PostgreSQL, Drive vẫn chứa file gốc theo UUID/Asset, không di chuyển khi phân loại.
2. **KT-123** — Quan hệ **bài cha→bài con** có hướng để biểu diễn Sách (bài)→Chương (bài)→Bài nhỏ; có mục lục H1–H6 trong từng bài, liên kết chéo và backlink là quan hệ khác, RelatedItem tương đồng không được giả làm cha–con.
3. Sau khi hai task được **code + test + browser QA** mới nhận xét UX tổ chức tri thức theo hướng Obsidian đã hoàn thiện; không được gán PASS vì PR #57 có cây Topic hoặc panel RelatedItem. Giữ 10.000 Item, không duplicate, portable backup/export; không triển khai graph DB hay thay nền tảng.

**Nhiệm vụ chi tiết:** [KT-122](workstreams/notes-ux-20261120/KT-122-FOLDER-EXPLORER.md), [KT-123](workstreams/notes-ux-20261120/KT-123-NOTE-HIERARCHY.md). **Trạng thái:** SPEC_READY/IMPLEMENTATION_NOT_RUN, branch code dựa trên `codex/notes-ux-integration` PR #57 vẫn open, không merge/deploy khi chưa có quyền.

## 12. Rà soát lại toàn bộ giá trị học từ 17 phần mềm — trách nhiệm G00 (20/11/2026)

**Không thể coi nghiên cứu 17 phần mềm thành công khi chỉ có 8 task UX và phải chờ người dùng nhắc về folder.** Lần ba G00 kiểm kê **38 nhóm năng lực** trong [sổ truy vết](workstreams/notes-ux-20261120/G00-FEATURE-TRACEABILITY.md), phân biệt code MAIN, candidate PR #57, đã có một phần, thiếu, và có điều kiện/hoãn. Báo cáo gốc ở PR #30–46 và thẩm định chi tiết PR #47 vẫn chưa merge. Không được suy 38 dòng = 38 tính năng native đã được thử hay phải lập trình hết.

**Các hành trình cốt lõi để dùng kho thật:**
1. **Tổ chức:** folder+ghi chú chung cây, bài cha/con, note nhiều nhánh cùng UUID, backlinks/wiki links, unlinked mentions, mục lục Markdown, Ctrl+K và breadcrumbs.
2. **Tìm lại và tổng hợp:** saved smart collections, filter động, view table/card/timeline trên cùng một ID, metadata/source status; không phải chỉ có nút chọn view.
3. **Thu thập và đọc nguồn:** nhanh từ web/Android, clip selected text hoặc article, gắn quote vào bài đã có, trích dẫn có provenance/locator tới PDF/time, bản user viết không bị chép đè.
4. **Sở hữu dữ liệu:** export/import Markdown vault với folder/notes/links/manifest + restore; Drive và PostgreSQL vẫn là nguồn sự thật, không nhân file MP4 khi chuyển folder.
5. **Bằng chứng thực:** QA hành trình giao diện 1920/1440/768/390 và Android thật khi có, corpus 10k, restore/hashing, đo tình trạng thiếu dữ liệu và xin quyền khi dùng tài khoản/dịch vụ thật.

**Các task bổ sung không được bỏ:** [KT-122](workstreams/notes-ux-20261120/KT-122-FOLDER-EXPLORER.md), [KT-123](workstreams/notes-ux-20261120/KT-123-NOTE-HIERARCHY.md), [KT-124](workstreams/notes-ux-20261120/KT-124-NAVIGATION-LINKING.md), [KT-125](workstreams/notes-ux-20261120/KT-125-SMART-COLLECTIONS.md), [KT-126](workstreams/notes-ux-20261120/KT-126-CLIPPER-HIGHLIGHTS.md), [KT-127](workstreams/notes-ux-20261120/KT-127-PORTABLE-VAULT.md), [KT-128](workstreams/notes-ux-20261120/KT-128-USER-JOURNEY-ACCEPTANCE.md). [KT-129](workstreams/notes-ux-20261120/KT-129-ORGANIZATION-REVIEW.md) cần evidence/benchmark; [KT-130](workstreams/notes-ux-20261120/KT-130-DEFERRED-RESEARCH.md) giữ các ý tưởng chưa áp dụng (Canvas, OCR, AI scoped research, offline sync, voice, semantic) có lý do và trigger, thay vì để chúng biến mất.

**Không đổi nền tảng đã chốt:** Django + PostgreSQL + Drive. **PR #57 là candidate OPEN/UNMERGED**, chưa chứng nhận các hành trình trên. Những task 122–130 mới ở trạng thái SPEC_READY / NOT_RUN. Chỉ tiến hành lập trình khi người dùng giao; test/CI phải báo rõ SHA và trạng thái thực.

## 13. Phụ lục đối chiếu ngày 22/11/2026 — không thay mục tiêu v4.7

Người dùng đã chỉ đạo **cập nhật thường xuyên và đối chiếu với kế hoạch trước khi triển khai**. Vì vậy áp dụng [checkpoint kiểm toán và cổng nghiệm thu](operations/RELEASE_READINESS_20261122.md) cho mọi vòng thực hiện.

- **Trục ưu tiên không đổi**: A (tiếp nhận/Drive/backup) → B (tự tổ chức/tìm kiếm/media) → C (ChatGPT pilot) → D (nâng cấp có điều kiện). Có thể nghiên cứu/viết mã cho D trước nhưng không được dùng CI xanh của D để gọi A/B đã nghiệm thu.
- **Yêu cầu bổ sung được chấp nhận sau baseline**: ô gửi mọi loại nội dung duy nhất (PR #81) và Gemini OCR ảnh / quản lý model (PR #82/#84). Tất cả đang là **mã đề xuất, chưa merge/deploy, chưa nghiệm thu API Gemini thật** tại checkpoint; không tự bật truyền dữ liệu/chi phí.
- **Khối lượng có ảnh hưởng trực tiếp tới bản đầu**: nâng cổng thực tế media (Facebook/TikTok/YouTube, link chỉ là link nếu tải thất bại), 10.000 mục, tiếng Việt, chứng cứ Google Drive readback và backup/restore, hành trình tạo→xếp→tìm→xem→khôi phục.
- **Hoãn theo người dùng:** Android/native; không mở rộng B2/R2, semantic/vector, chatbot riêng, microservices khi chưa có dấu hiệu cần thiết.
- **Tách cổng:** code/CI xanh **khác** UAT thật, độ chính xác OCR/ASR, Drive/provider thật và quyền/chi phí. Khi thiếu mẫu, không ghi 100% hoàn thành.
- Không đổi tên baseline kế hoạch thành v4.8 chỉ vì một bản kiểm toán; bản v4.8 chính thức cần tổng hợp lựa chọn và tiêu chí được người dùng duyệt.

Chi tiết công việc và trạng thái snapshot nằm ở tài liệu trên; `CURRENT_STATE.md` vẫn là sự thật **đã tích hợp/đã nghiệm thu** của main, không ghi PR Draft thành tính năng phát hành.
