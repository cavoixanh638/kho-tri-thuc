# G17 — Đánh giá độc lập Obsidian (đối chứng)

- **Thời điểm chốt:** 20/11/2026 (Asia/Bangkok, UTC+7); ngày truy cập nguồn: 20/11/2026.
- **Sản phẩm:** Obsidian, ứng dụng tri thức *local-first* dựa trên Markdown.
- **Đầu vào nội bộ:** `INDEX.md`, `G17-OBSIDIAN.md`, `G00-PROTOCOL.md`, `README.md`, `docs/CURRENT_STATE.md`, `docs/CAPTURE_AND_ORGANIZE.md` và **mã thật trên GitHub `main`**, không tham khảo báo cáo G01–G16 hay nguồn sơ bộ của G00.
- **Phương pháp:** kiểm tra tài liệu/release note/license/GitHub chính thức và đối chiếu mã; **không cài Obsidian, không đăng nhập, không dùng plugin cộng đồng, không dùng dữ liệu riêng**. Tất cả bài kiểm thử tương tác Obsidian: **NOT_RUN**. Các trạng thái Kxx bên dưới là **đánh giá khả năng theo bằng chứng tài liệu**, không phải kết quả test thực tế.

## 1. Kết luận điều hành (dưới 200 từ)

Obsidian là đối chứng mạnh cho trải nghiệm **viết và đọc Markdown trên máy người dùng**: Live Preview, liên kết hai chiều, tìm nhắc tới chưa tạo liên kết, nhiều dạng xem bằng Bases, Canvas và Web Clipper. File Markdown cục bộ làm giảm phụ thuộc định dạng độc quyền; Windows/Android và thao tác ngoại tuyến là ưu điểm rõ ràng. Bản 1.15.1 công khai ngày 12/11/2026 còn cải thiện tìm kiếm không dấu, trong đó có ký tự tiếng Việt.

Nhưng **Obsidian không thay thế nguyên khối Kho Tri Thức** hiện nay: chưa có bằng chứng về dịch vụ native tạo `CaptureEvent` bất biến theo giờ server, phân biệt gửi lại với HTTP retry, worker thu thập video/phụ đề rồi xác minh file gốc trên Google Drive, hoặc tự gán nhóm cũ với chứng cứ và giữ UUID nghiệp vụ. Sync trả phí không phải kho video hàng trăm GB.

**Đề nghị: Tham khảo UX; PoC nhỏ, có quyền rõ ràng, cho editor/backlinks/Bases-style views.** Giữ Django/PostgreSQL/Drive và bản gốc; chưa tích hợp plugin hay đổi kiến trúc. [O1][O2][O3][O4][O6][O9]

## 2. Phân ranh bằng chứng năm 2026

