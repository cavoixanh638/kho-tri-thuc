# KT-006 · Giao diện tiếp nhận và thư viện

Giao diện đã có trên [PR #9](https://github.com/cavoixanh638/kho-tri-thuc/pull/9) và nhánh `codex/kt-006-ui`. Phạm vi sửa nằm trong `apps/web/`.

- `df4a0a402e4935017b3d2925fb1641439fc9b397` thêm Django session và CSRF, gửi URL hoặc ghi chú, biên nhận theo giờ Việt Nam, lịch sử theo lượt gửi, thư viện theo mục, chi tiết và cài đặt Drive.
- `22e2a73df7aadbfc262a8446165badb6dfb1ee71` cải thiện độ tương phản, vùng chạm và cách hiển thị liên kết ở màn hình tablet.
- `06785923a7ab2ff28856aefa5ee1df59b10de83b` thêm gửi tệp multipart qua `POST /api/v1/uploads`. Giới hạn 128 MiB. Khi phản hồi chưa rõ, gửi lại cùng khóa idempotency. Biên nhận xác nhận đã tiếp nhận để xử lý. Nút mở tệp xuất hiện khi tài sản có trạng thái `verified`.

## Bằng chứng tại commit 0678592

- `npm ci`, `npm run build` (TypeScript và Vite) và `git diff --check` đã qua.
- Chromium trên bản Vite preview cùng fixture HTTP chạy qua đăng nhập sai và đúng, xoay CSRF token và giữ Host/Origin, đăng xuất, URL gửi lại với nhiều lượt trong lịch sử, lọc ngày theo UTC+7, sửa nội dung, yêu thích, thùng rác và khôi phục. Đã kiểm tra giữ nguyên ghi chú có dấu, dấu cách và ngắt dòng. Với ghi chú và tệp, fixture đã mô phỏng commit thành công với phản hồi 503, retry trả 200 dùng cùng khóa, lượt gửi mới dùng khóa khác. Đã kiểm tra multipart và việc biên nhận tệp liên kết tới mục đang chờ. Callback OAuth được mô phỏng.
- Chromium tại 1440, 768 và 390 px không tràn ngang. Inspector báo 0 FAIL; hai cảnh báo liên quan đến khoảng trống của màn hình ít dữ liệu và hai khối có độ dài độc lập. Geist được tải cùng miền. Lint báo một cảnh báo về việc đệm số 0 trong khóa idempotency không hiển thị.
- [CI cho commit 0678592](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44334120232) đã được khởi chạy. Trước khi công bố kết quả tích hợp, xác nhận lại CI trên commit điều phối ghép các nhánh.

Việc còn mở là smoke với API Django của nhánh tích hợp và thiết bị Android thật, gồm xác minh OAuth và lưu tệp vào Drive thật khi có cấu hình kiểm thử. Rollback UI bằng revert các commit tương ứng.
