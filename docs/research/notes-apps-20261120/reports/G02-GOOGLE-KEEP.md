# G02 — Nghiên cứu độc lập Google Keep cho Kho Tri Thức

**Thời điểm đánh giá:** 20/11/2026 (Asia/Bangkok, UTC+07)  
**Luồng:** G02, chỉ nghiên cứu Google Keep; chưa đọc bảng nguồn G00 hoặc kết quả bất kỳ luồng G01/G03–G17 nào.  
**Baseline mã:** [c97f5678a6893d7dfec2595d89c9122f05195320](https://github.com/cavoixanh638/kho-tri-thuc/commit/c97f5678a6893d7dfec2595d89c9122f05195320) trên main, lấy lúc nghiên cứu.  
**Phương pháp:** nghiên cứu tài liệu chính thức của Google (Google Workspace/Keep Help/Google Developers/Google Play), kiểm tra mã nguồn hiện tại trên GitHub; **không đăng nhập Google Keep cá nhân, không tạo ghi chú thật, không chạy thử UI/thiết bị/API, không benchmark 10.000 mục**. Tất cả test thao tác với Keep = **NOT_RUN**. Mã Kho Tri Thức chỉ được đọc, không sửa hay chạy test trong luồng này.

## 1. Executive summary (dưới 200 từ)

Google Keep là tham chiếu rất tốt về **ghi chú tức thời**: Android widget, ghi chú chữ/ảnh/giọng nói, danh sách, pin–màu–nhãn, tìm kiếm nhanh, đồng bộ và nhắc việc. Keep hiện có định dạng chữ trên web (không còn chỉ văn bản thô). Từ 2025, nhắc việc Keep liên thông Google Tasks; năm 2026 có Gemini tạo danh sách/tiêu đề và **Keep Live** tổ chức ý tưởng đọc bằng giọng nói, nhưng bị giới hạn điều kiện truy cập và không chứng minh tự phân loại mọi URL/tài liệu theo cây tri thức.

Keep **không phải phương án thay thế hợp lý** cho Kho Tri Thức đang có CaptureEvent bất biến, khử retry, thu thập URL/nguồn, phân nhóm có bằng chứng, RelatedItem, tài liệu/asset trên Google Drive và Markdown/provenance. Giới hạn **50 nhãn**, offline chỉ trên mobile, API chính thức hướng doanh nghiệp và xuất dữ liệu không tương đương import/export Markdown có cấu trúc làm tăng rủi ro. **Đề xuất: Tham khảo UX**, sau đó thử PoC nhỏ về thao tác capture/triage; **không thay backend Django/PostgreSQL/Drive**. Đánh giá tính năng dựa trên tài liệu, không phải kiểm thử chất lượng thực tế.

## 2. Tính năng, điều kiện phát hành, nền tảng, dữ liệu và chi phí

| Mục | Bằng chứng và mức chắc chắn |
| --- | --- |
| Ghi chú nhanh | Note chữ, checklist, ảnh, vẽ, audio/voice memo, widget Android, pin, nhãn và màu. Các tính năng cốt lõi ghi trong [S01], [S02], [S04], [S06], [S19]. **Đã tài liệu hóa**, tốc độ 1–2 thao tác chỉ là giả thuyết UX, **NOT_RUN**. |
| Nền tảng | Android app (Google Help ghi Android 5.0 trở lên); Windows truy cập web, không có ứng dụng Windows native được xác minh. Đồng bộ khi online; Google nói rõ **offline trên mobile, không hỗ trợ offline trên computer** [S08], [S22]. |
| Soạn thảo | Web đã hỗ trợ bold/italic/underline và heading (Google Workspace rollout 05/2025, Help hiện hành [S03], [S18]); checklist kéo thả [S20]. **Không được nói Keep chỉ plain text**. Chưa tìm thấy cam kết soạn/roundtrip Markdown, bảng GFM hay quản lý tài liệu dài kiểu editor chuyên dụng. API mô tả một khối text hoặc list, mỗi khối text dưới 20.000 ký tự [S12]. |
| Tổ chức/tìm kiếm | Một note có thể gắn nhiều label; pin, màu, archive và bộ lọc theo loại/nhãn/màu/URL; **tối đa 50 labels trên một tài khoản** [S04], [S05]. Các bộ lọc “Things” và OCR ảnh trong tìm kiếm không có bằng chứng là cây phân loại tri thức do người dùng thiết kế. Nguồn Google nêu tìm chữ trong ảnh **chỉ English** cho kiểu tìm kiếm đó [S05]; OCR tiếng Việt chưa kiểm chứng. |
| URL/video/web | Có ghi chú chứa URL và tùy chọn rich link preview [S21]. Chrome extension có Save page/selection nhưng Google ghi **từ 05/12/2022 note tạo trong extension không tự lưu**; phải kiểm tra tại keep.google.com [S13]. Không suy preview URL là tải video, transcript, content extraction, permalink timestamp hoặc download file media. |
| OCR | Google từng tài liệu hóa “Grab Image Text” trên ảnh [S07] và tìm chữ ảnh [S05]. Nguồn OCR hướng dẫn cũ không chứng minh độ chính xác/tính sẵn sàng trên ảnh tiếng Việt hiện tại; OCR tiếng Việt, offline OCR và OCR PDF: **UNVERIFIED/NOT_RUN**. |
| Reminders | Nhắc theo ngày/giờ, lặp và xem từ Keep/Tasks/Calendar [S09]. Từ 10/2025, Keep reminder chuyển sang Google Tasks [S10]; **nhắc theo vị trí không còn tạo/nhận được** theo Help hiện hành [S11], bất chấp nội dung mô tả cũ còn xuất hiện ở một số listing. Thông báo mobile do Tasks/Calendar đảm nhận, không phải Keep [S11]. |
| AI thông thường | Gemini tạo list và title trên Android; tài liệu hiện hành giới hạn vào Google AI Pro/Ultra hoặc thiết bị Pixel theo điều kiện [S14]. Đây là tạo nội dung theo yêu cầu, không phải tự phân nhóm URL/video có provenance. Không cam kết người dùng Việt Nam được sử dụng đủ tính năng. |
| Keep Live 2026 | Help mô tả Android có voice input để tạo note mới/cập nhật note cũ, kể cả câu nói gồm nhiều ý [S15]. Admin docs đặt **Keep Live ngày 31/08/2026 trong chương trình Gemini Beta**, yêu cầu edition Workspace đủ điều kiện, Beta mặc định tắt ở cấp admin [S16]; Help nêu Google AI Pro/Ultra hoặc Workspace Experiments (personal test program) [S15]. **Đã có mô tả sản phẩm; trải nghiệm/khả dụng tài khoản cụ thể = NOT_RUN**. Không đồng nhất “organize spoken ideas into notes” với gán nhiều nhãn/hierarchy cho toàn bộ kho. |
| API/SDK/MCP | Google Keep REST API v1 có notes.create/get/list/delete, media.download và permissions batch operations [S17], phạm vi Google nêu là **enterprise administration / CASB** [S18]. OAuth scopes keep/keep.readonly rất rộng trên nội dung [S23]. **Không có cơ sở coi đây là API consumer tự do để đồng bộ hai chiều**; phương án OAuth consumer, SDK consumer hay MCP Google Keep chính thức cho cá nhân = **UNVERIFIED**. API liệt kê **không có notes.update** [S17], vì vậy không hứa sync editor hai chiều. |
| Xuất/nhập | Google Takeout xuất được nội dung, list, ảnh/voice/drawing, màu, pin/archive, cộng tác viên và nhãn; tùy quyền quản trị Workspace có thể hạn chế [S24]. Copy từng note sang Google Docs được [S25]. Không có tài liệu về **nhập hàng loạt ngược Keep**, Markdown/GFM có assets + backlinks + ID giữ nguyên, manifest/restore chuẩn Kho Tri Thức. Version history trên web chỉ tải **text**, không gồm lịch sử ảnh [S26]. |
| Privacy và lưu giữ | Google Help khẳng định nội dung được mã hóa khi truyền/lưu, private trừ khi chia sẻ, xử lý nội dung phục vụ nhận dạng chữ/loại và **không dùng nội dung Keep để quảng cáo** [S27]. Tính năng Gemini/Experiments cần rà điều khoản dữ liệu/prompt/feedback riêng [S14], [S28]. Note trong Trash bị xóa vĩnh viễn sau 7 ngày theo Help [S29]. Không chuyển dữ liệu cá nhân vào dịch vụ nghiên cứu. |
| Giá, license | Các tác vụ Keep nền tảng hoạt động với Google Account cá nhân; Google Play cung cấp ứng dụng [S19]; không phát hiện bảng giá riêng cho note cơ bản. AI nâng cao có điều kiện Google AI Pro/Ultra/Workspace editions; **không báo giá tiền cụ thể khi chưa xác minh theo thị trường** [S14]–[S16]. Đây là ứng dụng dịch vụ đóng; giấy phép CC BY 4.0 cho trang tài liệu / Apache 2.0 cho **ví dụ mã trên website developer** [S18] **không phải giấy phép mở nguồn của Google Keep**. Không thấy repository nguồn chính thức của chính ứng dụng. |

### Các giới hạn cần ưu tiên ghi nhận

1. **Giới hạn cấu trúc:** 50 nhãn tổng cộng [S04] và không có chứng cứ cây nhiều cấp/bộ sách/chương, Item một-nhiều nhóm, RelatedItem dựa trên bằng chứng.
2. **Giới hạn nguồn và media:** link preview không tải/diễn giải video; chưa có tài liệu chứng minh thư viện PDF/video hàng trăm GB, timestamp media hay lưu Drive với ID nội bộ.
3. **Giới hạn offline và tích hợp:** Windows web **không offline** [S08]; API chính thức tập trung enterprise [S18], không lấy đó làm bảo chứng app cá nhân có thể tự đồng bộ.
4. **Giới hạn dữ liệu:** Takeout là đường **xuất**; roundtrip Markdown/assets/cây/ID chưa được chứng minh [S24], [S12].
5. **Giới hạn AI và quyền riêng tư:** Keep Live tùy edition/program, Android-only theo Help, tác động voice tự cập nhật note phải có review; năng lực tiếng Việt chưa kiểm thử [S15], [S16].
6. **Giới hạn phương pháp:** không đo latency, tỷ lệ mất note, OCR tiếng Việt, 10.000 mục; không coi tài liệu hãng là kết quả PASS thực nghiệm.

## 3. Ma trận K01–K12 (quy tắc G00)

**Chú giải:** NATIVE là có phần lõi được Keep hỗ trợ (ghi rõ phần thiếu); EXTENSION là dựa vào extension bên thứ nhất/bên thứ ba; CUSTOM_BACKEND là phải **tự xây hệ thống tách biệt**, không suy từ Keep API có thể làm; NOT_SUPPORTED là luồng đầy đủ không được sản phẩm hỗ trợ theo nguồn đọc; UNVERIFIED là thiếu bằng chứng, **không cho 0 điểm một cách máy móc**. **Tất cả ca thử thao tác thực tế = NOT_RUN.** Link [Snn] trỏ tới nguồn gốc ở phần 8.

| Ca | Trạng thái **đối với yêu cầu đầy đủ** | Chứng cứ/giới hạn | Bước kiểm thử tái lập khi được cấp tài khoản |
| --- | --- | --- | --- |
| K01 Gõ note tiếng Việt + receipt + giờ | **NATIVE (một phần)** | Note chữ Android/web được tài liệu hóa [S02], [S03]; API có createTime [S12]. Không có bằng chứng UI cấp receipt server và lịch sử request bất biến như Kho Tri Thức. | Trên Android và Windows tạo “Đề án kinh tế biển — 20/11”; đo từ mở app đến save; đối chiếu thời gian hiển thị và trạng thái sau reload/mất mạng. Kết quả: NOT_RUN. |
| K02 Gửi URL video/web; tự lấy metadata và nội dung | **CUSTOM_BACKEND** | Keep giữ URL/rich link preview [S21], extension trang web [S13], **không xác nhận lấy phụ đề/transcript hay tệp video**. | Chia sẻ 1 link FB/TikTok/YouTube/HTML từ Android, đối chiếu note URL, title, preview, transcript, file gốc và nguồn thật; ghi từng trường thiếu. NOT_RUN. |
| K03 Gửi cùng URL sau 1 ngày, phân biệt event và retry | **CUSTOM_BACKEND** | Note createTime/updateTime [S12] không phải sổ sự kiện độc lập mỗi lần gửi, và không có idempotency request trong API công bố [S17]. | Gửi cùng URL ngày khác và gửi lại do timeout; xem có 2 event hay 2 note, đối chiếu nguyên văn 2 annotation. NOT_RUN. |
| K04 Markdown + bảng + link nguyên vẹn | **NOT_SUPPORTED (đầy đủ)** | Rich text B/I/U/H1/H2 native [S03]; API text/list [S12]. Chưa có roundtrip Markdown GFM + bảng; **không nhầm rich text với Markdown portable**. | Paste/nhập mẫu Unicode có H1, danh sách lồng, bảng GFM, inline link, image; export rồi import/so byte/DOM. NOT_RUN. |
| K05 Tự nhận diện nhóm và **gán vào nhóm có sẵn** | **CUSTOM_BACKEND** | Nhãn/50-label thủ công [S04]; Keep Live tạo/cập nhật note từ **giọng nói**, không chứng minh tự xếp đa nhãn với taxonomy sẵn có từ web/video [S15], [S16]. | Tạo 4 nhóm, gửi 20 link/text có bằng chứng, đo số note được gán đúng label **mà không chọn tay**, kiểm nhãn đã pin. NOT_RUN. |
| K06 Liên quan/backlinks giữa mục | **UNVERIFIED (không thấy chức năng tương đương)** | Google mô tả lọc loại/nhãn/từ khóa [S05] chứ không xác nhận RelatedItem, lý do liên quan, trạng thái stale và backlinks. Thiếu tài liệu không được biến thành tuyên bố tuyệt đối mọi phiên bản. | Tạo 2 note khác từ khóa nhưng chung chủ đề, 1 trích nguồn; kiểm có link hai chiều + lý do tự sinh hoặc chỉ search trùng. NOT_RUN. |
| K07 Lưu PDF/audio/video, nhảy trang/timestamp | **NOT_SUPPORTED (đầy đủ)** | Native ảnh/voice [S06], [S19]; không có chứng cứ gắn PDF/video asset theo Drive + locator trang/timecode. OCR ảnh không đồng nghĩa hiểu video [S07]. | Thêm PDF 20 trang, MP4 30 phút và audio 5 phút; thử mở đúng trang 13 / 03:42; kiểm giữ original và checksum. NOT_RUN. |
| K08 Nhiều lĩnh vực, tree/table/card/timeline | **NOT_SUPPORTED (đầy đủ)** | Nhiều nhãn một note nhưng 50 nhãn và bộ lọc/ghim/màu [S04], [S05]; chưa có tài liệu tree đa cấp, quan hệ sách/chương, timeline theo event. | Một note gán 3 label, thử hierarchy 4 tầng, tìm ở table/card/timeline mà không nhân note. NOT_RUN. |
| K09 Android + Windows; offline và conflict | **NATIVE (một phần)** | Android app + Windows web; offline **chỉ mobile**, không trên computer [S08], [S19], [S22]. Chính sách conflict edit hai thiết bị offline = UNVERIFIED. | Hai máy cùng sửa một note khi Android offline và PC online; bật lại mạng, kiểm bản xung đột/Unicode, thời gian đồng bộ. NOT_RUN. |
| K10 API + Markdown/assets backup/restore/exit | **CUSTOM_BACKEND** | Takeout giữ nhiều trường note [S24], phiên bản text [S26]; API v1 enterprise [S18], không có importer/roundtrip Keep Markdown chính thức [S17]. | Xuất 100 note có image/audio/labels → parse archive **ngoài Keep**, import vào Kho Tri Thức staging, so ID/note/asset/labels/time; không thử với tài khoản thật. NOT_RUN. |
| K11 AI tách nguồn, gợi ý và sửa thủ công, quyền/chi phí | **CUSTOM_BACKEND** | Gemini list/title và Keep Live có thật nhưng theo điều kiện [S14]–[S16]. Chưa thấy provenance source-by-source, approval trước khi AI sửa curated note, quyền dùng nội dung/video. | Test 10 note người dùng sửa/pin; nhập text không tin cậy, dùng AI để gợi ý; đo có sửa ý người dùng hay tạo citation giả, kiểm điều khoản và phí. NOT_RUN. |
| K12 10.000 items + hàng trăm GB Drive video | **UNVERIFIED** | API text <20.000 ký tự/note [S12]; không có benchmark 10k, throughput sync/restore, media Drive nhiều TB hay link asset giữ ID trong nguồn đọc. **Không suy “unlimited notes” = đạt yêu cầu**. | Tạo dữ liệu tổng hợp hợp pháp trên tài khoản test nếu được phép, đo mở/search/export 10k notes và 500 GB remote video (không upload 500 GB thật nếu chưa được cấp quyền). NOT_RUN. |

**Cảnh báo:** một ca mang nhãn CUSTOM_BACKEND **không phải khuyến nghị viết Keep adapter**; với API consumer chưa chứng minh, đường khả thi cho Kho Tri Thức là dùng chính backend đã có và chỉ học UX.

## 4. Đối chiếu với mã **đang tồn tại** của Kho Tri Thức

Baseline GitHub đã có Django/PostgreSQL/React/worker, không phải repository thuần thiết kế; tài liệu CURRENT_STATE cũ có những đoạn lịch sử viết “chưa có mã” nên **không dùng các đoạn đó để kết luận hiện trạng**. Các nhận định dưới đây kiểm trực tiếp file code trên main tại commit nêu đầu báo cáo.

| Khả năng | Bằng chứng code Kho Tri Thức | Mức so với Keep / hướng hành động |
| --- | --- | --- |
| Capture receipt và lịch sử | [C01] có transaction tạo riêng **CaptureEvent**, giờ server, chỉ tạo Item một lần khi nhận diện Source; retry với cùng idempotency key trả event cũ. [C02] có index và ràng buộc duy nhất request key. [C03] UI gửi POST /captures với idempotencyKey và giữ state lỗi/receipt. | **Đã có nghiệp vụ sâu hơn Keep**. Chỉ học thao tác mở/ghi nhanh, không thay kiến trúc. |
| Share Android / Windows | [C04] có manifest web app với share_target GET (title/text/url); [C05] parse shared payload; [C03] UI nhận và gửi. | **Có đường kỹ thuật**, cần test Android thực và số thao tác. Không tuyên bố PASS share sheet từ chỉ một manifest. |
| URL, worker và trạng thái | [C01] khởi tạo Job fetch_source; [C06] mô hình Item có source_fetch/asset_storage/content_extract/classification_status; [C07] đọc văn bản trích xuất có source_locator và trạng thái thiếu text. | **Đã có hướng xử lý URL/nguồn thực**, mạnh hơn preview Keep; thất bại lấy video/transcript vẫn phải hiển thị đúng. |
| Markdown và đọc | [C08] render React Markdown + GFM table, link safe; [C07] ưu tiên authored note hoặc DerivedContent có processor/locator. [C09] panel sửa note. | **Đã có reading Markdown và provenance**, chưa khẳng định editor WYSIWYG như Keep/Docs. Có thể học formatting tùy chọn nhưng phải bảo toàn raw Markdown. |
| Tự xếp nhóm | [C10] OrganizationService dùng evidence từ note + derived text, tự gán **nhóm hiện hữu** và lưu Assignment, không ghi đè curated, xác định unclassified. | **Đã có rule-based auto-assign**; không dùng Keep Live để thay logic, đo precision/recall trên corpus thực vẫn là việc chưa xong. |
| Nội dung liên quan | [C10] có tùy chọn candidate_provider + similarity để tạo/stale RelatedItem; [C11] có UI RelatedItems. | **Có mô hình, đường tích hợp** nhưng xem điều kiện khởi tạo provider/ngưỡng và đo chất lượng trên dữ liệu thật, không coi mọi liên quan đã chạy tốt. Keep không có chứng cứ tương đương. |
| Cây và nhiều nhóm | [C12] KnowledgeTree cho nhiều loại node (library/field/series/book/chapter/folder); [C13] frontend thư viện có breadcrumb, scope, bộ lọc và danh sách; [C14] quan hệ ItemTopic/Project/Tag. | **Mạnh hơn 50 labels phẳng** cho nhu cầu phân tầng. Keep hợp làm ví dụ pin/màu/quick filter hơn là mô hình cây. |
| Drive export và backup | [C15] KnowledgeExport ghi Markdown/TXT trên Drive theo version và appProperties; [C16] CURRENT_STATE có kết quả pilot 8 Item/9 câu và hạn chế rõ. | **Đã có đường xuất có ID/version**. Không đồng nhất Takeout note với xuất hệ tri thức hoặc chứng minh mọi nguồn có transcript. |
| Offline/scale | [C04] web manifest có share target, **không phải bằng chứng offline queue**; CURRENT_STATE [C16] tự ghi Android, nguồn video khác, corpus thật, UI multi-device chưa nghiệm thu. | **Chưa có bằng chứng PASS offline Android/Windows hay 10k/500GB**. Keep mobile offline là UX đáng học nhưng không tự đưa thành acceptance đã đạt. |

**Đánh giá ưu điểm Google Keep so với mã đang có:** thao tác tạo note ngắn ít ngữ cảnh hơn; checklist kéo thả và widget/pin/màu trực quan; tìm theo loại/note color; nhắc việc gắn với Tasks; OCR ảnh một chạm; các thao tác giọng nói/AI hiện đại có thể đáng khảo sát. **Nhược điểm nếu thay toàn bộ:** mất transaction/receipt, mỗi capture event, provenance/locator, cấu trúc đa tầng, Drive asset, tìm liên quan dựa evidence, đường portable theo schema, và quyền kiểm soát dữ liệu/AI trong backend riêng.

**Unicode Việt:** Keep có hỗ trợ nhập chữ và giao diện Việt, nhưng **chưa chạy** test normalization NFC/NFD, tìm không dấu, OCR chữ tiếng Việt, voice tiếng Việt, lỗi gõ IME. Kho Tri Thức có lưu note gốc và Markdown nhưng chất lượng search thực tiễn cũng cần benchmark; không tô hồng một bên.

## 5. Điểm rubric 7 trụ — đánh giá sơ bộ, có độ tin cậy

Điểm là **mức thỏa yêu cầu Kho Tri Thức khi thay toàn bộ**, không phải điểm chất lượng ứng dụng Keep theo đối tượng phổ thông. Khoảng điểm thể hiện bất định do **NOT_RUN**, không quy đổi UNVERIFIED thành 0.

| Trụ | Điểm khoảng / tối đa | Lý do | Tin cậy |
| --- | ---: | --- | --- |
| Capture + ingestion | **10–13 / 20** | Note tức thời, widget, URL preview mạnh; không có evidence ingest video/doc/transcript và capture-event receipt [S02], [S13], [S21]. | Trung bình |
| Organization + recall | **6–9 / 20** | Label/color/pin/search, Keep Live voice; 50 label, không chứng minh tree/multi-group auto-assign [S04], [S05], [S15]. | Trung bình |
| Text editor + reading | **7–10 / 15** | Rich text, heading/list; thiếu chứng cứ roundtrip Markdown GFM/bảng/long reading [S03], [S12]. | Trung bình |
| Provenance + related + timestamp | **1–3 / 15** | API có create/updateTime và version text; chưa chứng minh source locator/backlinks/capture history [S12], [S26]. | Trung bình–thấp |
| Android/Windows/offline | **6–8 / 10** | Android và Windows browser, offline Android; offline PC không có [S08], [S22]. | Cao cho nền tảng, thấp cho conflict |
| Portability/backup | **4–6 / 10** | Takeout rộng nhưng không bảo đảm import structured Markdown/asset/relationships [S24], [S17]. | Trung bình |
| Integration/cost/maintenance | **3–5 / 10** | Note cơ bản dễ dùng, nhưng API enterprise, AI bị điều kiện, lock-in dịch vụ [S18], [S14]–[S16]. | Trung bình |
| **Tổng** | **37–54 / 100** | Khoảng điểm quyết định, **không phải benchmark thực nghiệm hay số đo product quality**. | Trung bình–thấp |

**Hai kết luận độc lập:** (1) **Thay toàn bộ hệ thống: không khuyến nghị** ở trạng thái nguồn hiện nay. (2) **Giá trị học UX: cao** ở quick capture, pin/màu/labels, voice-first interaction, OCR nhanh, reminder và widgets; phải chọn tính năng theo nhu cầu và bằng chứng acceptance, không copy kiến trúc đóng.

## 6. Sáu ý tưởng đáng mượn, độ khó/phụ thuộc, acceptance

| Ý tưởng | Hình thức, mức | Phụ thuộc cụ thể | Acceptance có thể đo | Rủi ro / ranh giới |
| --- | --- | --- | --- | --- |
| **I01. Quick capture “ghi là lưu”** | UX **S** | Sửa riêng CaptureScreen, giữ POST /captures + request key. | Trên Android/Windows, mở màn hình tạo note từ shortcut đến receipt **≤2 thao tác chủ ý** (sau login); ở 20 note tiếng Việt, 20/20 nhận đúng receipt và raw text. | UI phải nói rõ “Đã tiếp nhận”, không “Đã lưu video”; không đổi API. |
| **I02. Pin/màu nhấn mạnh + thẻ triage** | UX/backend adapter **M** | Item.favorite hiện có; bổ sung màu hiển thị/lựa chọn nếu có yêu cầu thực; không nhân schema chỉ để giống Keep. | 100 Item sample: pin lên đầu và lọc favorite, thay màu không ảnh hưởng note/assignment; thao tác bàn phím và contrast đạt WCAG AA. | Màu không thay nhãn chủ đề; không đồng bộ nhãn Keep vào taxonomy. |
| **I03. Share shortcut Android / link preview an toàn** | UX/integration **M** | Đã có PWA share_target [C04], parser [C05]; cần HTTPS/thiết bị Android thật. | Share 20 URL + 10 đoạn Unicode từ 3 app được hỗ trợ, nhận đúng 30/30 event, không tạo double event khi retry key; đo click-count và fail modes. | Share sheet có thể không xuất hiện theo trình duyệt/OS; tách preview link khỏi trích xuất content, chặn SSRF. |
| **I04. OCR ảnh theo yêu cầu** | Adapter/worker **M** (hoãn nếu chưa ưu tiên) | Asset + DerivedContent đã có; chọn OCR provider sau benchmark ảnh Việt, không gọi Keep API. | 20 ảnh tiếng Việt với ground truth: đo CER/WER, lưu source_locator, source/version, lỗi thành partial; original và user note không bị sửa. | Privacy, quota, OCR hallucination; **không tự suy video đã có nội dung**; không thêm hàng loạt khi chưa có nhu cầu. |
| **I05. Voice inbox nhiều ý (học UX Keep Live)** | PoC UX + ASR/service **L** (sau P0) | Dựa ASR theo yêu cầu sẵn có, cần mic permission, tách câu/nhóm có giám sát, chỉ khi có opt-in rõ. | 10 đoạn tiếng Việt nhiều chủ đề; preview note/ý mới, người dùng xác nhận trước khi sửa bài cũ; 0 overwrite curated note; gắn audio/time nếu lưu. | Keep Live có điều kiện tài khoản [S15], không mượn API/giọng nói độc quyền; chi phí và truyền dữ liệu nhạy cảm. |
| **I06. Reminders gắn note (tùy nhu cầu)** | UX **S–M**, ưu tiên thấp | Mô hình deadline và trigger riêng nếu thật sự cần, không bắt tích hợp Tasks từ đầu. | Nhắc 1 lần/lặp, múi giờ UTC+7 và trạng thái hoàn thành rõ; disable không làm mất note; test restart/timezone. | Không bê cơ chế location reminder cũ đã ngừng [S11]; nếu có tích hợp Google Tasks cần OAuth/scopes và test thật. |

**Đề xuất thứ tự:** I01 và I03 trước (tối ưu capture đang có); chỉ triển khai I02 khi người dùng thật dùng pin/màu; I04–I06 là PoC có điều kiện. **Không thêm thư viện/SDK chưa đánh giá license, không viết lại Django/PostgreSQL, không tự bật dịch vụ gửi nội dung cá nhân sang AI.**

## 7. Quyết định, phản chứng, bước kiểm chứng

**Quyết định hiện tại: THAM KHẢO UX, sau đó PoC nhỏ**. Không áp dụng như kho lưu dữ liệu trung tâm; không dùng Google Keep REST API trực tiếp cho tài khoản cá nhân cho đến khi có tài liệu chứng minh scope/phương thức phù hợp. Không tự kết nối Google Keep của người dùng hoặc thay đổi dữ liệu. Google Drive vẫn là kho file, PostgreSQL là chỉ mục/nghiệp vụ, backend hiện hữu xử lý receipt + source/provenance.

**Phản chứng có thể đảo chiều:** nếu Google cung cấp API consumer chính thức với quyền scope hạn chế, import/export Markdown + full asset + mapping ID được kiểm thử, tree/many-to-many + history nguồn, media page/timestamp; và thử với 10.000 note/500 GB đạt được các SLA đo rõ, lúc đó **đánh giá lại lựa chọn tích hợp/thay thế**. Nếu chỉ Keep Live tiếng Việt cho voice hiệu quả, thay đổi **ưu tiên I05**, không tự suy thành lý do bỏ toàn hệ thống.

**Nghiệm thu còn thiếu, tuyệt đối không ghi PASS:**
- **Keep UI/Android share:** NOT_RUN vì không đăng nhập hoặc dùng thiết bị thật. Ghi thời gian/nhấp, offline conflict, 50 labels, HTML export/Takeout và OCR Việt trên tài khoản test được cấp quyền.
- **Keep Live/Gemini:** NOT_RUN vì không xác nhận entitlement/edition/language và chưa chấp thuận truyền nội dung.
- **Kho Tri Thức:** việc đọc code xác nhận tồn tại đường xử lý, **không chứng minh CI mới nhất/PASS production**, Android và 10k/500GB vẫn NOT_RUN; chứng cứ vận hành có phạm vi giới hạn ở [C16].
- **Tính khả dụng/giá tại Việt Nam:** chưa có phép thử theo tài khoản/thiết bị; không đưa giá AI cụ thể.
- **Security/lock-in:** chỉ thiết kế sản phẩm riêng bằng kinh nghiệm UX, không sao chép mã Keep, không thu thập credential, không upload dữ liệu riêng tư vào dịch vụ khảo sát.

## 8. Danh mục nguồn và dấu vết tra cứu

**Tất cả URL bên dưới đã được truy xuất hoặc xác minh nội dung qua kết quả tìm kiếm trong ngày 20/11/2026; nếu nguồn không thể tải đầy đủ thì chỉ sử dụng phần nội dung xác nhận từ kết quả.** Ngày bài nguồn được nêu khi trang công bố; không đánh đồng ngày crawl với ngày cập nhật. Các nguồn [S] chủ yếu đều do **Google** xuất bản.

### Nguồn sản phẩm / chính thức Google

- **[S01]** Google Workspace — Google Keep product: https://workspace.google.com/intl/vi/products/keep/ (truy cập 20/11/2026).
- **[S02]** Google Keep Help — Create/edit notes, Android: https://support.google.com/keep/answer/2888246?co=GENIE.Platform%3DAndroid&hl=en (truy cập 20/11/2026).
- **[S03]** Google Keep Help — Create/edit note with formatted text on computer: https://support.google.com/keep/answer/2888246?co=GENIE.Platform%3DDesktop&hl=en (truy cập 20/11/2026).
- **[S04]** Google Keep Help — Organize notes, cap 50 labels: https://support.google.com/keep/answer/6191044?co=GENIE.Platform%3DDesktop&hl=en (truy cập 20/11/2026).
- **[S05]** Google Keep Help — Search/filter and “image text available in English only”: https://support.google.com/keep/answer/2888263?hl=en (truy cập 20/11/2026).
- **[S06]** Google Keep Help — Take image notes: https://support.google.com/keep/answer/6395566?co=GENIE.Platform%3DAndroid&hl=en (truy cập 20/11/2026).
- **[S07]** Google Workspace Blog — 8 tips, “Grab Image Text” OCR (bài cũ, **không thay cho test 2026**): https://workspace.google.com/blog/productivity-collaboration/8-tips-help-you-keep-google-keep (truy cập 20/11/2026).
- **[S08]** Google Keep Help — Keep Chrome app discontinued, mobile offline vs desktop not offline: https://support.google.com/keep/faq/3316156?hl=en (truy cập 20/11/2026).
- **[S09]** Google Keep Help — Set time reminders: https://support.google.com/keep/answer/3187168?co=GENIE.Platform%3DDesktop&hl=en (truy cập 20/11/2026).
- **[S10]** Google Workspace Updates — Reminder sync to Google Tasks (14/10/2025): https://workspaceupdates.googleblog.com/2025/10/google-keep-reminders-now-saved-to-tasks.html (truy cập 20/11/2026).
- **[S11]** Google Tasks Help — Migration and **location reminders discontinued**: https://support.google.com/tasks/answer/16540694?hl=en (truy cập 20/11/2026).
- **[S12]** Google Developers — REST Note schema, create/updateTime, <20k chars for text: https://developers.google.com/workspace/keep/api/reference/rest/v1/notes (truy cập 20/11/2026).
- **[S13]** Google Keep Help — Chrome extension behavior since 05/12/2022: https://support.google.com/keep/answer/3003125?hl=en (truy cập 20/11/2026).
- **[S14]** Google Keep Help — Gemini for list/title, conditions AI Pro/Ultra or Pixel: https://support.google.com/keep/answer/14626262?hl=en-SG (truy cập 20/11/2026).
- **[S15]** Google Keep Help — Generate notes with voice / conditions Android + AI Pro/Ultra + Experiments: https://support.google.com/keep/answer/17499364?hl=en (truy cập 20/11/2026).
- **[S16]** Google Workspace Admin/Generative AI — Gemini Beta/Keep Live 31/08/2026, editions, default-off: https://knowledge.workspace.google.com/admin/generative-ai/workspace-with-gemini/turn-access-to-google-workspace-with-gemini-beta-on-or-off (truy cập 20/11/2026).
- **[S17]** Google Developers — REST Keep API methods (notes/media/permissions): https://developers.google.com/workspace/keep/api/reference/rest (truy cập 20/11/2026).
- **[S18]** Google Developers — Keep API Overview (last updated 03/09/2026), enterprise admin use, page/source licenses: https://developers.google.com/workspace/keep/api/guides (truy cập 20/11/2026).
- **[S19]** Google Play (publisher Google LLC) — Keep Android app/update 09/2026: https://play.google.com/store/apps/details?id=com.google.android.keep (truy cập 20/11/2026; mô tả app có chỗ lỗi thời về reminder vị trí, ưu tiên [S11]).
- **[S20]** Google Keep Help — Make a checklist/list: https://support.google.com/keep/answer/6395451 (truy cập 20/11/2026).
- **[S21]** Google Keep Help — Rich link previews settings: https://support.google.com/keep/answer/6358550?co=GENIE.Platform%3DAndroid&hl=en (truy cập 20/11/2026).
- **[S22]** Google Keep Help — Computer browser support: https://support.google.com/keep/answer/9050190?co=GENIE.Platform%3DDesktop&hl=en (truy cập 20/11/2026).
- **[S23]** Google Developers — OAuth Keep/Keep.readonly scopes: https://developers.google.com/identity/protocols/oauth2/scopes (truy cập 20/11/2026).
- **[S24]** Google Keep Help — Export content/attachments/labels/state: https://support.google.com/keep/answer/10017039?hl=en (truy cập 20/11/2026).
- **[S25]** Google Keep Help — Send/copy note to Google Docs: https://support.google.com/keep/answer/6320648?co=GENIE.Platform%3DDesktop&hl=en (truy cập 20/11/2026).
- **[S26]** Google Keep Help — Version history: text only: https://support.google.com/keep/answer/13820887?hl=en (truy cập 20/11/2026).
- **[S27]** Google Keep Help — Privacy/encryption/content use: https://support.google.com/keep/answer/10431250?hl=en (truy cập 20/11/2026).
- **[S28]** Google Help — Workspace Experiments Privacy Notice: https://support.google.com/keep/answer/13447401?hl=en (truy cập 20/11/2026).
- **[S29]** Google Keep Help — Delete/restore from Trash after 7 days: https://support.google.com/keep/answer/16914649?hl=en (truy cập 20/11/2026).
- **[S30]** Google Workspace Updates — rich text Keep web rollout 05/2025: https://workspaceupdates.googleblog.com/2025/05/release-notes-05-09-2025.html (truy cập kết quả tìm kiếm 20/11/2026; trang đôi lúc trả 429 nên đối chiếu [S03]).

### Bằng chứng mã Kho Tri Thức đúng baseline commit (chỉ đọc)

- **[C01]** Ingestion transaction/events/jobs: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/ingestion/services.py#L78-L183
- **[C02]** CaptureEvent unique key/time model: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/ingestion/models.py#L11-L44
- **[C03]** React capture UI/idempotency receipt: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/CaptureScreen.tsx#L14-L145
- **[C04]** PWA Android share target manifest: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/public/manifest.webmanifest#L1-L29
- **[C05]** Shared query parser: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/sharedCapture.ts#L1-L19
- **[C06]** Item status model: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/models.py#L9-L39
- **[C07]** Knowledge reading with provenance: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/read_knowledge.py#L1-L66
- **[C08]** Markdown GFM renderer: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/KnowledgeText.tsx#L1-L30
- **[C09]** Edit authored note: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/ItemScreen.tsx
- **[C10]** OrganizationService + RelatedItem conditional: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/organization.py#L104-L263
- **[C11]** Group editor + RelatedItems UI: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/ItemOrganization.tsx#L85-L139
- **[C12]** Library tree view: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/KnowledgeTree.tsx#L1-L94
- **[C13]** Breadcrumb/filter library: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/LibraryScreen.tsx
- **[C14]** M2M associations: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/models.py#L54-L180
- **[C15]** Versioned KnowledgeExport to Drive: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/storage/knowledge_export.py#L90-L150
- **[C16]** Actual state and explicitly unverified gates: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/docs/CURRENT_STATE.md

**Hồ sơ bàn giao G02:** chỉ một tệp nghiên cứu này; không sửa code, tài liệu hệ thống, backlog hay báo cáo khác. PR về main **không merge**.  
