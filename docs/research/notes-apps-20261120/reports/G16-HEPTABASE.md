# G16 — Đánh giá độc lập Heptabase cho Kho Tri Thức

- **Thời điểm đánh giá/truy cập nguồn:** 20/11/2026 (Asia/Ho_Chi_Minh).
- **Phạm vi:** chỉ Heptabase; không đọc báo cáo G01–G17 khác hoặc `G00-INITIAL-SOURCES.md`. Theo `G16-HEPTABASE.md` và `G00-PROTOCOL.md`.
- **Đối chứng:** `cavoixanh638/kho-tri-thuc`, nhánh `main` tại commit `c97f5678a6893d7dfec2595d89c9122f05195320`; đã đọc tài liệu hiện trạng **và mã thật** (xem mục 5).
- **Phương pháp:** đọc website/help center/changelog/roadmap/Terms/GitHub công khai, đọc code đối chứng. **Không có tài khoản Heptabase được cấp, không cài app, không nhập dữ liệu cá nhân, không gọi MCP/CLI, không thử sản phẩm trực tiếp. Tất cả ca UI, offline, tải file, sync, tốc độ, Unicode và kiểm thử 10.000 mục đều `NOT_RUN`.** Từ “NATIVE” dưới đây nghĩa là *được nhà cung cấp tài liệu hóa*, không phải PASS qua thử tay.
- **Kết luận:** **THAM KHẢO UX + PoC hẹp về trích dẫn quay lại đúng nguồn**, **không thay toàn bộ Kho Tri Thức** tại thời điểm này. Không yêu cầu dựng whiteboard.

## 1. Tóm tắt điều hành (dưới 200 từ)

Heptabase là sản phẩm ghi chú/nghiên cứu thương mại có thế mạnh ở **card nguồn → highlight gắn vị trí PDF, đoạn văn và mốc thời gian YouTube/phụ đề → sắp xếp ý trên whiteboard**, kết hợp backlinks, tag database, ứng dụng Android/Windows và MCP/CLI chính thức. Các khả năng này đã được mô tả trong tài liệu và nhiều mục phát hành năm 2026. Điểm đáng học nhất là **đường truy nguyên từ ghi chú/AI về đúng đoạn nguồn**, không phải giao diện whiteboard bằng mọi giá. Tuy nhiên chưa có bằng chứng Heptabase đáp ứng lịch sử `CaptureEvent` bất biến, phân biệt gửi link mới với retry, tự nhập và xử lý Facebook/TikTok đa nguồn, tự gán nhóm đang có không cần thao tác, hay dùng Google Drive hiện có làm kho media gốc. Heptabase chưa cung cấp REST API công khai bao phủ mọi thao tác; dữ liệu cloud/AI, phí thuê bao, khả năng xuất lại toàn bộ quan hệ và quy mô 10.000 video vẫn là rủi ro. **Khuyến nghị giữ kiến trúc hiện hành**, chỉ mượn UX/provenance qua các cải tiến tăng dần và phép thử đo được.

## 2. Tính năng, trạng thái phát hành, nền tảng và bằng chứng Heptabase

