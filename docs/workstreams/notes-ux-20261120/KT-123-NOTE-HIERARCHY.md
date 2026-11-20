# KT-123 — Cấu trúc cha–con giữa **các bài ghi chú**, khác với “nội dung liên quan”

**Priority:** CORE UX / HIGH, phát hiện sau kiểm PR #57 ngày 20/11/2026. **Trạng thái:** SPEC_READY / CODE_NOT_RUN / NO_MERGE.  
**Phụ thuộc:** [KT-122 mixed explorer](KT-122-FOLDER-EXPLORER.md) cho cách thể hiện nhất quán; có thể thiết kế API/migration và test độc lập trước. **Base thực thi:** HEAD `codex/notes-ux-integration` (PR #57), tạo PR mới lên nhánh integration hoặc nhánh KT-122 nếu đã có. Không merge khi chưa được phép.

## 1. Nguyên nhân phải làm task riêng

- `Topic.parent` chỉ là **thư mục cha → thư mục con**; `ItemTopic` là **bài thuộc thư mục**.
- `RelatedItem` có cặp `item_a < item_b`, unique theo cặp và chủ yếu `relation_type=similar`, `reason`, confidence/provenance; **không biểu diễn an toàn quan hệ có hướng bài cha → bài con**. Backlinks từ Markdown là “A nhắc tới B”, cũng **không** có nghĩa “B thuộc A”.
- `Topic.node_kind=book/chapter` chỉ gắn nhãn thư mục, không biến bài “Sách”/bài “Chương” thành tài liệu cha–con. Người dùng cần **Sách (bài) → Chương (bài) → Mục (bài)**, vẫn phân biệt với folder.

## 2. Ba mối quan hệ phải thể hiện riêng

| Quan hệ | Kiểu đúng | Ví dụ | Khác với |
| --- | --- | --- | --- |
| Folder → Folder | `Topic.parent` hiện có | Pháp luật → Đầu tư | Không phải quan hệ note |
| Folder → Note | `ItemTopic` + vị trí chính theo KT-122 | Đầu tư → Quy trình điều chỉnh dự án | Note vẫn 1 ID dù có shortcut folder khác |
| **Note → Note** | **Directed structural parent–child** mới, explicit owner choice | Giáo trình → Chương 1 → Bài 1 | Không phải `RelatedItem(similar)`, backlinks hay tự phân loại |

Ngoài ra, có **Note ↔ Note tham chiếu** qua Markdown link/backlink; và **Note ↔ Note liên quan** qua `RelatedItem`, **không tự suy thành structural parent**. Tiêu đề Markdown H1–H6 là **mục lục bên trong một note**, không tự tạo Item con.

## 3. Quyết định đề nghị và yêu cầu kỹ thuật

1. Thiết kế một hợp đồng **ItemHierarchy/ItemParent/ItemRelation typed** tách khỏi `RelatedItem` existing. So sánh 2–3 cách (FK `Item.parent` vs bảng `ItemHierarchyEdge` directed vs typed ItemRelation), chọn cách đơn giản, an toàn và portable. Khuyến nghị **một cha cấu trúc trực tiếp cho một Item** để có cây xác định; **nhiều thư mục/những liên kết tham khảo** vẫn cho phép, không nhầm nhiều folder với nhiều note parents. Nếu cần nhiều cha cấu trúc, phải giải thích UX/backup/cycle trước.
2. Gắn `parent_item_id` / `child_item_id` có hướng, `sort_order`, `origin=user`, version/audit cho thao tác người dùng; chỉ cho cùng owner và item không xóa; cấm `parent==child`, cấm chu trình A→B→C→A, bảo vệ với transaction/concurrent edits. Đổi tên hoặc di chuyển note không mất GUID, file gốc, backlinks.
3. Giao diện explorer có **mở/đóng bài có bài con**, biểu tượng note khác folder; “Tạo ghi chú con” từ bài đang chọn; “Đặt làm con của…” / “Đưa lên cấp trên”; hiển thị breadcrumb và cấu trúc `parent item / child notes`. Nếu một note có folder chính và parent note thì UI phải quy ước một **đường xuất hiện chính** rõ, tránh vòng lặp và tránh nhân đôi bài. Bộ lọc folder và API không cần đi theo folder thật trên Drive.
4. **Mục lục H1–H6 của một note:** bên phải cho phép cuộn/navigating đúng heading của `Item.note` bằng anchor ổn định, không chuyển mọi heading thành ghi chú độc lập. Liên kết A→B và backlinks hiển thị riêng, không nâng “related” thành “child” nếu chưa được người dùng xác nhận.
5. Có trang **Quan hệ của bài** phân loại: “Thuộc bài cha”, “Bài con”, “Được nhắc tới” (backlink), “Liên quan theo gợi ý” (RelatedItem), “Cùng thư mục” — các số đếm riêng, nguyên nhân/provenance. Một node trong nhiều vị trí hiển thị shortcut cùng UUID, không nhân bản nội dung/Asset.
6. **Không tự cấu trúc từ AI**: đề xuất cha–con tự động (nếu có) phải là suggestion, người dùng chấp nhận rồi mới tạo relation; không cắt, hợp nhất hoặc ghi đè `Item.note` để biểu thị hierarchy.
7. Export/backup: lưu directed edges cùng stable UUID, order, version; restore trên PostgreSQL tạm, xử lý missing parent bằng trạng thái/orphan policy minh bạch, không làm rơi note, không xóa các quan hệ khác. Thử chuyển thư mục, đổi tên và gỡ quan hệ không làm hỏng Markdown links/Drive mapping.

## 4. Acceptance bắt buộc

- Cấu trúc thử: 1 folder “Sách”, 2 Item cha, 20 Item con và 3 cấp lồng; chọn/reorder/move note con, breadcrumb và nhánh hiển thị đúng. Không tự suy relation từ giống tiêu đề.
- 30 phép thử API gồm owner/unauth/CSRF, cycle 2/3/4 cạnh, cross-user, soft deleted, hai thao tác concurrent. **0 quan hệ chu trình** được lưu; không tồn tại hai cha cấu trúc khi mode 1 cha.
- Item xuất hiện trong 3 folder + 1 note parent: explorer chỉ hiển thị shortcut có dấu hiệu dễ hiểu, `COUNT(DISTINCT item_id)` đúng; 3 lần đổi tên không làm đứt links/mapping và không làm tăng `CaptureEvent`.
- Restore DB thử: `items_before == items_after`, `edges_before == edges_after`, `orphan_edges == 0` ở dữ liệu chuẩn. Không có môi trường DB/Android/Drive thật → NOT_RUN, không báo PASS từ mock.
- Browser 1920×1080/1440/768/390: keyboard/IME Việt, click heading đúng; các pane phân biệt các loại relation; với 10.000 Item không render toàn bộ tree cùng lúc.
- Test bằng đúng SHA cuối, Django migration forward/back, rollback có bảo toàn dữ liệu, `npm test`/build/Chromium/CI + Code SHA/Tested SHA/PASS/FAIL/NOT_RUN, không merge/deploy.

## 5. Ranh giới và điểm nối

Phải đọc/giữ nguyên `catalog.models.Item/Topic/ItemTopic/RelatedItem`, `knowledge_tree.py`, `KnowledgeTree.tsx`, `LibraryScreen.tsx`, `ItemOrganization.tsx`, `RelatedSources.tsx` của **PR #57**. Tách service/API/fixture mới, chỉ cập nhật UI sau khi có contract. Không dùng `RelatedItem` symmetrical pair như directed parent. Không di chuyển file vật lý Drive theo cây, không thay UUID/nguồn/biên nhận/job. Không sửa dữ liệu production hay `CURRENT_STATE.md` của main. Nếu KT-122 chưa xong, dựng fixture adapter độc lập và ghi cần ghép chỗ nào.

**Trạng thái đầu:** SPEC_READY / IMPLEMENTATION_NOT_RUN. Không đánh dấu DONE chỉ vì PR57 đã có backlinks/RelatedItems.
