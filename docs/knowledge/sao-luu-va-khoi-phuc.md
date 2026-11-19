# Sao lưu chỉ có giá trị khi khôi phục được

Một kho tri thức cần giữ cả **văn bản, nhóm, lịch sử và liên kết tới tài liệu nguồn**. Có file backup chưa đủ để kết luận khôi phục thành công.

## Công cụ PostgreSQL

`pg_dump` tạo bản xuất nhất quán của một database ngay cả khi database đang được sử dụng đồng thời. Các đối tượng toàn cluster, chẳng hạn role, thuộc phạm vi `pg_dumpall`. Archive được khôi phục bằng `pg_restore`.

## Kiểm tra khôi phục

1. Tạo database mới dành riêng cho lần kiểm tra.
2. Khôi phục bản sao vào database đó.
3. Đối chiếu văn bản, giờ tiếp nhận, nhóm và các định danh.
4. Đọc lại một tệp nguồn và kiểm checksum.

Giữ thêm một bản sao độc lập ngoài nơi lưu file chính. Bảo vệ thông tin đăng nhập riêng với dữ liệu tri thức.

Nguồn: [PostgreSQL 18 — pg_dump](https://www.postgresql.org/docs/18/app-pgdump.html). Phần kiểm tra là quy trình biên soạn cho Kho Tri Thức, ngày 19/11/2026.
