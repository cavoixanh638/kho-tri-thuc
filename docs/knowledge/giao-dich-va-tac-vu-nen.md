# Lưu tri thức trước, chạy tác vụ nền sau

Khi gửi nội dung vào kho, cần ghi nhận **văn bản và thời điểm tiếp nhận** trước. Việc tải media hoặc đồng bộ Drive có thể tiếp tục ở nền.

## Nguyên tắc giao dịch

- Chỉ xác nhận tiếp nhận sau khi bản ghi đã commit thành công.
- Với Django, `transaction.on_commit()` đăng ký công việc chạy sau commit.
- Nếu giao dịch rollback, callback đã đăng ký bị bỏ.
- Nếu không có giao dịch đang mở, callback chạy ngay.

## Áp dụng

Văn bản đã lưu phải đọc và tìm được trong thư viện ngay cả khi media còn xử lý. Lỗi tải video không được làm mất nội dung đã tiếp nhận. Một tác vụ nền thất bại có thể retry bằng cùng định danh.

Nguồn: [Django 5.2 — Performing actions after commit](https://docs.djangoproject.com/en/5.2/topics/db/transactions/#performing-actions-after-commit). Đây là bài diễn giải ngắn từ nguồn công khai, biên soạn ngày 19/11/2026.
