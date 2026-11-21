# G04 — Evernote v11: nghiên cứu độc lập cho Kho Tri Thức

**Ngày đánh giá:** 20/11/2026 (Asia/Ho_Chi_Minh)  
**Luồng:** G04, chỉ nghiên cứu Evernote v11; không đọc báo cáo của G01–G17 hoặc bảng nguồn sơ bộ G00.  
**Baseline so sánh:** cavoixanh638/kho-tri-thuc, main tại commit **c97f5678a6893d7dfec2595d89c9122f05195320** (20/11/2026 11:40:37 ICT; kiểm tra qua GitHub commits/main).  
**Phương pháp:** đọc code và tài liệu của Kho Tri Thức trên main; tra cứu tài liệu/release notes/dev docs/chính sách chính thức của Evernote. **Chưa đăng nhập, cài đặt, thanh toán, tải dữ liệu riêng tư hay thao tác trực tiếp trong Evernote: toàn bộ K01–K12 ở mức thực nghiệm = NOT_RUN.** Những đánh giá dưới đây là *khả năng sản phẩm theo tài liệu*, không phải kết quả benchmark.

## 1. Executive summary (dưới 200 từ)

Evernote v11 (phát hành 19/01/2026) là sản phẩm tham khảo UX tốt cho thu thập trang web, tìm kiếm nhiều loại nội dung và quản trị ghi chú. Tài liệu chính thức năm 2026 xác nhận Web Clipper, OCR/tìm kiếm ngữ nghĩa, transcript có điểm nhảy vào audio/video, AI Assistant/Edit, và MCP beta có công cụ tìm/đọc/ghi. Trình sửa AI có thay đổi được tô sáng; meeting recorder mới bổ sung ghi chú gõ trong khi thu để đưa vào tóm tắt.

Tuy nhiên, Evernote không có bằng chứng công khai về mô hình *mỗi lượt gửi URL là CaptureEvent bất biến*, retry idempotent, lưu video hàng trăm GB ở Google Drive theo ID độc lập, hoặc xuất Markdown gốc + toàn bộ provenance/locator. Xuất chính thức là ENEX/HTML trên desktop; giới hạn tìm kiếm PDF 52 MB/tệp. Việc sản phẩm tự nhận hỗ trợ AI/video không có nghĩa đọc hiểu mọi video hoặc có thể xuất toàn bộ bản chép lời cùng timestamp.

**Đề xuất: Tham khảo UX và thử PoC chọn lọc; không thay toàn bộ Kho Tri Thức.** Giữ Django/PostgreSQL/Drive và các chứng cứ kiểm thử hiện có; chỉ bổ sung những tính năng có tiêu chí nghiệm thu cụ thể.

## 2. Trạng thái Evernote v11 và các điểm cần phân biệt

