# G01 — Nghiên cứu độc lập Notion cho Kho Tri Thức

**Ngày đánh giá/tra cứu:** 20/11/2026 (Asia/Ho_Chi_Minh). **Phạm vi:** Notion, không đối chiếu kết luận luồng nghiên cứu khác.  
**Baseline Kho Tri Thức:** nhánh main, HEAD c97f5678a6893d7dfec2595d89c9122f05195320, xác nhận qua GitHub ngày 20/11/2026.  
**Trạng thái bằng chứng:** DOC_REVIEW đối với tài liệu chính thức và đọc mã GitHub; **NOT_RUN** đối với toàn bộ thao tác Notion trong tài khoản, thử UI, API, Android/Windows thực, benchmark 10.000 mục, thử xuất/khôi phục; không có quyền thử tài khoản Notion hoặc quyền tải dữ liệu riêng lên đó. **Không sửa mã và không đưa dữ liệu riêng tư vào dịch vụ.**

## 1. Tóm tắt điều hành (dưới 200 từ)

Notion có lợi thế nổi bật về soạn thảo dạng block, database nhiều kiểu xem, thuộc tính liên kết/rollup, backlinks, Web Clipper, ứng dụng Android/Windows và Agent có thể thao tác trên tài liệu, database. Offline **đã có** trên ứng dụng nhưng có giới hạn tải trang/database và đồng bộ. Notion cũng có API, MCP và xuất Markdown/CSV; đây không đồng nghĩa khôi phục nguyên vẹn mọi quan hệ hoặc dữ liệu gốc.

Với mục tiêu Kho Tri Thức — nhận URL/video ngay, giữ lịch sử từng lượt gửi, chống trùng, tự gán nhóm có bằng chứng, lưu tệp chính trên Google Drive và phân biệt văn bản được trích với nội dung video chưa biết — Notion chưa được chứng minh thay thế trọn hệ thống. Mã Kho Tri Thức hiện đã có nhiều nền tảng nghiệp vụ này. Đề xuất **THAM KHẢO UX** của Notion, không di chuyển kho hoặc viết lại backend. Chỉ đánh giá lại khả năng thay thế khi PoC bằng dữ liệu giả kiểm chứng được sự kiện, nguồn gốc, xuất/khôi phục, chi phí và quy mô.

## 2. Cách đánh giá và nguyên tắc đọc nguồn

- Nguồn ưu tiên: trang hướng dẫn Notion, Notion Developer, release ngày 13/10 và 19/10/2026, GitHub SDK chính thức; các URL ở mục 10. Các trang Help/Developer là nội dung đang hiển thị khi truy cập 20/11/2026, **không tự gán ngày xuất bản 2026** nếu trang không ghi.
- Tách bốn mức: **đã phát hành theo tài liệu**, **hạn chế theo gói/nền tảng**, **alpha/đang triển khai**, **chỉ nêu kế hoạch**. Đọc hướng dẫn của hãng không bằng thử nghiệm thực tế. Phần đánh giá kiến trúc là suy luận dựa trên chứng cứ, không phải chứng thực của Notion.
- Phân loại K01–K12 theo **đủ toàn bộ yêu cầu của tình huống**, không theo một tính năng con: **NATIVE** (có trực tiếp), **EXTENSION** (agent/automation/plugin/gói hoặc connector), **CUSTOM_BACKEND** (cần code và dữ liệu riêng), **NOT_SUPPORTED** (nguồn xác nhận không làm được), **UNVERIFIED** (chưa đủ bằng chứng). Mọi hàng đều **thử thực tế NOT_RUN**.
- So sánh với các file mã cụ thể của main [R01]–[R10], không dùng lời tuyên bố cũ rằng repo chỉ là kế hoạch. Số PASS lịch sử trong [R11] là báo cáo checkpoint, **không phải test do G01 chạy**.

## 3. Những gì Notion cung cấp — tình trạng 20/11/2026

