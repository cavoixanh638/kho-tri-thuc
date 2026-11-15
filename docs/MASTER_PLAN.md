# KHO TRI THỨC — KẾ HOẠCH TỔNG THỂ V4.2

**Ngày:** 15/11/2026 · **Trạng thái:** định hướng sản phẩm đã thống nhất; kiến trúc kỹ thuật đang chốt · **Nguồn chân lý về phạm vi:** tài liệu này.

> Mục tiêu ngắn hạn: hệ thống cá nhân để thu thập, lưu giữ, tự sắp xếp và tìm lại nội dung; ChatGPT có thể đọc kho qua MCP theo yêu cầu. KHÔNG biến bản đầu thành nền tảng AI xử lý nặng.

## 1. Nhu cầu và nguyên tắc

- Dùng được trên Android và máy tính Windows thông qua web/PWA, giao diện gọn, thao tác hằng ngày nhanh.
- Đầu vào: link Facebook/TikTok/YouTube/website; video và file tải lên; ảnh, ghi chú viết tay; PDF, DOCX, XLSX; ghi chú văn bản.
- Tự lưu nguồn, file gốc, metadata, thumbnail nếu có; tự tải video **khi kỹ thuật và quyền sử dụng cho phép**. Không hứa tải được mọi link. Link thất bại vẫn được lưu.
- Phân nhóm **theo lĩnh vực, chủ đề, dự án**, đồng thời **xem theo ngày**; một nội dung thuộc nhiều nhóm/dự án nhưng chỉ lưu một bản nội dung gốc.
- AI **nhẹ, có giới hạn chi phí** chỉ hỗ trợ tiêu đề, chủ đề, dự án, tag dựa trên metadata, văn bản trích xuất và ảnh đại diện nếu cần; không có căn cứ thì gắn *Chưa phân loại*.
- Tìm kiếm có dấu/không dấu, tìm trong ghi chú và văn bản trích xuất; bộ lọc kết hợp.
- Bản gốc không bị AI sửa; phân loại thủ công không bị tác vụ AI ghi đè; có thùng rác và lịch sử thay đổi thiết yếu.
- Sao lưu độc lập và thử khôi phục trước khi dùng dữ liệu quan trọng; file gốc được tham chiếu bằng ID nội bộ, không khóa vào Drive/B2.
- Dùng ChatGPT để đọc/nghiên cứu qua MCP **chỉ đọc**; chưa xây chatbot riêng hoặc vector database.

## 2. Phạm vi P0 — Bản đầu tiên phải sử dụng được

| Luồng | Chức năng cần có | Hành vi khi thất bại |
| --- | --- | --- |
| Tiếp nhận | Dán link; chia sẻ Android khi được hỗ trợ; tải file/ảnh; gõ ghi chú | Giữ yêu cầu, hiển thị lỗi cụ thể |
| Lưu trữ | B2 riêng tư, bản gốc, checksum, xem/tải lại; ID ổn định | Phân biệt *đã lưu link* và *đã lưu file* |
| Video | Chuẩn hóa URL, metadata, yt-dlp; adapter dự phòng có kiểm thử | Giữ link + thumbnail; cho bổ sung file |
| Trích xuất nhẹ | PDF có chữ, DOCX, XLSX mức cơ bản, web HTML, phụ đề có sẵn; chạy nền | Giữ file, đánh dấu *chưa đọc được nội dung* |
| Phân nhóm | Lĩnh vực/chủ đề, dự án, tag, AI gợi ý; sửa được | Chưa phân loại, không tự đoán |
| Thư viện | Danh sách, thẻ, xem theo lĩnh vực/dự án/ngày/loại, xem chi tiết | Trạng thái rõ ràng |
| Tìm kiếm | Từ khóa metadata + văn bản; không dấu; lọc đa điều kiện | Không bịa kết quả |
| Quản trị | Chống trùng, sửa tên/nhóm, đánh dấu quan trọng, thùng rác | Không xóa file vật lý ngay |
| Tin cậy | Đăng nhập, quyền, job bền vững, backup offsite, khôi phục cơ bản | Lỗi có thể retry |

**Lưu ý về PWA:** Android Share Target phải được xác minh trên trình duyệt/thiết bị thực; luồng dán link/tải file trên web là phương án dự phòng bắt buộc.

## 3. P1 — Kết nối và hoàn thiện ngay sau thư viện

