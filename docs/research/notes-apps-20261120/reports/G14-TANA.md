# G14 — Đánh giá độc lập Tana Outliner cho Kho Tri Thức

**Ngày khảo sát và truy cập nguồn:** 20/11/2026 (UTC+7)  
**Sản phẩm:** Tana Outliner — https://outliner.tana.inc/  
**Baseline Kho Tri Thức:** cavoixanh638/kho-tri-thuc, main, commit **c97f5678a6893d7dfec2595d89c9122f05195320** (20/11/2026, 04:40 UTC).  
**Phương pháp:** đối chiếu website/hướng dẫn/changelog chính thức và source code của Kho Tri Thức; không sử dụng báo cáo của luồng khác hoặc bảng nguồn sơ bộ G00; không đăng nhập, mua gói, đưa dữ liệu cá nhân lên Tana hoặc cài extension.  
**Trạng thái kiểm thử Tana trực tiếp:** **NOT_RUN** cho toàn bộ K01–K12. Chỉ có kiểm chứng tài liệu nguồn và đọc code; nhận định tính năng có dấu “NATIVE” nghĩa là **được nhà cung cấp tài liệu hóa**, không phải kết quả chạy thực tế.

## 1. Executive summary (dưới 200 từ)

**Đề xuất: Tham khảo UX và thử PoC có chọn lọc, không thay thế toàn hệ thống.** Tana Outliner nổi bật ở mô hình tri thức node có cấu trúc, Supertags kèm trường, tham chiếu dùng lại cùng một node, live search và nhiều chế độ xem; AI autofill/voice đáng học nhưng phụ thuộc cấu hình và quota. Đây là nền tảng tổ chức/tra cứu tri thức rất mạnh, song không có bằng chứng tương đương chuỗi lưu trữ video gốc Google Drive, CaptureEvent bất biến/idempotency, chứng cứ theo trang/giây và khôi phục đầy đủ của Kho Tri Thức. Xuất Markdown/JSON có thật nhưng bản TIF2 không phục hồi mọi thứ, không chứa byte media và bỏ thời gian transcript; Android có app nhưng offline chủ yếu để tạo mới. Tana Outliner **khác sản phẩm Tana mới chuyên họp** ra mắt năm 2026. Dựa trên source hiện hành, Kho Tri Thức đã có nhiều-nhiều cho nhóm, cây thư viện, tìm kiếm có chứng cứ và export Drive có version: chỉ nên học UX/template/query, giữ nguyên Django/PostgreSQL/Drive. [S01–S04, S07–S10, S15–S18]

## 2. Danh tính sản phẩm và bằng chứng hiện hành

### 2.1. Phân biệt Tana Outliner và Tana mới

- **Tana Outliner**: sản phẩm đồ thị tri thức/outliner hiện hữu được đổi tên theo thông báo **31/03/2026** [S01].
- **Tana** (tana.inc) mới: sản phẩm tập trung meeting, briefs, gợi ý lúc họp và công việc sau họp; bài chính thức **02/11/2026** nói đây **không phải phiên bản mới của Outliner** [S02]. Những tính năng đặc thù của nền tảng họp mới không được tính là tính năng Outliner. Việc kết nối dữ liệu giữa chúng qua MCP không đồng nghĩa chung backend hay đồng nhất dữ liệu.
- **Tana Capture** cũ đã ngừng; sản phẩm thay thế là **Tana Mobile**. Không dùng trang hướng dẫn Tana Capture làm bằng chứng cho trạng thái tính năng mobile mới [S14].

### 2.2. Năng lực, giới hạn và mức phát hành

