# G15 — Granola: nghiên cứu độc lập, đối chiếu Kho Tri Thức

**Thời điểm đánh giá:** 20/11/2026, giờ Việt Nam. **Đối tượng duy nhất:** Granola (granola.ai). **Baseline Kho Tri Thức:** nhánh main, SHA c97f5678a6893d7dfec2595d89c9122f05195320 (11:40 giờ Việt Nam, 20/11/2026). **Phạm vi ghi:** báo cáo nghiên cứu; không sửa mã, cấu hình, roadmap hoặc dữ liệu. **Nghiệm thu Granola trực tiếp:** NOT_RUN (không được cấp tài khoản Granola hoặc quyền gửi dữ liệu họp). Tài liệu chính thức được truy cập/nghiên cứu ngày 20/11/2026; thông tin thương mại và khả năng phát hành có thể đổi.

## 1. Tóm tắt điều hành (dưới 200 từ)

**Khuyến nghị: tham khảo UX của Granola; chỉ thử PoC có kiểm soát cho nguồn biên bản họp, không thay Kho Tri Thức.** Granola rất mạnh ở vòng đời cuộc họp: bắt lời nói ngay trên thiết bị, không đưa bot vào cuộc gọi, cho người dùng ghi ý chính trong khi diễn ra, tạo bản ghi chép tăng cường bởi AI và mở lại đoạn transcript làm bằng chứng cho nhận định. Đã có Windows, Android, tiếng Việt, API, MCP và webhook chính thức. Tuy nhiên sản phẩm lấy **cuộc họp** làm trung tâm, không phải kho tổng hợp URL/video/PDF với CaptureEvent, nhóm nhiều tầng, phiên bản trích xuất và Google Drive như dự án. Granola không giữ bản âm thanh sau khi phiên âm, nên khả năng nhảy về đoạn transcript **không tương đương nghe lại đúng mốc âm thanh**. Tính năng cuộc gọi qua Granola tại Việt Nam chưa có trong danh sách quốc gia hỗ trợ. Dữ liệu lưu/AI xử lý trên hạ tầng đám mây; CSV xuất thiếu một số bản ghi và không thay backup đầy đủ. Chấm mức thay thế toàn bộ **56/100 (ước lượng chuyên gia, chưa benchmark)**; giá trị học tập quy trình ghi chú, kiểm tra nguồn và mẫu biên bản **cao**.

## 2. Phương pháp, mức chứng cứ và mốc phát hành

- **Đã làm (DOC_REVIEW):** đọc INDEX, G15-GRANOLA và G00-PROTOCOL; đọc tài liệu kỹ thuật/trạng thái/main cùng các đoạn mã ứng dụng; kiểm tra website chính thức Granola, docs, pricing, API changelog, privacy, export. Không xem bảng nguồn sơ bộ G00 hay kết luận G01–G17.
- **Chưa làm (NOT_RUN):** không cài/đăng nhập Granola, không ghi âm hoặc nhập dữ liệu người dùng, không kiểm API/MCP bằng token, không đo độ chính xác tiếng Việt/độ trễ/thời gian offline/10.000 ghi chú và không chạy test code của Kho Tri Thức trong phiên nghiên cứu. Những chức năng phía Granola là **được tài liệu nhà cung cấp xác nhận**, không phải PASS thực nghiệm của nhóm.
- **Đã phát hành/xác nhận:** ứng dụng Windows/macOS/iOS/Android, nhận dạng tiếng Việt, ghi chú gốc và enhanced, transcript và liên kết từ ý tóm tắt đến đoạn gốc, folders/spaces, CSV export, Granola API và MCP chính thức; API changelog v1.7.0 **tháng 11/2026** bổ sung tìm trong transcript, bắt đầu truy xuất từ mốc thời gian và cải thiện phân dòng người nói trên Android/Watch. [S01] [S02] [S03] [S04] [S05] [S06] [S07] [S08]
- **Không coi là tính năng đã được chứng minh:** tự hiểu toàn bộ nội dung video chỉ nhờ metadata, tự phân nhóm theo ngữ nghĩa vào cây tùy ý, backlinks kiểu wiki, trả audio gốc để seek, trích PDF với locator trang như thư viện tài liệu, đồng bộ offline có kiểm chứng xung đột, dùng Google Drive như kho video hàng trăm GB. Không có bằng chứng đủ để gán PASS cho những điểm này.
- **Beta/roadmap:** không nhận một tính năng chưa có bằng chứng tài liệu chính thức là đã phát hành. Có trang cập nhật sản phẩm [S19], nhưng nghiên cứu này không coi bài giới thiệu hoặc demo marketing là benchmark.
- **Mã nguồn/giấy phép:** không tìm thấy bằng chứng Granola công bố ứng dụng lõi dưới giấy phép mã nguồn mở chính thức. Xem đây là **dịch vụ SaaS độc quyền**, các SDK/connector bên thứ ba không có bảo đảm do Granola vận hành; tích hợp chỉ nên đi qua API/MCP/webhook công khai, tuân thủ điều khoản và quyền truy cập. Trạng thái license của từng thư viện tích hợp bên ngoài: UNVERIFIED vì không chọn thư viện nào ở đợt này.

