# G07 — Báo cáo nghiên cứu độc lập Mem.ai

**Ngày đánh giá:** 20/11/2026 (Asia/Ho_Chi_Minh)  
**Người thực hiện:** luồng G07; chỉ nghiên cứu Mem.ai, không xem báo cáo/điểm số của luồng khác.  
**Đối chứng:** Kho Tri Thức, repository cavoixanh638/kho-tri-thuc, main tại commit **c97f5678a6893d7dfec2595d89c9122f05195320**.  
**Phương pháp:** đọc thông báo, Help Center, API docs và blog chính thức; đối chiếu trực tiếp source của repo ở commit trên và checkpoint CURRENT_STATE. **Không đăng nhập tài khoản Mem, không gọi API/MCP, không tải extension, không nạp dữ liệu người dùng hoặc chạy kiểm thử sản phẩm: PRODUCT_LIVE = NOT_RUN.**  
**Phạm vi commit:** duy nhất báo cáo này; không thay đổi mã nguồn, kế hoạch hay checkpoint hệ thống.

## 1. Executive summary (dưới 200 từ)

**Kết luận: không dùng Mem.ai để thay thế hoặc làm dịch vụ tích hợp cho Kho Tri Thức.** Ngày 16/11/2026, chính Mem công bố chuyển ghi chú sang chỉ đọc từ 18/12/2026 và đóng dịch vụ ngày 15/01/2027 [S01]. Bất cứ phương án phụ thuộc Mem API/MCP, lưu file gốc trên Mem hay di chuyển toàn bộ kho sang Mem đều là rủi ro không thể chấp nhận.

Tuy nhiên, sản phẩm để lại bài học UX rõ ràng: Heads Up tự đưa ghi chú liên quan bên cạnh văn bản đang đọc; Collections có thể xếp một ghi chú vào nhiều nhóm; Clean Up đề xuất thay đổi có bước xem diff và chấp nhận; clipper có thể bổ sung nội dung vào ghi chú hiện hữu; bản xuất Markdown/collection/attachment hỗ trợ rời nền tảng. Repo Kho Tri Thức đã có CaptureEvent, cây Topic đa nhánh, RelatedItem, Markdown, lưu nguồn và backup. Nên **tham khảo 5–6 tương tác chọn lọc**, không viết lại Django/PostgreSQL/Drive và không sao chép mã sở hữu của Mem. Những hiệu năng, tiếng Việt, Android và quy mô lớn chưa được thử phải giữ nhãn NOT_RUN/UNVERIFIED.

## 2. Bối cảnh sống còn: đóng dịch vụ và khả năng rút dữ liệu

| Sự kiện | Ngày / trạng thái được xác nhận | Ý nghĩa |
| --- | --- | --- |
| Thông báo đóng Mem | **16/11/2026**, nguồn chủ sở hữu [S01] | Không nên thiết kế tính năng mới phụ thuộc endpoint Mem |
| Thu phí / gói mới | Thu phí đã tạm dừng, **không nhận đăng ký trả phí mới** [S01, S02] | Bảng giá cũ không còn là giá mua dịch vụ tháng 11/2026 |
| Chỉ đọc | **18/12/2026** [S01] | Không còn tạo/sửa note, vẫn đọc và export |
| Ngừng dịch vụ | **15/01/2027** [S01] | Không truy cập sau hạn; không được coi lưu trữ cloud là bền vững |
| Mức độ bảo đảm | Thông báo chính thức; chưa thử tài khoản thực | Mốc có độ tin cậy cao, hành vi export thực tế = NOT_RUN |

