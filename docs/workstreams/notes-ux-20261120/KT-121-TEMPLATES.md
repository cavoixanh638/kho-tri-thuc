# KT-121 — UX-P2 CONDITIONAL: mẫu ghi chú và trường theo loại nội dung

**Trạng thái: HOLD, chỉ giao khi cần.** Học có chọn lọc từ Tana, Capacities, Superpowered; **không** fork/tích hợp những nhà cung cấp này làm nguồn dữ liệu.

## Khi được giao

- Có 3–4 template Markdown **tùy chọn** như Bài học, Sách/Chương, Cuộc họp, Video nguồn; field tối thiểu chỉ là metadata bổ sung (tác giả, ngày nguồn, trạng thái trích, liên kết), không bắt người dùng điền form trước khi lưu văn bản.
- Template không tự ghi đè note nguồn, user-pinned, CaptureEvent hoặc DerivedContent. Đổi template không chuyển Item sang Item mới, không nhân bản Drive asset, không sửa hierarchy chung.
- PoC frontend/config trước khi đề xuất migration; đối chiếu 2–3 cách lưu field (JSON có version / table typed / chỉ Markdown) và lập test export/restore.

## Acceptance khi được phép

- Ít nhất 3 mẫu × 10 Item tiếng Việt; lưu/reload/export không mất dữ liệu, giữ stable `item_id`/asset mapping. Nếu chưa có test UI/DB thì `NOT_RUN`. Không thêm công nghệ nặng chỉ vì mô hình Supertag.