| Hạng mục | Bằng chứng và giới hạn |
| --- | --- |
| Soạn thảo, văn bản | Trang gồm các block, bảng, liên kết, tệp/nhúng và page bên trong page; Notion import Markdown và export Markdown/CSV nhưng block đặc thù không nhất thiết xuất ra GFM y nguyên. Chưa chạy vòng import–edit–export với tiếng Việt [N12], [N13], [N14]. |
| Database/views | Một database có table, board, timeline, gallery, calendar, list và bộ lọc/sắp xếp; relation có thể hai chiều và rollup tổng hợp. Nội dung không buộc nhân bản để đổi view. Phân cấp trang là một khả năng khác với cây lĩnh vực many-to-many của Kho Tri Thức [N03], [N04]. |
| Link và thời gian | Links/backlinks dựa trên page mentions, có block links; thuộc tính created time, last edited time thuộc page/record. Chưa có bằng chứng native mô hình CaptureEvent bất biến nhiều lượt và idempotency request [N05], [N06]. |
| Clipper & mobile | Web Clipper tiện ích trình duyệt desktop; Android có Notion trong share sheet (Notion Help nêu Android 7+). Clipping web page/link không chứng minh tải video gốc, trích transcript, tạo lịch sử các lần gửi, tự nhận metadata của mọi nền tảng [N02], [N14]. |
| Offline & đa thiết bị | Desktop/mobile có chọn page offline trên **tất cả** gói; paid tự tải Recents/Favorites; subpage không được tự tải; database tải **50 dòng đầu của view đầu tiên** (có thể chọn thêm từng trang); embed, AI, forms, buttons không dùng khi offline; xung đột phi văn bản có rủi ro. Offline không khả dụng trong browser [N01]. |
| Agent/AI hiện hành | Notion Agent có thể tìm và sửa trang, tạo/sửa database, relation và views, phân tích tài liệu được tải lên tùy quyền; **không trả lời dựa vào nội dung non-PDF embed như transcript của video**; không tạo một số database automation/advanced properties. Custom Agents có trigger khi page được thêm vào database/property đổi và lịch chạy; khả năng gán nhóm đúng trên corpus này và giữ dữ liệu người dùng **chưa thử** [N07], [N08]. |
| Mốc 13 & 19/10/2026 | Notion công bố MCP/context 13/10; 19/10 công bố Agent dùng browser/computer, “Review for me”, Auto, cải tiến MCP và hệ credit. Con số rẻ hơn 90% là **tuyên bố của Notion**, không phải benchmark G01; **BYOK Enterprise private alpha**; **AI Command Center “coming soon”**, không tính là đang phát hành [N09], [N20]. |
| AI meeting/audio/video | AI Meeting Notes có thể nhận file audio/video tải lên rồi tạo transcript; là luồng **upload tệp riêng**, không chứng minh đọc trực tiếp mọi video từ FB/TikTok/YouTube clipper, giữ locator nhảy đúng thời điểm trong tệp gốc hoặc chạy ASR offline. Phần audio tải lên có lưu tại Notion cho đến khi xóa; live recording có chế độ xử lý khác, lưu ý đồng ý ghi âm [N15]. |
| Giá và hạn mức | Giá quảng cáo khi tra cứu: Free $0, Plus $10/ghế/tháng, Business $20/ghế/tháng, Enterprise liên hệ; giá tính tiền thật tùy kỳ thanh toán/địa phương. **5 MB/tệp Free**, tối đa **5 GB/tệp** ở paid, không phải dung lượng kho được cam kết. Notion Agent/Custom Agents có giới hạn gói/credit, Free/Plus chỉ thử một số AI [N11]. |
| Credit AI | Tài liệu Help nêu lượng thông thường **1.500 Standard + 500 Select credit/người/tháng** cho người dùng gói đủ điều kiện, không cộng dồn, có thể thay đổi theo hợp đồng; Custom Agents/beyond quota có credit trả thêm. Không mặc định một chi phí cố định mỗi 10.000 URL [N10], [N11]. |
| API/SDK/MCP | API Notion, hosted MCP/OAuth và SDK JS chính thức. API connection hiện **180 request/phút** Free/Plus và **600 request/phút** Business/Enterprise; data-source query giới hạn riêng khoảng 3 request/giây; lỗi 429 cần Retry-After. SDK JS trên GitHub có giấy phép MIT; **đây là giấy phép SDK, không có nghĩa mã máy chủ Notion là OSS**. Version API và rate/quota phải kiểm khi triển khai adapter [N16]–[N18]. |
| Xuất/khôi phục | Trang thông thường ra Markdown; database ra CSV kèm các page Markdown; callout ra HTML do thiếu biểu diễn Markdown tương đương. Có export toàn workspace, nhưng **chưa kiểm chứng** roundtrip giữ relation/rollup, internal IDs, blocks, assets/nhúng Google Drive, timeline, provenance và toàn bộ lịch sử sửa. Không nhầm export với bản sao database/restore giao dịch [N12], [N13]. |
| Bảo mật, lưu giữ, giấy phép | Notion là SaaS sở hữu riêng, không phải thư viện tự host. Trang an toàn AI nói Free/Plus/Business có AI-provider retention tối đa 30 ngày; Enterprise tùy model, nhiều model zero-retention nhưng có ngoại lệ opt-in. Cần xét quyền truy cập từng workspace, nguồn gửi AI và chính sách tài khoản trước PoC; không gửi dữ liệu cá nhân thật [N19]. |

