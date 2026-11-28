# Unified inbox — one paste/drop surface (21/11/2026)

## Người dùng nhìn thấy gì?
- Một ô duy nhất **Nhập hoặc thả nội dung** trong màn `#/gui`, không phải chọn Văn bản / Link / Tệp.
- Gõ hoặc dán văn bản Markdown; URL HTTP(S) ở dòng đầu được nhận làm **link** khi không có link khác trong nội dung; đoạn văn chứa nhiều link được giữ nguyên là văn bản, không tự động đi tải từng URL.
- Ctrl+V ảnh từ clipboard, chọn ảnh/tài liệu qua nút trong ô, hoặc kéo-thả tối đa 10 tệp. Có preview cục bộ PNG/JPEG/WebP/GIF/AVIF/BMP (không preview SVG vì nội dung có thể hoạt động).
- Gõ chú thích trong cùng ô trước khi gửi file; mọi tệp có chú thích này trên chính Item chứa tệp. Nhiều tệp hiện là **nhiều Item**, không hứa gom thành một Item đa tệp.
- Biên nhận từng mục được giữ trong trường hợp gửi hàng loạt có một tệp lỗi; chỉ tệp chưa xác nhận được thử lại cùng idempotency key. Lượt gửi mới có key mới.
- Bản nháp và File chỉ giữ trong bộ nhớ tab theo tài khoản, không phải hàng đợi offline bền vững.

## Về phân loại
- Text: `POST /captures` -> Job `organize`. Link: `POST /captures` -> Job `fetch_source`, pipeline nội dung được hỗ trợ sẽ phân loại sau.
- File/ảnh: `POST /uploads` (multipart field `file` + tùy chọn `note`) -> staging, Drive verified, tài liệu văn bản trích xuất rồi phân loại. Không gọi ACK là upload thành công lên Drive.
- Ảnh hoặc file không trích xuất được chữ: Job `organize` bổ sung đánh giá **tên file + chú thích**, chỉ gắn nhóm khi đủ chứng cứ theo quy tắc từ vựng. **Chưa OCR/chưa có AI thị giác**; tình trạng "chưa phân loại" là bình thường, không phải thất bại tải ảnh.
- Ảnh được xem trước trong trình duyệt bằng object URL và được thu hồi sau khi bỏ chọn. Ảnh chưa được tải lên khi đang xem trước.

## Các giới hạn chủ động
- Mỗi tệp <=128 MiB theo API hiện hành, <=10 tệp/lượt; nội dung gõ <=65.536 ký tự. Không tự chuyển đổi SVG/HTML thành ảnh để preview.
- Nếu có file và văn bản URL đồng thời, văn bản là **chú thích của file**; không tự thêm liên kết thành một Source liên kết. Mọi tệp có chú thích chung, không suy ra quan hệ phụ thuộc giữa các mục.
- Tính năng Android Share/IME vật lý được hoãn theo yêu cầu. Chỉ web desktop/mobile browser, không merge/deploy.
- Google Drive thật và văn bản trong ảnh yêu cầu nghiệm thu riêng; không khẳng định đã kiểm chứng trên dữ liệu người dùng.
- Không có API batch atomic và không khẳng định file đã phân loại xong ngay khi có receipt.

## Kiểm thử bắt buộc trước khi merge
- `apps/web/tests/kt117-capture.test.mjs`: 30 share corpus cũ, 401/403, timeout/draft/idempotency; mới có URL detection, một ô, clipboard PNG+note, lỗi giữa batch, giới hạn số lượng/dung lượng.
- `apps/backend/storage/test_uploads.py`: gửi image + caption vào đúng Item, 400 cho note không hợp lệ trước staging, idempotency replay không thay note.
- `tools/smoke/p13_share_contract.mjs` và `apps/web/tests/p13-capture.test.mjs` cập nhật kiểm tra hợp đồng thay vì đòi SegmentedControl cũ.
- `tools/smoke/preview_capture.mjs` chụp ảnh màn `#/gui` và ảnh PNG synthetic preview qua chính React chạy với PostgreSQL cách ly.
- CI phải PASS trên commit HEAD ứng viên của PR này (không dùng kết quả PR #79 cũ). Kiểm tra UX thực trước khi merge hoặc deploy.

## Rollback
Chỉ bỏ các commit trong nhánh `feat/unified-inbox-20261121`. Thay đổi upload là thêm tham số Form tùy chọn, không có migration. Client cũ tiếp tục gửi file như trước.