| Nhóm | Tình trạng tại 20/11/2026 | Bằng chứng và giới hạn |
| --- | --- | --- |
| PDF + source/highlight cards | **SHIPPED**. Kéo PDF vào thư viện/whiteboard; bôi chữ/vùng hình tạo highlight card, có liên kết về nơi trích. PDF parsing/OCR cũng đã phát hành, nhưng **parse không tự tạo highlight card**. | [S01], [S02], [S10] |
| Web article/YouTube | **SHIPPED**. Web Clipper lấy bài web/YouTube thành card; YouTube nhập caption **nếu nguồn có caption**, Insight gắn timestamp; webpage Insight quay về đoạn nội dung. **Không đồng nghĩa xử lý toàn bộ hình ảnh/âm thanh không phụ đề**. | [S01], [S02] |
| Podcast/audio | **SHIPPED**. Chọn podcast episode, AI transcript/insights; thời lượng/chi phí phụ thuộc gói. **Không suy rộng thành ASR tiếng Việt chính xác hoặc tự tải mọi audio/video URL**. | [S01], [S10] |
| Whiteboard / tổ chức | **SHIPPED**. Card xuất hiện trên nhiều board, sub-whiteboard, sections, connections/mind maps; bản 1.117.0–1.117.1 (06–10/11/2026) và 1.116.0 (03/11) cải thiện layout/MCP. | [S03], [S04], [S05] |
| Tag database / nested tags | **SHIPPED**. Tag với properties, table/kanban, filter, nested tags (13/01/2026), ngày tạo/cập nhật và nhiều view. Whiteboard là cấu trúc tri thức được nhà cung cấp ưu tiên; tag database phù hợp hồ sơ có trường dữ liệu. | [S02], [S03], [S04] |
| Backlinks / AI related | **SHIPPED**. Backlink tới block, tìm liên quan/gợi ý; agent có thể thao tác tổ chức qua yêu cầu. **Chưa thấy bằng chứng auto-assign vào nhóm có sẵn ngay sau mọi lần capture với ngưỡng confidence**. | [S02], [S03], [S08] |
| MCP / CLI | **SHIPPED**, không phải “planned”. MCP từ xa qua OAuth, search/read/write/cấp quyền; CLI 0.11.0 đi qua desktop, cần app chạy; plugin chính thức cho ChatGPT/Claude/Codex. Bản 03/11 thêm tạo media cards từ URL/tệp; 10/11 thêm citations tới đoạn văn chính xác. Một số thao tác MCP whiteboard cần app desktop/web mở. | [S02], [S06], [S07], [S08], [S09] |
| REST API / mã nguồn | **Không có REST API công khai đầy đủ**; giao diện tích hợp được hỗ trợ là MCP/CLI. Repo GitHub `heptameta/heptabase-cli-skills` là *hướng dẫn/skill cho CLI*, **không phải giấy phép mở mã nguồn ứng dụng**. Heptabase là dịch vụ/phần mềm thương mại độc quyền theo Terms. | [S06], [S18], [S19] |
| Nền tảng | **SHIPPED**: Windows, macOS, Linux, iOS/iPadOS, Android, web. 2026 có Quick Capture, Android PDF highlights, Share Sheet web content, xem backlinks, mobile AI. **Chưa thử trên máy thật**. | [S02], [S16], [S17] |
| Offline và đồng bộ | Desktop có database cục bộ để dùng offline; cloud sync mặc định ở nhiều cấu hình, có hướng dẫn xử lý `Unsynced Changes`. **Không có kết quả thử conflict Android↔Windows hay offline media dung lượng lớn**; nên phân biệt offline note và offline mọi attachment. | [S14], [S15], [S21] |
| Export / backup | **SHIPPED**: `Settings → Backup → Export now`, Markdown và `All-Data.json`; xuất thủ công có attachment, cần tự kiểm từng file. Auto cloud backup lưu vị trí/trạng thái/metadata **không có attachments**. Layout/quan hệ không chắc có thể nhập sang app khác nguyên vẹn. | [S12], [S13] |
| Giá (USD, nguồn ngày truy cập) | Pro **$11.99/tháng hoặc $107.88/năm**, Premium **$23.99/tháng hoặc $215.88/năm**, Premium+ **$71.99/tháng hoặc $647.88/năm**; Pro early-bird **$9.99/$83.88** chỉ cho người đủ điều kiện. Tương đương trả năm lần lượt **$8.99, $17.99, $53.99/tháng** (không phải giá trả tháng). AI credit **100/1.800/8.100 mỗi tháng**, không cộng dồn; tax/on-demand có thể cộng thêm. | [S10] |
| Upload/storage | Công bố **không giới hạn tổng lưu trữ** nhưng **mỗi file tối đa 2 GB**; PDF parse tối đa **350 MiB và 3.000 trang**. Không được suy “unlimited” nghĩa là hệ thống đã benchmark 10.000 video × hàng trăm GB; file có thể chiếm lưu trữ cục bộ desktop. | [S11], [S22] |
| Privacy & retention | Cloud AWS mã hóa TLS/at-rest AES-256, **không phải end-to-end encryption**; tìm kiếm/AI có xử lý nội dung trên server và bên thứ ba. Terms cập nhật **30/10/2026**; nội dung thuộc người dùng nhưng dịch vụ có quyền xử lý cần thiết. Lịch sử phiên bản được công bố **60 ngày**, ảnh snapshot trên 30 ngày có thể phải nhờ support để restore. | [S14], [S19], [S20] |
| Chưa phát hành | Theo roadmap **13/11/2026**: handwriting whiteboard/PDF/editor, inline tags, epub cards nằm ở **Working**; shape elements và nâng cấp voice note mobile nằm ở **internal testing, chưa shipped**. Không dùng làm tính năng hiện có. | [S03] |

**Cảnh báo phiên bản:** các mốc chức năng lấy từ changelog/roadmap đến **10–13/11/2026**, không lấy tên tính năng marketing làm bằng chứng vận hành. Chính sách, giá và quota có thể đổi sau ngày này. Điều kiện dùng MCP/CLI: thuê bao Pro/Premium/Premium+ hoặc trial đang hiệu lực; đọc-only cũng cần điều kiện ấy [S07], [S08].

## 3. Đánh giá chuyên sâu theo nhu cầu người dùng Việt Nam

### 3.1. Source cards và “highlight back to exact source”

- **PDF:** chọn chữ hoặc vùng trong trang → Highlight Card riêng → kéo vào whiteboard hay embed trong note → click về nội dung gốc. Trên mobile, hỗ trợ highlight/annotation đã phát hành năm 2026. Cơ chế này hữu ích hơn chỉ lưu `source_locator.page` vì tạo *đường điều hướng thật* từ trích dẫn về PDF [S01], [S02].
- **YouTube:** khi có captions mới nhập caption; Insights theo những đoạn chữ và link timestamp gốc. **Thiếu caption không có nghĩa Heptabase tự hiểu hình ảnh/âm thanh của video**. Trường hợp video upload và podcast có khả năng transcript, nhưng phải kiểm điều kiện, chi phí và độ chính xác riêng [S01], [S10].
- **Web:** web article thành card và Insight quay về đoạn văn; không mặc định page snapshot là toàn bộ bằng chứng bất biến nếu website đổi/chặn. Nên giữ URL, thời điểm và đoạn trích.
- **MCP/CLI (v1.117.1):** có thể tạo cards kèm citation link đến **đoạn văn xác định**; hỗ trợ truy vấn highlights và backlinks. Mức chi tiết của locator và khả năng export/import nguyên vẹn citation sang hệ khác vẫn **UNVERIFIED** [S02], [S08].
- Không nên nhầm **trích xuất một chuỗi phụ đề, một OCR paragraph** với việc hiểu *toàn bộ* video hoặc OCR đúng mọi bảng/biểu/ảnh.

### 3.2. Whiteboard, tags, quan hệ tri thức

- Whiteboard: kiến thức chuyên sâu theo chủ đề, bố trí không gian, liên kết ý, có sub-board/section. Một card có thể được dùng trên nhiều board; không được hiểu là nhân bản Item. Về UX, **backlink + related sources sát bài đọc** có thể đáng giá hơn một màn hình infinite canvas toàn thời gian.
- Tag Database có cột thuộc tính, lọc, table/kanban; nested tags là **SHIPPED**. Đây là cách phù hợp để hiển thị góc nhìn hồ sơ (“Nguồn”, “Chủ đề”, “Ngày lưu”, “Tình trạng trích xuất”) trên cùng dữ liệu. Chưa xác minh view timeline đáp ứng đầy đủ K08.
- Heptabase có AI Agent có thể sắp xếp khi người dùng giao việc, nhưng **không chứng minh** pipeline mặc định tự tìm *nhóm đã có* → gán thật theo confidence → giữ quyền ưu tiên phân loại tay như Kho Tri Thức. Vì vậy chỉ coi khả năng AI organization là tham khảo, không coi tương đương [S02], [S04].

