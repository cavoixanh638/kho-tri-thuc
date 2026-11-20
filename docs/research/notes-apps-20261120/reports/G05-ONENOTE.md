# G05 — Microsoft OneNote và Microsoft Copilot Notebooks: nghiên cứu độc lập

> **Ngày đánh giá và tra cứu:** 20/11/2026 (Asia/Ho_Chi_Minh).  
> **Đơn vị khảo sát:** Microsoft OneNote (trọng tâm Windows/Android/web) **và** Microsoft Copilot Notebooks (không đồng nhất với notebook của OneNote).  
> **Baseline Kho Tri Thức:** nhánh main, commit được API GitHub báo tại thời điểm đọc: [c97f5678a6893d7dfec2595d89c9122f05195320](https://github.com/cavoixanh638/kho-tri-thuc/commit/c97f5678a6893d7dfec2595d89c9122f05195320).  
> **Độc lập:** chỉ đọc INDEX, G05, G00-PROTOCOL, README/thiết kế/hiện trạng và mã của Kho Tri Thức; **không đọc** G00-INITIAL-SOURCES hay báo cáo/điểm của G01–G17.  
> **Bằng chứng:** DOC_VERIFIED (tài liệu chính thức) + CODE_INSPECTED (đọc code GitHub); **không** đồng nghĩa đã chạy sản phẩm. OneNote/Copilot runtime, license cá nhân, thiết bị Android, đối chiếu giá Việt Nam: **NOT_RUN/UNVERIFIED**.

## 1. Executive summary (dưới 200 từ)

**Khuyến nghị: Tham khảo UX và thử PoC có giới hạn; không thay toàn hệ thống Kho Tri Thức.** OneNote có lợi thế rõ ràng ở bố cục trang tự do, chữ viết tay, bảng/hình/tệp nằm cạnh ghi chú, sổ–mục–trang, tìm kiếm, và đặc biệt khả năng gắn ghi chú với thời điểm ghi âm trên desktop Windows. Copilot Notebooks là không gian AI dựa vào tập nguồn do người dùng lựa chọn, **khác** notebook của OneNote; đã có mặt trong OneNote nhưng tính năng và hạn mức lệ thuộc giấy phép. Tính năng Copilot “Organize this section” vẫn là **public preview**, có bước xem trước và Apply, không tự phân loại mọi bài vào nhóm hiện có.

Không thấy bằng chứng OneNote/Copilot cung cấp nguyên bộ cơ chế **CaptureEvent bất biến, retry idempotent, Item–Asset–Drive tách rời, lưu video hàng trăm GB trên Google Drive, auto-group có provenance và backup JSON/PostgreSQL**. Graph có API đọc/ghi trang, nhưng không phải API thay thế hoàn chỉnh cho backup notebook hay API của Copilot Notebooks. Nên học cách trình bày, chú thích theo mốc âm thanh và AI preview, không chuyển dữ liệu nguồn khi chưa có phép thử khôi phục độc lập.

## 2. Ranh giới sản phẩm, trạng thái phát hành, nền tảng và chi phí

| Chủ đề | OneNote notebooks | Copilot Notebooks | Nguồn / độ chắc chắn |
| --- | --- | --- | --- |
| Khái niệm | Lưu trữ dài hạn: notebook → section/section group → page/subpage; canvas tự do, rich text, ink, media, tag, liên kết thủ công | Workspace AI theo dự án, gom các **tham chiếu** (file/trang/chat/link) để hỏi–đáp và tạo nội dung có ngữ cảnh; có thể mở ngay trong OneNote | [S01], [S02]; cao |
| Capture web/video | Browser Web Clipper lưu article dạng text/ảnh, chụp full-page/region, clip PDF, ngữ cảnh YouTube; nhúng online video ở OneNote Windows trong điều kiện nêu tại tài liệu | Tham chiếu URL/web và tài liệu theo loại giấy phép, không phải công cụ tải MP4 hay trích toàn bộ lời video | [S03], [S04], [S05], [S06]; cao cho chức năng được công bố, **không kiểm chứng** Facebook/TikTok |
| Bút/ink, freeform | Rich text, hình, bảng, ảnh, vẽ tay trên canvas; ghi âm/video, typed notes có thể liên kết thời gian thu ở Windows | Tối ưu truy vấn/biên soạn trên tập nguồn, **không thay** canvas OneNote | [S01], [S07], [S08]; cao |
| AI tổ chức | Copilot **Organize this section** đang **public preview**: đề xuất bố cục, xem trước, **Apply** mới sửa; không chứng minh tự gán taxonomy trong backend | AI hỏi–đáp trên nguồn chỉ định, instructions, audio overview, tạo bản nháp; giới hạn grounding và tính năng theo gói | [S09], [S10], [S11], [S12]; cao về mô tả, trung bình về rollout thực tế |
| Thiết bị | Windows desktop, Android, web; sync/offline có tài liệu nhưng xung đột phải thử. **OneNote for Windows 10** đã hết hỗ trợ tháng 10/2025 | Web/Copilot và bề mặt trong OneNote; trên Android có thể tiếp tục notebook chats trong ứng dụng Copilot; không suy rằng mọi công cụ notebook/ink giống desktop | [S13], [S14], [S15], [S16]; cao |
| Hạn chế web | OneNote web không ghi âm/video; trang trợ giúp nêu media không phát trong web (có thể tải về), search hẹp, hạn chế ink/linked notes và khác desktop | Phụ thuộc giao diện Copilot/OneNote, lịch rollout, license và khu vực; không dùng tính năng desktop để chấm web | [S16], [S02]; cao trong phạm vi trang mô tả |
| API / SDK / MCP | **Microsoft Graph OneNote API** v1.0 đọc notebook/section/page, GET HTML/asset, POST HTML page và PATCH content với OAuth Notes.*; giới hạn API và throttling. Đây là API trang OneNote, **không** phải storage driver đa nguồn | Trong tập tài liệu chính thức được rà soát **chưa xác minh được API/SDK/MCP công khai chuyên dụng** cho tạo, hỏi hoặc xuất toàn bộ Copilot Notebooks; tuyệt đối không suy API OneNote quản lý được Copilot Notebooks | [S17], [S18], [S19], [S20]; cao cho Graph, thấp cho khẳng định phủ định → giữ UNVERIFIED |
| Giá/license | Có OneNote cho tài khoản Microsoft/Office và bản tải di động; khả năng cụ thể phụ thuộc app và quyền M365/OneDrive. Không xác nhận OneNote mọi tính năng AI đều miễn phí | Có đường dùng với Copilot/Copilot Chat đủ điều kiện; personal Microsoft 365 Personal/Family/Premium/Pro, hoặc license tổ chức + OneDrive/SharePoint service plan. Quyền và số tham chiếu khác theo tier. Một số tính năng như Capture/Mind maps không có ở một số gói personal | [S02], [S06], [S21], [S22]; cao về phân tầng, **chưa xác minh giá/gói thực trên tài khoản VN** |
| Lưu trữ, privacy/retention | OneNote đồng bộ trên OneDrive/SharePoint. Có lịch sử phiên bản/trash; export notebook trên web **chỉ** với OneDrive cá nhân và có giới hạn cỡ | Microsoft FAQ nói dữ liệu của Copilot Notebooks **không dùng huấn luyện LLM**; nội dung có tham chiếu theo quyền hiện hữu; trang hướng dẫn nói xóa notebook hiện có thể vĩnh viễn, recycle bin còn phát triển | [S23], [S24], [S11], [S06]; cao về chính sách nêu ra, cần xét điều khoản đúng loại tài khoản |

**Các phân biệt quan trọng (không suy diễn tính năng):**

1. **Video embed ≠ tải/lưu video.** [S04] công bố online video Windows từ YouTube/Vimeo/Dailymotion và yêu cầu Microsoft 365 subscription; [S03] nói clip YouTube **ngữ cảnh thành bài viết**, không khẳng định đã thu MP4/transcript/metadata API chuẩn. Facebook Reels và TikTok **UNVERIFIED**.
2. **Audio-linked notes ≠ locator của mọi file media.** [S07] nói ghi chú gõ *trong lúc OneNote đang ghi âm/video* được liên kết mốc. [S08] bổ sung transcription/ink replay; không có bằng chứng nhập MP4 ngoài rồi gõ ghi chú cũng được time-link đúng như vậy, hay OneNote web/Android có cùng khả năng. Không đánh đồng ASR/OCR với sự hiểu toàn bộ nội dung video.
3. **AI preview ≠ tự phân loại không cần duyệt.** [S09] rõ tính năng public preview; bản preview chỉ trở thành thay đổi sau Apply. Bản này không chứng minh tự chọn taxonomy hiện hữu, bảo toàn curated assignment và log lý do như Kho Tri Thức.
4. **Tài liệu giới hạn Copilot có biến động.** [S11] nêu grounding tối đa 300 tệp trong notebook; [S12]/[S21] nêu số tham chiếu và quyền khác giữa Copilot Chat và Microsoft Copilot (có mô tả mức 50 và >300 tham chiếu, grounding 300). Không khẳng định 300 là quota lưu trữ tuyệt đối hay áp dụng mọi gói; phải test đúng SKU. Audio overview trong [S11] **chưa liệt kê tiếng Việt** (các ngôn ngữ giới hạn khác Copilot chat).
5. **Chi phí minh họa, không phải báo giá Việt Nam:** trang Microsoft US [S22] niêm yết Microsoft 365 Personal **99,99 USD/năm hoặc 9,99 USD/tháng** ở thời điểm truy cập; chưa xác nhận chi phí thực trả ở Việt Nam, VAT, quota OneDrive, Copilot credits và các quyền enterprise. Không mua/đăng nhập để kiểm tra.

### Phát hành / preview / kế hoạch theo tài liệu

- **Đã được Microsoft mô tả như chức năng có sẵn**: OneNote desktop canvas, ink, section/pages, record audio/video và liên kết ghi chú, web clipper, Graph OneNote API; Copilot Notebooks theo nguồn được chọn, custom instructions, audio overview cho tier đủ quyền [S01], [S03], [S07], [S10], [S17]. Tình trạng **trên một tài khoản cụ thể chưa thử**.
- **Public preview**: “Organize this section” [S09]. **Rolling out**: “Take notes with Copilot” trong OneNote [S25]. Không ghi “GA toàn bộ”.
- **Tháng 11/2026**: trang so sánh và FAQ cập nhật tháng 11 [S01], [S06], [S11]. Release notes mới của Microsoft mô tả tạo draft Word từ Copilot Notebooks trên Windows/web [S26]; không suy có trên Android hay mọi license.
- **Planned**: Copilot Notebooks recycle bin đang phát triển theo [S11]; chỉ ghi kế hoạch, **không** coi là tính năng phục hồi đã hoạt động.
- **Giấy phép mã nguồn**: OneNote/Copilot là sản phẩm Microsoft độc quyền, không có bằng chứng repo mã nguồn ứng dụng chính hoặc license OSS cho phép fork. Microsoft Graph là giao diện API, không phải giấy phép sao chép mã. Không cài extension/plugin hoặc SDK không rõ nguồn.

## 3. Ma trận K01–K12 (tiêu chí đầy đủ của G00, không chỉ những phần OneNote làm được)

Quy ước: **NATIVE** = chức năng sản phẩm đáp ứng trọng tâm ca theo tài liệu; **EXTENSION** = có phần lõi nhưng cần plugin/quy trình ngoài; **CUSTOM_BACKEND** = muốn đủ hợp đồng Kho Tri Thức phải tự xây dịch vụ; **NOT_SUPPORTED** = không tìm thấy hỗ trợ native cho hợp đồng; **UNVERIFIED** = thiếu bằng chứng. **Toàn bộ thao tác thực tế của OneNote và Copilot: NOT_RUN.** Những bước dưới đây là *hướng dẫn tái thử*, không phải kết quả đã chạy.

| Ca | Trạng thái đối với **toàn bộ** hợp đồng G00 | Chứng cứ + cách tái thử tối thiểu | Thiếu chắc chắn / phần còn thiếu |
| --- | --- | --- | --- |
| **K01** Gõ note Việt, receipt + giờ server | **CUSTOM_BACKEND** | [S01], [S27]. Tạo trang với Unicode “Tài liệu — Hải Phòng”, ghi giờ máy, thoát/mở lại, xem creation time; dùng Graph kiểm createdDateTime. | OneNote tạo/sửa trang **NATIVE**, nhưng không thấy receipt có server_received_at bất biến cho **mỗi lần gửi**. Cần backend nếu giữ contract Event. IME/Unicode trên thiết bị VN: NOT_RUN. |
| **K02** Gửi URL video/web, lấy metadata + text | **CUSTOM_BACKEND** | [S03], [S04], [S17]. Dán URL bài HTML/YouTube, thử Web Clipper Article/Video, kiểm ảnh/nguồn/URL/text; đối chiếu với Facebook Reel/TikTok. | Clipper/embedding là **EXTENSION/NATIVE từng phần**, không có chứng cứ downloader, trích transcript/metadata đa nguồn và lưu file gốc trên Google Drive. |
| **K03** Link trùng sau 1 ngày ≠ retry | **NOT_SUPPORTED** (native) | [S17], [S18]. Lưu URL 2 lần cách nhau, kiểm danh sách trang/modifiedTime và xem có khóa idempotency hoặc bảng event bất biến không. | Không tìm thấy native CaptureEvent/retry key; tự tạo OneNote page khác không đáp ứng lịch sử chuẩn. Muốn đủ phải CUSTOM_BACKEND. |
| **K04** Markdown, bảng, link, Unicode roundtrip | **EXTENSION** | [S01], [S16], [S18]. Chép raw Markdown chứa GFM table, dấu Việt, link/ảnh vào trang; xuất qua Graph HTML, nhập lại, so sánh byte + ý nghĩa. | OneNote mạnh rich text/table/link nhưng chưa có chứng cứ roundtrip Markdown nguyên văn/cấu trúc + assets; cần bộ chuyển đổi và test lossless. |
| **K05** Tự tìm nhóm cũ và thực **gán** | **NOT_SUPPORTED** (native) | [S09]. Chuẩn bị 2 section đã có và nhiều trang; gọi “Organize this section”, kiểm preview rồi Apply, đối chiếu số quan hệ và quyết định tự động. | Chỉ tổ chức section theo **preview công khai**, cần xác nhận; không chứng minh tự gán taxonomy toàn kho theo confidence, không đụng curated. CUSTOM_BACKEND để đạt contract. |
| **K06** Related items/backlinks cạnh bài | **CUSTOM_BACKEND** | [S16], [S01]. Tạo hai trang liên quan, chèn link trang A→B, tìm trang backlinks B→A và lý do/provenance gợi ý. | OneNote có link thủ công đến trang nhưng không chứng minh tự xây backlinks hai chiều, RelatedItem có lý do/phiên bản và sidebar liên quan. |
| **K07** PDF/audio/video nhảy trang/timestamp | **EXTENSION** | [S07], [S08], [S16]. Desktop Windows ghi âm trong lúc gõ ở mốc 00:30 và 01:10, bấm ghi chú để seek; đính PDF 3 trang, MP4 ngoài, thử locator và lặp trên web/Android. | **Một phần NATIVE rất đáng học** cho audio-linked notes; không chứng minh accurate seek cho MP4 nhập từ ngoài, PDF locator tự động, hay playback trên web. Full contract cần backend/player có anchor. |
| **K08** Một bài nhiều lĩnh vực + tree/table/card/timeline | **CUSTOM_BACKEND** | [S01], [S28]. Đưa một trang vào hai section mà không copy; thử views theo tag, hierarchy và chronological timeline. | Notebook/section/page là cây thủ công; tag hỗ trợ tìm, không có chứng cứ many-to-many một Item/ID và đủ bốn chế độ view. |
| **K09** Windows + Android, offline, conflict | **NATIVE** (có điều kiện) | [S13], [S14], [S16]. Dùng cùng notebook trên Win/Android, sửa cùng đoạn khi airplane mode, online lại và kiểm bản nào còn/mất; kiểm attachment chưa tải. | Microsoft có offline local/cache & sync, nhưng conflict-resolution thực tế, quota cache, mobile parity và ổn định tiếng Việt **NOT_RUN**. Web không là desktop. |
| **K10** API + Markdown/assets export/import/backup | **CUSTOM_BACKEND** | [S17], [S18], [S19], [S20], [S23], [S29]. Graph GET pages/content/resources, export ZIP personal OneDrive, export PDF; thử tái nhập & kiểm hash/file liên kết. | Graph có CRUD trang nhưng giới hạn backup/restore notebooks; web ZIP chỉ cá nhân, import notebook trên web đã deprecated; PDF tĩnh; chưa có native Markdown + manifest + full restore tương đương DB. |
| **K11** AI có nguồn, tách gợi ý/sửa, quyền/giá | **EXTENSION** | [S09], [S10], [S11], [S12], [S21], [S24]. Tạo notebook với 3 file có câu mâu thuẫn, yêu cầu Copilot chỉ ra trích nguồn; kiểm ai có quyền, hành động Apply, AI credits và xóa notebook. | Grounding theo tập tham chiếu và preview là điểm mạnh, nhưng **chưa chứng minh** câu trả lời luôn có locator chính xác, không tự sửa curated dưới mọi lệnh, khả năng xuất audit log & phân biệt transcript thiếu. |
| **K12** >10.000 items + hàng trăm GB video/Drive | **UNVERIFIED** | [S11], [S20], [S30]. Mô phỏng 10k pages qua API, tải 100–500 GB media/remote, thử mở/search/restore/quota/chi phí. | **Không chạy benchmark**, không thấy cơ chế native dùng **Google Drive làm storage layer của OneNote**, API có rate/page-limit; Copilot giới hạn grounding, không chứng minh quy mô đầu vào. Không chấm điểm này bằng 0 tuyệt đối. |

**Tổng nhận xét:** K01–K04, K07, K09 có phần native hữu ích nhưng chỉ K09 phù hợp tương đối với toàn bộ ca (và vẫn cần kiểm xung đột). Không có bằng chứng đủ để chuyển toàn bộ K01–K12 sang OneNote mà không tự viết backend rất lớn. Trạng thái NOT_SUPPORTED ở đây nghĩa là **không tìm thấy hỗ trợ native cho hợp đồng được yêu cầu** trong tài liệu đã khảo sát, không khẳng định về tất cả plugin tồn tại trên thị trường.

### Bộ fixture/từng bước nghiệm thu đề xuất (không dùng dữ liệu thật)

- **Environment:** Windows 11 + OneNote desktop bản hiện hành; Android 13+ + OneNote; Edge/Chrome Web Clipper; một notebook **thử nghiệm** trên tài khoản Microsoft được phép; tier Copilot được ghi rõ. Không dùng nội dung cá nhân hoặc tài liệu cơ quan.
- **Corpus:** 20 bài Markdown/tiếng Việt (dấu, bảng, link, emoji), 3 trang PDF có page marker, 1 file audio 3 phút tự thu, 1 MP4 tự tạo 2 phút, 3 URL công khai thuộc 3 dạng (web, YouTube, mạng xã hội), 30 sự kiện gửi có 10 duplicate và 5 retry; bổ sung 2 bài có khẳng định xung đột để kiểm AI nguồn.
- **Ghi nhận:** account SKU/build, nền tảng, ID/URL, giờ máy + giờ server nếu API trả, hash đầu vào/đầu ra, ảnh màn hình có quyền, click-to-audio seek delta tính bằng giây, các lỗi sync, chi phí phát sinh, rõ PASS/FAIL/NOT_RUN theo từng ca.
- **Stress là gate riêng:** 10.000 items/100–500 GB và restore phải được tạo bằng dữ liệu tổng hợp, có tài khoản/quota và giới hạn API rõ ràng; **không** suy từ 20 item PASS rằng stress PASS.

## 4. So với **mã** Kho Tri Thức hiện có (không so với kế hoạch cũ)

Đã trực tiếp mở cấu trúc repo, các file bên dưới trên main. Trạng thái triển khai có tham khảo [CURRENT_STATE](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/CURRENT_STATE.md) 20/11/2026, nhưng **không tự chạy lại** CI/Windows; dữ kiện runtime dưới đây là checkpoint có đường dẫn log của dự án, không phải G05 test.

| Khả năng | Baseline code/reality Kho Tri Thức | OneNote/Copilot thêm được gì? | Kết luận |
| --- | --- | --- | --- |
| Receipt + lịch sử sự kiện | [ingestion/services.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/ingestion/services.py) tạo Item/Source/CaptureEvent sau transaction, server_received_at, idempotency_key; [CaptureScreen.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/web/src/CaptureScreen.tsx) có URL/text/file và receipt, [HistoryScreen.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/web/src/HistoryScreen.tsx) lọc giờ | Quick note/canvas và Web Clipper thân thiện hơn khi nhập nội dung, nhưng không thay event contract | **Đã có cốt lõi**; học UX, không thay backend |
| Nội dung đọc chính | [KnowledgeText.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/web/src/KnowledgeText.tsx) dùng react-markdown + remark-gfm, [ItemScreen.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/web/src/ItemScreen.tsx) textarea Markdown/đọc; giữ text nguyên văn | Canvas/ink/đính nguồn cạnh đoạn/bảng thao tác trực quan hơn; không bảo đảm Markdown roundtrip | **Cải thiện UX** theo chế độ bổ sung, không thay Markdown nguồn |
| Cây và nhiều nhánh | [catalog/knowledge_tree.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/catalog/knowledge_tree.py) và [KnowledgeTree.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/web/src/KnowledgeTree.tsx) có cây, phân loại loại node và ItemTopic nhiều nhánh | OneNote có section/page hierarchy, tabs nhanh, subpages | **Đã có mô hình mạnh hơn về quan hệ**; mượn navigation/tabs thôi |
| Auto-group + related | [catalog/organization.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/catalog/organization.py) thực sự lưu ItemTopic/Project/Tag AUTO và RelatedItem có reason/confidence/status; [catalog/models.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/catalog/models.py) bảo vệ phân biệt user curated. Chất lượng tự nhóm trên corpus cá nhân còn cần benchmark | Copilot tổ chức preview / Apply; cách hiển thị “trước/sau”, xin duyệt gợi ý tốt | **Cải thiện review UX**, không bỏ OrganizationService |
| Video/text/trích dẫn | [processing/read_knowledge.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/processing/read_knowledge.py) ưu tiên bài người dùng, tách transcript/derived; [KnowledgeReading.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/web/src/KnowledgeReading.tsx) cảnh báo ASR cần rà soát và có page/section locator. [processing/transcribe.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/processing/transcribe.py) là ASR offline giới hạn | Audio-linked notes khi ghi âm Windows là ý tưởng time anchor mạnh; không giải quyết MP4/video tiếng Việt bằng metadata | **Chưa có click-to-timestamp phổ quát**; PoC độc lập |
| Search | [SearchScreen.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/web/src/SearchScreen.tsx) đã có filter theo nhóm, evidence snippet/locator; backend SearchService FTS; OneNote tìm text/tag/ink, audio search desktop là tính năng tùy chọn | Tìm text trong ảnh/ink và điều hướng theo trang là gợi ý, nhưng không thay FTS provenance | **Đã có** search nguồn; mở rộng có điều kiện |
| Drive & restore | [storage/drive.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/storage/drive.py), [storage/knowledge_export.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/storage/knowledge_export.py), [backup-live-results](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/operations/hierarchy-backup-live-results.json) và [restore-details](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/operations/hierarchy-restored-details-results.json). Checkpoint ghi Drive full readback/restore cluster kiểm thử | OneNote OneDrive ZIP personal + PDF, Graph đọc assets; không tương đương backup manifest/restore độc lập | **Không phù hợp** để thay Drive/PostgreSQL |
| AI nguồn/ChatGPT | [CURRENT_STATE](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/CURRENT_STATE.md) ghi controlled pilot ChatGPT/Drive có giới hạn search; chưa có MCP, không gọi AI hoàn chỉnh | Scoped notebook / chỉ chọn nguồn, custom instruction, summary; không tự đọc Postgres/Drive của dự án | **Tham khảo cách chọn tập nguồn**, chưa có adapter đủ căn cứ |
| Windows/Android | Windows live đã có bằng chứng tại CURRENT_STATE; **Android PWA và HTTPS chưa nghiệm thu** | OneNote Android là app lâu đời, hỗ trợ sync/offline; độ tương đương ghi âm/ink/attachment cần test | **Cải thiện ý tưởng** multi-device, không thay thế nghiệm thu Android dự án |

**Đọc code đã xác nhận khác với chạy nghiệm thu:** Đã có các lớp nghiệp vụ thực và các lời gọi UI; không kiểm thực nghiệm tài khoản Microsoft, browser/Android/CI của G05. CURRENT_STATE còn nêu Reel có transcript tiếng Anh 11 đoạn cục bộ và khôi phục 15 collection đã thử, **chưa** đánh giá chất lượng ASR tiếng Việt, seek theo đoạn và thiết bị Android. Các bằng chứng đó có giới hạn theo thời điểm, không phải lời hứa “hệ thống đã hoàn thành 100%”.

## 5. Chấm 7 trụ theo rubric G00 (có tách hai mục đích)

Chấm cho giả thuyết **dùng OneNote + Copilot Notebooks thay toàn Kho Tri Thức**; tài liệu chứng minh một tính năng thì được điểm, thiếu thử quy mô/giấy phép làm tăng khoảng bất định chứ **không mặc định 0**.

| Trụ | Trọng số | Điểm ước lượng | Lý do và độ tin cậy |
| --- | ---: | ---: | --- |
| Capture + ingestion | 20 | **8** (6–10) | Ghi chú/Clipper tốt, đa nguồn YouTube, nhưng thiếu chứng cứ receipt immutable, idempotent, FB/TikTok/Drive downloader. **Trung bình** [S03], [S04] |
| Organization + recall | 20 | **10** (8–12) | Hierarchy/tag/search tốt; auto-organize mới preview và không có model Item nhiều nhánh + RelatedItem provenance native. **Trung bình** [S01], [S09], [S28] |
| Text editor + reading | 15 | **14** (12–15) | Freeform/rich text/ink/multimedia/audio-linked mạnh; trừ Markdown fidelity. **Cao** cho Win desktop, **trung bình** Android/web [S01], [S07], [S16] |
| Provenance / related / timestamps | 15 | **7** (5–9) | Có audio-linked lúc ghi và link trang thủ công; không có bằng chứng event immutable hay transcript/video timestamp rộng. **Trung bình** [S07], [S17] |
| Android / Windows / offline | 10 | **8** (6–9) | App/sync được hướng dẫn; conflict & parity chưa thử, web bị hạn chế. **Trung bình** [S13], [S14], [S16] |
| Portability / backup | 10 | **4** (2–5) | Graph read/export từng phần, ZIP chỉ personal, import deprecated, PDF static; khó roundtrip Markdown/asset. **Cao** về giới hạn công bố [S23], [S29], [S17] |
| Integration / cost / maintainability | 10 | **5** (3–7) | Graph tồn tại nhưng có throttling và hạn chế full backup; Copilot license không đồng nhất, OneDrive ≠ Google Drive. **Trung bình** [S20], [S21], [S22] |
| **Tổng** | **100** | **56/100** (ước lượng 42–67 theo tổng khoảng hàng; mức hợp lý xem xét ~49–62) | **Không phải benchmark thực nghiệm.** Công thức 8+10+14+7+8+4+5=**56**. Các khoảng thể hiện bất định, không là khoảng tin cậy thống kê. |

**Kết luận tách biệt:**
- **Thay thế toàn hệ thống:** **KHÔNG KHUYẾN NGHỊ**, vì vướng các gate không thể đánh đổi bằng UI đẹp: event provenance, Drive file gốc, lịch sử retry và restore độc lập. Một điểm tổng 56 không “xóa” gate.
- **Giá trị học/tái sử dụng tính năng:** **CAO (4/5, định tính)**, nhất là audio-linked notes, trình bày trang, navigation, clipping và AI preview. **Chỉ dùng làm nguồn cảm hứng UX/luồng**, không sao chép code/thiết kế độc quyền.

## 6. Đề xuất áp dụng 6 ý tưởng cụ thể, không thay Django/PostgreSQL/Drive

| Ưu tiên / độ khó | Ý tưởng + UX | Technical / adapter nhỏ | Acceptance đo được + rủi ro |
| --- | --- | --- | --- |
| **P1 / L** | **Chú thích gắn mốc media**: vừa phát/ghi audio, bấm tạo ghi chú; click ghi chú → nhảy đúng đoạn. Lấy cảm hứng từ OneNote Windows audio-linked [S07]. | Thêm model/record **TimedAnnotation** với item_id, asset_id, start_ms/end_ms, text anchor, origin, source_version; player seek có xác nhận, không sửa Item.note bản gốc. Tận dụng Asset/DerivedContent hiện có. | 20 anchor trong MP4/MP3 test, ≥95% click seek có sai lệch ≤1 giây trên Chrome Windows với tệp local; anchor tồn tại sau edit/nạp lại/restore; Android cần gate riêng. Rủi ro drift, browser media seeking, đồng bộ text anchor. |
| **P1 / M** | **Xem trước trước khi AI xếp/chỉnh**: bảng “Đề xuất → Đang có → Áp dụng/Bỏ qua” theo section/nhóm. Lấy từ Copilot Organize preview [S09]. | Read-only proposal từ OrganizationService và JSON diff; áp dụng qua API sau xác nhận; giữ origin/confidence, user_pinned ưu tiên. Không gọi Copilot API. | 100% đề xuất medium/low không thay quan hệ curated trước Apply; hủy không thay DB; ghi audit reason/version và undo tối thiểu một thao tác. Rủi ro UI phức tạp, race giữa gợi ý và thay đổi nhóm. |
| **P1 / M** | **Clipper 3 chế độ**: URL/Article/Ảnh màn hình tùy quyền, có nhãn nguồn gốc và ngày thu; dùng ý tưởng OneNote Web Clipper [S03]. | Bổ sung chế độ capture trong React (bắt đầu bằng dán URL + trích text sẵn có); screenshot là Asset mới chỉ sau user chọn, giữ URL/canonical/time/hash; không thêm extension trình duyệt ở vòng đầu. | 15 URL công khai, server ACK trước trích; bài thất bại giữ link+event; không nhân đôi tệp khi retry; nguồn luôn hiển thị với extraction status. Rủi ro bản quyền, SSRF, clip thay đổi theo trang. |
| **P2 / M** | **Không gian nghiên cứu theo tập nguồn**: chọn 5–20 Item liên quan rồi mở một màn hình “Tư liệu đang tham chiếu” trước khi hỏi AI. Lấy ý tưởng scoped notebooks [S10], [S11]. | Danh sách UUID/phiên bản trong DB, build context từ ReadKnowledgeService/KnowledgeExportService; AI chỉ dùng text/transcript có nguồn; không đẩy MP4 sang Copilot để suy “đã hiểu”. Bật khi có AI provider và được chấp thuận. | Test 10 câu: tất cả khẳng định có item_id/source/locator, file thiếu transcript hiển thị “chưa có nội dung”, 0 nội dung người dùng bị sửa; đo chi phí token. Rủi ro hallucination, quota, lộ dữ liệu khi gọi ngoài. |
| **P2 / S–M** | **Thanh điều hướng và ghi chú cạnh nguồn**: danh sách section/subpage thu gọn, kéo ảnh/PDF làm minh họa, click mở nguồn ở cạnh trang thay vì thay toàn màn hình. Học cách dùng OneNote canvas nhưng giữ Markdown là nguồn chuẩn. | Dùng React existing KnowledgeTree + ItemScreen + AssetPreview, không cần freeform editor mới; thêm split-view/anchor theo đoạn khi phù hợp. | 8 bài có Markdown+PDF+video, từ đoạn đọc mở nguồn ≤2 click, back không mất vị trí scroll và Unicode; màn nhỏ 360px không che nội dung. Rủi ro layout và khả năng tiếp cận. |
| **P2 / M** | **Xuất Portable Package cho một bài** (không mang tên/định dạng OneNote): Markdown/JSON manifest + assets + provenance, kiểm lại hash. Bài học phản diện từ hạn chế export [S23], [S29]. | Dùng export/backup đã có, chỉ bổ sung bundle cấp item và schema version, không làm thêm DB hay storage provider. | 30 Item có Unicode/bảng/ảnh/PDF/transcript được export→import DB thử với 100% UUID/quan hệ/locator/hash; không cần Microsoft account. Rủi ro gói lớn, không xuất nội dung có quyền hạn chế. |

**Chọn trước:** PoC TimedAnnotation + preview nhóm; các ý tưởng còn lại vào backlog nghiên cứu sau G00, **không thay đổi code ở PR này**. Đặc biệt, không nhảy sang OneNote Graph/Outlook/SharePoint subscription chỉ để có UI gần giống.

## 7. Hạn chế, phản chứng và điều kiện đảo chiều

**Ít nhất 8 rủi ro/giới hạn:**
1. **Vendor lock-in/export:** OneNote ZIP notebook chỉ OneDrive cá nhân; enterprise SharePoint không cùng đường; nhập notebook web deprecated [S23]. Graph HTML/tài nguyên chưa bảo đảm lossless Markdown/ink/audio.
2. **Mất dữ liệu khi quá tin cloud:** Copilot notebook delete hiện có thể vĩnh viễn, recycle bin còn phát triển [S11]; cần xuất thử/restore, không coi lịch sử chat là backup.
3. **Không tương thích kiến trúc storage:** OneNote dùng OneDrive/SharePoint; không có chứng cứ lưu OneNote notebooks trực tiếp như file gốc trong Google Drive với ID ổn định, checksum/mapping độc lập.
4. **Licensing/region rollout:** gói personal/enterprise/owner, AI credits, eligibility, Copilot preview và Android/Web lệch tính năng. Giá Microsoft US không đại diện Việt Nam [S06], [S21], [S22].
5. **Ngôn ngữ và media:** văn bản Unicode Việt Nam hợp lý về định dạng nhưng IME/OCR/speech-to-text/audio overview tiếng Việt **chưa thử**; tổng hợp video khác hiểu video, phụ đề cần truy nguồn [S07], [S11].
6. **API limits:** Graph OneNote throttling (delegated 120 request/phút, 400/giờ; 5 đồng thời) và section/page limit có thể trở ngại nhập 10k mục; chưa benchmark [S20], [S30].
7. **Offline conflict:** nhà sản xuất có hướng dẫn sync, nhưng xung đột khi Windows và Android cùng sửa một đoạn, file lớn chưa tải về, và dữ liệu mất kết nối dài ngày cần test riêng [S13], [S14].
8. **Privacy:** Microsoft FAQ nói Copilot Notebooks không dùng dữ liệu để train LLM [S24], nhưng loại tài khoản, quản trị/retention và nội dung bí mật phải được kiểm đúng điều khoản. Không được tự chuyển dữ liệu thật lên sản phẩm ngoài.

**Giả thuyết phản chứng bắt buộc (có thể làm thay đổi kết luận):**
- **H1 — khả năng thay thế:** nếu PoC có quyền chính thức chứng minh được gửi lặp giữ CaptureEvent/receipt bất biến, tự phân loại vào nhóm hiện có, giữ nguồn + locator, 10.000 Item/100GB media và full export/restore sang môi trường không còn Microsoft account với tỷ lệ 100%, chi phí thấp hơn kho hiện tại thì **đánh giá lại** khuyến nghị “không thay”.
- **H2 — giá trị timed notes:** nếu trên Windows/Android việc tạo note khi ghi và click-to-seek không ổn định (ví dụ <95% anchor đạt ≤1s) hoặc text anchor hỏng sau sửa, **không nên áp dụng rộng** tính năng này; chọn cách nhập mốc thủ công.
- **H3 — AI scope:** nếu Copilot Notebooks trả lời từ nguồn không nằm trong curated references hoặc không có trích dẫn kiểm tra được trên fixture có dữ liệu mâu thuẫn, **hạ mức ưu tiên** thiết kế scoped AI và bắt buộc từng câu trả lời có xác nhận nguồn.
- **H4 — quản lý chi phí:** nếu hỗ trợ OneNote/Copilot cần mua gói hoặc duy trì Microsoft account thứ hai và chi phí di chuyển/backup vượt lợi ích UX, giữ hoàn toàn UI/công nghệ hiện tại, không tích hợp Graph.

**Điều kiện dừng trước bất kỳ migration:** có chủ trương riêng của chủ kho; test nhập–xuất/restore độc lập; không thay dữ liệu đang chạy; có báo cáo benchmark Android/Windows và phí Việt Nam; pin rủi ro 3rd-party plugin. Chưa đạt bất kỳ gate nào trong phạm vi G05.

## 8. Nguồn chính thức, thời điểm, phương pháp và tái lập

**Tất cả URL được truy cập/tra cứu ngày 20/11/2026** bằng tìm kiếm web và tài liệu Microsoft công khai; “last updated” chỉ ghi khi chính trang nêu. Không dùng tài khoản để thử hay mua dịch vụ. Các đường dẫn Microsoft Support có thể thay đổi tên/điều hướng sau ngày đánh giá. Nguồn S01–S30 chủ yếu là **Microsoft Support/Learn**; liên kết Kho Tri Thức trong mục 4 là **bằng chứng code của chính repo**, không được tính là bằng chứng Microsoft.

- **[S01]** — Microsoft Support, *Compare Microsoft Copilot Notebooks and Microsoft OneNote Notebooks*, cập nhật **11/2026**; phân biệt hai sản phẩm, feature matrix.
- **[S02]** — Microsoft Support, *What are Copilot Notebooks in OneNote?*, cập nhật **11/2026**; khả năng tích hợp và tài liệu tham chiếu.
- **[S03]** — Microsoft Support, *Getting Started with the OneNote Web Clipper*; article/full/region/PDF/YouTube, extension quyền truy cập.
- **[S04]** — Microsoft Support, *Insert online videos into OneNote for Windows*; nền tảng và điều kiện M365.
- **[S05]** — Microsoft Support, *Get answers and insights about your Copilot Notebook*; nguồn được hỗ trợ và giới hạn.
- **[S06]** — Microsoft Support, *FAQ Copilot Notebooks*, cập nhật **11/2026**; license, tiers, privacy.
- **[S07]** — Microsoft Support, *Record audio or video notes*; liên kết ghi chú với thời điểm ghi.
- **[S08]** — Microsoft Support, *Transcribe your recordings*; OneNote capture/transcribe và ink replay.
- **[S09]** — Microsoft Support, *Organize your notes with Copilot in OneNote*; **public preview**, preview → Apply.
- **[S10]** — Microsoft Support, *How Copilot Notebooks works*, cập nhật **11/2026**; scoped references.
- **[S11]** — Microsoft Support, *How Copilot Notebooks works*; **up to 300 files for grounding**, audio languages, notebook deletion.
- **[S12]** — Microsoft Support, *Get answers and insights...*; số references theo gói.
- **[S13]** — Microsoft Support, *Sync a notebook in OneNote*; offline, auto sync trên Android và Windows.
- **[S14]** — Microsoft Support, *Fix issues when you can't sync OneNote*; sync conflict/large attachments.
- **[S15]** — Microsoft Support, *Continue Copilot Notebook chats on mobile*, cập nhật **11/2026**.
- **[S16]** — Microsoft Support, *Differences between browser and desktop OneNote*; thiếu audio/ink/linked notes web.
- **[S17]** — Microsoft Learn, *Get OneNote content and structure*, Graph GET pages/HTML/resources, backup limitations.
- **[S18]** — Microsoft Learn, *Create OneNote pages*, Graph POST HTML + permissions.
- **[S19]** — Microsoft Learn, *Update OneNote page content*, Graph PATCH + permissions.
- **[S20]** — Microsoft Learn, *Microsoft Graph service-specific throttling limits*, OneNote limits.
- **[S21]** — Microsoft Support, *Copilot Notebooks licensing*, cập nhật **11/2026**, bảng tier doanh nghiệp; không áp giá enterprise cho personal.
- **[S22]** — Microsoft Store US, *Compare Microsoft 365 Plans & Pricing*, giá US minh họa ở thời điểm truy cập, không phải giá VN.
- **[S23]** — Microsoft Support, *Export OneNote notebooks*; personal-only và import deprecated.
- **[S24]** — Microsoft Support, *FAQ Copilot Notebooks*, mục Privacy; không dùng dữ liệu notebook để train LLM.
- **[S25]** — Microsoft Support, *Take notes with Copilot in OneNote*; rollout chưa phủ hết.
- **[S26]** — Microsoft Learn, *Release Notes Microsoft 365 Copilot* (trang công bố cập nhật giữa **11/2026**); tạo bản nháp Word từ Copilot Notebooks trên Windows/web.
- **[S27]** — Microsoft Support, *OneNote for the web Help*; page timestamp và chức năng web.
- **[S28]** — Microsoft Support, *Apply a tag to a note in OneNote*; tag thủ công và tìm theo tag.
- **[S29]** — Microsoft Support, *Export notes from OneNote as a PDF*; snapshot tĩnh, không phải backup khả năng edit.
- **[S30]** — Microsoft Learn, *Create OneNote pages*; lỗi 507 khi chạm page/section limit.

[S01]: https://support.microsoft.com/en-us/microsoft-365-copilot/compare-microsoft-365-copilot-notebooks-and-microsoft-onenote-notebooks
[S02]: https://support.microsoft.com/en-us/microsoft-365-copilot/what-are-microsoft-365-copilot-notebooks-in-onenote
[S03]: https://support.microsoft.com/en-us/onenote/getting-started-with-the-onenote-web-clipper
[S04]: https://support.microsoft.com/en-us/onenote/insert-online-videos-into-onenote-for-windows
[S05]: https://support.microsoft.com/en-us/microsoft-365-copilot/get-answers-and-insights-about-your-microsoft-365-copilot-notebook
[S06]: https://support.microsoft.com/en-us/microsoft-365-copilot/frequently-asked-questions-about-microsoft-365-copilot-notebooks
[S07]: https://support.microsoft.com/en-us/onenote/onenote-help-and-learning/record-audio-or-video-notes
[S08]: https://support.microsoft.com/en-us/word/transcribe-your-recordings
[S09]: https://support.microsoft.com/en-us/onenote/organize-your-notes-with-copilot-in-onenote
[S10]: https://support.microsoft.com/en-us/microsoft-365-copilot/how-microsoft-365-copilot-notebooks-works
[S11]: https://support.microsoft.com/en-us/microsoft-365-copilot/how-microsoft-365-copilot-notebooks-works
[S12]: https://support.microsoft.com/en-us/microsoft-365-copilot/get-answers-and-insights-about-your-microsoft-365-copilot-notebook
[S13]: https://support.microsoft.com/en-us/onenote/onenote-help-and-learning/sync-a-notebook-in-onenote
[S14]: https://support.microsoft.com/en-us/onenote/onenote-help-and-learning/fix-issues-when-you-can-t-sync-onenote
[S15]: https://support.microsoft.com/en-us/microsoft-365-copilot/continue-microsoft-365-copilot-notebook-chats-on-your-mobile-device
[S16]: https://support.microsoft.com/en-us/onenote/onenote-for-web-help-and-learning/differences-between-using-a-notebook-in-the-browser-and-in-onenote
[S17]: https://learn.microsoft.com/en-us/graph/onenote-get-content
[S18]: https://learn.microsoft.com/en-us/graph/onenote-create-page
[S19]: https://learn.microsoft.com/en-us/graph/onenote-update-page
[S20]: https://learn.microsoft.com/en-us/graph/throttling-limits
[S21]: https://support.microsoft.com/en-us/microsoft-365-copilot/copilot-notebooks-licensing
[S22]: https://www.microsoft.com/en-us/microsoft-365/buy/compare-all-microsoft-365-products
[S23]: https://support.microsoft.com/en-us/onenote/export-and-import-onenote-notebooks
[S24]: https://support.microsoft.com/en-us/microsoft-365-copilot/frequently-asked-questions-about-microsoft-365-copilot-notebooks
[S25]: https://support.microsoft.com/en-us/onenote/take-notes-with-copilot-in-onenote
[S26]: https://learn.microsoft.com/en-us/microsoft-365/copilot/release-notes
[S27]: https://support.microsoft.com/en-us/onenote/onenote-for-the-web-help
[S28]: https://support.microsoft.com/en-us/onenote/onenote-help-and-learning/apply-a-tag-to-a-note-in-onenote
[S29]: https://support.microsoft.com/en-us/onenote/onenote-help-and-learning/export-notes-from-onenote-as-a-pdf
[S30]: https://learn.microsoft.com/en-us/graph/onenote-create-page

## 9. QA nghiên cứu / phạm vi thực thi

| Hạng mục | Kết quả | Giới hạn |
| --- | --- | --- |
| Đọc đúng entrypoint G05 + quy trình K01–K12 | **PASS (document inspection)** | Không sử dụng báo cáo luồng khác |
| Đối chiếu mã main: ingestion, catalog, organization, tree, read_knowledge, transcribe, UI | **PASS (code inspection)** | Không checkout/chạy lại test; các claim runtime dẫn CURRENT_STATE |
| Nguồn tối thiểu 5 URLs / 3 nguồn chính thức | **PASS** (30 mã nguồn tham chiếu; 23 URL phân biệt, đều Microsoft công khai) | Có URL trùng khi dùng nguồn cho hai luận điểm, công bố rõ |
| K01–K12 có trạng thái, chứng cứ, bước tái thử, phần thiếu | **PASS (coverage check)** | Chưa chạy UAT |
| 7 trụ, công thức tổng, 3–6 ý tưởng, phản chứng và ≥3 rủi ro | **PASS (coverage check)** | Score là review định tính, không đo hiệu năng |
| OneNote/Copilot trên account/license thật | **NOT_RUN** | Không có quyền/credential được cung cấp và không tự đăng ký/mua |
| Windows/Android UI, IME Việt, offline sync conflict, audio seek | **NOT_RUN** | Không có buổi kiểm thử thiết bị/app trong phạm vi report |
| Graph API thực với OAuth/restore ZIP và benchmark 10k media | **NOT_RUN** | Không xin token/không chuyển dữ liệu thật |
| Runtime test Kho Tri Thức trong G05 | **NOT_RUN** | Phạm vi chỉ nghiên cứu; không thay mã, không sửa CURRENT_STATE |
| Giá/điều kiện tài khoản ở Việt Nam | **UNVERIFIED** | Giá US chỉ minh họa |

**Bản nghiên cứu độc lập; cần G00 phản biện/kiểm chéo nguồn trước khi quyết định roadmap. Không merge PR, không sửa ứng dụng.**