| Chủ đề | Thực trạng đã công bố và chứng cứ | Loại / lưu ý |
| --- | --- | --- |
| Phiên bản | `Obsidian 1.15.1 Desktop` và `1.15.1 Mobile` **public** ngày 12/11/2026. Desktop cải thiện search relevance, bỏ dấu và ánh xạ `đ`→`d`, index vault lớn; mobile thêm Web viewer và Android widget. | **Released**, không suy ra bộ kiểm thử IME tiếng Việt đã PASS [O1]. |
| Lưu trữ, trình soạn | Vault là thư mục trên thiết bị, ghi chú `.md`, internal links, source mode/Live Preview/Reading view; file vẫn đọc được ngoài ứng dụng. | **Native core**, riêng Unicode/bảng/IME phải thử trực tiếp [O2][O3]. |
| Liên kết | Backlinks gồm *linked mentions* và *unlinked mentions* (dò tên ghi chú); Outgoing links/Graph theo liên kết. | **Native core**; không phải tự hiểu ngữ nghĩa hay `RelatedItem.reason` có version [O4]. |
| Bases | Bộ lõi tạo bảng, list, cards, kanban, map và lọc/sắp xếp bằng properties của Markdown, cấu hình `.base`; thêm layout qua plugin. | **Native core** cho các view được tài liệu liệt kê; không đồng nghĩa auto-assignment/relational DB [O5]. |
| Canvas | Board 2D nối note/media/web, file `.canvas` theo JSON Canvas mở; thẻ text độc lập **không hiện trong backlinks** khi chưa chuyển thành file. | **Native core**; không phải hệ thống bằng chứng có version [O6]. |
| Web Clipper | Extension trình duyệt miễn phí, lưu web content/highlight/metadata theo template về vault; hỗ trợ Firefox Mobile và Safari iOS. Clipper mã nguồn mở. | **Official extension, không phải core capture/worker**; không bảo đảm tải MP4 hoặc transcript YouTube/TikTok/Facebook [O7][O8]. |
| Android, Windows, offline | Ứng dụng hỗ trợ các nền tảng này, đọc/sửa vault offline; sync sau khi online nếu có dịch vụ thích hợp. | **Native client**; trải nghiệm máy thật: **NOT_RUN** [O1][O9]. |
| Obsidian Sync | Standard: **4 USD/tháng trả năm hoặc 5 USD trả tháng**, 1 vault, 1 GB, **5 MB/file**, 1 tháng lịch sử; Plus: **8/10 USD/tháng**, 10 vault, 10 GB (nâng tối đa 100 GB), **200 MB/file**, 12 tháng lịch sử. | **Paid service**, hạn mức trên không đáp ứng hàng trăm GB video [O9][O10]. |
| Xung đột, backup | Sync merge Markdown bằng diff-match-patch, file khác ưu tiên bản sửa sau; có tùy chọn tạo conflict file. Sync **không thay** backup độc lập. | Cần kịch bản phục hồi, không đồng nhất “sync xong” với dữ liệu bất biến [O11][O12]. |
| CLI/Headless | CLI chính thức có tạo/đọc/tìm kiếm note nhưng cần app Obsidian chạy (hoặc được khởi chạy); **Obsidian Headless Sync đang open beta**, yêu cầu thuê bao Sync, chạy đồng bộ vault không GUI. | **Official CLI / beta Headless**; không phải REST API managed catalog, không phải Drive backend [O13][O14]. |
| Plugin, API, AI | Plugin API dành cho extension; plugin cộng đồng có thể đọc file, ra mạng, cài chương trình, không có sandbox permission tinh. Web Clipper có Interpreter tùy cấu hình dịch vụ AI. | **Official API for plugins**, AI tùy chọn/ngoài; không mặc định có backend AI an toàn hoặc provenance [O7][O15][O16]. |
| Giấy phép/portability | App miễn phí cả cá nhân và thương mại, nhưng mã app **không open-source theo MIT**; nội dung thuộc người dùng. Obsidian Clipper và typings plugin API có repo GitHub công khai. `.md` và JSON Canvas portable, nhưng `.base`/wiki links/properties đòi parser phù hợp. | **Core proprietary; một số thành phần open source**. Không sao chép mã giao diện/logic đóng [O6][O8][O17][O18]. |
| Nội dung nguồn | Có thể nhúng PDF, âm thanh, video cục bộ, liên kết trang PDF; không tìm thấy bằng chứng core tạo transcript có locator hoặc tự lưu video Drive theo OAuth. | **Native attachment, custom ingestion**; không suy “xem MP4” = “hiểu nội dung MP4” [O19]. |

**Giới hạn xác minh:** giá/phiên bản tại ngày ghi; web docs có thể thay đổi. “Chưa tìm thấy chức năng core” **không** đồng nghĩa phủ định mọi plugin hiện có. Không có số đo thực tế độ trễ, mức tiêu thụ RAM, thành công sync, khôi phục hay quy mô 10.000 note. Plugin bên thứ ba không được coi là native.

## 3. Ma trận K01–K12 theo quy trình G00

