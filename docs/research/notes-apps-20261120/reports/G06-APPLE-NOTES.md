# G06 — Nghiên cứu độc lập Apple Notes cho Kho Tri Thức

**Ngày đánh giá:** 20/11/2026 (ICT, UTC+07). **Nguồn ứng dụng:** Apple Notes. **Baseline Kho Tri Thức:** `main` tại `c97f5678a6893d7dfec2595d89c9122f05195320`, đọc trực tiếp mã và hiện trạng ngày 20/11/2026. **Nhánh nghiên cứu:** `research/notes-20261120-g06`. **Đối tượng nghiệm thu:** nghiên cứu tài liệu, không sửa ứng dụng, không thử tài khoản người dùng. **Không đọc** G00-INITIAL-SOURCES hoặc báo cáo của các luồng khác.

**Phương pháp và mức chứng cứ:** `DOCS_VERIFIED` = đối chiếu hướng dẫn/Apple Developer chính thức; `CODE_INSPECTED` = đọc trực tiếp mã trên GitHub; `REPORTED_LIVE` = chỉ dẫn tới log/checkpoint vận hành đã có, không phải G06 tự tái chạy; `NOT_RUN` = chưa thử trên Apple ID, iPhone/iPad/Mac, Windows/Android hay tập >10.000 mục. Nguồn web truy cập ngày 20/11/2026; trang guide thường **không ghi ngày xuất bản**, nên dùng đường dẫn gắn phiên bản iOS 27/macOS 27 và không tự suy ngày phát hành. Nhiệm vụ trỏ iOS 26 làm điểm xuất phát; tại lúc khảo sát Apple đã có guide iOS 27/macOS 27 [A01, A11]. Không khẳng định beta/planned nếu không có bằng chứng.

## 1. Tóm tắt điều hành (dưới 200 từ)

**Đề xuất: THAM KHẢO UX; không thay toàn bộ Kho Tri Thức bằng Apple Notes.** Apple Notes mạnh về ghi nhanh từ Share Sheet/Quick Notes, ghi chú giàu định dạng, scan tài liệu, tìm trong ảnh/PDF, tag/Smart Folder, liên kết ghi chú/đề mục, ghi âm và chạm transcript để phát lại; bản mới hỗ trợ trao đổi Markdown [A02–A12]. Đây là nguồn thiết kế tương tác rất đáng mượn. Tuy nhiên, Notes không có API CRUD công khai theo xác nhận của kỹ sư Apple [A15], không chứng minh được hợp đồng receipt/CaptureEvent/idempotency, tự nạp metadata và nội dung video theo nguồn, tự gán nhóm hiện có, provenance của trích xuất, backup/restore manifest hay quy mô media trên Google Drive. Đa nền tảng Android/Windows và thử OCR/ASR tiếng Việt phải được phân biệt theo tính năng, không đánh đồng. Kho Tri Thức hiện đã có ứng dụng chạy Windows, PostgreSQL, Markdown, ID/event, pipeline nguồn/ASR có điều kiện và backup thực [R01–R12]. **Không đề xuất nhập dữ liệu cá nhân vào Apple Notes, migrate Drive/PostgreSQL hay cài bridge bên thứ ba.**

## 2. Bằng chứng sản phẩm: điều gì đã có và điều gì chưa được chứng minh

