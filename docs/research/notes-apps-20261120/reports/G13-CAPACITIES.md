# G13 — Nghiên cứu độc lập Capacities (20/11/2026)

> **Phạm vi:** Chỉ Capacities; nghiên cứu tính năng có thể áp dụng vào phần văn bản, nguồn và quan hệ tri thức của Kho Tri Thức. **Ngày tra cứu:** 20/11/2026 (UTC+7). **Baseline Kho Tri Thức:** nhánh main tại commit [c97f5678](https://github.com/cavoixanh638/kho-tri-thuc/commit/c97f5678a6893d7dfec2595d89c9122f05195320). **Trạng thái đánh giá:** REVIEWED_DOCS_AND_SOURCE; Capacities UI/API/Android/Windows: **NOT_RUN** (không đăng nhập tài khoản, không cấp token, không mua Pro, không thử tệp cá nhân). Không đọc bảng nguồn sơ bộ G00 hoặc kết luận các luồng khác.

## 1. Executive summary (dưới 200 từ)

**Kết luận độc lập: Tham khảo UX, không thay toàn bộ Kho Tri Thức.** Capacities mạnh ở ghi chú theo **đối tượng có kiểu/thuộc tính**, liên kết ngược, quan hệ, daily notes, đa chế độ xem, Reader và gạch chân nguồn PDF/web. Có Windows, Android, offline và API/MCP dành cho Pro. Tuy nhiên nền tảng **không tự xếp ghi chú vào nhóm trong nền**, không chứng minh được lịch sử nhận bất biến phân biệt gửi lại với retry, không có bằng chứng trích hiểu toàn bộ video/timestamp trực tiếp, giới hạn upload **100 MB/tệp** cho mọi gói và không thể khôi phục đầy đủ workspace từ export. API có hạn mức tạo 5.000 object rồi tăng 100/tháng; đây **không** phải giới hạn tổng số ghi chú của ứng dụng. Trong khi đó Kho Tri Thức đã có Django/PostgreSQL/Drive, CaptureEvent, tự gán nhóm, RelatedItem, Markdown và cơ chế backup/restore đã kiểm một phần trên Windows. Nên học 5 mẫu UX/thuật toán nhẹ, giữ ID, dữ liệu, luồng capture và storage hiện hành; chỉ PoC khi có ca chấp nhận đo được.

## 2. Phương pháp, mức bằng chứng và phát hành

- **Dữ liệu trực tiếp đã đọc:** tài liệu chính thức Capacities, developer API, changelog tính đến tháng 11/2026 và mã nguồn **main** Kho Tri Thức (xem mục 5). Một trang mô tả tính năng không phải thử nghiệm độc lập. Không dùng tài liệu của G01–G17 khác; không dùng bảng nguồn sơ bộ G00.
- **NATIVE:** sản phẩm công bố có khả năng cốt lõi; không suy là toàn bộ điều kiện nghiệp vụ đã nghiệm thu. **EXTENSION:** bổ trợ từ tích hợp/tiện ích; **CUSTOM_BACKEND:** phải lập trình nghiệp vụ riêng; **NOT_SUPPORTED:** bằng chứng chính thức loại trừ mục tiêu đã định; **UNVERIFIED:** thiếu bằng chứng đáng tin hay cần thử thực tế. Mọi phép thử Capacities dưới đây là **NOT_RUN**, dù có chức năng công bố.
- **Trạng thái/độ mới:** [S01] Media analysis cập nhật 09/2026, [S02] API 2.0 ra 07/2026 và beta API cũ ngừng 01/09/2026, [S03] mobile 2.0 và Weblink analysis ra 08/2026, [S04] tháng 11/2026 tablet Android/iPad mới và ghi âm/AI audio chuyển vào Pro. **Reminders chỉ Beta cho Believer**, không được coi bản đại trà. Tránh suy các hạng mục roadmap là đã triển khai.
- **Nguồn/cấp phép:** ứng dụng dịch vụ Capacities không được đối xử như thư viện mã nguồn mở. Có **API REST/TypeScript SDK chính thức** ([S12], [S13]) và MCP của hãng ([S14]); chưa thấy giấy phép cho phép sao chép mã Capacities vào ứng dụng này. Mọi ý tưởng dưới đây là thiết kế độc lập, không sao chép code, assets hoặc API không được cấp quyền.
- **Đặc trưng Việt Nam:** tài liệu xác nhận Windows/Android nhưng **chưa có thử UTF-8 tiếng Việt với dấu tổ hợp NFC/NFD, nhập bằng EVKey/Unikey, tìm kiếm không dấu, 4G chập chờn và khôi phục xung đột**. Không được ghi PASS cho chúng. Không đưa nội dung cá nhân vào dịch vụ thứ ba khi chưa được phép.

### Bằng chứng tính năng và các giới hạn quan trọng

| Chủ đề | Sự thật có nguồn và gói/nền tảng | Phân định |
|---|---|---|
| Đối tượng và quan hệ | Object types, typed properties, tags, collections, backlinks, queries; một đối tượng có một loại nhưng nhiều tag/liên kết. Không dựa trên hệ thư mục truyền thống. [S05], [S06], [S07] | **Đã có** chức năng được mô tả; tên gọi object không đồng nghĩa auto-group hay cây thư mục |
| Ghi nhanh/thời gian | Daily notes, calendar, created date, di chuyển giữa đối tượng; Android Share Sheet gửi text/link/media. [S08], [S09] | **Đã có** hoạt động ghi chú; **không xác nhận** receipt bền vững server + event bất biến hoặc idempotency |
| Web và PDF | Weblink tạo đối tượng/metadata từ URL; web Reader/phân tích lưu trang là **Pro trên desktop**, có điều kiện trang lấy được. PDF có đọc, highlight, chú giải và nhảy đến vị trí trang. [S10], [S11], [S01] | **Đã có, có điều kiện**; nguồn web private, chống bot và PDF scan phải thử; không suy metadata là hiểu clip |
| Audio/video | Phân tích media bật AI theo space và người dùng chủ động bấm Analyze; bảng hỗ trợ **image, weblink, PDF, audio** (Pro/Believer), **không liệt kê video**. Ghi âm và phân tích audio vào Pro từ 11/2026. [S01], [S04] | Video có thể gắn link/nhúng, nhưng **không chứng minh** phân tích nội dung toàn video/seek bằng transcript |
| Lưu media | Mỗi file tối đa **100 MB ở Basic, Pro, Believer**; Basic 100 MB/tháng và 5 GB tổng; Pro/Believer không giới hạn tháng/tổng theo bảng công bố, vẫn chịu 100 MB/tệp. [S15] | **Không phù hợp** làm kho MP4 gốc lớn; “unlimited” không xóa giới hạn từng tệp |
| Liên quan/AI tổ chức | Related Content tự gợi các bài liên quan (Pro); AI có thể **đề xuất** để người dùng xác nhận. FAQ hãng khẳng định **không tự động xếp ghi chú trong nền**. [S16], [S17] | **Khác** K05 yêu cầu hành động gán nhóm thực tế vào nhóm đã có |
| Offline/đồng bộ | Ghi chú cache offline; media chế độ Everything/Required only; Android tải media nền qua Wi-Fi; khi xung đột phải chọn local hoặc server, bản bỏ bị xóa. AI không chạy offline. [S18] | **Đã có** offline-first, nhưng không chứng minh merge ba chiều/không mất phiên bản; note cục bộ không phải tệp Markdown trực tiếp |
| API/MCP | REST API theo **một space/token, Pro**, đọc/ghi object/block/property/daily note; TS SDK, OAuth/MCP do hãng quản lý. API có rate limit/429, quota tạo object **5.000 + 100/tháng sau mốc**; concurrency last-write-wins không giao dịch xuyên request. [S12], [S13], [S14], [S19], [S20] | **Đã phát hành** API 2.0; API không thay PostgreSQL event transaction; không nhầm quota API với quota UI |
| Export/restore | Export Markdown/YAML front matter, CSV collection và media; tự export ngày/tuần/tháng **chỉ khi ứng dụng mở** tại giờ chạy, cần media đã tải về. Hãng **không hỗ trợ clone/restore trọn vẹn space từ export**, có bulk import hạn chế. [S21], [S22], [S23] | Có đường xuất nội dung nhưng **không** có tính tương đương backup/restore toàn trạng thái |
| Giá, quyền riêng tư | Basic miễn phí; tham khảo giá công bố 05/10/2026: Pro **US$11.99/tháng** hoặc **US$119.88/năm** (~$9.99/tháng quy đổi); Believer **$14.99/tháng** hoặc **$149.88/năm** (~$12.49/tháng quy đổi), kiểm lại trước mua. AI có **ngân sách**, tính mức dùng theo loại phân tích; gói Plus/top-up tùy nhu cầu. Không end-to-end encrypted; AI tùy chọn per-space, chính sách nhà cung cấp phụ trợ cần duyệt. [S24], [S25], [S26], [S27] | Chi phí mỗi tháng cho kịch bản hàng nghìn media **chưa biết**; **không** coi quảng bá bảo mật là kiểm toán độc lập |

## 3. Ma trận K01–K12 và quy trình tái kiểm

**Ký hiệu:** trạng thái là khả năng đáp ứng **kịch bản đầy đủ**; nếu ô NATIVE nhưng vẫn thiếu điều kiện phải ghi rõ. “Tái thử” là quy trình phải chạy trên tài khoản thử được cấp phép; **mọi thao tác UI/API hiện NOT_RUN**. Cần ghi PASS/FAIL bằng ảnh, ID, thời điểm, dump/export hợp lệ, không dùng dữ liệu riêng tư.

| K | Phân loại | Bằng chứng và ranh giới | Cách tái thử/điểm chưa chắc |
|---|---|---|---|
| **K01** Gõ note Việt, receipt, thời điểm | **UNVERIFIED** (soạn note NATIVE) | Daily Note/Quick Capture và created date [S08][S09]. Không tìm được hợp đồng **ACK sau commit và server_received_at bất biến**. | Tạo 10 note Unicode trên Android/Windows; ghi giờ nhận có lệch đồng hồ; offline→online. Kiểm ID/receipt và thời điểm xuyên sync, không chấm PASS chỉ vì note xuất hiện. |
| **K02** Gửi URL web/video, metadata + nội dung | **NATIVE** cho weblink; **UNVERIFIED** video content | URL tạo Weblink + metadata cơ bản [S10]; **Pro desktop** mới phân tích nội dung trang [S01]. Link YouTube có thể xem/nhúng, không tương đương ASR/hiểu video. | Share 5 web công khai, 3 YouTube/Facebook/TikTok, 2 link private; đối chiếu title, description, text, nguồn, trạng thái lỗi. Không ghi “đã hiểu video” nếu chỉ embed/metadata. |
| **K03** Gửi lại link ngày sau vs HTTP retry | **UNVERIFIED** | Created date ≠ lịch sử CaptureEvent; REST LWW [S20]; không chứng minh một Item + hai event, retry một event. | Tạo cùng URL ngày D và D+1, gửi lại cùng request ID, kiểm event store, timestamps, số item/asset. Thiếu endpoint/idempotency contract. |
| **K04** Markdown/bảng/link/Unicode bảo toàn | **NATIVE** ở mức editor, import/export; bảo toàn byte **UNVERIFIED** | Block editor/Markdown import-export [S21][S23], không bảo đảm round-trip nguyên văn khoảng trắng/Unicode. | Paste 30 fixture gồm bảng GFM, link, code, ký tự Việt NFC/NFD; xuất rồi so normalize-và-so-byte riêng; mở lại ở hai nền tảng. |
| **K05** Tự gán vào nhóm **có sẵn** | **NOT_SUPPORTED** với auto background | Hãng nói thẳng không tự file note trong nền; Related Content và AI chỉ gợi ý/chờ duyệt [S17]. | Chuẩn bị ba collection, 50 ghi chú; không thao tác AI; đếm quan hệ gán thực tế sau nhận. Nếu dùng API worker riêng, đó là **CUSTOM_BACKEND**, không phải native. |
| **K06** Liên quan, backlinks/quan hệ | **NATIVE** | Manual mentions/links/backlinks, typed properties; Related Content Pro gợi ý bản ghi gần nghĩa [S05][S16]. Không mặc định có reason/provenance định lượng. | Tạo A→B, B→C, hai note tương tự không link; kiểm backlink, hiển thị related, điều khiển loại bỏ, nguồn lý do. |
| **K07** PDF/audio/video → đúng trang/mốc | **UNVERIFIED** cho bộ ba; **NATIVE** với PDF page | PDF Reader highlight/jump [S11]; audio AI transcription Pro [S04]; không có nguồn chứng minh seek đến chính xác timestamp video/audio trích dẫn. | PDF 20 trang→đánh dấu trang 17 và click; audio/video thử timestamp 00:37.250 sau refresh và export. Chấm riêng PDF PASS, audio/video NOT_RUN. |
| **K08** Một bài nhiều lĩnh vực, tree/table/card/timeline | **NATIVE** đối với đa tag/views; tree/timeline tương đương **UNVERIFIED** | Một object type với nhiều tag/collection, Queries & Views [S05][S06]; không phải cây thư mục tuỳ ý. **Điện thoại** chỉ list, không gallery/table/wall [S09]. | Gán một bài cho 3 tag/collection, so số object trước/sau; xem gallery/table/lists trên desktop và Android; thử tree phân cấp 4 tầng và timeline theo event riêng. |
| **K09** Android+Windows, offline/sync/conflict | **NATIVE** trên tài liệu; thiết bị thật **NOT_RUN** | Có Windows/Android [S28], offline cache và popup giải quyết phiên bản [S18]; bản bị bỏ **không hồi phục**. | Ngắt mạng 30 phút, sửa cùng note hai thiết bị, đồng bộ, ghi bản mất/được và lựa chọn; media >100MB fail theo điều kiện. Test Android bằng máy thật. |
| **K10** API, import/export tài liệu+assets, backup | **NATIVE** một phần; full restore **NOT_SUPPORTED** | Pro REST/MCP [S12][S14], Markdown/CSV/media export [S21], bulk import desktop [S23]; hãng không hỗ trợ clone/restore hoàn chỉnh [S22]. API LWW [S20]. | 100 bài, 10 relation, 10 PDF, giờ tạo và tag; export→import space mới; so ID, link, nguồn, thuộc tính và asset SHA. Kỳ vọng mất mát phải nêu, không gọi backup tương đương. |
| **K11** AI provenance, gợi ý vs ghi đè, quyền/giá | **UNVERIFIED** cho quy trình kiểm chứng nguồn; AI hỗ trợ có điều kiện | AI/Media analysis cần bật theo space và Pro, một số thay đổi cần duyệt [S01][S17][S26]; không có bài thử độc lập đo trích dẫn nguồn PDF/video và thao tác ghi đè. | Dùng tập 20 câu có đáp án/locator; bật/tắt AI, ghi prompt+model+quota/cost, kiểm yêu cầu xác nhận khi sửa curated note; không đưa dữ liệu mật. |
| **K12** Trên 10.000 items, hàng trăm GB video trên Drive | **NOT_SUPPORTED** với **media gốc large-file/Drive**; scale note **UNVERIFIED** | 100 MB/tệp mọi gói [S15]; sản phẩm không cung cấp DriveStorage kiểu Kho Tri Thức; API tạo 5.000 object rồi +100/tháng [S19] **không** là giới hạn số note tạo bằng UI. | Fixture tổng hợp 10k URL/note và 200GB MP4 nhiều file 101MB+; đo ingest/restore/storage ownership; không thử tải dữ liệu thật hay phí trả trước. URL-only có thể giữ link chứ không đáp ứng lưu file nguồn. |

**Tóm tắt kiểm thử G13:** 12/12 kịch bản **đã lập phương pháp, 0/12 đã thực thi trên Capacities**. Không có account Pro, API key, build chạy Android hay 200GB file được dùng. Bằng chứng ứng dụng chỉ là tài liệu công khai; kiểm tra repo nội bộ là **source inspection**, không phải chạy suite mới.

## 4. Phân tích riêng cho người dùng Android/Windows tại Việt Nam

1. **Gửi URL:** Trải nghiệm share sheet/Quick Capture của Capacities đáng học: người dùng có thể gửi đường dẫn hoặc văn bản từ app khác đến một inbox/daily note. Tuy nhiên **lượt nhận**, URL gốc, lỗi quyền truy cập, thứ tự ngày, danh tính nội dung và tác vụ tải media thuộc logic hệ thống Kho Tri Thức; Weblink metadata không đáp ứng các bất biến này. AI Weblink chỉ chạy Pro desktop, không được coi đã phân tích nội dung Facebook/TikTok riêng tư.
2. **Thao tác văn bản tiếng Việt:** cấu trúc object + property và backlinks giúp tìm nội dung dài; kiểm chứng riêng phím Telex/VNI, IME composition, paste từ Word, Markdown GFM, số hiệu văn bản và tìm kiếm không dấu. Chưa có bằng chứng tìm kiếm Việt ngữ tương đương SearchService unaccent/trigram. Không kết luận Capacities lỗi tiếng Việt chỉ vì chưa thử.
3. **Lịch sử thời gian:** daily notes, ngày tạo/sửa phục vụ quản trị cá nhân, **không thay** ba trường khác nhau là giờ server nhận, ngày nguồn đăng và giờ worker xử lý. Cần lineage từng lần capture, không chỉ thuộc tính một object.
4. **Nguồn và AI:** highlight PDF → trang cụ thể là giá trị lớn; Reader web chỉ có nội dung nếu trang trích được. Audio transcribe có ích, nhưng ASR **không** chứng minh hiểu toàn bộ hình/động tác/video; thiếu transcript hoặc phụ đề phải hiện “chưa có nội dung” theo nguyên tắc dự án. AI dùng ngân sách và có thể gửi dữ liệu cho model bên ngoài. Cần nguyên văn do người dùng viết bất khả xâm phạm.
5. **Khả năng thoát:** export Markdown có URL/local-link, frontmatter và media là điểm cộng, nhưng full restore chính thức **không có**. Offline dữ liệu lưu trong DB ứng dụng chứ không phải vault Markdown truy cập trực tiếp; xung đột có thể mất một phiên bản. Không thiết kế Kho Tri Thức phụ thuộc bản export Capacities để phục hồi DB/Drive.

## 5. Đối chiếu **mã hiện hành** Kho Tri Thức, không dựa trên kế hoạch

Đối chiếu commit main nêu trên và [CURRENT_STATE.md](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/docs/CURRENT_STATE.md). Báo cáo trạng thái nói **Windows KT-113 LIVE_PASS**, dữ liệu mẫu 2 kho con/19 nhánh/5 item, 211 backend test và 19 frontend test; Android chưa nghiệm thu, dữ liệu cá nhân lớn và độ chính xác ASR tiếng Việt chưa đo. Đó là bằng chứng của **đợt chạy trong log**, không phải kiểm thử mới của G13, và không suy toàn hệ thống đã PASS.

| Khả năng Kho Tri Thức | Bằng chứng mã trên main / trạng thái | So với Capacities; quyết định |
|---|---|---|
| Gửi chữ/URL + receipt mỗi lần | [ingestion/services.py L78–170](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/ingestion/services.py#L78-L170): transaction, Item/Source/CaptureEvent, server_received_at, idempotency; [CaptureScreen.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/CaptureScreen.tsx) | **Đã có nghiệp vụ cốt lõi**; nên học UX share/quick capture, **không** thay CaptureEvent bằng daily note. |
| Tổ chức nhiều kho con/cây và nhiều đường dẫn | [catalog/knowledge_tree.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/knowledge_tree.py), [catalog/models.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/models.py) | **Đã có** Topic.parent, ItemTopic M:N, Project/Tag. Object types/templates là **ý tưởng cải thiện UX**, không nên tạo cấu trúc cứng mới. |
| Tự gán nhóm sẵn có + quan hệ | [catalog/organization.py L104–256](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/organization.py#L104-L256): _assign_groups tạo quan hệ thật, RelatedItem được lưu, không sửa nhãn người dùng pinned | **Đã có nhưng đánh giá thực còn thiếu**; Capacities thiếu auto file nền. Có thể cải thiện UI lý do/suggestion, không thay thuật toán bằng AI marketing. |
| Văn bản là đối tượng tri thức chính | [processing/read_knowledge.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/read_knowledge.py), [web/KnowledgeReading.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/KnowledgeReading.tsx): ưu tiên note, đọc derived text có locator; frontend Markdown react-markdown/remark-gfm đã tích hợp | **Đã có** đọc/soạn; học Reader/highlight, typed metadata và backlinks nhìn thấy được; không viết lại editor trước benchmark. |
| Tìm kiếm tiếng Việt và provenance | [search/services.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/search/services.py): trả snippet/locator/provenance; FTS/unaccent/trigram | **Đã có nền tảng**, thiếu thử dữ liệu lớn; không ép semantic/embeddings mới chỉ vì Related Content. |
| Video/ASR/Drive gốc | [processing/transcribe.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/transcribe.py) và [storage/knowledge_export.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/storage/knowledge_export.py): ASR có thời đoạn với giới hạn, bản xuất lên Drive giữ ID. Windows đã thử một Reel tiếng Anh, Drive SHA verify | **Đã có một phần**, chưa thử nhiều video/ASR Việt/seek; **không phù hợp** chuyển video sang Capacities (100 MB/tệp, không có Drive adapter). |
| Android Share Target, offline | [web/manifest.webmanifest](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/public/manifest.webmanifest) có share_target; Windows chạy đã kiểm | **Chưa nghiệm thu Android vật lý/offline**; đây là điểm nên học và PoC; không giả đã PASS vì manifest có khai báo. |
| Backup, exit, khôi phục | [CURRENT_STATE.md](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/docs/CURRENT_STATE.md), kết quả 15 collection restore DB mới, Drive file hash và manifest phiên bản | **Đã có kiểm thử live trong phạm vi ghi nhận**, giữ PostgreSQL+Drive+manifest; Capacities export **không** khôi phục toàn trạng thái. |

**Mức phù hợp kỹ thuật:** Capacities không cho thấy lợi thế đủ để thay Django/PostgreSQL, UUID/DriveStorage, raw event ledger, ASR adapter và backup đã xây. Các điểm đáng học chủ yếu là **trình bày, tổ chức theo kiểu đối tượng, trích dẫn nguồn và đường đi từ mobile vào kho**.

## 6. Chấm 7 trụ theo rubric G00

Điểm đánh giá **trên tài liệu**, không phải điểm benchmark: số giữa thể hiện mức khớp yêu cầu của Kho Tri Thức; khoảng là biên do chưa thử UI/corpus; không đánh đồng “UNVERIFIED” với 0 điểm. Trục tổng 100 nhưng **không được suy điểm cộng bù cho blocker không thể bỏ qua**.

| Trụ | Điểm / tối đa; khoảng hợp lý | Lý do | Tin cậy |
|---|---:|---|---|
| Capture + ingestion | **12/20** (9–15) | Share sheet, URL metadata tốt, nhưng thiếu receipt event và quy trình video ingestion/Drive | Trung bình |
| Organization + recall | **16/20** (13–18) | Object types, relations, backlinks, queries/related rõ; không auto-file nền | Cao với feature, thấp với quality recall |
| Text editor + reading | **12/15** (10–14) | Blocks, template, highlight PDF/web, export; cần thử Unicode/GFM và editor performance | Trung bình |
| Provenance/related/timestamps | **7/15** (4–10) | Backlinks/PDF page native; thiếu event provenance và timestamp seek đa media | Trung bình |
| Android/Windows/offline | **8/10** (6–9) | Hai nền tảng, offline conflict UI; loss of discarded version, NOT_RUN thiết bị thật | Trung bình |
| Portability/backup | **6/10** (3–8) | Export Markdown/media tốt; không thể restore identical workspace | Cao |
| Integration/cost/maintainability | **5/10** (3–7) | Pro API/MCP; quota 5k API creations, AI budget, 100MB/file và dữ liệu bên nhà cung cấp | Trung bình-cao |
| **Tổng** | **66/100** (**48–81** từ tổng biên các trụ) | Tổng = 12+16+12+7+8+6+5=**66**; khoảng = (9+13+10+4+6+3+3)=**48** đến (15+18+14+10+9+8+7)=**81**. | Đánh giá dựa trên docs |

**Hai kết quả tách biệt:**
- **Thay thế toàn bộ Kho Tri Thức: KHÔNG PHÙ HỢP ở hiện trạng**, do 3 gate chặn: (a) lưu media gốc lớn >100MB/Drive và hàng trăm GB, (b) sổ CaptureEvent bất biến/phân biệt retry, (c) tự động gán nhóm hiện có không cần người duyệt. Điểm khung 66/100 không xóa ba blocker này. Việc chuyển dữ liệu đã lưu cũng có rủi ro mất trạng thái do export không restore lossless.
- **Giá trị học hỏi tính năng: CAO, chọn lọc 5 ý tưởng UX/Reader (mục 7).** Tận dụng Django/PostgreSQL hiện có để bảo đảm provenance và không khóa dữ liệu. Không đề nghị phụ thuộc Capacities API/MCP cho luồng sản xuất.

## 7. Năm đề xuất áp dụng (không sửa code trong PR nghiên cứu)

| Ưu tiên; độ khó | UX nhận từ Capacities | Technical/adapter trong kiến trúc hiện hữu | Acceptance đo được; phụ thuộc và rủi ro |
|---|---|---|---|
| **P1 — M** | **Backlinks có ngữ cảnh**: cuối bài hiện “Được nhắc từ” và “Mục liên quan”; người dùng click mở đoạn nguồn và có nút ẩn sai gợi ý | Dựa Item/RelatedItem + link markdown nội bộ và SearchService, giữ reason, source_version; không thêm graph DB | Dataset 30 bài, 15 liên kết chủ ý + 10 tương đồng. 100% backlink do người tạo dẫn đến đúng item; ẩn 5 related sai không tái xuất sau refresh/reprocess; related tự động có reason/version. Rủi ro: false positive và lỗi quyền |
| **P1 — S/M** | **Mẫu thông tin theo kiểu tài liệu**: Video, Bài viết, Sách, PDF có field nhẹ (tác giả/ngày nguồn/trạng thái trích) mà không chặn gõ note | Frontend config schema/template trên Item/Source metadata hiện có; chỉ migrate khi chứng minh cần, giữ UUID và Item.note | 4 type x 10 item, tạo note chưa điền metadata vẫn ACK; đổi type không nhân item, không mất ghi chú/cây/Drive ID; field do người duyệt không bị AI đè. Rủi ro: dữ liệu rỗng/taxonomy phình |
| **P1 — M** | **Đọc web kèm highlight/trích nguồn**: chọn một đoạn → “Lưu trích dẫn”, thấy URL, tiêu đề, ngày truy cập, trích đoạn, lỗi nguồn | Bám DerivedContent và source_locator, trích text web đã có; lưu span offset/quote hash/version và fallback “không tìm lại được”; không giả trích được mọi trang | 20 trang web công khai/5 trang chặn; 95% link trích về đúng đoạn trên trang giữ nguyên, khi trang đổi phải báo stale, không trỏ sang đoạn nhầm; không ghi đè note gốc. Rủi ro copyright/trang đổi |
| **P2 — M** | **Highlight PDF có nút tới trang/đoạn** thay vì chỉ danh sách văn bản | Reader PDF hiện hữu + pypdfium2 thumbnail + DerivedContent locator page; có thể giữ trang và rectangle khi parser đủ tin cậy | 20 PDF Việt 2–100 trang, 50 highlight: 50/50 nhảy đúng trang sau refresh; nếu không có tọa độ, chỉ nhảy trang và nhãn “chưa xác định đoạn”; kiểm Unicode, dữ liệu text cũ không mất. Rủi ro scan/OCR và parser version |
| **P1 — S/M** | **Android Share Sheet/Quick Capture tối giản**: gửi URL/text → receipt cùng giờ và trạng thái đồng bộ, nhập chú thích tùy chọn | Hoàn thiện Share Target/PWA đã khai báo, offline queue nhẹ có idempotency_key; backend CaptureService hiện có; không tạo kênh sự kiện khác | Máy Android thật + Windows: 30 lần share; ACK hiện ≤3 giây khi DB online; 5 lần retry cùng key không tăng Event; 3 lần gửi lại URL chủ đích tạo 3 Event và 1 Item; khi offline hiện pending rõ, sau online không trùng. Rủi ro Android OS lifecycle, ngắt mạng |

**Điều kiện triển khai:** Những con số acceptance là **mục tiêu tương lai**, không phải kết quả đo. Chỉ G00 chốt vào backlog sau khi review nguồn, xét công sức; ưu tiên nghiệm thu Android, related UI và Reader trước khi mở rộng AI. Không nhập thư viện, extension hay code Capacities bên thứ ba không kiểm giấy phép. Tất cả dữ liệu/ID gốc, lịch sử và mapping Drive phải giữ nguyên; rollback UI không thay đổi DB không tương thích.

## 8. Rủi ro, giả thuyết phản chứng và điều kiện đảo chiều

### Rủi ro phải ghi nhận

1. **Khóa nhà cung cấp/khôi phục:** xuất bản dễ đọc nhưng hãng xác nhận không full restore/clone; sao lưu chỉ chạy tự động khi app mở và local media sẵn [S21][S22]. Không dùng làm backup authoritative.
2. **Media & chi phí:** upload 100MB/tệp không đáp ứng nhiều MP4, Pro “unlimited” vẫn có điều kiện; AI tiêu ngân sách tăng theo loại nội dung và độ dài, chưa benchmark [S01][S15][S25].
3. **Quyền riêng tư:** dữ liệu tại cloud, không E2EE; bật AI per-space đồng nghĩa xử lý thông tin qua nhà cung cấp model theo điều khoản; không thử với văn bản công vụ/nhạy cảm [S26][S27].
4. **Tính toàn vẹn dữ liệu:** API last-write-wins, không giao dịch xuyên request; xung đột offline có nguy cơ mất bản không chọn [S18][S20]; khác hợp đồng CaptureEvent của dự án.
5. **Độ trễ/quota & lỗi tiếng Việt:** tạo hàng loạt qua Pro API có quota cứng rồi +100/tháng, 429 trên endpoint; chưa thử 10k item, tìm không dấu, IME Android. Không dùng suy đoán hiệu năng.
6. **Nguồn gốc tri thức:** tóm tắt AI web/PDF có thể không chính xác; video embed hay metadata không là transcript/hiểu động tác; phải giữ rõ nguồn, parser, locator và “thiếu nội dung” trên ứng dụng riêng.

### Phản chứng có thể làm thay đổi kết luận

- **H1 (thay thế):** Nếu Capacities công bố cách giữ video gốc **trên Drive sở hữu người dùng**, không giới hạn >100 MB/file, có API transaction tạo **event nhận bất biến/idempotency**, background tự phân nhóm **không cần duyệt**, và export→restore 100% ID/quan hệ/media, **đồng thời** PoC 10k item + 200GB vượt bài đo của Kho Tri Thức trên cùng dữ liệu, khi đó đánh giá lại “không thay toàn bộ”. **Đến 20/11/2026 chưa có các bằng chứng này; hiện H1 bị phản bác bởi tài liệu 100MB, auto-file và export.**
- **H2 (UX):** Nếu kiểm dùng thử 20 người/20 tác vụ trên Android và Windows cho thấy typed object/backlinks làm chậm capture >20% hoặc tăng lỗi phân loại so với UI hiện có, bỏ thiết kế tương ứng dù hấp dẫn trên website.
- **H3 (đọc nguồn):** Nếu thử 20 PDF/20 web cho thấy Reader/highlight không cải thiện tỷ lệ truy ngược đúng trang/đoạn ít nhất +15 điểm phần trăm so với baseline, không mở rộng chức năng highlight.
- **H4 (AI):** Nếu 30 query có nguồn mà trên 10% tạo lập luận không có locator đúng, hoặc chi phí vượt ngưỡng chủ sở hữu duyệt, giữ AI mặc định tắt; không triển khai phân tích video chỉ dựa trên marketing.

## 9. Kết quả QA nghiên cứu, giới hạn và điểm bàn giao

| Bài kiểm | Kết quả 20/11/2026 | Giới hạn |
|---|---|---|
| Đã đọc đúng INDEX, G13 và G00 protocol | **PASS (review tài liệu repo)** | Không đọc G00 source sơ bộ/báo cáo Gxx khác |
| Tính năng có nguồn chính thức, mốc release/plan | **PASS (source review)** | Nguồn có thể được cập nhật sau ngày tra cứu |
| K01–K12 có nhãn, URL, bước tái thử | **PASS (đủ 12 kịch bản)** | **NOT_RUN 12/12** phép thử ứng dụng thật |
| Đối chiếu code React/Django/PostgreSQL main | **PASS (inspection tại SHA cố định)** | Không chạy suite hay kiểm Windows/Android mới |
| Điểm 7 trụ, 2 trục, phản chứng, >=3 rủi ro | **PASS (đủ cấu trúc)** | Điểm ước lượng theo docs, không benchmark |
| PoC sản phẩm, Pro AI, API/MCP, quota live | **NOT_RUN** | Không có tài khoản/token/ủy quyền sử dụng |
| 10k item, 200GB media, Việt ngữ/IME | **NOT_RUN** | Chỉ có giới hạn từ docs, không thử tải |
| Thay đổi code ứng dụng | **NOT_APPLICABLE** | Chỉ nộp một báo cáo, không đụng code |

**Bàn giao cho G00:** Ưu tiên tham khảo **Backlinks + Reader highlight + typed metadata + Android quick capture**; không đề xuất migration từ Drive/PostgreSQL. Không biến lập luận về docs thành “ứng dụng đã vượt nghiệm thu thực tế”.

## 10. Danh mục nguồn gốc (truy cập 20/11/2026)

Các URL sau được dùng trực tiếp trong nghiên cứu; tài liệu Capacities là **nguồn từ nhà sản xuất**, còn GitHub main của dự án là nguồn code nền. Ngày ghi sau link (nếu có) là ngày **changelog/doc tự công bố**, không phải ngày đã chạy test.

- **[S01]** [Media analysis](https://docs.capacities.io/reference/media-analysis) — docs, cập nhật **09/2026**, danh sách media và quyền Pro.
- **[S02]** [Release 67 — API 2.0](https://capacities.io/whats-new/release-67) — **07/2026**, thay API beta.
- **[S03]** [Release 68 — mobile 2.0](https://capacities.io/whats-new/release-68) — **08/2026**.
- **[S04]** [Release 73 — tablet/audio/reminders](https://capacities.io/whats-new/release-73) — **11/2026**, audio Pro và reminders Believer Beta.
- **[S05]** [Object types](https://docs.capacities.io/reference/content-types) và [Object types vs folders](https://docs.capacities.io/tutorials/object-types-vs-folders).
- **[S06]** [Cấu trúc không cần thư mục](https://docs.capacities.io/faq/editing/structure-without-folders) và [Queries](https://docs.capacities.io/reference/queries).
- **[S07]** [Backlinks](https://docs.capacities.io/reference/backlinks), [Link types/relations](https://docs.capacities.io/faq/editing/different-kinds-of-links).
- **[S08]** [Dates & Daily Notes](https://docs.capacities.io/reference/dates-and-daily-notes).
- **[S09]** [Capacities on Mobile](https://docs.capacities.io/reference/mobile) — Share Sheet, offline companion, **list-only trên phone**.
- **[S10]** [Weblinks](https://docs.capacities.io/reference/basic-types/weblinks) — metadata và Reader/analysis phân tầng.
- **[S11]** [PDFs](https://docs.capacities.io/reference/basic-types/pdfs) — highlight và jump page.
- **[S12]** [REST API overview](https://developers.capacities.io/api/overview) — Pro, one space/token, TypeScript SDK.
- **[S13]** [TypeScript SDK và API versioning](https://developers.capacities.io/api/overview/sdks) — thư viện chính thức; xem thêm [versioning](https://developers.capacities.io/api/overview/versioning).
- **[S14]** [MCP chính thức](https://docs.capacities.io/developer/model-context-protocol) — quyền/cách kết nối qua OAuth.
- **[S15]** [Media Upload](https://docs.capacities.io/misc/media-upload) — 100MB/tệp trên mọi gói.
- **[S16]** [Related Content](https://docs.capacities.io/reference/related-content) — Pro suggested related items.
- **[S17]** [Official migration from Mem](https://docs.capacities.io/migration/switching-from-mem) — hãng nêu rõ không auto-organize trong nền.
- **[S18]** [Offline Support](https://docs.capacities.io/misc/offline-support) — local cache, version conflict/selection, không phải direct Markdown files.
- **[S19]** [API rate limits & creation quota](https://developers.capacities.io/api/overview/rate-limiting) — hard 10k API object creations, +500/tháng, 429.
- **[S20]** [API concurrency](https://developers.capacities.io/api/overview/concurrency) — stateless, last-write-wins, không transaction đa request.
- **[S21]** [Export Markdown/frontmatter/CSV/media](https://docs.capacities.io/reference/export) — export tự động khi app đang mở.
- **[S22]** [Can I restore or clone a space from export?](https://docs.capacities.io/faq/account/restore-space-from-export) — **No**, không đầy đủ.
- **[S23]** [Bulk Import](https://docs.capacities.io/reference/bulk-import) — desktop import, không đồng nhất full restore.
- **[S24]** [Facts](https://capacities.io/about/facts) — cập nhật **05/10/2026** và [Pricing](https://capacities.io/pricing) — giá có thể đổi theo chu kỳ tính tiền.
- **[S25]** [Subscriptions and AI budgets](https://docs.capacities.io/reference/subscriptions).
- **[S26]** [AI Privacy](https://docs.capacities.io/more/ai-privacy) — lựa chọn AI và bên xử lý.
- **[S27]** [Why not end-to-end encrypted](https://docs.capacities.io/more/end-to-end-encryption).
- **[S28]** [Download Windows/Android](https://capacities.io/download-app).
- **Repo nội bộ:** [main @ c97f5678](https://github.com/cavoixanh638/kho-tri-thuc/tree/c97f5678a6893d7dfec2595d89c9122f05195320) + [CURRENT_STATE.md](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/docs/CURRENT_STATE.md).

**Lưu ý:** Bộ tài liệu online có thể đổi sau 20/11/2026; các giới hạn, tính năng phát hành và giá phải tái xác minh trước khi mua hoặc ra quyết định thay đổi kiến trúc.