**Quy ước:** mỗi dòng dùng **một nhãn chính** cho toàn bộ yêu cầu của Kho Tri Thức; ô mô tả nêu chức năng native/extension đáp ứng *một phần*. `CUSTOM_BACKEND` nghĩa là phải tự xây lớp nghiệp vụ để đạt đúng hợp đồng, không có nghĩa Obsidian tuyệt đối không thể nối bằng công cụ ngoài. **Cả 12 ca chạy trực tiếp: NOT_RUN.**

| Ca | Trạng thái | Bằng chứng, phần đạt/chưa đạt và cách tái thử |
| --- | --- | --- |
| **K01** Gõ note Việt, receipt/giờ nhận | **CUSTOM_BACKEND** | Gõ và lưu Markdown vào vault là **NATIVE**; URI/CLI có tạo note [O2][O3][O13][O20]. **Thiếu receipt server** có giao dịch và ID bất biến. *Tái thử:* ngắt mạng, tạo note “Đường sắt Hải Phòng”, xem mtime cục bộ và tìm trường server-received; so với receipt API dự án. |
| **K02** URL video/web, lấy metadata/nội dung | **EXTENSION** | Clipper trình duyệt lấy nội dung trang, biểu mẫu và URL [O7]; không có bằng chứng pipeline tự lấy file MP4/phụ đề/Drive từ ba nền tảng. Phần đủ video cần **CUSTOM_BACKEND**. *Tái thử:* clip một trang HTML có title/meta; gửi link video chỉ có metadata, kiểm file media thực sự tồn tại hay không. |
| **K03** Cùng link gửi lại/ngày khác vs retry | **CUSTOM_BACKEND** | Vault lưu note/file; không có `CaptureEvent` + `idempotency_key` native; tạo note trùng và ghi lịch sử lượt gửi là nghiệp vụ khác [O2][O13]. *Tái thử:* gửi URL lần hai và request retry cùng key, kiểm chính xác **2 Event nhưng 1 Item** theo hợp đồng KTTC. |
| **K04** Markdown, bảng, link, Unicode | **NATIVE** | Editor Markdown, properties, links, Live Preview và reading mode [O2][O3]. *Tái thử:* lưu/đọc lại UTF-8 tiếng Việt có dấu, bảng GFM và links; đổi source↔Live Preview↔Reading rồi so hash nguyên văn và vị trí con trỏ. **IME/browser/device NOT_RUN**. |
| **K05** Tự gán vào **nhóm có sẵn** | **CUSTOM_BACKEND** | Bases lọc/hiển thị thuộc tính, không chứng minh bộ máy tự quyết định Topic/Project cũ có threshold và ghi origin/confidence [O5]. *Tái thử:* tạo Topic A, gửi 10 note đủ/thiếu dữ kiện, đo số tự gán đúng mà không click tay; giữ user-pinned. |
| **K06** Backlinks/nội dung liên quan | **NATIVE** | Backlinks và unlinked mentions là native [O4]; chỉ là liên kết/chứa tên, không phải tự đề xuất **semantic RelatedItem + lý do + stale version**. *Tái thử:* hai note khác tên nhưng cùng ý, và một note có wikilink; đối chiếu liên kết thật, unlinked mention và related theo chứng cứ. |
| **K07** PDF/audio/video + nhảy trang/giờ | **CUSTOM_BACKEND** | Đính kèm/nhúng các định dạng là native, PDF link theo trang có thể dùng [O19]. Chưa xác minh luồng transcript + locator giây, seek đồng bộ media Drive + quyền phát. *Tái thử:* PDF nhiều trang, MP4 với subtitle có timecode; bấm trích dẫn đi đúng trang/giây và đối chiếu nguồn. |
| **K08** Nhiều nhóm, view tree/table/card/timeline | **EXTENSION** | Tags/links/folders và **Bases core** table/cards/list/kanban/map đáp ứng phần lớn [O5], nhưng view timeline theo sự kiện và cùng một UUID nghiệp vụ xuyên nhiều Topic không phải toàn bộ cấu trúc vault mặc định; cần extension/custom. *Tái thử:* một note trong hai lĩnh vực và 4 view, kiểm không copy file; timeline theo `server_received_at`. |
| **K09** Android/Windows offline + conflict | **NATIVE** | Client Windows/Android lưu cục bộ, offline; Sync trả phí merge conflict [O1][O9][O11]. *Tái thử:* cùng note đổi hai nơi offline, kết nối lại, xem conflict file/version; IME Android, share intent & quota thực: **NOT_RUN**. |
| **K10** API, import/export MD/assets/backup | **CUSTOM_BACKEND** | MD folder và JSON Canvas portable, CLI và developer Plugin API [O2][O6][O13][O16]. Nhưng export **toàn bộ** Event/UUID/mapping Drive/DerivedContent/restore chuẩn KTTC không có native. Headless **beta + paid**, không REST API [O14]. *Tái thử:* round-trip 100 note+asset+Event/UUID và xác minh all invariants. |
| **K11** AI có nguồn, bảo vệ bài người dùng, phí | **CUSTOM_BACKEND** | Web Clipper Interpreter tùy dịch vụ; plugin cộng đồng có quyền mạnh [O7][O15]. Không có bằng chứng core tách user note/derived/AI, source version và curated override như KTTC. *Tái thử:* AI gợi ý phân loại với nội dung nguồn prompt-injection; xác nhận không sửa note và không truyền dữ liệu riêng khi chưa bật. |
| **K12** >10.000 Item, video hàng trăm GB/Drive | **CUSTOM_BACKEND** | Changelog nói tăng tốc vault hàng nghìn note [O1] nhưng **chưa có benchmark 10.000/100 GB**. Sync tối đa 100 GB và 200 MB/file (Plus); local drive lớn khả thi tùy phần cứng, còn storage remote Google Drive/verification cần tự làm [O10]. *Tái thử:* 10k note giả và media lớn **chỉ môi trường tách biệt**, đo search/index/recovery/Drive checksum. |

