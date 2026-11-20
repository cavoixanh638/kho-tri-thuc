# G11 — Nghiên cứu độc lập Gemini Notebook (trước đây là NotebookLM)

**Ngày đánh giá:** 20/11/2026 (Asia/Bangkok, UTC+7) · **Đơn vị nghiên cứu:** G11 · **Phạm vi:** chỉ Gemini Notebook; không tham chiếu báo cáo G01–G17 hoặc `G00-INITIAL-SOURCES.md`.  
**Baseline Kho Tri Thức:** `cavoixanh638/kho-tri-thuc` / `main` commit `c97f5678a6893d7dfec2595d89c9122f05195320` (đã đọc trực tiếp bằng GitHub connector).  
**Mức kiểm chứng:** `DOC_REVIEW` = đọc tài liệu chính thức và mã; `PRODUCT_UI_NOT_RUN`; `PRODUCT_API_NOT_RUN`; `ANDROID_DEVICE_NOT_RUN`; `LIVE_DATA_NOT_RUN`. Không đăng nhập Gemini Notebook, không thử tài khoản/quota thực, không upload dữ liệu cá nhân, không chạy kiểm thử nguồn Google.

## 1. Executive summary (dưới 200 từ)

Google đổi tên NotebookLM thành **Gemini Notebook ngày 16/07/2026**; đây vẫn là sản phẩm riêng, mạnh về nghiên cứu có nguồn, câu trả lời kèm trích dẫn dẫn tới đoạn nguồn, Fast/Deep Research, Audio/Video Overviews, tài liệu và đầu ra tương tác. **REST API và MCP đã tồn tại dưới dạng Public Preview** (không còn chính xác nếu nói “không có API”), nhưng quyền dùng API, phương thức và quota còn hạn chế. YouTube URL chủ yếu nhập **bản chép lời**, không đồng nghĩa đọc toàn bộ khung hình/âm thanh video. Không có bằng chứng sản phẩm thực hiện đầy đủ capture-event bất biến, phân biệt retry/gửi lại, kho MP4 hàng trăm GB, backup toàn vẹn và mối quan hệ một-nhiều xuyên notebook. Trong khi đó, Kho Tri Thức đã có code cho các nghiệp vụ cốt lõi và đã triển khai Windows ở một phạm vi cụ thể. **Kết luận: “Tham khảo UX”, có thể thử PoC nhỏ nếu được cấp quyền; không thay toàn bộ Kho Tri Thức.** Giá trị học tập lớn nhất là *hỏi đáp chọn nguồn + trích dẫn có thể kiểm tra*, giữ nguyên file gốc, ID và database hiện tại. Chưa có kiểm thử thật nên không tuyên bố tính năng Google hay tích hợp đạt PASS.

## 2. Phương pháp, thang bằng chứng và thông tin sản phẩm

- `NATIVE`: tài liệu chính thức xác nhận chức năng trực tiếp (không đồng nghĩa đã chạy test); `EXTENSION`: chỉ đạt một phần, cần cơ chế/ứng dụng phụ; `CUSTOM_BACKEND`: buộc giữ hoặc xây nghiệp vụ riêng tại Kho Tri Thức; `NOT_SUPPORTED`: tài liệu hiện tại chỉ rõ thiếu hoặc cách vận hành không đáp ứng yêu cầu; `UNVERIFIED`: tài liệu không đủ để kết luận yêu cầu chặt chẽ. Ký hiệu `NOT_RUN` là **trạng thái thử nghiệm** độc lập với phân loại chức năng.
- Ưu tiên văn bản Google Developers/Google Help và thông báo sản phẩm có ngày. Các trang Help cập nhật liên tục; ngày **truy cập/kiểm chứng nguồn: 20/11/2026**. Không lấy marketing làm kết quả kiểm thử. Mốc mới nhất tra được: tài liệu API quota và roadmap **cập nhật 19/11/2026** [S10], [S12].
- Kết luận dựa trên tài liệu công khai; điều **không thấy trong REST reference** không nhất thiết vĩnh viễn không tồn tại ở giao diện web. Mọi khẳng định “không có” dưới đây được giới hạn về API Public Preview hoặc về hợp đồng nghiệp vụ chưa có bằng chứng.

### 2.1. Mốc phát hành và phân tầng

