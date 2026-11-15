# LỘ TRÌNH TRIỂN KHAI VÀ KIỂM THỬ — KHO TRI THỨC

**Ngày:** 15/11/2026 · **Dựa trên:** `MASTER_PLAN.md` v4.2 và `ARCHITECTURE_AND_DATA.md`.  
**Nguyên tắc:** ưu tiên sản phẩm dùng được; không làm trước chức năng P2. Bảng này là backlog, **chưa có mục nào được báo PASS**.

## A. Thứ tự thực hiện và cổng nghiệm thu

| Đợt | Ưu tiên | Kết quả nhìn thấy | Cổng bắt buộc trước khi đi tiếp |
|---|---|---|---|
| 0. Khởi tạo và test kết nối | P0 | Repo chuẩn, local compose, mock UI, DB, test B2 | Không ghi secret; chạy local; tạo/read một file test có checksum |
| 1. Lưu và xem lại | P0 | Đăng nhập, nhận link/ghi chú/file, thư viện cơ bản | E2E lưu–đọc–xóa mềm–khôi phục, job retry, backup/restore |
| 2. Tổ chức tự động | P0 | Metadata, text nhẹ, AI phân loại, lĩnh vực/dự án/ngày, tìm kiếm/bộ lọc | Bộ thử thật + không ghi đè phân loại thủ công |
| 3. MCP chỉ đọc | P1 gần | ChatGPT tìm và đọc đúng tài liệu | OAuth/quyền và MCP tools pass; thử trong ChatGPT web thực tế |
| 4. Tối ưu vận hành | P1 | Android share, Drive backup, bulk, export, dashboard | Restore, hiệu năng, UX thiết bị thật |
| 5. Xử lý AI nâng cao | P2 tùy chọn | OCR/ASR/vector/research khi người dùng đặt hàng | Phát hành từng phần, không làm chặn các bước trước |

**Thứ tự ưu tiên thực tế:** nếu phải lựa chọn, hoàn thành **Nhận nhanh > Lưu an toàn > Xem lại > Phân nhóm > Tìm kiếm > MCP > Tối ưu**. Sao lưu tối thiểu phải làm đồng thời với lưu trữ sản xuất, không dời tới đợt 4.

## B. Backlog giao Codex / AI theo phụ thuộc

### Đợt 0 — Chỉ chứng minh hệ thống có thể triển khai

| ID | Việc | Đầu ra | Phụ thuộc |
|---|---|---|---|
| KT-001 | Repo scaffold + Docker Compose local | Vite + Mantine, Django 6 + Ninja, Postgres, worker, Caddy dev | Kế hoạch + R1 tech comparison |
| KT-002 | Thiết kế Django Ninja OpenAPI + Django migration đầu tiên | Schema items/source/assets/storage, Django admin; contract chuẩn | KT-001 |
| KT-003 | Django Auth single-user, session | Superuser, login/logout, rate limit, CSRF, test | KT-001 |
| KT-004 | StorageAdapter B2 proof-of-concept | Upload/download/verify/presigned URL bucket riêng tư | KT-001 |
| KT-005 | Thử Procrastinate/Django vs Chancy/PgQueuer | Restart, retries, lỗi, không lặp job; quyết định kèm bằng chứng | KT-001 |
| KT-006 | Frontend Mantine skeleton + design tokens | Desktop/mobile responsive, 4 khu vực, mock data | KT-001 |

**G0 PASS:** local stack khởi động, tài khoản thử đăng nhập được, file thử được upload/download/đối chiếu checksum, job restart đúng. **Chưa cần OAuth Drive, embedding, MCP hoặc chatbot**.

### Đợt 1 — Bản Alpha có thể lưu dữ liệu thật