**Tóm tắt kiểm thử:** chính sách/phân loại trong ma trận dựa trên docs và inspection mã repo, **không có ca Kxx nào được chạy trên Obsidian**. Những giả định về performance, IME tiếng Việt, PDF seek, sync/conflict và plugin API hiện cần PoC để chuyển từ “đánh giá có căn cứ” sang “nghiệm thu”.

## 4. Đối chiếu *mã hiện hành*, không đối chiếu kế hoạch cũ

| Hợp đồng | Kho Tri Thức có bằng chứng trong `main` (20/11/2026) | Đánh giá khi dùng Obsidian |
| --- | --- | --- |
| Tiếp nhận bất biến | `apps/backend/ingestion/services.py`: `submit_capture` giao dịch tạo `CaptureEvent`; retry cùng key trả Event cũ; link gửi lại cho Event mới; `ingestion/api.py` trả `capture_id/item_id/received_at`. | Obsidian native note+URI/CLI **không thay** server receipt và semantics Event/Item. **Giữ**. |
| Bài viết và giao diện | `apps/web/src/CaptureScreen.tsx` nhận Markdown/link/file; `ItemScreen.tsx` có `Textarea` Markdown, render `KnowledgeText`, xem raw và nguồn. `apps/web/package.json` đã có `react-markdown` + `remark-gfm`. | **Cải thiện UX** Live Preview, chuyển Source/Reading, outline, link autocomplete. Không cần đổi backend hay giả đã có Live Preview. |
| Phân loại và liên hệ | `apps/backend/catalog/models.py`: Topic cây, nhiều Topic/Project/Tag trên cùng Item, `RelatedItem` có reason/confidence/version/status. `catalog/organization.py`: rule gán nhóm có sẵn và cổng liên hệ phụ thuộc candidate provider + ngưỡng. | Mượn trình bày backlinks/unlinked, Bases-style views; **không thay** schema hoặc coi RelatedItem tự động đã nghiệm thu chất lượng. |
| Tìm kiếm | `apps/backend/search/services.py` trả bằng chứng từ Item/DerivedContent/CaptureEvent; `SearchService` giữ phân biệt nguồn. | Học relevance search/điều hướng; benchmark chính thức 1.15.1 về không dấu không thay thế đo recall tiếng Việt của KTTC. |
| Nguồn/Drive | `apps/backend/storage/models.py`: `Asset` UUID, `StorageLocation` Drive provider ID/status, `KnowledgeExport` per-Item có source/exported version. `CURRENT_STATE.md` ghi một Reel Drive đã xác minh hash và pilot riêng 8 Item export. | Obsidian vault không làm backend Drive upload/verify/idempotent media. Chỉ coi MD xuất ra Drive là bản chiếu có version, không phải nguồn chính. |
| Windows/Android | `CURRENT_STATE.md` ghi đã chạy, build, kiểm live trên Windows; Android, share thiết bị và video lớn vẫn **NOT_RUN/chưa đủ bằng chứng**. | Obsidian Android là kinh nghiệm UX hữu ích; **không suy** Android Kho Tri Thức đã PASS. |
| Backup/restore | `CURRENT_STATE.md` ghi test sao lưu/khôi phục thực đã thực hiện có giới hạn; manifest ánh xạ gốc vẫn cần giữ. | Obsidian Sync không phải bản backup/restore Postgres+Asset mapping; không tự bỏ kết quả/giải pháp hiện có. |