### 3.3. Capture URL, lịch sử và metadata

- Web Clipper/Share Sheet/MCP/CLI giúp nạp URL, YouTube, trang web và media. **Không có nguồn chính thức xác nhận nạp/tải ổn định Facebook Reels, TikTok Shorts**, không có evidence dedupe bản gốc qua Drive, và **không có hợp đồng `CaptureEvent.server_received_at` bất biến** hoặc phân biệt “gửi lại ngày mai = event mới” với “HTTP retry cùng khóa = event cũ”.
- Tag Database có created/updated time, nhưng đó là **metadata card**, không được coi là event log bất biến từng lượt nhận; `published_at` của nguồn cũng phải phân biệt `saved_at` và `processed_at`.
- Đối với 10.000+ video, 2 GB/file và “no overall limit” là chính sách lưu trữ, **không chứng minh** hiệu năng import, indexing, playback, export hay chi phí ASR theo lô [S11].

### 3.4. Unicode, Android, Windows, AI

- Windows/Android chính thức được hỗ trợ; 2026 có cải tiến spell-check languages trên Windows, sửa thanh công cụ khi nhập Android, chia sẻ web từ mobile. Đây **không phải kiểm thử** gõ dấu tiếng Việt, IME, bảng Markdown, clipboard, mất mạng rồi xử lý conflict. Kịch bản thử ở mục 4/8 [S02], [S16].
- Desktop offline thông qua local DB; sync/cloud/AI qua server. Lỗi local sync và file lớn có thể làm nghẽn sync. Cần đo riêng **offline text**, **offline nguồn media**, **2 thiết bị cùng sửa** [S14], [S15].
- AI Agent/Tutor có khả năng search/triage/đặt card vào whiteboard và sửa note; tồn tại snapshot/diff cho một số tác vụ. Không có căn cứ rằng mọi AI edit đều giữ nguyên bản người dùng hoặc có provenance đầy đủ ngang mức Kho Tri Thức. **Không tự bật AI ghi đè note curated**; yêu cầu diff/chấp thuận + version [S02], [S14].
- Dữ liệu cloud được mã hóa khi truyền/lưu nhưng **không E2EE**; việc dùng API key riêng không biến Heptabase thành xử lý local-only. Với tài liệu nhạy cảm, trước PoC phải duyệt quy tắc dữ liệu và chỉ dùng fixture công khai/giả [S14], [S19].

## 4. K01–K12 — ma trận năng lực và phép thử tái lập

**Quy ước:** `NATIVE` = có chức năng nhà cung cấp tự triển khai ở phạm vi đã ghi; `EXTENSION` = qua extension/plugin; `CUSTOM_BACKEND` = phải tự viết nghiệp vụ riêng; `NOT_SUPPORTED` = có bằng chứng phủ định; `UNVERIFIED` = không đủ bằng chứng cho toàn bộ yêu cầu. **Không có kết quả thử tay: tất cả 12 ca đều `NOT_RUN`.** Trạng thái là phân loại dựa tài liệu, không phải verdict PASS.

