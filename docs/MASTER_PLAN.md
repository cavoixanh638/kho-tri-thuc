# KHO TRI THỨC — KẾ HOẠCH TỔNG THỂ V4.3 (TINH GỌN, DRIVE-FIRST)

**Ngày rà soát:** 15/11/2026 · **Thay thế:** v4.2 · **Trạng thái:** định hướng để xây ứng dụng, chưa triển khai mã nguồn.  
**Thay đổi cốt lõi:** Chủ sở hữu đã xác nhận **lưu dữ liệu trên Google Drive**, dữ liệu cá nhân tương đối đơn giản, một người dùng, không cần hạ tầng hoặc mô hình bảo mật doanh nghiệp. Những lựa chọn từng đưa B2/R2 làm kho chính **được hủy bỏ**.

## 1. Mục tiêu không đổi

Một ứng dụng dễ dùng trên Android và máy tính, để:
1. Nhận link Facebook/TikTok/YouTube/website; nhận file, ảnh, ghi chú.
2. Lưu **file gốc vào Google Drive của người dùng**, lưu URL gốc và trạng thái thực. Với video, tự tải khi nguồn cho phép và kỹ thuật hỗ trợ; nếu không tải được vẫn giữ link.
3. Lấy metadata, văn bản PDF có lớp chữ/DOCX/XLSX/HTML, phụ đề có sẵn; không chạy OCR/ASR hàng loạt.
4. AI nhẹ gợi ý lĩnh vực, chủ đề, dự án, tag và tên từ dữ liệu có sẵn; giữ quyền sửa thủ công.
5. Xem theo **lĩnh vực / dự án / ngày / loại nội dung**; tìm kiếm tên, mô tả, ghi chú, văn bản trích xuất và lọc.
6. Khi muốn ChatGPT nghiên cứu: **thử ứng dụng Google Drive có sẵn trong ChatGPT trước**. Chỉ xây MCP tùy chỉnh nếu ChatGPT phải tìm theo tag/dự án nội bộ hoặc Drive plugin không đáp ứng được.

**Không làm ngay:** chatbot riêng, vector DB, AI nghiên cứu tự động, graph tri thức, OCR/ASR hàng loạt, Kubernetes, CDN, nhiều kho S3, hạ tầng kiểm soát quyền kiểu doanh nghiệp.

## 2. Lưu trữ: Google Drive là kho CHÍNH

- Người dùng đã có ưu đãi khoảng **500 GB Drive trong năm đầu** (chưa xác minh ngày hết hạn, cần kiểm tra thực tế).
- Tạo thư mục chuyên dụng `Kho Tri Thuc/` trong **My Drive**; ví dụ `Video/`, `Tai lieu/`, `Hinh anh/`, `He thong/`. Tổ chức bằng lĩnh vực, dự án và ngày nằm **trong metadata ứng dụng**, không phải nhiều bản sao/thư mục vật lý.
- Mỗi mục có `item_id`; file có `drive_file_id`. Drive ID không đổi khi người dùng sửa tên hoặc sắp xếp; không lưu đường dẫn dưới dạng định danh.
- **Google Drive API OAuth**: ưu tiên `drive.file` chỉ truy cập file do ứng dụng tạo/mở hợp lệ; nếu muốn duyệt file đã có thì bổ sung Google Picker theo nhu cầu, không đòi quyền đọc toàn bộ Drive.
- Upload lớn qua Google Drive resumable upload; file/Drive preview được mở bằng link Google Drive đã xác thực. Chưa tự xây proxy phát video hoặc presigned URL kiểu S3.
- Có trạng thái `link_saved`, `download_pending`, `file_saved`, `failed` rõ ràng; “đã lưu link” KHÔNG đồng nghĩa “đã lưu video”.
- Nếu Google OAuth có lỗi hoặc quota hết: giữ bản ghi/link, báo lỗi, cho kết nối lại, không giả vờ upload thành công.
- Hạn 500 GB có thể hết sau một năm: theo dõi quota, có thể xuất/migrate về sau; B2/R2 là phương án **chỉ khi cần**.

