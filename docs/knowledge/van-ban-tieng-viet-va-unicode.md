# Giữ đúng văn bản tiếng Việt

Hai chuỗi có thể nhìn giống nhau nhưng khác cách biểu diễn Unicode. Điều này quan trọng với tìm kiếm, so sánh và kiểm tra toàn vẹn văn bản.

## Các dạng chuẩn hóa

- `NFD`: phân rã chính tắc.
- `NFC`: phân rã chính tắc rồi tổ hợp lại.
- `NFKC` và `NFKD`: bổ sung quy tắc tương thích.

Trong Python, `unicodedata.normalize()` nhận các dạng trên. Không nên mặc định hai chuỗi nhìn giống nhau luôn bằng nhau.

## Áp dụng cho kho tri thức

Nội dung người dùng nhập phải được giữ nguyên. Có thể chuẩn hóa một bản biểu diễn dành cho tìm kiếm, nhưng không ghi đè bản gốc chỉ để dễ so khớp. Kiểm thử cần có chữ **Đ/đ**, dấu tổ hợp, xuống dòng và khoảng trắng.

Nguồn: [Python 3.13 — unicodedata.normalize](https://docs.python.org/3.13/library/unicodedata.html#unicodedata.normalize). Phần áp dụng là khuyến nghị biên soạn cho Kho Tri Thức, ngày 19/11/2026.