### Tính năng quan trọng theo phạm vi thực tế

| Khả năng | Bằng chứng/giới hạn | Phân loại |
| --- | --- | --- |
| Bot-free meeting capture | Ứng dụng thu microphone/system audio trực tiếp trên máy, chủ động bấm bắt đầu; không có bot dự họp. Có thông báo/đồng ý phù hợp, **không** có nghĩa bản ghi luôn nằm cục bộ. [S09] [S10] | Phát hành |
| Human-in-the-loop | Ghi các ý ngắn vào raw notes trong cuộc họp; AI tạo enhanced notes dựa trên transcript, raw notes, lịch và hồ sơ; quay lại sửa/raw và regenerate. [S05] [S06] | Phát hành |
| Provenance hội thoại | Nút tra cứu cạnh ý trong enhanced note đưa tới phần transcript/raw note tương ứng; API có speaker/timing và tìm đoạn theo keyword. Không có audio gốc lưu để play/seek. [S06] [S07] [S09] | Phát hành, phạm vi transcript |
| Android + tiếng Việt | Android chính thức trên Play Store, ghi họp trực tiếp; tiếng Việt ở mobile và desktop. Điện thoại không thu được âm thanh họp trực tuyến từ ứng dụng khác; Android cuộc gọi **đi** dùng dialer riêng, cuộc gọi **đến** chưa hỗ trợ. [S03] [S04] [S11] | Phát hành, có giới hạn |
| API/MCP/webhook | Business/Enterprise có API key, scope; MCP OAuth với Basic giới hạn lịch sử 30 ngày và không có transcript tools, trả phí rộng hơn; webhook ký số, retry/event. [S01] [S07] [S08] [S12] | Phát hành, khác nhau theo gói |
| Offline | Tài liệu bảo đảm cache ghi chú để **xem/sửa khi offline**; chưa tìm thấy cam kết bảo đảm toàn bộ ASR/AI chạy offline hoặc thuật toán hòa giải conflict offline. [S09] | Một phần; sync conflict UNVERIFIED |
| Xuất/di chuyển | CSV gồm title, summary, transcript của ghi chú **do người yêu cầu sở hữu và đã có summary**; bản đã xóa/không summary không có; link 24 giờ, giới hạn một lần/24 giờ; không phải Markdown+assets round-trip. [S13] | Phát hành, không tương đương full backup |

### Giá và chính sách dữ liệu (tại ngày đọc)

- **Basic:** 0 USD/người/tháng, lịch sử tra cứu trong ứng dụng 30 ngày; MCP giới hạn các ghi chú 30 ngày và không có công cụ transcript. **Business:** giá niêm yết 14 USD/người/tháng, toàn bộ lịch sử, API, MCP/transcript, nhiều tích hợp. **Enterprise:** từ 35 USD/người/tháng theo bảng công khai, SSO/admin, policy tổ chức, công cụ kiểm soát và tính năng bảo mật nâng cao. Không tính thuế/quy đổi VND/giảm giá theo hợp đồng; chi phí thật còn tùy hóa đơn và số ghế. [S01] [S08]
- **Lưu trữ/xóa:** Granola nêu audio chỉ được cache tạm để phiên âm và **xóa sau khi hoàn thành**, note/transcript lưu đám mây AWS tại **Hoa Kỳ**. Dù không có bot và không giữ audio, vẫn có truyền dữ liệu để xử lý AI. Transcript có chính sách xóa tự động; xóa là **không khôi phục**, mất khả năng regenerate/giảm chất lượng chat, trong khi note vẫn tồn tại. [S09] [S14]
- **Training:** trên Basic/Business mặc định Granola có thể dùng dữ liệu đã ẩn danh để cải thiện dịch vụ và có tùy chọn opt-out; Granola nói nhà cung cấp model bên thứ ba không dùng dữ liệu này để train. Enterprise mặc định opt-out. Trên Android chưa bật/tắt trực tiếp được mà phải chỉnh qua desktop/iOS, áp dụng cho account. Không hỗ trợ BYO AI model. [S15]
- **Chia sẻ/đồng ý:** ghi chú riêng tư mặc định nhưng có chia sẻ link/folder, có thể để bất cứ ai có link xem nếu người dùng mở quyền. Người dùng cần thông báo và có cơ sở đồng ý hợp lệ trước khi thu âm cuộc họp; với hồ sơ công vụ/nội dung nhạy cảm cần thẩm định chính sách tổ chức/pháp lý trước khi dùng SaaS bên ngoài. [S09] [S16]
- **Tính năng cuộc gọi ở Việt Nam:** danh sách các quốc gia được Granola hỗ trợ cho dialer outbound **không liệt kê Việt Nam** vào 20/11/2026; do đó không nên kỳ vọng dùng tính năng này với số Việt Nam. Điều đó **không chứng minh** ứng dụng Android hoặc ghi chú cuộc họp trực tiếp bị chặn ở Việt Nam. [S11]
- **Giới hạn nội dung:** ảnh/tệp đính kèm có mức giới hạn riêng, không phải kho lưu mọi video: tài liệu nêu tối đa 30 MB/tệp, 1 GB/folder và 200 tệp/folder; không suy giới hạn này thành tổng dung lượng tối đa của toàn dịch vụ. [S17]

