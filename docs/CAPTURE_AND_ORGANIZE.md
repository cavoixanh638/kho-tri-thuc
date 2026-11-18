# QUY TRÌNH TIẾP NHẬN VÀ TỰ TỔ CHỨC TRI THỨC — V4.7

**Ngày quyết định:** 18/11/2026. **Trạng thái:** đặc tả để giao Codex, chưa có runtime test PASS.
**Nguồn chuẩn:** tài liệu này mô tả nghiệp vụ; `MASTER_PLAN.md` giữ phạm vi, `ARCHITECTURE_AND_DATA.md` giữ schema/kiến trúc, `ROADMAP_AND_TESTS.md` giữ tiêu chí nghiệm thu; `CURRENT_STATE.md` giữ tiến độ thật.

## 1. Hành vi người dùng cần đạt

Người dùng chỉ cần **gửi một lần**: URL Facebook/TikTok/YouTube/web hoặc ghi chú chữ; về sau có file hoặc URL + ghi chú. Hệ thống **lưu ngay lượt gửi cùng giờ server và nội dung gốc**, không bắt đợi worker, tải video, Google Drive hoặc AI. Sau đó hệ thống tự thu thập nội dung khả dụng, **tìm nhóm có sẵn và tự xếp nếu đủ tin cậy**, tìm các mục cụ thể có nội dung liên quan, đồng thời bảo toàn mọi thời điểm tiếp nhận.

Không hứa "lấy đủ video/nội dung" khi nguồn bị chặn, riêng tư, không có phụ đề hoặc chưa cấu hình ASR. Chỉ được ghi "đã lưu file" khi upload đã verify. Nếu máy chủ/DB không sẵn sàng, UI phải nói "chưa tiếp nhận", không giả thông báo thành công. Offline/PWA queue là bổ sung có điều kiện sau kiểm thử.

## 2. Quy trình chuẩn

~~~text
User send(URL / text)
  -> POST /api/v1/captures
  -> validate + authenticate + server timestamp
  -> PostgreSQL transaction: CaptureEvent + find/create Item + optional Source + Job
  -> commit -> ACK {capture_id, item_id, received_at, state}
  -> worker: fetch metadata/web/video/captions when available -> Drive upload/verify if file
  -> extracted text and source provenance -> candidate retrieval
  -> classification: auto-assign existing groups OR suggest/unclassified
  -> link RelatedItem with evidence -> update each processing state
  -> view: Capture timeline by time / Item library by group/project/tag
~~~

Ghi chú **chỉ là chữ**: lưu nguyên văn Unicode/ngắt dòng trong Item.note, không bắt tạo file Drive; có thể chạy phân nhóm sau. Với link: lưu URL gốc kể cả khi không tải được; content/video metadata, phụ đề/trích xuất chỉ ghi khi thực sự lấy được. Gửi URL + ghi chú: giữ annotation của **từng lần gửi**; không ghi đè Item.note được người dùng chỉnh.

## 3. Thời gian bất biến

| Giá trị | Ý nghĩa | Quy tắc |
| --- | --- | --- |
| `CaptureEvent.server_received_at` | Giờ backend tiếp nhận thành công **một lần gửi** | UTC/timezone-aware, **bất biến**; hiển thị giờ Việt Nam UTC+7 |
| `CaptureEvent.client_sent_at` | Giờ thiết bị tự khai (nếu có) | Chỉ tham khảo, không thay thời gian server |
| `Item.saved_at` | Giờ **tiếp nhận đầu tiên** của Item | Không thay khi gửi lại URL, chạy lại AI, đổi nhóm |
| `Source.published_at` / `Item.published_at` | Giờ nguồn đăng nếu lấy được | Để NULL nếu không biết; không trộn với giờ người dùng gửi |
| `Job.completed_at`, `DerivedContent.created_at` | Giờ xử lý/trích xuất | Không sửa giờ lịch sử |
| `Item.updated_at` | Giờ sửa ghi chú/cập nhật | Độc lập lịch sử lượt gửi |

**Hai màn hình khác nhau:** **Lịch sử tiếp nhận** hiển thị một dòng cho mỗi `CaptureEvent` theo giờ gửi; **Thư viện** hiển thị một card cho mỗi `Item` (có thể chọn sắp theo lần nhận đầu/cuối). Ngày lọc phải chỉ rõ đang lọc *ngày gửi* hay *ngày xuất bản*; mặc định ngày gửi. Backup/restore giữ toàn bộ Event và thứ tự.