| ID | Việc | Đầu ra | Phụ thuộc |
|---|---|---|---|
| KT-101 | API nhận note/link/file + idempotency | CRUD theo nghiệp vụ, giữ origin/metadata | KT-002,003 |
| KT-102 | B2 storage production adapter + verify | Object key ổn định, CORS, expiry, checksum | KT-004 |
| KT-103 | Download worker (yt-dlp + ffprobe) | Metadata, trạng thái link/file, không tải nhầm | KT-005,101 |
| KT-104 | UI Quick Add: dán link, note, file | Không chờ download, hiện job status | KT-006,101 |
| KT-105 | Library list + detail + file preview | Mở nguồn, ảnh, PDF, phát video có Range | KT-104,102 |
| KT-106 | Chống trùng / trash / restore | Sha256, external ID, xóa mềm, hoàn tác | KT-101 |
| KT-107 | Backup độc lập + restore drill | DB dump + R2 copy/manifests đã kiểm; Drive là mở rộng | KT-102,105 |
| KT-108 | E2E alpha + smoke trên điện thoại | Checklist 10 loại dữ liệu và lỗi | KT-103..107 |

**G1 PASS:** lưu link, ghi chú, ảnh, file và video tải được; xem lại; job lỗi không mất record; ít nhất một backup restore thành công. Google Drive backup có thể làm bằng job/CLI độc lập, không ép UI OAuth.

### Đợt 2 — Bản đầu đầy đủ: tự phân nhóm và tìm kiếm

| ID | Việc | Đầu ra | Phụ thuộc |
|---|---|---|---|
| KT-201 | Taxonomy & projects model + migration | Một mục nhiều lĩnh vực/dự án/tag | G1 |
| KT-202 | Giao diện chủ đề, dự án, dòng thời gian | 3 cách xem; quản lý nhóm và tag | KT-201 |
| KT-203 | Lightweight extraction adapters | PDF text/DOCX/XLSX/Web/subtitles | G1 |
| KT-204 | Search + faceted filters + unaccent | Tìm tên/nội dung có dấu và không dấu | KT-201,203 |
| KT-205 | AI classification adapter | Structured output, cost/privacy, human override | KT-201,203 |
| KT-206 | Bulk edit/đánh dấu quan trọng | Chuyển nhóm và quản lý hàng loạt | KT-202 |
| KT-207 | End-to-end auto organize tests | Bộ dữ liệu 30–50 mục và chỉ số chất lượng | KT-204,205 |

**G2 PASS:** tải nhiều loại nội dung; trích văn bản khi có; AI gợi ý nhóm; tìm theo lĩnh vực/dự án/ngày, không dấu; sửa thủ công không bị AI làm mất.

### Đợt 3 — MCP chỉ đọc

| ID | Việc | Đầu ra | Phụ thuộc |
|---|---|---|---|
| KT-301 | Tool contract search/fetch/read | JSON có ID, title, URL/locator, văn bản | G2 |
| KT-302 | Official MCP SDK v2 + Django OAuth Toolkit >=3.4 | Chỉ scope read, OAuth metadata/CIMD/DCR, token validation và test ChatGPT thật | KT-301 |
| KT-303 | ChatGPT integration test | Kết nối workspace thực, công cụ phản hồi đúng | KT-302 |
| KT-304 | Permission / leakage tests | Không đọc/xóa/sửa ngoài quyền, URL không lộ dữ liệu | KT-302 |
| KT-305 | Long document paging | Fetch theo section/trang khi quá dài | KT-301 |

**G3 PASS:** ChatGPT tìm được tài liệu, đọc đúng nội dung đủ căn cứ, dẫn đúng nguồn khi có; nếu video thiếu phụ đề/tài liệu scan không có text phải báo rõ.

### Đợt 4 — Tối ưu (không chặn bản đầu)

- KT-401 Android Share Target thử trên máy thật; fallback share-to-web; thêm Telegram Bot chỉ nếu cần.
- KT-402 Google Drive one-way backup via rclone hoặc tương đương, kiểm tra reconnect; OAuth/Picker native chỉ nếu có use case.
- KT-403 Export toàn bộ metadata + assets manifest; test restore/migration giữa provider.
- KT-404 Performance 1.000/10.000 mục, tối ưu index, worker/CPU, quan sát chi phí.
- KT-405 Quản lý job lỗi, retry UI, thống kê storage, lập lịch backup và báo động.

## C. Bộ test nghiệm thu thực tế

### Dữ liệu thử ban đầu