## 3. Ma trận K01–K12 theo giao thức chung

**Quy ước:** cột Trạng thái là mức Granola đáp ứng **toàn ca kiểm thử** theo tài liệu; NATIVE/EXTENSION/CUSTOM_BACKEND/NOT_SUPPORTED/UNVERIFIED là đúng năm nhãn của protocol. **Toàn bộ kịch bản thao tác thực tế tại Granola = NOT_RUN**; các bước dưới đây là quy trình tái thử tương lai, không phải test đã chạy. EXTENSION chỉ tính khi phải dùng khả năng nối ra hệ thống khác; CUSTOM_BACKEND là cần tự viết logic và giữ dữ liệu ngoài Granola. NOT_SUPPORTED là không có luồng được nhà cung cấp tài liệu hóa cho yêu cầu đầy đủ, không phải khẳng định đã kiểm mọi ngõ ngách sản phẩm.

| Ca | Trạng thái | Bằng chứng và cách tái thử | Khoảng trống/bất định |
| --- | --- | --- | --- |
| **K01** Ghi ngay tiếng Việt + receipt/giờ | **NATIVE** (một phần) | [S05] [S04]. Mở note trống trên desktop/Android, nhập 3 dòng Unicode, kết thúc, mở lại và đối chiếu ngày note. | Ghi trực tiếp có, nhưng ACK kiểu CaptureEvent bất biến và **server_received_at** chính xác chưa thấy bằng chứng. |
| **K02** Chia sẻ URL video/web lấy metadata/content | **NOT_SUPPORTED** | [S05] [S09]. Thử dán URL YouTube/web và yêu cầu tự lấy metadata, phụ đề, file nguồn vào một item. | Workflow trọng tâm là họp đang diễn ra; không chứng cứ generic video ingest tự động; không đánh đồng transcript hội thoại với hiểu MP4 trên web. |
| **K03** Gửi link trùng ngày khác nhưng retry không thêm Event | **CUSTOM_BACKEND** | [S12]. Giả lập hai lần gửi cùng URL khác ngày, và retry cùng event_id; cần adapter tự tạo Event và idempotency key ở hệ thống ngoài. | Webhook Granola có event ID giúp chống retry, nhưng **không phải** mô hình mỗi lượt share URL của Kho Tri Thức. |
| **K04** Markdown, bảng, link, Unicode round-trip | **UNVERIFIED** | [S05] [S07]. Tạo bảng GFM 3×3 có dấu tiếng Việt và link; xuất/nhập lại, so diff byte/AST; với Business gọi API private_notes_markdown. | Có ghi chú rich text/Markdown và API private notes; **chưa có bằng chứng** tables GFM, Markdown full fidelity và asset round-trip. |
| **K05** Tự gán vào nhóm **đã có** theo nội dung | **NOT_SUPPORTED** | [S18]. Tạo hai folder chủ đề, ghi note tương tự nhưng không phải series; xem có tự gán group đúng mà không bấm không. | Auto-add Granola là **theo cuộc họp lặp lịch**, không phải tự phân loại dựa ngữ nghĩa vào danh mục sẵn có. |
| **K06** Related items/backlinks có lý do | **UNVERIFIED** | [S08] [S18]. Tạo 2 note liên quan; kiểm cạnh bài có quan hệ hai chiều bền vững và nguồn lý do hay chỉ chat/search. | Có AI search across meetings; chưa chứng minh backlink hoặc cặp RelatedItem lưu độc lập. |
| **K07** PDF/audio/video và locator trang/mốc phát lại | **NOT_SUPPORTED** | [S06] [S07] [S09]. Dùng note có transcript, click ý → dòng transcript; thử mở audio gốc ở giây đó và PDF đúng trang. | Transcript có timestamp và tra nguồn **một phần**; audio sau phiên âm bị xóa, không có seek bản gốc; không tìm được full media/PDF page-locator workflow. |
| **K08** Một bài nhiều lĩnh vực, tree/table/card/timeline | **EXTENSION** | [S18] [S07]. Thêm note vào 2 folder, xem sidebar, dùng API dựng thêm tree/card/timeline nếu cần. | Một note thuộc nhiều folder là NATIVE; chỉ 1 tầng folder con, không có chứng cứ đầy đủ các chế độ xem yêu cầu, phải thêm UI ngoài. |
| **K09** Android+Windows, offline và conflict | **NATIVE** (một phần) | [S01] [S03] [S09]. Trên hai thiết bị sửa cùng note khi ngắt mạng, reconnect, so phiên bản; thử Android họp trực tiếp và virtual call. | Cả hai app + offline xem/sửa được nêu rõ; **conflict resolution UNVERIFIED**; Android không bắt âm thanh từ app họp trực tuyến khác. |
| **K10** API/Markdown/assets/backup/exit | **CUSTOM_BACKEND** | [S13] [S07] [S08]. Export CSV, API list/get+transcript, so count với tổng note kể cả chưa summary, kiểm asset/import Markdown. | CSV bỏ notes chưa summary/deleted; API yêu cầu gói trả phí; phải tự viết backup/manifest để gần yêu cầu Kho Tri Thức. |
| **K11** AI biết nguồn, không ghi đè bản người dùng, quyền/chi phí | **NATIVE** (một phần) | [S06] [S01] [S15]. Viết raw notes, sinh summary, sửa raw, regenerate, click nguồn; kiểm quyền share và opt-out. | Tách raw/enhanced và nhảy transcript rất đáng học; chưa benchmark AI hallucination/độ chính xác quote hay hành vi xung đột. |
| **K12** >10.000 item và nhiều trăm GB video qua Drive | **NOT_SUPPORTED** | [S17] [S01]. Cần benchmark list/search 10k + nhập hàng trăm GB media vào remote Drive. | Không có mô hình Granola vận hành Drive video như kho file gốc; hiệu năng 10k note riêng lẻ **UNVERIFIED**, không tự gán thất bại/đạt. |