- MCP remote chỉ đọc cho ChatGPT: tìm kiếm, đọc kết quả, liệt kê và đọc metadata/file được phép; tìm/đọc không phụ thuộc embedding.
- Tích hợp và kiểm thử trong ChatGPT web, theo quyền quản trị workspace thực tế; không hứa hỗ trợ cài MCP trực tiếp từ ứng dụng di động.
- Telegram Bot tùy chọn nếu chia sẻ Android PWA không thuận tiện.
- Đồng bộ/sao lưu Google Drive 500 GB năm đầu theo cách đơn giản (ví dụ rclone), tích hợp OAuth/Picker đầy đủ **không là chốt chặn** của bản đầu.
- Phân nhóm hàng loạt, xuất dữ liệu, thống kê bộ nhớ và trạng thái tác vụ, tối ưu trải nghiệm.

## 4. P2 — Chỉ thêm khi thực sự có nhu cầu

- OCR chữ viết tay/PDF scan; ASR cho video không có phụ đề; vision chi tiết; tài liệu pháp lý/Excel phân tích cấu trúc nâng cao.
- Embedding, semantic search, reranking, chatbot tích hợp; hệ thống nghiên cứu/kiểm chứng tự động; đồ thị tri thức.
- Playwright cho trang JS khó, CDN/Cloudflare, thêm nhà cung cấp cloud và tự động di chuyển kho hàng loạt.
- Khi ChatGPT cần một file thiếu văn bản, có thể bổ sung **tác vụ trích xuất theo yêu cầu**, tách khỏi pipeline mặc định.

## 5. Quy trình vận hành thực tế

### A. Link video

Nhận URL -> kiểm tra an toàn/chuẩn hóa -> kiểm tra trùng -> lưu Source -> lấy metadata -> tải khi được phép và có thể -> xác minh media/checksum -> B2 -> phụ đề nguồn nếu có -> văn bản tìm kiếm -> gợi ý nhóm -> thư viện. Nhiều bước **bất đồng bộ**: xác nhận nhận link KHÔNG đồng nghĩa download thành công.

### B. Tài liệu

Nhận file -> kiểm tra định dạng/dung lượng -> lưu gốc, checksum -> trích văn bản thô theo khả năng -> lập chỉ mục -> phân loại nhẹ -> thư viện. Với PDF scan/mã hóa, ghi trạng thái thiếu văn bản, không tự nhận là đã trích xuất.

### C. Bài viết web

Lưu URL; lấy metadata; trích nội dung chính bằng Trafilatura khi truy cập được; giữ thời gian thu thập và nguồn. Không chạy browser headless trong bản đầu.

### D. Ảnh và ghi chú

Lưu nguyên trạng; ghi chú có thể sửa và tìm toàn văn; ảnh/thumbnail có thể được AI nhìn để gợi ý nhóm khi được người dùng cho phép.

### E. MCP

Người dùng hỏi trong ChatGPT -> MCP gọi API có quyền -> trả về danh sách kết quả + locator -> đọc văn bản trích xuất hoặc báo không có -> ChatGPT tổng hợp. Với MP4 thiếu transcript, MCP **không được khẳng định đã hiểu nội dung video**.

## 6. Cách phân nhóm

- **Lĩnh vực:** nhóm lớn, ví dụ Công việc; Quy hoạch/Đầu tư; Công nghệ/AI; Học tập; Kỹ năng; Đời sống.
- **Chủ đề:** nhóm con tùy chỉnh, có thể đổi tên/sáp nhập.
- **Dự án:** thực thể riêng, có trạng thái và mô tả, một mục nằm trong nhiều dự án.
- **Ngày:** ngày lưu, ngày nguồn công bố (có thể trống), ngày cập nhật; **không dùng ngày như thư mục vật lý**.
- **Tag:** nhãn tự do và nhóm thông minh (Mới lưu, Chưa phân loại, Quan trọng, Đang nghiên cứu, Chưa tải được, Chưa trích xuất).
- Phân loại AI là **đề xuất có nguồn**, giữ ưu tiên lựa chọn thủ công. Không tạo tự động hàng trăm nhóm gần giống.

## 7. Trích xuất nhẹ — RANH GIỚI QUAN TRỌNG

