# KT-128 — End-to-End User Journeys & Release Gates

**Phân loại:** RELEASE BLOCKING QA. **Ngày lập:** 20/11/2026. **Trạng thái:** SPEC_READY / IMPLEMENTATION_NOT_RUN. **Nguồn:** [G00 traceability audit](G00-FEATURE-TRACEABILITY.md), PR #30–47, PR #57. Đây là đề xuất có thể giao, **không phải tính năng đã triển khai**.

**Nhiệm vụ:** Sửa lỗi quản trị G00 “CI PASS nhưng UX chính còn thiếu”. Đây là acceptance qua màn hình/browser thật, có evidence, KHÔNG phải chỉ test component và KHÔNG tự merge/production.

**E2E user journeys bắt buộc sau KT122–127:**
1. Tạo kho/folder → folder con → note trong folder → thêm note con → đọc/sửa → chuyển folder bằng kéo thả hoặc menu → home/shortcut nhiều folder vẫn một UUID.
2. Viết `[[` chọn note từ autocomplete → đổi tên đích → backlink và unlinked mentions đúng → Ctrl+K mở note → TOC H1–H6 nhảy trong bài.
3. Gửi URL/clip selected quote vào note có sẵn → giữ bản người viết → có Source/Asset version → click đúng PDF page hoặc video time nếu locator được chứng minh. Thiếu locator phải label trung thực.
4. Lọc theo ngày/Topic/tag, lưu smart collection → đổi nhãn note → collection tự cập nhật; List/Table/Card/Timeline dùng cùng Item IDs.
5. Chọn template/AI manual review (provider OFF), đề xuất không sửa note khi reject; bản export Markdown vault và import DB sạch giữ hierarchy/links/metadata.
6. 10.000 Item PostgreSQL synthetic + tree 1.000 node nếu giới hạn cho phép, pagination/lazy, search đúng distinct IDs; sao lưu/khôi phục có hash; kiểm retry không nhân Event.
7. Windows 1920×1080, 1440, 768, 390, và Android vật lý khi có; IME Unikey/EVKey, keyboard accessibility, `prefers-reduced-motion`; sidebar ở <=1100px phải có affordance dễ nhìn, không gọi “không có folder”.

**Gate:** Mỗi journey ghi `input fixture/expected/actual/tested SHA/screenshots hoặc video không nhạy cảm/PASS-FAIL-NOT_RUN`, thời gian đo theo công thức; tổng pass = passed / executed, NOT_RUN tách riêng. Bất kỳ mất Item/Asset/Event, lộ token, sai quyền, hỏng Markdown là blocker. Drive thật, native PDF page, Android, 100 GB media vẫn NOT_RUN nếu không có bằng chứng. Phân biệt `UNIT_PASS`, `INTEGRATION_PASS`, `BROWSER_UAT_PASS`, `PROD_NOT_RUN`. PR #57 hiện OPEN, không merge/deploy tự động.

**Bàn giao:** Mỗi agent đọc AGENTS.md, CURRENT_STATE.md, code HEAD và các PR đang mở, ghi Code SHA/Tested SHA, lệnh kiểm, PASS/FAIL/NOT_RUN, dependency, rollback; commit/push/PR riêng. Không merge hay deploy. Không được tự sửa hợp đồng data gốc, CURRENT_STATE đồng thời hoặc dữ liệu sản xuất.