## 4. Đặc thù sử dụng cá nhân tại Việt Nam

**Điểm phù hợp:** Việt ngữ đã nằm trong danh sách của Windows và Android; transcript/summary từ hội thoại có thể giúp xử lý biên bản và thu hồi quyết định, người phụ trách, thời hạn. Windows có khả năng bắt âm thanh hệ thống trong họp trực tuyến, Android ghi họp trực tiếp; bắt đầu thủ công tránh bot xuất hiện với tư cách người tham dự. Template cho từng loại cuộc họp và raw/enhanced separation phù hợp thao tác viết tay/gõ trọng tâm. [S04] [S05] [S06] [S09]

**Điểm phải xác nhận trong PoC:** bảng tên riêng Việt Nam, từ viết tắt, họ tên, số liệu/quyết định, dấu và biểu thức; chất lượng diarization khi nhiều người nói hoặc phòng ồn; Unicode round-trip, lựa chọn dấu câu. Desktop tự nhận chuyển ngôn ngữ; Android chọn một ngôn ngữ trội, không phù hợp hội thoại đổi liên tục giữa hai ngôn ngữ. Giao diện hiện bằng tiếng Anh, không có localization UI tiếng Việt. [S04]

**Thời điểm và sự kiện:** lịch họp/ngày họp, thời điểm câu nói trong transcript và thời điểm hệ thống Kho Tri Thức nhận link là ba thực thể khác nhau. Granola API tháng 11/2026 có keyword search transcript, from_time và speaker-line timestamp, nhưng một số mốc có thể không tồn tại/không chính xác, nhất là bản ghi ghép sau khi kết thúc; adapter cần lưu nguồn + độ tin cậy locator và không bịa độ chính xác. [S07]

**Phạm vi AI:** bản transcript chỉ cho biết những lời đã được nhận dạng (có thể sai), bản summary là nội dung suy diễn cần rà soát; không thể suy toàn bộ nội dung/video nguồn từ title/metadata hoặc lấy summary làm biên bản có hiệu lực mà không xét lại. Bắt buộc ghi phân biệt quote được đối chiếu, AI gợi ý và nội dung được người dùng chốt.

**Tổng chi phí/lock-in:** với nhu cầu chỉ 1 người, bản Basic có thể đủ **học UX** nhưng API/webhook PoC cần Business; USD và thanh toán/subscription phụ thuộc biến động. Dù có API và CSV, hệ thống vẫn phụ thuộc khả năng truy cập cloud, retention transcript, auth scopes, giá gói, chính sách AI và đầy đủ export. Không tạo phụ thuộc sản xuất mới chỉ để lấy chức năng mà Kho Tri Thức đã có.

## 5. Đối chiếu mã **đang có trên main** của Kho Tri Thức

Không lấy trạng thái trong MASTER_PLAN làm PASS. Đối chiếu ở commit cố định nêu đầu báo cáo; bằng chứng vận hành chi tiết do **CURRENT_STATE.md** lưu, bao gồm checkpoint KT-112, KT-113; không tự tái chạy những test này.