| Chủ đề | Đã được Apple mô tả chính thức | Phạm vi, giới hạn và bằng chứng |
| --- | --- | --- |
| Quick Notes / share capture | Ghi qua nút Quick Note/Share, đính URL, ảnh, tag; từ Safari có thể quay lại đoạn đánh dấu [A03]. | Hành vi trên thiết bị Apple; đây là lưu note/link, **không** là cam kết tải video, trích audio hay lưu receipt server. |
| Soạn và đọc | Heading, checklists, bảng, divider, section có thể thu gọn trên iOS 27 [A02]; liên kết tới note và section, gõ `>>` [A08, A25]. | Rich text không đồng nghĩa lưu mọi cú pháp Markdown dạng nguyên văn; import Markdown được đổi thành rich text [A12]. Không có chứng cứ backlink tự động hai chiều hoặc graph. |
| Scan / OCR / tìm | Camera Scan Text, Scan Documents (PDF trong note), tìm text gõ/viết tay, ảnh và scanned documents, tìm cả attachment [A04, A05]. | Apple liệt kê **Live Text tiếng Việt** trong iOS 27 [A19]; chưa tự thử độ chính xác scan tài liệu hành chính tiếng Việt hay từng tính năng tìm; không quy suy OCR tiếng Việt ở mọi chế độ. |
| Tags / Smart Folders | Nhiều tag mỗi note; Tag Browser; Smart Folder áp bộ lọc any/all theo tag, ngày, mention... [A06, A07]. | **Lọc động không phải phân loại bằng nội dung rồi gán quan hệ Topic/Project**. Tag là một từ; có thể dùng dấu gạch nối/gạch dưới [A06]. |
| Ghi âm / timestamp | Có recording, transcript có thể tìm, chạm đoạn text để phát từ vị trí tương ứng; tóm tắt transcript bằng Apple Intelligence khi thiết bị/ngôn ngữ đủ điều kiện [A09]. | **Phiên âm trực tiếp trong Notes không liệt kê tiếng Việt**, dù Apple Intelligence có hỗ trợ tiếng Việt ở một số tính năng [A09, A19]. Tính chính xác timestamp, xuất file kèm locator, video timestamp và API không được chứng minh. |
| Ngày tạo/sửa, version | Notes cho xem/sắp xếp ngày tạo và ngày sửa, autosave trên Mac [A20, A24]. | Không tương đương nhật ký **bất biến từng lần gửi**, source-posted-at, retry idempotency hay receipt của server. |
| Markdown / xuất nhập | Trên Mac: import Markdown/TXT/HTML/RTF/ENEX, export từng note ra PDF/Markdown, copy as Markdown [A11]; iPhone iOS 27 xuất Markdown/PDF [A10]; import MD được Apple xác nhận từ iOS/iPadOS/macOS 26 [A12]. | Xuất từng note **không phải** export toàn bộ cây + attachments + source ID + quan hệ + manifest kiểm checksum; tài liệu iPhone cảnh báo PDF export note có multipage PDF chỉ chứa trang đầu của attachment [A10]. Không khẳng định roundtrip lossless. |
| Nền tảng / offline | Native iPhone, iPad, Mac; có iCloud Notes web, Windows PC được Apple liệt kê truy cập qua iCloud.com [A13, A14, A21]. Mac có lưu cục bộ On My Mac [A24]. | **Không tìm thấy ứng dụng Android/Windows native chính thức**; với Android browser, tương thích chức năng đầy đủ và xử lý mất mạng/chỉnh xung đột là `UNVERIFIED`. iCloud.com không cung cấp tài liệu chứng minh offline. |
| API / SDK / MCP | Kỹ sư DTS của Apple xác nhận **không có Notes API** cho CRUD, AppleScript chỉ trên Mac; App Intents có thể cung cấp action của *app của ta* cho Shortcuts, không mở API của Notes [A15, A16]. Shortcuts có action Create Note/Append to Note [A26]. | Không có bằng chứng REST API/SDK/MCP chính thức quản lý Notes từ máy chủ Windows/Android. **Không lấy private CloudKit endpoint hoặc script không chính thức làm nền tảng.** |
| Privacy / xóa | Notes iCloud hỗ trợ sharing; Advanced Data Protection (ADP) tùy chọn đưa Notes vào nhóm dữ liệu iCloud được mã hóa end-to-end [A17]. iCloud Notes cho khôi phục note xóa trong tối đa 30 ngày [A23]. | Không tuyên bố **mọi** ghi chú mặc định E2EE. Đặc tính ADP thay đổi theo vùng, thiết bị và thao tác cấu hình; chưa kiểm thử tài khoản thực. Notes thuộc hệ sinh thái Apple, không có mã nguồn Notes OSS chính thức được xác nhận từ các nguồn khảo sát. |
| Chi phí | Notes là app kèm hệ sinh thái; iCloud 5GB miễn phí, iCloud+ tại Việt Nam 50GB 25.000đ, 200GB 89.000đ, 2TB 299.000đ/tháng (có gói lớn hơn) [A18]. | Giá là **dung lượng iCloud chung**, không phải thuê bao Notes riêng; phí thiết bị/Apple ID không cộng vào. Nếu cần chứa hàng trăm GB, 200GB không đủ; điều này không chứng minh Notes hỗ trợ ingest hơn 10.000 video. |

**Trạng thái phát hành:** Các khả năng ở bảng được hướng dẫn như tính năng đang có trong tài liệu iOS 27/macOS 27 hoặc được Apple xác nhận có từ iOS 26; **không** gọi các ý tưởng đề xuất cho Kho Tri Thức là tính năng Apple đã phát hành. Apple Intelligence và một số tính năng Siri AI còn bị giới hạn theo ngôn ngữ, thiết bị, khu vực, chính sách sử dụng [A09]. Không tìm thấy roadmap API Notes hay GitHub mã nguồn chính thức để xác minh kế hoạch phát triển; ghi `UNVERIFIED`, không suy diễn.

**Tiếng Việt — phân định quan trọng:** (1) Apple có hệ thống nhập liệu tiếng Việt; Live Text có tiếng Việt [A19, A27]; (2) Apple Intelligence liệt kê tiếng Việt cho một số khả năng [A09, A19]; (3) **Notes Audio Transcription hiện chỉ liệt kê English, Spanish, Portuguese, Italian, French, German, Japanese, Korean, Chinese Simplified/Traditional** trên iPhone 12 trở lên, **không liệt kê Vietnamese** [A09]; (4) năng lực nhận dạng thực tế dấu/biểu mẫu/PDF tiếng Việt, ASR tiếng Việt và export-import không mất dữ liệu: `NOT_RUN`. Không biến (1)/(2) thành kết luận (3).

## 3. Ma trận K01–K12 theo hợp đồng chung

**Cách đọc:** Trạng thái đánh giá tính năng Apple Notes trong **toàn bộ** ca; có thể có thành phần native nhưng chưa thỏa mục tiêu. `CUSTOM_BACKEND` nghĩa là chỉ đạt được toàn bộ khi có hệ thống ngoài Notes, **không** ngụ ý Apple có API. Cột `Thử lại` là **quy trình đề xuất**, chưa chạy. Tất cả phép thử thực tế trong cột này = `NOT_RUN`.