| Ca | Phân loại | Chứng cứ/phạm vi | Cách thử lại bằng dữ liệu giả và điều chưa chắc |
| --- | --- | --- | --- |
| **K01** Gõ note tiếng Việt, receipt + giờ | **UNVERIFIED** (quick capture **NATIVE**) | Inbox/Journal/Quick Capture có sẵn; tag created time [S02], [S05]. **Chưa thấy receipt giờ server bất biến.** | Android/Windows gõ “Đường Nguyễn Văn Linh, Hải Phòng – bảng 1/2”; gửi, ghi giờ thiết bị/server và biên nhận; so sánh sau reload, offline/sync. **NOT_RUN**. |
| **K02** Gửi URL + metadata và text | **NATIVE** trong **web/YouTube có caption**; FB/TikTok **UNVERIFIED** | Web Clipper, YouTube card/captions, CLI/MCP nhập nguồn [S01], [S02], [S08]. | Gửi 1 web article, 1 YouTube có/không caption, 1 FB Reel, 1 TikTok; so title/author/published_at/transcript/hash file. URL hỏng vẫn cần item. **NOT_RUN**. |
| **K03** Link lặp ngày khác vs HTTP retry | **UNVERIFIED** | Không thấy API hợp đồng per-capture receipt/idempotency; MCP/CLI là công cụ tích hợp, không chứng minh semantics [S06], [S08]. | Gửi cùng URL ngày D1/D2; retry cùng request-key; đếm event và file. Kỳ vọng 2 event/1 asset và retry không thêm event. **NOT_RUN**. |
| **K04** Markdown, bảng, Unicode | **NATIVE** cho soạn thảo + export Markdown | Editor bảng/links, copy/export MD, import Obsidian/Markdown [S02], [S12]. | Tạo bảng, URL, tiêu đề, NFC/NFD, emoji, dấu; export→import→hash/visual diff; kiểm link/assets. Round-trip chính xác **UNVERIFIED/NOT_RUN**. |
| **K05** Tự gán vào nhóm đã có | **UNVERIFIED** (AI-assisted organization **NATIVE**) | AI Agent chỉnh tags/boards theo lệnh, không có chứng cứ **auto-assign after capture** theo confidence [S02], [S04]. | Chuẩn bị 3 nhóm; gửi 30 mẫu, không prompt gán; đo ≥90% precision auto-assignment và không thay curated. **NOT_RUN**. |
| **K06** Related/backlinks cạnh bài | **NATIVE** | Backlinks, AI suggested related cards, board connections, block references [S02], [S04], [S08]. | Tạo 2 card liên quan + 1 không liên quan; kiểm link 2 chiều, lý do, khi xóa/relink, UI đọc. **NOT_RUN**. |
| **K07** PDF/audio/video định vị | **NATIVE** trong **PDF + captioned YouTube/podcast**; file MP4 tự upload tùy trường hợp **UNVERIFIED** | PDF highlight theo vùng; YouTube Insights tới timestamp; podcast transcript; MCP citations đoạn nguồn [S01], [S02]. | PDF 10 trang có bảng/ảnh, clip 90s có subtitle; click citation→đúng trang/đoạn, sai số seek ≤2s; kiểm MP4 không transcript. **NOT_RUN**. |
| **K08** Đa nhóm, tree/table/card/timeline | **NATIVE** với sub-board/tag/table/kanban/card; timeline **UNVERIFIED** | Nested tags, subboards, tag database created/updated dates, nhiều view [S02], [S03], [S04]. | Một card trong ≥2 board/tag; lọc table + card + date; kiểm số Item không tăng. Tree/timeline tương đương mức nào **NOT_RUN**. |
| **K09** Android + Windows, offline/conflict | **NATIVE** cho app 2 nền tảng + offline desktop; conflict toàn diện **UNVERIFIED** | Trang download, local DB, sync troubleshooting [S14], [S15], [S16]. | Android mất mạng tạo/sửa note; Windows sửa cùng note; bật mạng, xác minh xung đột không mất bản; kiểm 1 video lớn. **NOT_RUN**. |
| **K10** API, Markdown/assets, backup/exit | **NATIVE** với export Markdown/JSON/assets & MCP/CLI; **NOT_SUPPORTED** nếu đòi REST tổng quát | Export và CLI/MCP chính thức, **không public full REST** [S06], [S08], [S12], [S13]. | Xuất 50 notes + 10 assets + 3 board; chuyển sang app khác, đối chiếu hash, link, tags, arrows, restore. Bản portable đủ quan hệ **NOT_RUN**. |
| **K11** AI có source + không ghi đè | **NATIVE** cho AI search/insight/agent; **UNVERIFIED** về toàn bộ provenance và bảo vệ note | AI model/credits, citation về đoạn, AI edit hỗ trợ preview ở một số luồng [S02], [S10], [S14]. | Đặt 5 câu hỏi bẫy không đủ nguồn; đối chiếu citation, preview diff, quyền sửa, chi phí 50 lần hỏi. **NOT_RUN**. |
| **K12** >10.000 mục + hàng trăm GB remote Drive | **UNVERIFIED** | Heptabase công bố unlimited tổng dung lượng, 2 GB/file; local storage cần cân nhắc; không có evidence Drive làm source-of-truth bên ngoài [S11], [S22]. | 10.000 item + 300 GB media *giả/đã được phép*, benchmark import/search/play/export/restore, đo local disk/network/chi phí. Không được dùng dữ liệu thật để thử không phép. **NOT_RUN**. |

**Diễn giải không được nhầm:** K01/K03/K05/K12 chưa đạt bằng chứng của cả ca, dù sản phẩm có vài chức năng liên quan. K07 và K10 chỉ **NATIVE theo phạm vi con có chứng cứ**, không cam kết video bất kỳ hay full REST API. Các ca chưa được dùng để tuyên bố Heptabase PASS khi thay hệ thống.

## 5. Đối chiếu **mã main hiện tại** của Kho Tri Thức

Đã đọc trực tiếp mã tại SHA nêu đầu báo cáo, ngoài `README.md`, `docs/CURRENT_STATE.md`, `docs/CAPTURE_AND_ORGANIZE.md`, `docs/ARCHITECTURE_AND_DATA.md` và `docs/operations/TEXT_KNOWLEDGE.md`. Kết luận dưới đây là **code inspection**, không phải tự chạy server hoặc CI; các `LIVE_PASS` trích từ `CURRENT_STATE.md` là **checkpoint của dự án**, không phải kết quả G16 đã chạy lại.