| Năng lực/ý tưởng Granola | Kho Tri Thức tại main: code & bằng chứng | Kết luận |
| --- | --- | --- |
| Nhận nội dung lập tức + giờ riêng | **CaptureEvent** có original/raw input và server_received_at, idempotency; **submit_capture** tạo event/Item/Job trong transaction; CaptureScreen có text/link/file/receipt. [R01] [R02] [R03] | **Đã có** và cần giữ; Granola không thay mô hình này. |
| Meeting capture không bot/desktop system audio | Repo có ingest text/url/file, parser và ASR offline xử lý một video thật; **chưa có** module ghi họp desktop trực tiếp kiểu Granola. [R04] [R05] | **Chưa có** trong Kho Tri Thức; chỉ cân nhắc nguồn cuộc họp riêng sau quyết định phạm vi. |
| Raw note song song enhanced note | Item.note là authored và ưu tiên khi đọc; DerivedContent là dẫn xuất có processor/status; UI chỉnh Markdown có màn xem nguồn nhưng **chưa có** UX meeting raw/AI side-by-side và approve version. [R04] [R06] [R07] | **Cải thiện UX**; không cho AI ghi đè note. |
| Transcript có provenance/nhảy dòng | DerivedContent.source_locator và processor_version; faster-whisper cục bộ đã có v2; ReadKnowledgeService chọn transcript khi không có note; CURRENT_STATE nêu transcript 11 đoạn EN từ một Reel, **chưa nghiệm thu seek audio theo đoạn**. [R04] [R05] [R06] | **Đã có nền dữ liệu, chưa có tương tác seek được xác minh**. |
| Auto-group, related items | OrganizationService tìm/assign nhóm hiện có, tạo RelatedItem, tránh user-curated; nhiều nhánh trong cây; Granola folder recurring theo lịch không tương đương. [R08] [R09] | **Kho Tri Thức đang có năng lực sâu hơn**, không thay. |
| Markdown / nhiều nguồn / media | KnowledgeReading, ItemScreen và CaptureScreen đọc/sửa Markdown với nguồn/tệp; DriveStorage/KnowledgeExport có kiểm soát phiên bản; Granola tập trung note họp. [R03] [R07] [R10] | **Đã có** văn bản nguồn tổng hợp; chỉ học cách nén giao diện họp. |
| Search/ChatGPT/portability | SearchService gộp Item, DerivedContent, CaptureEvent; KnowledgeExport đồng bộ bản xuất trên Drive, restore có kiểm chứng phạm vi; không có Granola adapter. [R11] [R10] | **Đã có** hạ tầng; API Granola chỉ là nguồn tùy chọn, không thay PostgreSQL/Drive. |
| Android | App PWA/share target có mã, nhưng Android vật lý/HTTPS còn **NOT_RUN** theo CURRENT_STATE; Granola có Android phát hành, nhưng ghi âm virtual call hạn chế. [R12] | **Cần kiểm Android riêng**; không tuyên bố dự án đã đạt nhờ Granola có ứng dụng. |

**Cảnh báo về hiện trạng:** Theo CURRENT_STATE, CI/backend/frontend, Windows, Drive live/restore, một Reel và Markdown đã có bằng chứng kiểm thử giới hạn; corpus cá nhân 10k item, Android thật, AI quality tiếng Việt, các nguồn media khác và audio seek theo đoạn **chưa nghiệm thu**. Nhãn "đã có" trong bảng là xác nhận **mã/code path** hoặc bằng chứng trong checkpoint, không đồng nghĩa kiểm mọi thiết bị và ngữ liệu.

## 6. Rubric bảy trụ — mục tiêu **thay toàn bộ** Kho Tri Thức

Điểm là **nhận định chuyên gia dựa vào tài liệu**, không là số benchmark hoặc đánh giá review của người dùng. Với tiêu chí chưa được chứng minh, thể hiện khoảng và hạ mức tin cậy; **không gán điểm 0 chỉ do thiếu test**.

| Trụ tiêu chí | Điểm/kịch trần | Khoảng hợp lý | Tin cậy | Lý do |
| --- | ---: | ---: | --- | --- |
| Capture + ingestion | **10/20** | 8–12 | Trung bình | Meeting capture mạnh; thiếu URL/video/web ingestion và CaptureEvent như yêu cầu. |
| Organization + recall | **8/20** | 6–10 | Trung bình | Search/chat, folders đa thành viên; cây chỉ một cấp con, không chứng cứ semantic auto-group/backlinks. |
| Text editor + reading | **9/15** | 7–11 | Trung bình | Raw/enhanced, template, highlight; GFM/table/import round-trip còn chưa rõ. |
| Provenance/related/timestamps | **10/15** | 8–12 | Trung bình | Transcript/source jump và API timestamps, nhưng không có audio seek, cross-item provenance. |
| Android/Windows/offline | **7/10** | 6–8 | Trung bình | Hai app có, tiếng Việt có, offline xem/sửa; Android virtual meetings và sync conflicts hạn chế. |
| Portability/backup | **5/10** | 3–6 | Trung bình | CSV/API thực, nhưng bỏ unsummarized, thiếu asset/Markdown full backup/restore verify. |
| Integration/cost/maintenance | **7/10** | 6–8 | Trung bình | API, MCP, webhook chính thức; Business phí theo ghế, cloud/training/retention/lock-in. |
| **Tổng** | **56/100** | **44–67/100** | **Trung bình-thấp** | Không benchmark trực tiếp; đánh giá mức phù hợp với yêu cầu Kho Tri Thức, **không phải điểm chất lượng Granola nói chung**. |

