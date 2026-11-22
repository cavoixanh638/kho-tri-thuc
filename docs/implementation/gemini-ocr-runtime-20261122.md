# Gemini OCR ảnh — tích hợp runtime có kiểm soát (22/11/2026)

## Quy trình

1. Người dùng dán/chọn ảnh tại `Gửi vào kho`, có thể kèm chú thích. API nhận nguyên bản và tạo Asset/Item, không gọi AI trong request.
2. Worker `upload_asset` lưu **Google Drive**; chỉ sau khi Drive đã xác minh phiên bản, SHA-256 và trạng thái thì ảnh mới có thể được đưa vào hàng đợi `gemini_image_ocr`.
3. Điều kiện bắt buộc đồng thời: `GEMINI_API_KEY`, `GEMINI_OCR_ENABLED=1`, `GEMINI_OCR_EXTERNAL_PROCESSING_ALLOWED=1`, người dùng đánh dấu **đồng ý gửi ảnh** trong Cài đặt, ảnh gốc JPEG/PNG/WebP/GIF/BMP/AVIF không quá 8 MiB, tài khoản có model đã duyệt và chưa vượt giới hạn nội bộ. Mặc định tất cả **TẮT**.
4. OCR worker dùng `DriveStorage.read_range` (xác minh size, SHA, provider_revision trước/sau) rồi kiểm lại SHA, Pillow chỉ nhận ảnh giải mã được, giới hạn 24 megapixel, xoay EXIF đúng chiều, thu nhỏ cạnh dài tối đa 3200px, bỏ metadata/EXIF và đóng gói PNG/JPEG tối đa 8 MiB. **GIF chỉ khung đầu**. Không gửi note/chú thích nguyên văn lên Gemini.
5. Gửi tới endpoint cố định `v1beta/models/{model}:generateContent`, `x-goog-api-key` trong header, inline image + prompt OCR tiếng Việt + JSON schema. Model ID được lấy từ danh mục duyệt của PR #82, không phải URL người dùng nhập. Timeout 45 giây, phản hồi tối đa 512KiB. Không log ảnh, API key hoặc phản hồi Gemini.
6. Ghi `DerivedContent(kind=image_ocr)` cho chữ OCR và `DerivedContent(kind=image_description)` cho mô tả. Mỗi phần có asset ID, checksum, model và `modelVersion`, version prompt, `review_required=true`. **Không bao giờ sửa ghi chú người dùng**. Text mới tham gia full text search và luật phân nhóm hiện có. Khi OCR cập nhật, kết quả cũ chuyển trạng thái stale.
7. Chặn model dựa trên quota local theo project với transaction/row lock; reservation event trước request. Khi 429 không xác định rõ model-specific, xem là giới hạn project, **không xoay model**, khi 404 lưu tạm ngưng model, 5xx retry hạn chế, key/quyền lỗi thì dừng. Google không có nguồn API bảo đảm số lượng quota còn lại: Usage hiện chỉ quan sát request/token của chính Kho Tri Thức.

## Bật pilot sau khi duyệt

- Tạo `GEMINI_API_KEY` thuộc **dự án Google được phép xử lý tài liệu**, kiểm tra chính sách dữ liệu Free/Paid, chi phí và giới hạn thật trong AI Studio. **Không đưa key vào GitHub, log hay đường dẫn URL**.
- Chọn nhánh đã merge, áp dụng migration `processing.0004_external_ocr_consent`. Kiểm thử endpoint liệt kê model và benchmark OCR tiếng Việt có đối chiếu thủ công.
- Đặt `GEMINI_OCR_ENABLED=1` và `GEMINI_OCR_EXTERNAL_PROCESSING_ALLOWED=1` trong môi trường **sau khi** có quyết định xử lý ảnh ngoài hệ thống; không bật tự động từ CI. Người dùng phải tự bật checkbox ở Cài đặt, không được mặc định đồng ý.
- File tải lên sau thời điểm bật được lên lịch tự động nếu thuộc loại hỗ trợ. Ảnh cũ: `python manage.py queue_gemini_ocr --limit 50` để xem trước, chỉ khi phê duyệt mới chạy `--execute`; command không gọi API, nhưng worker sau đó sẽ xử lý, có thể tính phí.
- Dùng một tài khoản/tập ảnh tổng hợp riêng (bảng số, văn bản quy phạm, ảnh màn hình, ảnh không có chữ, ảnh mờ, tiếng Việt dấu) đo CER/WER, vị trí bảng và tỷ lệ suy đoán. Chỉ cấp quyền truy cập ảnh thật sau khi nghiệm thu chất lượng/điều khoản.
- Tài liệu mật, hồ sơ cá nhân, thông tin định danh: nếu chính sách nội bộ không cho gửi bên thứ ba, **không bật checkbox**; cân nhắc OCR cục bộ PaddleOCR cho nhóm dữ liệu đó.

## Các giới hạn chưa hoàn thành

- Không gọi Gemini với API key thực trong PR/CI. Chưa đo **độ chính xác OCR thực tế** hoặc xác minh mức giá và quota với dự án người dùng.
- Chưa OCR PDF scan nhiều trang, chưa xử lý các trang/khung GIF khác, ảnh >8MiB bị bỏ qua OCR (ảnh gốc vẫn được lưu). Không hứa chữ từ ảnh sẽ chính xác tuyệt đối. Text OCR có `review_required` và có thể sai bảng/số.
- API `models.list` có thể liệt kê model không khả dụng cho project; 404 được xử lý an toàn. Gemini có thể tính phí ngay cả khi đầu ra vô ích; lỗi mất kết nối sau inference có thể dẫn tới chi phí trùng khi job retry dù chưa lưu kết quả. Giới hạn request nội bộ **không** thay thế trần chi tiêu ở AI Studio.
- Android vẫn hoãn; toàn bộ mã nằm trên PR #84 Draft, chưa merge/deploy.

## Lệnh và kiểm thử

- `python manage.py test processing.test_gemini_ocr processing.test_gemini_router storage.test_uploads`
- `python manage.py makemigrations --check --dry-run` và `python manage.py migrate`
- Frontend `npm test` / `npm run build`; giao diện đồng ý gửi ảnh ở Cài đặt.
- GitHub Actions dùng ảnh PNG tổng hợp, HTTP mock; **không có live billing, Drive người dùng hoặc provider model thật**.
- Rollback: giữ flags 0 và thu hồi consent; không xóa ảnh gốc và văn bản người dùng. Không tự hủy kết quả DerivedContent/usage audit nếu revert mã.