**Quy trình export do Mem công bố [S03, S04]:** đăng nhập trên máy tính → Settings → Exports → Start new export → My Computer → Start export → Download ZIP. Giữ cả ZIP và bản giải nén. Kiểm thư mục **notes/** (mỗi note một file Markdown), **collections/** (chỉ mục liên kết, một note có thể nằm ở nhiều collection), **attachments/** (file khả dụng, cần giữ quan hệ đường dẫn tương đối), và **export-report.md** nếu có (các nội dung không thể xuất). Transcript có thể đi kèm nếu tồn tại; **recording audio gốc phải chủ động chọn tùy chọn xuất**. Không đồng nhất note họp, transcript và bản ghi âm. Đối chiếu số lượng, nội dung, link và media trước khi coi migration thành công.

**Lỗ hổng round-trip:** nhập Mem chỉ nhận .md/.txt, có giới hạn thao tác khoảng 1.000 file/lần; không nhập cấu trúc folder hay attachment tự động [S05]. Vì thế “có export Markdown” không chứng minh nhập sang nền tảng khác sẽ bảo toàn trọn vẹn liên kết, bản ghi, quyền, lịch sử phiên bản hoặc mối quan hệ. Không có export Mem thực để chạy checksum nên chưa thể xác nhận tỷ lệ bảo toàn.

## 3. Tính năng và vòng đời, tách phát hành với beta/không được chứng minh

| Năng lực | Bằng chứng & trạng thái theo tài liệu | Hệ điều hành, hạn chế và độ tin cậy |
| --- | --- | --- |
| Editor, Markdown, bảng, @mentions, phiên bản | Help Center mô tả editor, version history [S06, S07]; tính năng có tài liệu sử dụng | Đọc như **đã được mô tả là phát hành**; chưa test dấu tiếng Việt/import–export byte-for-byte |
| Collections và Auto-organize | Một note thuộc nhiều collection; thao tác Organize → Auto-organize **thử thêm vào collection hiện có hoặc tạo mới** [S08] | Có action thực; **không suy ra tự xếp mọi note sau khi nhận** hoặc tỷ lệ đúng cao |
| Related Notes → Copilot → Heads Up | Tài liệu chuyển đổi Mem 2.0 (2025) gọi Copilot là tên tiếp nối Related Notes [S09]; Help Center 2026 mô tả Heads Up dạng panel: Meeting Timeline, Related Topic Bundle, Related Collections [S10] | Đây là lịch sử khái niệm/tên gọi theo các thời điểm; **không chứng minh cùng thuật toán** hay precision |
| Search và AI recall | Keyword + Deep Search theo ý nghĩa [S11]; Chat truy vấn/sửa/tổ chức [S12] | Tính năng được hãng mô tả; corpus tiếng Việt và provenance câu trả lời chưa đánh giá độc lập |
| Chrome Web Clipper | Đoạn văn/trang web/YouTube, AI tóm tắt và chọn note cũ/collection [S13] | **EXTENSION**, yêu cầu Chrome/đăng nhập; không suy ra lấy toàn bộ hình/âm thanh Facebook, TikTok hay MP4 nguồn |
| PDF & image understanding | Tự index file tải lên, tìm/trích trang PDF và bấm citation [S14] | Help mô tả tối đa 100 trang chi tiết/tài liệu và 25 MB/file; Free 25 trang PDF/tháng, Pro không giới hạn tổng trang tháng nhưng vẫn ngưỡng tài liệu; giới hạn công bố trước shutdown có thể đổi |
| Voice/meeting note | Voice Mode ghi âm/chuyển lời nói thành note [S15]; calendar source card với tên sự kiện, người tham dự [S16] | Không có chứng cứ mọi câu có timestamp seek chính xác |
| Heads Up Live + Meeting Briefings | Blog **23/03/2026** ghi rõ **beta chỉ cho Pro** [S16] | Không chuyển thành GA chỉ vì trang hỗ trợ có nhắc đến Heads Up |
| Offline/sync | Help mô tả lưu note/sửa tại máy rồi đồng bộ khi có mạng [S17] | Windows/Mac/iOS/Web được hướng dẫn ở nguồn sản phẩm; **không tìm được bằng chứng Android native + share target**. Xung đột đa thiết bị chưa test |
| API, MCP | REST API docs Mem It POST /v2/mem-it trả request ID, xử lý nền [S18]; MCP **hosted OAuth** có read/create/search/organize/edit [S19] | Không phải thư viện mã nguồn mở hay MCP tự host; API request ID không phải bằng chứng cho receipt giờ server bất biến |
| Giá, privacy, license | Pricing chính thức hiện thông báo không nhận thuê bao trả phí mới [S02]. Privacy policy sửa 13/08/2026: cam kết không bán dữ liệu hoặc dùng dữ liệu để huấn luyện mô hình AI tổng quát, nhưng có nhà cung cấp xử lý [S20] | Các gói Free/Pro trong help là phân tầng tính năng **lịch sử**, không phải giá mới. Không có bằng chứng source code/MCP server được mở license; không đề xuất copy code. Privacy là tuyên bố chủ sở hữu, chưa audit độc lập |

**Lưu ý về bằng chứng:** Help Center không hiển thị ngày xuất bản từng trang trong nội dung được truy cập 20/11/2026; dùng trạng thái “theo help hiện có” thay vì tự gán release date. Blog 2025 là **lịch sử**, blog tháng 3/2026 chỉ xác nhận beta tại ngày công bố. Không suy diễn beta đã lên stable tới 20/11/2026. Câu “AI hiểu PDF hoặc YouTube clip” cũng **không đồng nghĩa** AI hiểu toàn bộ video/audio gốc, đặc biệt khi chỉ có metadata/summary.

## 4. Ma trận kiểm tra chung K01–K12

**Quy ước:** NATIVE = được Mem mô tả như tính năng sản phẩm; EXTENSION = cần tiện ích; CUSTOM_BACKEND = phải xây phần riêng mới đáp ứng; NOT_SUPPORTED = tài liệu xác nhận thiếu phần bắt buộc; UNVERIFIED = chưa đủ chứng cứ cho **trọn tình huống**. Trạng thái phản ánh tài liệu, **không phải PASS kiểm thử**. Cột “Cách tái thử” là recipe nếu có tài khoản/môi trường hợp lệ; **K01–K12 đều PRODUCT_LIVE = NOT_RUN**, không dùng dữ liệu cá nhân.

| Ca | Trạng thái có điều kiện | Chứng cứ và phạm vi / thiếu chắc chắn | Cách tái thử có thể kiểm toán |
| --- | --- | --- | --- |
| **K01** Note tiếng Việt, receipt giờ nhận | **UNVERIFIED** | Editor native [S06], Mem It trả request ID nền [S18]; chưa chứng minh timestamp **server-received bất biến** của note và receipt | Tạo note “Tiếng Việt: Hải Phòng, ă â ê ơ ư đ”; chụp receipt và so giờ server, sửa rồi đọc lại; NOT_RUN |
| **K02** URL video/web, metadata + nội dung | **EXTENSION (partial)** | Chrome clipper có trang, đoạn trích, YouTube summary [S13]; không chứng minh video full-content, TikTok/Facebook hoặc timestamp | Clip URL web và YouTube, ghi nguồn và kiểm raw URL/title/summary/transcript/asset riêng; NOT_RUN |
| **K03** Link trùng sau một ngày ≠ HTTP retry | **UNVERIFIED** | API xử lý bất đồng bộ [S18]; không thấy đặc tả idempotency key vs capture-event lặp | Gửi cùng link với key A, retry A, gửi key B sau đổi ngày; đếm event/Item và giờ; NOT_RUN |
| **K04** Markdown, bảng, link, Unicode round trip | **NATIVE (partial)** | Editor [S06], export ZIP .md [S03], import .md/.txt [S05]; không bảo đảm bảo toàn Unicode/nội dung bảng 100% | Tạo 1 bảng tiếng Việt/NFC/NFD/link, export, import lại, so diff và link; NOT_RUN |
| **K05** Tìm nhóm sẵn có và **thực sự gán** | **NATIVE** | Auto-organize có action gán collection hiện có hoặc tạo mới [S08]; không có precision hay chứng cứ trigger tự động theo mọi lượt capture | Tạo 3 collection và 12 note, bấm Auto-organize, kiểm membership thật/nhóm đã có, ghi nhầm; NOT_RUN |
| **K06** Bài liên quan, ngữ cảnh, backlinks | **NATIVE (partial)** | Heads Up hiện related topic bundle/collections/meeting timeline [S10], editor liên kết note [S06]; không khẳng định đồ thị backlink hai chiều có API đầy đủ | Tạo 5 note cùng dự án, xem panel và click nguồn; kiểm backlink chiều ngược và lý do; NOT_RUN |
| **K07** PDF/audio/video → đúng trang/timestamp | **UNVERIFIED** | PDF native citation trang bấm được [S14]; voice/transcript [S15]; không thấy hợp đồng nhảy đúng **thời điểm video/audio** trong full case | Tải PDF 120 trang và đoạn ghi âm 3 mốc; tìm câu hỏi rồi đo page và sai số seek, ghi giới hạn 100 trang; NOT_RUN |
| **K08** Đa lĩnh vực + tree/table/card/timeline | **UNVERIFIED** | Đa Collection native [S08], meeting timeline trong Heads Up [S10]; chưa có chứng cứ toàn bộ tree/table/card/timeline trên cùng tập dữ liệu | Xếp một note vào 2 collection, kiểm cả 4 view và không nhân đôi ID; NOT_RUN |
| **K09** Android + Windows, offline & conflict | **NOT_SUPPORTED (Android native share workflow)** | Offline sync có tài liệu [S17], Share to Mem **iOS-only** [S21]; không xác minh Android app/share target, conflict merge và PWA Android | Windows ngắt mạng tạo note; Android share link; sửa chéo xung đột rồi đồng bộ; NOT_RUN |
| **K10** API, export/import notes + assets + backup | **UNVERIFIED (partial native)** | API/MCP hosted [S18, S19], ZIP .md/collections/attachments [S03]; nhập .md/.txt **không kèm attachments/folder** [S05] và không có kiểm thử restore | Xuất 100 note, 2 collection, 5 assets rồi tái nhập/đối chiếu hash, quan hệ, transcript; NOT_RUN |
| **K11** AI nguồn trích, gợi ý vs sửa, quyền/chi phí | **NATIVE (partial)** | Clean Up có diff và Accept/Reject [S22], chat có quyền sửa note [S12], PDF citation [S14], privacy [S20]; hallucination và phân quyền thực chưa audit | Bản note có source + text nguyên gốc, chạy cleanup và chat, so before/after, kiểm thao tác không cho phép; NOT_RUN |
| **K12** Hơn 10.000 mục + hàng trăm GB video Drive | **UNVERIFIED** | Không có benchmark công khai đáng tin cho 10k/300GB/Drive như kho gốc; PDF 25MB và 100-page cap [S14] không thay thế storage video | Dùng corpus giả được phép, đo 10k notes/300GB remote, tốc độ, tỷ lệ tải/xuất/restore; NOT_RUN |

**Nguyên tắc diễn giải:** ca có label NATIVE hay EXTENSION vẫn là **DOCUMENTED**, không chuyển thành TESTED/PASS. Những năng lực thiếu bằng chứng không bị chấm mặc định 0; ca K09 “NOT_SUPPORTED” chỉ kết luận cho **Android native share flow theo tài liệu tại ngày xem**, không khẳng định người dùng hoàn toàn không thể mở Mem qua trình duyệt Android.

## 5. Đối chiếu trực tiếp với code Kho Tri Thức ở main, không so với kế hoạch cũ

Nguồn cố định để tái kiểm: [B01]–[B12] ở cuối. Các trạng thái dưới đây mô tả **sự hiện diện trong mã**, không tự khẳng định môi trường Android/production đã nghiệm thu. Checkpoint vận hành [B01] báo Windows Live đối với tập 5 Item và 19 nhánh, Drive readback và một lần ASR tiếng Anh; không suy từ đó ra hiệu năng mọi loại video.

| Khả năng | Hiện trạng Kho Tri Thức, bằng chứng code | Kết luận so với Mem |
| --- | --- | --- |
| Gửi chữ/link và ghi chính xác thời điểm | Item UUID, saved_at; CaptureEvent UUID, server_received_at, idempotency_key; submit_capture tạo mỗi lần gửi event mới, retry cùng key trả event cũ [B02, B03, B04] | **Đã có; giữ kiến trúc.** Mem không chứng minh thay được mô hình sự kiện này |
| Text-first, Markdown bảng/link | ReactMarkdown + remark-gfm, skipHtml; editor nhận Markdown, ReadKnowledgeService ưu tiên note người dùng [B05, B06, B07] | **Đã có**; cân nhắc UX thao tác nhanh và sửa cạnh nguồn, không thay editor chỉ vì Mem |
| URL/media metadata + raw asset | Source, Job, DerivedContent/source_locator, DriveKnowledge export version/hash [B02, B04, B08, B09] | **Đã có một phần tích hợp**; clip-to-existing-note là **cải thiện UX**; không đồng nhất summary clip với nguồn video |
| Tự gán vào nhóm hiện có | Topic parent và ItemTopic/Project/Tag đa nhóm, Auto origin/pin; OrganizationService rule gán nhóm thật [B02, B10, B11] | **Đã có** mức rule. Chất lượng semantic/tiếng Việt trên corpus lớn **chưa có bằng chứng nghiệm thu**; học nút Auto-organize, không copy thuật toán đóng |
| Liên kết mục liên quan | RelatedItem lưu reason, confidence, method/source version, status; UI liệt kê lý do [B02, B10, B12] | **Đã có backend + UI danh sách**; **cải thiện** thành Heads Up theo ngữ cảnh, timeline và giải thích chọn |
| Cây nhiều nhánh | Topic.parent, node_kind, sort_order, cùng bài nhiều nhánh không nhân đôi [B02, B13] | **Đã có** cấu trúc mạnh hơn flat Collections ở nhu cầu cá nhân; **không phù hợp** bỏ cây để chuyển toàn hệ thống sang Mem |
| Tìm kiếm và chứng cứ | SearchService/SQL hợp nhất Item và DerivedContent, snippet cùng provenance/locator; UI thể hiện trang PDF như text [B14, B15] | **Đã có** keyword/provenance; **cải thiện** mở trực tiếp đúng trang PDF/đoạn audio khi có locator |
| Đọc ghi âm/video có nguồn | DerivedContent lưu processor/version/locator; ASR nhanh ở một clip tiếng Anh trong checkpoint, cần review, chưa có seek theo timestamp [B07, B08, B01] | **Chưa có** seek đúng timestamp được nghiệm thu; **không phù hợp** giả vờ clipper Mem giải quyết MP4/Drive |
| AI sửa note có diff an toàn | Item.user_edit_version và nguyên tắc không sửa nguồn [B02, B01]; không thấy tương tác Clean Up diff/accept trong UI nguồn đã đọc [B16] | **Cải thiện/chưa có UX tương đương**; chỉ làm nếu opt-in và kiểm xung đột phiên bản |
| Backup và di chuyển | Kho đã có Drive readback/checksum và backup/restore thực trong phạm vi checkpoint [B01, B09]; mô hình item/storage tách nhau [B02] | **Đã có cốt lõi**; **cải thiện** portable ZIP/manifest có bộ kiểm tái nhập. Mem nhắc bài học không phụ thuộc một nhà cung cấp |
| Android + Windows | React/PWA và Windows live theo checkpoint [B01]; Android HTTPS/share thực ghi NOT_RUN | **Chưa nghiệm thu Android** ở Kho; không thể xem Mem là giải pháp Android thay thế |
| Tích hợp Mem SaaS/API/MCP vào Django | API và MCP của Mem phụ thuộc server sắp đóng [S01, S18, S19] | **Không phù hợp / NO-GO**; không thêm adapter Mem, không gửi token hay dữ liệu |

**Điểm phân biệt quan trọng:** auto-group Kho hiện dùng rule tìm nhãn có bằng chứng; RelatedItem worker đang dùng lexical threshold rất chặt (min_shared_tokens = 6, min_similarity = 1.0) và source ghi rõ cần đánh giá KT-107 trước khi nới [B11]. Không gọi đây là hệ thống “AI tự hiểu ngữ nghĩa” đã PASS. Tương tự Mem quảng bá semantic search không thay thế phép thử thực tế trên tiếng Việt, video thiếu transcript và dữ liệu hàng chục nghìn mục.

## 6. Giá trị thực tế cho người dùng Việt Nam và các rủi ro độc lập

**Điểm mạnh để học:**
- Ghi nhanh và điều hướng tri thức ngay khi đang biên tập; Heads Up tránh phải rời note để tìm bài liên quan [S10].
- Collection đa nhãn + hành động Auto-organize; tư duy một Item nhiều ngữ cảnh phù hợp nhu cầu cá nhân [S08].
- Clip có thể đẩy vào note có sẵn; ít thao tác hơn copy/paste thủ công [S13].
- Xem diff trước khi AI thay nội dung, có Accept/Reject; phù hợp văn bản cần giữ nguyên bản gốc [S22].
- Export Markdown tách note/collection/assets, cùng file báo lỗi export: bài học thiết kế “cửa thoát” ngay từ đầu [S03].

**Giới hạn/điểm yếu và các giả định cần bác bỏ:**
1. **Rủi ro tồn vong = xác nhận chính thức:** đóng dịch vụ 15/01/2027, do đó Mem chỉ có giá trị làm mẫu học UX, không còn phù hợp làm nền tảng lâu dài [S01].
2. **Android quan trọng:** trang Share to Mem ghi iOS-only [S21]. Trình duyệt trên Android có thể có hành vi khác, nhưng chưa chứng minh Android native share, offline/sync và resolve conflict như yêu cầu.
3. **Unicode tiếng Việt:** editor hỗ trợ text, nhưng không có benchmark NFC/NFD, tổ hợp dấu, bàn phím tiếng Việt, Markdown table và di chuyển file. Không gán PASS quốc tế hóa.
4. **Video:** YouTube clipper mô tả *tóm tắt* [S13], không xác nhận tải MP4 gốc hoặc đánh giá toàn bộ diễn biến theo thời gian; FB/TikTok và truy cập riêng tư phải UNVERIFIED. Kho cần phân biệt original_url, metadata, transcript, human note và AI draft.
5. **Provenance/time:** metadata calendar source card [S16] khác receipt giờ nhận bất biến; trích dẫn PDF [S14] khác seek audio/video có độ lệch tối đa định lượng.
6. **Privacy/lock-in:** chủ sở hữu công bố chính sách không dùng nội dung huấn luyện AI tổng quát, nhưng có subprocessor; không chứng minh E2E, không có source license công khai được xác minh để dùng lại mã, MCP hosted tạo phụ thuộc vendor [S19, S20]. Tránh đưa tài liệu nội bộ người dùng vào tài khoản thử.
7. **Giới hạn tài liệu và dữ liệu lớn:** 25MB/file, 100 trang chi tiết PDF, thiếu benchmark 10k notes/300GB video [S14]. Không quy đổi số file ghi chú thành năng lực lưu Media Drive.
8. **Export không tương đương restore:** các chỉ mục collection và Markdown có thể mất version/permission/asset links. Hướng dẫn Import của chính Mem không nhập trực tiếp attachment [S05].
9. **Nguồn có thể lệch phiên bản:** blog 2025 và Help 2026 diễn tả các thế hệ sản phẩm khác nhau; Mem đang đóng nên không dùng định hướng roadmap hay “coming soon” để bảo vệ quyết định kỹ thuật [S09, S01].
10. **Chi phí thật:** bảng gói trong feature help mô tả giới hạn theo plan; website pricing hiện là thông báo dừng gói trả phí và dừng charge. Không được khẳng định vẫn mua được Pro hay áp phí USD lịch sử [S02, S14].

## 7. Chấm bảy trụ — điểm tiềm năng lịch sử, không phải quyết định chọn nhà cung cấp

Thang điểm đúng G00-PROTOCOL: 20 + 20 + 15 + 15 + 10 + 10 + 10 = **100**. Điểm dưới đây là **đánh giá chuyên gia theo bằng chứng tài liệu**, không là đo kiểm; các ca thiếu chứng cứ có khoảng điểm, **không tự tính 0 vì UNVERIFIED**.

| Trụ | Điểm tham khảo / tối đa | Mức tin cậy | Lý do / vùng chưa rõ |
| --- | ---: | --- | --- |
| Capture + ingestion | **13/20** | Trung bình | Note, REST, Chrome clipper [S06, S13, S18]; thiếu full-media, receipt và retry semantics |
| Organization + recall | **16/20** | Trung bình | Collections thực sự gán, Heads Up, Deep Search [S08, S10, S11]; chưa đo accuracy tiếng Việt |
| Text editor + reading | **12/15** | Trung bình | Editor, Markdown, split/PDF viewer, version [S06, S07, S16]; round-trip chưa test |
| Provenance, relation, timestamps | **9/15** | Trung bình–thấp | PDF citation, Heads Up, calendar [S10, S14, S16]; audio/video seek và capture-event time thiếu chứng cứ |
| Android + Windows + offline | **5/10** | Trung bình | Offline documented; thiếu Android native share workflow, conflict test [S17, S21] |
| Portability + backup | **6/10** | Trung bình | ZIP .md/collection/attachments [S03]; thiếu full round-trip, import assets [S05] |
| Integration + cost + maintainability | **1/10** | **Cao về trạng thái đóng**, thấp về hiệu năng | API/MCP từng có [S18, S19] nhưng dịch vụ đóng [S01]; không nên phụ thuộc nữa |
| **Tổng tham khảo** | **62/100** | Thấp–trung bình tổng thể | 13 + 16 + 12 + 9 + 5 + 6 + 1 = **62**; sai số chủ quan khoảng **52–70/100** vì không thử live |

**Hai phán quyết khác nhau:**
- **Mức phù hợp thay thế toàn hệ thống: KHÔNG ÁP DỤNG (NO-GO)** — veto độc lập với tổng điểm vì service sẽ đóng, Android/Drive-scale và fidelity không được chứng minh.
- **Giá trị tham khảo tính năng: CAO có chọn lọc** — tập trung UX Heads Up, clip-to-existing-note, diff/accept, portable export, deep links, timeline; không dùng SDK/API/MCP Mem. Không thể suy điểm 62 thành khuyến nghị mua/di chuyển dữ liệu.

## 8. Sáu ý tưởng chỉ học UX/nguyên lý; không thêm công nghệ nặng

**I1 — Panel “Liên quan ngay lúc đọc” theo Heads Up — M.** Trong trang Item, thêm khu vực bên phải (mobile dạng tab thu gọn) gồm *Bài liên quan*, *Cùng nhóm*, *Lịch sử liên quan theo thời gian*. Dữ liệu từ RelatedItem, Topic/Project và CaptureEvent hiện có; hiển thị reason, item ID và nguồn, không tạo link giả; nếu chưa có chứng cứ phải ghi “Chưa tìm thấy”. **Nghiệm thu:** bộ fixture 30 Item có 6 quan hệ thật, 3 nhóm, 5 sự kiện; 100% link đúng owner/ID, 0 mục không có chứng cứ bị gợi ý thành fact, không thay dữ liệu; kiểm cả keyboard và viewport nhỏ. **Phụ thuộc:** B02/B03/B10/B12; không AI ngoài. **Rủi ro:** thuật toán lexical chưa đủ recall, panel quá nhiễu.

**I2 — Timeline nguồn/sự kiện, không nhập nhằng giờ — M.** Lọc theo server_received_at (lần nhận), saved_at (lưu đầu), published_at (nguồn), có badge nguồn giờ và timezone Asia/Ho_Chi_Minh; xem meeting series là một kiểu lọc dựa trên chứng cứ sẵn có, không tự chế event lịch. **Nghiệm thu:** 12 case gồm gửi lại URL cách ngày, retry cùng idempotency key, UTC ngày đổi, source thiếu published_at; mỗi case so đúng event count và thứ tự, không sửa timestamp gốc. **Phụ thuộc:** B02–B04/B14; **rủi ro:** nhầm giờ nguồn và giờ nhận.

**I3 — “Gửi vào bài đang có” và “Lưu vào nhóm” nhanh — S/M.** Nút ở Item/Capture cho phép dán URL hoặc đoạn chọn vào existing note/Item, thêm Source và CaptureEvent mới theo API đã có, nhưng nội dung người dùng chỉ thay sau khi xác nhận; clip chọn sẵn nhóm đang có (auto assignment giữ pinned). **Nghiệm thu:** 10 lượt gửi, trong đó 3 link trùng và 2 retry; không làm nhân đôi asset hoặc Item trái ý, giữ note gốc/markdown và nguyên văn link, có receipt. **Phụ thuộc:** ingestion APIs/B04, UI capture/B05; **rủi ro:** nguồn bị trộn vào nội dung đã biên soạn.

**I4 — AI “Đề xuất chỉnh sửa → xem diff → chấp nhận” — M.** UX như Clean Up: proposal riêng chứa before version / proposed text / reason / citations, hiển thị thay đổi màu; người dùng Accept/Reject/Refine. AI **không được tự sửa** Item.note hay file gốc; nếu user_edit_version thay đổi, bắt rebase/review. Nhà cung cấp AI và dữ liệu ra ngoài cần opt-in, có đường tắt không dùng AI. **Nghiệm thu:** 20 note Markdown tiếng Việt có bảng/link/dấu và 5 tình huống sửa đồng thời; Reject giữ byte-for-byte, Accept đúng một lần sau version check; mọi đề xuất không có nguồn được đánh dấu “AI draft”. **Phụ thuộc:** B02/B05/B07; **rủi ro:** AI làm sai ý, phí/dữ liệu riêng tư.

**I5 — Bản xuất dễ di chuyển + kiểm thử phục hồi — M.** Bổ sung cách *đóng gói có thể xem bằng file explorer* trên lớp backup/KnowledgeExport đã có: note .md, danh mục JSON manifest với item_id/source/event/group/asset locators, checksum, báo thiếu file; không thay thế pg_dump + Drive. Không lệ thuộc cấu trúc đóng của Mem. **Nghiệm thu:** tập fixture tối thiểu 100 Item, 2 Topic một Item thuộc cả hai, 5 asset, 3 lần gửi cùng URL; restore thử vào DB rỗng và verify 100% UUID/link/timestamp/sha256 hoặc xuất báo cáo missing; không xuất token hoặc .env. **Phụ thuộc:** B01/B02/B09; **rủi ro:** ZIP nặng và link assets bị gãy.

**I6 — Link chứng cứ mở trúng trang/đoạn (PDF trước, audio/video sau) — L.** UI chuyển source_locator đã có thành deep link có quyền kiểm soát; PDF page= đúng trang; transcript media cần time-start/time-end đã được lấy từ dữ liệu trích và playback có seek đo được, không tự suy từ ký tự. **Nghiệm thu:** 10 PDF và 10 audio/video fixture có locator chuẩn, bấm kết quả đến đúng trang; media seek sai số mục tiêu tối đa 1 giây khi có hỗ trợ, ghi NOT_RUN nếu codec/webview/Drive chưa xử lý; không đánh dấu PASS cho clip chỉ có metadata. **Phụ thuộc:** B07/B08/B14/B15 và viewer; **rủi ro:** Drive preview latency, seek precision, quyền tệp.

**Ưu tiên:** I1/I3 trước (học UX trên dữ liệu đã có), I2/I5 khi cần truy hồi/backup tốt hơn, I4 chỉ khi có lựa chọn AI và quyền gửi dữ liệu, I6 chia PDF trước rồi media sau. Mọi ý tưởng là đề xuất cho G00 đánh giá, **không phải yêu cầu tự ý bổ sung vào roadmap hay code của đợt nghiên cứu**.

## 9. Phản chứng, điều kiện đảo quyết định và ghi nhận kiểm thử

**Giả thuyết cần phản chứng:** “Vì Mem có Heads Up và search AI nên thay toàn bộ hệ thống bằng Mem sẽ nhanh, ít chi phí và đủ an toàn.” Điều kiện bác bỏ đã có: nhà cung cấp xác nhận đóng; dữ liệu media/phân loại/lịch sử vòng đời đang có contract riêng; Android và 10k video chưa chứng minh. Điều kiện **lý thuyết** để xem lại kết luận thay hệ thống sau này: nhà cung cấp chính thức hủy quyết định đóng, đưa ra hợp đồng hỗ trợ dài hạn và quyền xuất/backup kiểm chứng độc lập; thử trên Android+Windows; benchmark ít nhất 10k Item và kho 300GB; kiểm export/restore tất cả asset+relations+time; báo cáo chi phí và privacy rõ ràng. Không có các bằng chứng đó ở 20/11/2026 nên **NO-GO** giữ nguyên.

**Giả thuyết đối chứng 2:** “Kho Tri Thức đã có RelatedItem nên UX Heads Up không có gì để học.” Sai ở tầng tương tác: RelatedItem tồn tại dưới dạng danh sách có lý do [B12], nhưng chưa có bảng ngữ cảnh nhiều nguồn hiện tự động bên cạnh editor. I1 có thể tăng khả năng tái khám phá mà không cần thêm AI/DB mới; giả thuyết cần kiểm bằng task user study (tìm đúng bài trong không quá 3 thao tác với 20 tình huống), không tuyên bố đã chứng minh.

**Giả thuyết đối chứng 3:** “Export .md là đủ bảo đảm thoát vendor.” Không đủ: chính hướng dẫn Mem yêu cầu giữ attachments, collections và báo missing [S03], trong khi import không tự nhận folder/assets [S05]. I5 phải có restore thử, không chỉ thấy một nút Export.

**Bằng chứng kiểm thử G07 thực sự:**
- **PASS — DOC_REVIEW:** đọc các nguồn chính thức [S01–S22] và các phần code [B01–B16] tại ngày đánh giá.
- **PASS — SCOPE:** chỉ viết một file report, không thay đổi ứng dụng.
- **NOT_RUN — MEM_PRODUCT:** không đăng nhập, không gọi API/SDK/MCP, không dùng account, không có corpus thử; toàn bộ K01–K12 chỉ là kế hoạch tái thử.
- **NOT_RUN — REPO_RUNTIME:** không chạy backend/frontend tests, CI hay Windows/Android khi nghiên cứu tài liệu. Các số PASS về Kho Tri Thức được nêu như *checkpoint nguồn* [B01], không là test của G07.
- **UNVERIFIED:** độ chính xác semantic tiếng Việt, số lần auto-group đúng, video transcript toàn nội dung, seek theo timestamp, đồng bộ conflict, lô 10k/300GB, tính toàn vẹn Mem export thực.
- **Rollback:** xóa/revert duy nhất commit thêm report nếu G00 không dùng; không có migration hoặc thay đổi dữ liệu.

## 10. Nguồn để tái kiểm (truy cập 20/11/2026)

### Tài liệu Mem chính thức

- **[S01]** Mem Labs, *Mem is shutting down*, **16/11/2026**: https://get.mem.ai/blog/mem-is-shutting-down
- **[S02]** Mem Labs, *Pricing & subscriptions* — trang đang ở trạng thái winding down, không báo giá mới, ngày trang không nêu: https://get.mem.ai/pricing
- **[S03]** Mem Help Center, *Save a copy on your computer*, ngày trang không nêu: https://help.mem.ai/migration/save-a-copy
- **[S04]** Mem Help Center, *Check your move and find missing items*, ngày trang không nêu: https://help.mem.ai/migration/check-your-move
- **[S05]** Mem Help Center, *Imports*, ngày trang không nêu: https://help.mem.ai/features/imports
- **[S06]** Mem Help Center, *Note Editor*, ngày trang không nêu: https://help.mem.ai/features/editor
- **[S07]** Mem Help Center, *Version History*, ngày trang không nêu: https://help.mem.ai/features/version-history
- **[S08]** Mem Help Center, *Collections*, ngày trang không nêu: https://help.mem.ai/features/collections
- **[S09]** Mem Labs, *Mem 1.0 → 2.0 Transition Guide*, **2025** (nguồn lịch sử): https://get.mem.ai/blog/mem-2-dot-0-transition-guide
- **[S10]** Mem Help Center, *Heads Up*, ngày trang không nêu: https://help.mem.ai/features/heads-up
- **[S11]** Mem Help Center, *Search*, ngày trang không nêu: https://help.mem.ai/features/search
- **[S12]** Mem Help Center, *Chat*, ngày trang không nêu: https://help.mem.ai/features/chat
- **[S13]** Mem Help Center, *Mem Chrome Extension*, ngày trang không nêu: https://help.mem.ai/features/chrome-extension
- **[S14]** Mem Help Center, *PDF & Image Understanding*, ngày trang không nêu: https://help.mem.ai/features/pdf-and-image-understanding
- **[S15]** Mem Help Center, *Voice Mode*, ngày trang không nêu: https://help.mem.ai/features/voice-mode
- **[S16]** Mem Labs, *Product Update Roundup* (calendar, connector, Pro beta), **23/03/2026**: https://get.mem.ai/blog/product-update-roundup-calendar-integration-claude-connector-referral-program-plus-experimental-features-for-pro-users
- **[S17]** Mem Help Center, *Offline Mode & Syncing*, ngày trang không nêu: https://help.mem.ai/features/offline-mode-syncing
- **[S18]** Mem Developer Docs, *API Quickstart* (Mem It, request ID), ngày trang không nêu: https://docs.mem.ai/guides/get-started/quickstart
- **[S19]** Mem Developer Docs, *Mem MCP* (hosted/OAuth), ngày trang không nêu: https://docs.mem.ai/mcp/overview
- **[S20]** Mem Labs, *Privacy Policy*, **sửa 13/08/2026**: https://get.mem.ai/pages/privacy
- **[S21]** Mem Help Center, *Share to Mem* (iOS-only), ngày trang không nêu: https://help.mem.ai/features/share-to-mem
- **[S22]** Mem Help Center, *Clean Up* (diff/review/accept), ngày trang không nêu: https://help.mem.ai/features/clean-up

### Nguồn đối chứng code Kho Tri Thức (pinned SHA)

- **[B01]** Checkpoint vận hành (có giới hạn rõ): https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/docs/CURRENT_STATE.md
- **[B02]** Item/Source/Topic/Assignment/RelatedItem: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/models.py
- **[B03]** CaptureEvent: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/ingestion/models.py
- **[B04]** Capture service (idempotency & transaction): https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/ingestion/services.py
- **[B05]** CaptureScreen (text/Markdown, URL, file): https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/CaptureScreen.tsx
- **[B06]** Markdown renderer: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/KnowledgeText.tsx
- **[B07]** ReadKnowledgeService: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/read_knowledge.py
- **[B08]** DerivedContent + locator: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/models.py
- **[B09]** DriveKnowledge export (hash/version): https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/storage/knowledge_export.py
- **[B10]** OrganizationService: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/organization.py
- **[B11]** Job, lexical threshold: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/organization_job.py
- **[B12]** UI group/RelatedItems: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/ItemOrganization.tsx
- **[B13]** Tree/multiple paths: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/knowledge_tree.py
- **[B14]** SearchService: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/search/services.py
- **[B15]** Search UI + evidence locator: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/SearchScreen.tsx
- **[B16]** Item editor: https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/ItemScreen.tsx

**Kết luận cuối G07:** **KHÔNG ÁP DỤNG Mem.ai làm nền tảng/tích hợp**. **THAM KHẢO UX VÀ CƠ CHẾ** theo I1–I6, chỉ triển khai sau khi G00 chọn và có test acceptance. Báo cáo độc lập này không chứa kết luận của luồng khác, không cấp quyền thử với dữ liệu riêng tư, không tự merge.