**Tách hai kết luận:** (1) **Thay toàn hệ thống:** không khuyến nghị (không đáp ứng ingestion nhiều loại, Drive, CaptureEvent, cây sâu/related, playback media và portability). (2) **Giá trị học/tái sử dụng tính năng:** **cao** ở UX ghi họp, bảo toàn ghi chú gốc, trace quote-to-transcript, template và nguồn API chính thức. Không dùng điểm 56/100 để phủ định giá trị meeting assistant của Granola.

## 7. Đề xuất áp dụng có giới hạn (không đổi kiến trúc lõi)

**Nguyên tắc:** dùng Item/Source/CaptureEvent/DerivedContent/Asset đã có; chỉ thêm code khi được giao giai đoạn triển khai, chưa phải việc của PR nghiên cứu này. Các test dưới đây là **tiêu chí acceptance đề nghị, chưa chạy**.

| Ý tưởng | UX, giải pháp kỹ thuật tối thiểu | Độ khó | Acceptance có thể đo | Phụ thuộc/lock-in |
| --- | --- | --- | --- | --- |
| **A. Ghi chú họp: Thô / AI gợi ý / Đã chốt** | Trong màn đọc Item, hiển thị raw note bất biến theo version và bản gợi ý riêng; nút Áp dụng/Hoàn tác rõ. Dùng Item.note + DerivedContent.kind=meeting_summary hoặc bản dẫn xuất mới; không sửa note thẳng từ worker. | **M** | Bộ 20 fixture Unicode/tên riêng: 20/20 note gốc còn nguyên sau regenerate, bỏ áp dụng và lỗi; bản AI phải có nhãn chưa xác minh; không có auto-overwrite. | Cần transcript/tóm tắt có quyền. Nếu dùng AI ngoài phải có opt-in, chi phí và quy tắc giữ dữ liệu. |
| **B. Tra ngược ý chính về dòng transcript** | Mỗi ý đề xuất giữ source_locator (segment ID/time/speaker/text hash); click highlight đúng đoạn transcript; nếu không có audio gốc thì **không hiển thị nút nghe**. | **M** | 30 đoạn gồm trùng câu, lệch thời gian, thiếu speaker: 100% locator còn trỏ đúng segment cùng version; sau reprocess locator cũ hiện stale; không ngụy tạo seek. | Tận dụng DerivedContent/ReadKnowledgeService; không cần vector DB; audio seek riêng chỉ khi KTT đã có Asset âm thanh thật. |
| **C. Mẫu biên bản họp và tách quyết định/việc giao** | Mẫu Markdown nhỏ (diễn biến, kết luận, người thực hiện, thời hạn, căn cứ, chờ xác nhận); đoạn máy gợi ý có badge, người dùng chốt trước lưu chính thức. | **S** | 5 mẫu, 10 bộ input có tên/giờ VN: edit/preview/export không mất ký tự và giữ thứ tự; không biến việc AI suy ra thành quyết định đã phê duyệt. | Không cần Granola API; có thể làm thuần frontend/processor tùy chọn. |
| **D. Adapter Granola opt-in để nhập cuộc họp** | Chỉ nếu thật sự dùng Granola: API Business+ lấy note/transcript, webhook ký HMAC báo thay đổi; map remote note_id thành Source identity, event_id chống retry, source_version; lưu original summary/transcript có nhãn Granola. | **M–L** | Với mock server: 2 lần cùng webhook event_id = 1 hành động xử lý; 2 phiên bản note = 2 version dẫn xuất, 1 Item; 401/403/429/413 retry rõ, không lộ API key, revocation ngừng đồng bộ; đối chiếu 10 note đủ/chưa summary. | **Paid plan**, key theo scope, HTTPS public, cloud US, retention và API thay đổi; không tự động import cuộc họp nhạy cảm. |
| **E. Bảng kiểm chứng AI bằng trích dẫn câu nói** | Trong tóm tắt, mỗi câu thuộc nhóm đã dẫn chứng/chưa đủ nguồn; phiên bản transcript và vị trí được kèm theo; chỉ khẳng định khi văn bản nguồn được đọc. | **M** | Bộ ≥30 đoạn transcript tiếng Việt được phép: ≥95% câu được đánh nhãn "có chứng cứ" trỏ tới span hiện có; 100% câu không đủ bằng chứng bị chặn trích dẫn giả; người dùng kiểm ngẫu nhiên. | Chất lượng ASR/AI phải đo thật, không áp dụng tiêu chí trên cho clip chỉ có metadata. |

**Thứ tự tối thiểu nếu triển khai sau:** A → B → C; D chỉ nếu có Granola account hợp lệ và nhu cầu đồng bộ chứng minh; E là quality gate trước khi dùng biên bản trong công việc quan trọng. **Không** thay Django/PostgreSQL/Drive, không thêm Redis/pgvector/MCP mới, không cài script hay connector không rõ giấy phép trong nhiệm vụ này.

## 8. Phản chứng, rủi ro và điểm có thể đảo chiều quyết định