| Nhu cầu | Trạng thái trong mã Kho Tri Thức | Heptabase giúp gì? | Quyết định |
| --- | --- | --- | --- |
| Receipt, giờ nhận, retry, URL trùng | **ĐÃ CÓ trong mã:** `CaptureEvent.server_received_at`, `idempotency_key`, `Source.identity_hash/canonical_url`; `submit_capture` giao dịch atomic, retry trả event cũ, link lặp tạo event mới nhưng tái dùng Item. [Mã ingestion][KTC1], [CaptureService][KTC2]. | Chưa có evidence equivalent. | **Giữ nguyên**; không thay bằng created_at của card. |
| Văn bản/Markdown nguyên gốc | **ĐÃ CÓ:** `Item.note` UTF-8, `KnowledgeText.tsx` với `react-markdown`/`remark-gfm`, bỏ HTML nguy hiểm; `ReadKnowledgeService` ưu tiên note biên soạn. [KTC3], [KTC4], [KTC5]. | Tham khảo thao tác editor/inbox, không đổi storage format. | **CẢI THIỆN UX** khi cần. |
| Cây thư viện, nhiều nhóm, related | **ĐÃ CÓ:** `Topic.parent`, `ItemTopic/Project/Tag` many-to-many, `RelatedItem` có reason/confidence/status và `OrganizationService` gán group/related; UI cây thư viện [KTC3], [KTC6], [KTC7]. | Backlink/context panel, tag database view và UX đặt related cạnh nội dung. | **CẢI THIỆN**; không xây graph DB. |
| Nguồn/metadata/trích xuất | **ĐÃ CÓ nền tảng:** `Source` metadata+published_at, `DerivedContent` text, `source_locator` JSON, processor/version/input_hash/status; `ReadKnowledgeService` trả parts/locator [KTC3], [KTC8], [KTC5]. | **Còn thiếu UX click exact locator**; Heptabase đưa mô hình PDF/YouTube source-highlight đáng học. | **ƯU TIÊN PoC hẹp**. |
| Jump exact page/timestamp | **CHƯA CÓ đầy đủ trong UI main:** `KnowledgeReading.tsx` hiện *hiển thị* `Trang N`/section và nút “Xem minh họa từ nguồn”, **không gọi seek đến đúng trang/timestamp** [KTC9]. Có thể đã có transcript source locator nhưng thiếu contract UI↔viewer. | UX bấm citation → nguồn đúng vị trí. | **CẢI THIỆN trước whiteboard**. |
| Video + ASR | **PARTIAL:** có modules `video_download.py`, `transcribe.py`, `transcript_job.py`; `CURRENT_STATE` báo đã thử một Reel và ASR offline, nhưng Android/đa nguồn/seek chưa nghiệm thu. [KTC10], [KTC11], [KTCS]. | Insight cho video có caption, podcast ASR; **không thay downloader/Drive**. | **GIỮ**, thêm provenance. |
| Drive và bản backup | **ĐÃ CÓ kiến trúc/thực thi:** `Asset/StorageLocation` tách, worker, backup/restore theo `CURRENT_STATE`, Google Drive chính; Heptabase là SaaS khác, không chứng minh lưu media trên Drive người dùng. [KTCS], [KTCA]. | Export UX/kiểm attachments làm checklist. | **KHÔNG PHÙ HỢP để thay**. |
| API / tích hợp AI | **ĐÃ CÓ:** API Django Ninja, KnowledgeExport lên Drive và pilot ChatGPT connector ghi trong `CURRENT_STATE`; MCP riêng mới là tùy nhu cầu. [KTC5], [KTCS]. | MCP/CLI Heptabase chứng minh UX tích hợp trực tiếp khả thi, **nhưng tích hợp vào Heptabase ≠ plugin truy vấn PostgreSQL Kho Tri Thức**. | **THAM KHẢO**, không bê nguyên. |
| Android và offline | **Chưa nghiệm thu:** Kho Tri Thức PWA được thiết kế Android/Windows, tài liệu báo Windows PASS/Android NOT_RUN. Heptabase có app native Android/Windows; offline/collision chưa G16 thử. [KTCS], [S16]. | Benchmark sau khi có nhu cầu app native thật. | **CHƯA KẾT LUẬN**. |

**Không có lý do kỹ thuật từ nghiên cứu này để viết lại Django 5.2/PostgreSQL/Google Drive hoặc thêm Redis, vector DB, canvas library ngay.** Source locator/related/group hiện hữu có thể làm tốt hơn bằng API và component mới, không phá `CaptureEvent`/`Item`/`Asset`.

## 6. Rubric 7 trụ — điểm minh bạch, không đánh đồng “có tài liệu” và “đã test”

Điểm là **ước lượng chuyên gia dựa trên nguồn chính thức**, không phải kết quả benchmark; mỗi trụ có khoảng bất định, phần **UNVERIFIED không tự chấm 0**.

| Trụ | Điểm/ tối đa | Lý do | Độ tin cậy |
| --- | ---: | --- | --- |
| Capture + ingestion | **12/20** (10–15) | Nhiều lối web/YouTube/PDF/podcast, MCP/CLI; FB/TikTok, capture event, retry, pipeline số lượng lớn chưa xác minh. | **Trung bình** |
| Organization + recall | **16/20** (14–18) | Card/board/nested tags/tag database/backlinks/AI related mạnh; auto-assign nhóm có sẵn ngay sau capture chưa chứng minh. | **Trung bình** |
| Text editor + reading | **13/15** (11–14) | Editor, Markdown export, PDF highlights, đọc đa nguồn tốt; roundtrip Unicode/tables/assets chưa thử. | **Trung bình** |
| Provenance + relationships + time | **12/15** (10–14) | Highlight quay về PDF/đoạn web/YouTube timestamp, citations v1.117.1; event history/MP4 timestamp chưa xác minh. | **Trung bình** |
| Android/Windows/offline | **7/10** (5–9) | Có app cả hai, desktop local DB, nhưng offline Android/media và conflict chưa đo. | **Thấp–trung bình** |
| Portability + backup | **6/10** (4–8) | Markdown/All-Data.json/asset export; quan hệ/whiteboard roundtrip ngoài Heptabase và auto cloud backup attachments hạn chế. | **Trung bình** |
| Integration + cost + maintainability | **5/10** (3–7) | MCP/CLI hữu dụng, nhưng trả thuê bao/AI credits, SaaS riêng, không full REST, không khớp backend Drive hiện hành. | **Trung bình** |
| **Tổng** | **71/100** (khoảng nhận định **57–85**, không phải CI confidence interval) | Tổng = **12+16+13+12+7+6+5 = 71**. Nếu thiếu bằng chứng được kiểm thử, điểm chỉ mang tính định hướng. | **Trung bình–thấp** |

**Tách 2 trục quyết định:**
1. **Thay toàn hệ thống Kho Tri Thức:** **thấp, ~3/10**. Heptabase mạnh nghiên cứu tài liệu, nhưng chuyển dữ liệu sẽ mất hợp đồng capture/retry/Drive và cần chứng minh scale/portability; không có lý do thay kiến trúc đã chạy.
2. **Giá trị học hỏi/tái sử dụng *ý tưởng*:** **cao, ~8/10**. Điểm cao nhất ở source highlights, panel backlinks, multi-view tags và cách dùng AI có citation. Đây **không phải** yêu cầu sao chép mã/license Heptabase.