## 4. Ma trận K01–K12 — mức hỗ trợ trọn tình huống

**Tất cả tình huống: NOT_RUN trong UI/ứng dụng/API của Notion.** Cột trạng thái là nhận định từ tài liệu, không được gọi PASS. Ký hiệu [Nxx] trỏ URL chính thức ở mục 10.

| Ca | Trạng thái | Bằng chứng, điểm khuyết và bước tái thử bằng dữ liệu giả |
| --- | --- | --- |
| **K01** Gõ ghi chú tiếng Việt, receipt + giờ | **CUSTOM_BACKEND** | Native tạo page tiếng Việt, có created time [N06]; **không có chứng cứ** ACK có server_received_at bất biến tách page. Thử: tạo hai page có dấu, ghi giờ phía client, dùng API lấy created_time và kiểm receipt có tồn tại độc lập không. |
| **K02** Gửi URL video/web, metadata + nội dung | **CUSTOM_BACKEND** | Native Web Clipper/share [N02], embed [N14]; agent không đọc transcript trong non-PDF video embed [N07]. Thử: gửi URL web và video có/không phụ đề; so sánh tiêu đề/metadata, có lưu file, có nội dung nguồn hay chỉ preview. Không tự khẳng định clipper tải MP4/transcript. |
| **K03** Gửi lại URL sau 1 ngày so với retry | **CUSTOM_BACKEND** | Page ID/created time không thay cho Event tách Item và key idempotency [N06]; tài liệu không mô tả cặp ngữ nghĩa này. Thử: post 2 lần cùng URL với key khác và retry cùng key, kiểm có 2 events nhưng 1 item và không nhân bản asset. Cần adapter/DB riêng. |
| **K04** Markdown, bảng, link, Unicode không mất | **UNVERIFIED** | Native editor/import/export có hỗ trợ thành phần chính nhưng export có block ra HTML, chưa chứng minh roundtrip lossless [N12], [N13]. Thử 20 văn bản GFM tiếng Việt với bảng, URL, Unicode tổ hợp, CRLF, code; export/import, so text/hash/AST và danh mục lỗi. |
| **K05** Tự gán vào **nhóm đã có** | **EXTENSION** | Custom Agent có trigger page-added và quyền sửa DB [N08], Agent sửa thuộc tính [N07]; chưa có bằng chứng chính xác, ngưỡng tin cậy hay bảo vệ curated. Thử 100 bài mù, đối chiếu nhóm chuẩn; 0 lần ghi đè nhóm pinned; đo precision/recall, credit và tỉ lệ chưa phân loại. Không gọi native auto-tag đúng chuẩn. |
| **K06** Backlinks/mục liên quan theo nội dung | **CUSTOM_BACKEND** | Native backlinks trên link/mentions và relation thủ công [N05], [N04]; **tự phát hiện** bài có nội dung liên quan và lưu reason/provenance chưa được chứng minh. Thử 20 cặp đã biết, thêm/sửa link rồi xem backlink; muốn quan hệ ngữ nghĩa có bằng chứng cần dịch vụ kiểm soát riêng. |
| **K07** PDF/audio/video, trích dẫn đến đúng page/time | **CUSTOM_BACKEND** | Native file/embed [N14], AI Meeting Notes transcript cho file upload [N15]; chưa có bằng chứng hỗ trợ **locator chính xác đến trang/timestamp trên mọi nguồn** và click phát chính xác từ source. Thử PDF nhiều trang + MP4 có lời và một URL video: đối chiếu page 3, đoạn 00:42; ghi NOT_SUPPORTED khi thực nghiệm xác nhận thiếu, hiện **chưa chạy**. |
| **K08** Nhiều lĩnh vực + tree/table/card/timeline | **NATIVE** (phần xem/quan hệ) | Database relation đa trang và đa view [N03], [N04]; phân cấp trang không đương nhiên đáp ứng cây linh hoạt many-to-many như KTT. Thử 1 bài gắn 2 lĩnh vực, 4 views, điều chỉnh một lần; kiểm cùng page ID và khả năng tìm qua mỗi nhánh. |
| **K09** Android/Windows, offline, xung đột | **NATIVE** (có điều kiện) | Native app & offline, nhưng chỉ page tải và 50 dòng đầu view đầu của DB; browser không offline, xung đột non-text có thể mất một cập nhật [N01], [N02]. Thử thật trên 2 thiết bị: tải 60 items, sửa text và select đồng thời rồi kết nối lại; phải ghi số items/trường hợp xung đột. |
| **K10** API, Markdown/assets export, backup/exit | **EXTENSION** | Native API/MCP/export [N12], [N16], [N17]; lossless của DB relation, file/Drive và full restore không chứng minh. Thử export 100 pages có assets, 2-way relation, rollup, link; import workspace rỗng; đo mapping ID, nội dung, attachment. Adapter/backup riêng nếu dùng làm system-of-record. |
| **K11** AI nguồn trích/gợi ý ≠ sửa user, quyền/giá | **EXTENSION** | Notion Agent/Custom Agent có quyền đọc và **sửa** trang, credit và retention theo plan [N07]–[N11], [N19]; chưa chứng minh khóa cưỡng chế “chỉ gợi ý, không được ghi đè curated”. Thử trên 30 draft với bảng approval/diff, quyền read-only và cost log; yêu cầu không một sửa đổi không được duyệt. |
| **K12** 10.000+ items, hàng trăm GB Drive | **UNVERIFIED** | Có API nhưng rate limit và file-upload caps [N11], [N17]. **Không có benchmark** 10k item + 100 GB nguồn gốc Drive, độ trễ lọc, thumbnail, playback, export/restore. Thử 10.000 item giả có liên kết external Drive và mô phỏng 100 GB (không upload dữ liệu riêng), đo p95, lỗi 429, chi phí và mất link. |