| Năng lực / trục kiểm chứng | Điều tài liệu chính thức xác nhận tới 20/11/2026 | Giới hạn, độ tin cậy |
| --- | --- | --- |
| **Phiên bản và thời điểm** | V11 công bố 19/01/2026. Trang What's New ghi rõ **16/11/2026** Tags view/sub-tags, **18/11/2026** gõ notes khi meeting recorder đang thu, **19/11/2026** tùy chỉnh table of contents; release notes desktop/web hiển thị 11.43.4 [E01–E03]. | **Đã công bố**, không xác nhận tài khoản/thiết bị đang ở đúng bản phát hành. |
| **Web Clipper** | Extension Chrome/Safari/Firefox; clip Article, Simplified Article, Full Page, Bookmark, Screenshot, selection; giữ URL, có comment, notebook/tag; smart filing đề xuất notebook/tag [E04–E06]. Clip có chế độ riêng cho YouTube [E05]. | Clip thông tin *trang* không đồng nghĩa tải MP4, có transcript hoặc thu toàn bộ nội dung động; Web Clipper có thể lỗi với multimedia [E04]. |
| **Tìm kiếm** | Keyword, Boolean/filters, semantic, OCR ảnh/chữ viết tay/PDF và text trong tài liệu; match bên trong audio/video **khi có transcript** đưa người dùng đến waveform/moment [E07–E08]. | Semantic search có độ trễ lập chỉ mục; chưa chứng minh chất lượng tiếng Việt. **PDF trên 52 MB/tệp không được xử lý cho tìm kiếm**, khác giới hạn đính kèm [E07]. |
| **AI Assistant và AI Edit** | AI Assistant tìm/tổng hợp, dẫn chiếu note đã dùng và thao tác tổ chức note/tag; **Edit mode** mặc định cho thay đổi tô sáng để duyệt; Ask mode không sửa [E12]. Công cụ **AI Edit** ở toolbar có hộp thoại để Copy và dán kết quả [E13]. | *Hai UX khác nhau*; không gộp thành bảo đảm tự động lưu lịch sử mọi đề xuất. Theo FAQ, Assistant không đọc/chỉnh Word, Excel, audio, video **trực tiếp** dù tìm kiếm có thể dùng OCR/transcript [E12]. |
| **Meeting recorder và AI Transcribe** | Thu hoặc tải file, phân vai speaker, đổi nhãn, play từ từng block (desktop), live transcript, ghi notes khi thu; app hỗ trợ audio/video AI transcription tối đa 2 giờ và 1 GB; trang AI Transcribe standalone còn nhận URL YouTube/social, giới hạn riêng 100 MB/60 phút [E09–E11]. | **Đã công bố**, hiệu năng/ngôn ngữ Việt chưa thử. URL nhập ở **standalone web tool** là bước riêng, không được tính thành tự động xử lý mọi URL trong Evernote. Transcript copy được nhưng tài liệu meeting recorder nói chưa tải riêng transcript/summary từ block; giới hạn xuất provenance [E09]. |
| **Ghi chú và PDF** | Editor rich text, bảng, Markdown shortcut/paste, note history và khôi phục; PDF/image annotation, chuyển trang, annotation summary có số trang [E15, E27, E29]. | Markdown khi paste được **chuyển thành rich text**; không khẳng định giữ nguyên byte Markdown nguồn. PDF viewer mở trang thủ công nhưng deep-link có locator bền vững theo API **chưa xác minh**. Cảnh báo pixelate PDF trên desktop có thể xóa vĩnh viễn nội dung bên dưới [E27]. |
| **Android, Windows, offline** | Có ứng dụng Windows/Android và web. Desktop đồng bộ nội dung về local DB và đọc/sửa offline sau đăng nhập; mobile chủ yếu cache metadata, muốn nội dung đầy đủ offline phải tải note/notebook [E17]. | Chưa test xung đột đồng bộ, IME tiếng Việt, độ mượt 10.000 note trên thiết bị thật. |
| **MCP / API** | What's New công bố **04/08/2026**; dev quickstart có server https://mcp.evernote.com/mcp; dev docs liệt kê **28 tool** (search, semantic, note, tags, tasks, attachments...). OAuth, beta, quyền theo tài khoản, có rate limit; được nêu dành cho gói trả phí [E02, E22–E25]. | **MCP beta đã có tài liệu dùng**, không phải bảo đảm client bất kỳ hoạt động; chưa tự kết nối. Trang landing marketing cũ còn ghi *waitlist/development* [E28], trái với release/dev docs cập nhật; ưu tiên chứng cứ phát hành mới. Classic EDAM API/SDK **deprecated** [E26], không dùng làm căn cứ hứa tích hợp ổn định. |
| **Export/import** | Export desktop Windows/Mac: ENEX hoặc HTML, chọn tối đa 100 note hoặc toàn notebook, ENEX tối đa 300 MB–2 GB mỗi tệp; user Free cũng export được [E14]. Import từ phần Settings nhận .md/.txt/.html/.pdf/.docx thành note chỉnh sửa được [E16]. | **Không tìm thấy xuất Markdown gốc như một lựa chọn chính thức** trong tài liệu export; import Markdown ≠ export Markdown. ENEX/HTML cần chuyển đổi và thử round-trip assets, link, metadata. |
| **Gói phí & quy mô** | Free: 50 note/1 notebook/1 GB/1 thiết bị; Starter: 1.000 note, 20 notebook, 5 GB, 3 thiết bị; Advanced: số note/notebook/attachment và storage được quảng bá *unlimited* nhưng có safeguard limits [E18–E19]. | Với >10.000 mục, Starter **không đủ**; Advanced là mức tối thiểu xét theo số note, không xác nhận thư viện video hàng trăm GB thực tế hoặc backend Drive riêng. Bảng phí FAQ 22/10/2026: USD Starter **$14.99/tháng hoặc $99/năm**, Advanced **$24.99/tháng hoặc $249.99/năm**; giá theo nước/kênh thanh toán/thuế có thể khác [E19]. |
| **Dữ liệu, quyền và license** | FAQ AI nói không dùng nội dung để huấn luyện AI; Semantic Search xử lý indexing trên hạ tầng Evernote, AI Assistant và summary có xử lý bởi OpenAI, có tùy chọn model transcription internal/external [E20–E21]. Chính sách 01/10/2026 nói dữ liệu sync lưu trên server tại Hoa Kỳ [E20]. | Sản phẩm SaaS độc quyền, **không có chứng cứ phát hành mã nguồn để nhúng**; chỉ học UX/đặc tả. Dữ liệu không phải end-to-end encrypted mặc định: hạ tầng dùng server-side encryption; dữ liệu cần giữ riêng/nhạy cảm phải đánh giá chính sách trước khi tải lên [E20, E30]. |

### 2.1. Ba nhầm lẫn có ảnh hưởng trực tiếp tới quyết định