- 10 link video gồm Facebook, TikTok, YouTube (không coi tải được 100% là điều kiện; điều kiện là trạng thái/khôi phục đúng).
- 10 tài liệu: PDF có chữ, PDF scan, DOCX có bảng, XLSX nhiều sheet, file hỏng/mật khẩu.
- 10 ảnh (kèm vài ảnh viết tay tiếng Việt).
- 10 ghi chú, bao gồm dài/nhiều dấu, URL trong ghi chú.
- 5 website gồm HTML tĩnh và JS.
- 20 câu tìm kiếm metadata/nội dung có/không dấu, 10 truy vấn lọc kết hợp, 10 câu MCP khi đến đợt 3.

### Test nghiệp vụ bắt buộc

| Mã | Tình huống | PASS khi |
|---|---|---|
| A01 | Share/dán link 2 lần | Không tạo hai file gốc vô lý; ghi nhận idempotency |
| A02 | Link không tải được | Vẫn còn item + original URL + trạng thái đúng |
| A03 | Upload bị ngắt | Không xác nhận thành công nếu B2 chưa có object |
| A04 | File/ghi chú đã lưu | Mở/tải lại đúng nội dung, checksum khớp |
| A05 | Trùng checksum nhưng khác nguồn | Nhận diện trùng file; không mất metadata nguồn |
| A06 | Worker restart giữa download | Không mất job; không tạo nội dung trùng khi retry |
| A07 | PDF scan không OCR | Có file gốc, status *cần OCR*, không tạo text giả |
| A08 | XLSX phức tạp | Không treo worker; có giới hạn và thông báo partial |
| A09 | Website JS/chặn bot | Giữ link/metadata; extraction status fail/partial |
| A10 | AI sai hoặc thiếu thông tin | Có thể đổi nhóm thủ công; AI retry không ghi đè |
| A11 | Theo lĩnh vực + dự án + ngày | Cùng item ở nhiều view, không nhân bản file |
| A12 | Tìm có dấu/không dấu | Trả kết quả tương đương trong test set |
| A13 | Xóa mềm và khôi phục | File và metadata trở lại, không xóa vật lý sớm |
| A14 | B2 presigned access hết hạn | Không còn tải được bằng URL đã hết hạn |
| A15 | Backup restore | Phục hồi DB + file + quan hệ + ghi chú, có log |
| M01 | ChatGPT search & fetch đúng ID | Text/locator có căn cứ, không trộn kết quả |
| M02 | MCP thiếu quyền | Từ chối, không rò rỉ metadata/private URL |
| M03 | MCP gặp video không transcript | Không nói đã nghe/xem nội dung |
| M04 | MCP nhận prompt injection từ web | Không thực hiện thay đổi hay lộ secret |

### Chất lượng định lượng — mục tiêu để đo, chưa phải số liệu đã đạt

- 1.000 item: tìm metadata p95 dưới ~1 giây trên môi trường chốt, kiểm chứng lại với máy chủ thật.
- 100% thao tác lưu ghi nhận trạng thái thành công/thất bại rõ; không silent failure.
- >= 95% trường hợp thử basic metadata/format có kết quả hoặc có thông báo không thể đọc, không tự tạo thông tin.
- Phân loại AI: đánh giá *accuracy@1, coverage, tỉ lệ người dùng phải sửa, chi phí/100 items* trên bộ dữ liệu thực; chỉ bật auto-assign nếu cải thiện rõ rệt.
- Restore drill PASS trước dữ liệu quan trọng, sau đó lặp lại theo chu kỳ.
- MCP không có tool write trong bản đầu và xác minh quyền ở mọi tool.

## D. Ma trận rủi ro và điều kiện dừng