1. **Rủi ro riêng tư/đồng ý:** không bot không có nghĩa không gửi nội dung lên cloud. Granola giữ notes/transcript trên AWS tại Hoa Kỳ; meeting công vụ, nội dung cá nhân hoặc dữ liệu thuộc phạm vi bảo vệ đặc biệt không được đem thử khi chưa được phép. Bảo đảm người dự họp được thông báo và có căn cứ hợp pháp. [S09] [S16]
2. **Mất nguồn truy nguyên:** transcript auto-deletion không phục hồi; audio sau ASR không còn, summary vẫn còn nên người dùng có thể hiểu nhầm khả năng kiểm chứng đầy đủ. [S09] [S14]
3. **Khóa nhà cung cấp/chi phí:** CSV thiếu note chưa summary, API khóa gói trả phí, MCP scopes/workspace, Cloud US, phí thuê bao; cần backup và khả năng chuyển dữ liệu ngoài Granola trước khi tích hợp. [S01] [S08] [S13]
4. **Sai lệch nhận dạng tiếng Việt:** danh sách ngôn ngữ có tiếng Việt nhưng chưa có WER/CER trên cuộc họp dài, tiếng địa phương, nhiều người nói, tên riêng/câu số. Diarization/timestamps không đủ chuẩn để tự lập biên bản ký xác nhận. [S04] [S07]
5. **Giới hạn điện thoại:** Android không nghe virtual meeting chạy trong app khác; outbound dialer không công bố hỗ trợ Việt Nam; không nhận incoming. [S03] [S11]
6. **Rủi ro phân quyền/tích hợp:** webhook/API key, folder public và MCP có thể vô tình đưa dữ liệu ra ngoài; các quyền chia sẻ phải kiểm trên workspace thật. [S08] [S12] [S18]

**Giả thuyết có thể bác bỏ kết luận hiện tại:**
- Nếu Granola chính thức mở quy trình ingest URL/video/PDF, cây đa cấp, auto-group semantic, media seek, round-trip Markdown/assets và export/restore đầy đủ có bằng chứng trên >10k items với phí hợp lý, phải **chấm lại** khả năng thay thế; hiện không có chứng cứ.
- Nếu PoC tiếng Việt trên 30 cuộc họp được phép không đạt độ chính xác tên/số liệu và tỷ lệ câu có chứng cứ, **không dùng** tóm tắt AI như nguồn gốc biên bản; chỉ tham khảo giao diện gõ thô và mẫu biên bản.
- Nếu dữ liệu phải chỉ ở máy nội bộ, hoặc chính sách tổ chức cấm chuyển âm thanh/transcript ra cloud, **không triển khai adapter Granola**; thay vào đó chỉ mượn UX, dùng ASR cục bộ và nguồn nội bộ của Kho Tri Thức.
- Nếu import API không lấy đủ note chưa summary, attachments hoặc những note đã hết retention, mọi phương án coi Granola là **kho dữ liệu chính** bị bác bỏ trừ khi có backup thứ hai được thử restore độc lập.

**Quyết định G15:** **Tham khảo UX** ngay ở mức nghiên cứu; **Thử PoC có điều kiện** cho hội thoại không nhạy cảm, chỉ sau khi được phép và chốt rõ nơi lưu/consent/chi phí. **Không áp dụng Granola thay toàn bộ**; **không tích hợp thư viện mới** trong PR này.

## 9. Kiểm tra và bàn giao

| Mục | Kết quả | Bằng chứng / giới hạn |
| --- | --- | --- |
| Đọc tài liệu nhiệm vụ/quy trình | **PASS (đọc)** | INDEX.md, G15-GRANOLA.md, G00-PROTOCOL.md trong cùng thư mục |
| Đọc hiện trạng và mã main | **PASS (đọc)** | MAIN commit c97f5678…, file code [R01]–[R12], CURRENT_STATE.md (20/11/2026) |
| Kiểm chứng nguồn công khai Granola | **PASS (desk research)** | [S01]–[S19], ngày truy cập 20/11/2026; mô tả chỗ khác biệt giữa docs/product |
| K01–K12 phân loại có đường tái thử | **PASS (desk research)** | Mục 3, mọi ca **đều NOT_RUN trên tài khoản Granola** |
| Đo tiếng Việt/Android/Windows/API/10k | **NOT_RUN** | Không có tài khoản/quyền hoặc môi trường test Granola; không suy đoán PASS |
| Build/test ứng dụng Kho Tri Thức | **NOT_RUN** | PR chỉ có 1 file Markdown, không thay đổi mã; không dùng trạng thái CI cũ làm kết quả test lượt này |
| Phạm vi file/rollback | **Giới hạn 1 báo cáo** | Nếu cần loại bỏ thay đổi, revert riêng commit tài liệu hoặc đóng PR, không đụng dữ liệu người dùng |

## 10. Danh mục nguồn đã đọc

**Nguồn chính thức Granola** (truy cập 20/11/2026; một số docs không có ngày đăng, ghi rõ là *ngày truy cập* chứ không ngụy tạo ngày công bố). Changelog API có nhãn tháng 11/2026; bảng giá/chính sách có thể đổi mà không có release note riêng.

