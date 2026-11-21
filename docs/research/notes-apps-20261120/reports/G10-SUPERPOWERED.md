# G10 — Nghiên cứu độc lập Superpowered AI Notetaker

**Thời điểm khảo sát:** 20/11/2026 (Asia/Ho_Chi_Minh)  
**Sản phẩm:** Superpowered AI Notetaker tại https://superpowered.me/ — công cụ ghi chú họp *botless*, **không phải** SuperpoweredAI (superpowered.ai, RAG API), Superpowered Audio SDK (superpowered.com) hoặc Superhuman.  
**Đối chứng nội bộ:** cavoixanh638/kho-tri-thuc, nhánh main, commit [c97f5678a6893d7dfec2595d89c9122f05195320](https://github.com/cavoixanh638/kho-tri-thuc/commit/c97f5678a6893d7dfec2595d89c9122f05195320).  
**Phương pháp:** đọc website, hồ sơ sản phẩm và nguồn đối chiếu độc lập; kiểm mã nguồn Kho Tri Thức; **không đăng nhập, cài phần mềm, cấp quyền lịch hoặc gửi dữ liệu thật**. UI/API/ASR thực của Superpowered: **NOT_RUN**. Không đọc báo cáo các luồng nghiên cứu khác hoặc G00-INITIAL-SOURCES.

## 1. Tóm tắt điều hành (dưới 200 từ)

**Khuyến nghị: Không áp dụng để thay thế Kho Tri Thức; chỉ tham khảo UX/tư duy tổ chức biên bản họp.** Superpowered từng được giới thiệu là phần mềm Windows/macOS thu tiếng từ thiết bị mà không đưa bot vào cuộc họp, chuyển lời nói thành ghi chú và dùng mẫu ghi chú. Nhà cung cấp tuyên bố không lưu bản ghi âm, âm thanh được xóa ngay, transcript giữ 7 ngày. Tuy nhiên, **trang tải xuống chính thức hiện thông báo không còn cho tải ứng dụng**, trong khi trang chủ vẫn giữ bảng giá/quảng cáo; vì vậy không thể coi bảng giá hoặc tính năng lịch sử là một dịch vụ đang mua và chạy được. Ứng dụng cũng công khai không hỗ trợ Android, không có bằng chứng về tiếp nhận URL/video/PDF như một kho tri thức, cây phân loại, quan hệ nguồn hay đường xuất dữ liệu mở. Repo Kho Tri Thức đã có những năng lực đó ở mức triển khai/kiểm thử khác nhau. Hướng đáng học: mẫu biên bản, tách việc cần làm khỏi phần ghi chú, UX lấy ghi chú nhanh và chính sách rõ ràng cho dữ liệu AI tạm thời.

## 2. Xác minh sản phẩm, tình trạng vận hành, phát hành

### 2.1. Phát hiện có thể kiểm chứng

1. **[S1, nguồn chính thức, hiện còn truy cập]** Trang chủ mô tả *no bots, no recordings*, AI Notes/AI Templates và AI Chat **“Coming Soon”**; ghi rõ macOS/Windows, **không có mobile/Linux**; có tiếng Việt trong danh sách ngôn ngữ hỗ trợ. Đây là **tuyên bố sản phẩm**, không phải bài đo chất lượng tiếng Việt.
2. **[S2, nguồn chính thức, quan trọng nhất]** Đường “Try now for free” trên trang chủ trỏ tới https://superpowered.me/download; tại ngày khảo sát trang ghi **“Superpowered is no longer available for download.”** Do đó **không thể xác nhận cài mới hoặc kiểm thử end-to-end**. Không tự suy rằng mọi tài khoản cũ, dữ liệu cũ hoặc backend đã đóng hoàn toàn.
3. **[S3, trang trạng thái của nhà cung cấp]** Ghi “All services are online”, nhưng **lần cập nhật hiển thị cuối là 30/06/2026**. Trang này không phủ nhận thông báo ngừng tải ngày khảo sát; backend/landing hoạt động không có nghĩa một người dùng mới đăng ký/cài được.
4. **[S4, nguồn công bố lịch sử qua Y Combinator]** Liên kết YC từ trang chủ Superpowered hiện điều hướng sang hồ sơ **Vapi**; nội dung lịch sử ghi rõ có thời kỳ Superpowered AI Notes bot-free. **[S5, TechCrunch ngày 10/11/2023]** cho biết nhóm sáng lập chuyển hướng sang Vapi; **tại thời điểm bài báo**, họ nói sản phẩm cũ chưa đóng. Đây là thông tin **2023**, không phải bằng chứng về hoạt động năm 2026.
5. **[S6, danh mục độc lập]** Dang.ai đánh dấu ứng dụng không còn hoạt động từ **31/07/2024**. Đây là dấu hiệu thứ cấp, **không đủ để khẳng định ngày ngừng thực tế**. Trang chủ cũ và mục quảng bá/số liệu khách hàng không được dùng để bác bỏ [S2].
6. **Không tìm được changelog/release note chính thức 2026 của ứng dụng ghi chú**, không xác minh bản cài mới hoặc vòng đời hỗ trợ. Các repo/SDK tại **superpowered.ai** và **superpowered.com** không phải mã/API của ứng dụng **superpowered.me** ([S10], [S11]).

### 2.2. Năng lực công khai, phân loại độ chắc chắn

| Năng lực/thuộc tính | Phát hành/beta/planned và giới hạn chứng cứ |
| --- | --- |
| Ghi chú cuộc họp *botless*, không thêm người tham dự | **Đã từng được công bố** [S1, S4]. Lấy âm thanh thiết bị rồi chuyển thành transcript; **không đồng nghĩa ghi âm file để phát lại**. Khả năng dùng mới 20/11/2026: **UNVERIFIED** vì [S2]. |
| Live transcription và AI meeting notes | **Đã được quảng bá là tính năng hiện hữu trong phiên bản lịch sử** [S1, S4]. Chưa test độ trễ, speaker diarization, độ chính xác hoặc lưu/sao chép transcript. |
| Mẫu AI (1:1, sales, interviews, tự tùy biến) | **Đã được quảng bá** [S1], có thể lấy làm mẫu thiết kế UX; cấu trúc nội bộ/export không được công khai. |
| Trích xuất đầu việc | Ví dụ *Action Items* xuất hiện trong bản giới thiệu/ảnh mô tả [S1]; **chưa xác minh** có task entity, deadline, người phụ trách, API hoặc tự đẩy tác vụ. |
| AI Chat hỏi lại mọi cuộc họp | Trang chủ ghi **Coming Soon** [S1]. **Không coi đã phát hành**. |
| Google/Outlook Calendar; Slack, Email, Notion, Google Drive, Salesforce, HubSpot, Zapier | **Tuyên bố tích hợp/định mức theo gói** trên trang chủ [S1]. Đồng bộ ghi chú tới Google Drive/Notion **không chứng minh** export đầy đủ history, assets, raw transcript hay API mở. |
| Nền tảng | **Windows/macOS lịch sử**, nhà cung cấp nói **mobile và Linux chưa hỗ trợ** [S1]. Không tìm được chế độ Android Share Target hay offline-first. Tải desktop mới đang bị chặn [S2]. |
| Ngôn ngữ | Website liệt kê **Vietnamese** [S1]; **NOT_RUN** với tiếng Việt có dấu, tên riêng, nhiều người nói, tiếng địa phương. Không tìm được cam kết về giao diện tiếng Việt hoặc Unicode Markdown round-trip. |
| Lưu trữ/riêng tư | Nhà cung cấp nói **không giữ audio**, xóa sau chuyển lời; **transcript giữ 7 ngày**; **note history** là thuộc tính riêng của gói [S1]. Không kiểm được xóa thật, nơi lưu, bản sao lưu, export, DPA hoặc chu kỳ lưu log. |
| Bảo mật/license | Trang chủ **tự tuyên bố** SOC 2 Type II và GDPR [S1]; link security truy cập trả **403** [S8], policy/terms dẫn tới Notion trả **404** [S9]. Không xác minh báo cáo kiểm toán hay giấy phép code; **không có bằng chứng ứng dụng ghi chú là open source**. |
| API / SDK / MCP / file Markdown import-export | **UNVERIFIED**: không thấy tài liệu công khai cho ứng dụng **superpowered.me**. Không suy API từ GitHub của sản phẩm **superpowered.ai** [S10]. |

**Giá hiển thị, không phải báo giá khả dụng:** trên [S1] trang chủ đang hiển thị Free **$0**, Basic **$25/tháng**, Pro **$50/tháng**, chọn năm ghi giảm **tối đa 54%**. Trang cũng hiển thị Free có **1 tháng** lịch sử notes, hai gói trả phí ghi **unlimited notes history**, các tích hợp theo tier. **Chưa thử thanh toán**, chưa xác minh thuế, quota/chỗ phân gói hoặc tình trạng thuê bao sau thông báo [S2]. **7 ngày transcript khác với 1 tháng/vô hạn lưu notes**; không đánh đồng các retention này.

### 2.3. Giới hạn riêng tư và nguồn

- Phương án *không lưu audio* có ích về tối thiểu hóa dữ liệu nhưng khiến việc **nhảy tới chính xác thời điểm audio/video gốc** không có sẵn trong sản phẩm. Nếu Kho Tri Thức muốn chứng minh câu trích thì phải giữ nguồn riêng có quyền truy cập; AI summary không thay nguồn.
- Dù không lưu recording, **vẫn phải xét thông báo và sự đồng ý hợp lệ khi xử lý lời nói cuộc họp**; chính FAQ của nhà cung cấp nhắc kiểm luật đồng ý [S1]. Không suy tuyên bố “SOC 2/GDPR compliant” là bảo đảm tuân thủ của người dùng Việt Nam.
- Không thấy tài liệu public về bulk export/GDPR deletion request, nơi xử lý dữ liệu, chế độ giữ file PDF/video, khả năng self-host, hay bản OSS. Chứng cứ **vắng mặt** được đánh dấu **UNVERIFIED**, không gán thành “không tồn tại” một cách chắc chắn.

## 3. Bộ ca K01–K12 (đánh giá từ nguồn, không giả lập PASS)

**Ý nghĩa trạng thái:** NATIVE = có chứng cứ chức năng **đúng toàn bộ yêu cầu**; EXTENSION = phụ thuộc plugin công bố; CUSTOM_BACKEND = muốn đạt được phải xây một backend riêng **bên ngoài sản phẩm**; NOT_SUPPORTED = gặp giới hạn công khai trực tiếp; UNVERIFIED = không có bằng chứng đủ. Tất cả ca **chưa chạy trực tiếp: NOT_RUN** vì [S2] và chưa có tài khoản/quyền. Các bước tái thử sau đây chỉ dành cho trường hợp nhà cung cấp cung cấp lại bộ cài/chỗ truy cập hợp lệ.

| Ca | Trạng thái | Căn cứ + bước tái thử tối thiểu; điều chưa chắc |
| --- | --- | --- |
| **K01** ghi nhanh tiếng Việt, receipt + giờ | **UNVERIFIED** | [S1] hỗ trợ tiếng Việt trong danh sách ASR và AI meeting notes, **không có chứng cứ** editor tự gõ + server receipt. Tái thử: gõ hai câu có dấu, gửi, kiểm ID/thời gian server, reload và so byte Unicode. |
| **K02** gửi URL video/web, tự lấy metadata/nội dung | **UNVERIFIED** | [S1] chỉ mô tả audio cuộc họp/công cụ lịch. Tái thử: dán URL công khai web, YouTube, TikTok, Facebook; kiểm nhận ngay, metadata và **transcript thật**/trạng thái thiếu; không suy lời nói từ tiêu đề. |
| **K03** gửi URL trùng ngày sau, tách event/retry | **UNVERIFIED** | Không có mô hình capture-event/idempotency công khai [S1]. Tái thử: gửi link hai ngày khác nhau, lặp cùng request key; đếm sự kiện, item/file, kiểm UTC và giờ địa phương. |
| **K04** Markdown + bảng/link/Unicode qua save/reload | **UNVERIFIED** | AI Templates không chứng minh Markdown editor/round-trip [S1]. Tái thử ghi bảng GFM, dấu tiếng Việt, liên kết, export rồi import; so nội dung gốc. |
| **K05** tự gán vào nhóm **đã có** | **UNVERIFIED** | Không thấy bằng chứng về taxonomy hoặc **gán thật**; AI Chat vẫn *Coming Soon* [S1]. Tái thử tạo 3 nhóm cố định, 10 tài liệu cùng chủ đề, kiểm assignment DB chứ không chỉ đề xuất. |
| **K06** backlinks/related items cạnh bài | **UNVERIFIED** | Không có public schema/UI liên kết có nguồn [S1]. Tái thử hai ghi chú liên quan nhưng không trùng, xem liên kết hai chiều, reason/confidence, bỏ liên kết. |
| **K07** PDF/audio/video + nhảy trang/timestamp | **NOT_SUPPORTED** **đối với phát lại audio họp** | [S1] nêu **không giữ bản ghi âm**, do đó không có audio lưu trong chính app để seek. PDF/video/locator riêng **UNVERIFIED**. Tái thử bằng PDF 5 trang, MP4 có mốc, đo thời điểm seek ±2s và xác minh tài sản gốc. |
| **K08** nhiều lĩnh vực, tree/table/card/timeline | **UNVERIFIED** | [S1] có “notes history”, **không chứng minh** quan hệ many-to-many/hệ đa góc nhìn. Tái thử một bài gán hai lĩnh vực, đối chiếu tree/table/card/timeline cùng Item ID. |
| **K09** Android + Windows, offline, conflict | **NOT_SUPPORTED** **về Android** | [S1] nói mobile chưa hỗ trợ; Windows từng được hỗ trợ nhưng [S2] hiện không cho tải. Offline/conflict **UNVERIFIED**. Tái thử Android Share/PWA, Windows, ngắt mạng rồi sửa hai phía và đối chiếu conflict. |
| **K10** API, export/import Markdown+assets, backup thoát dịch vụ | **UNVERIFIED** | [S1] liệt kê Notion/Drive integration nhưng không cho thấy API/bulk export, [S9] policy/terms không đọc được. Tái thử xuất 100 notes, 10 assets + links/timestamps, nhập vào máy khác giữ IDs; thử delete/export request. |
| **K11** AI có provenance, gợi ý khác sửa user, quyền/chi phí | **UNVERIFIED** | **Thành phần AI Notes NATIVE theo tuyên bố lịch sử** [S1, S4], nhưng không chứng minh cite từng nguồn/đoạn, audit, quyền duyệt hay khả năng bảo toàn ghi chú gốc. Tái thử 20 mẫu, so gợi ý với nguồn, từ chối/duyệt, đo usage và kiểm không tự sửa. |
| **K12** >10.000 mục, hàng trăm GB video/Drive | **UNVERIFIED** | Không thấy giới hạn/quota/benchmark/remote-storage corpus [S1]; số khách hàng quảng bá **không phải số item hoặc video**. Tái thử import bộ dữ liệu được phép, đo tốc độ/index/chi phí 10.000 items và 300 GB, verify checksum từ xa. |

**Kết luận ma trận:** không ca nào được gán **PASS thực nghiệm**; không viện dẫn SDK/API từ sản phẩm trùng tên. Việc nhiều ca UNVERIFIED là **giới hạn bằng chứng**, không tự động coi tất cả là 0 điểm chất lượng sản phẩm.

## 4. Đối chiếu **mã hiện hành** Kho Tri Thức, không dựa vào bản kế hoạch cũ

Đã xem mã ở **main SHA c97f5678…**; các link dưới đây khóa về chính commit đã khảo sát. Bằng chứng runtime được tham chiếu **CURRENT_STATE.md** ngày 20/11/2026, **không chạy lại Windows/Android/CI trong luồng nghiên cứu**. CURRENT_STATE có đoạn bảng lịch sử chưa cập nhật ASR; ưu tiên checkpoint mới ở **đầu file** và code có thực.

| Nhu cầu | Hiện trạng đã tìm trong code/repo | So với Superpowered / quyết định |
| --- | --- | --- |
| Capture text/URL, receipt, giờ bất biến, retry | **ĐÃ CÓ mã**: [ingestion/services.py#L78-L181](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/ingestion/services.py#L78-L181) ghi CaptureEvent, server_received_at, canonical Source/Item và idempotency; [CaptureScreen.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/CaptureScreen.tsx) có nhập text/link/file. | Superpowered không chứng minh giải pháp tốt hơn cho URL/video: **không thay**. |
| Markdown/GFM bảng, link, Unicode | **ĐÃ CÓ mã** textarea chỉnh nội dung + [KnowledgeText.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/KnowledgeText.tsx) dùng react-markdown/remark-gfm và bảo vệ URL; [ItemScreen.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/ItemScreen.tsx). | **CẢI THIỆN** UX mẫu ghi chú/chuyển bản nháp; chưa cần đổi editor. |
| Nhóm nhiều-mục, cây sâu, liên quan | **ĐÃ CÓ mã** [catalog/models.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/models.py), [organization.py#L104-L233](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/catalog/organization.py#L104-L233) và [KnowledgeTree.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/web/src/KnowledgeTree.tsx); rule lexical còn cần đánh giá corpus thật. | Superpowered không có bằng chứng hỗ trợ cây/quan hệ: **không áp dụng** mô hình thay thế. |
| URL/web/video/source provenance | **ĐÃ CÓ nhưng còn giới hạn** [source_fetch.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/source_fetch.py) và source/asset metadata; Reel Facebook live đã được kiểm, các nguồn khác chưa nghiệm thu đủ. | **Không** lấy nội dung cuộc họp từ metadata hay giả định toàn video đã được AI hiểu. |
| ASR video với đoạn thời gian | **ĐÃ CÓ mã** [transcribe.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/transcribe.py), [transcript_job.py#L238-L288](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/transcript_job.py); transcript với segments, language, model_version, gắn với Asset; checkpoint **KT-113** ghi Reel thử có 11 đoạn local ASR. | **CẢI THIỆN** UI đánh dấu quyết định/đầu việc từ transcript, không thay offline ASR bằng dịch vụ không còn bộ cài. Chưa chứng minh seek audio chính xác hay ASR đa nguồn. |
| Bảo toàn nguồn và AI-derived content | **ĐÃ CÓ** [processing/models.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/models.py) với source_locator, processor/version/hash, không đồng nhất Item.note với derived text; [knowledge.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/processing/knowledge.py) cảnh báo video chưa có transcript. | **CẢI THIỆN** policy hiển thị TTL dữ liệu tạm thời, tách lời nói/ghi chú AI và gốc. |
| Drive/export/restore | **ĐÃ CÓ mã và một số live pilot**: [storage/knowledge_export.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/apps/backend/storage/knowledge_export.py), trạng thái nêu trong [CURRENT_STATE.md](https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/docs/CURRENT_STATE.md). | Superpowered chỉ giới thiệu tích hợp, không có bằng chứng portable hơn: **không thay** Drive/PostgreSQL. |
| Android/Windows | PWA có thành phần frontend, **Windows đã được checkpoint live**, **Android thiết bị thật/HTTPS vẫn NOT_RUN** theo CURRENT_STATE.md. | Superpowered công khai **không hỗ trợ Android** [S1]: **không phù hợp** cho workflow Android + PC. |
| Mẫu biên bản và trích việc cần làm có duyệt | **CHƯA THẤY** entity/flow sản phẩm chuyên cho họp tại code đã xem; có Item.note, DerivedContent và workflow để tích hợp nhẹ. | **THAM KHẢO UX**, không sao chép UI/code/SDK thương mại; triển khai độc lập khi có yêu cầu. |
| Ghi cuộc họp botless theo thời gian thực | Kho Tri Thức hiện chú trọng thu URL/text/file và offline ASR sau khi có file; **chưa thấy live desktop system-audio capture**. | **KHÔNG ƯU TIÊN** cho kho cá nhân; nếu cần họp live phải kiểm đồng ý, quyền OS, thiết bị, lưu nguồn và mục tiêu tìm kiếm. |

### Nhìn từ người dùng cá nhân Việt Nam

**Điểm có ích ở Superpowered (theo công bố lịch sử):** rút ngắn thao tác lập biên bản sau cuộc họp; mẫu ghi chú giúp thống nhất kết quả; tách action items; transcript tiếng Việt được liệt kê hỗ trợ; giảm nhu cầu mời bot vào phòng họp.

**Điểm không phù hợp:** không cho tải bộ cài mới, không Android, không hỗ trợ thư viện văn bản/media đa nguồn được chứng minh, không giữ âm thanh để người dùng nhảy đúng giây, thiếu API/export độc lập và thiếu bằng chứng phân loại/liên kết. Độ chính xác tiếng Việt, Word-like editor, offline, quyền xử lý cuộc họp nội bộ, data residency chưa được đo. **Một bản chép lời chỉ chứng minh những từ hệ thống ghi nhận; không chứng minh AI đã hiểu toàn bộ video.**

## 5. Chấm 7 trụ G00 theo **mức đáp ứng yêu cầu Kho Tri Thức** (không chấm chất lượng lịch sử của ứng dụng)

| Trụ | Điểm phù hợp / tối đa | Độ tin cậy | Giải thích |
| --- | ---: | --- | --- |
| Capture + ingestion | **4/20** | Trung bình | Có meeting capture theo mô tả lịch sử; không có chứng cứ capture URL/video/web/file đa nguồn, lại dừng phát bộ cài. |
| Organization + recall | **3/20** | Trung bình | Notes history và template có ích; không chứng minh taxonomy many-to-many, auto assignment/backlinks; AI Chat còn *coming soon*. |
| Text editor + reading | **4/15** | Trung bình | AI Notes/templates; chưa chứng minh editor Markdown/GFM và bảo toàn văn bản qua round-trip. |
| Provenance / related / timestamps | **1/15** | Trung bình-cao | Không lưu recording; chứng cứ chi tiết theo nguồn, thời gian và đồ thị liên quan không có. |
| Android / Windows / offline | **1/10** | Cao về Android và khả dụng | Windows từng hỗ trợ; Android không hỗ trợ; tải mới đóng; offline/conflict không rõ. |
| Portability / backup | **0–3/10** | **Thấp** | Có nhắc tích hợp Drive/Notion, nhưng chưa chứng minh bulk export API/asset, không được tự chấm 0 tuyệt đối. |
| Integration / cost / maintainability | **2/10** | Trung bình | Có tích hợp và giá hiển thị, nhưng không thể xác minh vận hành/mua mới; không có SDK/MCP phù hợp. |
| **Tổng** | **15–18/100** | **Khoảng ước lượng, không phải điểm đo thực nghiệm** | 4+3+4+1+1+(0–3)+2 = **15–18**. |

**Phán quyết hai trục:**
- **Thay thế toàn hệ thống: KHÔNG ÁP DỤNG** (dù cho điểm tối đa trong vùng chưa xác minh, vẫn thiếu Android, URL/video corpus, quyền sở hữu dữ liệu và trạng thái phân phối).
- **Giá trị học tính năng: TRUNG BÌNH–KHÁ, giới hạn ở UX ghi chú họp** (mẫu, action items, giảm thao tác, tối thiểu hóa dữ liệu tạm). Đây là **giá trị ý tưởng**, không phải đề xuất tích hợp sản phẩm đã ngừng tải.

## 6. Ý tưởng mượn có kiểm soát, không viết lại stack

| Đề xuất + ưu tiên | UX / technical / adapter, độ khó | Acceptance test đo được; phụ thuộc, rủi ro |
| --- | --- | --- |
| **A. Mẫu ghi chú có cấu trúc** — Ưu tiên 1 | **S**. Nút “Tạo từ mẫu” sinh Markdown có mục *Nội dung / Quyết định / Việc cần làm / Nguồn*; 3 preset (họp, phỏng vấn, ghi chú đọc); ghi vào Item.note qua API hiện có. **Không cần SDK bên thứ ba.** | 3 mẫu tạo/lưu/reload đúng cấu trúc; thử 20 ghi chú tiếng Việt có dấu + bảng GFM đạt **20/20 byte-roundtrip**; thay mẫu không tự ghi đè note đã sửa. Rủi ro: mẫu cứng làm rườm rà, luôn có “trống”. |
| **B. Action items ở dạng đề xuất có duyệt** — Ưu tiên 2 | **M**. Trên note hoặc transcript đã có, trích *việc / người / hạn / nguồn trích* thành **proposal**, cho chấp nhận/sửa/bỏ; dùng DerivedContent/source_locator hiện có hoặc adapter mỏng, **không** viết trực tiếp vào Item.note. Quy tắc đơn giản trước; model adapter chỉ khi được duyệt. | Bộ 30 đoạn gán nhãn thủ công; **0 đề xuất nào được chấp nhận tự động**, 100% đề xuất có source item + đoạn chứng cứ, đánh giá precision trước bật AI (mục tiêu **≥90%** trên dữ liệu kiểm thử), không invent deadline/người nếu nguồn thiếu. Rủi ro chi phí và ảo giác AI. |
| **C. Quick note bám nguồn và thời gian** — Ưu tiên 3 | **M**. Trong màn đọc video/transcript cho nhập ghi chú tại mốc đang xem; lưu như ghi chú/ngữ cảnh riêng, liên kết tới item_id/source_locator/time; dùng CaptureEvent và frontend hiện có, không đụng DB/Drive gốc nếu schema hiện tại đủ; nếu thiếu thì làm PoC adapter trước. | 20 ghi chú giả lập tại 20 mốc: thứ tự và receipt đúng, 0 mất chữ sau reload, 0 thay đổi Asset gốc; 5 seek thử với media thật phải vào đúng đoạn **±2 giây** trước khi báo PASS. Rủi ro khi video Drive chưa phát được và khi source hết quyền. |
| **D. Chính sách rõ ràng cho transcript/AI tạm** — Ưu tiên 4, có điều kiện | **M**. UX gắn nhãn “AI tạo / nguồn có thể xóa / giữ vĩnh viễn nếu người dùng chủ động xác nhận”, cho chọn TTL riêng với **dữ liệu dẫn xuất**. Tối thiểu hóa retention; **không xóa** CaptureEvent lịch sử, Item.note của người dùng hoặc nguồn gốc do AI suy đoán. Chỉ triển khai sau khi xác định chính sách backup. | Đồng hồ giả lập ở mốc ngày 0/7/8, test xoá chỉ đúng derivative được chọn, source/Item/backup được kiểm tra nhất quán; audit lưu dấu quyết định; tắt TTL không xóa gì. Rủi ro backup giữ transcript lâu hơn TTL, cần mô tả rõ. |
| **E. Nhận diện cuộc họp từ lịch (tùy chọn sau)** | **M**. Bắt đầu bằng nhập tiêu đề/thời gian cuộc họp hoặc file .ics do người dùng chủ động cung cấp; lưu metadata nguồn vào Item/Source hiện có. **Không** xin OAuth lịch/phân quyền doanh nghiệp ở bản đầu. | 10 sự kiện + 2 trùng được ghép đúng, không ghi trùng lịch sử capture, giờ Việt Nam/UTC hiển thị chuẩn, không tự gửi dữ liệu họp ra SaaS. Rủi ro lộ tiêu đề/đối tượng họp, khóa consent ở nhập nguồn. |

**Nguyên tắc thực thi:** các mục A–E là **đề xuất cho G00 đánh giá**, không phải tính năng đã triển khai hoặc yêu cầu sửa code trong PR nghiên cứu. Không thêm PostgreSQL mới, Celery, graph DB, API Vapi hay plugin có license chưa kiểm. Chưa ưu tiên botless realtime audio capture vì Windows system audio/consent/diarization và phát lại là một phạm vi khác; ASR hậu xử lý hiện có nên được kiểm thực tế trước.

## 7. Rủi ro, giới hạn, giả thuyết phản chứng

**Các rủi ro/giới hạn quan trọng:**

1. **Khả dụng:** [S2] chặn tải mới; homepage chưa xóa giá. Không có đăng nhập/bộ cài ⇒ **NOT_RUN** toàn bộ K01–K12 ở UI thật, không gán PASS.
2. **Bằng chứng pháp lý thiếu:** security [S8] trả 403; Terms/Privacy [S9] trả 404 ở kênh web khảo sát. Tuyên bố SOC 2/GDPR của trang chủ chưa được kiểm chứng độc lập, quy tắc xóa dữ liệu/backup chưa rõ.
3. **Dữ liệu không đủ cho truy nguyên:** không recording + transcript 7 ngày là điểm khác biệt lớn so với mục tiêu xem video, dẫn lại đúng thời điểm, xuất độc lập toàn bộ kho.
4. **Chênh lệch nguồn theo thời gian:** TechCrunch năm 2023 nói chưa đóng sản phẩm cũ; danh mục Dang.ai năm 2024 đánh dấu inactive; status 06/2026 nói backend online; trang tải hiện tại nói không còn. Vì vậy **không áp ngày đóng chính xác**; chỉ kết luận **không còn kênh tải công khai** tại ngày khảo sát.
5. **Thiếu phép đo:** không có kiểm ASR tiếng Việt/chuyên ngành, Android, offline, nhiều người nói, API/exports, hiệu năng >10.000 mục, hay chi phí thật; thông tin marketing không phải performance benchmark.
6. **Tên gọi gây nhầm:** SuperpoweredAI SDK RAG [S10] và Superpowered Audio SDK [S11] là sản phẩm/domain khác. Không được dùng mã hoặc giấy phép của chúng để “chứng minh” SDK cho superpowered.me.
7. **Lock-in/licensing:** nếu ghi chú/AI history nằm trong tài khoản SaaS không có bulk export/backup được chứng minh, mất kênh tải đồng nghĩa rủi ro không thể khôi phục. **Không nhập dữ liệu cá nhân/cuộc họp thật** để thử lại khi chưa xác minh quyền và điều khoản.

**Phản chứng có thể đổi khuyến nghị:** sản phẩm có thể được phát hành lại. Chỉ xem xét **PoC tích hợp/đổi điểm** nếu đồng thời có: (i) bộ cài và dashboard hoạt động chính thức, tài liệu hỗ trợ còn cập nhật; (ii) API hoặc export đầy đủ Markdown/raw notes, metadata, asset pointers và bằng chứng khôi phục; (iii) chạy được Android/Windows hoặc luồng Android Share hợp lệ; (iv) kiểm chứng được URL/video provenance và 10.000-item scale. Khi đó chạy lại **K01–K12** trên dữ liệu tổng hợp, không dùng tư liệu riêng, rồi chấm lại. **Chỉ có demo AI note đẹp không đảo ngược quyết định thay cả kho.**

## 8. Nguồn, thời gian và nhật ký kiểm chứng

**Đã truy cập/tra cứu ngày 20/11/2026.** Thứ tự ưu tiên: nguồn sản phẩm gốc → tổ chức giới thiệu sản phẩm → báo chí → danh mục độc lập. Các trang không mở được được nêu như giới hạn, không dùng làm chứng cứ nội dung.

| ID | Nguồn/URL | Ngày nội dung hoặc kết quả |
| --- | --- | --- |
| **S1 (chính thức)** | https://superpowered.me/ | Trang chủ truy cập 20/11/2026, copyright 2023, không thấy release date/changelog mới. Claims: tính năng, nền tảng, giá, ngôn ngữ, 7 ngày transcript, AI Chat planned. |
| **S2 (chính thức)** | https://superpowered.me/download | Truy cập 20/11/2026: **không còn cho tải**. Trang không ghi chính xác ngày bắt đầu. |
| **S3 (chính thức)** | https://status.superpowered.me/ | Hiện “online”, **Last updated Jun 30, 2026**. Không phải bằng chứng cho bộ cài/khả năng dùng. |
| **S4 (công bố lịch sử của đội ngũ sản phẩm)** | https://www.ycombinator.com/companies/superpowered (chuyển tới https://www.ycombinator.com/companies/vapi) | Trang YC cho biết quá trình ra Superpowered AI Notes và chuyển sang Vapi; có launch text lịch sử, không phải changelog 2026. |
| **S5 (báo chí)** | https://techcrunch.com/2023/11/10/yc-backed-productivity-app-superpowered-pivots-to-become-a-voice-api-platform-for-bots/ | Bài 10/11/2023: chuyển hướng Vapi; khi đó **chưa thông báo đóng** sản phẩm cũ. |
| **S6 (độc lập, độ tin cậy hạn chế)** | https://dang.ai/tool/ai-meeting-note-capture-and-transcription-tool-superpowered | Trang ghi ngừng active 31/07/2024, có dấu cập nhật 25/05/2026; không xác minh ngày đóng chính thức. |
| **S7 (lịch sử sản phẩm)** | https://www.producthunt.com/products/superpowered-me?launch=superpowered-3 | Có lịch sử sản phẩm, mốc launch 2021/2023, không phải chứng cứ đang hoạt động. |
| **S8 (chính thức, không đọc được)** | https://security.superpowered.me/ | HTTP **403** qua kênh truy cập hiện tại; không kiểm chứng được SOC 2 audit report. |
| **S9 (chính thức, không đọc được)** | https://superpowered.notion.site/Superpowered-Privacy-Policy-2a30820a790f4b0b9024e3fc10a7a4af | Liên kết từ website trả **404**; Terms cũng 404: https://superpowered.notion.site/Superpowered-Terms-of-Service-cf564af02de345749849ec9164956622. |
| **S10 (cảnh báo nhầm sản phẩm)** | https://github.com/SuperpoweredAI/superpowered-ai và https://www.ycombinator.com/companies/superpowered-ai | **superpowered.ai** là RAG/knowledge API, **không phải** notetaker tại superpowered.me. |
| **S11 (cảnh báo nhầm SDK)** | https://superpowered.com/ và https://docs.superpowered.com/getting-started/how-to-integrate/ | C++/WebAssembly audio SDK, sản phẩm khác, **không** phải API notetaker. |
| **B1 (mã Kho Tri Thức)** | https://github.com/cavoixanh638/kho-tri-thuc/tree/c97f5678a6893d7dfec2595d89c9122f05195320/apps | Kiểm các file ingestion, catalog, processing, storage, UI cùng snapshot main. |
| **B2 (trạng thái nội bộ)** | https://github.com/cavoixanh638/kho-tri-thuc/blob/c97f5678a6893d7dfec2595d89c9122f05195320/docs/CURRENT_STATE.md | Đầu file cập nhật 20/11/2026: KT-113 có mã ASR + 11 segments trên một Reel; Windows live trong phạm vi, Android/scale chưa nghiệm thu. |

**Kiểm thử:** đọc code/nguồn và kiểm consistency **DESK_REVIEW**; test cài đặt, API, dữ liệu, phí, ASR Superpowered, xuất/nhập, restore **NOT_RUN**. Không viết/sửa ứng dụng, không đọc báo cáo luồng khác, không merge. **Phạm vi commit mong đợi chỉ file báo cáo này**.