1. **AI xử lý văn bản/ảnh/transcript ≠ AI đã xem và hiểu một video gốc.** Tài liệu Assistant loại trừ đọc trực tiếp audio/video; tìm kiếm timestamp chỉ dựa vào transcript được tạo và có thể sai [E07, E11–E12]. Không gắn nhãn “đã hiểu video” nếu chỉ thấy trang clip/thumbnail/metadata.
2. **Có nút Export ≠ dữ liệu thoát nhà cung cấp theo mô hình Kho Tri Thức.** ENEX/HTML giữ nhiều nội dung và attachment, nhưng chưa chứng minh phục hồi chính xác CaptureEvent, source revision, Drive file ID, phiên bản mô hình hoặc locator transcript vào schema riêng [E14].
3. **Có MCP ≠ API ingestion/backend mở hoàn toàn.** MCP beta thực sự có 28 tool, nhưng phạm vi và limit theo server/client; EDAM classic đã deprecated. Không cam kết có webhook nhận mọi sự kiện, batch sync hàng chục nghìn video hoặc SLA [E22–E26].

## 3. Ma trận K01–K12 (phân loại *khả năng theo tài liệu*)

**Quy ước:** NATIVE = tính năng chính thức trong sản phẩm; EXTENSION = extension/công cụ kèm quy trình riêng; CUSTOM_BACKEND = chỉ đạt yêu cầu đầy đủ nếu bổ sung backend tự làm; NOT_SUPPORTED = có bằng chứng không hỗ trợ; UNVERIFIED = thiếu bằng chứng để khẳng định. Các ô NATIVE luôn ghi rõ phần chưa đáp ứng. **Trạng thái chạy thực tế của cả 12 ca: NOT_RUN; không có dữ liệu/tài khoản Evernote thử.**

| Ca | Phân loại và chứng cứ | Quy trình tái thử, điều kiện PASS / điểm chưa chắc chắn |
| --- | --- | --- |
| **K01** Gõ ghi chú tiếng Việt, receipt, thời điểm | **NATIVE (một phần)**. Tạo note trên Windows/Android, đồng bộ/offline [E17, E29]; **receipt có server timestamp bất biến: UNVERIFIED**. | Nhập “Thử tiếng Việt: ă â ê ô ơ ư đ” cùng giờ, lưu và mở lại; so created/updated note và server time. Chưa tìm tài liệu bảo đảm transaction ACK riêng cho mỗi lần nhập. |
| **K02** Gửi URL video/web, tự lấy metadata và nội dung nếu có | **EXTENSION (một phần)**. Clipper lưu bài/URL/YouTube clip [E04–E06]; AI Transcribe standalone nhận URL YouTube/social và có Save to Evernote [E11]. | Clipper một URL bài báo, một Facebook Reel, một YouTube Shorts; kiểm URL, title, article text, metadata, media bytes, transcript, lỗi. **Không coi clip URL là đã tải video**; không thấy tài liệu native cho TikTok/Facebook tự động download & storage ở quy mô cần thiết. |
| **K03** URL trùng ngày sau vs retry | **UNVERIFIED**. Evernote có note history [E29], nhưng không có đặc tả sự kiện tiếp nhận/idempotency tương ứng [B02]. | Gửi cùng URL hai ngày, retry cùng request key sau timeout; cần một Item và hai CaptureEvent với hai giờ; retry không thêm Event. Nếu chỉ xuất hiện một note/modified time thì **FAIL so với yêu cầu của kho**. |
| **K04** Markdown, bảng, links, Unicode round-trip | **NATIVE (một phần)**. Shortcut/paste Markdown có bảng/link [E15], import .md [E16]. | Dán .md UTF-8 gồm CRLF, bảng, dấu tiếng Việt, code, link rồi export/reimport; diff ký tự/ngắt dòng. Vì paste **chuyển rich text**, **chưa xác minh** bảo toàn Markdown nguyên văn; bản thân tính năng định dạng được xác nhận. |
| **K05** Phát hiện nhóm và tự gán vào nhóm có sẵn | **UNVERIFIED cho điều kiện tự gán không cần xác nhận**. Web Clipper smart filing *đề xuất* notebook/tag [E06]; Assistant có lệnh tạo/thêm tag và chuyển notebook [E12]. | Chuẩn bị 10 nhóm có sẵn, gửi 30 mục chưa nhãn, không nhấn chọn suggestion; đo số note tự gán nhóm đúng, không tạo trùng, không ghi đè tag thủ công. Không suy từ “smart filing” thành tự gán nền chắc chắn. |
| **K06** Mục liên quan/backlinks cạnh bài | **NATIVE (một phần)** ở semantic results và note linking; **graph có cạnh/quan hệ có phiên bản: UNVERIFIED** [E07–E08, E12]. | Soạn 3 note cùng nghĩa khác từ khóa, kiểm gợi ý liên quan ngay trong item, backlinks hai chiều, lý do, khả năng dismiss. Chưa xác minh mối liên hệ lưu thành đối tượng riêng kiểu RelatedItem. |
| **K07** PDF/audio/video với page/timestamp trích dẫn | **NATIVE (một phần)**. PDF annotation/chuyển trang [E27]; transcript search khớp audio/video theo waveform, play từ speaker block [E07, E09]. | Đính 3-page PDF và đoạn MP4 có câu ở 00:41; bấm search match phải nhảy đúng thời gian; lưu lại locator trang/giây, reload rồi mở. **Persistent deep-link vào PDF page/transcript segment và export locator: UNVERIFIED**; transcript phụ thuộc xử lý thành công. |
| **K08** Một bài đa lĩnh vực và nhiều chế độ xem | **NATIVE (một phần)** qua tags, notebook, Spaces, nested tags [E02, E18]. **Toàn bộ tree/table/card/timeline theo cùng Item: UNVERIFIED**. | Gán note vào 2 tags ở 2 cây; tìm qua cả hai mà không nhân note; thử chuyển nhanh tree, table, card, timeline. Notebook không được coi đương nhiên là nhiều cha. |
| **K09** Android + Windows offline/conflict | **NATIVE** Windows/Android, offline desktop, offline note/notebook mobile [E17]; **conflict behavior: UNVERIFIED**. | Download note offline Android, sửa đồng thời Windows mất mạng rồi reconnect; kiểm hai phiên bản, bản gốc và lịch sử; cần ghi rõ sync conflict nếu xảy ra. Không test thiết bị thật. |
| **K10** API, Markdown/assets, backup/exit | **NATIVE (một phần)** ENEX/HTML desktop/đính kèm [E14]; **MCP beta** cho đọc/ghi/nội dung attach [E22–E25]; Markdown **import** [E16]. | Export notebook lớn theo ENEX + HTML, đọc lại tags/created_at/attachment/binary/hash; chuyển thành Markdown và import về DB riêng. Markdown native export/round-trip locator và bulk API ổn định **UNVERIFIED**; classic EDAM deprecated [E26]. |
| **K11** AI dẫn nguồn, suggestion vs nội dung gốc, quyền/chi phí | **NATIVE (một phần)** Assistant cite note, Ask/Edit, highlight chỉnh sửa, nút duyệt; AI privacy và model toggles [E12–E13, E21]. | Cho AI hỏi 5 fact có nguồn; đối chiếu citation với note/sentence; Edit mode sửa bài rồi reject, hash nội dung phải giữ nguyên; bật/tắt từng AI; khảo sát credit/rate limit từng gói. **Cite ở cấp video timestamp và sổ kiểm toán từng sửa: UNVERIFIED**. |
| **K12** >10.000 item + hàng trăm GB Drive/remote | **UNVERIFIED**. Advanced quảng bá notes/storage unlimited nhưng có safeguard limits [E18–E19]; app AI Transcribe max 1GB/2h, PDF search max 52MB [E07, E11]. | Benchmark 10k–20k items + file nhiều TB/GB, filter/search/backup, hỏng mạng/khôi phục; chứng minh tài sản vẫn ở Drive với ID bất biến và không tái tải. Không thấy bằng chứng kiến trúc “Evernote làm UI trên 500GB Google Drive mà không sao chép media”. |