| Thời điểm/khả năng | Tình trạng có chứng cứ | Điều kiện/giới hạn |
| --- | --- | --- |
| 16/07/2026: NotebookLM → **Gemini Notebook** | **Đã công bố đổi tên**; sản phẩm standalone, notebook đồng bộ với Gemini app | Tích hợp AI Mode của Search được mô tả **sắp có**, không tính là đã phát hành [S01]. |
| 06/2026, cập nhật 16/07: nghiên cứu sâu/agent, cloud computer chạy code, xuất nhiều loại tài liệu | **Phát hành theo nhóm người dùng**; giới thiệu PDF/DOCX/Markdown, CSV/JSON, XLSX/PPTX, hình/charts; không đồng nhất với khả năng export toàn bộ dữ liệu gốc | Google AI Ultra và Workspace có quyền thích hợp; lộ trình Pro không được coi tự động đã tới mọi tài khoản [S02], [S01]. |
| 09–10/2026: ghi âm di động, trò chuyện giọng nói, Interactive Learning Overview, quiz nhiều định dạng, 60s short video | **Phát hành/đang triển khai theo từng tính năng, tuổi, plan và ngôn ngữ** | Bài 15/09 ghi rõ ghi âm trong app với ngôn ngữ đầu ra **English** tại thời điểm thông báo; livestream voice có phased rollout [S03], [S04]. |
| 16/11/2026: biến nguồn thành **interactive site** | **Đang rollout toàn cầu trên web** cho 18+, gồm tài khoản Workspace; mobile **sắp có** | Một website/visualization được AI tạo không phải frontend hoặc backup của kho gốc [S05]. |
| REST API + MCP server | **Public Preview**: API tạo/lấy/danh sách/cập nhật notebook, tạo/lấy/danh sách source; MCP cho agent nhập nguồn | **Tài khoản Google cá nhân**, chưa hỗ trợ Workspace ở API, OAuth scope `notebook`, không dùng API key; phương thức truy vấn câu trả lời và tạo artifact trong API còn trong roadmap [S06]–[S09], [S12]. |
| UploadSource | **Được tài liệu API chính thức mô tả** qua endpoint upload REST, tối đa 200 MiB; phải thử trên tài khoản thật | Không hiện trong REST Discovery/generated reference hoặc MCP; có khả năng trả `501 UNIMPLEMENTED` nếu chưa được mở cho caller; không nói “API hoàn toàn không upload” [S11]. |

### 2.2. Nguồn, metadata, nền tảng, giá và quyền riêng tư

1. **Web/YouTube/audio/PDF/Drive:** giao diện web hỗ trợ PDF, DOCX, PPTX, TXT, MD, CSV, EPUB, ảnh, Google Docs/Slides/Sheets và audio; nguồn Drive nhập qua UI được tự đồng bộ định kỳ khi mở notebook và có nút sync. HTML URL chỉ lấy **text** (không nhập embedded video/hình); YouTube URL công khai có captions nhập **transcript text** (không phải pixels của video), video mới trong 72 giờ có thể chưa nhập được; nguồn video bị xóa/đặt private có thể tự biến mất khỏi notebook trong 30 ngày. Facebook/TikTok không được liệt kê như YouTube importer có hỗ trợ chuyên biệt [S13].
2. **Giới hạn:** tối đa **500.000 từ/nguồn**, **200 MB/nguồn upload**. API inline text/Markdown tối đa **1 MB**, UploadSource 200 **MiB**; Free **100 notebooks × 50 sources**, Plus **200 × 100**, Pro **500 × 300**, Ultra **500 × 600** (chỉ là quota lý thuyết, không phải benchmark 10.000 nguồn). API preview 20 CreateSource/phút/người dùng, 20 upload/phút/người dùng; quota cấp project 100 read và 100 write/phút. Các notebook độc lập, không truy vấn toàn bộ notebook cùng lúc [S10], [S13], [S14].
3. **API khác UI:** qua `CreateSource` có public HTTPS web, YouTube có captions, inline text/Markdown; `UploadSource` có danh sách MIME PDF, DOCX, PPTX, CSV, audio, image...; **không có MP4 phổ thông** trong danh sách MIME upload của API. URL Google Drive/Docs **không được API CreateSource chấp nhận**, dù UI có import Google Drive; Drive URL là mục roadmap. Public Preview API chưa expose API lấy nội dung câu trả lời, kết quả AI/artefacts, xóa source/notebook hoặc full archive [S06], [S08], [S11], [S12].
4. **Nền tảng/tiếng Việt:** web chạy trên trình duyệt Windows; Android app yêu cầu **Android 10+**, danh sách quốc gia có Việt Nam. Mobile hỗ trợ chia sẻ web/PDF/YouTube vào notebook nhưng **chưa sửa được Note**, một số kiểu nhập nguồn và tạo báo cáo/notes trên mobile bị hạn chế. Ghi âm/thuyết minh, giọng tương tác và giao diện có điều kiện ngôn ngữ riêng; tài liệu nói hỗ trợ 80+ ngôn ngữ, có Vietnamese trong danh sách tiếng audio import. **Chưa tự kiểm tra roundtrip Unicode tiếng Việt hoặc chức năng ghi âm tiếng Việt** [S15], [S16], [S17].
5. **Export/backup:** web có `Export to Docs` cho Notes và báo cáo, `Export to Sheets` cho bảng; file xuất **không sync ngược**, không kế thừa permission từ Notebook. Chat/agent có thể tạo PDF/Markdown/XLSX, nhưng không tương đương xuất manifest toàn bộ Notebook/source ID/mối quan hệ, lịch sử, bản gốc. Chưa có chứng cứ công cụ backup/restore nguyên notebook thành JSON + media + provenance và API Public Preview hiện không có phương thức này [S14], [S18], [S06].
6. **Privacy/license:** sản phẩm dịch vụ độc quyền của Google, **không có chứng cứ repo mã nguồn sản phẩm được cấp phép open-source**; API/reference không phải code ứng dụng để fork. Theo chính sách, nội dung không dùng để *trực tiếp huấn luyện foundation model* trừ khi người dùng gửi feedback; feedback có thể kéo theo nguồn, câu hỏi và output, xem xét thủ công và lưu **tới 3 năm**. Workspace đủ điều kiện có bảo đảm riêng về người review/training. Đừng gửi dữ liệu công vụ/riêng tư chưa được phép; đọc điều khoản tài khoản cụ thể trước PoC [S19].
7. **Chi phí:** Google cung cấp mức Free và các tầng Plus/Pro/Ultra, khác nhau về quota; **API miễn phí trong Public Preview** theo tài liệu ngày 19/11/2026 [S10]. Không khẳng định giá VND/tháng, thuế Việt Nam hoặc giá tương lai của API khi chưa có dữ liệu hợp đồng địa phương. Giới hạn tính năng premium có thể gây đổi chi phí giữa thử nghiệm và vận hành.