| Ca | Trạng thái | Chứng cứ / đánh giá và giới hạn | Cách tái thử đo được (NOT_RUN) |
| --- | --- | --- | --- |
| **K01** Gõ ghi chú tiếng Việt, receipt, thời điểm | **NATIVE (một phần)** | Tạo/auto-save, ngày tạo/sửa [A02, A20]; receipt server và UUID event **không được Apple cam kết**. | iPhone tạo `Hải Phòng – Ủy ban`, offline/online; đo hiển thị ngày tạo/chỉnh, đồng bộ Mac/iCloud, tìm lại, kiểm có ACK ID & timestamp server riêng hay không. |
| **K02** Share URL video/web, tự lấy metadata + nội dung | **CUSTOM_BACKEND** | Share/Quick Note lưu link [A03], nhưng không có bằng chứng tự fetch URL Facebook/TikTok/YouTube, download/subtitle/HTML và ghi trạng thái parser. Apple không có Notes API [A15]. | Share 3 link công khai (web, YouTube, TikTok) từ Safari/Share Sheet; ghi raw URL, title, author, posted-at, text/transcript được lưu **thực**, đối chiếu bằng chứng nguồn; phần thiếu ghi không hỗ trợ. |
| **K03** Link trùng ngày sau ≠ retry | **NOT_SUPPORTED** | Notes có ngày tạo/sửa note [A20], không có interface được công bố cho immutable capture ledger/idempotency key [A15]. Đây là nhận định **trên tính năng công bố**, không chứng minh không thể có log nội bộ. | Gửi link 2 lần cách một ngày và thử lại một request; xác minh hai event mới, một item nguồn, retry không tăng event, đối chiếu timestamp; không có dữ liệu xuất => fail yêu cầu. |
| **K04** Markdown/bảng/link/Unicode roundtrip | **NATIVE (một phần)** | Bảng, link, định dạng, import/export MD chính thức [A02, A10–A12]. Import MD thành rich text, cấu trúc phức tạp/đính kèm và Unicode roundtrip nguyên byte chưa chứng minh. | Note gồm `# Tiêu đề`, GFM table, URL, emoji, chữ `Đường Quán Nam`, file đính kèm; export .md → import lại → diff văn bản, bảng, liên kết, asset/hash; báo riêng thất thoát. |
| **K05** Auto gán nhóm đã tồn tại | **NOT_SUPPORTED** | Tag nhập/chọn thủ công, Smart Folder lọc theo quy tắc [A06, A07]; không có bằng chứng tự hiểu nội dung và ghi membership vào nhóm hiện có; không gọi bộ lọc là auto-classifier. | Tạo `Golf`/`Đầu tư` trước, nhập 20 note chưa có tag; đo số membership **thực** tự tạo, lý do, confidence, mức không đè gán tay. |
| **K06** Liên kết/ngữ cảnh/backlinks | **NATIVE (một phần)** | Link thủ công tới note/section, đổi tiêu đề có thể cập nhật label [A08, A25]; không có bằng chứng backlinks/related-by-content tự phát hiện và provenance. | Tạo A→B, B→C, đổi tên B; xác minh link không gãy, xem A có xuất hiện trong backlink của B không, có liên quan do nội dung được ghi lý do hay không. |
| **K07** PDF/audio/video jump locator | **NATIVE (một phần: audio)** | PDF scan/tìm attachment [A04, A05]; transcript audio click-to-play [A09]. **Chưa chứng minh** trích dẫn PDF trang X và video tại mm:ss lưu, mở lại bằng ID/timestamp qua API. | PDF 12 trang có dấu Việt, audio 4 phút, video 2 phút; ghi locator `page=7` và `start=01:12`; reload và mở từ từng trích dẫn, đo độ lệch ≤1s và trang; ghi unsupported path. |
| **K08** Một mục nhiều nhánh, tree/table/card/timeline | **NATIVE (một phần)** | Nhiều tag, Smart Folder, folder view list/gallery, lọc theo ngày [A06, A07, A28]. **Không có chứng cứ** tree nhiều cha, table và timeline đầy đủ với cùng item ID. | Gắn note vào 2 chủ đề/tags, tạo 2 Smart Folders, tìm ở mỗi nơi; kiểm cùng một note, lịch sử sửa và có tree/table/card/timeline chuyển được không. |
| **K09** Android + Windows, offline/xung đột | **NOT_SUPPORTED (toàn bộ yêu cầu)** | iCloud.com hỗ trợ Windows PC [A13, A14]; app native thuộc thiết bị Apple [A21], không có Android native được Apple công bố. Android browser/offline conflict resolution chưa xác minh. | Thử Windows Chrome/Edge và Android Chrome có/không mạng, sửa note đồng thời từ 2 máy; ghi màn hình/chức năng, mất dữ liệu, cách resolve conflict, trạng thái `NOT_RUN` cho đến khi kiểm. |
| **K10** API, export/import MD+assets, backup/exit | **NOT_SUPPORTED (toàn bộ yêu cầu)** | Export/import Markdown từng note có thật [A10–A12]; **Apple DTS xác nhận không có Notes CRUD API** [A15]; bulk manifest schema, asset hash/mapping và restore đầy đủ không được chứng minh. | Nhập 50 note nhiều bảng/ảnh/PDF, xuất tất cả, định danh ID/asset, hash, tags/links, xóa kho thử rồi import; so COUNT, liên kết, bytes và tạo bản backup độc lập. |
| **K11** AI có nguồn, phân biệt gợi ý/sửa, chi phí | **CUSTOM_BACKEND** | Apple Intelligence tóm tắt *transcript audio* khi đủ điều kiện [A09]; không có chứng cứ source-level provenance, tách authored/derived hay review queue của các URL/video. | Tạo audio có 3 phát biểu kèm 1 thông tin sai, tóm tắt, xác định được transcript/timestamp dẫn chứng không; thử bật/tắt AI, xem thay đổi text gốc, lưu model/version/chi phí. |
| **K12** 10.000+ items, vài trăm GB video qua Drive | **UNVERIFIED** | Giá iCloud 5GB→2TB+ [A18], Notes cho đính file [A29]; không thấy benchmark của Apple cho 10.000 note/video, remote Drive storage, pagination/search latency, bandwidth và restore. Không tự chấm 0 chỉ vì chưa có bằng chứng. | Tạo corpus giả lập 10.000 note + 100GB assets không chứa dữ liệu riêng; đo P50/P95 tạo/tìm/mở/sync/backup, quota, xung đột, link còn đúng; cần quyền tài khoản thử trước khi thực hiện. |

