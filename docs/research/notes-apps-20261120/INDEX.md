# Bộ giao việc nghiên cứu độc lập các ứng dụng ghi chú/tri thức — 20/11/2026

**Trạng thái cập nhật 20/11/2026:** **17/17 luồng đã nộp báo cáo vào PR #30–#46**, nhánh riêng, mỗi PR chỉ sửa tệp report được giao; **chưa merge**. G00 đã thẩm định lần hai và đính chính trong [PR #47](https://github.com/cavoixanh638/kho-tri-thuc/pull/47) (**chưa merge**). Việc giao nghiên cứu đã kết thúc ở cấp báo cáo, không phải 17 sản phẩm đã được tích hợp/kiểm thử thực tế. **Giao AI triển khai mới:** [KT-114–KT-121](../../workstreams/notes-ux-20261120/INDEX.md) trên main. Một chat ChatGPT không tự mở 17 chat khác; các luồng ban đầu do người dùng khởi chạy.

**Prompt lịch sử nếu cần tái nghiên cứu một luồng (KHÔNG phải lệnh triển khai):** Mở một chat riêng, dán: `Bạn là luồng Gxx nghiên cứu sản phẩm. Đọc tài liệu tại https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/Gxx-SLUG.md và G00-PROTOCOL.md cùng thư mục; chủ động tra cứu website chính thức và GitHub, lập báo cáo độc lập theo yêu cầu, không xem báo cáo các luồng khác. Nếu được phép, commit vào đúng report/branch riêng và tạo PR, không merge, không sửa code.` Đổi Gxx-SLUG theo dòng bên dưới.

**Quy trình chung:** [G00-PROTOCOL.md](G00-PROTOCOL.md). Bảng nguồn sơ bộ **chỉ G00 đọc sau khi nghiên cứu độc lập nộp báo cáo**: [G00-INITIAL-SOURCES.md](G00-INITIAL-SOURCES.md).

| Luồng | Sản phẩm | Tài liệu giao việc | Ưu tiên |
| --- | --- | --- | --- |
| G01 | Notion | [G01-NOTION.md](G01-NOTION.md) | Chính |
| G02 | Google Keep | [G02-GOOGLE-KEEP.md](G02-GOOGLE-KEEP.md) | Chính |
| G03 | Lark Docs/Wiki/Base | [G03-LARK.md](G03-LARK.md) | Chính |
| G04 | Evernote v11 | [G04-EVERNOTE.md](G04-EVERNOTE.md) | Chính |
| G05 | Microsoft OneNote + Copilot Notebooks | [G05-ONENOTE.md](G05-ONENOTE.md) | Chính |
| G06 | Apple Notes | [G06-APPLE-NOTES.md](G06-APPLE-NOTES.md) | Chính |
| G07 | Mem.ai | [G07-MEM-AI.md](G07-MEM-AI.md) | Chính |
| G08 | Coda / Superhuman Docs | [G08-CODA.md](G08-CODA.md) | Chính |
| G09 | Reflect Classic / Reflect Open | [G09-REFLECT.md](G09-REFLECT.md) | Chính |
| G10 | Superpowered AI Notetaker | [G10-SUPERPOWERED.md](G10-SUPERPOWERED.md) | Chính |
| G11 | Gemini Notebook (trước đây NotebookLM) | [G11-GEMINI-NOTEBOOK.md](G11-GEMINI-NOTEBOOK.md) | Mở rộng |
| G12 | AFFiNE | [G12-AFFINE.md](G12-AFFINE.md) | Mở rộng |
| G13 | Capacities | [G13-CAPACITIES.md](G13-CAPACITIES.md) | Mở rộng |
| G14 | Tana Outliner | [G14-TANA.md](G14-TANA.md) | Mở rộng |
| G15 | Granola | [G15-GRANOLA.md](G15-GRANOLA.md) | Mở rộng |
| G16 | Heptabase | [G16-HEPTABASE.md](G16-HEPTABASE.md) | Mở rộng |
| G17 | Obsidian (đối chứng) | [G17-OBSIDIAN.md](G17-OBSIDIAN.md) | Mở rộng |


**Các nguồn báo cáo chưa merge:** [Danh sách PR G01–G17](https://github.com/cavoixanh638/kho-tri-thuc/pulls?q=is%3Apr+is%3Aopen+research%2Fnotes-20261120), [PR G00 #47](https://github.com/cavoixanh638/kho-tri-thuc/pull/47). Luồng triển khai đọc source thực + `docs/CURRENT_STATE.md`, không lấy điểm product 17 báo cáo làm benchmark chạy được. **Cập nhật chính xác:** Capacities audio Pro đã có (11/2026); Reflect Open có Windows/Linux experimental unsigned, Android chưa hỗ trợ; G00 đã sửa các nhận định này tại PR #47.

## Quy tắc báo cáo
- G01–G17 làm độc lập, không đọc báo cáo khác cho tới khi nộp. Mọi nhánh chỉ sửa `reports/Gxx-...md`; G00 không làm thay kết luận của luồng khác.
- Không nhận định toàn hệ thống đã PASS từ file kế hoạch; lấy chứng cứ từ code/CI và ngày hiện tại.
- G00 tổng hợp theo hai trục: có thay được Kho Tri Thức không, và tính năng nào đáng học. G00 chỉ chọn những ý tưởng có nguồn, chi phí hợp lý và không phá dữ liệu hiện có.
- Không cài plugin/script bên ngoài hoặc đưa dữ liệu riêng tư vào các sản phẩm thử mà chưa có quyền.
