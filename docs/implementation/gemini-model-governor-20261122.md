# Gemini model discovery and OCR governor — thiết kế kiểm soát cập nhật (22/11/2026)

## Quyết định sản phẩm

Mặc định **Tự động cân bằng**, có thêm **Ưu tiên chất lượng**, **Tiết kiệm**, **Chọn model thủ công**. Tất cả tự động chỉ chọn model **đã kiểm thử OCR ảnh tiếng Việt** và có giá, khả năng truy cập, hạn mức/chi phí được cấu hình; không mặc định model mới nhất mạnh nhất. Manual pin không fallback ngầm. Chọn model tách riêng OCR, phân loại, tóm tắt, ASR và embedding; không trộn các model tạo ảnh/audio đầu ra vào danh sách OCR.

## Cơ chế kiểm tra thường xuyên

1. **Hằng ngày** (worker scheduler của môi trường triển khai, không dùng GitHub Actions mặc định để tránh chi phí): gọi `GET https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000` với `x-goog-api-key` trong header. Theo `nextPageToken` cho đến hết, giới hạn số trang, timeout; không log API key. `processing.gemini_model_catalog.list_models` hiện thực lớp thu thập. Ghi snapshot JSON ở nơi riêng tư theo biến cấu hình, không commit dữ liệu môi trường.
2. **Mỗi lần phát hiện model mới hoặc sửa thông số**: đối chiếu các bản snapshot; thông báo trong cài đặt ở trạng thái *Chưa xác minh*, **không tự chuyển production ngay**.
3. **Hàng tuần**: chạy tập mẫu chuẩn OCR Việt (tiếng Việt có dấu, ảnh mờ, bảng, văn bản pháp lý, ảnh có nhiều ngôn ngữ, infographic). Đo CER/WER, giữ vị trí dòng/bảng, tỷ lệ suy diễn sai, latency và chi phí/token. Không gửi tài liệu nhạy cảm lên free tier. Model mới chỉ được promote nếu vượt chuẩn từng loại tác vụ.
4. **Hằng ngày** rà [Gemini API deprecations](https://ai.google.dev/gemini-api/docs/deprecations) và [release notes](https://ai.google.dev/gemini-api/docs/changelog). Trang web không là giao diện máy đọc ổn định được đảm bảo; cần adapter versioned, fail closed khi không parse được, hoặc kiểm tra thủ công. Trước ngày shutdown, tạo cảnh báo và migration gate.
5. **Khi model trả 429**: phân loại RPM/TPM/RPD/spend cap và Retry-After/ErrorDetails, backoff + jitter, lưu cooldown; chỉ fallback sang model đã xác minh nếu chủ tài khoản cho phép và còn ngân sách. 404: đánh dấu model không khả dụng với dự án hiện tại, không tin chỉ `models.list`. 403/401: lỗi quyền/key, **không thử quay vòng model để vượt giới hạn**. 503: retry có giới hạn.
6. **Khi hết ngân sách**: dừng Gemini, đưa Job vào chờ, hoặc OCR local nếu được cấu hình. Không thay đổi thành gói trả phí hay vượt hạn mức tự đặt.

## Điều phải ghi rõ về hạn mức

Google hiện công bố chủ yếu qua dashboard AI Studio Usage/Rate Limits/Billing theo **Google Cloud project**, không theo mỗi API key. `models.list` **không trả mức quota còn lại hay giá**. Không được tính `remaining` bằng cách lấy danh mục model hoặc dựa trên 429 duy nhất.

Bộ giám sát chỉ có:
- `estimated_remaining` = giới hạn do chủ dự án cấu hình trừ request/token do **chính ứng dụng** đã sử dụng trong kỳ, chỉ là **ước tính** vì dự án có thể có client/app khác.
- `UNKNOWN` khi không có giá, không có số quota thực hoặc tier đổi.
- `AVAILABLE / THROTTLED / BLOCKED / DEPRECATED / NOT_TESTED` là tình trạng quan sát; không tự khẳng định con số quota API thực tế.
- `request_count`, `input_tokens`, `output_tokens`, `usage_metadata`, `modelVersion` (nếu endpoint trả về), job ID, thời điểm, cấu hình model, giá theo phiên bản và SHA ảnh để audit.
- Không coi hạn mức miễn phí là quyền dùng dữ liệu nhạy cảm miễn phí: kiểm tra chính sách dữ liệu/tier thực tế trước.

## Quy tắc chọn tự động

- Lọc: chỉ model input **image** -> output **text**, generateContent, được phép sử dụng, không sắp hết hạn, có đánh giá đạt ngưỡng chất lượng, giá nằm trong ngân sách, không cooldown.
- Balanced: chất lượng đã kiểm định và chi phí, ưu tiên ổn định.
- Quality: quality_score cao nhất đạt ngân sách.
- Economy: giá/tác vụ ước tính thấp nhất trong nhóm đạt chất lượng tối thiểu; ưu tiên Batch khi có thể và người dùng chấp nhận chờ.
- Manual: khóa ID, thông báo khi unavailable, không âm thầm dùng model khác.
- **Không dùng `gemini-flash-latest` trực tiếp cho production**: alias tự đổi làm kết quả/giá thay đổi không báo trước. `modelVersion` của kết quả (nếu API cung cấp) cần được lưu.
- **Không tự "nâng cấp" model ngay khi Google phát hành**: chỉ đưa vào candidates; shadow-evaluation, ngưỡng, rollout 5% -> 25% -> 100% với rollback.

## Phạm vi code checkpoint

- `processing/gemini_model_catalog.py`: danh mục phân trang, key header, snapshot delta, ghi atomic và file 0600.
- `processing/gemini_model_policy.py`: 4 chế độ chọn từ candidates **đã được xác minh**; không phỏng đoán quota.
- `processing/test_gemini_model_governor.py`: dữ liệu giả, không gọi Gemini thật.
- **Chưa tích hợp Gemini API OCR runtime, không có secret ở repo, không có scheduler triển khai, chưa kiểm tra thực với tài khoản AI Studio.** Trước khi bật cho người dùng, cần nối adapter OCR thực, nhập hạn mức, giá, tập gold ảnh và trạng thái model thực trong DB; bảo đảm jobs retry độc lập và snapshot audit.

## Rollback

Không thay schema/production. Nhánh QA chỉ bổ sung module và tài liệu; bỏ nhánh hoặc revert các file riêng nếu không đạt nghiệm thu.