**Ghi chú phân loại:** các hàng có `NATIVE (một phần)` **không** được xem là toàn ca PASS. Các hàng `NOT_SUPPORTED` nói về thiếu hợp đồng công khai phục vụ bài toán Kho Tri Thức, không phải phán quyết mọi khả năng chưa từng tồn tại ở Apple. Chưa có Apple UI/API chạy thật: **K01–K12 đều NOT_RUN ở cấp thực nghiệm**, chỉ có chứng cứ tài liệu tương ứng.

## 4. Đối chiếu mã thực tế Kho Tri Thức: không so với roadmap trống

| Năng lực | Kho Tri Thức main tại SHA khảo sát | Apple Notes có thể dạy gì / đánh giá |
| --- | --- | --- |
| Nhận văn bản/link/file, từng lần gửi, retry | **ĐÃ CÓ:** `CaptureScreen.tsx` lựa chọn text/link/file, `ingestion/services.py` lưu Event với `server_received_at`, tìm retry cùng key; Windows thực đã kiểm luồng receipt [R01–R03]. | **CẢI THIỆN UX** share nhanh, Quick Note prefill tiêu đề/lựa chọn, phím tắt. Không thay CaptureEvent bằng modified date. |
| Markdown văn bản chính, bảng/link/Unicode | **ĐÃ CÓ:** `KnowledgeText.tsx` render Markdown GFM, nguồn HTML bị bỏ qua, link HTTP(S); `ReadKnowledgeService` ưu tiên note người dùng; bốn bài thật đã đưa vào thư viện và kiểm Drive xuất [R03–R05]. | **CẢI THIỆN:** heading có thể thu gọn, section outline, thao tác định dạng/bảng trực quan; **không** bắt chuyển lưu trữ sang rich text riêng của Apple. |
| Cây tri thức và đa nhóm | **ĐÃ CÓ:** `KnowledgeTree.tsx`, `catalog/knowledge_tree.py` dùng cây không chép bản gốc; `ItemOrganization.tsx` cho nhiều nhóm/nhánh [R06–R08]. | **THAM KHẢO:** Smart Views any/all tags/date, gắn bộ lọc như lối tắt; không thay M:N trong DB bằng một thư mục duy nhất. |
| Tự nhóm & mục liên quan | **ĐÃ CÓ TRONG CODE / CHƯA NGHIỆM THU CORPUS CÁ NHÂN:** `catalog/organization.py` auto-assign nhóm hiện có và `RelatedItem`, UI hiển thị reason [R07, R09]. | Apple Smart Folders và manual note links **không thay** được automatic evidence+assignment; học cách hiển thị link và navigation. |
| Tài liệu, video, nguồn, OCR/ASR | **ĐÃ CÓ MỘT PHẦN:** pipeline web/document/video + `DerivedContent`, bản gốc Drive, provenance; faster-whisper offline option, đã có 11 segment tiếng Anh trên một Reel qua Windows theo checkpoint [R04, R10, R11]. OCR hàng loạt, chất lượng tiếng Việt đa nguồn còn mở. | **HỌC:** scan dễ dùng, tìm từ PDF/ảnh, transcript có thể click-to-seek. **CHƯA CÓ:** seek chuẩn trong ứng dụng; đừng coi có segment thời gian là đã phát đúng thời điểm. |
| Xuất/backup/migrate | **ĐÃ CÓ TỪNG PHẦN VÀ ĐÃ LIVE TEST:** Markdown export một số Item lên Drive/connector; backup manifest v3 giữ cây/quan hệ; restore DB mới đúng phạm vi checkpoint [R11–R13]. | **CẢI THIỆN** thao tác xuất một note thành .md ngay ở UI; Apple không thay thế manifest/Drive checksum/restore. |
| Tìm kiếm/độ trễ | **ĐÃ CÓ:** SearchService tìm text/nhóm và dẫn xuất, 2 GIN indexes, với corpus thử và văn bản thật [R11, R14]. | Apple tìm ảnh/scan là UX mục tiêu; kết quả thực tế tiếng Việt và 10.000 mục phải đo, không ghi PASS từ tài liệu. |
| Windows/Android | **WINDOWS LIVE; ANDROID NOT_RUN:** Windows native loopback, React/PWA có share target nhưng chưa thử điện thoại Android thật [R11]. | Apple Notes native không giải quyết Android; iCloud web Windows không thay phần thu nhận/worker tự vận hành của Kho Tri Thức. |