**Ranh giới then chốt:** [S13] nói YouTube URL nhập *duy nhất transcript*. [S11] nói uploaded audio có thể được xử lý, nhưng **không đủ chứng cứ** để khẳng định mô hình phân tích toàn video/khung hình theo timestamp. Video Overview là **video tổng hợp do AI tạo**, không phải “đã phân tích MP4 gốc”.

## 3. Ma trận 12 tình huống G00 — phạm vi thật và cách tái thử

**Tất cả K01–K12: thử nghiệm sản phẩm `NOT_RUN`.** Phân loại dựa trên tài liệu; mỗi ca có thao tác độc lập có thể tái hiện khi chủ sở hữu cho phép.

| Ca | Phân loại | Chứng cứ, kết luận có điều kiện | Tái thử cụ thể và điểm chưa chắc |
| --- | --- | --- | --- |
| **K01** Gõ ghi chú tiếng Việt + receipt/giờ | **CUSTOM_BACKEND** | Web có Note source, dùng để trích dẫn; API Source có `createTime` nhưng không bảo đảm receipt bất biến theo từng lần gửi [S18], [S11]. | Web tạo Note “Hải Phòng – Đường Quán Nam”; kiểm hiển thị, thời gian/tính bất biến khi sửa/reload. Không có test ACK theo hợp đồng Kho Tri Thức. |
| **K02** Gửi URL và lấy metadata/nội dung | **EXTENSION** | Web URL nhập HTML text; YouTube lấy captions; API có `originalUrl`, `displayName`, `state`; FB/TikTok/private/MP4 chưa có chứng cứ hỗ trợ ngang mức [S13], [S11]. | Tạo notebook, nhập web public + YouTube captions + URL không có captions + TikTok/FB; đối chiếu trạng thái và nội dung, không suy video vision. |
| **K03** Gửi link lại sau 1 ngày vs retry | **CUSTOM_BACKEND** | API `Source.createTime` là thời điểm tạo source, **không phải mô hình `CaptureEvent` + idempotency key**. Không thấy hợp đồng gộp Item và giữ tất cả lần gửi [S11]. | Gửi cùng URL 2 lần ở hai ngày, retry cùng key; kiểm event/receipt riêng và source không nhân đôi. Thiếu API contract này → giữ hệ thống hiện hữu. |
| **K04** Markdown + bảng + link + Unicode không mất | **UNVERIFIED** | Có MD nguồn và Note, export Docs; **chưa chứng minh** vòng nhập–sửa–xuất–nhập giữ nguyên bytes/bảng/link/Unicode [S11], [S18]. | Import UTF-8 MD có GFM table, URL, CRLF, dấu, emoji; sửa và export/reimport; so SHA/text/AST; kiểm field formatting. |
| **K05** Tự gán vào nhóm **đã có** | **UNVERIFIED** | Web có auto-label/categorize khi >=5 nguồn và chỉnh labels thủ công; không có chứng cứ guarantee dùng đúng group hiện có và bảo vệ curated assignment [S14], [S13]. | Chuẩn bị 5–10 sources + nhãn có sẵn, thêm mục thứ 11; kiểm assignment DB/nhãn hiện hữu, giải thích và undo. |
| **K06** Mục liên quan/backlink ngay cạnh bài | **EXTENSION** | Mind maps/grounded citation giúp khám phá liên quan; chưa có bằng chứng backlink cấp Item/mối quan hệ bền vững xuyên notebook như `RelatedItem` [S14], [S20]. | Tạo 3 ghi chú có liên hệ, chỉnh một mục, tìm backlinks hai chiều và lý do liên kết; kiểm khả năng quản lý thủ công. |
| **K07** PDF/audio/video + đúng trang/giây trích dẫn | **UNVERIFIED** | Chat click citation tới **đoạn trích trong nguồn**, PDF/audio được nhận; video URL nhập transcript, không xác nhận seek MP4 tới giây; khả năng locator trang/giây cụ thể phải thử thật [S20], [S13]. | 1 PDF 20 trang có anchor, 1 MP3 có câu ở 01:37, 1 YouTube có caption; hỏi rồi click cite, đo vị trí trang/giây, phân biệt transcript và frame. |
| **K08** Một bài đa lĩnh vực, tree/table/card/timeline | **NOT_SUPPORTED** *(yêu cầu trọn vẹn)* | Notebook độc lập, source labels; không có mô hình tree nhiều cha + bốn view lịch sử cho một Item thống nhất [S14]. | Tạo một nguồn ở hai domain, thử cùng ID hiển thị trong tree/table/card/timeline và lọc theo event time; xem có nhân đôi không. |
| **K09** Android + Windows, offline, xung đột | **UNVERIFIED** | Android 10+ có app, Windows web; chỉ **Audio Overview download** có chứng cứ offline rõ ràng, không có chứng cứ sửa đồng thời Note offline + conflict merge; mobile còn thiếu editor [S15], [S18]. | Android + Chrome Windows cùng sửa note khi mất mạng 10 phút; reconnect kiểm merge, không mất dữ liệu/duplicated work; thao tác native Android mới được coi PASS khi chạy thiết bị. |
| **K10** API, MD/assets import/export/backup đầy đủ | **CUSTOM_BACKEND** | REST/MCP preview thật, web export note/artefact nhưng chưa có API bulk get content/delete/restore/full archive; cần giữ backup/manifest độc lập [S06]–[S12], [S18]. | API OAuth account cá nhân; list/get notebook/source; export note; thử phục hồi toàn bộ nguồn gốc, metadata, quan hệ qua file độc lập; kỳ vọng thiếu chứ không xóa dữ liệu thật. |
| **K11** AI cite nguồn, quyền/chi phí, không ghi đè | **NATIVE** *(citation và tạo output; kiểm soát ghi đè chưa chứng minh)* | Chat có citation đến đoạn, chọn subset nguồn; agent tạo artifact; Google cảnh báo lỗi và privacy; không đồng nghĩa có write protection/approval workflow cho `Item.note` của mình [S20], [S19]. | Prompt hỏi một thông tin chỉ có ở 2/5 nguồn, kiểm citation; yêu cầu sửa note gốc, kiểm có approval và diff; thử quota ở Free/Pro nếu tài khoản được phép. |
| **K12** >10.000 items, hàng trăm GB video Drive/remote | **CUSTOM_BACKEND** | Quota notebook/source, 200 MiB/upload và notebook độc lập; một số tier có tổng slot lý thuyết >10k nhưng không chứng minh tổng hệ và không nhận MP4 nguyên bản đúng yêu cầu [S10], [S11], [S14]. | Dùng corpus *giả/synthetic* 100/1.000/10.000 source và manifest ngoài (chỉ sau duyệt quota), đo truy vấn, kiểm 300GB video trong Drive không upload vào Notebook; tránh gây tốn tiền hoặc vi phạm ToS. |

