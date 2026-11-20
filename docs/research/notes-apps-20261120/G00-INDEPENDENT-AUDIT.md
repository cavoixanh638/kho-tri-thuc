# G00 — THẨM ĐỊNH ĐỘC LẬP CÁC BÁO CÁO G01–G17

**Ngày thẩm định:** 20/11/2026 (UTC+07). **Vai trò:** Tổng chỉ huy sau khi các luồng nghiên cứu đã nộp kết quả. **Trạng thái:** DESK_AUDIT_DONE / PRODUCT_UAT_NOT_RUN / NO_MERGE.  
**Nhánh đối chiếu:** main của https://github.com/cavoixanh638/kho-tri-thuc; các báo cáo nằm ở 17 PR #30–#46, chưa tích hợp.  
**Phạm vi chứng nhận:** kiểm tra cấu trúc toàn bộ 17 báo cáo và đối chiếu độc lập **ít nhất một nhận định trọng yếu của mỗi sản phẩm** với nguồn chính thức. Đây **không phải** tuyên bố đã xác thực từng câu, từng link hoặc đã thao tác trong 17 ứng dụng.

## 1. Kiểm tra hồ sơ và ranh giới nguồn

- Đã kiểm 17/17 PR, 17/17 nhánh riêng và 17/17 tệp báo cáo theo đường dẫn reports/Gxx-*.md. Cả 17 PR chỉ thay đổi **một tệp báo cáo đúng luồng**, không sửa ứng dụng hay tài liệu baseline.
- Trong từng báo cáo đã xác nhận có ma trận K01–K12, đánh giá 7 trụ, giới hạn NOT_RUN và đề xuất. Đây là kiểm tra **sự hiện diện**, không chứng minh từng bảng điểm hay citation là đúng.
- G00 mở lại nguồn chính thức/nguồn code công khai độc lập với báo cáo. Ma trận dưới đây ghi rõ phần đã được xác nhận và phần **chưa thể suy ra từ tài liệu**. Nguồn có thể cập nhật; ngày kiểm là 20/11/2026.
- Test trên tài khoản sản phẩm trả phí, thao tác UAT Android/Windows, tải và phát 10.000 video, đồng bộ xung đột/khôi phục dữ liệu **NOT_RUN**. Không dùng dữ liệu cá nhân, OAuth, tài khoản thử hoặc tiện ích cài ngoài.
- Bảng điểm của từng Gxx do tác giả ước lượng theo mô tả sản phẩm, **không phải benchmark thực nghiệm**; các khoảng điểm và điều kiện veto phải giữ nguyên.

## 2. Ma trận xác minh độc lập 17 nguồn quyết định