## 3. Dữ liệu danh mục không nhất thiết cùng công nghệ với file gốc

- File gốc ở Google Drive.
- **Danh mục ứng dụng** (tiêu đề, nguồn, tag, lĩnh vực, dự án, ngày, tình trạng) ưu tiên **SQLite** — database nhẹ, một file, không có PostgreSQL server, phù hợp ít người truy cập.
- File SQLite đang chạy phải nằm **trên ổ cục bộ của backend**, không đặt trực tiếp trong thư mục Google Drive đang đồng bộ.
- Xuất/sao lưu database (SQLite snapshot/JSON/CSV) định kỳ **lên Drive**; giữ ít nhất một bản sao tải xuống PC hoặc nơi độc lập cho dữ liệu không thể tái tạo.
- Tìm kiếm đơn giản bằng SQLite FTS5 + trường text chuẩn hóa tiếng Việt có/không dấu; thử với dữ liệu thực.
- Có thùng rác mềm và bảo vệ không tự xóa bản gốc ngay.

## 4. Mức an toàn vừa đủ

Người dùng không yêu cầu bảo mật doanh nghiệp; chỉ cần:
- **Một tài khoản đăng nhập**, HTTPS khi mở internet; không đăng ký công khai.
- Không đăng công khai file Drive hoặc đặt link “Anyone with link” chỉ để app hoạt động.
- Không lưu mật khẩu, Google access/refresh token vào GitHub hoặc frontend.
- Hạn chế đầu vào URL độc hại (SSRF), tệp quá lớn, tải video mất kiểm soát.
- Sao lưu metadata/file quan trọng và thử khôi phục tối thiểu.
- MCP tùy chỉnh (nếu làm) chỉ đọc; không công khai endpoint vô danh có quyền đọc Drive.

Không làm hệ RBAC nhiều vai trò, audit doanh nghiệp, dịch vụ quản lý khóa chuyên dụng, phân tích tuân thủ hoặc hệ thống backup đa cloud phức tạp.

## 5. Những chức năng bản đầu phải có

| Nhóm | Phạm vi |
| --- | --- |
| Thêm | Dán/chia sẻ URL; nhập ghi chú; tải ảnh, tài liệu, video |
| Lưu vào Drive | File gốc, metadata liên kết tới file ID, trạng thái upload |
| Link video | yt-dlp khi được phép/hỗ trợ, lấy metadata/phụ đề có sẵn, fallback chỉ lưu link |
| Trích xuất nhẹ | PDF có chữ, DOCX, XLSX, bài viết HTML; trích thất bại không xóa file |
| Phân nhóm | Lĩnh vực/chủ đề, dự án, tag, ngày; AI nhẹ gợi ý, người dùng sửa |
| Thư viện | Thẻ/danh sách, xem theo nhiều cách, trang chi tiết, mở Drive |
| Tìm kiếm | Từ khóa, không dấu, lọc ngày/nguồn/dự án/lĩnh vực/tag |
| Tin cậy | Ghi nhận lỗi, retry cơ bản, xóa mềm, backup SQLite |

Phân loại AI có thể tắt; không buộc phải gửi mọi tài liệu cho AI nếu thiếu quyền hoặc quota.

## 6. Lộ trình ưu tiên — chỉ bốn mốc

### Mốc A — Chứng minh Drive và giao diện (đi đầu)

- Xác thực Google Drive trên tài khoản thật, tạo folder, upload một ảnh/PDF, mở lại trên điện thoại và PC.
- Tạo frontend cơ bản, đăng nhập một người dùng, SQLite index.
- Lưu note/link/file vào Drive, thư viện, xem chi tiết.
- Ghi rõ dữ liệu ở Drive, không tạo B2/R2.
- **PASS:** người dùng thực sự lưu và xem lại tài liệu từ chính Drive của mình.