**Chính xác về các mốc:** `CURRENT_STATE.md` mở đầu đã cập nhật KT-113 (211 backend test, 19 frontend test/build, Windows live 5 bài, 11 transcript segment tiếng Anh). Một số bảng/timeline phía sau còn mô tả snapshot cũ KT-112 hoặc Gate D; vì thế lấy **đầu mục KT-113 + code** làm hiện trạng mới nhất; không dùng hàng cũ “ASR chưa có” làm kết luận chung [R11]. `LIVE_PASS` được **trích lại từ checkpoint**, G06 chưa độc lập tái chạy regression, ASR hay browser.

### Giá trị với người dùng Việt Nam, nguồn và thời gian

- **Luồng Android/Windows:** Quick Note trên iPhone rất nhanh nhưng không phải share target Android; Kho Tri Thức nên hỗ trợ gửi từ trình duyệt/Android bằng receipt ngay và worker sau, không phụ thuộc Apple ID.
- **Gửi video/URL:** Apple Notes lưu link/preview thuận tiện; Kho Tri Thức phải giữ phân biệt `source_url`, URL gốc, `received_at`, `source_posted_at`, extraction state và processor version. Video có title/thumbnail **không** đồng nghĩa hiểu lời thoại hay nội dung video; nếu transcript không có, hiển thị “chưa đủ text”.
- **Chữ tiếng Việt:** Live Text hỗ trợ Vietnamese theo danh sách Apple [A19]; ASR của Notes chưa liệt kê Vietnamese [A09]; Kho Tri Thức hiện mới ghi log transcript *tiếng Anh* một Reel và chưa đo ASR tiếng Việt [R11]. Cần dữ liệu benchmark có dấu, chữ in/viết tay, biểu mẫu/số hiệu, OCR PDF scan.
- **Quan hệ tri thức:** liên kết được tạo do người dùng khác với `RelatedItem` suy ra từ text; hiển thị nguồn/độ tin cậy, không được thay nội dung curated. Tags/Smart Folder là cách xem nhiều chiều, không phải bằng chứng tự động hiểu chủ đề.
- **AI & quyền riêng tư:** Apple Intelligence có thể tóm tắt transcript trên thiết bị hỗ trợ, nhưng chưa có công bố cho pipeline metadata/video của kho; ADP tùy chọn không đồng nghĩa mọi integration có cùng mô hình quyền. Không đồng bộ dữ liệu riêng cho dịch vụ Apple chỉ để thử khảo sát. Nếu áp dụng OCR/ASR local, ghi rõ parser+version+locator, giữ raw source.
- **Khả năng thoát nhà cung cấp:** Notes có Markdown export là tiến bộ đáng kể; trong Kho Tri Thức cần manifest JSON, ID ổn định và Drive/backup copy kiểm SHA, quan hệ và lịch sử. Không nhập làm dữ liệu chính trong Notes vì cần roundtrip attachments/tags/links chưa được chứng minh.

## 5. Chấm 7 trụ (theo G00, không coi thiếu bằng chứng = 0)

Thang điểm là **độ phù hợp của Apple Notes để thay cả Kho Tri Thức**, không là điểm chất lượng chung của sản phẩm. Các khoảng biểu thị dữ liệu còn thiếu; điểm trung tâm là phán đoán từ phạm vi công bố chứ **không** phải benchmark. Mức tin cậy đánh giá ở góc nhìn bài toán Android/Windows + provenance + Drive.

| Trụ | Trọng số | Điểm ước lượng (khoảng) | Tin cậy | Căn cứ |
| --- | ---: | ---: | --- | --- |
| Capture + ingestion | 20 | **10** (8–12) | Trung bình | Quick Notes/Share/scan tốt; thiếu backend video/text/meta/event contract [A03–A05, A15]. |
| Organization + recall | 20 | **11** (9–13) | Trung bình | Tags/Smart Folder/link note tốt; auto-group/RelatedItem theo chứng cứ chưa có [A06–A08]. |
| Text editor + reading | 15 | **13** (12–14) | Cao cho tài liệu | Heading/collapse, tables, PDF, audio, import/export Markdown [A02, A10–A12]. |
| Provenance/related/timestamps | 15 | **5** (3–7) | Trung bình | Link note và audio click text; thiếu immutable event, derived provenance, video/PDF locators chuẩn [A09, A20]. |
| Android/Windows/offline | 10 | **2** (1–4) | Cao về native, thấp về browser | Windows iCloud web được xác nhận; Android native thiếu, Android web và sync conflict offline chưa thử [A13, A21]. |
| Portability/backup | 10 | **5** (3–6) | Trung bình | Export từng .md/PDF; không có Notes API và manifest/restore end-to-end [A10–A12, A15]. |
| Integration/cost/maintainability | 10 | **4** (3–6) | Trung bình | App đóng, AppleScript Mac, iCloud quota; khó ghép với Django/Drive qua API [A15–A18]. |
| **Tổng** | **100** | **50/100** (39–62 nếu cộng các khoảng biên) | **Trung bình** | Chấm cho **thay toàn bộ**, không kết luận Notes kém khi dùng thuần Apple. |