**Thống kê phân loại chính trên 12 ca:** **NATIVE 8** (K01, K04, K06, K07, K08, K09, K10, K11; mỗi ca vẫn có phần chưa kiểm), **EXTENSION 1** (K02), **UNVERIFIED 3** (K03, K05, K12); tổng **8 + 1 + 3 = 12**. Đây **không phải số PASS**: 12/12 ca thử thực tế đều **NOT_RUN**. Những điều kiện thiếu trong ca NATIVE vẫn được liệt kê rõ trong cột đánh giá.

## 4. Đối chiếu với code thật Kho Tri Thức

Nguồn baseline trực tiếp: [B01–B12], không đọc đánh giá nhóm khác. **Không suy code = đã nghiệm thu thiết bị thật**. Docs CURRENT_STATE có bằng chứng CI và Windows live theo hạng mục nhưng xác nhận Android, seek timestamp, video nhiều nguồn và chất lượng tiếng Việt còn chưa chạy [B01].

| Nghiệp vụ | Kho Tri Thức main hiện có (theo file code; bằng chứng kiểm thử ở B01) | Evernote đáng học / giới hạn |
| --- | --- | --- |
| **Gửi và giữ nguồn** | CaptureSubmission/CaptureEvent, idempotency theo owner/channel/key, giờ server và re-send URL tạo event khác, nguyên URL giữ [B02–B03]; giao diện text/link/file, tối đa upload 128 MiB [B04]. | Web Clipper có lựa chọn article/selection/bookmark/screenshot tốt hơn UI của kho. **Không thay** event ledger bằng note modified time. |
| **Văn bản chính** | Item.note giữ Markdown, KnowledgeText dùng react-markdown + remark-gfm, skipHtml, chặn URL ngoài HTTP(S); có trình đọc Tri thức; markdown import/extract [B05–B07]. | Evernote editor rich text, TOC, bảng và công cụ sửa dễ dùng; nhưng round-trip Markdown nguồn không được xác nhận. **Học UX, không đổi định dạng gốc sang ENEX**. |
| **Phân cấp & đa lĩnh vực** | Topic.parent/node_kind và ItemTopic M:N, rule-based OrganizationService gán Topic/Project/Tag có version/confidence; RelatedItem riêng và stale [B08–B09]. | Cách tô màu/nested tags và lọc Tags view đẹp, nhưng không thay schema nhiều nhánh của kho. Evernote smart filing cần thử độ đúng. |
| **Tìm kiếm** | SearchService Postgres, tìm theo Item/DerivedContent, lịch sử annotation, tiếng Việt có/không dấu, có nguồn [B10]. | OCR PDF/ảnh, semantic search, search modal, highlight đúng match, waveform. Nên thử search UX và PoC semantic **sau khi có corpus gán nhãn**; không nhúng model nặng ngay. |
| **Video/transcript** | Worker yt-dlp/Drive verify; ASR local faster-whisper có segments/locator và needs_review trong ReadKnowledgeService [B01, B11]; UI hiện đọc text nhưng chưa nhảy từ transcript sang playback mốc [B06–B07]. | Evernote chứng minh pattern **search match → waveform/segment → play**, nhưng không thay yt-dlp + Drive ID. Đây là khoảng trống UI có giá trị cao. |
| **File và backup** | Asset/StorageLocation Google Drive, bản sao manifest v3/restore, KnowledgeExport per-Item versioned [B01, B12]. | ENEX/HTML dễ xuất toàn notebook, nhưng kho đã có portability theo schema riêng, hash/recovery test; không đổi hệ thống lưu chỉ vì Evernote nói unlimited. |
| **AI và dẫn xuất** | DerivedContent giữ processor, version, locator, không ghi đè Item.note; hiện related chủ yếu lexical, semantic AI chưa là backend sản xuất [B06, B09–B11]. | Ask/Edit với thay đổi tô sáng cần áp dụng bằng bản nháp/patch rõ ràng. Không nhầm AI Assistant đọc note với việc có được video transcript đã kiểm duyệt. |
| **Windows/Android** | Windows native/live và Compose CI theo B01; web frontend/PWA; Android thiết bị thật chưa nghiệm thu. | Evernote offline mobile là đối chứng tốt nhưng không làm mất gate Android thật của kho. |

