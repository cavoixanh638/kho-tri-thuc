# KT-116 — UX-P0: trích dẫn nguồn mở được đúng trang PDF, đoạn web, thời điểm audio/video

**Trạng thái:** READY_TO_ASSIGN / NOT_RUN. **Giao diện hiện có:** `processing.models.DerivedContent.source_locator` JSON; `ReadKnowledgeService` trả `parts[].locator`, `parts[].asset_id`; `KnowledgeReading.tsx` mới hiển thị page/section và nút mở minh họa, **chưa có jump-to-locator tin cậy**. `AssetPreview.tsx` là thumbnail, **không phải video player**.

## Nhiệm vụ thực thi

1. Kiểm JSON locator đang phát sinh từ PDF/text/transcript, xác định schema phiên bản và độ tin cậy **trước khi tạo field mới**. Có thể dùng adapter nội bộ `parseLocator` nhận `page`, `section`, `start_ms`/`start_seconds`, tùy dữ liệu thực; không tự suy timestamp từ chữ metadata, không nhận URL không an toàn.
2. Chuyển phần đọc nguồn thành citation/source-chip có trạng thái `AVAILABLE / MISSING_LOCATOR / MISSING_ASSET / STALE_SOURCE / NOT_SUPPORTED` hoặc tương đương. Bấm mở đúng file/trang/giây nếu có dữ liệu/format được kiểm; nếu không, chỉ mở file gốc và báo không thể định vị.
3. PDF: dùng viewer hiện có hoặc giải pháp nhỏ bảo đảm truy cập file private; không dùng URL Drive token lộ ra ngoài. Media: thiết kế handler seek dựa trên `HTMLMediaElement.currentTime`, cần xác định **nguồn byte hoặc URL mở có thực sự stream hỗ trợ HTTP Range/CORS/auth**; không đánh đồng thumbnail/Drive preview và player có seek.
4. Không lấy một source = một asset. Giữ quan hệ hiện có và version/processor; một nguồn có thể có nhiều asset hợp lệ. Không sửa raw `Item.note`, Event, Drive ID, không tự ASR toàn bộ nếu thiếu transcript.

## File sở hữu

- `apps/web/src/KnowledgeReading.tsx`, `apps/web/src/SourceLocator*.tsx` và test mới `apps/web/tests/kt116-*.test.mjs`.
- Có thể sửa `apps/backend/processing/read_knowledge.py` và tests **chỉ nếu contract read thiếu dữ liệu bắt buộc**; migration cần proof/backup và chỉ được sau review.
- `ItemScreen.tsx`, `api.ts`, `styles.css`, `package.json` là tích hợp chung/đang do task khác sở hữu; ghi callback/prop yêu cầu G00 nối, tránh xung đột.

## Acceptance

- Fixture **30 locator có ground-truth** PDF/web/audio/video và các case thiếu dữ liệu; expected association `asset_id`/source version đúng **30/30** ở mức mapping logic.
- Với file/video có stream thật và browser, mục tiêu `abs(actual_time-target_time) <= 1s` tại mốc do người dùng bấm, đo ít nhất 20 mốc và công bố codec/device/tolerance. Không có stream/Range/video thật → **NOT_RUN**, không báo PASS seek chỉ vì gọi `currentTime`.
- Xử lý 403/404/stale/expired token an toàn; click không làm lộ OAuth/Drive token; người dùng thấy rõ “chưa có transcript” nếu chưa trích text.
- Run backend unit + `npm test`, `npm run build`, test mới riêng; PR nêu dependency viewer/host và rollback.