**Giới hạn phân loại:** “CUSTOM_BACKEND” không khẳng định Notion **không thể** làm nghiệp vụ; nghĩa là không thấy Notion native đủ hợp đồng của KTT và cần logic tự viết. Tình huống K08/K09 “NATIVE” vẫn có giới hạn đã nêu. Không kết luận một bài chứa URL video là nội dung video đã được hiểu hoặc lưu file gốc.

## 5. Đối chiếu trực tiếp với code Kho Tri Thức tại main

| Khả năng | Tình trạng thực tế trong repo KTT | Điểm Notion hơn/kém; đề xuất |
| --- | --- | --- |
| Nhận URL/chữ và lịch sử | [R01], [R02]: transaction và CaptureEvent UUID bất biến; cùng idempotency key trả Event cũ, request mới tới canonical URL tái dùng Item/Source nhưng tạo Event mới. UI [R08] trả receipt sau gửi. | Notion clipper tiện thao tác nhanh; **không thay** hợp đồng sự kiện KTT. Mượn UX clip/preview, giữ DB/ACK. |
| Cây, gán nhóm, liên quan | [R03] Topic.parent, ItemTopic/Project/Tag many-to-many, user_pinned; [R04] rule-based assignment vào nhóm đang có và RelatedItem có reason/method/source version; UI cây và multi-select [R09]. | Notion vượt ở views/relations/rollups và block UX; KTT đã có cấu trúc và bảo vệ nguồn gốc tự gán. Thêm các kiểu xem mới, **không tạo DB song song**. |
| Văn bản và editor | [R08], [R09]: văn bản Markdown trong thư viện; [R10] react-markdown + remark-gfm, URL safety, bảng. Editor trong ItemScreen hiện là vùng nhập văn bản, chưa tương đương rich block/WYSIWYG. | Notion tốt hơn rõ về inline rich editing; áp dụng editor Markdown-first nếu roundtrip an toàn, không lưu dữ liệu chính thành Notion blocks. |
| Nguồn, nội dung dẫn xuất | [R03] Source và [R05] DerivedContent có processor/version/input_hash/source_locator; [R06] xuất snapshot kèm source, file, cảnh báo thiếu transcript. | Notion link/embed thân thiện nhưng trang Help không chứng minh locator và provenance chặt. Giữ lớp nguồn/tệp/dẫn xuất của KTT; UI gắn link mở đúng nguồn. |
| Video/ASR/Drive | [R07] có ASR cục bộ giới hạn, segments thời gian; [R06] xử lý cảnh báo thiếu transcript; [R11] báo cáo thử một Reel, **chưa nghiệm thu tiếng Việt/seek Android**. KTT lưu file/định danh trên Drive qua storage adapter. | Notion AI Meeting Notes là nhánh riêng, có chi phí và gửi dữ liệu lên dịch vụ; không thay hệ Drive/Python ASR. Chỉ nghiên cứu UI transcript nếu hợp lệ. |
| Tìm kiếm, quyền sửa | [R04] auto-group có version, [R09] UI phân biệt tự gán/người dùng; [R06] xuất deterministic, ghi rõ derived và note. Không coi similarity là AI hiểu sâu. | Notion Agent thao tác đa bước, nhưng không có bằng chứng giữ bất biến đối với quyền chỉnh tay; thêm chế độ đề xuất có duyệt trước khi thử. |
| Khả năng vận hành | [R11] checkpoint Windows/live cho một tập nhỏ; **Android, 10k-item, video seek, chất lượng phân nhóm/ASR tiếng Việt vẫn chưa nghiệm thu**. | Notion có app/offline native nhưng phụ thuộc SaaS và plan; không phủ nhận hạn chế hiện tại của KTT, cũng không khẳng định thay thế đã được chứng minh. |

