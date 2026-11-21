# KT-122 — Trình quản lý thư mục + ghi chú trong **cùng một cây**, theo thao tác Obsidian

**Priority:** CORE UX / HIGH; phát hiện thiếu sau review PR #57 ngày 20/11/2026. **Trạng thái:** SPEC_READY / CODE_NOT_RUN / NO_MERGE.  
**Đầu việc phụ thuộc:** KT-113 đã có `Topic.parent`, `ItemTopic`, API `/knowledge-tree` và `LibraryScreen/KnowledgeTree`. KT-118 ở **PR #57 chưa merge**, chỉ bổ sung List/Table/Card/Timeline, **không** cung cấp mixed file explorer. **Tích hợp dựa trên HEAD `codex/notes-ux-integration` của PR #57** (đọc commit mới nhất, không hardcode SHA); tạo PR mới **target nhánh integration**, không merge/triển khai. Sau khi thử, G00 quyết định có cherrypick/merge lên PR #57 hay không.

## 1. Bối cảnh và lỗi phạm vi

- Hiện tại cây bên trái (`KnowledgeTree.tsx`) chỉ chứa **các Topic/nhánh**, theo `parent_id`. Các `Item`/ghi chú chỉ hiển thị **trong danh sách riêng bên phải** (`LibraryScreen.tsx`). Chuyển bài sang nhánh phải mở bài → `ItemOrganization` → MultiSelect → Lưu. Không có thao tác kéo/thả bài vào thư mục, nút tạo ghi chú tại thư mục, hay cây có xen kẽ folder + note.
- `Topic.node_kind` hiện có `library/field/series/book/chapter/folder` chỉ là **nhãn loại nhánh**. Không được nói quan hệ “Sách → Chương” giữa **hai `Item`** đã có; phần đó thuộc [KT-123](KT-123-NOTE-HIERARCHY.md).
- Kích thước viewport <= 1100px, `LibraryViews.css` đang ẩn cây ở trạng thái đầu: `.library-tree-content{display:none}`, chỉ hiện sau nút “Mở mục lục kho tri thức”. Việc ẩn phải **có trạng thái rõ, dễ tìm và giữ lựa chọn**, không khiến người dùng tưởng không có folder.
- Tham chiếu UX: [Obsidian File Explorer](https://obsidian.md/help/plugins/file-explorer) (tạo, đổi tên, kéo thả tệp/thư mục); **học mô hình tương tác, không fork mã nguồn**. `Topic`/PostgreSQL mới là folder ảo trong app; file gốc vẫn ở Drive, **không di chuyển file Drive mỗi lần kéo thả**.

## 2. Kết quả bắt buộc

### 2.1. Cây hỗn hợp (mixed explorer)

1. Cột trái có thể mở rộng dạng **folder → folder/note**, cùng thứ tự anh em và thụt cấp. Folder có icon, tên, số lượng Item *duy nhất*; note có icon Markdown/video/PDF thích hợp, tiêu đề, trạng thái; click note mở Item hiện có theo UUID, click folder lọc vùng chính; breadcrumb phản ánh đường dẫn chính đang chọn.
2. Folder có thể **tạo con, đổi tên, chuyển cha, sắp thứ tự, thu gọn/mở rộng**, duy trì quy tắc cấm chu trình/độ sâu, không trùng tên folder cùng cha (NFC+casefold) như API hiện tại. Danh sách lớn **phân trang/lazy-load** note con, không render 10.000 Item trong DOM.
3. Từ folder đang chọn có **“Thêm ghi chú tại đây”** và **“Thêm thư mục con”**; thao tác tạo Item phải dùng luồng CaptureService/auth/CSRF/transaction hiện tại, nhận receipt sau DB commit; lưu `ItemTopic`/home folder hợp lệ. Không tạo nguồn gốc, CaptureEvent hoặc Item mới do chỉ mở folder.
4. Ghi chú có menu ngữ cảnh **Đổi tên/Mở/Chuyển thư mục/Thêm vào thư mục khác/Bỏ khỏi nhánh**; kéo thả được trên desktop, có lựa chọn bằng menu + keyboard tương đương cho mobile/accessibility. **Hai hành động khác nhau:** “Chuyển vị trí chính” và “Thêm vào nhánh khác”. Kéo thả folder vào chính nó/hậu duệ = lỗi 422 không mutate.
5. **Nhiều nhánh nhưng chỉ một Item:** nếu note có `ItemTopic` thuộc nhiều folder thì trong **các folder khác** hiển thị shortcut/reference tới **cùng UUID**, không nhân bản Item/note/Asset/CaptureEvent. Xác định **vị trí chính** một cách bền vững: so sánh lựa chọn tối thiểu (ví dụ `primary` có constraint trong ItemTopic hoặc FK riêng tới Topic) rồi chốt sau migration/rollback review. Không chỉ chọn path bằng sort ngẫu nhiên; auto classification không được xóa/chiếm chỗ home do người dùng chốt.
6. Bảo đảm mục **“Chưa xếp thư mục”**, folder rỗng, di chuyển sai quyền, folder archived, note xóa mềm, cây chuyển nhánh và URL trực tiếp được xử lý đúng. Xóa/ẩn folder **không xóa** Item hay file Drive, không đổi `CaptureEvent.server_received_at`.
7. Không loại bỏ List/Table/Card/Timeline của KT-118. Chúng là cách xem vùng chính của **cùng Item ID**; mixed explorer là navigator, không phải view tạo bản sao. Trên màn <= 1100px, nút mở cây phải hiển thị dễ nhận biết và nhớ trạng thái; không đẩy nội dung hoặc làm mất focus.

### 2.2. API/DB tối thiểu

- Dùng lại `Topic.parent` và `ItemTopic` hiện tại. Trước khi đổi DB, viết **ADR nhỏ** so sánh 2–3 cách giữ home folder (FK Item, unique primary ItemTopic, preference/placement riêng) về migration, constraint, multi membership, pinned, restore và truy xuất nhanh. Ưu tiên cách **ít sửa dữ liệu** nhất, có migration/backfill/rollback.
- API cho cây **mixed** phải có owner filtering, cursor/page, counts (direct vs descendant; `COUNT(DISTINCT item_id)`), sort_order stable, không leak filename/source private và không tải toàn bộ note/asset lớn khi dựng cây.
- Thao tác tạo/chuyển note ↔ folder và folder ↔ folder dưới transaction, CSRF, 404/422/409 thích hợp, input Unicode an toàn. Reorganize chỉ cập nhật quan hệ trình bày, không gọi lại worker tải video/Drive hoặc tái tạo Source/Asset/DerivedContent.
- Không thay Google Drive bằng folder file system, không fork Obsidian, không biến label ngày/thẻ Project thành path vật lý.

## 3. Phạm vi code và xung đột

**Điểm đọc chính:** `apps/web/src/KnowledgeTree.tsx`, `LibraryScreen.tsx`, `LibraryViews.tsx`, `LibraryViews.css`, `ItemOrganization.tsx`; `apps/backend/catalog/models.py`, `knowledge_tree.py`, `knowledge_tree_api.py` (tên thực tế phải tra cây repo), `groups_api.py`, `api.py`; `CaptureService`, `SearchService`, `RelatedItem`.  
**Sở hữu trên nhánh mới KT-122:** file component `KnowledgeExplorer*.tsx/.css`, endpoint folder-placement nếu cần, migrations/tests tên KT-122, và thay đổi kết nối vào `LibraryScreen/KnowledgeTree` **chỉ sau khi base cập nhật đúng PR #57**. Không sửa báo cáo nghiên cứu, dữ liệu thật, production runtime, `CURRENT_STATE.md` trên main hay PR #57 mà người khác đang sửa. Nếu cùng file đang có luồng khác, dùng adapter độc lập và mô tả chỗ G00 nối.

## 4. Kiểm thử bắt buộc / cách đo

- **Folder 5 tầng**, tạo/xóa mềm/chuyển cha/đổi tên; thử cycle, duplicate Unicode, cross-user, archived, deleted và quyền CSRF; không làm mất Item.
- **1 ghi chú xếp 3 thư mục:** toàn hệ chỉ có 1 `Item.id`, 1 note raw, cùng Asset/Drive mapping; di chuyển chính không xóa 2 thư mục phụ; `COUNT(DISTINCT item_id)` đúng trong mọi scope; auto-group không làm thay primary.
- Tạo **10 ghi chú ngay tại thư mục** qua luồng thực (không chỉ mock click); kiểm CaptureEvent mới = +10 khi tạo thành công, refresh/retry cùng idempotency key = +0; không orphan ItemTopic hoặc receipt báo thành công giả.
- **10.000 Item fixture/1.000+ folder nếu đủ giới hạn**: lazy tree/pagination, stable order, không truy xuất 10k note bodies ở lần tải đầu, đo query count/latency với công thức `P95 = percentile_95(samples_ms)`, báo số mẫu và môi trường, không bịa mục tiêu P95 trước benchmark.
- Thử Chromium Windows 1920×1080/1440/768/390, bàn phím Tab/Enter/Space/Arrow, kéo thả và menu tương đương, không tràn. Trình duyệt/Android/Drive thật **NOT_RUN** nếu chưa có.
- `npm test`, `npm run build`, Django/DB tests, test browser thật và CI **ở đúng SHA cuối**. Báo PASS/FAIL/NOT_RUN + data safety + rollback; **không merge, không deploy**.

## 5. Tiêu chí bàn giao

Một người dùng bình thường mở Thư viện sẽ thấy **thư mục và ghi chú trong cùng cây**, có thể tạo/mở/chuyển nội dung ngay trong cây, nhìn thấy bố cục cha–con, và biết đâu là bản gốc so với shortcut. Ghi chú có thể nằm nhiều folder mà vẫn là **một** Item. Quan hệ **bài cha → bài con** là nhiệm vụ khác [KT-123](KT-123-NOTE-HIERARCHY.md); không được dùng RelatedItem “similar” để giả nghĩa cha–con.

**Tình trạng ban đầu:** SPEC_READY / IMPLEMENTATION_NOT_RUN / WINDOWS_UAT_NOT_RUN. Người dùng giao code riêng mới chạy. PR #57 chưa merge, không coi candidate tích hợp là đã có tính năng này.