## 4. Đối chiếu mã **hiện có** của Kho Tri Thức (không dùng roadmap làm PASS)

Đã đọc trực tiếp các tệp thuộc `main` commit ở đầu báo cáo, và `docs/CURRENT_STATE.md` (báo cáo này phân biệt kiểm thử CI/live/NOT_RUN). Mỗi dòng “đã có” nghĩa là **có mã và bằng chứng trạng thái trong repo**, không ngầm khẳng định mọi tình huống đa thiết bị đã nghiệm thu.

| Năng lực | Bằng chứng trong mã/hiện trạng Kho Tri Thức | Gemini Notebook làm tốt hơn / đề xuất xử lý |
| --- | --- | --- |
| Gửi URL/text và giờ lưu | `apps/backend/ingestion/services.py`, `apps/backend/ingestion/models.py`: `submit_capture` tạo/reuse Item/Source và `CaptureEvent.server_received_at`; `apps/web/src/CaptureScreen.tsx` có receipt/idempotency. `CURRENT_STATE` đánh dấu phần tiếp nhận **PASS**. | **Đã có, giữ nguyên.** Không thay receipt bằng Source.createTime của Google. |
| Văn bản Markdown như nội dung chính | `apps/web/src/KnowledgeText.tsx` dùng `react-markdown + remark-gfm`; `ItemScreen.tsx` cho sửa note; `processing/read_knowledge.py` ưu tiên authored text. `CURRENT_STATE` ghi `KT-112 LIVE_PASS` ở phạm vi Windows, Android không chạy. | **Đã có**; học việc biến Note thành source được chọn cho hỏi đáp, không thay editor đã có chỉ bằng UI Notebook. |
| Nhóm, cây và quan hệ | `catalog/models.py` có `Topic/Project/Tag`, Assignment, `RelatedItem`; `catalog/organization.py` gán nhóm có evidence; `apps/web/src/KnowledgeTree.tsx` render cây. `CURRENT_STATE` có test/Windows proof nhưng benchmark thực tế phân loại vẫn thiếu. | **Đã có phần lõi**; Auto-label và visual mind map là tham khảo. Không chuyển sang các notebook độc lập làm kho chính. |
| Web/PDF/ASR, provenance | `processing/document_extract.py`, `processing/read_knowledge.py` và `DerivedContent.source_locator`; `transcript_job.py` có mốc giây; `CURRENT_STATE` nói ASR một Reel, 11 đoạn được test, **không** suy chất lượng hàng loạt/YouTube/TikTok. | **Cải thiện UI**: cite-chip nhảy tới đúng locator; cần test chính xác mốc. Google YouTube text-only có thể hữu ích cho nghiên cứu nhưng không thay video gốc đã lưu. |
| Drive file gốc, bản xuất tri thức | `storage/drive.py`, `storage/knowledge_export.py` giữ `provider_file_id`, version/sha; `CURRENT_STATE` có live readback/connector trên mẫu 8 Item. | **Đã có**; nếu thử Notebook chỉ nhập *bản xuất đã được phép*, tham chiếu theo `item_id`, không dịch chuyển file gốc hoặc duplicate toàn bộ. |
| Backup và tính di chuyển | `docs/operations/BACKUP_RESTORE.md`, `CURRENT_STATE` mô tả restore vào DB thử, manifest các phiên bản, giới hạn đã ghi. | **Đã có phần quan trọng** mà API Notebook chưa thay được. Không dùng “Export to Docs” như backup đầy đủ. |
| AI Q&A source-scoped, cite/research report/interactive output | Không thấy trong code `main` một giao diện chat grounded citation tương đương Notebook; tài liệu kiến trúc chỉ dành trục nâng cấp và connector pilot. | **Chưa có / đáng học:** chọn nguồn trước câu hỏi, citation-click, cảnh báo phần thiếu text, báo cáo có nguồn, interactive report optional. |
| Android thật, nhiều quy mô và phân loại tiếng Việt | `CURRENT_STATE` đánh dấu `ANDROID_NOT_RUN`, kiểm tra 10.000 Item/100GB và benchmark phân loại trên dữ liệu thực chưa đạt. | **Cả hai bên chưa có bằng chứng nghiệm thu yêu cầu**. Không chấm Notebook tốt hơn nhờ quảng cáo số người dùng hoặc quota. |