**Ranh giới kiến trúc:** Notion là sản phẩm SaaS và có SDK/MCP; không có bằng chứng giấy phép hoặc mã nguồn máy chủ cho phép “ghép editor Notion” trực tiếp vào React/KTT. Không đề xuất copy mã hoặc dựng backend Notion. Nếu muốn tích hợp API về sau, làm **adapter tùy chọn**, không chuyển source-of-truth sang Notion.

## 6. Chấm điểm 7 trụ (định lượng có điều kiện)

Các điểm là **ước lượng chức năng theo tài liệu, không phải điểm test thực tế**; khoảng thể hiện độ không chắc chắn do NOT_RUN. 0 không dùng để thay cho UNVERIFIED. Trọng số cố định của G00, không tự sửa sau khi xem báo cáo nhóm khác.

| Trụ (tối đa) | Điểm tham chiếu | Khoảng hợp lý | Mức tin cậy | Cơ sở |
| --- | ---: | ---: | --- | --- |
| Capture + ingestion (20) | **8** | 6–11 | Trung bình | Clipper/share mạnh, thiếu evidence full event/dedup/video ingest [N02], [N06], [N07]. |
| Organization + recall (20) | **16** | 14–18 | Cao về UX, thấp về auto-quality | Relation/rollup/multiple views mạnh, agent auto grouping chưa đo [N03], [N04], [N08]. |
| Text editor + reading (15) | **13** | 12–14 | Cao về tính năng, vừa về UTF-8 roundtrip | Block editor tốt, export không luôn GFM lossless [N12], [N13]. |
| Provenance/related/timestamps (15) | **5** | 3–8 | Trung bình | Backlinks/thời gian page có, thiếu sự kiện bất biến và locator PDF/video được xác minh [N05], [N06], [N14]. |
| Android/Windows/offline (10) | **7** | 6–8 | Cao về tài liệu, thấp về thiết bị | Có offline, giới hạn số dòng và conflict [N01], [N02]. |
| Portability/backup (10) | **6** | 5–8 | Trung bình | Markdown/CSV/API có; restore quan hệ/files chưa kiểm [N12], [N16]. |
| Integration/cost/maintainability (10) | **6** | 4–8 | Trung bình | API/MCP/SDK dễ tích hợp nhưng SaaS, credit, 429, lock-in [N10], [N11], [N17]. |
| **Tổng (100)** | **61** | **50–75** | **Hạn chế — chưa benchmark** | Tổng điểm 8+16+13+5+7+6+6 = **61**; khoảng: (6+14+12+3+6+5+4) = **50** đến (11+18+14+8+8+8+8) = **75**. |