### 4.1. Sự thật triển khai để tránh “đánh giá dựa trên kế hoạch”

- Kho **đã có mã** React/Django/Postgres, ghi chú Markdown, CaptureEvent, gán nhóm có bằng chứng và ASR local; không nên gọi chúng “chưa lập trình” chỉ vì một đoạn docs cũ ghi future [B01–B11].
- B01 nêu Windows với 211 backend PASS, 19 frontend PASS/build PASS ở mốc KT-113 và một Reel đã verify file Drive; **chỉ phạm vi đó**. Không tự chạy lại test ở G04. Chất lượng video tiếng Việt, 10.000 mục, Android, seek theo đoạn và nhiều nền tảng vẫn **NOT_RUN**.
- Evernote cũng **chưa được G04 chạy thử**; không so benchmark giữa “source code có thật” và “marketing được coi như test”.

## 5. Chấm 7 trụ: thang 100, mức bất định được giữ thành khoảng

Điểm *chuyên gia dựa trên chứng cứ/tài liệu* cho đúng yêu cầu Kho Tri Thức; không phải speed/accuracy benchmark. **UNVERIFIED không bị gán 0**; khoảng điểm lớn khi thiếu dữ liệu hoặc gói sử dụng chưa thử.

| Trụ | Trọng số | Khoảng điểm G04 | Lý do / độ tin cậy |
| --- | ---: | ---: | --- |
| Capture + ingestion | 20 | **10–14** | Web Clipper mạnh; không có bằng chứng immutable receipt, lưu/retry video đa nền tảng; **trung bình** [E04–E06, E11]. |
| Organization + recall | 20 | **11–15** | Tag/nested tags, smart filing, semantic search tốt; thiếu bằng chứng auto-group có version/cạnh RelatedItem; **trung bình** [E02, E06–E08]. |
| Text editor + reading | 15 | **11–14** | Editor/TOC, Markdown shortcut, AI edit; thiếu raw Markdown portability; **cao cho tính năng, trung bình cho round-trip** [E02, E12, E15]. |
| Provenance / related / timestamp | 15 | **7–10** | Search/audio timestamp có thật; thiếu capture ledger và xuất locator theo ID; **trung bình** [E07, E09, E14]. |
| Android / Windows / offline | 10 | **7–9** | Hai nền tảng, desktop offline, mobile tải offline; conflict và tiếng Việt NOT_RUN; **cao về nền tảng, thấp về stress** [E17]. |
| Portability / backup | 10 | **4–6** | ENEX/HTML/attachment export có, nhưng không native Markdown, khó bảo toàn schema/provenance; **cao về định dạng, thấp về round-trip** [E14–E16]. |
| Integration / cost / maintainability | 10 | **4–6** | MCP beta là điểm cộng, EDAM deprecated, phí và lock-in còn đáng kể; **trung bình** [E18–E19, E22–E26]. |
| **Tổng (cộng min/max)** | **100** | **54–74/100** | Không thay các khoảng chưa biết bằng điểm trung tâm giả tạo. |

