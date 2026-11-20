# KT-117 — CORE Android + UX-P0: ghi nhanh và nhận chia sẻ PWA

**Trạng thái:** READY_TO_ASSIGN; Android thiết bị thật **NOT_RUN cho tới khi có evidence**.

## Baseline không được làm lại

- `apps/web/public/manifest.webmanifest` **đã có `share_target`** nhận `shared_title`, `shared_text`, `shared_url`.
- `apps/web/src/sharedCapture.ts` đã parse dữ liệu; `CaptureScreen.tsx` đã có text/link/file, retry key, receipt.
- `CaptureService` đảm bảo ACK **sau DB transaction**; offline/network fail **không được** hiện “đã lưu”. Không thêm một bảng Event hoặc queue song song.

## Công việc triển khai

1. Kiểm từng bước Android share từ Chrome/YT/TikTok/file browser (nếu được phép và có thiết bị), khác chế độ PWA đã install/chưa install, tên app, routing/hash và quyền đăng nhập. Viết test URL Unicode, tiêu đề, nhiều URL trong đoạn text, query dài, clip không có URL, dữ liệu sai/malicious.
2. Giảm số thao tác từ “Share → nhận receipt”, ưu tiên note nhanh và xem lại kết quả. Hỗ trợ clear/prefill hợp lý, không bỏ nội dung người dùng trước ACK. Phân biệt receipt Event/Item và trạng thái xử lý video/Drive chưa xong.
3. HTTP retry dùng **cùng** idempotency key, người dùng chủ động gửi lại là **một Event mới**; chống bấm đúp; giữ draft khi 401/403/mất mạng/timeout. Nếu muốn thêm offline queue phải là nhiệm vụ được phê duyệt với test sync, không ngầm hiện đã tiếp nhận.
4. Đảm bảo không tự mở rộng privileged OAuth, không đẩy secret vào URL/share parameters. Không dùng data URL/JS URL trong preview.

## Quyền sửa file

- `CaptureScreen.tsx`, `sharedCapture.ts`, `public/manifest.webmanifest`, test mới `apps/web/tests/kt117-*.test.mjs`; chỉnh capture backend **chỉ** nếu test chứng minh bug nằm ở contract core, PR riêng nếu xung đột.
- Không sửa `ItemScreen.tsx`, `LibraryScreen.tsx`, `KnowledgeReading.tsx`, `styles.css`, runner chung khi chạy song song.

## Acceptance

- Fixture **30 lượt** gồm URL/text/share tiếng Việt; đúng `raw_kind/raw`, chú thích và receipt **30/30**; `new_send = +1 Event`, `same_key_retry = +0 Event`.
- Đo số thao tác và `ACK latency = receipt_timestamp - user_submit_timestamp` từ client (chỉ giá trị tham khảo, không nhầm giờ server); không ấn định SLA khi chưa đo môi trường.
- Thử trên **Android thật** nếu được cấp thiết bị/quyền; ghi trình duyệt/OS, lỗi và screenshot không nhạy cảm. Nếu không, `ANDROID_NOT_RUN` dù jsdom/build PASS.
- Mọi lỗi mạng phải biểu thị chưa nhận hoặc trạng thái chưa biết, không tuyên bố file MP4 đã lưu/Drive verify khi mới có URL.
