# Đọc và viết tri thức bằng Markdown

Văn bản là nội dung chính của một mục trong kho. Media/tài liệu gốc giúp minh
họa và kiểm chứng nguồn; lưu được video chưa đồng nghĩa có nội dung lời nói.

- **Gửi vào kho** mặc định chọn **Văn bản / Markdown**. Dán văn bản hoặc viết
  tiêu đề `#`, danh sách, bảng, liên kết rồi lưu. Mục xuất hiện trong Thư viện.
- Mở mục để đọc phần **Tri thức**. **Chỉnh sửa** mở nội dung Markdown; **Xem
  Markdown gốc** cho xem bản nguyên văn. Text và giờ từng lượt gửi được giữ riêng.
- Nguồn/media nằm sau phần đọc. Văn bản trích xuất vẫn có provenance, không tự
  ghi đè bài đã biên soạn. Với nguồn thiếu text, ứng dụng nói rõ chưa có bài.
- Có thể gửi tệp `.md`/`.markdown` UTF-8 bằng luồng Tệp; worker lưu bản gốc,
  trích văn bản để tìm kiếm và hiển thị Markdown. Nhánh này đã qua extraction
  test; nghiệm thu browser multipart `.md` thật còn chưa chạy.
- Bật **Bản xuất tri thức** cho từng mục để đồng bộ Markdown lên
  `Kho Tri Thuc/ChatGPT_Index`. Bản xuất gắn cùng Item, retry không tạo bài khác.

Ngày 19/11/2026 đã nhập bốn bài công khai có nguồn ở `docs/knowledge/` vào thư
viện đang dùng. Chúng là bài biên soạn thật, khác bốn fixture giả của pilot riêng.
Tại nghiệm thu thư viện có bốn bài và Reel người dùng đã gửi; bốn bài đọc lại
đúng hash/version trên Drive và connector đọc được cả bốn.
[Bằng chứng](text-first-live-results.json).

Người vận hành có lệnh `import_knowledge_notes` để nhập các file được chọn.
Mặc định preview; `--apply` ghi qua CaptureService, `--export` bật bản xuất.
Đã kiểm chạy lại giữ cùng Item/Event và không ghi đè sửa đổi của người dùng.
Nếu nguồn nhập đổi hoặc mục đã xóa, lệnh dừng để người dùng chỉnh/khôi phục
trong thư viện. Không tự quét toàn Drive hoặc nhập bản xuất của chính ứng dụng.