**Hai kết luận độc lập:** (1) *Thay toàn hệ thống*: **không đề xuất**, vì K03/K10/K12 là ràng buộc dữ liệu cốt lõi; điểm tính năng không bù được thiếu event provenance/Drive ownership. (2) *Học và tái sử dụng tính năng*: **cao**, chủ yếu Web Clipper, search-to-locator, AI diff approval, tag/search UX; vẫn phải thử PoC nhỏ.

## 6. Đề xuất 6 ý tưởng, không viết lại backend

Ưu tiên theo hiệu quả với **mã đã có**, không phải sao chép code độc quyền.

| ID / Ý tưởng | Hình thức / độ khó | Phụ thuộc và rủi ro | Acceptance đo được |
| --- | --- | --- | --- |
| **G04-I1: Capture mode như Web Clipper** | UX + browser extension/adapter; **M** | Dùng CaptureService có sẵn, fetch web an toàn, sanitize HTML; nội dung động/bản quyền và trình duyệt khác nhau. | Cho lưu Article/Simplified/Selection/Bookmark, cùng URL gửi hai lần sinh **2 Event / 1 Item** khi identity chắc, retry cùng key **1 Event**; không ghi đè note người dùng hoặc lưu raw HTML lâu dài [B02, E04]. |
| **G04-I2: Search match → đúng vị trí nguồn** | UX + player/locator adapter; **M** cho transcript, **L** nếu bổ sung PDF anchor bền vững | Dùng DerivedContent.source_locator có sẵn và time segments từ ASR; phải tránh tự đoán offset; kiểm seek media được phép. | 20 fixture audio/video có timestamp: click match → play bắt đầu sai lệch ≤1 giây so với start segment; 10 PDF có locator: mở đúng trang ±0; không hiện click-to-seek khi chỉ có text không có locator. |
| **G04-I3: AI Edit theo patch duyệt từng phần** | UX + optional AI adapter; **M** | Không gửi dữ liệu riêng tư cho model ngoài khi chưa opt-in; giữ user_edit_version, note gốc, rollback và provenance [B06, E12–E13]. | 10 ca tiếng Việt: reject/cancel làm SHA Item.note **không đổi**; accept đúng patch tăng edit version một lần; diff hiển thị 100% chỗ thay, không tự áp AI khi tái trích nguồn; undo hiệu quả. |
| **G04-I4: Tags view và đường dẫn nhóm rõ ràng** | UX trước, metadata color; **S–M** | Giữ Topic tree và nhiều ItemTopic, không ép một notebook duy nhất. Nested tags chỉ thêm nếu phân biệt rõ tag với Topic. | Trên 100 mục thử, lọc theo tag màu/tầng và theo nhánh không nhân Item; chuyển tab/tìm tag trong ≤3 tương tác; kiểm screen nhỏ/keyboard/accessibility. |
| **G04-I5: Search modal có highlight + saved search** | UX và truy vấn hiện hành; **S–M** | Tận dụng SearchService; link tới source locator khi thật sự có; lưu filter/saved query theo owner. | 30 truy vấn tên/tag/text/derived: highlight đúng fragment, filter kết quả đúng tập; không lộ dữ liệu owner khác; tìm nhanh bằng keyboard; truy vấn tiếng Việt có/không dấu. |
| **G04-I6: Semantic retrieval có điều kiện (không mặc định)** | PoC SearchService adapter, **M**; rollout tùy kết quả | Cần tập 50–100 item tiếng Việt con người gán nhãn, đánh giá quyền riêng tư/chi phí; không tự tạo embedding stack mới khi chưa có lợi ích [E07–E08, B10]. | Recall@5 tăng ≥10 điểm phần trăm so với lexical trên 50 query đã định trước, false-related không tăng quá 5 điểm phần trăm, lưu model/version, opt-out khả dụng. Nếu không đạt: giữ PostgreSQL search cũ. |

**Thứ tự khuyến nghị:** I2 → I1/I5 → I3 → I4 → I6 (chỉ khi dữ liệu và cơ sở đánh giá đủ). Không cài extension Evernote, SDK không rõ phép, hoặc đưa dữ liệu người dùng vào SaaS để “thử nhanh”.

## 7. Quyết định, giới hạn và phản chứng

**Quyết định G04:** **“Tham khảo UX” ngay ở cấp tài liệu; “Thử PoC”** I1/I2/I3/I5 khi G00 ưu tiên và giao coding; **không tích hợp thư viện Evernote, không thay toàn bộ**. Đề xuất này không thay đổi kiến trúc hiện hành hay nhiệm vụ gốc.

### Rủi ro phải giữ riêng

