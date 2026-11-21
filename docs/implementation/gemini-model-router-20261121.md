# Gemini model lifecycle & quota-aware routing — 21/11/2026

## Quyết định

**Mặc định Tự động – cân bằng**, có chế độ Tiết kiệm / Chất lượng cao / Thủ công tại Cài đặt. Không chọn model có phiên bản lớn nhất chỉ vì số hiệu lớn. Gemini 4, image-generation, TTS, Live, experimental và alias `-latest` KHÔNG tự đưa vào pipeline OCR.

Cần phân biệt **ba khái niệm**: Google đã công bố model; model xuất hiện trong `models.list` cho API key; model thực sự trả lời được yêu cầu OCR trong hạn mức của **project**. Ba trạng thái này không tương đương.

## Nguồn chính thức đã kiểm tra

- REST Models API: https://ai.google.dev/api/models — `GET https://generativelanguage.googleapis.com/v1beta/models`, phân trang bằng `nextPageToken`, có `supportedGenerationMethods`, token limits, **không có số quota còn lại, giá, OCR benchmark hoặc image capability assurance**.
- Rate limits: https://ai.google.dev/gemini-api/docs/rate-limits — RPM/TPM/RPD, giới hạn theo **project** (không phải API key); RPD đặt lại vào nửa đêm Pacific; 429 có thể là quota, spend cap, prepay, tier, chứ không đơn giản là hết lượt của một model.
- Official models & lifecycle: https://ai.google.dev/gemini-api/docs/models, https://ai.google.dev/gemini-api/docs/deprecations, https://ai.google.dev/gemini-api/docs/changelog
- Pricing: https://ai.google.dev/gemini-api/docs/pricing — giá tùy model, hình thức xử lý, tier và thời điểm; KHÔNG lấy giả từ `models.list`.

**Ghi chú 21/11/2026:** Có nhiều model Gemini 3.x và 4.x; 2.5 Flash/Pro ở nhiều dự án mới đã khó sử dụng. Danh sách `MODEL_PROFILES` cần benchmark trên ảnh tiếng Việt của Kho Tri Thức trước khi thay đổi. Đừng copy số phiên bản mới nhất vào code để tự chuyển!

## Cơ chế đã cài trên nhánh này

1. Khi **máy chủ có GEMINI_API_KEY**, worker chạy kiểm tra nền, mỗi 10 phút hỏi xem đã đến kỳ hay chưa; sau mỗi lần đồng bộ thành công chỉ gọi Google `models.list` **12 giờ/lần**, có DB lease chống nhiều worker chạy trùng. Có thể staff yêu cầu refresh sớm nhưng không vượt giới hạn 5 phút.
2. Lấy đủ các trang, chặn redirect, HTTPS host cố định, `x-goog-api-key` trong header (không nằm ở URL), kích cỡ tối đa 3MiB/trang, timeout 10s/trang, tối đa 10 trang, không ghi API key/response thô vào log.
3. Lưu danh sách model trong PostgreSQL; model mới chưa thuộc `MODEL_PROFILES` là `reviewed=False`, chỉ xuất hiện trong mục "chưa đánh giá", **không tự kích hoạt**. Model có tên trùng profile chỉ được coi là *ứng viên đã rà tài liệu*, chưa được coi là đã qua OCR benchmark hoặc còn quota.
4. Chỉ đánh dấu model không còn được liệt kê sau **hai lần đồng bộ đầy đủ liên tiếp**; khi lỗi mạng giữ danh mục tốt gần nhất. Ngày shutdown/chính sách giá **không** có trong API — cần xem changelog/deprecations và cập nhật policy riêng.
5. `gemini_policy.choose_model`: nhiệm vụ `ocr_simple / ocr_complex / tagging` phân biệt; cân bằng: Flash-Lite cho ảnh đơn giản, Flash cho ảnh khó; chất lượng cao ưu tiên 3.8 với `GEMINI_ALLOW_PREMIUM_MODELS=1`. Manual = 1 model, không fallback âm thầm. Mọi model mới/không được duyệt, tạo ảnh, video, TTS không bao giờ vào OCR vì tên gọi.
6. `gemini_routing.select_for_user`: **chưa gọi API OCR**; nó cung cấp ứng viên theo chính sách. Số lần gọi/tokens trong PostgreSQL là *số đo nội bộ*, không là số hạn mức còn lại thực trên Google. `model_rate_limit` cho cooldown 10 phút; `project_quota` hoặc `billing_exhausted` chặn thay model trong ngày; giới hạn nội bộ mặc định 80 lượt/ngày theo mốc Pacific.
7. Mặc định `GEMINI_OCR_ENABLED=0`, `GEMINI_ALLOW_PREMIUM_MODELS=0`. Có key vẫn chỉ làm mới **metadata**; không tự gửi ảnh cá nhân, không chạy benchmark trả phí, không phát sinh lệnh generateContent cho tới khi OCR adapter được hoàn thiện và được bật có chủ đích.