| Luồng/PR | Kết quả kiểm nguồn | Điều đã xác nhận và giới hạn kết luận | Nguồn chính thức đã mở/đối chiếu |
| --- | --- | --- | --- |
| G01 — [Notion](https://github.com/cavoixanh638/kho-tri-thuc/pull/43) | XÁC NHẬN CÓ GIỚI HẠN | Offline chỉ trong ứng dụng desktop/mobile; trang phải sẵn có để tải offline. Không kết luận browser offline hay sync xung đột đã PASS. | [Nguồn](https://www.notion.com/help/use-pages-offline) |
| G02 — [Google Keep](https://github.com/cavoixanh638/kho-tri-thuc/pull/42) | XÁC NHẬN | Ghi nhãn/màu/pin và tối đa 50 nhãn; không thể làm cây hàng nghìn nhóm trực tiếp bằng labels. | [Nguồn](https://support.google.com/keep/answer/6191044?hl=en) |
| G03 — [Lark](https://github.com/cavoixanh638/kho-tri-thuc/pull/45) | XÁC NHẬN TÍNH NĂNG; CHƯA THỬ CHẤT LƯỢNG | Base hỗ trợ AI import text/ảnh → fields, phân loại và workflow; không suy ra tự tải video hoặc tự gán Topic của dự án. | [Nguồn](https://www.larksuite.com/hc/en-US/articles/708041262345-overview-of-ai-features-in-base) |
| G04 — [Evernote](https://github.com/cavoixanh638/kho-tri-thuc/pull/46) | XÁC NHẬN CÔNG BỐ | FAQ chính thức liệt kê semantic search, OCR và AI Meeting Notes; các gói, độ chính xác tiếng Việt và trạng thái UI thực tế chưa thử. | [Nguồn](https://help.evernote.com/hc/en-us/articles/45353174499475-Evernote-s-AI-Features-FAQ) |
| G05 — [OneNote](https://github.com/cavoixanh638/kho-tri-thuc/pull/40) | XÁC NHẬN THEO PHIÊN BẢN | OneNote Windows có ghi âm/video và ghi chú liên kết thời điểm đang ghi. Không suy tính năng này giống nhau trên Android/web. | [Nguồn](https://support.microsoft.com/en-us/onenote/onenote-help-and-learning/record-audio-or-video-notes) |
| G06 — [Apple Notes](https://github.com/cavoixanh638/kho-tri-thuc/pull/41) | XÁC NHẬN | iOS 26 cho xuất ghi chú ra Markdown, nhập Markdown có tài liệu riêng; không tự suy round-trip hình, bảng và quan hệ là lossless. | [Nguồn](https://support.apple.com/en-mide/guide/iphone/iphdf551cfa2/ios) |
| G07 — [Mem.ai](https://github.com/cavoixanh638/kho-tri-thuc/pull/38) | XÁC NHẬN — ĐIỀU KIỆN LOẠI | Nhà cung cấp thông báo 16/11/2026: read-only 18/12/2026, đóng 15/01/2027. Không mua/tích hợp/lưu nguồn gốc vào Mem. | [Nguồn](https://get.mem.ai/blog/mem-is-shutting-down) |
| G08 — [Coda / Superhuman Docs](https://github.com/cavoixanh638/kho-tri-thuc/pull/36) | XÁC NHẬN; PHÂN BIỆT BETA | Coda đổi tên 08/07/2026; Docs AI vẫn beta, AI Views open beta, database sản phẩm riêng closed beta. Không coi beta như GA. | [Nguồn](https://help.superhuman.com/hc/en-us/articles/46210093285773-What-s-changing-Coda-becomes-Superhuman-Docs) |
| G09 — [Reflect Open](https://github.com/cavoixanh638/kho-tri-thuc/pull/34) | XÁC NHẬN HƯỚNG KIẾN TRÚC; CẦN TÁI KIỂM NỀN TẢNG | Blog 14/07/2026 xác nhận local-first Markdown/MIT, Windows/Android chưa có vào ngày công bố; báo cáo G09 nêu Windows unsigned sau đó, phải kiểm release đúng ngày/phiên bản trước khi dựa vào chi tiết này. | [Nguồn](https://reflect.app/blog/reflect-open) |
| G10 — [Superpowered](https://github.com/cavoixanh638/kho-tri-thuc/pull/39) | XÁC NHẬN — ĐIỀU KIỆN LOẠI TÍCH HỢP | Trang tải chính thức thông báo không còn cho tải, trái với việc trang chủ còn bảng giá/quảng bá; chỉ học mẫu UX họp, không chọn dịch vụ. | [Nguồn](https://superpowered.me/download) |
| G11 — [Gemini Notebook](https://github.com/cavoixanh638/kho-tri-thuc/pull/44) | XÁC NHẬN; PREVIEW | Google đổi tên NotebookLM 16/07/2026; REST API/MCP tồn tại nhưng early access Public Preview và giới hạn tài khoản cá nhân; chưa có full dump/restore. | [Nguồn](https://developers.google.com/notebook/docs) |
| G12 — [AFFiNE](https://github.com/cavoixanh638/kho-tri-thuc/pull/32) | XÁC NHẬN NGUYÊN TẮC; CHƯA THỬ REUSE | Repo chính thức có Page/Edgeless, local-first, self-host; giấy phép/phạm vi từng package phải rà khi chọn thư viện, không suy cả hệ thống an toàn để fork. | [Nguồn](https://github.com/toeverything/AFFiNE) |
| G13 — [Capacities](https://github.com/cavoixanh638/kho-tri-thuc/pull/37) | XÁC NHẬN — PHÂN BIỆT ĐÃ CÓ/BETA/CHƯA CÓ | Media analysis đòi Pro và bật AI, kích hoạt thủ công; ảnh có, phân tích weblink beta theo plan, audio ở mục coming soon; không coi auto-video analysis là đã phát hành. | [Nguồn](https://docs.capacities.io/reference/media-analysis) |
| G14 — [Tana Outliner](https://github.com/cavoixanh638/kho-tri-thuc/pull/33) | XÁC NHẬN ĐỊNH DANH VÀ CHỨC NĂNG | Tana Outliner có supertags, saved views và node; khác tana.inc meeting platform; không coi mô hình node là thay được CaptureEvent/Drive. | [Nguồn](https://outliner.tana.inc/) |
| G15 — [Granola](https://github.com/cavoixanh638/kho-tri-thuc/pull/31) | XÁC NHẬN — RANH GIỚI NGHIỆP VỤ | Có Windows/Android và ghi âm để phiên âm, nhưng không giữ âm thanh gốc; vì vậy không đáp ứng yêu cầu nghe lại chính xác audio gốc. | [Nguồn](https://www.granola.ai/security) |
| G16 — [Heptabase](https://github.com/cavoixanh638/kho-tri-thuc/pull/35) | XÁC NHẬN MỘT PHẦN; CẦN TEST LOCATOR | Changelog/tài liệu xác nhận PDF highlight, ứng dụng Android, CLI và nguồn media; chưa tự kiểm chứng end-to-end link ghi chú→mốc YouTube hay MP4 người dùng. | [Nguồn](https://wiki.heptabase.com/changelog) |
| G17 — [Obsidian](https://github.com/cavoixanh638/kho-tri-thuc/pull/30) | XÁC NHẬN TÍNH NĂNG; KHÔNG PHẢI BACKEND VIDEO | Tài liệu chính thức xác nhận Bases/backlinks, note Markdown và chế độ edit/read; không chứng minh thay thế job tải video, Drive hay sự kiện tiếp nhận. | [Nguồn](https://obsidian.md/help/Plugins/Core%2Bplugins) |

**Nguồn bổ sung để làm rõ mốc thời gian và phạm vi:**
- G06: [Apple hướng dẫn nhập Markdown trên iOS/macOS 26](https://support.apple.com/en-sg/102223).
- G08: [Docs AI vẫn ở beta](https://help.superhuman.com/hc/en-us/articles/46210156957197-Use-Docs-AI-in-Superhuman-Docs).
- G09: [Mã nguồn MIT của Reflect Open](https://github.com/team-reflect/reflect-open), đọc riêng với blog ngày phát hành.
- G11: [Google xác nhận đổi tên ngày 16/07/2026](https://blog.google/innovation-and-ai/products/gemini-notebook/notebooklm-gemini-notebook/), [API roadmap](https://developers.google.com/notebook/docs/roadmap) và [MCP mới](https://developers.google.com/notebook/docs/mcp).
- G15: [Granola mô tả capture tại máy nhưng transcribe trên cloud và không lưu audio](https://www.granola.ai/blog/local-first-ai-notetaker-vs-cloud).
- G16: [Heptabase hướng dẫn đọc PDF và media](https://wiki.heptabase.com/pdf-annotation).
- G17: [Obsidian Bases](https://obsidian.md/help/bases/syntax), [đọc/chỉnh sửa Markdown](https://obsidian.md/help/edit-and-read).

## 3. Phát hiện phải tác động đến quyết định (không bỏ qua)

1. **Veto vận hành:** G07 Mem đóng ngày 15/01/2027; G10 Superpowered không còn cho tải mới. Không đề xuất sử dụng làm dịch vụ nguồn gốc hay tích hợp, bất kể bảng điểm lịch sử.
2. **Phải phân biệt công bố và GA:** G08 Docs AI / AI Views / databases chưa ở cùng mức phát hành; G11 API/MCP Public Preview; G13 media analysis AI có yêu cầu plan và không hỗ trợ audio analysis như tính năng GA.
3. **Không đánh đồng bản chép lời với audio/video thật:** G15 Granola không lưu audio gốc; G11 nhập YouTube URL không chứng minh phân tích từng khung hình; G16 dẫn PDF/YouTube công bố không chứng minh phát MP4 từ Google Drive và seek chính xác cho từng điểm trên dự án.
4. **Không mặc định tương thích nền tảng:** G05 Windows audio-linked note không tự áp cho Android/web; G09 trang phát hành tháng 7 nói Windows/Android không có, trong khi báo cáo có nhận định mới về Windows unsigned — cần xác minh release pin nếu dùng tính năng Windows trong quyết định. G01 offline page chỉ trong ứng dụng và điều kiện tải trước.
5. **Không suy đoán quyền license qua nhãn “open source”:** AFFiNE/BlockSuite cần kiểm từng package, code editor nhúng, phụ thuộc và nghĩa vụ giấy phép trước khi lấy mã.
6. **Điểm không thắng điều kiện bắt buộc:** một sản phẩm có điểm cao vẫn bị loại khỏi phương án thay toàn bộ khi thiếu CaptureEvent theo lần gửi, Drive file gốc, đối soát SHA, multi-parent taxonomy, recovery hoặc API kiểm chứng.

## 4. Mã Kho Tri Thức hiện có: không đề nghị làm lại tính năng đã có

- [CURRENT_STATE.md](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/CURRENT_STATE.md): Windows live nghiệm thu trong phạm vi công bố; Android vẫn NOT_RUN; không biến số liệu của pilot thành bảo đảm 10.000 video.
- [CaptureService](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/ingestion/services.py): biên nhận sau giao dịch, nguồn và lịch sử, idempotency.
- [OrganizationService](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/catalog/organization.py): nhóm hiện có và quan hệ có lý do; cần cải thiện UX, không lập taxonomy thứ hai.
- [ReadKnowledgeService](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/processing/read_knowledge.py): ưu tiên note do người dùng viết, giữ nguồn trích riêng.
- [ItemScreen](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/web/src/ItemScreen.tsx): hiện editor kiểu Textarea (chưa là Live Preview giàu tính năng).
- [KnowledgeText](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/web/src/KnowledgeText.tsx): đã có React Markdown/GFM renderer nhưng chưa đồng nghĩa tương tác editor.
- [KnowledgeTree](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/web/src/KnowledgeTree.tsx): có cây nhiều cấp và liên kết một bài vào nhiều nhánh.

## 5. Phạm vi của kết luận G00 và chứng cứ cần có khi triển khai

**Đã hoàn thành:** rà 17 hồ sơ/PR và xác nhận lại từng nhận định chủ đạo liên quan **đến quyết định kiến trúc** từ nguồn chính thức, ghi giới hạn/ngoại lệ.  
**Không tuyên bố đã hoàn thành:** xác thực tất cả nhiều trăm URL, UI trả phí, thử tốc độ/độ chính xác, test Android thật và corpus trên 10.000 mục. Những phần này là **cổng UAT/benchmark của từng PoC**, không phải lý do giữ trống quyết định G00.

**Cách sử dụng:** xem tài liệu G00-CROSS-APP-DECISION.md cùng thư mục để biết ma trận so sánh, danh mục tính năng được ưu tiên/hoãn và tiêu chí nghiệm thu. Không hợp thức hóa tính năng beta, không dùng score đơn độc để tự merge hoặc thay kiến trúc. Báo cáo gốc G01–G17 được giữ nguyên.