1. **Khóa dữ liệu/định dạng:** Evernote export ENEX/HTML, không phải raw Markdown/manifest; nhiều tệp media và metadata có thể mất mapping khi chuyển đổi [E14–E16].
2. **Chi phí/quy mô:** Starter không đáp ứng 10k item; Advanced phí định kỳ, giới hạn “unlimited” vẫn chịu safeguards, transcript/file/search có cap khác nhau [E07, E11, E18–E19].
3. **Nguồn và tính đúng:** Audio transcript phụ thuộc model/lang; AI có thể sai; những gì đã cắt từ web không bảo đảm video được tải hoặc hiểu [E04, E07, E11–E12].
4. **Riêng tư và nơi lưu:** sync server Hoa Kỳ, AI processing cần đọc kỹ; “không huấn luyện” không đồng nghĩa nội dung không xử lý trên cloud. Đặc biệt không đưa dữ liệu công vụ/riêng tư vào sản phẩm khi chưa được phép [E20–E21].
5. **Tích hợp tương lai:** MCP đang beta và rate limit, legacy API deprecated; không đặt backend ingestion hàng chục nghìn file lên một giao diện chưa đo [E23–E26].
6. **An toàn tài liệu:** thao tác pixelate/redaction PDF có thể xóa nội dung thật, cần bản gốc immutable nếu học thiết kế annotation [E27].

### Giả thuyết có thể đảo chiều

Quyết định **“không thay”** chỉ đáng xem lại khi một thử nghiệm *có quyền* chứng minh đồng thời: (a) 10k+ note và hàng trăm GB media lưu/đọc có kiểm hash, không buộc nhân bản vô kiểm soát khỏi Drive; (b) hai lượt share cùng URL vẫn có lịch sử tiếp nhận bất biến, phân biệt retry; (c) export → restore giữ Unicode, assets, source/version/locator và kiểm SHA; (d) Android/Windows offline conflict không mất ghi chú; (e) tổng chi phí 3 năm và pháp lý dữ liệu chấp nhận được. **Không có chứng cứ này ở 20/11/2026**.

**Phản chứng với kỳ vọng “Evernote tốt nên phải thay”:** nếu mẫu 50 video chủ yếu chỉ clip trang/link còn MP4/ASR phải làm thủ công, nếu ENEX không giữ giờ từng lần gửi hoặc nếu 30% transcript Việt sai từ khóa quan trọng, thì việc chuyển hệ thống sẽ làm mất năng lực cốt lõi dù UI Evernote tốt hơn. Cần thử, không định trước kết quả.

## 8. Kiểm tra phương pháp và trạng thái bàn giao

- [x] Đọc giao việc G04 và quy trình G00; không đọc nguồn sơ bộ G00 hoặc báo cáo khác.
- [x] Đọc main ở SHA ghi trên đầu, đối chiếu cả docs lẫn code thay vì xem kế hoạch là hiện trạng.
- [x] Tra tài liệu/release note **tới 19/11/2026**, tách năng lực công bố, beta, gói phí, limitation và thông tin tự suy.
- [x] Lập đủ K01–K12, nguồn, bước tái thử, 7 trụ, quyết định và điều kiện đảo chiều.
- [ ] **NOT_RUN**: thao tác UI Evernote bằng tài khoản thật, export/import thật, OCR/ASR/semantic tiếng Việt, benchmark 10k note/500GB và chi phí thanh toán thực tế.
- [ ] **NOT_RUN**: chạy test app Kho Tri Thức tại máy trong luồng nghiên cứu (chỉ đối chiếu evidence/CI trên repo; không tái ghi nhận PASS).
- **Files thay đổi:** chỉ file báo cáo G04 này. **Không đổi application code, master plan, roadmap hay trạng thái chung**.
- **Kiểm soát tính đúng:** tránh diễn giải “không tìm thấy” thành “chắc chắn không hỗ trợ”; những nội dung chưa có bằng chứng được giữ là UNVERIFIED. Bảng đánh giá yêu cầu **recheck** khi bản Evernote thay đổi.

## 9. Nguồn đã tra cứu (truy cập 20/11/2026)

### 9.1. Evernote — nguồn chính thức (chủ yếu 2026)