- [S01] [Pricing & plan comparison](https://www.granola.ai/pricing) — phí, API/MCP/training/retention; truy cập 20/11/2026.
- [S02] [Granola updates](https://www.granola.ai/updates) — tiến trình phát hành, gồm Android/Windows; truy cập 20/11/2026.
- [S03] [Getting started with Granola for mobile](https://docs.granola.ai/help-center/ios/getting-started.md) — Android, hạn chế thu virtual meeting, sync; truy cập 20/11/2026.
- [S04] [Multi-language support](https://docs.granola.ai/help-center/customising-granola/multi-language.md) — ma trận tiếng Việt desktop/mobile, giao diện English; truy cập 20/11/2026.
- [S05] [Taking notes in Granola](https://docs.granola.ai/help-center/taking-notes/taking-notes-in-granola.md) — raw notes/formatting; truy cập 20/11/2026.
- [S06] [AI-enhanced notes](https://docs.granola.ai/help-center/taking-notes/ai-enhanced-notes.md) — raw/enhanced và jump-to-transcript; truy cập 20/11/2026.
- [S07] [API changelog](https://docs.granola.ai/api-reference/changelog.md) — v1.7.0 tháng 11/2026, timing/search; truy cập 20/11/2026.
- [S08] [Granola MCP](https://docs.granola.ai/help-center/sharing/integrations/mcp.md) — OAuth, plan/scopes/tools; truy cập 20/11/2026.
- [S09] [Security, Privacy & Data FAQs](https://docs.granola.ai/help-center/consent-security-privacy/security-privacy-data-faqs.md) — cloud US, bot-free, audio delete, offline cache, consent; truy cập 20/11/2026.
- [S10] [Transcription](https://docs.granola.ai/help-center/taking-notes/transcription.md) — start/stop, live transcript; truy cập 20/11/2026.
- [S11] [Phone calls](https://docs.granola.ai/help-center/ios/phone-calls.md) — Android outbound, incoming không có, khu vực không có VN; truy cập 20/11/2026.
- [S12] [Webhooks](https://docs.granola.ai/webhooks.md) — event, ký số, retry, API key; truy cập 20/11/2026.
- [S13] [Exporting notes](https://docs.granola.ai/help-center/sharing/exporting-notes.md) — CSV, lọc, thời hạn link, giới hạn quyền; truy cập 20/11/2026.
- [S14] [Transcript auto-deletion](https://docs.granola.ai/help-center/consent-security-privacy/transcript-auto-deletion.md) — retention, xóa vĩnh viễn; truy cập 20/11/2026.
- [S15] [Models & training](https://docs.granola.ai/help-center/consent-security-privacy/model-training.md) — opt-out/BYO; truy cập 20/11/2026.
- [S16] [Getting consent](https://docs.granola.ai/help-center/consent-security-privacy/getting-consent.md) — nghĩa vụ thông báo/đồng ý; truy cập 20/11/2026.
- [S17] [Increased file limits](https://docs.granola.ai/help-center/troubleshooting/increased-file-limits.md) — giới hạn attachment/folder; truy cập 20/11/2026.
- [S18] [Spaces & folders](https://docs.granola.ai/help-center/sharing/folders/spaces-and-folders.md) — đa folder, một cấp con và auto-add recurring; truy cập 20/11/2026.
- [S19] [Granola API](https://docs.granola.ai/help-center/sharing/integrations/granola-api.md) — Business/Enterprise API key/scopes; truy cập 20/11/2026.
- [S20] [Granola engineering: agent meeting search](https://www.granola.ai/blog/how-we-help-your-agent-find-what-its-looking-for) — giải thích cách hãng tiếp cận retrieval; là **nguồn tự thuật của nhà cung cấp**, không coi số liệu nội bộ là benchmark độc lập; truy cập 20/11/2026.

**Nguồn code và chứng cứ Kho Tri Thức**: URL cố định tại cùng một Git commit (truy cập 20/11/2026); ngoài ra tham chiếu [CURRENT_STATE.md](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/docs/CURRENT_STATE.md) cho các kiểm thử đã ghi nhận, không khẳng định vừa chạy lại.

- [R01] [CaptureEvent model](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/ingestion/models.py)
- [R02] [Capture submission/service](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/ingestion/services.py)
- [R03] [CaptureScreen](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/CaptureScreen.tsx)
- [R04] [DerivedContent model](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/models.py)
- [R05] [Offline transcription](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/transcribe.py)
- [R06] [ReadKnowledgeService](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/read_knowledge.py)
- [R07] [ItemScreen](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/ItemScreen.tsx)
- [R08] [OrganizationService](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/organization.py)
- [R09] [Catalog models](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/models.py)
- [R10] [Knowledge export/Drive](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/storage/knowledge_export.py)
- [R11] [SearchService](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/search/services.py)
- [R12] [README/main PWA status](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/README.md)

**Không có dữ liệu riêng tư, token, bản ghi âm, transcript cuộc họp thật hoặc mã nguồn ứng dụng thay đổi trong nghiên cứu này.** Báo cáo độc lập G15 được nộp để G00 review và tổng hợp sau; không tự merge.