**Nguồn mã đã đọc:** [ingestion/services.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/ingestion/services.py), [ingestion/api.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/ingestion/api.py), [catalog/models.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/catalog/models.py), [catalog/organization.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/catalog/organization.py), [search/services.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/search/services.py), [storage/models.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/storage/models.py), [ItemScreen.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/web/src/ItemScreen.tsx), [LibraryScreen.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/web/src/LibraryScreen.tsx), [CURRENT_STATE.md](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/CURRENT_STATE.md). **Không chạy runtime hoặc CI của repo trong luồng nghiên cứu này**.

## 5. Chấm 7 trụ và tính nhạy của đánh giá

**Rubric G00** — điểm **ước lượng dựa trên mức phủ chức năng có chứng cứ**, không phải phép thử tốc độ/độ tin cậy. “Thiếu bằng chứng” được ghi là **UNVERIFIED / khoảng bất định**, *không tự động cho 0*. Vì Kxx chứa yêu cầu backend khác bản chất local note, đây không phải bảng xếp hạng “Obsidian tốt/xấu”.

| Trụ | Điểm tham chiếu | Lý do | Độ tin cậy |
| --- | ---: | --- | --- |
| Capture & ingestion | **8/20** | Local note, URI, Clipper tốt; không có server ACK/event, media worker/Drive verify. | Trung bình |
| Organization & recall | **14/20** | Backlinks, unlinked mentions, Bases, search mạnh; tự gán nhóm có sẵn/RelatedItem có chứng cứ cần custom. | Trung bình |
| Text editor & reading | **14/15** | Live Preview, Markdown, đọc nguồn, link/note, file mở; chưa test IME/Unicode roundtrip. | Cao về chức năng, thấp về test |
| Provenance/related/timestamps | **4/15** | Link trang có native; thiếu event idempotency, source lineage/version, locator đồng bộ. | Trung bình |
| Android/Windows/offline | **9/10** | App đa nền tảng, offline; sync conflict trả phí, thiết bị chưa thử. | Cao về tài liệu, thấp về trải nghiệm |
| Portability/backup | **9/10** | MD/plain files/JSON Canvas có chủ quyền tốt; metadata đặc thù, assets, backup toàn DB không native. | Trung bình–cao |
| Integration/cost/maintenance | **6/10** | App miễn phí, SDK/CLI/Headless; plugin security, Sync/video quota, tích hợp lại nghiệp vụ tốn công. | Trung bình |
| **Tổng** | **64/100** | **Khoảng nhạy cảm gợi ý 54–72/100**, chờ thử tương tác và hiệu năng; không phải kiểm thử PASS. | Trung bình |

