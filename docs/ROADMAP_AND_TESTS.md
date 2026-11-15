# LỘ TRÌNH VÀ KIỂM THỬ V4.3 — GOOGLE DRIVE TRƯỚC

**Cập nhật:** 15/11/2026 · **Dựa trên:** `MASTER_PLAN.md` và `ARCHITECTURE_AND_DATA.md` v4.3.  
**Chưa có đầu việc nào đã triển khai/PASS.** Bản trước dựa trên B2/R2/PostgreSQL/Procrastinate và MCP bắt buộc đã được thay thế.

## 1. Ưu tiên theo giá trị sử dụng

1. **Kiểm chứng lưu Google Drive:** tạo folder, OAuth, upload, mở file.
2. **Ứng dụng Thêm + Thư viện:** link, ghi chú, ảnh/file/video, danh mục SQLite; thao tác được trên điện thoại/PC.
3. **Tự phân nhóm & tìm kiếm:** metadata, trích xuất nhẹ, AI nhẹ, lĩnh vực/dự án/ngày/tag.
4. **Thử ChatGPT Google Drive app:** đọc, tóm tắt, so sánh file trong thư mục; **chỉ làm MCP nếu thiếu tính năng truy vấn metadata ứng dụng**.
5. **Hoàn thiện:** Android Share Target, xuất/backup, giao diện quản lý hàng loạt, OCR/ASR on-demand khi có nhu cầu.

**Không chờ:** cài B2/R2, PostgreSQL, Procrastinate, Elasticsearch, MCP OAuth server, Docker multi-service, Kubernetes để có bản đầu.

## 2. Đợt A — Drive proof-of-concept và UI skeleton

| Mã | Việc | Tiêu chí đạt |
| --- | --- | --- |
| KT-001 | Kết nối tài khoản Google qua `drive.file` OAuth | Tạo `Kho Tri Thuc` trong My Drive, upload 1 ảnh và 1 PDF, tải/mở lại đúng tài khoản |
| KT-002 | Kiểm tra expiry/reconnect | Biết rõ trạng thái Testing/Production; khi token lỗi báo và kết nối lại; không để credential vào Git |
| KT-003 | Khởi tạo Django 6/Ninja + SQLite | Login 1 người; migration; tạo item + drive file reference |
| KT-004 | React/TS/Vite/Mantine 4 màn hình | Thêm/Thư viện/Chi tiết/Cài đặt responsive, phân biệt dữ liệu thật và mock |
| KT-005 | Smoke backup SQLite local→Drive | Snapshot nhất quán khôi phục được trên máy thử |

**Gate A:** Một file thật từ web/app lên **đúng Google Drive**; thư viện thấy item và mở lại file. Không ghi “đã lưu” chỉ vì đã tạo database record.

## 3. Đợt B — Bản đầu sử dụng hằng ngày

| Mã | Việc | Tiêu chí đạt |
| --- | --- | --- |
| KT-101 | Dán URL/ghi chú/upload PDF-ảnh-video | Có original URL, item ID, trạng thái rõ, tự lưu metadata |
| KT-102 | Google Drive resumable upload | File >5 MB, mạng rớt, retry và xác minh Drive file ID |
| KT-103 | Django model nhóm + tag + ngày | Một item ở nhiều lĩnh vực/dự án, xem theo ngày, không nhân file |
| KT-104 | SQLite FTS5/tìm có dấu & không dấu | Tìm tên/mô tả/ghi chú và lọc ngày, lĩnh vực, dự án |
| KT-105 | yt-dlp worker + temp file + Drive upload | Link nguồn hỗ trợ tải được; nguồn không tải được vẫn lưu link, lỗi không khóa UI |
| KT-106 | Metadata, pypdf/DOCX/XLSX/Web, phụ đề có sẵn | Text extraction fail không xóa gốc, tìm được chữ đã lấy |
| KT-107 | AI gợi ý phân nhóm nhẹ khi cần | Có thể sửa; AI retry không ghi đè gán thủ công, hạn mức chi phí |
| KT-108 | Thùng rác mềm + backup/restore thật | Khôi phục được SQLite với item/group/Drive ID |
| KT-109 | Android web/PWA smoke test | Dán link, mở thư viện, mở Drive viewer trên điện thoại thật |

**Gate B:** Người dùng chia sẻ/dán link, upload file, tìm theo lĩnh vực/dự án/ngày; Drive có file gốc và hệ thống phân biệt rõ link-only. Không cần MCP/Google Sheets/Redis.

## 4. Đợt C — Kết nối ChatGPT với tài liệu

| Mã | Việc | Tiêu chí đạt |
| --- | --- | --- |
| KT-201 | Thử Google Drive app/Library trong ChatGPT | Tìm file, mở 1 PDF/Doc/Sheet, so sánh 3 file; ghi quyền và hạn chế thật |
| KT-202 | Đánh giá nhu cầu custom MCP | Có ít nhất một câu hỏi thực tế không được Drive connector giải quyết nhưng metadata trong SQLite giải quyết được |
| KT-203 (điều kiện) | MCP chỉ đọc: `search`, `fetch` | Chỉ khi KT-202 chứng minh cần; kết nối với ChatGPT và không để lộ dữ liệu |
| KT-204 (điều kiện) | Auth/Tunnel phù hợp MCP | Chỉ khi có KT-203; test workspace/Platform, không tạo OAuth server vội |