### Mốc B — Tự sắp xếp và tìm kiếm (bản sử dụng hằng ngày)

- Metadata website/video, yt-dlp thử trên host thật, phụ đề có sẵn.
- Trích văn bản nhẹ, AI gợi ý nhóm; lĩnh vực/dự án/ngày/tag.
- Bộ lọc, không dấu, sửa nhóm, phát hiện trùng, trạng thái lỗi.
- Một worker nền nhẹ, không triển khai Redis/Procrastinate/PostgreSQL khi chưa cần.
- **PASS:** gửi nội dung không cần tự chọn thư mục; tìm được bằng chủ đề/dự án/ngày.

### Mốc C — Dùng ChatGPT để nghiên cứu

- **Trước tiên kết nối/thử Google Drive app trong ChatGPT** với thư mục/file thật (phụ thuộc tài khoản/workspace).
- Nếu chỉ cần ChatGPT đọc, so sánh và nghiên cứu file Drive và đáp ứng tốt: **dừng ở đây, không xây MCP**.
- Nếu cần ChatGPT truy vấn taxonomy, tag, ghi chú và văn bản trích xuất riêng: xây MCP chỉ đọc, dùng backend hiện có, thử ChatGPT thật.
- **PASS:** giải quyết được câu hỏi nghiên cứu thực tế; không đánh đồng metadata với nội dung file/video.

### Mốc D — Nâng cấp tùy nhu cầu

Android Share Target khi được máy hỗ trợ, Telegram Bot nếu cần, phân nhóm hàng loạt, OCR/ASR theo yêu cầu, mở rộng lưu trữ sau hết hạn 500 GB.

## 7. Bài thử nghiệm thu thiết yếu

1. Gửi 1 link lỗi và 1 link tải được: phân biệt rõ trạng thái.
2. Lưu 1 ảnh, 1 PDF có chữ, 1 DOCX/XLSX, 1 ghi chú; mở file từ Drive.
3. Tự phân loại cùng một nội dung vào nhiều chủ đề/dự án, xem theo ngày nhưng không nhân file.
4. Tìm “quy hoạch” và “quy hoach” trong tài liệu/ghi chú; kết quả phù hợp.
5. Ngắt mạng khi upload: không thông báo file đã lên Drive nếu chưa xác minh.
6. Khởi động lại worker khi đang xử lý: tác vụ có thể retry, không tạo trùng.
7. Xóa mềm và khôi phục, backup/restore SQLite, đối chiếu drive_file_id.
8. Google OAuth hết hạn/bị thu hồi: báo lỗi và có cách kết nối lại.
9. Nếu có ChatGPT Drive app: thử đọc, so sánh 3 file trong Drive; nếu có MCP riêng: test quyền chỉ đọc.

## 8. Những việc cần xác minh trước khi triển khai thật

- Tài khoản Google Drive nào có 500 GB, thời điểm hết ưu đãi và quota còn lại.
- OAuth project chuyển ra `In production` khi phù hợp; với app External/Testing, refresh token thường hết hạn 7 ngày, không thiết kế như token vĩnh viễn.
- Kênh triển khai: local Windows để thử; VPS nhỏ chỉ thuê khi cần app hoạt động 24/7 và tự tải video.
- Lượng video/thời lượng thực, điều kiện tải hợp pháp và khả năng tải từ IP của host.
- ChatGPT Google Drive app có khả dụng trên workspace và quyền hiện tại hay không.

**Lựa chọn triển khai và bảng so sánh công nghệ:** xem `ARCHITECTURE_AND_DATA.md`. **Thứ tự nhiệm vụ và nghiệm thu:** xem `ROADMAP_AND_TESTS.md`.

**Trạng thái:** tài liệu thiết kế; chưa có app/deployment. Các benchmark video cũ là tham khảo, không phải chứng nhận vận hành của kho này.