**Kết quả tách biệt:** (1) **Thay toàn bộ:** không đề nghị (50/100, thiếu những hợp đồng cốt lõi). (2) **Tham khảo tính năng/UX:** **cao, 8/10** (định tính, không cộng vào thang 100), nổi bật Quick Capture, Smart View, collapsible headings, manual links và tap transcript. Đây không phải điểm tổng hợp của các luồng khác.

**Giới hạn/rủi ro chính:** (i) G06 không có Apple ID/môi trường iOS/macOS để thử UI, conflict và benchmark; (ii) thiếu Notes API công khai/giấy phép OSS, rủi ro lock-in nếu tích hợp trái qua đường riêng; (iii) đánh đổi Android/Windows và iCloud với Drive hiện tại; (iv) export Markdown đơn lẻ không chứng minh backup assets/tags/links chính xác; (v) phiên âm Notes không có Vietnamese trong danh sách chính thức, còn Live Text có hỗ trợ Vietnamese nhưng độ chính xác chưa đo; (vi) tài liệu guide có thể đổi, phải kiểm bản OS và ngày nguồn; (vii) benchmark 10.000 item/100GB chưa chạy.

### Phản chứng/điều kiện đảo chiều

- **Điều kiện để cân nhắc thay toàn bộ:** Apple cung cấp *chính thức* CRUD/bulk export/import/asset provenance, timestamped capture events/idempotency, Android+Windows offline tương thích, hỗ trợ ingest Drive và chứng cứ 10.000+ item/100GB; chạy PoC độc lập đạt các ca K01–K12 và restore hoàn toàn. **Hiện không đủ chứng cứ**.
- **Giả thuyết bác bỏ khuyến nghị “học Smart Folder”:** benchmark UX trên 50+ bài do người dùng thực thao tác cho thấy bộ lọc lưu sẵn ít được dùng hơn tree/search hiện tại hoặc gây nhầm lẫn auto-gán; khi đó không thêm màn hình mới.
- **Giả thuyết bác bỏ “tap-to-seek”:** Drive remote preview không hỗ trợ Range/seek đáng tin cậy hoặc sai lệch timestamp >1 giây trong hơn 5% lượt, ngay cả sau tối ưu; giữ link tới asset/timestamp và giải thích giới hạn thay vì hứa chức năng đã PASS.
- **Giả thuyết bác bỏ “Markdown editor enhancement”:** roundtrip dữ liệu GFM, Unicode, link nội bộ hoặc accessibility giảm so với editor hiện hữu; giữ renderer và bổ sung chỉ chế độ đọc/outline, không đổi lưu trữ.
- **Trường hợp thay đổi nhận định về tiếng Việt:** tài liệu Audio Transcription Apple được cập nhật nêu Vietnamese rõ ràng *và* thử audio Việt trên thiết bị phù hợp đạt chuẩn nhận dạng; khi đó chỉ tăng điểm ASR/UX, **không** tự giải quyết API/Drive.

## 6. Sáu ý tưởng có thể mượn — không tự triển khai trong nhánh nghiên cứu

| Ưu tiên | Tính năng / loại tác động | Thiết kế áp dụng tại Kho Tri Thức, tái dùng hiện tại | Độ khó | Nghiệm thu đo được / rủi ro |
| --- | --- | --- | --- | --- |
| **P1** | **Quick Capture 1 thao tác** — UX + adapter nhỏ | Android Share Target/PWA và ô nhận nhanh Windows; prefill URL, tiêu đề, đoạn bôi đen, note; gọi API capture đã có, hiển thị `CaptureEvent.id` và giờ server. Không tạm coi link là đã fetch. | **S–M** | 20 ca text/URL tiếng Việt nhận ACK sau transaction, 2 gửi thật = 2 Event, retry cùng key = 1 Event; offline hiển thị chưa gửi chứ không “đã lưu”. Android thiết bị thật `NOT_RUN` hiện tại. |
| **P1** | **Smart Views / Saved Filters** — UX+query | Lưu điều kiện any/all tags, project, tree branch, ngày nhận, trạng thái chưa trích; truy vấn DB hiện hữu, kết quả là view không gán/sửa M:N. Có nút “Xem điều kiện” để phân biệt filter với auto-group. | **M** | 100 Item/20 nhóm: bộ lọc OR/AND và loại trừ cho ra count cố định, một bài hiện nhiều view nhưng một UUID; không thay user-pinned groups; P95 <500ms trong corpus nhỏ (đặt ngưỡng trước benchmark lớn). |
| **P2** | **Section outline / thu gọn heading** — frontend | Dùng AST Markdown hiện có để dựng mục lục đầu bài, collapse H2/H3 và anchor; nguồn Markdown text gốc giữ nguyên, dùng heading IDs ổn định tránh script/HTML tùy ý. | **S–M** | 30 note GFM có bảng/link/Unicode, sau collapse/expand editor text diff nguyên byte, keyboard Tab/Enter và focus vẫn dùng được; 0 link mất. |
| **P2** | **Link nội bộ + backlink có chứng cứ** — UX + model M:N nhỏ | Bật cách chọn item/tìm tiêu đề giống `>>`, nhưng lưu **UUID đích** và label riêng, không nối bằng title; hiển thị “Bài trỏ tới đây”; phân biệt user link với RelatedItem tự đề xuất, tránh tạo group mới. | **M** | Tạo A→B; rename B vẫn mở đúng UUID, xóa mềm B có nhãn “không còn”; query backlinks không tự merge notes, 0 broken pointers sau export/restore v3. |
| **P2/P3** | **Click transcript → seek đúng media** — frontend+stream adapter | Dùng `DerivedContent.source_locator.start/end` và `Asset` verified; UI đặt cạnh transcript, mở player và `currentTime`, xử lý chuyển clip, URL Drive hết hạn, Range/resume. Giữ nhãn ASR cần kiểm. | **L** | 20 segment từ 3 clip (ngắn/dài, pause/resume, seek lại): ≥95% tới trong ±1s theo video playable; không hiển thị “đã hiểu video” khi thiếu transcript; Drive seek thật `NOT_RUN`. |
| **P3, có điều kiện** | **Scan PDF/ảnh tiếng Việt + OCR provenance** — UX+extractor | Share/camera PDF/ảnh vào Asset gốc; chỉ khi nhu cầu được chốt mới bổ sung OCR parser versioned như `DerivedContent`, locator page/bbox, hiển thị confidence và nguồn; không lén upload lên AI bên ngoài. | **L** | Benchmark ≥30 trang có dấu và số hiệu: CER/WER, thời gian, RAM, page locator; gốc SHA không đổi, nguồn thiếu text không bị gán nội dung bịa; quyền camera/Android `NOT_RUN`. |

