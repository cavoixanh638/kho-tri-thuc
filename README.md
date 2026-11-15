# Kho Tri Thức — Quản lý tri thức cá nhân

**Kế hoạch hiện hành: v4.3 (15/11/2026) — Google Drive là kho dữ liệu chính.**  
**Trạng thái:** mới lập kế hoạch, chưa có mã nguồn ứng dụng hoặc triển khai.

## Dành cho người dùng

Kho Tri Thức giúp tiếp nhận link Facebook/TikTok/YouTube/web, video, ảnh, file và ghi chú; lưu file gốc lên **Google Drive đang có**; tự lấy metadata, trích xuất văn bản đơn giản và AI gợi ý phân nhóm **theo lĩnh vực / dự án / chủ đề**. Có thể xem **theo ngày**, tìm kiếm không dấu và lọc nội dung.

**ChatGPT:** thử ứng dụng Google Drive có sẵn trong ChatGPT trước để đọc và nghiên cứu tài liệu. Chỉ xây MCP riêng nếu cần ChatGPT tìm theo tag/dự án/ghi chú đang lưu trong ứng dụng.

## Quy tắc ưu tiên

1. **Kết nối Drive và lưu file thật** — không cần B2/R2.
2. **Thêm + Thư viện** — link, ghi chú, ảnh/file/video; xem lại được.
3. **Tự phân nhóm và tìm kiếm** — metadata, trích chữ nhẹ, chủ đề/dự án/ngày/tag.
4. **Thử ChatGPT Google Drive** — custom MCP là **tùy chọn**.
5. **Mở rộng khi cần** — Android Share Target, OCR/ASR theo yêu cầu, nâng dung lượng.

## Kiến trúc đề xuất tinh gọn

| Thành phần | Lựa chọn |
| --- | --- |
| Kho file gốc | **Google Drive My Drive**, OAuth `drive.file` |
| Danh mục và tìm kiếm | **SQLite + FTS5**, backup snapshot/JSON lên Drive |
| Backend | **Django + Django Ninja** |
| Frontend | **React + TypeScript + Vite + Mantine** (static/PWA) |
| Tác vụ nền | **1 Python worker + bảng jobs SQLite**, không Redis/Procrastinate |
| Video | yt-dlp + FFmpeg khi nguồn cho phép; link-only fallback |
| Trích văn bản | pypdf, python-docx, openpyxl, Trafilatura, phụ đề nguồn |
| ChatGPT | **Google Drive app trước; MCP riêng chỉ khi thiếu chức năng** |
| Hosting | Chạy Windows/local trước; 1 VPS nhỏ khi cần 24/7 |

Không có lý do triển khai PostgreSQL, B2, R2, hệ thống OAuth server riêng cho MCP, microservices hoặc vector DB ở bản đầu.

## Tài liệu chuẩn (chỉ 5 file sống)

- [MASTER_PLAN.md](docs/MASTER_PLAN.md) — phạm vi sản phẩm v4.3, thứ tự ưu tiên.
- [ARCHITECTURE_AND_DATA.md](docs/ARCHITECTURE_AND_DATA.md) — **so sánh 2–3 phương án mỗi quyết định**, lý do phù hợp, thiết kế kỹ thuật, hạn chế Drive và SQLite.
- [ROADMAP_AND_TESTS.md](docs/ROADMAP_AND_TESTS.md) — backlog KT-xxx và tiêu chí nghiệm thu Drive-first.
- [AGENTS.md](AGENTS.md) — nguyên tắc cho Codex và AI lập trình.
- [README.md](README.md) — trang giới thiệu này.

**Không lưu file cá nhân, OAuth token, mật khẩu hoặc database đang chạy trong repository.**

Benchmark video tham khảo nằm ở repo khác: [video-download-benchmark](https://github.com/cavoixanh638/video-download-benchmark); kết quả benchmark không đồng nghĩa ứng dụng này đã chạy.

**Các lựa chọn vẫn cần thử:** Drive OAuth trên tài khoản thật; giới hạn API; Drive preview; video downloader trên máy thật; chất lượng phân nhóm AI; quyền Google Drive app của ChatGPT.