**Hai kết luận tách riêng:**

1. **Thay thế toàn bộ KTT:** không khuyến nghị tại ngày đánh giá. Điểm 61/100 là mức giàu tính năng nói chung, **không vượt qua các gate bắt buộc**: CaptureEvent/idempotency, giữ tệp Drive gốc, provenance/timestamp, cost + backup roundtrip, 10k item. Điểm không thay cho tiêu chí nghiệm thu.
2. **Học/tái sử dụng tính năng:** **cao** (định tính 4,5/5 cho UX database nhiều view, block-reading, relation, backlinks, quick capture), nhưng phải tự triển khai tương thích React/Django/PostgreSQL và không giả định Notion core là thư viện nhúng.

## 7. Sáu ý tưởng áp dụng — không yêu cầu viết lại kiến trúc

| Ý tưởng | Loại / độ khó | Phụ thuộc và rủi ro | Acceptance test đo được |
| --- | --- | --- | --- |
| 1. Saved views Thư viện: list/table/card/timeline; nhớ filter/sort | **UX + frontend / M** | Dùng API items hiện có, không đổi Item UUID; timeline theo saved_at/published_at tách biệt; pagination có thể chậm. | 100 Item giả, 1 Item trong 4 view có cùng UUID; filter cây nhiều nhánh nhất quán; không tạo mới Item. |
| 2. Cột/property chips và relation card cho Topic/Project/Tag | **UX / S–M** | Tái dùng ItemTopic/Project/Tag; không sửa user_pinned bởi auto; không đổi taxonomy. | 30 Item nhiều nhóm, đổi 1 lần cập nhật mọi view; 0 mất phân nhóm pinned sau organize job. |
| 3. Backlink panel + “Vì sao liên quan?” mở qua Item ID | **UX + API / M** | RelatedItem có source version, không coi link là quan hệ ngữ nghĩa; stale/dismissed phải hiện đúng. | 20 cặp kiểm thử: show đúng relation status, reason và target; 0 edge mất provenance. |
| 4. Gửi URL/Share Target một bước, preview source và trạng thái tải | **UX / M** | Giữ CaptureService transaction; URL/video có thể không tải, không gán nhầm transcript; rủi ro duplicate do retry. | 2 yêu cầu cùng URL khác key tạo 2 Event/1 Item; retry cùng key 1 Event; receipt xuất hiện trước worker hoàn tất. |
| 5. Rich editing *lấy cảm hứng* từ block, nhưng lưu Markdown | **UX + editor adapter / M–L** | Không dùng SDK Notion như component editor; bảo toàn GFM/Unicode và preview sanitize, hỗ trợ fallback source editor. | Bộ 30 ghi chú tiếng Việt (bảng, link, code, Unicode tổ hợp, xuống dòng) có vòng save/reopen/export không rơi chữ/link; không đổi Item ID. |
| 6. AI review dạng đề xuất/diff có nguồn, mặc định không áp dụng | **UX + adapter / L, tùy chọn** | Provider/cost/privacy, prompt injection từ nguồn; không cho ghi đè Item.note hoặc curated group mặc định. | 50 fixture: 0 ghi đè trước nút xác nhận, 100% đề xuất hiển thị source và version, chi phí được ghi; mất AI vẫn gõ/đọc bình thường. |

**Ưu tiên:** thực hiện độc lập ý tưởng 1–3 trước; ý tưởng 4 chỉ tối ưu UI capture đã có; ý tưởng 5 cần benchmark Markdown lossless; ý tưởng 6 chỉ PoC sau khi đồng ý ngân sách/chính sách dữ liệu.

## 8. Rủi ro, phản chứng và điều kiện đổi quyết định