**Ràng buộc kiến trúc:** sáu ý tưởng không yêu cầu bỏ Django/PostgreSQL/Drive, không nhúng mã Apple (closed source), không yêu cầu mua API không tồn tại. Không cài AppleScript/cloudkit private SDK. Mọi adapter mới phải giữ session/CSRF, xác thực chủ sở hữu, idempotency và sự tách biệt authored/derived. Khó S/M/L là ước lượng tương đối chưa quy đổi giờ/chi phí. Ưu tiên test UX/DOM/Android và seed giả, không dùng ghi chú riêng tư để benchmark.

## 7. Tái lập khảo sát và điều kiện QA

**Đã làm:** đọc bộ giao việc G06/G00, fetch baseline `main`, đối chiếu mã từng module ở [R01–R14], tra tài liệu Apple chính thức [A01–A29] và phân loại mỗi ca theo chuẩn; không xem báo cáo luồng khác. **Đã kiểm tài liệu**, chưa đăng nhập sản phẩm/đăng ký iCloud/mua dung lượng/cài extension. **Không làm:** chạy Apple Notes iOS/macOS, mượn thiết bị người dùng, mở dữ liệu cá nhân, benchmark mạng/10.000 mục, chạy test ứng dụng từ clone, sửa mã app. Đó là `NOT_RUN`, không gọi PASS.

**Quy trình tái lập sau khi được cho phép:** (1) dùng tài khoản Apple/Drive **thử nghiệm** và file giả có quyền, cùng bản OS, ghi screen/log không lộ ID; (2) chạy lần lượt các bước K01–K12, ghi thiết bị, khu vực, ngôn ngữ, số lần thử, kết quả native/third-party; (3) xuất .md/PDF, thực hiện diff Unicode và roundtrip attachment/hash; (4) đánh giá OCR Việt, transcript audio, web Android/Windows, chi phí/thời gian/giới hạn; (5) ghi FAIL/UNVERIFIED có lý do, không mặc định PASS; (6) so lại với baseline Kho Tri Thức tại SHA tương ứng và chỉ đề xuất PR mã sau khi G00 phân công.

**Kiểm soát chất lượng nghiên cứu:** ≥5 nguồn (thực tế 29 Apple, trong đó phần lớn support chính thức và 1 Developer forum có trả lời DTS), 12/12 ca có classification/evidence/test steps, 7/7 trụ và 6 ý tưởng acceptance; mọi claim quan trọng có URL và bản code đối chiếu. Kiểm soát rủi ro thời gian: mỗi lần nâng cấp OS cần đối chiếu guide mới, thông báo nếu khẳng định cũ không còn đúng.

## 8. Nguồn chính thức / truy cập ngày 20/11/2026

### Apple (nguồn sản phẩm, ưu tiên hướng dẫn và nhà phát triển)