| Chủ đề | Kết quả kiểm chứng tài liệu (không phải test trực tiếp) | Mức / chứng cứ |
| --- | --- | --- |
| Node/supertag | Mọi nội dung là node; Supertags định nghĩa field/template/command. AI autofill có thể điền tiêu đề, trường, mô tả nhưng phải cấu hình, có thể loại trừ field [S05]. | **Đã tài liệu hóa**; AI có quota [S12] |
| References / graph | Copy/paste trong Outliner tạo **reference** chứ không mặc định nhân bản; “duplicate” là hành động riêng. Có liên kết/reuse node và related-content panel [S06, S07]. | **Đã tài liệu hóa** |
| Live search | Điều kiện tìm kiếm trả về tham chiếu tới node gốc, có thể đặt trong dashboard, tính lại khi mở rộng; tối đa **2.500 kết quả**; truy vấn vượt ngưỡng yêu cầu thu hẹp [S08]. | **Đã tài liệu hóa**; giới hạn số kết quả |
| Chế độ xem | Outline, Table, Cards, Lanes, List, Calendar, Tabs, Pivot; Pivot công bố **16/11/2026**, giới hạn **2.000 node**, **200 nhóm mỗi trục** [S09, S10]. | **Đã phát hành**, không suy có generic timeline |
| URL/ingestion | Dán URL tạo node liên kết. Tự lấy title/description/image trang web cần bật **Fetch URL metadata** trong Tana Labs (opt-in), ghi rõ changelog **02/11/2026** [S11]. Không có chứng cứ Outliner mặc định tải Facebook/TikTok/Shorts, lưu MP4 vào Drive hoặc hiểu ngữ nghĩa cả video từ URL. | **Opt-in / UNVERIFIED** cho video pipeline |
| Giọng nói và AI | Voice memo, meeting/transcript và AI chat/commands là tính năng công bố; AI **không hoạt động offline**; chi phí trừ credits [S05, S12, S13]. | **Đã tài liệu hóa**, không suy tương đương ASR cục bộ / chứng cứ theo timestamp |
| Windows/Android | Desktop Windows/Mac/Linux, desktop offline cho workspace cá nhân từ v1.0.50; shared workspace chỉ đọc khi cố ý offline. Android/iOS có Tana Mobile và widget; mobile có thể capture offline rồi đồng bộ, **không đọc ghi chú cũ offline** [S13, S15]. Hướng dẫn Android nói một số chức năng chưa ngang iOS [S15]. | **Đã tài liệu hóa; parity Android chưa bảo đảm** |
| Local API/MCP | Desktop chạy MCP tại **http://localhost:8262/mcp**, cần desktop mở, đọc/tìm/ghi node qua tools. Hosted MCP **https://app.tana.inc/mcp** đang **beta, yêu cầu gói trả phí**, dùng HTTP/OAuth [S16]. Có thể nối client phù hợp, nhưng không tự có quyền đọc dữ liệu ở nơi khác. | **Local: hiện hữu / Hosted: beta trả phí** |
| Input API | API HTTP **POST ghi một chiều**, token per workspace: 1 request/giây/token, tối đa 100 node/call, payload tối đa 5.000 ký tự, không đồng bộ nếu workspace hơn 750.000 node; trang pricing đặt tích hợp Input API ở Pro [S12, S17]. API Input không có GET **nhưng MCP có công cụ đọc**: hai bề mặt API khác nhau, không coi đây là mâu thuẫn. | **Đã tài liệu hóa, có hạn mức** |
| Export, nhập ngược | Markdown ZIP; JSON **Tana JSON** dùng kỹ thuật (không nhập bằng importer TIF) và **Tana Intermediate Format 2.1** nhập tạo **workspace/node ID mới**, không khôi phục view, automation, quyền, setting; transcript mất timing; chỉ link media, không sao chép byte [S18, S19]. | **Có export**, **round-trip không nguyên vẹn** |
| Dung lượng | Pricing công bố Free: **0,5 GB** file tải lên, **5 MB/file**, tối đa 3 workspace; chưa có bằng chứng nhận hàng trăm GB Google Drive làm kho gốc. [S12]. | **Giới hạn Free xác minh**; mức các gói khác phải kiểm lại |
| Giá & license | Trang giá tại lần truy cập hiển thị **Free $0, Plus $8/tháng, Pro $14/tháng**, tương ứng 500/2.000/5.000 AI credits theo gói; có chuyển đổi Monthly/Yearly nên **xác nhận kỳ thanh toán và thuế trước khi mua** [S12]. Kho code **tana-import-tools** công bố MIT cho **bộ chuyển đổi**, không phải license mã lõi Outliner [S20]. | **Giá tại ngày truy cập; mã lõi không xác nhận open source** |
| Dữ liệu riêng tư | Privacy Policy công khai có ngày cập nhật **14/02/2024**, quy định xử lý dữ liệu dịch vụ [S21]. Chưa có đánh giá độc lập về dữ liệu cá nhân, địa điểm xử lý AI, E2EE, SLA hay kiểm soát export bằng tài khoản thực. | **Tài liệu cũ/UNVERIFIED** về nhiều kiểm soát |

**Điểm cần phản biện:** Trang hỗ trợ billing [S22] từng ghi Free không có AI trong khi bảng giá [S12] và thông báo bổ sung credit Free [S23] nói có 500 credit. Khi mâu thuẫn, ưu tiên trang giá đang hiển thị cộng ngày changelog, đồng thời không khẳng định mọi AI command được mở ở Free; phân cấp truy cập tính năng và quota cần test bằng tài khoản Free, **NOT_RUN**. Hướng dẫn mobile “browse/edit” [S15] khác ghi chú khả năng chỉnh sửa Android còn tiếp tục được làm [S13]; không mặc định Android có đủ mọi thao tác iOS/desktop.