- **[E01]** V11, ngày 19/01/2026: https://evernote.com/en-us/blog/introducing-v11
- **[E02]** What's New, bao gồm 04/08/2026 MCP; 28/07/2026 AI Edit; 16–19/11/2026 Tags, Meeting Notes và TOC: https://evernote.com/whats-new
- **[E03]** Release notes desktop/web phiên bản 11.43.4 khi tra: https://evernote.com/en-us/release-notes
- **[E04]** Web Clipper Quick Start: https://help.evernote.com/hc/en-us/articles/209125877-Evernote-Web-Clipper-Quick-Start-Guide
- **[E05]** Clip formats, YouTube, smart filing: https://help.evernote.com/hc/en-us/articles/209125827-Clip-formats
- **[E06]** Web Clipper settings và smart filing: https://help.evernote.com/hc/en-us/articles/208314738-Evernote-Web-Clipper-settings
- **[E07]** Search overview, PDF 52 MB, transcript waveform, text highlighting: https://help.evernote.com/hc/en-us/articles/360040282613-Search-overview
- **[E08]** Semantic Search: https://help.evernote.com/hc/en-us/articles/45706285591955-Semantic-search
- **[E09]** Meeting recorder, live transcript, speaker blocks, notes typed while recording: https://help.evernote.com/hc/en-us/articles/45695698380563-Meeting-recorder
- **[E10]** Audio recording, search highlighted moment, thiết bị: https://help.evernote.com/hc/en-us/articles/46398549125011-Audio-recording-in-Evernote
- **[E11]** AI Transcribe FAQ, *app* vs *standalone* và giới hạn khác nhau: https://help.evernote.com/hc/en-us/articles/40725583696787-AI-Transcribe-FAQ
- **[E12]** AI Assistant, Edit/Ask, citation và giới hạn trực tiếp media: https://help.evernote.com/hc/en-us/articles/46319409880211-AI-Assistant
- **[E13]** AI Edit dạng dialog riêng: https://help.evernote.com/hc/en-us/articles/41938251046163-AI-Edit
- **[E14]** Export ENEX/HTML desktop, limit 100 note/toàn notebook, tệp 300MB–2GB (bài cập nhật 12/03/2025; đối chiếu với 2026): https://help.evernote.com/hc/en-us/articles/209005557-Export-Notes-and-Notebooks-as-ENEX-or-HTML
- **[E15]** Markdown copy/paste hỗ trợ một phần: https://help.evernote.com/hc/en-us/articles/39988720040211-Markdown-support-and-copy-paste-behavior
- **[E16]** Import .md/.txt/.pdf/.docx: https://help.evernote.com/hc/en-us/articles/208314308-Import-content-from-other-apps-into-Evernote
- **[E17]** Offline Windows/mobile: https://help.evernote.com/hc/en-us/articles/209005177-Set-up-offline-notes-and-notebooks-on-mobile-devices
- **[E18]** Current plan capacities: https://evernote.com/compare-plans
- **[E19]** Starter/Advanced USD giá, cập nhật **22/10/2026**; nội dung “AI coming soon” trong bảng này **đã cũ** so với [E02,E12]: https://help.evernote.com/hc/en-us/articles/46317642175763-Discontinuing-Evernote-Personal-Professional-Introducing-Starter-Advanced-FAQ
- **[E20]** Privacy Policy, ngày 01/10/2026, US data location: https://evernote.com/en-us/privacy/policy
- **[E21]** AI Features FAQ, mô hình nội bộ/ngoài, giới hạn, không train: https://help.evernote.com/hc/en-us/articles/45353174499475-Evernote-s-AI-Features-FAQ
- **[E22]** MCP server quickstart & OAuth URL: https://dev.evernote.com/mcp/quickstart
- **[E23]** MCP 28 tools: https://dev.evernote.com/mcp/tools
- **[E24]** MCP known limitations, beta: https://dev.evernote.com/mcp/limitations
- **[E25]** MCP FAQ: rate limits và paid plans: https://dev.evernote.com/mcp/faq
- **[E26]** Classic API/SDK đã deprecated: https://dev.evernote.com/legacy
- **[E27]** PDF annotation, page navigation, destructive redaction: https://help.evernote.com/hc/en-us/articles/209005587-Annotate-images-and-PDFs
- **[E28]** **Nguồn mâu thuẫn cũ, không ưu tiên:** Evernote marketing MCP still “in development”: https://evernote.com/model-context-protocol/access-evernote-notes-with-ai
- **[E29]** Note History: https://help.evernote.com/hc/en-us/articles/208313858-Use-note-history-to-view-and-restore-older-versions-of-a-note
- **[E30]** Security Overview, TLS/server-side encryption: https://evernote.com/legal/security

### 9.2. Kho Tri Thức — mã và kiểm thử ở baseline main

- **[B01]** Hiện trạng mốc 20/11, rõ PASS/NOT_RUN và liên kết CI: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/docs/CURRENT_STATE.md
- **[B02]** CaptureService, unique retry, giờ nhận: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/ingestion/services.py
- **[B03]** CaptureEvent model/unique constraint: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/ingestion/models.py
- **[B04]** Capture UI text/link/file: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/CaptureScreen.tsx
- **[B05]** Markdown renderer/chặn external links: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/KnowledgeText.tsx
- **[B06]** ReadKnowledgeService và source provenance: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/read_knowledge.py
- **[B07]** KnowledgeReading UI: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/KnowledgeReading.tsx
- **[B08]** Item/Topic/ItemTopic/Source/RelatedItem models: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/models.py
- **[B09]** OrganizationService/group assignment/related lexical version: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/organization.py
- **[B10]** SearchService: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/search/services.py
- **[B11]** Transcript worker + locators: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/transcript_job.py
- **[B12]** Drive-based exported knowledge: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/storage/knowledge_export.py

**Kiến nghị gửi G00:** Xét PR như một báo cáo nghiên cứu/khuyến nghị; không merge hay coi bất kỳ PoC nào đã PASS chỉ vì có đề xuất ở đây.