1. **Source-of-truth/lock-in:** bản xuất Markdown/CSV không đồng nghĩa giữ mọi relation/rollup/hình/asset/version; nếu bị khóa dịch vụ phải có export/restore + checksum đo được [N12], [N13].
2. **Video và provenance:** web-clip/bookmark/embed hoặc có transcript AI Meeting Notes **không chứng minh** lưu bản MP4 gốc hay trích nguồn đúng timestamp cho mọi video [N07], [N14], [N15].
3. **Quyền và AI cost:** Agent có khả năng sửa các trang nó được cấp quyền; bắt buộc có ranh giới giữa gợi ý và curated, đo giá trong credit; retention và quyền người dùng theo plan [N07], [N10], [N19].
4. **Offline/concurrency:** 50 dòng đầu, subpage không tự tải, browser không offline và conflict non-text là trở ngại thực sự cho thư viện lớn trên Android [N01].
5. **Hiệu năng/quota:** 10k pages + clip ingest + query + export có thể phát sinh nhiều API calls/429 và credit; **không có dữ liệu thực nghiệm nên không khẳng định thất bại hay thành công** [N11], [N17].
6. **Sự thay đổi của hãng:** 2026 có alpha/coming soon; nếu đưa roadmap hoặc marketing vào điều kiện thiết kế sẽ lệch kế hoạch [N09].

**Điều kiện đảo chiều quyết định “không thay toàn bộ”:** với dữ liệu giả và gói giá công bố rõ ràng, chứng minh đồng thời (a) 10.000+ mục, 100 GB file nguồn trong Drive với ID/permission bất biến, xem được trên Android/Windows; (b) ACK và hai Event riêng khi gửi lại, retry không nhân đôi; (c) file video/PDF source và locator trang/giây mở chính xác, không suy video khi không có transcript; (d) tự gán nhóm cũ đạt tiêu chí do chủ sở hữu chốt, không sửa pinned; (e) export/restore giữ toàn bộ Item–Event–asset–relation với checksum; (f) offline, API quota, tổng chi phí/credit và quyền dữ liệu đáp ứng dùng cá nhân. Chỉ một bản demo đẹp hoặc điểm tổng cao **không** đủ đảo kết luận.

**Phản chứng với khuyến nghị học UX:** nếu 30 văn bản tiếng Việt roundtrip qua editor mới làm mất Markdown, hoặc 100 mục đa view tạo Item trùng/đổi ID, bỏ ý tưởng tương ứng và giữ editor/tree hiện có. Nếu Notion thực nghiệm xuất/nhập giữ toàn bộ relations và tải media gốc qua Drive adapter với chi phí hợp lý, mở lại hạng mục thay thế từng phần — không suy từ tài liệu quảng bá.

## 9. Các phép thử chưa chạy và cách nghiệm thu độc lập về sau

| Thành phần | Trạng thái | Vì sao |
| --- | --- | --- |
| Đọc trang docs/release/public GitHub | **DOC_REVIEW** | Đã tra cứu URL và đối chiếu chức năng; thông tin dịch vụ có thể đổi sau 20/11/2026. |
| Notion Web/Desktop/Android; Web Clipper/Agent/Custom Agents | **NOT_RUN** | Không mở workspace Notion của người dùng, không được cấp phép thử gói trả phí/agent; không báo PASS. |
| API/SDK/MCP tạo page/relation, retry/429 | **NOT_RUN** | Không cấp token hay chạy request đến workspace; chỉ xem tài liệu API. |
| Import/export/backup/restore, Unicode CRLF, audio/video locator | **NOT_RUN** | Không có bộ dữ liệu thử/Notion workspace; chưa có hash/biên bản so sánh. |
| 10k items, 100GB, offline 2 thiết bị thật, mức tiêu hao credit | **NOT_RUN** | Chưa có tài khoản/test-bed/ngân sách; không suy ngưỡng năng lực. |
| Đọc code và trạng thái main của Kho Tri Thức | **CODE_REVIEW_ONLY** | Đã đọc trực tiếp các file [R01]–[R10]; không checkout/build/động vào runtime và không chạy test; [R11] là log ghi trong repo. |

**Đầu ra nghiên cứu:** duy nhất file báo cáo này. Không sửa code/app, docs hệ thống, không dùng dữ liệu thật của người dùng. PR để G00 review, **không merge**.

## 10. Danh mục nguồn có thể tái kiểm

**Nguồn Notion/Notion Developer/GitHub công khai (truy cập 20/11/2026).** Ngày xuất bản chỉ ghi khi có thể xác nhận:

- [N01] [Notion Help — Use pages offline](https://www.notion.com/help/use-pages-offline), trạng thái Help khi truy cập.
- [N02] [Notion Help — Save web pages with Notion Web Clipper](https://www.notion.com/help/web-clipper), trạng thái Help khi truy cập.
- [N03] [Notion Help — Database views, filters, sorts & groups](https://www.notion.com/help/views-filters-and-sorts), trạng thái Help khi truy cập.
- [N04] [Notion Help — Relations & rollups](https://www.notion.com/help/relations-and-rollups), trạng thái Help khi truy cập.
- [N05] [Notion Help — Links & backlinks](https://www.notion.com/help/create-links-and-backlinks), trạng thái Help khi truy cập.
- [N06] [Notion Help — Database properties](https://www.notion.com/help/database-properties), trạng thái Help khi truy cập.
- [N07] [Notion Help — Get started with Notion Agent](https://www.notion.com/help/notion-agent), trạng thái Help khi truy cập.
- [N08] [Notion Help — Custom Agents](https://www.notion.com/help/custom-agents), trạng thái Help khi truy cập.
- [N09] [Notion release — Agents, rebuilt to do more for less](https://www.notion.com/releases/2026-10-19), **phát hành 19/10/2026**; tách released/alpha/coming soon.
- [N10] [Notion Help — Manage your AI credits](https://www.notion.com/help/manage-your-ai-credits), trạng thái Help khi truy cập; bao gồm ngoại lệ phân bổ.
- [N11] [Notion — Pricing](https://www.notion.com/pricing), bảng giá hiển thị 20/11/2026; không là báo giá cam kết.
- [N12] [Notion Help — Export your content](https://www.notion.com/help/export-your-content), trạng thái Help khi truy cập.
- [N13] [Notion Help — Import data](https://www.notion.com/help/import-data-into-notion), trạng thái Help khi truy cập.
- [N14] [Notion Help — Embeds, bookmarks & link mentions](https://www.notion.com/help/embed-and-connect-other-apps), trạng thái Help khi truy cập.
- [N15] [Notion Help — AI Meeting Notes](https://www.notion.com/help/ai-meeting-notes), trạng thái Help khi truy cập; chú ý bản ghi live và file upload khác nhau.
- [N16] [Notion Developer — Notion MCP overview](https://developers.notion.com/guides/mcp/overview), trạng thái Developer Docs khi truy cập.
- [N17] [Notion Developer — API request limits](https://developers.notion.com/reference/request-limits), trạng thái Developer Docs khi truy cập (180/600 requests/min theo gói).
- [N18] [GitHub — official makenotion/notion-sdk-js](https://github.com/makenotion/notion-sdk-js), chỉ áp dụng giấy phép của SDK client; không suy license của Notion core.
- [N19] [Notion Help — AI security & privacy practices](https://www.notion.com/help/notion-ai-security-practices), trạng thái Help khi truy cập; retention theo gói/model.
- [N20] [Notion release — Notion 3.8](https://www.notion.com/releases/2026-10-13), **phát hành 13/10/2026**.

**Mã/đánh giá hiện trạng nội bộ Kho Tri Thức:** các link này tham chiếu **đúng commit baseline main** c97f5678a6893d7dfec2595d89c9122f05195320 (truy cập 20/11/2026), không phải API/demo Notion.

- [R01] [ingestion/services.py — CaptureSubmission và submit_capture](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/ingestion/services.py).
- [R02] [ingestion/models.py — CaptureEvent và unique key](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/ingestion/models.py).
- [R03] [catalog/models.py — Item, Source, Topic, assignments, RelatedItem](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/models.py).
- [R04] [catalog/organization.py — auto group/related provenance](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/organization.py).
- [R05] [processing/models.py — DerivedContent/version/locator](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/models.py).
- [R06] [processing/knowledge.py — snapshot, nguồn và cảnh báo transcript](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/knowledge.py).
- [R07] [processing/transcribe.py — local bounded ASR](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/transcribe.py).
- [R08] [web/CaptureScreen.tsx — nhận URL/text và receipt](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/CaptureScreen.tsx).
- [R09] [web/KnowledgeTree.tsx — cây UI](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/KnowledgeTree.tsx) và [web/ItemOrganization.tsx — groups & related](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/ItemOrganization.tsx).
- [R10] [web/KnowledgeText.tsx — Markdown/GFM renderer](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/KnowledgeText.tsx).
- [R11] [docs/CURRENT_STATE.md — điểm checkpoint, giới hạn chưa nghiệm thu](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/docs/CURRENT_STATE.md).