**Phân biệt source & truth:** tại Kho Tri Thức `CaptureEvent`/`Item`/`Asset`/`DerivedContent`/`RelatedItem` là hệ thống bản ghi chuẩn. Notebook chỉ thích hợp là **không gian nghiên cứu dẫn xuất**, chọn lọc theo dự án/câu hỏi, không được tái định nghĩa thời điểm lưu, quyền sửa hay bản gốc từ kết quả sinh AI.

## 5. Chấm 7 trụ (rubric G00, tổng 100)

Điểm là **ước tính năng lực dựa trên tài liệu, không phải điểm sau kiểm thử**. Bất định không tính là 0; những điểm không chứng minh được ghi rõ và biên dao động đề phòng khác biệt UI/quota.

| Trụ | Điểm tạm tính | Độ tin cậy | Lập luận chính / thiếu dữ liệu |
| --- | ---: | --- | --- |
| Capture + ingestion (20) | **13/20** | Vừa | Rất nhiều loại nguồn qua UI, share Android, API mới; thiếu hợp đồng event/retry, FB/TikTok/MP4 nhập trực tiếp, mobile hạn chế [S11], [S13]. |
| Organization + recall (20) | **12/20** | Vừa | Auto-label khi >=5, tìm nguồn, Deep Research, cite; không truy vấn nhiều notebook đồng thời, không chứng minh graph/backlink/assign curated [S14], [S13]. |
| Editor + reading (15) | **9/15** | Vừa | Notes + report/Docs, bảng, nguồn để hỏi đáp; mobile chưa sửa note, Markdown roundtrip nghiêm ngặt chưa thử [S18], [S15]. |
| Provenance/related/timestamps (15) | **9/15** | Vừa-thấp | Citation nhảy đoạn rất mạnh; thiếu bằng chứng immutable capture events, relationship graph và seek chính xác media [S20]. |
| Android/Windows/offline (10) | **6/10** | Vừa | Android 10+ và web, Việt Nam có trong danh sách; offline được công bố rõ cho Audio Overview, không xác nhận offline edit/sync conflict [S15]. |
| Portability/backup (10) | **4/10** | Vừa | Có Docs/Sheets/download artifact và API list metadata; chưa có full data+media+relation export/restore [S18], [S06], [S12]. |
| Integration/cost/maintainability (10) | **7/10** | Vừa | API/MCP thật, preview free, quota minh bạch; cá nhân-only, API missing read/artefact, vendor lock-in [S06]–[S12]. |
| **Tổng** | **60/100** | **Tạm tính; khoảng tham khảo 53–67** | Không phải tỷ lệ “PASS K01–K12”, không dự đoán giá/khả năng mở rộng sau 2026. |