- **[A01]** iOS 27 iPhone User Guide, mục Notes: https://support.apple.com/guide/iphone/welcome/27/ios/27
- **[A02]** Create and format notes iOS 27 (headings, table, collapsible section): https://support.apple.com/en-lamr/guide/iphone/iph1ac0b3a2/27/ios/27
- **[A03]** Quick Notes on iPhone (Share/capture): https://support.apple.com/en-lamr/guide/iphone/iph5084c0387/ios
- **[A04]** Scan text and documents iOS 27: https://support.apple.com/guide/iphone/scan-text-and-documents-iph653f28965/27/ios/27
- **[A05]** Search through notes including scanned/attachments: https://support.apple.com/en-sg/guide/iphone/iphb8628c6b8/27/ios/27
- **[A06]** Organize notes with tags iOS 27: https://support.apple.com/en-ie/guide/iphone/iphedddbfdf9/27/ios/27
- **[A07]** Smart Folders iOS 27: https://support.apple.com/en-ie/guide/iphone/iphc43adabc2/27/ios/27
- **[A08]** Links to notes and sections iPhone: https://support.apple.com/en-gb/guide/iphone/iph908d1558b/ios
- **[A09]** Record/transcribe audio iOS 27; supported spoken languages and Apple Intelligence caveats: https://support.apple.com/en-sg/guide/iphone/iphbe11247b5/27/ios/27
- **[A10]** Export PDF/Markdown iPhone (including PDF attachment limitation): https://support.apple.com/en-lamr/guide/iphone/iphdf551cfa2/27/ios/27
- **[A11]** Import/export/print notes on Mac, current guide: https://support.apple.com/guide/notes/import-export-and-print-notes-not201900c07/mac
- **[A12]** Import or share notes; Markdown introduced on macOS/iOS/iPadOS 26: https://support.apple.com/en-sg/102223
- **[A13]** iCloud.com browser support on Windows PC and iPhone: https://support.apple.com/en-us/105119
- **[A14]** iCloud Notes overview/limitations: https://support.apple.com/guide/icloud/notes-on-icloudcom-overview-mm6704cac5/1.0/icloud/1.0
- **[A15]** Apple Developer Forums, DTS engineer confirms no Notes CRUD API and limits AppleScript/Shortcuts: https://developer.apple.com/forums/thread/813810
- **[A16]** Shortcuts share actions, Append to Note: https://support.apple.com/en-asia/guide/shortcuts/apdaf74d75a5/10.0/ios/27
- **[A17]** Apple Platform Security, optional iCloud Advanced Data Protection incl. Notes: https://support.apple.com/en-afri/guide/security-pdf/sec973254c5f/web
- **[A18]** Giá iCloud+ tại Việt Nam (bài hỗ trợ cập nhật năm 2026): https://support.apple.com/vi-vn/108047
- **[A19]** iOS/iPadOS 27 feature availability (Vietnamese Live Text, Apple Intelligence, Audio/Call differences): https://www.apple.com/ios/feature-availability/
- **[A20]** Sort & pin on Mac (date created vs edited): https://support.apple.com/en-ie/guide/notes/apdb54e469b6/4.13/mac/27
- **[A21]** iCloud for Notes on devices: https://support.apple.com/guide/icloud/set-up-notes-mm8685520792/icloud
- **[A22]** Notes collaboration (iPhone): https://support.apple.com/guide/iphone/share-and-collaborate-iphe4d04f674/26/ios/26
- **[A23]** Recently deleted Notes recovered for 30 days on iCloud.com: https://support.apple.com/en-sg/guide/icloud/-mm2f42f05cb9/icloud
- **[A24]** Notes accounts/On My Mac local: https://support.apple.com/en-vn/guide/notes/not85d6f7b58/mac
- **[A25]** Add links on Mac, note and section link: https://support.apple.com/guide/notes/add-links-apde615d29c2/4.13/mac/27
- **[A26]** Shortcuts release notes (Create Note and Append to Note actions): https://support.apple.com/en-ie/101583
- **[A27]** Keyboard languages iPhone iOS 27: https://support.apple.com/vi-vn/guide/iphone/iph73b71eb/27/ios/27
- **[A28]** Folder/list/gallery/date sort: https://support.apple.com/en-ie/guide/iphone/ipha61270292/26/ios/26
- **[A29]** Attach photos/video/PDFs to notes: https://support.apple.com/en-gb/118442

**Ghi chú về ngày:** [A18] công bố bảng giá theo vùng, trang có ngày cập nhật 2026; [A26] có ngày công bố cũ 2023; các guide hiện tại tự xác định bằng phiên bản /27 hoặc /26. Không dùng kết quả preview web làm bằng chứng Apple chạy UI thật.

### Kho Tri Thức (mã tại HEAD đã nêu; đọc từ kết nối GitHub)

- **[R01]** Gửi/receipt phía UI: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/CaptureScreen.tsx
- **[R02]** CaptureEvent và idempotency: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/ingestion/services.py
- **[R03]** Render Markdown: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/KnowledgeText.tsx
- **[R04]** Read knowledge, authored/derived: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/read_knowledge.py
- **[R05]** Text knowledge live description: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/docs/operations/TEXT_KNOWLEDGE.md
- **[R06]** Cây thư viện frontend: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/KnowledgeTree.tsx
- **[R07]** UI nhóm và related items: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/ItemOrganization.tsx
- **[R08]** Cây và M:N backend: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/knowledge_tree.py
- **[R09]** Auto group & related: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/organization.py
- **[R10]** Transcript job+locator: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/transcript_job.py
- **[R11]** Hiện trạng 20/11/2026 (KT-113 top section, live & CI): https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/docs/CURRENT_STATE.md
- **[R12]** Hướng dẫn tree/transcript/Drive: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/docs/operations/KNOWLEDGE_TREE.md
- **[R13]** Knowledge export pilot: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/docs/operations/KNOWLEDGE_EXPORT.md
- **[R14]** SearchService: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/search/services.py

**Kết luận bảo lưu:** Báo cáo G06 là đánh giá độc lập, có thể bị sửa *bằng nguồn mới kèm lịch sử sửa* nhưng không điều chỉnh để khớp thứ hạng của G00 hay báo cáo luồng khác. **Khuyến nghị cuối: Tham khảo UX, PoC các ý tưởng chọn lọc theo gate, KHÔNG thay toàn hệ thống và KHÔNG merge PR nghiên cứu.**