| Rủi ro | Phòng ngừa | Không được làm |
|---|---|---|
| Hạ tầng chưa có | Chạy local/mock để phát triển UI và API | Báo production PASS |
| Không có B2 credentials | FakeStorage trong test, rõ ràng là fake | Nói đã lưu cloud |
| Không có backup thứ hai | Chuẩn bị provider khác + chạy restore drill | Nhập dữ liệu nhạy cảm thật |
| OAuth MCP chưa cấu hình | Chạy MCP local test client trước | Mở public no-auth server |
| Chặn tải YouTube trên cloud | Link-only + tải file hợp lệ từ người dùng | Hứa tải được mọi Shorts |
| AI API hết quota hoặc nội dung nhạy cảm | Fallback chưa phân loại/manual | Truyền tài liệu riêng tư trái quyền |
| Tài liệu lớn/nén độc hại | Giới hạn size, timeout, parser sandbox | Đọc vô hạn RAM |
| Giấy phép thư viện | Duyệt license trước khi đóng gói | Mặc định gắn PyMuPDF AGPL vào sản phẩm private |

## E. Quy trình báo cáo & checkpoint

- Mỗi tác vụ/PR có: mã KT-xxx, phạm vi file sửa, commit SHA, test thực chạy, các test chưa chạy, hạn chế, rollback.
- Ghi kết quả vào PR hoặc tóm tắt checklist tại tài liệu này khi hoàn thành giai đoạn; không tự đổi `CHƯA LÀM` thành `PASS`.
- Không merge đồng thời nhiều worker sửa chung schema/API mà chưa thống nhất contract.
- CI kiểm thử và staging là điều kiện trước production; không kết luận chỉ từ screenshot/green workflow.
- Tài liệu phân quyền: `MASTER_PLAN` nêu chức năng, `ARCHITECTURE_AND_DATA` nêu cách làm, file này nêu công việc và điều kiện PASS.
- Quyết định phát sinh được chốt và lưu thành mục *Decision/Tradeoff* tại tài liệu kiến trúc; chỉ tách ADR riêng khi quy mô thay đổi.

## F. Quy tắc quyết định khi chọn/thay công nghệ

- Bắt buộc so sánh công nghệ dự kiến với **2–3 lựa chọn cùng nhóm** (tài liệu và giá hiện hành) theo 5 tiêu chí tại `ARCHITECTURE_AND_DATA.md#14`.
- Ghi phương án chọn, lý do loại và phép thử chuyển từ *đề xuất* sang *PASS*; không tự mở rộng kiến trúc chỉ vì công nghệ mới.
- **Chưa có kết quả benchmark mới trong repo này**: các so sánh đang là quyết định thiết kế có dẫn nguồn.

## G. Việc phải quyết định trước từng đợt

**Trước đợt 0:** hạ tầng local/đích, domain dự kiến, dữ liệu thử không nhạy cảm, quyền repo, có/không B2 test bucket.

**Trước đợt 1 production:** lựa chọn đăng nhập, cách lưu secret, backup độc lập, retention thùng rác, dung lượng upload tối đa.

**Trước đợt 2:** nhà cung cấp AI phân loại, ngân sách tháng, chính sách dữ liệu riêng tư, bộ taxonomy thử nghiệm, quy tắc phân loại tự động.

**Trước đợt 3:** ChatGPT workspace có quyền cài custom MCP; OAuth provider và domain/tunnel; quyền người dùng khi MCP gọi; giới hạn trích nội dung.

**Đợt 4–5:** Google Drive adapter native, ASR/OCR on-demand, embedding, CDN, thêm provider: quyết theo kết quả sử dụng thật, không áp trước.

## H. Điều kiện bàn giao

- Các file code có hướng dẫn setup; cấu hình mẫu KHÔNG chứa secret; repo clone về chạy local được.
- Database migration được chạy thử; test fixtures không dùng dữ liệu riêng tư.
- Một bản demo giao diện sử dụng API thật (nếu chưa có backend, phải gắn nhãn mock).
- Bản phát hành có ghi version, nguồn commit SHA, checklist kiểm thử và phương án rollback.
- Sau G2: phần mềm thực sự dùng được để quản lý tri thức; sau G3: có MCP ChatGPT đọc được theo quyền.

**Chưa thực hiện ở ngày soạn tài liệu:** không có code frontend/backend triển khai, không có database hoặc production deployment. Đây là kế hoạch công việc và acceptance, không phải kết quả kiểm thử đã PASS.