**Hai kết quả tách biệt:**
- **Thay thế toàn Kho Tri Thức: KHÔNG PHÙ HỢP tại 20/11/2026** — thiếu nguồn dữ liệu chính, lịch sử nhận bất biến, file gốc dung lượng lớn, multi-parent model, portability và kiểm thử 10k video; dù score tính năng nghiên cứu là 60/100, *điểm thay thế* không được suy từ 60%.
- **Học/tái sử dụng tính năng: CAO về UX nghiên cứu** — đặc biệt grounded citation, source selection, auto-label có người kiểm soát, báo cáo có nguồn, outputs tương tác. **Quyết định tác nghiệp: “Tham khảo UX”; chỉ “Thử PoC” giới hạn khi chủ sở hữu cấp quyền và corpus không nhạy cảm.**

## 6. Đề xuất 5 tính năng áp dụng (không viết lại kiến trúc)

| # | Ý tưởng (UX) | Technical / adapter & mức độ | Nghiệm thu đo được, không suy AI đã hiểu video | Rủi ro/license |
| --- | --- | --- | --- | --- |
| **G11-P1** | Cite-chip trong câu trả lời hoặc tóm tắt → bấm để mở đúng đoạn/chương/trang/mốc thời gian, hiển thị tên nguồn và loại trích xuất | **M** — mở rộng `DerivedContent.source_locator` + API read/search hiện tại; giao diện citation viewer, không thay Postgres/Drive | 20 đoạn đã gán nhãn PDF/web/ASR, click cite đúng file và locator **>=18/20**; sai/thiếu locator hiển thị `Không xác định`, không bịa mốc; link media mở được nếu asset verified | Trích xuất lỗi khiến dẫn nguồn sai; cite không chứng minh claim đúng |
| **G11-P2** | Chọn **phạm vi nguồn** cho một phiên hỏi đáp/đọc: tất cả, chỉ ghi chú, chỉ nguồn đã chọn; thấy danh sách nguồn và thiếu text | **M** — UI source selector + read-only adapter trên `SearchService` và `ReadKnowledgeService`; backend AI tùy chọn, bật sau pilot | 9 câu hỏi x 3 mode; mỗi claim có `item_id + source_id + version + locator`, không lấy nguồn ngoài selection; 0 lần sửa `Item.note` tự động, 0 lần gửi dữ liệu tới provider khi opt-in tắt | AI gửi dữ liệu ngoài, token/quota, cần kiểm duyệt quyền và consent |
| **G11-P3** | “Nguồn có gì / chưa có gì” rõ ngay khi gửi YouTube/FB/TikTok: title/metadata ≠ transcript ≠ audio/vision | **S** — chỉ UI component trên states `source_fetch/content_extract` đã có; ghi version và lý do | 6 fixture (web text, YouTube captions, video không captions, FB MP4 không ASR, MP3 ASR, PDF scan): nhãn chính xác **6/6**, không bao giờ ghi “đã hiểu video” nếu chỉ có metadata | UX dài dòng; không được tự nhập nội dung bản quyền trái quyền sử dụng |
| **G11-P4** | Tự nhãn nguồn và gợi ý liên quan nhưng **ưu tiên nhóm đã có** và hiển thị tại sao, Cho phép Chốt/Bỏ/Hoàn tác | **M** — `OrganizationService` hiện có + evidence panel trong Item; không tạo notebook làm “nhóm mới” | Corpus 30–50 Item người gán nhãn: đo precision auto-assign **>=90%** trên các trường hợp thực hiện auto; curated group đổi ngoài ý muốn **0**; cùng nội dung/khác note không merge | Sai tiếng Việt, nguồn nghèo transcript; cần đánh giá trên dữ liệu người dùng cho phép |
| **G11-P5** | Sinh bản **FAQ/briefing theo tập nguồn** với citation, lưu thành bản nháp riêng có version và khả năng export Markdown; tương tác/voice là giai đoạn sau | **M** — service tạo `DerivedArtifact`/tệp Markdown chỉ sau bật AI, output giữ references, không tự ghi đè bài. Bắt đầu bằng template không AI hoặc provider adapter có sẵn nếu được duyệt | Tập 10 tài liệu nguồn công khai; 100% mục có pointer tới source/version hoặc đánh dấu thiếu chứng cứ; export/import UTF-8 không mất dấu; stale warning khi source version đổi; chủ sở hữu phải bấm mới áp dụng nội dung | Hallucination/chi phí. Không sao chép mã nguồn proprietary hoặc giả sản phẩm Google có SDK/giấy phép cho engine. |

