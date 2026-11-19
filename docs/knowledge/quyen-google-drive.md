# Quyền theo tệp trong Google Drive

Quyền `drive.file` giới hạn ứng dụng vào các tệp được tạo, mở, chọn hoặc chia sẻ với ứng dụng. **Quyền này không đồng nghĩa với quyền đọc toàn bộ Drive.**

## Hai kết nối cần phân biệt

| Kết nối | Mục đích |
| --- | --- |
| Kho Tri Thức → Google Drive | Lưu media, tài liệu nguồn và bản xuất văn bản |
| ChatGPT/Codex → Google Drive | Tìm và đọc các tài liệu mà connector truy cập được |

Ứng dụng đã lưu được tệp không chứng minh connector đang dùng cùng tài khoản hoặc đã đọc được nội dung. Khi kiểm tra cần xác minh đúng tài khoản, tìm đúng tệp và đọc lại văn bản.

Không mở rộng quyền một cách mặc định chỉ vì một truy vấn không tìm thấy kết quả. Thử từ khóa cụ thể và kiểm tra quyền truy cập của chính tệp đó.

Nguồn: [Google Drive — Choose API scopes](https://developers.google.com/workspace/drive/api/guides/api-specific-auth). Bài diễn giải và hướng dẫn vận hành, biên soạn ngày 19/11/2026.