## 4. Trùng lặp, retry và nguyên văn

- **URL lần đầu:** Event mới + Item mới + Source/Job. **URL gửi lại sau giờ/ngày khác:** Event mới với giờ mới, tham chiếu Item cũ nếu canonical identity/platform ID hoặc hash đủ chắc; không nhân bản file đã verify. Luôn lưu URL gốc.
- **HTTP retry/timeout cùng `idempotency_key`:** trả về **chính Event cũ**, không tạo Event/Job thứ hai. Request key là theo lần gửi, không được dùng mã URL làm request key.
- **URL có query tracking:** chỉ chuẩn hóa theo quy tắc nền tảng được kiểm thử, không xóa tham số làm thay đổi video/bài. Hai URL cùng chủ đề **không có nghĩa cùng Item**.
- **Hai ghi chú chữ giống/khá giống:** vẫn là **hai Item riêng**; có thể xếp cùng Topic và nối RelatedItem; tuyệt đối không auto-merge hoặc sửa chữ của người dùng.
- **Gửi link + ghi chú, rồi gửi lại kèm ghi chú khác:** giữ nguyên hai annotation trong từng Event; không overwrite Item.note; phải tìm lại được chú thích qua SearchService (ban đầu có query riêng/giới hạn, đo trước khi thêm index).
- **Nguồn không truy cập được:** lưu Event/Item/URL ngay và trạng thái lỗi/partial; không hiển thị đã lưu video, đã có transcript hoặc đã xem nội dung.

## 5. Tự xếp nhóm và tìm nội dung liên quan là HAI nghiệp vụ

**Tự phân loại:** lấy metadata, text/phụ đề có thật, ghi chú, các Topic/Project/Tag đã có; truy hồi ứng viên bằng rules/`SearchService`, và AI nhẹ khi được bật + cho phép. Nếu đủ tin cậy thì `auto_assigned`: **ghi quan hệ ItemTopic/ItemProject/ItemTag thật**. Nếu chưa đủ: `suggested` / `unclassified` (bộ lọc ảo Chưa phân loại) / `needs_review`; người dùng không phải duyệt mỗi lần. **Ưu tiên nhóm có sẵn**, không tạo trùng nghĩa; tự tạo nhóm mới chỉ khi đạt quy tắc chặt chẽ được đo trên bộ thử, nếu không thì để đề xuất. Project cần bằng chứng cụ thể, không suy chỉ từ từ khóa chung. Giữ `origin`, `confidence`, `method_version`, `source_version`, `user_pinned`; AI không ghi đè curated/manual khi trích lại.

**Liên kết nội dung liên quan:** SearchService truy hồi **các Item cụ thể** bằng hai nhóm GIN Item/DerivedContent + pg_trgm, taxonomy, nguồn; AI có thể đánh giá lại *ứng viên* khi được phép. Lưu `RelatedItem` (cặp ID chuẩn hóa tránh trùng 2 chiều, kiểu quan hệ, lý do, độ tin cậy, method/source version, trạng thái). **Liên quan không đồng nghĩa trùng để gộp**. Khi text nguồn thay đổi phải đánh giá stale. Không mặc định PostgreSQL FTS tìm đủ các nội dung đồng nghĩa không có từ chung; đo recall và chỉ nâng semantic khi có bằng chứng.

**Hạn chế AI:** tắt AI ngoài vẫn phải lưu Event/Item và phân nhóm bằng rule nếu đủ rõ; thiếu nội dung thì Chưa phân loại. Mọi prompt/data lấy từ web/video là dữ liệu không đáng tin, không có quyền chỉ đạo hệ thống. Không gửi nội dung người dùng cho model bên ngoài khi chưa được phép; có giới hạn chi phí và phương án fallback.

## 6. Trạng thái độc lập và giao diện