**Thử PoC kết nối Gemini Notebook API (tuỳ chọn, không phải yêu cầu triển khai ngay):** chỉ đồng bộ *bản xuất Markdown đã cho phép* của 3–5 Item vào notebook cá nhân qua REST/OAuth scope `notebook`; map `item_id ↔ notebook/source_id` ở adapter, không gán Google ID làm PK; so `ACTIVE/FAILED` và quota. **Không tự lưu token vào GitHub, không dùng tài khoản Workspace (preview chưa hỗ trợ), không upload video gốc, không tự xoá dữ liệu**. Kiểm tra `UploadSource` riêng vì caller có thể gặp `501`. Nếu không có đồng ý/quyền, giữ `NOT_RUN` [S07], [S11].

## 7. Giới hạn, phản chứng và điều kiện đổi quyết định

### Rủi ro/phản chứng phải nhìn thẳng

1. **Citations ≠ fact-check:** AI có thể cite đúng đoạn mà suy luận sai; các câu hỏi không có nguồn hoặc PDF scan còn nguy cơ bịa. Bắt buộc đo grounding và có trạng thái không chắc [S20].
2. **Tính độc lập notebook:** một notebook không tham chiếu đồng thời toàn kho notebook khác, làm phân mảnh thư viện 10k+ mục và giảm recall xuyên chủ đề [S14].
3. **Ranh giới video:** YouTube URL = transcript text, FB/TikTok không có importer được bảo đảm; MP4 gốc 100GB không phải nguồn ingest phổ thông. Không lấy Video Overview làm bằng chứng hiểu file gốc [S13], [S11].
4. **API Public Preview thay đổi liên tục:** giới hạn personal account, methods, quotas, `501` upload; tài liệu có thể đi trước tính năng thực trên tài khoản, phản hồi thực tế có thể khác [S07]–[S12].
5. **Lock-in & backup:** xuất Docs/Sheets/AI artifacts không bảo toàn toàn bộ cấu trúc; các bản Docs/Sheets xuất không sync ngược, URL/permissions có thể hỏng [S18], [S14].
6. **Rủi ro privacy/copyright:** gửi nguồn công vụ/cá nhân vào AI, feedback và chia sẻ notebook có thể lộ nội dung; không thử bằng dữ liệu người dùng khi chưa được cấp quyền [S19], [S21].
7. **Đa thiết bị/tiếng Việt:** Android có tại Việt Nam nhưng editor ghi chú mobile, offline edit, xung đột chưa đáp ứng; tiếng Việt là hỗ trợ ngôn ngữ được công bố, không phải kiểm định dấu/ASR chất lượng [S15]–[S17].
8. **Chi phí và quota:** tier cao có thêm nguồn nhưng không đảm bảo hàng trăm GB và 10k active sources mượt; preview API miễn phí hôm nay không phải cam kết dài hạn [S10].

### Giả thuyết có thể bác bỏ kết luận

- **H0 hiện tại:** Gemini Notebook **không** thay được Kho Tri Thức nếu cần `CaptureEvent` bất biến, cùng một bài nhiều nhánh, MP4 gốc Drive/remote và manifest portable.
- **Phản chứng đủ mạnh để đảo chiều:** Google phát hành/cho test **API production** có event/idempotency, nguồn Drive/MP4 và metadata/version đủ dùng, full export/restore, khả năng tìm kiếm/quan hệ qua >=10.000 items/100GB, chỉnh offline Android+Windows có chống xung đột, và hỗ trợ chuyển dữ liệu nguyên vẹn với chi phí chấp nhận được. Chạy ít nhất 50 Item đối chứng rồi 1.000 và 10.000 synthetic; đối chiếu hash/locator/receipt/nhóm và restore; chấm rubric lại **sau thử nghiệm**, không trước.
- **Phản chứng ngược cho việc học tính năng:** nếu citation click tại corpus PDF/audio tiếng Việt sai >10% hoặc chat lẫn nguồn khác selection, loại bỏ P1/P2; nếu auto-label gây sai curated assignment, không auto-commit P4; nếu export không có version/portable, không đưa P5 thành bản gốc.

### Trạng thái & bước tiếp theo