## 7. 5 cải tiến đề xuất cho Kho Tri Thức (ưu tiên, thiết kế, acceptance test)

**Nguyên tắc chung:** mỗi tính năng dùng `item_id`/`asset_id`/`source_id` hiện có, không tự di chuyển media gốc khỏi Drive, không viết lại schema event, không tự AI ghi đè `Item.note`. Mức độ: **S** = chỉnh UI/API nhỏ, **M** = UI+backend/test phối hợp, **L** = thiết kế thành phần mới đáng kể.

### H16-01 — Citation / Highlight → đúng PDF page hoặc video time (**M**, ưu tiên 1; PoC)

- **UX:** trong phần “Tri thức trích từ nguồn”, mỗi đoạn có nút “Đến nguồn” chỉ hiện khi locator đủ tin cậy. Click với PDF mở viewer ở `page`/vùng bôi; với transcript mở video đúng `start_ms`; hiển thị nhãn nguồn, processor/version, cảnh báo transcript máy chưa kiểm chứng. Locator lỗi → fallback “Mở nguồn”, không dẫn sai.
- **Technical:** chuẩn hóa **adapter trong** cho `DerivedContent.source_locator`, ví dụ `{kind: "pdf", page: 3, rect: ...}` hoặc `{kind: "video", start_ms: 42000, end_ms: 48500}`; validate bounds/page count/duration, version hóa conversion; không nhúng URL ký Drive tồn tại ngắn lâu vào note; giữ link Item/Asset và provenance.
- **Acceptance:** trên bộ *fixture không nhạy cảm* ≥20 passage thuộc ≥5 PDF và ≥20 transcript segments: click → đúng trang **100%**, video sai số ≤**2 giây** cho ≥**95%** vị trí được kiểm (không có kết quả test thì FAIL/NOT_RUN), 0 locator ngoài giới hạn, fallback rõ ràng; bảo toàn nguyên Markdown gốc và bất biến event. Có test case PDF scan/chưa extract và video không transcript.
- **Rủi ro/phụ thuộc:** parser có locator kém, player Drive không hỗ trợ seek ngay; có thể cần proxy/range hoặc fallback, đo trước; tuyệt đối không gắn timestamp suy đoán từ văn bản tóm tắt.

### H16-02 — “Nguồn liên quan”/backlinks ngay cạnh bài (**S–M**, ưu tiên 2)

- **UX:** panel bên cạnh/trên bài: “Được liên kết từ”, “Liên quan vì…”, phân biệt auto vs người dùng; click 1 lần tới bài và quay lại; cho ẩn/dismiss suggestion, không ngầm gộp bài.
- **Technical:** dùng `RelatedItem` hiện hữu với `reason/confidence/status`; đọc ngược theo cả `item_a/item_b`; lọc stale/dismissed; API owner scoped, phân trang/lazy render; thêm authored link nếu thực tế cần, không tạo graph DB.
- **Acceptance:** ≥6 fixtures (2 linked, 2 similar, 2 unrelated), không lộ item khác owner; dismiss không tự hồi sinh trong cùng version; 0 bản sao Item; mở/tắt sidebar không thay note; có test với 500 quan hệ.

### H16-03 — Tag/table view nhẹ cho hồ sơ (không thay tree) (**M**, ưu tiên 3)

- **UX:** từ cùng Item, đổi “Cây” ↔ “Bảng”; cột `ngày lưu/nguồn/chủ đề/trạng thái text/nhãn`, filter nhiều tag và sort; một bài vẫn thuộc nhiều nhánh, **không nhân Item**.
- **Technical:** dùng `ItemTopic/ItemTag/ItemProject` + existing SearchService, server pagination/filter; group là quan hệ, date là thuộc tính, không viết hệ database table mới như SaaS.
- **Acceptance:** fixture 10.000 Item phân nhiều nhóm; 1 bản ghi Item duy nhất trong kết quả; lọc kết hợp/diacritics chính xác; P95 API tìm/lọc <**1 s** trên máy benchmark được mô tả; 0 thay đổi `CaptureEvent`; test keyboard/Android layout.

### H16-04 — Inbox triage sau receipt (**S–M**, ưu tiên 4, không trì hoãn lưu)

- **UX:** mọi URL/note gửi vào nhận ACK ngay; nếu chưa nhóm tự động, vào “Chưa phân loại/Cần duyệt” với hành động gán nhóm đã có, mở nguồn, giữ lại; Quick Capture đa nền tảng có thông báo phân biệt “đã nhận” và “đã trích xong”.
- **Technical:** chỉ dùng `CaptureEvent` + trạng thái `Item.classification_status/source_fetch/content_extract`, không phát minh queue song song; retry request-key giữ nguyên; link gửi lại ngày khác có event riêng.
- **Acceptance:** test 2 gửi cùng URL/2 key → **2 events, 1 item**; 3 retry cùng key → **không event mới**; mất mạng sau ACK/worker restart không mất record; UI phát trạng thái thực, không báo xong khi job pending. Trên Android Share Target thực đánh **NOT_RUN** cho đến khi kiểm.

### H16-05 — AI insights có citations, diff và quyền duyệt (**M**, ưu tiên 5; chỉ khi có provider)