- ACK ngay: **"Đã tiếp nhận lúc HH:mm, dd/MM/yyyy"**, không phải "Đã tải video". Ghi chú chỉ chữ thấy ngay ở Lịch sử/Thư viện.
- `source_fetch`: pending/partial/done/failed; `asset_storage`: not_applicable/pending/verified/failed; `content_extract`: not_available/partial/done/failed; `organization`: pending/auto_assigned/suggested/unclassified/needs_review.
- Trong Item detail: nguồn và giờ gửi, lần gửi lại, nhóm auto/đã chốt, lý do gán nếu có, **Nội dung liên quan** (khác với danh sách Cùng nhóm). Lỗi source có nút thử lại và giải thích phần thiếu.
- Trạng thái worker/AI có thể thay đổi, nhưng **raw input** và giờ Event không đổi. Cài đặt có tùy chọn bật/tắt AI và giới hạn chi phí.

## 7. Mốc thực thi và nghiệm thu

**Gate A:** CaptureEvent + transaction/ACK + ghi chú thuần chữ + URL lưu trước xử lý + lịch sử giờ + retry/idempotency + duplicate có Event mới + backup bảo toàn sự kiện. **Gate B:** thu thập nội dung khả dụng, **tự gán nhóm có sẵn** khi đủ tin cậy (không chỉ gợi ý), RelatedItem có provenance, tìm theo nhóm/ngày, đánh giá precision/coverage. Chưa cần Redis, Meilisearch, vector DB, OCR/ASR hàng loạt hay tự tạo taxonomy phức tạp.

| ID | Kịch bản phải kiểm |
| --- | --- |
| N01 | 08:15 gửi URL: có Event/Item/Job/receipt ngay trước khi worker chạy; không báo file đã lưu |
| N02 | Worker chạy muộn/restart: giờ Event và raw input không đổi |
| N03 | 11:30 ghi chú thuần chữ: nguyên văn Unicode/ngắt dòng, không tạo Drive asset |
| N04 | Gửi lại cùng URL ngày khác: Event mới, một Item/asset khi identity chắc |
| N05 | Retry request cùng key: Event/Job không nhân đôi |
| N06 | Hai ghi chú gần nghĩa: hai Item khác nhau, có thể cùng nhóm và RelatedItem |
| N07 | Link private/404/video thiếu quyền: giữ URL/giờ và ghi partial/failed trung thực |
| N08 | Tắt hoặc lỗi AI: tiếp nhận vẫn thành công, không xóa nhãn curated |
| N09 | Nhóm đã tồn tại + đủ dữ kiện: **auto-gán thật**, có provenance |
| N10 | Người dùng chốt/sửa nhóm: reprocess không ghi đè |
| N11 | Chủ đề chưa rõ hoặc Project không chắc: Chưa phân loại/Đề xuất, không auto tạo nhiều nhóm |
| N12 | DerivedContent đổi version: RelatedItem/nhóm tự động được đánh dấu/đánh giá lại; Event giữ nguyên |
| N13 | Ngày đăng nguồn khác giờ người dùng gửi: hai cột độc lập, lịch sử theo giờ gửi |
| N14 | Backup/restore: mọi Event, Item, raw text, quan hệ và timestamp nguyên vẹn |
| N15 | Cùng URL kèm hai chú thích ở hai lần gửi: từng annotation còn, tìm lại được |
| N16 | Có title nhưng không có transcript: không nói "đã hiểu toàn bộ video" |
| N17 | Cùng ý nhưng dùng từ khác: báo candidate recall và kết quả giới hạn FTS, không tự khẳng định có semantic match |

**Đánh giá chất lượng:** tập 30–50 mục có người kiểm tra cho precision/coverage nhóm auto, tỷ lệ gán sai Project, tỷ lệ Chưa phân loại, chất lượng RelatedItem/recall ứng viên và chi phí AI. Ngưỡng auto-assign/new-group được chọn **sau** thử nghiệm, không tự bịa KPI PASS. Thử thực tế lưu bằng SHA, environment, PASS/FAIL/NOT_RUN trong `CURRENT_STATE.md`; không công bố hoàn thành khi mới có tài liệu.

## 8. Ranh giới và an toàn

Tải video/trích trang chỉ thực hiện khi được phép và công cụ hỗ trợ; không vượt giới hạn riêng tư/DRM. Kiểm tra URL/redirect/SSRF, giới hạn dung lượng/thời gian, không làm lộ token trong log. Nguồn gốc và dữ liệu người dùng không bị AI tự ghi đè. Karakeep là **sản phẩm tham khảo**, không chứng minh Kho Tri Thức đã có tính năng này và không thay thế lựa chọn Django/PostgreSQL/Google Drive đã chốt.