**Trục A — thay toàn hệ thống:** **không đạt các điều kiện loại trừ** K01/K03/K05/K10/K11/K12 nếu chỉ dùng native và Sync; không nên thay toàn bộ Django/Postgres/Drive kể cả điểm UX cao.

**Trục B — học/tái sử dụng:** **cao** tại editor, backlinks, multi-view và clip preview. Không được cộng điểm UX để hợp thức hóa bỏ `CaptureEvent`/UUID.

### Các rủi ro và giả định cần phản chứng

1. **Plugin security/chuỗi cung ứng:** community plugin không giới hạn quyền như sandbox; nếu cần REST/MCP qua plugin, nguy cơ lộ vault hoặc chạy mã vượt chức năng. Chỉ dùng API chính thức và audit/cho phép riêng; không cài vào kho thật để “thử nhanh” [O15].
2. **File nhiều GB và đồng bộ:** Sync Plus tối đa 100 GB tổng và 200 MB/file; không tương đương Google Drive hàng trăm GB. Nếu dùng đường dẫn ngoài vault, phải xử lý token/quyền xem/hết hạn/khác thiết bị, không suy file đã được backup [O9][O10][O12].
3. **Phân loại ≠ thư mục/link:** việc copy cùng note vào nhiều folder sẽ tạo bản gốc trùng hoặc phá UUID, làm sai semantics `CaptureEvent`/Item và curated m2m; giữ canonical identity ở DB.
4. **Xung đột khi offline:** markdown merge có thể sinh văn bản chắp vá; canvas/file khác last-write-wins. Không dùng mtime địa phương làm `server_received_at` [O11].
5. **Định dạng mở nhưng metadata chuyên biệt:** `[[wikilink]]`, properties, `.base`, `.canvas` có thể cần converter khi import/export; export MD đơn thuần không mang đầy đủ source lineage, lịch sử và quan hệ. Cần round-trip test.
6. **AI/provenance:** Interpreter/AI plugin không đồng nghĩa bộ xử lý an toàn; phải giữ AI-generated riêng, label xuất xứ và quyền chấp thuận. Không tự suy video đã có transcript từ tên/title.

## 6. Sáu ý tưởng áp dụng có điều kiện (không triển khai mã trong G17)