## 3. K01–K12: ma trận kiểm chứng theo quy trình G00

**Quy ước:** trạng thái là đánh giá mức hỗ trợ trong **tài liệu hiện hành**: **NATIVE**, **EXTENSION** (cấu hình/thêm tích hợp), **CUSTOM_BACKEND** (cần mã riêng), **NOT_SUPPORTED**, **UNVERIFIED**. Mọi dòng có trạng thái thực hành **NOT_RUN** vì không có môi trường Tana đăng nhập; “tái thử” là hướng dẫn kiểm thử sau này, **không phải kết quả đã chạy**. Các yêu cầu ghép nhiều điều kiện chỉ được gọi hỗ trợ một phần nếu nhà cung cấp chỉ chứng minh một phần.

| Ca | Kết luận hỗ trợ tài liệu | Nguồn | Cách tái thử + khoảng trống chứng cứ |
| --- | --- | --- | --- |
| **K01** Gõ ngay note tiếng Việt, có receipt/giờ | **NATIVE** cho tạo note, **UNVERIFIED** cho receipt và thời điểm server bất biến | [S13, S15] | Tạo “Biên bản cuộc họp ở Hải Phòng” trên Android và Windows; ngắt mạng/gửi lại; kiểm UI/đồng bộ/giờ server. Không có bằng chứng Tana cung cấp receipt bất biến kiểu CaptureEvent. **NOT_RUN** |
| **K02** URL video/web → metadata + nội dung | **EXTENSION** cho webpage metadata khi bật Labs; **UNVERIFIED** cho fetch nội dung video | [S11, S15] | Gửi 1 URL HTML và 1 video công khai; kiểm title/description/thumbnail, full text phụ đề, asset và file gốc; không suy AI hiểu video từ metadata. **NOT_RUN** |
| **K03** gửi URL trùng ngày khác, tách sự kiện khỏi retry | **UNVERIFIED** | [S06, S17] | Cùng URL gửi 2 ngày, rồi retry request cùng key; tìm 2 lịch sử nhận khác nhau, một Item chuẩn và timestamp riêng; docs không chứng minh idempotency/immutable event. **NOT_RUN** |
| **K04** Markdown, bảng, link, Unicode, round-trip không mất | **UNVERIFIED** cho yêu cầu *toàn vẹn*; editor/Markdown export có tài liệu | [S18, S24] | Dùng fixture NFC/NFD tiếng Việt, bảng GFM, code/URL; nhập–xuất–nhập, so text byte/AST, links, table, node IDs. Không suy kiểu editor node = giữ nguyên Markdown file. **NOT_RUN** |
| **K05** tự gán **nhóm đã có** | **EXTENSION** với Supertags + AI command cấu hình; **UNVERIFIED** cho tự gán đúng trong bộ nhóm có sẵn | [S05] | Lập 10 nhóm cố định, nộp 30 bài không rõ; đo true/false assignments và bảo vệ nhóm đã user pinned; không coi autofill fields là auto-group. **NOT_RUN** |
| **K06** mục liên quan ở cạnh bài/backlinks | **NATIVE** cho reference/backlinks/panel; **UNVERIFIED** tự phát hiện semantic tương tự | [S06, S07] | Chèn node A vào B bằng reference, sửa A, xác nhận B phản chiếu; thêm bảng related; đánh giá có lý do và liên kết nguồn hay không. **NOT_RUN** |
| **K07** PDF/audio/video → locator trang/giây | **UNVERIFIED** | [S19, S25] | Gắn PDF 20 trang và audio/video có câu ở 01:23; bấm trích dẫn nhảy đúng trang/giây; xuất TIF2 xem có mất timing (docs xác nhận *có mất*). **NOT_RUN** |
| **K08** một mục nhiều ngành; tree/table/card/timeline | **NATIVE** cho reuse references và các view Table/Cards/Calendar/Outline; **UNVERIFIED** cho timeline tổng quát | [S06, S09, S10] | Một node vào hai outline khác nhau không nhân byte; chuyển 4 view, xác nhận cùng identity; lịch theo ngày khác với timeline video. **NOT_RUN** |
| **K09** Windows + Android; offline và xung đột | **NATIVE** cho Windows offline và mobile capture offline; **NOT_SUPPORTED** cho đọc ghi chú cũ offline trên mobile tại ngày khảo sát | [S13, S15] | Windows edit offline, Android capture offline; đồng bộ 2 máy khi nối lại; kiểm conflict, voice/upload queue. Shared workspaces offline bị giới hạn, nguy cơ ghi đè sau reconnect. **NOT_RUN** |
| **K10** API/Markdown/assets/backup/exit | **NATIVE** cho MCP, Input API, export MD/TIF2; **NOT_SUPPORTED** cho round-trip hoàn chỉnh bằng TIF2 | [S16–S19] | Export workspace đầy đủ, download media, nhập vào workspace mới, đối chiếu node/refs/views/automations/transcript offset/assets; phân biệt Tana JSON và TIF2. **NOT_RUN** |
| **K11** AI có căn cứ, tách gợi ý với sửa user, quyền/chi phí | **NATIVE** cho AI autofill/chat/transcription **có credits**; **UNVERIFIED** cho nguồn chứng cứ/audit và chống ghi đè | [S05, S12, S16] | Gợi ý điền field từ 5 tài liệu VN; yêu cầu citation tới đoạn nguồn; từ chối và kiểm dữ liệu gốc không đổi, log credit/role, kiểm quyền. **NOT_RUN** |
| **K12** trên 10.000 item, hàng trăm GB video qua Drive | **UNVERIFIED** | [S08, S09, S12, S17–S19] | Sinh 10.001 node không chứa nội dung riêng, đo tìm kiếm/render/API/export/restore; test 500 GB Drive chỉ trong sandbox được phép. Không coi ngưỡng 750k node của Input API là benchmark, cũng không coi 0,5 GB Free là bằng chứng gói trả phí đáp ứng 500 GB. **NOT_RUN** |