## Tiêu chí để duyệt model Gemini mới

- Có xác minh hỗ trợ **ảnh đầu vào** và `generateContent`/structured output; không phải image generation, TTS, Live hoặc preview đã sắp hết vòng đời.
- Kiểm thử bằng bộ ảnh tiếng Việt độc lập (văn bản hành chính, ảnh màn hình, bảng số liệu, slide, ảnh nghiêng/mờ, không có chữ). So CER/WER, số liệu bảng, diễn giải sai và JSON schema.
- Có bằng chứng tài khoản thật gọi được, kết quả ổn định; không dựa duy nhất vào `models.list`.
- Cập nhật giá và đánh giá chính sách dữ liệu Free/Paid trước khi được cho phép. Trong môi trường có billing, mọi token có thể phát sinh phí; **không có cách bảo đảm miễn phí chỉ bằng tên model**.
- Đưa mẫu qua kiểm thử, PR phê duyệt hoặc feature flag rồi mới nâng profile. Ghi mã model, phiên bản policy, prompt, timestamp trong DerivedContent; không thay đổi nội dung OCR cũ khi alias di chuyển.

## Hành vi khi vượt hạn mức / lỗi

| Loại tín hiệu | Tác động |
| --- | --- |
| 429 có bằng chứng là *chỉ* một model hết RPM/TPM | Chờ RetryInfo / backoff; tạm khóa model đó, có thể chọn ứng viên tiếp theo cùng chính sách chi phí |
| 429 chung không rõ nguyên nhân, project-tier/spend cap/prepay | Không "nhảy" model liên tục; dừng xử lý, giữ job chờ, yêu cầu xem AI Studio |
| 503/504 quá tải | Backoff có jitter và số lần thử giới hạn; không kết luận hết hạn mức |
| 404 với model vừa có trong models.list | Có thể bị hạn chế quyền truy cập theo project; vô hiệu ứng viên và yêu cầu kiểm tra, không xóa bản gốc |
| OCR trả JSON lỗi/chữ không chắc chắn | Không tự xác nhận kết quả; chuyển sang kiểm tra hoặc OCR đối chiếu, giữ nguyên tệp gốc |

**Cảnh báo:** mã nhánh này mới thiết lập chính sách, danh mục, UI, DB, telemetry và schedule; **chưa triển khai OCR inference, tính giá theo token chính xác, kiểm tra quota còn lại từ Google, fallback của request thật**. Không merge/deploy như OCR đã chạy. Các chức năng đó cần adapter với benchmark và giới hạn tài chính cụ thể.

## Bộ kiểm thử

- `python manage.py test processing.test_gemini_router`: pagination, header key, lỗi mạng, 2 lần vắng mặt, unknown model, preview/imagegen excluded, profile/manual, Pacific DST, project-wide budget, API permission.
- `python manage.py makemigrations --check --dry-run` và `python manage.py migrate`.
- Frontend `npm test`, `npm run build`; Chromium Settings trên 1440/390 và không lộ API key.
- Không chạy live key trong CI; chỉ `GEMINI_API_KEY` fixture và mocked model list.

## Ràng buộc

- Giữ nguyên PR #79/#81, không merge hoặc deploy.
- Không lưu, hiện hoặc gửi API key vào frontend hoặc log.
- User quyết định có bật gửi ảnh cho Gemini hay không. Tài liệu nhạy cảm có thể chọn chế độ chỉ OCR cục bộ khi xây adapter.