| ID / quy mô | Đề xuất | Phụ thuộc, rủi ro | Acceptance đo được |
| --- | --- | --- | --- |
| **G17-I1 (M)** | **Live Preview** khi gõ Markdown + chuyển `Source / Edit+Preview / Read`; toolbar và shortcut ưu tiên bàn phím. | Giữ `Item.note` nguyên bản, chặn XSS, xử lý IME Unikey/EVKey; so sánh 2–3 phương án editor theo `AGENTS.md` trước khi chọn thư viện mới, không tự thêm CodeMirror/ProseMirror. | Với 30 note/bảng/link tiếng Việt: nhập/sửa/undo và đổi 3 chế độ không mất dấu, không sửa raw không chủ ý; so diff và cursor/selection; Windows browser PASS trước, Android NOT_RUN đến khi thử. |
| **G17-I2 (M)** | **Panel backlinks + unlinked mentions** ở cạnh bài, tách `link chủ động` khỏi `related tự động` kèm lý do/nguồn/version. | Dùng SearchService và RelatedItem; false positive tên trùng, dữ liệu stale, không ghi đè link user. | A liên kết B -> B thấy backlink A; C chỉ chứa tên B -> unlinked mention riêng; 2 note cùng nghĩa không auto-merge; khi source version thay, badge stale hiển thị; không tự thêm quan hệ không chứng cứ. |
| **G17-I3 (M)** | **Nhiều view cùng dữ liệu**: List/Table/Card/Kanban (chỉ sau đó xét timeline), lưu bộ lọc/sort/group. | Dựa trên một `item_id` và m2m Topic/Project; pagination, hiệu năng 10k; tránh tái tạo DB theo file. | 1 Item thuộc 2 nhánh hiển thị ở cả hai nhưng cùng UUID, sửa ở view A thấy ở B; chuyển view không mất bộ lọc; đo 10k item synthetic. |
| **G17-I4 (M)** | **Xem trước khi clip**: trang web/url/title/đoạn trích/ảnh đại diện và chỉ báo phần nào đã thực nhận, định dạng mẫu ghi nguồn. | Trích HTML từ worker hiện tại, tách nội dung không đáng tin, kiểm SSRF/quota; không thêm extension bên ngoài ở bước đầu. | Trang công khai lưu đúng URL, giờ nhận, provenance, preview; video thiếu transcript hiện `Chưa có văn bản`; request retry giữ Event, gửi mới có Event mới. |
| **G17-I5 (M)** | **Xuất/nhập Markdown portable có frontmatter tối thiểu + manifest** (không làm file Drive thành DB); cho phép mở bằng Obsidian hoặc editor ngoài. | Giữ UUID, hash, timestamp UTC, mapping Asset/StorageLocation riêng; tránh mất m2m/history; xử lý wiki-links/files; tôn trọng opt-in và dữ liệu riêng. | Round-trip 100 note tiếng Việt, 2 Topic/note, 2 capture/link, 1 asset/note: UUID, giờ bất biến, source version, hash file không đổi; không phát tán dữ liệu ngoài opt-in. |
| **G17-I6 (L, hoãn)** | **Board nguồn-cạnh-bài / Canvas-lite** để nối luận điểm–chứng cứ, click trích đoạn tới PDF/trang/video/giây khi có locator thật. | Chỉ mở sau đo nhu cầu và có dữ liệu locator; tính năng 2D nặng, performance 1k nodes, không sao chép code app đóng. | 20 bài mẫu với citation thật: mỗi cạnh truy ngược item/source/locator, rời board không mất note, bảo toàn version; tránh dựng graph vô ích. |

**Thứ tự pilot đề xuất:** I1 → I2 → I3 → I5 → I4 → chỉ xem I6 khi có bằng chứng nhu cầu. Thay thế đối tượng “giao diện Markdown” chỉ sau test tương đương/superior; **không đổi PostgreSQL, Drive, API, worker hay domain models** bằng nghiên cứu này.

## 7. Khuyến nghị, điều kiện đảo chiều và phản chứng

**Chọn hiện tại: THAM KHẢO UX**, chưa “Thay toàn bộ”, chưa “Tích hợp thư viện” hoặc cài plugin. Có thể **Thử PoC** bằng 10–20 note giả/công khai xuất `.md` sang vault riêng (chỉ sau khi chủ sở hữu cho phép và bảo đảm không ghi đè production), đo keyboard flows, Live Preview, backlinks, khả năng export. Không cần tài khoản trả phí.

**Điều kiện để cân nhắc đảo chiều thay toàn hệ thống:** chứng minh qua release docs + PoC rằng một bộ native/official-supported có thể:
- tạo event immutable theo server time, idempotency và map item/asset/URL;
- upload video/Drive thật, verify checksum và retry bền vững;
- tự gán có chứng cứ vào nhóm đã có, bảo vệ nhóm chốt;
- giữ source/provenance/derived version, full restore không mất UUID;
- hoạt động ở quy mô >10.000 bài + hàng trăm GB media với chi phí và quyền hợp lý, trên Windows/Android;
- không phụ thuộc plugin thiếu kiểm soát bảo mật và không phá dữ liệu lịch sử hiện có.

**Phản chứng khiến ngay cả PoC UX không đáng tiếp tục:** trải nghiệm gõ/preview tiếng Việt không khá hơn editor hiện có; lỗi cursor/IME hoặc định dạng quá thường xuyên; mất nguồn khi round-trip; rủi ro plugin/giấy phép/chi phí cao hơn lợi ích; chi phí triển khai/duy trì vượt mục tiêu đơn giản.