**Tổng số ca có test Tana trực tiếp:** 0/12; **NOT_RUN:** 12/12; không đưa chỉ số K01–K12 thành “PASS”. Ngay cả khi tài liệu hóa NATIVE, yêu cầu nghiệm thu phải chạy ca trên đúng Android/Windows, gói dịch vụ và bộ dữ liệu tiếng Việt.

## 4. So với code đang tồn tại của Kho Tri Thức (không so với kế hoạch)

Đối chiếu trực tiếp tại main SHA ở đầu báo cáo; tài liệu **docs/CURRENT_STATE.md** bổ sung bối cảnh Windows/Drive nhưng các khẳng định kỹ thuật dưới đây chủ yếu bám source. Đây **không phải** cuộc chạy lại CI hoặc đo chất lượng dữ liệu cá nhân.

| Nghiệp vụ | Evidence code Kho Tri Thức hiện có | Tana đem lại gì; khoảng trống thực |
| --- | --- | --- |
| Capture URL/text/file + receipt | **apps/web/src/CaptureScreen.tsx** nhận link/Markdown/file và hiển thị giờ server; **apps/backend/ingestion/models.py**, **services.py** giữ CaptureEvent, idempotency key và source; media jobs trong **apps/backend/processing/**. | Tana có capture rất nhanh/voice/mobile widget [S15], đáng học UX; **không chứng minh** thay thế event ledger/source identity/Google Drive ingest. |
| Bài văn bản và nguồn | **apps/backend/catalog/models.py** có Item UUID, Source canonical_url và metadata; **apps/web/src/KnowledgeText.tsx**, **KnowledgeReading.tsx** đọc Markdown, bảng, liên kết, phần trích có locator và cảnh báo thiếu transcript. | Tana mạnh ở gõ outline và reference [S06, S24]; yếu thế nếu coi bài dạng tài liệu Markdown dài/bảng và media citation là nguồn chuẩn; chưa có đo Unicode roundtrip. |
| Phân nhóm đa chiều | **ItemTopic/ItemProject/ItemTag** many-to-many, user_pinned, origin auto/user; **catalog/organization.py** tự thử gán vào nhóm tồn tại có provenance/version. | Supertags/field schemas có UX điều khiển dữ liệu mạnh [S05]; **cải thiện**, không cần thay Item/Topic/Project/PostgreSQL. Chất lượng auto-group hiện tại **chưa được benchmark dữ liệu cá nhân**. |
| Cây tri thức | **catalog/knowledge_tree.py** và **apps/web/src/KnowledgeTree.tsx** lưu cấu trúc kho con/lĩnh vực/sách/chương/nhánh, nhiều bài trong nhiều nhánh. | Tana có reference reuse trực quan hơn [S06], đa chế độ xem [S09]. Ý tưởng tăng UI thay vì thay model. |
| Quan hệ & tìm kiếm chứng cứ | **catalog/models.py/RelatedItem**, **ItemOrganization.tsx/RelatedItems**, **search/services.py** trả snippet, locator, provenance; điều kiện sinh related qua provider/threshold, không có bảo đảm semantic AI. | Live searches/panels [S07, S08] là hình mẫu dashboard; không đánh đồng related panel Tana với auto-discovery, hay coi Kho Tri Thức đã có semantic retrieval toàn diện. |
| Drive + bản xuất | **storage/knowledge_export.py** viết bản MD/TXT được opt-in, so SHA, cập nhật cùng ID; **storage/drive.py** và data model Asset/StorageLocation giữ tệp gốc tách biệt. **CURRENT_STATE** ghi báo cáo pilot; không suy test hàng trăm GB. | Tana hỗ trợ export Markdown nhưng không gói media bytes trong ZIP, TIF2 mất timeline/metadata [S18, S19]; không đủ thay backup có map file/ID/version. |
| Windows/Android | UI React/PWA tồn tại; **CURRENT_STATE** có bằng chứng Windows, nhưng Android device và full offline **chưa nghiệm thu**. | Tana chứng minh bản desktop offline và mobile capture [S13]; đây là **benchmark UX**, không phải xác nhận Kho Tri Thức chạy mobile tốt hay Tana hỗ trợ offline mobile đủ. |
| AI và trích xuất | Có source extraction/worker/transcript trong **processing/** và DerivedContent; ghi chú user tách với AI; trạng thái từng nguồn khác nhau. | Tana AI autofill là mẫu workflow [S05]; không suy có tự nhận dạng tài liệu PDF/MP4 gốc với chứng cứ trang/giây đầy đủ. |

**Khác biệt kiến trúc:** Tana tổ chức dữ liệu chủ yếu thành node+refs+supertags. Kho Tri Thức cần **Item/CaptureEvent/Source/Asset/StorageLocation/DerivedContent/Job** riêng để giữ lịch sử bất biến, media gốc, tiến trình và quyền sửa của người dùng. Chuyển toàn bộ thành node có nguy cơ làm mất các phân biệt này. Không đề nghị thay Django 5.2, PostgreSQL, Google Drive hoặc triển khai Tana MCP như một phụ thuộc runtime của Kho Tri Thức.

## 5. Đánh giá người dùng cá nhân Việt Nam

- **Tiếng Việt và soạn thảo:** có thể nhập tiếng Việt theo editor tổng quát, nhưng chưa trực tiếp test IME Unikey/EVKey, dấu tổ hợp NFC/NFD, paste từ Word, bảng Markdown, tự động lưu và export Unicode. Không công bố “PASS tiếng Việt”. Với văn bản pháp lý hoặc ghi chú dài, kiểu outline node có thể làm mất cấu trúc/nhịp đọc một bài viết; đánh giá bằng tài liệu thật có quyền sử dụng, không dựa quảng cáo.
- **Android + Windows:** capture bằng widget/voice và desktop outline keyboard là điểm hay; Android offline không mở được ghi chú cũ; các thao tác Android có thể chưa ngang iOS [S13, S15].
- **Nguồn và timestamp:** Outliner có voice/transcription nhưng export TIF2 bỏ mốc transcript [S19]. “URL có metadata” ≠ “đã tải file gốc” ≠ “đã có toàn văn/ASR” ≠ “AI hiểu video”; mỗi trạng thái cần thấy rõ.
- **Riêng tư:** không đưa dữ liệu cá nhân, tài liệu cơ quan, media riêng tư vào workspace Tana chỉ để benchmark. Các thao tác MCP có quyền ghi; phải xét permission/OAuth và kiểm audit nếu quyết định thử tích hợp. Privacy policy [S21] không thay cho đánh giá bảo mật cụ thể.
- **Chi phí:** điểm mạnh giao diện bị đánh đổi bởi dịch vụ thuê bao/AI credits; việc dùng Drive đang có để giữ media gốc là quyết định kinh tế khác biệt. Không giả định giá ổn định hoặc dùng gói Free làm kho video [S12].

## 6. Chấm bảy trụ (ước lượng từ tài liệu, không phải benchmark)

**Thang:** khoảng điểm biểu thị phần hỗ trợ đã được chứng minh, mức bất định cho các ca không thử. **UNVERIFIED không bị tự động chấm 0**. Tối đa 100; khoảng cộng theo công thức tổng cận dưới và tổng cận trên, không quy đổi thành điểm chính xác.

| Trụ | Khoảng / tối đa | Lý do | Tin cậy |
| --- | ---: | --- | --- |
| Capture + ingestion | **12–15 /20** | text/voice/web/desktop/mobile tốt; URL metadata opt-in, chưa có bằng chứng downloader/video Drive, receipt/idempotency [S11, S13–S15]. | Trung bình |
| Organization + recall | **15–18 /20** | Supertag, refs, live queries, đa view mạnh; auto-group có bảo vệ pinned vẫn phải thử [S05–S10]. | Trung bình–cao |
| Text editor + reading | **7–10 /15** | outline mạnh, code document có thêm; roundtrip Markdown/GFM/IME Việt/đọc tài liệu dài chưa được đo [S18, S24]. | Trung bình |
| Provenance/related/timestamps | **4–7 /15** | references/related live; thiếu bằng chứng locator PDF/video và TIF2 mất transcript timing [S07, S19]. | Thấp–trung bình |
| Android/Windows/offline | **6–8 /10** | desktop personal offline, mobile capture offline; mobile không đọc note cũ offline; Android parity chưa đầy đủ [S13, S15]. | Cao cho giới hạn, trung bình cho UX |
| Portability + backup | **4–6 /10** | MD/TIF2 export có thật, nhưng byte media không kèm, roundtrip lossy, có rủi ro xuất workspace lớn [S18, S19]. | Cao cho giới hạn, thấp cho test restore |
| Integration/cost/maintainability | **5–7 /10** | local MCP miễn phí, hosted MCP beta trả phí, Input API write-only/rate limits/Pro, credits và storage [S12, S16, S17]. | Trung bình |
| **Tổng (không phải đo hiệu năng)** | **53–71 /100** | 12+15+7+4+6+4+5 = **53**; 15+18+10+7+8+6+7 = **71**. | **Không đủ bằng chứng để xếp hạng tuyệt đối** |

**Kết quả A — nếu thay toàn bộ Kho Tri Thức:** **không đề xuất thay** do thiếu chứng cứ đạt K02/K03/K07/K10/K12, có tổn thất chắc chắn ở đường export TIF2, và không còn lấy Drive làm nguồn file gốc. Đây là kết luận phù hợp **use case**, không phán xét chất lượng Tana như app ghi chú.

**Kết quả B — giá trị học/tái sử dụng:** **cao** cho reference reuse, Supertags, live search, multi-view và capture nhẹ; **trung bình** cho AI workflow, cần kiểm soát dữ liệu/chi phí. Điểm học không bị trừ vì Tana không làm video downloader — vì đó là nhu cầu hệ thống khác.

## 7. Năm ý tưởng có thể áp dụng: phạm vi, phụ thuộc, acceptance

| ID / độ khó | Ý tưởng UX/technical/adapter | Phụ thuộc & rủi ro | Điều kiện nghiệm thu đo được |
| --- | --- | --- | --- |
| **T14-01 / M** | **“Loại bài” dạng Supertag nhẹ:** cho người dùng tạo mẫu field cho Bài tri thức/Nguồn video/Sách/Chương, gợi ý field dựa loại mục; lớp metadata bên cạnh Item, không thay schema lõi bằng graph. | Cần thiết kế giới hạn số field và schema/version; tránh biến mọi bài thành form. | 3 mẫu; 30 bài tiếng Việt; áp mẫu/xóa mẫu không sửa note/Source/CaptureEvent; export/restore giữ field mapping 30/30. |
| **T14-02 / M** | **Saved searches/collection sống:** lưu filter của SearchService theo chủ đề/project/date, hiển thị ở sidebar/dash; tìm lại theo query và chứng cứ, không tạo bản sao Item. | SearchService hiện có, phân quyền owner; query nặng phải page/rate-limit; không sao chép định nghĩa DSL của Tana. | 5 saved views với 10.000 Item fixture, mỗi trang ≤50 Item, phân trang không trùng, thay tag thì view cập nhật, không leak owner khác. |
| **T14-03 / S–M** | **Panel “Liên quan ngay cạnh bài”**: RelatedItem hiện có hiện tiêu đề, lý do, nguồn/locator, đường mở bên cạnh và nút bỏ đề xuất; bố cục thu gọn trên Android. | Dùng RelatedItem/Source evidence; không phát sinh “AI kết luận video” khi chỉ metadata; kiểm stale version. | 20 cặp liên kết fixture: click đúng Item 20/20; reason/provenance có nguồn; dismissed không tự mọc lại; sửa nội dung đánh dấu stale theo version. |
| **T14-04 / M** | **Một tập ID, nhiều chế độ xem**: tree/list/table/cards/calendar, giữ bộ lọc, state, quyền và pagination; chế độ xem là biểu diễn, không phải bản copy Item. | React UI, cùng ItemTopic multi-path; cần WCAG, hiệu năng 21–24 inch 1080p và Android; calendar dùng saved_at/published_at rõ ràng. | 1 Item ở 2 lĩnh vực vẫn 1 UUID/1 source; đổi 4 view không mất filter; tổng theo distinct Item; kiểm 390/768/1920 viewport trong browser thực. |
| **T14-05 / M–L** | **AI đề xuất điền field, không tự ghi đè**: quyền opt-in mỗi nguồn, hiển thị giá/credits nếu gọi API; proposal gồm claim + câu trích + locator + model/version + nút Duyệt/Bỏ. | Chỉ áp sau đủ quyền chia sẻ, benchmark parser; hạn mức/timeout; không thêm vector DB hoặc dịch vụ mới ngay. | 30 ca gán nhãn: 100% đề xuất có nguồn hoặc nhãn “không đủ bằng chứng”; mọi thay đổi user phải qua duyệt, 0 overwrite của note pinned; xác nhận log không lộ dữ liệu nhạy cảm. |

**Ưu tiên nếu được giao triển khai sau nghiên cứu:** T14-03 và T14-02 (lợi ích tức thì trên code sẵn có), rồi T14-04, T14-01; T14-05 chỉ khi có corpus/nguồn và ngân sách được phép. Đây là **ý tưởng**, **không sửa code** trong PR G14. Không chép source của Outliner; nếu tham khảo công cụ import MIT, giữ tuân thủ license riêng và chỉ sau đánh giá bảo mật.

## 8. Giới hạn/rủi ro, phản chứng và điều kiện đảo chiều quyết định

1. **Dữ liệu thoát nhà cung cấp không toàn vẹn:** Markdown ZIP chỉ có link media; TIF2 mất view/automation/permission và timing transcript; “có export” **không đủ** để đáp ứng backup/restore có bằng chứng [S18, S19].
2. **Chi phí + kho lưu trữ:** Free 0,5 GB/5 MB-file; không có tài liệu xác nhận 500 GB Drive có thể làm nơi giữ file gốc trực tiếp cho Outliner; API/AI có cấp gói/hạn mức [S12, S17]. Cần tổng chi phí 12 tháng và chi phí thoát.
3. **Tính đúng nguồn:** URL metadata và graph relation không tương đương ingest/download/transcript/search video; thiếu locator timestamp chuẩn khi export [S11, S19].
4. **Android/offline/conflict:** offline Android chưa đọc notes cũ; desktop shared offline có cảnh báo sửa đồng thời ghi đè [S13, S15].
5. **Quy mô:** live-search 2.500 node, pivot 2.000, export lớn có thể thiếu RAM/CPU; không được suy 10.000 Item+500 GB hoạt động tốt chỉ từ quy mô node được nêu [S08, S09, S18].
6. **Vendor/API/security:** hosted MCP beta/paid; Input API chỉ POST 1 req/s 100 node/5.000 chars, node có thể khác UUID trong khi import; không có kiểm thử trực tiếp quyền và log AI [S16, S17, S19, S21].
7. **Khả năng học/UX:** Outliner với schema/supertags có đường cong học cao (bản thân thông báo Tana mới nói đến rào cản học Outliner [S01, S02]); không ép người dùng tạo field hay command cho mọi ghi chú.

**Phản chứng quan trọng, nếu đúng thì phải thay kết luận:** Có triển khai chính thức/được phép dùng Tana Outliner với (a) ghi API/read+write idempotent và event nhận bất biến; (b) giữ file gốc trực tiếp trong Drive có checksum và backup phục hồi qua format công khai không mất schema, audio timing; (c) Android đọc/chỉnh sửa offline đầy đủ; (d) so được >10.000 Item+500 GB trên hai nền tảng với số đo; (e) tổng chi phí thấp hơn hoặc ngang hệ đang dùng; và (f) test nguồn tiếng Việt K01–K12 thực tế đạt ngưỡng. Hiện **chưa có đủ bằng chứng** cho bộ điều kiện này; không kết luận Tana “không bao giờ làm được”.

**Quyết định đề xuất trong phạm vi G14:** **Tham khảo UX** là lựa chọn mặc định; **Thử PoC** riêng cho saved search/related panel sau khi G00 chọn ưu tiên. **Không áp dụng** phương án thay toàn bộ/nhập dữ liệu thật lên Tana. **Không tích hợp thư viện hay sản phẩm Tana vào runtime** ở giai đoạn này.

## 9. Danh mục nguồn tra cứu — truy cập 20/11/2026

Tất cả URL dưới đây được mở/đối chiếu ngày **20/11/2026**; ngày “công bố” chỉ ghi khi nguồn ghi rõ. Nguồn [S01]–[S19], [S21]–[S25] là nhà cung cấp; [S20] là kho GitHub của nhóm phát triển dành cho import tool. Không sử dụng kết luận của luồng độc lập khác.

| Mã | Nguồn, ngày công bố nếu có | URL |
| --- | --- | --- |
| S01 | Tana, *The next chapter*, **31/03/2026** | https://outliner.tana.inc/blog/the-next-chapter-for-tana |
| S02 | Tana, *How Tana differs from Tana Outliner*, **02/11/2026** | https://outliner.tana.inc/blog/how-tana-differs-from-tana-outliner |
| S03 | Trang sản phẩm Outliner | https://outliner.tana.inc/ |
| S04 | Tana, tài liệu tổng thể về Outliner features | https://outliner.tana.inc/learn |
| S05 | Supertags, AI autofill, command workflows | https://outliner.tana.inc/learn/features/supertags |
| S06 | Node & references | https://outliner.tana.inc/learn/features/nodes-and-references |
| S07 | Related content / panels | https://outliner.tana.inc/learn/features/related-content |
| S08 | Search nodes, live searches và giới hạn 2.500 kết quả | https://outliner.tana.inc/learn/features/search-nodes |
| S09 | Views, Pivot 2.000 node & 200 groups | https://outliner.tana.inc/learn/features/views |
| S10 | Changelog **16/11/2026** Pivot + Android link fix | https://outliner.tana.inc/changelog/2026-11-16-pivot-tables-and-faster-autocomplete |
| S11 | Changelog **02/11/2026** code documents và opt-in URL metadata | https://outliner.tana.inc/changelog/2026-11-02-code-documents |
| S12 | Pricing, giới hạn Free, giá/credits và plan Pro | https://outliner.tana.inc/pricing |
| S13 | Help: mobile/desktop, offline, Android limitations | https://outliner.tana.inc/help/mobile-and-desktop |
| S14 | Tana Capture đã deprecated, thay Tana Mobile | https://outliner.tana.inc/learn/features/tana-capture |
| S15 | Tana Mobile Android/iOS và widgets | https://outliner.tana.inc/learn/features/tana-mobile |
| S16 | Local API/MCP & hosted MCP beta | https://outliner.tana.inc/learn/features/local-api-mcp |
| S17 | Input API: endpoint, POST-only, 1req/s, 100 nodes, 5.000 chars | https://outliner.tana.inc/learn/features/input-api |
| S18 | Copy/paste, Markdown/JSON export | https://outliner.tana.inc/learn/features/copy-paste-and-export |
| S19 | Tana Intermediate Format 2.1, importer và những dữ liệu mất | https://outliner.tana.inc/learn/features/tana-intermediate-format |
| S20 | Repository **MIT** dành riêng cho import tools/format, không phải mã lõi app | https://github.com/tanainc/tana-import-tools |
| S21 | Privacy Policy (trên trang ghi cập nhật **14/02/2024**) | https://outliner.tana.inc/privacy |
| S22 | Billing/Account Help (nội dung Free AI có thể cũ hơn Pricing) | https://outliner.tana.inc/help/billing-and-account |
| S23 | Blog chính thức thông báo Free có 500 AI credits từ **01/10/2025** | https://outliner.tana.inc/blog |
| S24 | Outline editor và thao tác node | https://outliner.tana.inc/learn/features/outline-editor |
| S25 | Getting started / Export workspace (video/image bytes không đi kèm) | https://outliner.tana.inc/help/getting-started |

## 10. Bằng chứng phạm vi, checkpoint, tái lập và bàn giao G00

- **Đã thực hiện:** đọc trực tiếp INDEX, G00-PROTOCOL, G14-TANA, MASTER_PLAN, ARCHITECTURE_AND_DATA, CAPTURE_AND_ORGANIZE, CURRENT_STATE của **main**; đọc code actual như bảng mục 4; kiểm chứng hướng dẫn + changelog + pricing + GitHub import tool. Không đọc G00-INITIAL-SOURCES hoặc G01–G17 reports.
- **Không thực hiện:** không đăng nhập tài khoản Tana, chưa dùng app Android/Windows, chưa nhập dữ liệu thử, không chạy đo UI/benchmark, không chạy CI (PR chỉ là nghiên cứu Markdown). **Tana UI 12/12 NOT_RUN; integration 12/12 NOT_RUN**.
- **Điều cần kiểm sau:** 12 ca K01–K12 với fixture tiếng Việt có quyền; Android real device; Offline and conflict; API token scopes+rate limit; TIF2 roundtrip + hash asset; chi phí storage plan; 10.000 item / 500GB real workload. Không ghi PASS khi chưa chạy.
- **Đường rollback:** đóng PR hoặc revert commit tài liệu; không có code/schema/dữ liệu sản xuất bị tác động.
- **Phạm vi sửa Git:** chỉ **docs/research/notes-apps-20261120/reports/G14-TANA.md**; nhánh **research/notes-20261120-g14**, PR về main, **không merge**. SHA commit và URL PR được GitHub tạo, kiểm tra ở PR; không ghi trước SHA giả vào báo cáo.