- **Đã làm:** đọc toàn bộ tài liệu giao việc G11/G00, nguồn Google chính thức, hạn mức API 19/11/2026; đọc code `main` ở SHA nêu trên, lập K01–K12, rubric và ý tưởng có acceptance.
- **NOT_RUN:** đăng nhập Gemini Notebook web/mobile; OAuth API/MCP; trực tiếp thử upload/export/citation, tiếng Việt, offline, benchmark quy mô, chi phí tài khoản thật. Không có dữ liệu Google cá nhân được truy cập/ghi.
- **Không thay đổi code, không chạm docs kế hoạch, không đọc báo cáo luồng khác.** Chỉ tài liệu nghiên cứu thuộc G11 được commit. G00 có thể thẩm định và điều phối; không merge bởi G11.

## 8. Nguồn độc lập (truy cập 20/11/2026)

**Nguồn chính thức Google, ưu tiên tài liệu gốc và phát hành 2026:**

- **[S01]** Google, 16/07/2026, *NotebookLM is now Gemini Notebook*: https://blog.google/innovation-and-ai/products/gemini-notebook/notebooklm-gemini-notebook/
- **[S02]** Google, 08/06/2026, cập nhật 16/07/2026, *Do better research with NotebookLM*: https://blog.google/innovation-and-ai/products/notebooklm/better-research-notebooklm/
- **[S03]** Google, 15/09/2026, *Sharpen your study routine with new Gemini Notebook tools*: https://blog.google/innovation-and-ai/products/gemini-notebook/new-study-tools-september-2026/
- **[S04]** Google, 16/10/2026, *3 new study features*: https://blog.google/innovation-and-ai/products/gemini-notebook/three-tips-study-gemini-notebook/
- **[S05]** Google, 16/11/2026, *Interactive sites*: https://blog.google/innovation-and-ai/products/gemini-notebook/interactive-sites/
- **[S06]** Google Developers, *Gemini Notebook API* (Public Preview): https://developers.google.com/notebook/docs
- **[S07]** Google Developers, *Authentication*, personal account + OAuth scopes: https://developers.google.com/notebook/docs/authentication
- **[S08]** Google Developers, *REST Reference*, danh sách methods thực: https://developers.google.com/notebook/reference/rest
- **[S09]** Google Developers, *Remote MCP*, endpoint và tools: https://developers.google.com/notebook/docs/mcp
- **[S10]** Google Developers, *Rate limits and quotas*, **last updated 19/11/2026**: https://developers.google.com/notebook/docs/rate-limits
- **[S11]** Google Developers, *Sources*, REST `CreateSource`, `UploadSource`, MIME/limits/status: https://developers.google.com/notebook/docs/sources
- **[S12]** Google Developers, *Roadmap*, **last updated 19/11/2026**: https://developers.google.com/notebook/docs/roadmap
- **[S13]** Google Help, *Add or discover new sources* (web/YouTube chỉ text, Google Drive sync): https://support.google.com/gemininotebook/answer/16215270?co=GENIE.Platform%3DDesktop&hl=en
- **[S14]** Google Help, *Create a notebook* (notebooks độc lập, auto labels, export): https://support.google.com/gemininotebook/answer/16206563?hl=en
- **[S15]** Google Help, *Mobile app Android* (Android 10+, Việt Nam, hạn chế offline/editor): https://support.google.com/gemininotebook/answer/16296687?co=GENIE.Platform%3DAndroid&hl=en
- **[S16]** Google Help, *Learn about Gemini Notebook* (ngôn ngữ, privacy chung): https://support.google.com/gemininotebook/answer/16164461?co=GENIE.Platform%3DDesktop&hl=en
- **[S17]** Google Help, *Audio source languages and limits*: https://support.google.com/gemininotebook/answer/16215270
- **[S18]** Google Help, *Create & add notes* (Note source, export Docs, mobile không edit): https://support.google.com/gemininotebook/answer/16262519
- **[S19]** Google Help, *Privacy and Terms of Use*, feedback/retention: https://support.google.com/gemininotebook/answer/17004255
- **[S20]** Google Help, *Use chat* (grounded citations và agentic capability): https://support.google.com/gemininotebook/answer/16179559
- **[S21]** Google Help, *Public notebook sharing* (sharing caveats): https://support.google.com/gemininotebook/answer/16322204

**Đối chiếu code/tình trạng Kho Tri Thức**, chỉ `main` tại SHA ở đầu báo cáo:

- [B01] https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/ingestion/services.py
- [B02] https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/models.py
- [B03] https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/organization.py
- [B04] https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/read_knowledge.py
- [B05] https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/transcript_job.py
- [B06] https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/KnowledgeText.tsx
- [B07] https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/KnowledgeTree.tsx
- [B08] https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/storage/knowledge_export.py
- [B09] https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/docs/CURRENT_STATE.md

**License nguồn tham khảo:** tài liệu Google Developers nêu giấy phép riêng cho *documentation* (CC BY 4.0) và *code samples* (Apache 2.0); điều này **không** cấp phép fork/sao chép hệ thống Gemini Notebook. Tài liệu này trích ý và đường dẫn, không sao chép mã Google hoặc dữ liệu cá nhân.