- **UX:** insight trên đoạn nguồn có thẻ trích dẫn, confidence/nguồn; nút “Thêm vào bản nháp” và “Duyệt thay đổi”, **không sửa note authored âm thầm**. Nếu thiếu transcript, nói rõ “chưa có dữ liệu lời nói”, không tạo tóm tắt video bằng suy đoán.
- **Technical:** giữ `DerivedContent` phiên bản, `source_locator` và hash/provenance của prompt/nguồn; AI output nằm bản đề xuất riêng, có diff và audit trước promote sang note. Chỉ mở API/provider sau khi đo chi phí; không thêm vector index theo mặc định.
- **Acceptance:** 30 prompt gồm 10 câu không đủ nguồn; hệ thống phải từ chối hoặc gắn nhãn không chắc cho **10/10**, 0 chỉnh sửa note khi chưa approve, citations có `source_id/locator`; có ledger token/cost theo item, thử mất kết nối và rollback.

**Không đề xuất làm bây giờ:** infinite whiteboard/canvas, graph DB, tái tạo Heptabase editor, bê CLI nội bộ Heptabase, hoặc đồng bộ hai chiều toàn bộ Heptabase ↔ Drive. Chỉ cân nhắc whiteboard **L** khi người dùng chứng minh một workflow không đáp ứng được bằng tree/table/backlinks, có ≥3 ca dùng thực tế và tiêu chí đo hiệu quả. Điều này tránh chi phí UI/đồng bộ không cần thiết.

## 8. Giả thuyết phản chứng, rủi ro và điều kiện đảo chiều

**Giả thuyết có thể bác bỏ kết luận “chỉ học UX”:**
- Nếu PoC Heptabase với dữ liệu giả chứng minh **K01/K03/K05/K12** đầy đủ (receipt immutable, retry/new event, auto-group đúng ngưỡng, 10.000+ mục), xuất toàn bộ relations/assets *sang định dạng độc lập* không mất dữ liệu, và tổng chi phí vòng đời ≤ giải pháp hiện hành, cần **đánh giá lại khả năng thay thế**.
- Ngược lại, nếu PoC H16-01 cho thấy reader và viewer Drive hiện hành không thể seek với tỷ lệ pass tối thiểu sau 2 vòng thử, không nên ép xây một abstraction locator quá phức tạp; cân nhắc nút “Mở nguồn” và giữ timestamp dạng text đến khi có player phù hợp.
- Nếu sử dụng thực tế cho thấy >80% tri thức được thao tác qua cây/tìm kiếm và rất hiếm cần nhóm ý trực quan, càng không có lý do dựng whiteboard.

**Rủi ro tối thiểu cần quản trị:**
1. **Lock-in và phí:** SaaS trả theo tháng/năm, AI credits không cộng dồn, on-demand phát sinh. Thử xuất trước khi trả tiền dài hạn [S10], [S12].
2. **Không portable toàn phần:** Markdown có thể rời nền tảng nhưng layout, links và semantic metadata khi sang app khác không đảm bảo; auto-cloud backup **không có attachment** [S12], [S13].
3. **Privacy/cloud:** không E2EE; dữ liệu có thể qua AI provider, search index; không đưa hồ sơ riêng tư/công vụ vào PoC chưa duyệt [S14], [S19].
4. **Ingestion không tương đương:** YouTube có caption ≠ mọi FB/TikTok tải được; capture time của note ≠ lịch sử tiếp nhận per-event [S01], [S06].
5. **10.000 file ≠ 10.000 video:** unlimited công bố không chứng minh khả năng index/seek/export trên 300 GB; file >2 GB có thể bị chặn; local storage tăng [S11], [S22].
6. **Sync/offline:** local thay đổi chưa đồng bộ có thể mất khi reset; cần kiểm cross-device và bản sao trước khi thao tác [S15].
7. **Licensing:** Terms cấp quyền sử dụng dịch vụ, không cho sao chép mã nguồn/đồ họa; repo skills public không phải phần core; chỉ áp dụng **mô hình tương tác/ý tưởng**, tự viết mã và rà license bên thứ ba [S18], [S19].

**Điều kiện đảo chiều sang “Thử dùng Heptabase làm công cụ bổ trợ”:** có nhu cầu nghiên cứu PDF học thuật nhiều, người dùng chấp thuận phí và privacy, xuất-backup 10/10 assets PASS, và có thể **dùng ngoài Kho Tri Thức, không nhập toàn bộ dữ liệu gốc**. Không dùng Heptabase như hệ thống thay Drive/Postgres trước khi các test K01/K03/K05/K10/K12 đạt bằng chứng.

## 9. Checklist tái lập, kiểm chứng và giới hạn nghiệm thu G16

1. **Không đụng tài khoản thật:** dùng trial nếu chủ tài khoản đồng ý; 10 note tiếng Việt giả, 3 web public, 2 YouTube (có/không captions), 2 PDF public, 1 audio tự tạo, 1 MP4 tự tạo; tránh tài liệu riêng tư. Ghi bản/OS/plan và thông số mạng.
2. **Chụp evidence cho từng K:** ngày, thao tác, screenshot/video ngắn *không chứa bí mật*, export zip, kết quả hash/locator, chi phí, sync log, verdict PASS/FAIL/NOT_RUN riêng. Đừng biến SHIPPED theo changelog thành PASS.
3. **Bảo toàn:** trước khi reset/test đồng bộ, export toàn bộ, xác nhận assets thực sự mở được; bản auto-cloud backup không chứa attachments.
4. **Tính điểm lại** chỉ khi có test; mỗi phép thử có tiêu chí ở K01–K12 và H16-xx, lỗi/phiên bản được lưu.
5. **G16 hiện tại:** web/docs **REVIEWED**, GitHub Kho Tri Thức code **INSPECTED**, Heptabase hands-on **NOT_RUN**, Windows/Android live **NOT_RUN**, private media **NOT_RUN**, load 10.000 **NOT_RUN**. Đây là **báo cáo nghiên cứu**, không sửa code, không cài plugin/skill ngoài, không có kiểm thử CI sản phẩm được khởi chạy ở luồng này.

## 10. Nguồn tham chiếu (truy cập 20/11/2026)