- PDF có lớp chữ: dùng pypdf hoặc bộ trích phù hợp đã kiểm giấy phép, lưu tham chiếu trang khi dễ có.
- DOCX: đoạn văn và bảng ở mức cơ bản.
- XLSX: tên sheet, giá trị ô văn bản/đầu mục và vùng sử dụng; không khẳng định hiểu công thức.
- Website: Trafilatura, không cam kết trang chặn bot/JS.
- Video: phụ đề có sẵn nếu nền tảng cho phép; không tự gọi ASR toàn bộ.
- Tài liệu lớn: giới hạn kích thước, xử lý theo phần và cung cấp đoạn trích khi hỏi; không nhồi toàn văn vào một trường mô tả.
- **Không cho trích xuất/AI làm cản trở việc lưu bản gốc.**

## 8. Tìm kiếm và trải nghiệm

- Một thanh tìm kiếm toàn cục; tìm tên, ghi chú, tác giả, metadata, nội dung trích xuất và phụ đề.
- Bộ lọc chồng: lĩnh vực, chủ đề, dự án, tag, loại nội dung, nền tảng, ngày, trạng thái, quan trọng.
- Màn hình chính dự kiến: **Thêm / Thư viện / Tìm kiếm / Cài đặt**; giao diện responsive desktop/mobile.
- Thẻ mục: thumbnail, tiêu đề, nhóm, thời gian, trạng thái; trang chi tiết có nguồn, nội dung gốc, ghi chú, văn bản trích xuất, thông tin xử lý.
- Các thao tác quan trọng có trạng thái/undo; có xóa mềm và khôi phục.

## 9. Lưu trữ, riêng tư và backup

- File chính trên Backblaze B2 riêng tư; PostgreSQL giữ tri thức/metadata; server chỉ cung cấp quyền file tạm thời theo kiểm tra quyền.
- Có thể dùng Google Drive 500 GB năm đầu làm nơi sao lưu thứ hai; OAuth đầy đủ không bắt buộc.
- Không coi một file trên B2 là backup độc lập của chính nó; backup database và file không tái tạo phải được kiểm thử khôi phục.
- Dữ liệu công việc/nội bộ hạn chế **không tự chuyển cho mô hình AI bên ngoài**. Cấu hình privacy mặc định an toàn và cho phép người dùng kiểm soát.
- Không lấy nội dung bị hạn chế truy cập trái phép hoặc né cơ chế bảo vệ nguồn.

## 10. Thứ tự triển khai đã chốt

1. **Lưu trữ thật và thư viện:** API + DB + B2 + ghi chú/link/file/video nguồn hỗ trợ + xác thực + job + backup.
2. **Sắp xếp thông minh:** metadata + trích xuất nhẹ + lĩnh vực/dự án/ngày/tag + AI nhẹ + tìm kiếm/bộ lọc.
3. **MCP đọc cho ChatGPT:** công cụ tìm và đọc, bảo mật, test nguồn và quyền.
4. **Tối ưu vận hành:** Android share, tùy chọn Telegram, Drive backup, bulk operations, xuất dữ liệu.
5. **AI chuyên sâu tùy chọn:** chỉ đầu tư theo nhu cầu thật.

## 11. Những điều KHÔNG được giả định đã hoàn thành

- GitHub Actions tải được vài video không chứng minh mọi nguồn đều hoạt động ở máy chủ đích.
- Văn bản được trích xuất không đồng nghĩa nội dung có độ chính xác tuyệt đối.
- Có file MP4 không đồng nghĩa ChatGPT qua MCP nghe/xem được nó.
- Có backup nhưng chưa thử restore không được coi là có thể phục hồi.
- Giao diện có nút Share không chứng minh Android đã chia sẻ vào được.
- MCP có endpoint không chứng minh đã kết nối được với workspace ChatGPT thực tế.

## 12. Tài liệu đi kèm và quản trị thay đổi

- `README.md`: hướng dẫn và trạng thái.
- `AGENTS.md`: quy tắc làm việc cho Codex/AI.
- `docs/MASTER_PLAN.md`: yêu cầu và phạm vi sản phẩm (file này).
- `docs/ARCHITECTURE_AND_DATA.md`: lựa chọn kỹ thuật, dữ liệu, giao diện, API và danh sách cần chốt.
- `docs/ROADMAP_AND_TESTS.md`: việc ưu tiên, điều kiện PASS, checkpoint và thứ tự phát hành.

Công nghệ ở tài liệu kiến trúc được đánh dấu **CHỐT ĐỀ XUẤT / CẦN KIỂM THỬ / CHƯA QUYẾT ĐỊNH**; chưa có code triển khai tại thời điểm lập kế hoạch.

**Tham chiếu bài kiểm thử video hiện có:** https://github.com/cavoixanh638/video-download-benchmark (không phải thư viện triển khai sản xuất).
