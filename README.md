# Kho Tri Thức

**Kho Tri Thức** là dự án quản lý tri thức cá nhân: lưu link, video, hình ảnh, ghi chú và tài liệu; tự trích xuất văn bản ở mức nhẹ, gợi ý phân loại theo **lĩnh vực / chủ đề / dự án**; xem theo **ngày**; tìm kiếm với bộ lọc; kết nối **ChatGPT qua MCP chỉ đọc** để nghiên cứu khi cần.

**Trạng thái: ĐANG THIẾT KẾ — mới có tài liệu kế hoạch, chưa có ứng dụng triển khai.**  
**Kế hoạch hiện hành: v4.2 (15/11/2026).**

## Thứ tự ưu tiên

1. **Lưu và xem lại:** link, ghi chú, tài liệu, ảnh, video nguồn hỗ trợ, chống trùng, B2, job nền, đăng nhập, backup tối thiểu.
2. **Tự sắp xếp và tìm kiếm:** metadata, PDF/Word/Excel/Web trích xuất chữ có sẵn, phụ đề video có sẵn, AI gợi ý phân nhóm, xem theo lĩnh vực/dự án/ngày, bộ lọc.
3. **Kết nối MCP:** ChatGPT tìm và đọc nội dung theo quyền, không xây chatbot riêng.
4. **Tối ưu vận hành:** Android Share/PWA, Google Drive backup, bulk edit, khôi phục/xuất dữ liệu.
5. **Chỉ khi cần:** OCR, ASR tự động, embedding/RAG, AI nghiên cứu sâu, Playwright production, CDN nâng cao.

## Bộ tài liệu chính

- [Kế hoạch tổng thể v4.2](docs/MASTER_PLAN.md) — mục tiêu, phạm vi và quy trình sử dụng.
- [Kiến trúc và dữ liệu](docs/ARCHITECTURE_AND_DATA.md) — lựa chọn frontend/backend/DB/B2/queue/MCP, schema, API, bảo mật, hạ tầng, **danh sách quyết định chưa chốt**.
- [Lộ trình và kiểm thử](docs/ROADMAP_AND_TESTS.md) — thứ tự triển khai, backlog KT-xxx, cổng nghiệm thu và test thực tế.
- [AGENTS.md](AGENTS.md) — quy tắc làm việc dành cho Codex/AI, bảo vệ dữ liệu và phối hợp nhiều nhánh.

## Đề xuất kiến trúc gọn

- UI: **React + TypeScript + Vite**, Tailwind/shadcn, PWA.
- API: **FastAPI + SQLAlchemy + Alembic**.
- Database/search: **PostgreSQL**, không cần vector ban đầu.
- File: **Backblaze B2 riêng tư**; backup độc lập (có thể tận dụng Google Drive 500 GB khi cấu hình).
- Xử lý nền: PostgreSQL-backed queue (đang cần thử), yt-dlp, trích xuất nhẹ.
- Kết nối AI: AI phân nhóm tùy chọn; **MCP chỉ đọc**, qua xác thực phù hợp.
- Hạ tầng: Docker Compose + reverse proxy HTTPS.

Đây là **phương án thiết kế**. Những điểm còn mở (máy chủ, tên miền, chi phí, AI provider, quyền dữ liệu nhạy cảm, phương thức backup, OAuth MCP) được liệt kê ở [Kiến trúc — Mục 12](docs/ARCHITECTURE_AND_DATA.md#12-danh-sách-quyết-định-chưa-chốt--chỉ-cần-người-dùng-xác-nhận-khi-có-căn-cứ).

## Dành cho Codex và người phát triển

Đọc theo thứ tự: `AGENTS.md` → `docs/MASTER_PLAN.md` → phần liên quan trong `docs/ARCHITECTURE_AND_DATA.md` → một hạng mục trong `docs/ROADMAP_AND_TESTS.md`.

**Không coi các hạng mục là đã code/test chỉ vì tài liệu mô tả.** Không commit secrets, tài liệu riêng tư hay file media vào repo.

### Tham khảo kiểm thử video độc lập

[Video Download Benchmark](https://github.com/cavoixanh638/video-download-benchmark) có kết quả thử yt-dlp/Cobalt/phụ đề; kết quả đó **không đồng nghĩa** dịch vụ trong repo này đã triển khai.