Tất cả nguồn S01–S22 được mở/đối chiếu ngày **20/11/2026**; khi trang help ghi “Updated over a week ago”, đó không phải ngày chính xác. Những trang release/roadmap có ngày phát hành nêu riêng. Các tài liệu chính thức ưu tiên hơn marketing. Không tham khảo báo cáo các luồng khác.

- **[S01]** Heptabase Public Wiki, *Read PDFs, media, eBooks & webpages* — PDF highlights, YouTube caption + timestamps, podcast transcript.
- **[S02]** Heptabase Public Wiki, *Changelog*, phiên bản 2026 đến **10/11/2026** (desktop 1.117.1, mobile 1.41.9; plugin 0.2.0).
- **[S03]** Heptabase Public Wiki, *Public Roadmap*, cập nhật **13/11/2026**; phân biệt Shipped/Working/Internal testing.
- **[S04]** Heptabase Public Wiki, *Organize knowledge & projects*, board hierarchy, tags/table.
- **[S05]** Heptabase Public Wiki, *User Interface Logic*, Inbox/Journal/Card Library/Tag Database.
- **[S06]** Help Center, *Does Heptabase provide a public API?*, không có full public REST.
- **[S07]** Help Center, *Heptabase MCP*, OAuth/remote server và điều kiện plan.
- **[S08]** Help Center, *Heptabase MCP and CLI: what's the difference?*, bảng khả năng và điều kiện mở app.
- **[S09]** Help Center, *Heptabase CLI*, bản 0.11.0 với desktop v1.117.1.
- **[S10]** Help Center, *Plans and pricing*, gói, credit/AI, PDF parsing và trial.
- **[S11]** Help Center, *What's the size limit for uploading files?*, 2 GB/file, PDF 350 MiB/3.000 trang.
- **[S12]** Help Center, *Business sustainability and data portability*, Markdown/All-Data.json.
- **[S13]** Help Center, *How does auto-backup work in Heptabase?*, cloud auto backup không attachment, manual export có tệp.
- **[S14]** Help Center, *Is my data safe in Heptabase?*, AWS/không E2EE/AI/search.
- **[S15]** Help Center, *Troubleshoot unsynced desktop changes*, rủi ro local/sync.
- **[S16]** Heptabase official *Download*, Windows/Android/macOS/Linux/iOS.
- **[S17]** Help Center, *Download the Android APK safely*, kênh Google Play/APK qua support.
- **[S18]** GitHub `heptameta/heptabase-cli-skills`, skills CLI công khai; **không đại diện source code app**.
- **[S19]** Heptabase *Terms of Service*, **30/10/2026**, quyền nội dung/license/API/AI.
- **[S20]** Help Center, *Restore from version history*, 60 ngày, hạn chế restore snapshot cũ.
- **[S21]** Help Center, *Move to a new device*, sync cloud và không hỗ trợ chuyển giữa tài khoản.
- **[S22]** Help Center, *What does "Your local storage is almost full" mean?*, cache/`hepta-files` và disk.
- **[KTCS]** Repo Kho Tri Thức: `docs/CURRENT_STATE.md` tại commit baseline; các tuyên bố live có nguồn test dự án nhưng **không chạy lại ở G16**.
- **[KTCA]** Repo Kho Tri Thức: `docs/ARCHITECTURE_AND_DATA.md` tại commit baseline, quyết định Drive/Postgres.

[S01]: https://wiki.heptabase.com/pdf-annotation
[S02]: https://wiki.heptabase.com/changelog
[S03]: https://wiki.heptabase.com/roadmap
[S04]: https://wiki.heptabase.com/organize-knowledge-and-projects
[S05]: https://wiki.heptabase.com/user-interface-logic
[S06]: https://support.heptabase.com/en/articles/10447604-does-heptabase-provide-a-public-api
[S07]: https://support.heptabase.com/en/articles/12679581-heptabase-mcp
[S08]: https://support.heptabase.com/en/articles/18302976-heptabase-mcp-and-cli-what-s-the-difference
[S09]: https://support.heptabase.com/en/articles/14715462-heptabase-cli
[S10]: https://support.heptabase.com/en/articles/12990121-plans-and-pricing
[S11]: https://support.heptabase.com/en/articles/10447030-what-s-the-size-limit-for-uploading-files
[S12]: https://support.heptabase.com/en/articles/10364279-business-sustainability-and-data-portability
[S13]: https://support.heptabase.com/en/articles/11064116-how-does-auto-backup-work-in-heptabase
[S14]: https://support.heptabase.com/en/articles/10448141-is-my-data-safe-in-heptabase
[S15]: https://support.heptabase.com/en/articles/10575619-troubleshoot-unsynced-desktop-changes
[S16]: https://heptabase.com/download
[S17]: https://support.heptabase.com/en/articles/15410871-download-the-android-apk-safely
[S18]: https://github.com/heptameta/heptabase-cli-skills
[S19]: https://heptabase.com/terms_of_service
[S20]: https://support.heptabase.com/en/articles/10448124-restore-from-version-history
[S21]: https://support.heptabase.com/en/articles/11401554-move-to-a-new-device
[S22]: https://support.heptabase.com/en/articles/10410165-what-does-your-local-storage-is-almost-full-mean
[KTCS]: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/docs/CURRENT_STATE.md
[KTCA]: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/docs/ARCHITECTURE_AND_DATA.md
[KTC1]: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/ingestion/models.py
[KTC2]: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/ingestion/services.py
[KTC3]: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/models.py
[KTC4]: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/KnowledgeText.tsx
[KTC5]: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/read_knowledge.py
[KTC6]: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/organization.py
[KTC7]: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/KnowledgeTree.tsx
[KTC8]: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/models.py
[KTC9]: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/KnowledgeReading.tsx
[KTC10]: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/video_download.py
[KTC11]: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/transcribe.py