**Gate C:** ChatGPT thực sự nghiên cứu được file Drive; nếu plugin đáp ứng đủ, **đợt C hoàn thành mà không có MCP riêng**.

## 5. Đợt D — Chỉ thêm khi có nhu cầu thật

- Share Target Android khi PWA hỗ trợ, hoặc Capacitor nếu chia sẻ thiếu tin cậy.
- Telegram Bot nếu thuận lợi hơn dán link.
- Tăng dung lượng khi Google Drive 500 GB hết/quota thấp; nếu cần mới so B2/R2 hoặc gói Drive.
- OCR/ASR cho nội dung không có chữ/phụ đề **khi người dùng yêu cầu**.
- Bulk edit/backup độc lập hàng tháng nếu dữ liệu trở nên quan trọng.
- Chuyển SQLite→PostgreSQL chỉ nếu có nhiều concurrent users/tác vụ, benchmark chứng minh SQLite không đủ.

## 6. Dữ liệu thử thật và nghiệm thu

**Mẫu nhỏ:** 3 video (mỗi nền tảng FB/TikTok/YouTube nếu có), 3 PDF (có chữ, scan, file lỗi), 3 DOCX/XLSX, 3 link website, 3 ảnh, 5 ghi chú và 5 chủ đề/dự án. Mở rộng lên 30–50 item để kiểm AI.

| Test | Mô tả | PASS |
| --- | --- | --- |
| T01 | OAuth `drive.file` | App tạo được folder và file trong Drive người dùng |
| T02 | OAuth lỗi/revoked | Có thông báo reconnect, link/metadata không mất |
| T03 | Upload 10 MB và ngắt giữa chừng | Không báo file đã lưu khi Drive chưa nhận; retry xác minh |
| T04 | Lưu link không tải được video | Link vẫn có trong thư viện, file status không giả |
| T05 | Video tải được | MP4 thật trong Drive, mở/tải lại được |
| T06 | Trùng link/file | Không phát sinh file lặp vô lý; giữ nguồn phù hợp |
| T07 | Tài liệu có lớp chữ | Trích và tìm được chữ; PDF scan không tạo chữ ảo |
| T08 | Theo lĩnh vực/dự án/ngày | Cùng item hiện ở các view mà không copy file |
| T09 | Gõ không dấu | “quy hoạch” và “quy hoach” tìm tương thích |
| T10 | Đổi nhóm thủ công | AI không ghi đè khi job lặp |
| T11 | Khởi động lại worker | Tác vụ pending/running có thể retry, không nhân file |
| T12 | Backup/restore | SQLite snapshot/JSON khôi phục được link Drive ID và nhóm |
| T13 | Xem trên Android | Mở được app và file trong Drive với đúng tài khoản |
| T14 | ChatGPT Drive (khi có quyền) | Tìm/đọc/so sánh file nguồn; nêu giới hạn |
| T15 | MCP (nếu triển khai) | Chỉ đọc, tìm đúng theo tag/project, không có quyền sửa/xóa |

**Chú ý:** Không lấy số lượng video tải thành công trong benchmark GitHub Actions làm bằng chứng tỉ lệ thành công trên hosting thật. Không cho rằng ChatGPT đã hiểu nội dung video chỉ vì có MP4.

## 7. Những lựa chọn cần quyết định khi thực sự ảnh hưởng

- **Ngay trước KT-001:** tài khoản Drive và quyền OAuth; không phải hỏi tiền VPS, B2 hay Cloudflare trước.
- **Ngay trước KT-105:** môi trường Python chạy thường xuyên (Windows khi mở máy hay VPS 24/7); dung lượng file tạm và mạng.
- **Ngay trước KT-107:** API AI, mức tiền tối đa và có/không cho gửi thumbnail/tài liệu.
- **Ngay trước KT-201:** quyền Google Drive app trong ChatGPT/workspace.
- **Chỉ khi mở MCP:** cách kết nối và xác thực phù hợp.
- **Khi gần hết Drive:** duy trì Google Drive hay chuyển kho; dữ liệu/ID trong app phải xuất được.

## 8. Quy tắc giao Codex

- Đọc `AGENTS.md` → `MASTER_PLAN.md` → phần liên quan của kiến trúc → **một nhiệm vụ KT-xxx**.
- Trước khi thay quyết định công nghệ, so với **2–3 phương án** theo nhu cầu và viện dẫn nguồn/kiểm thử hiện hành.
- Commit SHA, test thực chạy, test chưa chạy, giới hạn và rollback phải có bằng chứng.
- Không “làm đẹp” checkpoint thành PASS nếu thiếu file thật trên Drive hoặc chưa có restore test.
- Chưa làm: **toàn bộ code frontend/backend/MCP**, không nhầm tài liệu này với sản phẩm đã hoàn thành.