**Điều kiện có thể giảm đánh giá hiện tại:** thử thực tế 10k note, đồng bộ hai máy/Android, và thao tác keyboard cho kết quả kém; hoặc source docs/chi phí đã đổi sau 20/11/2026. Đánh giá này độc lập, không mượn kết luận các luồng khác.

## 8. Kiểm chứng, trạng thái và nguồn

- **GitHub read:** đã đọc nhiệm vụ/protocol, trạng thái `main` và các file nguồn kể trên.
- **Official web evidence:** đã truy cập và đối chiếu thông tin version/plan/feature/security ngày 20/11/2026. Phân biệt **released / optional extension / paid / beta / chưa xác minh**.
- **Obsidian UI, cài đặt, extension/plugin, login, API thực, Sync trả phí, video/Drive test:** **NOT_RUN**.
- **Repo build/lint/unit/e2e trong G17:** **NOT_RUN**; G17 **chỉ thay đổi 1 file Markdown nghiên cứu**. Không suy các test từ `CURRENT_STATE.md` là do luồng này chạy.
- **Dữ liệu nhạy cảm / secret / media thật:** không sử dụng, không ghi vào báo cáo.
- **Điểm cần G00 kiểm tiếp:** xác minh giá/version lại khi tổng hợp; so tiêu chí K01/K03/K05/K12 giữa các báo cáo, không sửa kết luận của G17; chọn 1 PoC editor chỉ sau test.

### Tài liệu/nguồn tham khảo (đều truy cập 20/11/2026)

- **[O1]** Obsidian official changelog, Desktop/Mobile public 1.15.1 (12/11/2026): https://obsidian.md/changelog/
- **[O2]** Local data storage and vault: https://obsidian.md/help/data-storage
- **[O3]** Edit and Read (Live Preview / Source / Reading): https://obsidian.md/help/edit-and-read
- **[O4]** Backlinks / unlinked mentions (core): https://obsidian.md/help/plugins/backlinks
- **[O5]** Introduction to Bases (core views, local properties): https://obsidian.md/help/bases
- **[O6]** Canvas (core, JSON Canvas, text cards caveat): https://obsidian.md/help/plugins/canvas
- **[O7]** Obsidian Web Clipper official help (browser extension): https://obsidian.md/help/web-clipper
- **[O8]** Web Clipper GitHub repository (scope of open-source source, not app core): https://github.com/obsidianmd/obsidian-clipper
- **[O9]** Obsidian Sync features/platform/offline/pricing: https://obsidian.md/sync
- **[O10]** Obsidian Sync plan storage and per-file maximum: https://obsidian.md/help/sync/plans
- **[O11]** Obsidian Sync conflict resolution: https://obsidian.md/help/Obsidian%2BSync/Troubleshoot%2BObsidian%2BSync
- **[O12]** Obsidian backup guidance: https://obsidian.md/help/backup
- **[O13]** Obsidian CLI (requires running app): https://obsidian.md/help/cli
- **[O14]** Obsidian Headless Sync (**open beta**, paid Sync): https://obsidian.md/help/sync/headless
- **[O15]** Community plugin security and permissions: https://obsidian.md/help/Extending%2BObsidian/Plugin%2Bsecurity
- **[O16]** Official developer documentation and Plugin API: https://docs.obsidian.md/
- **[O17]** License overview (app free, app code protected): https://obsidian.md/license
- **[O18]** Obsidian Plugin API type definitions source (not REST backend): https://github.com/obsidianmd/obsidian-api
- **[O19]** Supported file formats and media embed: https://obsidian.md/help/file-formats
- **[O20]** Obsidian URI capture mechanisms: https://obsidian.md/help/uri

*Nguồn ngoài chủ yếu là tài liệu của nhà sản xuất, phù hợp xác minh khả năng công bố, **không** thay thế test độc lập về trải nghiệm, bảo mật hoặc năng lực 10k+ dữ liệu. Không có báo cáo hay xếp hạng Gxx khác được sử dụng.*
