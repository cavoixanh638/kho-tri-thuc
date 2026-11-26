# Kế hoạch chức năng chi tiết — Kho Tri Thức

Ngày 25/11/2026. **Nguồn chuẩn theo dõi ưu điểm của 17 nghiên cứu**, bổ sung [ROADMAP_AND_TESTS](ROADMAP_AND_TESTS.md); không thay [CURRENT_STATE](CURRENT_STATE.md). Yêu cầu người dùng: giữ từng chức năng và ánh xạ nguyên bản, triển khai và cập nhật thường xuyên. Baseline RC [#100](https://github.com/cavoixanh638/kho-tri-thuc/pull/100) d1e47e8 + [#101](https://github.com/cavoixanh638/kho-tri-thuc/pull/101) a820a6decad67dc4c5381ccc79d9184b255c0f3a (chưa merge, hai test frontend lỗi). Nhánh `coord/feature-catalog-20261125` tách từ #101.

## Quy tắc không bỏ sót

- Mỗi ID là **một chức năng độc lập**. Các nhóm chỉ để phân công, không được xóa dòng hoặc đánh dấu toàn nhóm DONE. Một code change có thể phục vụ nhiều ID nhưng nghiệm thu riêng từng ID. Gxx.n là thứ tự đề xuất trong báo cáo gốc; Gxx+ là ưu điểm mô tả sản phẩm hoặc rà soát bổ sung, đặc biệt G17+ là yêu cầu workspace Obsidian. Không giả định chúng đều được đề xuất trong báo cáo gốc.
- CÓ MÃ không đồng nghĩa UAT hoặc deploy; MỘT PHẦN là code/quality/gate thiếu; THIẾU là chưa tìm thấy ở baseline; HOÃN có điều kiện, phải giữ lý do. Các trạng thái là kiểm kê tĩnh, không phải kết quả test mới.
- Mỗi PR/checkpoint cập nhật dòng ID và nhật ký bên dưới: Code SHA, Tested SHA, PASS/FAIL/NOT_RUN, số ca + link evidence, Windows DEPLOYED/NOT_DEPLOYED, giới hạn, rollback, NEXT. G00 cập nhật CURRENT_STATE sau review/merge. Không xóa đề xuất vì trùng hoặc hoãn; không chỉ báo trong chat.
- Giữ React/Django/PostgreSQL/Drive, raw Markdown, UUID, CaptureEvent, source version, owner, consent. Không tự bật AI ngoài/chi phí, merge/deploy, đổi storage, chạy migration thật hoặc tự mở nhiều chat. Android hoãn theo chỉ đạo hiện tại. So sánh 2–3 phương án trước chọn editor/schema/provider mới; test độc lập. Nhóm P0 bảo vệ RC/an toàn trước mở rộng P1, P2.

Chạy `node tools/smoke/feature_catalog_contract.mjs` trước mỗi PR. Cổng offline trong smoke workflow kiểm tra các ID tối thiểu đã chốt, đề xuất gốc 94/94, đúng PR nguồn, ánh xạ hai chiều và tổng số theo trạng thái; cho phép mở rộng nhưng không được bỏ ID. Không tốn dịch vụ ngoài, không thêm workflow/job.

## Danh mục

### WS — Workspace Obsidian (P0)

Điểm sở hữu/đối chiếu: KnowledgeWorkspace.tsx / App.tsx / KnowledgeExplorer.css. Frontend tại apps/web/src, backend tại apps/backend. Tiêu chí là mục tiêu, không phải PASS.

| ID | Trạng thái | Chức năng | Nguồn | Tiêu chí / giới hạn |
| --- | --- | --- | --- | --- |
| WS-01 | MỘT PHẦN | Sidebar cố định, cuộn độc lập và giữ DOM khi mở bài | G17+ | Chuyển route giữ sidebar, scroll, nhánh; #101 còn 2 test lỗi |
| WS-02 | CÓ MÃ | Kéo đường biên để resize, lưu chiều rộng, hỗ trợ bàn phím | G17+ | 240–480px, reload, 390px không tràn |
| WS-03 | CÓ MÃ | Mở nhiều tab, đóng và mở lại tab | G17+ G14+ | Cùng UUID, không mất draft |
| WS-04 | MỘT PHẦN | Ghim, sắp xếp tab, mở bài trong tab mới | G17+ | Không mất editor state |
| WS-05 | THIẾU | Chia pane ngang/dọc, mở nguồn cạnh bài | G05.5 G17+ | Hai pane độc lập, mobile fallback |
| WS-06 | MỘT PHẦN | Khôi phục phiên làm việc, bố cục, tab | G17+ | Tách tài khoản, không lưu raw ngoài DB |
| WS-07 | MỘT PHẦN | Back/forward và lịch sử vị trí đọc | G17+ | Quay lại đúng vị trí |
| WS-08 | THIẾU | Preview bài khi hover/tap, mở không mất trang | G05.5 G17+ | Owner scope, Escape trả focus |
| WS-09 | THIẾU | Panel mục lục phải và liên quan bật/tắt được | G07.1 G14.3 G16.2 G17+ | Không che editor, lưu layout |
| WS-10 | MỘT PHẦN | Responsive, keyboard, reduced-motion | G17+ | 390/768/1440/1920px, IME |

### TREE — Cây thư mục và note (P0)

Điểm sở hữu/đối chiếu: KnowledgeExplorer.tsx / ItemStructurePanel.tsx / catalog/explorer.py. Frontend tại apps/web/src, backend tại apps/backend. Tiêu chí là mục tiêu, không phải PASS.

| ID | Trạng thái | Chức năng | Nguồn | Tiêu chí / giới hạn |
| --- | --- | --- | --- | --- |
| TREE-01 | CÓ MÃ | Folder và note xen kẽ, lazy load | G05.5 G12.3 G17+ | Một UUID, phân trang |
| TREE-02 | CÓ MÃ | Tạo note tại folder, thêm thư mục con | G05.5 G17+ | ACK/retry không nhân Event |
| TREE-03 | CÓ MÃ | Kéo thả, đổi tên, move folder, Ctrl-drop shortcut | G01+ G03+ G17+ | Chặn cycle, owner, version |
| TREE-04 | CÓ MÃ | Bài cha–con, đổi cha, sắp thứ tự | G05+ G14+ G17+ | Không dùng related giả parent |
| TREE-05 | MỘT PHẦN | Animation, chevron/icon, đường cấp, cache | G17+ | 180ms, reduced motion, không giật |
| TREE-06 | MỘT PHẦN | Mở tổ tiên, active note, tự cuộn tới bài | G17+ | Deep link 5 tầng |
| TREE-07 | CÓ MÃ | Thu gọn tất cả và mở lại nhánh | G17+ | Không remount root, keyboard |
| TREE-08 | CÓ MÃ | Giữ root khi lọc unfiled, cô lập lỗi API sidebar | G17+ | Không sập capture/login; test malformed response |
| TREE-09 | CÓ MÃ | Tìm nhanh folder/note trong cây | G17+ | 10k không tải hết note |
| TREE-10 | MỘT PHẦN | Outliner indent/outdent, move bằng phím, zoom node | G14+ | Undo, không sửa raw |
| TREE-11 | MỘT PHẦN | Reference/node tái sử dụng nhiều vị trí | G14+ G16+ | Shortcut có; block ref còn thiếu |

### EDIT — Soạn thảo (P1)

Điểm sở hữu/đối chiếu: MarkdownEditor.tsx / MarkdownEditorDraft.tsx / KnowledgeText.tsx / NoteOutline.ts. Frontend tại apps/web/src, backend tại apps/backend. Tiêu chí là mục tiêu, không phải PASS.

| ID | Trạng thái | Chức năng | Nguồn | Tiêu chí / giới hạn |
| --- | --- | --- | --- | --- |
| EDIT-01 | CÓ MÃ | Source Markdown, Reading Mode, GFM | G17.1 G01.5 G09+ | Roundtrip Unicode, bảng, link |
| EDIT-02 | MỘT PHẦN | Split Edit/Preview đồng bộ | G17.1 G01.5 | Giữ scroll/con trỏ |
| EDIT-03 | THIẾU | Inline Live Preview tại con trỏ | G17.1 G01.5 G12.4 | So 2–3 editor; 50 note lossless, IME, undo, 100k ký tự |
| EDIT-04 | THIẾU | Toolbar định dạng, menu / và shortcut | G01.5 G17.1 G12.4 | Selection, undo chính xác |
| EDIT-05 | THIẾU | Block kéo, nhân bản, xóa, đổi loại | G01.5 G12.4 G14+ | Không mất raw/anchor |
| EDIT-06 | MỘT PHẦN | Chỉnh bảng trực tiếp, thêm/xóa hàng/cột | G01.5 G12.4 | GFM roundtrip |
| EDIT-07 | MỘT PHẦN | Ảnh inline, kéo thả ảnh/media vào bài | G05.5 G12.4 | Asset verified, giữ vị trí |
| EDIT-08 | THIẾU | Callout, toggle block, divider, checklist tương tác | G01+ G06+ G02+ | Không phá raw, version |
| EDIT-09 | CÓ MÃ | Mục lục heading và anchor | G06.3 G17+ | Heading trùng tên ổn định |
| EDIT-10 | CÓ MÃ | Thu gọn heading và nội dung con | G06.3 G17+ | Không sửa raw; nhớ state |
| EDIT-11 | THIẾU | Block/section link, copy permalink đoạn | G01+ G06.4 G16+ | Rename, stale rõ |
| EDIT-12 | MỘT PHẦN | Autosave draft, cảnh báo rời bài, undo/redo | G01.5 G17.1 | Reload/concurrent edit/IME |
| EDIT-13 | THIẾU | Lịch sử version, so sánh và restore bản cũ | G04+ G09+ G15.1 | Restore tạo version mới |
| EDIT-14 | HOÃN CÓ ĐIỀU KIỆN | Viết tay, vẽ tự do | G05+ G12+ | Chỉ khi có nhu cầu bút |
| EDIT-15 | THIẾU | Preview link và chọn link ngay trong editor | G17+ G09.2 | UUID không phụ thuộc title |

### TYPE — Loại bài và thuộc tính (P1)

Điểm sở hữu/đối chiếu: PropertyChips.tsx / NoteTemplateConfig.ts / NoteTemplatePicker.tsx; ADR schema. Frontend tại apps/web/src, backend tại apps/backend. Tiêu chí là mục tiêu, không phải PASS.

| ID | Trạng thái | Chức năng | Nguồn | Tiêu chí / giới hạn |
| --- | --- | --- | --- | --- |
| TYPE-01 | CÓ MÃ | Chips loại, ngày nhận/đăng, trạng thái, nhóm | G01.2 G13.2 | Đúng DTO |
| TYPE-02 | CÓ MÃ | Template Bài học/Sách/Họp/Video | G10.1 G15.3 G13.2 G14.1 | Không ghi đè |
| TYPE-03 | THIẾU | Tự tạo/sửa/xóa template | G01+ G10.1 G14.1 | Version, xóa không xóa note |
| TYPE-04 | THIẾU | Custom object type/Supertag | G13.2 G14.1 | Gắn/bỏ type không đổi UUID |
| TYPE-05 | THIẾU | Field text/number/date/checkbox/select/multiselect | G01.2 G13.2 G14.1 | Validation/null/date/roundtrip |
| TYPE-06 | THIẾU | Relation field một/nhiều bài, inverse | G01.2 G08.2 G14.1 | Owner, rename giữ ID |
| TYPE-07 | THIẾU | Tác giả/ngày nguồn/trạng thái/URL typed | G03.1 G13.2 G08.5 | Nguồn tách user |
| TYPE-08 | THIẾU | Field mặc định/bắt buộc/tùy chọn theo loại | G08.5 G14.1 G13.2 | Ghi nhanh vẫn ACK |
| TYPE-09 | THIẾU | Form nhập theo type/preset | G08.5 G03.1 | Bỏ form vẫn lưu |
| TYPE-10 | THIẾU | Filter/sort/group theo custom field | G01.2 G14.1 G16.3 | 10k, NULL đúng |
| TYPE-11 | HOÃN CÓ ĐIỀU KIỆN | Formula/lookup/rollup | G01+ G08+ | Khi có hồ sơ cần, không code tùy ý |
| TYPE-12 | HOÃN CÓ ĐIỀU KIỆN | Lệnh riêng theo type | G14+ | Whitelist action |

### VIEW — Góc nhìn dữ liệu (P1)

Điểm sở hữu/đối chiếu: LibraryViews.tsx / SavedCollections.tsx / collection_service.py. Frontend tại apps/web/src, backend tại apps/backend. Tiêu chí là mục tiêu, không phải PASS.

| ID | Trạng thái | Chức năng | Nguồn | Tiêu chí / giới hạn |
| --- | --- | --- | --- | --- |
| VIEW-01 | CÓ MÃ | List/Table/Card/Timeline cùng UUID/filter | G01.1 G03.3 G08.1 G12.3 G14.4 G16.3 G17.3 | 4 view cùng tập ID, 10k |
| VIEW-02 | CÓ MÃ | Saved Collection động any/all/exclude | G01.1 G04.5 G06.2 G14.2 G17.3 | Xóa filter không xóa bài |
| VIEW-03 | CÓ MÃ | Lưu view, sort và khoảng ngày | G01.1 G06.2 G08.1 G17.3 | Reload, filter tự cập nhật |
| VIEW-04 | THIẾU | Đổi tên/ẩn/hiện/reorder/resize cột, lưu view | G01+ G08+ G17+ | Nhiều layout cùng data, per owner |
| VIEW-05 | THIẾU | Chỉnh trực tiếp ô field/tag/group | G01.2 G08.1 G16.3 | Version conflict, mọi view cập nhật |
| VIEW-06 | THIẾU | Group-by loại/chủ đề/trạng thái/field | G01.1 G14.4 G17.3 | Distinct UUID |
| VIEW-07 | THIẾU | Kanban, kéo cập nhật thuộc tính có duyệt | G01+ G08+ G12+ G17.3 | Không mất group |
| VIEW-08 | THIẾU | Calendar theo ngày nhận/đăng/field | G01+ G08+ G14.4 G13+ | Timezone, ngày thiếu |
| VIEW-09 | HOÃN CÓ ĐIỀU KIỆN | Dashboard/biểu đồ/Pivot/map | G08+ G14+ G17+ | Ca dùng và aggregate đúng |
| VIEW-10 | HOÃN CÓ ĐIỀU KIỆN | Nhúng saved query sống trong note | G14+ G17+ | Read-only references, bounded |
| VIEW-11 | CÓ MÃ | Nút gắn nguồn/mở nguồn/nhóm/xử lý lại | G08.3 | Idempotent retry |
| VIEW-12 | HOÃN CÓ ĐIỀU KIỆN | Nút hành động tùy chỉnh, workflow điều kiện | G08+ G03+ | Whitelist, audit |
| VIEW-13 | MỘT PHẦN | Tag browser, nested tags/màu, đường dẫn nhóm | G04.4 G06+ G16+ | Cây Topic khác tag; không nhân bản; lọc ≤3 thao tác |

### LINK — Liên kết và liên quan (P1)

Điểm sở hữu/đối chiếu: RelatedSources.tsx / NoteLinkContext.tsx / navigation_api.py. Frontend tại apps/web/src, backend tại apps/backend. Tiêu chí là mục tiêu, không phải PASS.

| ID | Trạng thái | Chức năng | Nguồn | Tiêu chí / giới hạn |
| --- | --- | --- | --- | --- |
| LINK-01 | CÓ MÃ | Wiki autocomplete UUID ổn định | G09.2 G06.4 G03.4 G17.2 | Rename/trùng tên |
| LINK-02 | CÓ MÃ | Outgoing links/backlinks chủ ý | G01.3 G03.4 G06.4 G09.2 G12.2 G17.2 | Gỡ link mất backlink |
| LINK-03 | CÓ MÃ | Unlinked mentions tách link thật | G17.2 | Không tự tạo quan hệ |
| LINK-04 | CÓ MÃ | Related/cùng nhóm, reason và version | G01.3 G07.1 G08.2 G12.2 G13.1 G14.3 G16.2 G17.2 | Owner; reason thật |
| LINK-05 | MỘT PHẦN | Context excerpt, mở đúng đoạn backlink | G13.1 G14.3 G16.2 | Excerpt/anchor/version |
| LINK-06 | THIẾU | Dismiss/giữ gợi ý sai bền vững, undo | G08.2 G13.1 G14.3 G16.2 | 5/5 không tái xuất cùng version |
| LINK-07 | MỘT PHẦN | Heads Up khi đọc và soạn theo ngữ cảnh | G07.1 G14.3 G16.2 | Không cản editor |
| LINK-08 | THIẾU | Gợi ý collection và timeline liên quan | G07.1 G07.2 | Không chế event |
| LINK-09 | THIẾU | Semantic related, trùng/mâu thuẫn có chứng cứ | G07+ G13+ G17.2 | Gold Việt, không merge |
| LINK-10 | HOÃN CÓ ĐIỀU KIỆN | Graph contextual/toàn kho, edge phân loại | G07+ G12+ G13+ G16+ G17+ | 1k nodes, không graph DB |

### NAV — Điều hướng và thời gian (P1)

Điểm sở hữu/đối chiếu: KnowledgeCommandPalette.tsx / HistoryScreen.tsx. Frontend tại apps/web/src, backend tại apps/backend. Tiêu chí là mục tiêu, không phải PASS.

| ID | Trạng thái | Chức năng | Nguồn | Tiêu chí / giới hạn |
| --- | --- | --- | --- | --- |
| NAV-01 | CÓ MÃ | Ctrl+K tìm bài/thư mục | G09.4 G17+ | 10k, keyboard/IME |
| NAV-02 | MỘT PHẦN | Palette tạo/gắn nguồn/chuyển nhánh/mở ngày | G09.4 | Mở rộng action registry |
| NAV-03 | CÓ MÃ | Timeline nhận lần đầu, lịch sử từng lần gửi | G07.2 G09.1 G01.1 | Giờ bất biến, retry |
| NAV-04 | MỘT PHẦN | Lọc ngày nhận và ngày nguồn | G07.2 G09.1 G06.2 | Timezone, nguồn thiếu ngày |
| NAV-05 | THIẾU | Daily Notes riêng mỗi ngày | G09.1 G02+ G13+ | Không tự tạo DB song song |
| NAV-06 | THIẾU | Recent, pin bài, giữ vị trí đọc | G02.2 G06+ G17+ | Pin khác favorite |

### CAP — Quick Capture và Inbox (P1)

Điểm sở hữu/đối chiếu: CaptureScreen.tsx / sharedCapture.ts / inboxInput.ts / ingestion. Frontend tại apps/web/src, backend tại apps/backend. Tiêu chí là mục tiêu, không phải PASS.

| ID | Trạng thái | Chức năng | Nguồn | Tiêu chí / giới hạn |
| --- | --- | --- | --- | --- |
| CAP-01 | CÓ MÃ | Ô gửi text/link/file, receipt nhanh | G01.4 G02.1 G06.1 G09.1 G16.4 | ACK sau commit, idempotency |
| CAP-02 | CÓ MÃ | Paste/drag-drop, lưu draft | G02.1 G06.1 G08.5 | Mất mạng giữ nháp |
| CAP-03 | MỘT PHẦN | Android share, shortcut/widget | G02.3 G06.1 G13.5 | 30 lượt máy thật; hoãn Android |
| CAP-04 | MỘT PHẦN | Link preview, metadata, trạng thái | G01.4 G02.3 G17.4 | Không suy hiểu video |
| CAP-05 | MỘT PHẦN | Gửi vào bài/nhóm đã có | G07.3 G13.5 | 10 lượt không nhân asset |
| CAP-06 | MỘT PHẦN | Chưa phân loại và review từng bài | G16.4 G02.2 | Luồng xử lý gọn |
| CAP-07 | THIẾU | Inbox triage hàng loạt, đánh dấu đã xử lý | G16.4 G02.2 | Undo, giữ lịch sử |
| CAP-08 | MỘT PHẦN | Favorite, pin và màu card | G02.2 G06+ | Pin khác favorite, contrast |
| CAP-09 | THIẾU | Checklist nhanh, reorder card | G02+ | Lưu version, keyboard |
| CAP-10 | THIẾU | Camera scan nhiều trang, crop/rotate PDF | G06.6 | Giữ ảnh gốc, permission |
| CAP-11 | MỘT PHẦN | OCR ảnh theo yêu cầu, tìm chữ ảnh/scan | G02.4 G06.6 | Có code Gemini pilot; 30 ảnh gold CER/WER, consent |
| CAP-12 | THIẾU | Voice inbox, chuyển lời thành note | G02.5 G06+ G13+ | ASR Việt, audio source |
| CAP-13 | THIẾU | Tách nhiều ý nói thành nhiều đề xuất | G02.5 | 10 sample, duyệt |
| CAP-14 | HOÃN CÓ ĐIỀU KIỆN | Reminders theo giờ/lặp | G02.6 G13+ | Timezone; không location |

### CLIP — Clipper và trích dẫn (P1)

Điểm sở hữu/đối chiếu: ResearchClipper.tsx / processing/clips.py / clip_api.py. Frontend tại apps/web/src, backend tại apps/backend. Tiêu chí là mục tiêu, không phải PASS.

| ID | Trạng thái | Chức năng | Nguồn | Tiêu chí / giới hạn |
| --- | --- | --- | --- | --- |
| CLIP-01 | CÓ MÃ | Bookmark, article, selection và preview | G04.1 G05.3 G17.4 | URL/quote/version/receipt |
| CLIP-02 | MỘT PHẦN | Simplified article, bỏ quảng cáo/ảnh đại diện | G04.1 G17.4 | 20 trang public, lỗi rõ |
| CLIP-03 | THIẾU | Full page/screenshot/vùng ảnh | G04.1 G05.3 | Chỉ user chọn |
| CLIP-04 | THIẾU | Browser extension/menu chuột phải đoạn chọn | G04.1 G17.4 | So extension/bookmarklet/PWA, scope tối thiểu |
| CLIP-05 | MỘT PHẦN | Chọn bài/nhóm nhận, comment/tag khi clip | G07.3 G04.1 G17.4 | 1–2 thao tác |
| CLIP-06 | THIẾU | Template clip, metadata tác giả/ngày/ảnh | G17.4 G03.1 | Preview, thiếu để trống |
| CLIP-07 | CÓ MÃ | Lưu quote/hash/version, stale | G13.3 G04.1 G17.4 | Không đổi raw |
| CLIP-08 | MỘT PHẦN | Reader web, highlight và quay lại đúng đoạn | G13.3 G16.1 | 20 trang/5 blocked |
| CLIP-09 | MỘT PHẦN | Clip đoạn PDF/transcript vào bài có sẵn | G07.3 G13.4 G16.1 | Thao tác trực quan |
| CLIP-10 | THIẾU | Smart filing trong preview clip | G04.1 G03.2 | Không tạo taxonomy bừa |

### SOURCE — Đọc và khai thác nguồn (P0/P1)

Điểm sở hữu/đối chiếu: SourceLocator.tsx / KnowledgeReading.tsx / viewer_api.py / SourceCitationBridge.tsx. Frontend tại apps/web/src, backend tại apps/backend. Tiêu chí là mục tiêu, không phải PASS.

| ID | Trạng thái | Chức năng | Nguồn | Tiêu chí / giới hạn |
| --- | --- | --- | --- | --- |
| SOURCE-01 | CÓ MÃ | Source cards, file, processor/version, trạng thái trích | G03.5 G09.3 G11.3 G12.1 | Không nói đã hiểu nếu thiếu text |
| SOURCE-02 | MỘT PHẦN | PDF đúng trang, SHA/version | G04.2 G05.1 G06.5 G07.6 G11.1 G13.4 G16.1 | 6 trang đã thử; >24 MiB chưa; 20 PDF/50 locators |
| SOURCE-03 | MỘT PHẦN | Seek video/audio đúng mốc | G04.2 G05.1 G06.5 G07.6 G11.1 G16.1 | 2 mốc MP4 đã thử; 20 mốc ≥95% ±1s |
| SOURCE-04 | MỘT PHẦN | Transcript segment/time, click-to-seek | G03.6 G06.5 G15.2 | Thiếu mốc/speaker rõ |
| SOURCE-05 | THIẾU | Transcript highlight đồng bộ playback | G03.6 G05.1 | Tua/pause/scroll đúng |
| SOURCE-06 | THIẾU | Search hit mở thẳng trang/mốc/đoạn | G04.2 G11.1 G16.1 | Không giả seek |
| SOURCE-07 | THIẾU | PDF bôi chữ, rectangle/vùng hình, màu | G13.4 G16.1 G04+ | 50 highlight page+rect+hash |
| SOURCE-08 | THIẾU | Highlight card độc lập, ghi chú lề, kéo vào note | G16.1 G05.5 | Xóa card không xóa nguồn |
| SOURCE-09 | THIẾU | TimedAnnotation ghi chú tại thời điểm phát | G05.1 G10.3 G16.1 | 20 mốc, version, reload/restore |
| SOURCE-10 | THIẾU | Reader/editor cạnh nhau, giữ focus/scroll | G05.5 G16.2 G12.1 | 8 bài, 2 click |
| SOURCE-11 | MỘT PHẦN | PDF/web extraction, ASR/captions có sẵn | G06.5 G11.3 G16+ | Quality/codec thực |
| SOURCE-12 | HOÃN CÓ ĐIỀU KIỆN | Speaker diarization và đổi nhãn người nói | G04+ G15.2 | Gold có quyền |
| SOURCE-13 | HOÃN CÓ ĐIỀU KIỆN | Podcast/caption YouTube thành source cards | G16+ G11+ | Nguồn được phép, thiếu captions rõ |
| SOURCE-14 | MỘT PHẦN | Phân tích ảnh/PDF/media theo yêu cầu | G13+ G11.3 | OCR pilot, không tự bật phí |

### SEARCH — Tìm kiếm (P0/P1)

Điểm sở hữu/đối chiếu: SearchScreen.tsx / search/services.py / search/recall.py. Frontend tại apps/web/src, backend tại apps/backend. Tiêu chí là mục tiêu, không phải PASS.

| ID | Trạng thái | Chức năng | Nguồn | Tiêu chí / giới hạn |
| --- | --- | --- | --- | --- |
| SEARCH-01 | CÓ MÃ | FTS dấu/không dấu, note và derived | G04.5 G07+ G17+ | 86 query PostgreSQL |
| SEARCH-02 | CÓ MÃ | Filter topic/project/tag, saved search | G04.5 G06.2 G14.2 | Owner scope |
| SEARCH-03 | MỘT PHẦN | Fuzzy/tìm theo trí nhớ | G04.6 G07+ | 1/36 đầu, 34/36 mở rộng; 10/15 câu âm có gợi ý sai |
| SEARCH-04 | CÓ MÃ | Highlight hit đúng fragment | G04.5 G04.2 | XSS safe |
| SEARCH-05 | THIẾU | Hybrid semantic và nhận biết không có đáp án | G04.6 G07+ G11+ | Gold ≥50 query, recall@5 +10 điểm %, false-related ≤+5 điểm; không tự bật provider |
| SEARCH-06 | MỘT PHẦN | Modal search, facets, keyboard | G04.5 G09.4 | Palette có, evidence chưa |
| SEARCH-07 | THIẾU | Tìm OCR/transcript và mở locator từ hit | G02.4 G04.2 G06.6 | Thiếu locator fallback |
| SEARCH-08 | THIẾU | Eval người dùng thực được phép | G04.6 G17+ | Đo thời gian/mở đúng/false positive |

### ORG — Tự phân loại và field (P0/P1)

Điểm sở hữu/đối chiếu: OrganizationReview.tsx / organization.py / organization_review.py. Frontend tại apps/web/src, backend tại apps/backend. Tiêu chí là mục tiêu, không phải PASS.

| ID | Trạng thái | Chức năng | Nguồn | Tiêu chí / giới hạn |
| --- | --- | --- | --- | --- |
| ORG-01 | MỘT PHẦN | Auto-group dùng taxonomy hiện có | G03.2 G11.4 G08.4 | 19/22 đúng, 19/32 đủ; cải thiện |
| ORG-02 | CÓ MÃ | Review bằng chứng accept/reject/pin/undo | G03.2 G05.2 G11.4 G08.4 | Curated/exclusion bền |
| ORG-03 | THIẾU | Review queue và duyệt hàng loạt | G05.2 G16.4 G08.4 | Owner, version, undo |
| ORG-04 | THIẾU | Paste-to-fields text/ảnh có preview | G03.1 G14.5 G08.5 | 30 input, ≥27 đúng type |
| ORG-05 | THIẾU | AI autofill từng field, duyệt/sửa/bỏ | G03.1 G14.5 G08.4 | Evidence/consent, 0 overwrite |
| ORG-06 | THIẾU | Gợi ý relation/tag theo ngữ cảnh | G03.2 G08.2 G13.1 G14.5 | Không tạo taxonomy bừa |
| ORG-07 | MỘT PHẦN | Workflow theo sự kiện gửi/trích, retry | G03+ G08.3 | Job idempotent |
| ORG-08 | THIẾU | Gold label độc lập và đo công sửa | G03.2 G11.4 G08.4 | Precision auto ≥90%, không mất pinned |

### AI — AI và nghiên cứu đa nguồn (P2)

Điểm sở hữu/đối chiếu: ItemSuggestionPanel.tsx / suggestions.py / ReadKnowledgeService; provider OFF mặc định. Frontend tại apps/web/src, backend tại apps/backend. Tiêu chí là mục tiêu, không phải PASS.

| ID | Trạng thái | Chức năng | Nguồn | Tiêu chí / giới hạn |
| --- | --- | --- | --- | --- |
| AI-01 | CÓ MÃ | Diff thủ công, accept/reject/undo | G01.6 G04.3 G07.4 G09.6 G15.1 G16.5 | manual_review_poc, không AI |
| AI-02 | THIẾU | AI viết/chỉnh/tóm tắt draft riêng | G01.6 G04.3 G07.4 G15.1 G16.5 | Opt-in, model/cost/version, fail closed |
| AI-03 | THIẾU | Duyệt patch từng phần, regenerate/refine | G04.3 G07.4 G15.1 | 20 note, reject giữ raw |
| AI-04 | THIẾU | Source-set read-only, notebook nghiên cứu | G05.4 G11.2 | 5–20 UUID, quyền/version |
| AI-05 | THIẾU | Chatbot một bài/tập nguồn/toàn kho | G05.4 G11.2 G07+ | 9 câu x 3 mode, không nguồn ngoài |
| AI-06 | THIẾU | Cite-chip claim→span/page/time | G11.1 G15.5 G16.5 | 30 claims, stale, thiếu bằng chứng nói rõ |
| AI-07 | THIẾU | FAQ, briefing, tóm tắt/so sánh đa nguồn | G11.5 G15.1 | Artifact riêng, export Markdown |
| AI-08 | THIẾU | Mâu thuẫn/trùng ý/mức chắc chắn | G07+ G11+ | Hai chiều evidence, không merge |
| AI-09 | THIẾU | AI insights từ nguồn, thêm note qua review | G16.5 G15.5 | 30 prompt gồm 10 âm, không citation giả |
| AI-10 | THIẾU | Trích đầu việc/người/hạn/quyết định | G10.2 G15.3 | 30 đoạn, precision ≥90%, không invent |
| AI-11 | HOÃN CÓ ĐIỀU KIỆN | Quiz/flashcard/mindmap/audio overview/học tương tác | G11+ | Nhu cầu, citation |
| AI-12 | MỘT PHẦN | Opt-in theo bài/nguồn, privacy, cost/quota | G09.6 G01.6 G14.5 G16.5 | OCR consent có; 30 private fail closed |
| AI-13 | HOÃN CÓ ĐIỀU KIỆN | NotebookLM adapter qua API/MCP | G11.2 G11.5 | Chỉ khi Drive/export pilot không đủ |

### MEET — Khai thác nội dung họp (P2)

Điểm sở hữu/đối chiếu: DerivedContent / NoteTemplateConfig / adapter Mốc Họp; không recorder trùng. Frontend tại apps/web/src, backend tại apps/backend. Tiêu chí là mục tiêu, không phải PASS.

| ID | Trạng thái | Chức năng | Nguồn | Tiêu chí / giới hạn |
| --- | --- | --- | --- | --- |
| MEET-01 | MỘT PHẦN | Mẫu họp/phỏng vấn/đọc, quyết định/việc làm | G10.1 G15.3 | Mở rộng template |
| MEET-02 | THIẾU | Raw/enhanced/đã chốt, regenerate | G15.1 G10.2 | Giữ raw, provenance |
| MEET-03 | THIẾU | Ý chính→câu nói gốc/speaker/version | G15.2 G15.5 | Thiếu audio không hiện nghe |
| MEET-04 | THIẾU | Nhập bản ghi/biên bản/mốc từ Mốc Họp | G05.1 G10.3 G15.2 | Adapter UUID/time/asset |
| MEET-05 | HOÃN CÓ ĐIỀU KIỆN | Retention derivative/TTL | G10.4 | Không xóa raw/Event/asset |
| MEET-06 | HOÃN CÓ ĐIỀU KIỆN | Lịch họp/.ics thủ công | G10.5 G07+ | 10 event + 2 trùng |
| MEET-07 | HOÃN CÓ ĐIỀU KIỆN | Granola API/webhook opt-in | G15.4 | Chỉ khi có account, HMAC, scope |
| MEET-08 | HOÃN CÓ ĐIỀU KIỆN | Botless live transcript | G10+ G15+ | Tái dùng recorder, consent |

### VIS — Tổ chức trực quan (P2)

Điểm sở hữu/đối chiếu: KT130; refs trình bày, không graph DB/CRDT. Frontend tại apps/web/src, backend tại apps/backend. Tiêu chí là mục tiêu, không phải PASS.

| ID | Trạng thái | Chức năng | Nguồn | Tiêu chí / giới hạn |
| --- | --- | --- | --- | --- |
| VIS-01 | THIẾU | Canvas-lite nối luận điểm và nguồn | G12.5 G17.6 | 20 node/30 edge; xóa board không xóa item |
| VIS-02 | THIẾU | Whiteboard/sub-board/section, card tái sử dụng | G16+ G12.5 | Một card nhiều board |
| VIS-03 | THIẾU | Mind map, contextual graph | G16+ G17+ G13+ | Phân biệt edge user/related |
| VIS-04 | HOÃN CÓ ĐIỀU KIỆN | Page↔Edgeless layout nâng cao | G12.5 | 3 ca dùng thật |
| VIS-05 | HOÃN CÓ ĐIỀU KIỆN | Layout portable/JSON Canvas | G17.6 G12.5 | Restore 20 nodes, refs đúng |

### PORT — Portability và offline (P0/P2)

Điểm sở hữu/đối chiếu: KnowledgeVaultPanel.tsx / catalog/vault.py / storage/knowledge_export.py / backup. Frontend tại apps/web/src, backend tại apps/backend. Tiêu chí là mục tiêu, không phải PASS.

| ID | Trạng thái | Chức năng | Nguồn | Tiêu chí / giới hạn |
| --- | --- | --- | --- | --- |
| PORT-01 | CÓ MÃ | Markdown Vault export/import/manifest UUID | G05.6 G07.5 G09.5 G17.5 | Preview, conflict, roundtrip |
| PORT-02 | MỘT PHẦN | Gói một bài kèm đầy đủ media | G05.6 G07.5 G09.5 G17.5 | Vault không chứa media; verify hash |
| PORT-03 | MỘT PHẦN | Import Markdown/Obsidian phổ thông/frontmatter/link | G09.5 G17.5 G12+ | Importer vault có, format ngoài cần thử |
| PORT-04 | HOÃN CÓ ĐIỀU KIỆN | Importer Notion/Keep/OneNote/ENEX/HTML | G04+ G06+ G12+ | Theo format người dùng cần |
| PORT-05 | CÓ MÃ | Backup PostgreSQL/manifest/restore DB sạch | G07.5 G05.6 G17.5 | 10k text đã thử, media riêng |
| PORT-06 | MỘT PHẦN | Draft offline/retry | G02.3 G06.1 G13.5 | Không báo ACK giả |
| PORT-07 | HOÃN CÓ ĐIỀU KIỆN | Chọn bài offline, sync đa thiết bị/conflict | G01+ G04+ G09+ G12+ G13+ G17+ | 2 máy thật, không đổi DB |
| PORT-08 | HOÃN CÓ ĐIỀU KIỆN | Xuất định kỳ và history restore | G13+ G16+ G07.5 | Không chồng job, checksum |
| PORT-09 | HOÃN CÓ ĐIỀU KIỆN | MCP read-only có scope | G09+ G11+ G14+ G16+ G17+ | Pilot ChatGPT Drive 5–10 bài trước |
| PORT-10 | MỘT PHẦN | Bảo mật/riêng tư theo bài, export không secrets | G09.6 G07.5 | Owner/consent; AI policy từng item |

### GATE — Nghiệm thu và vận hành (P0)

Điểm sở hữu/đối chiếu: CURRENT_STATE.md / evals / tools/smoke / CI. Frontend tại apps/web/src, backend tại apps/backend. Tiêu chí là mục tiêu, không phải PASS.

| ID | Trạng thái | Chức năng | Nguồn | Tiêu chí / giới hạn |
| --- | --- | --- | --- | --- |
| GATE-01 | MỘT PHẦN | Sửa #101 và test đúng SHA | G17+ | 335/337 trước sửa, build/frontend/browser |
| GATE-02 | MỘT PHẦN | Windows UAT 4 viewport/keyboard/IME | G01–G17 | RC 13/13 cũ; HEAD mới chưa đủ |
| GATE-03 | MỘT PHẦN | 10k text/1k topic, perf, restore | G01–G17 | Không suy 10k video/100GB thật |
| GATE-04 | MỘT PHẦN | Drive PDF/MP4 thật, quota, quyền, latency | G01–G17 | 6 trang/2 mốc, >24MiB chưa |
| GATE-05 | MỘT PHẦN | Ingest đa nguồn FB/TikTok/YouTube | G01–G17 | FB live có; media TikTok/YT chưa gate; tuân quyền |
| GATE-06 | HOÃN CÓ ĐIỀU KIỆN | Android thực theo chỉ đạo | G01–G17 | Hoãn, không PASS |
| GATE-07 | MỘT PHẦN | Gold search/auto-group Việt độc lập | G01–G17 | Synthetic có; người dùng chưa chạy |
| GATE-08 | MỘT PHẦN | Giữ raw/UUID/Event/idempotency/consent | G01–G17 | Regression mỗi PR, backup trước migration |
| GATE-09 | MỘT PHẦN | Ledger feature ID/code SHA/tested SHA/DEPLOY | G01–G17 | Không drop row, cập nhật mỗi checkpoint |

## Ma trận truy ngược 94 đề xuất gốc

Các đề xuất A–E, P1–P5, I01–I06 quy đổi số theo thứ tự xuất hiện. Một đề xuất có thể ánh xạ nhiều ID.

| Báo cáo gốc | Đề xuất | ID |
| --- | --- | --- |
| [G01 Notion #43](https://github.com/cavoixanh638/kho-tri-thuc/pull/43) | G01.1 Saved views | VIEW-01, VIEW-02, VIEW-03, VIEW-06, NAV-03 |
| [G01 Notion #43](https://github.com/cavoixanh638/kho-tri-thuc/pull/43) | G01.2 Property/relation | TYPE-01, TYPE-05, TYPE-06, TYPE-10, VIEW-05 |
| [G01 Notion #43](https://github.com/cavoixanh638/kho-tri-thuc/pull/43) | G01.3 Backlinks | LINK-02, LINK-04 |
| [G01 Notion #43](https://github.com/cavoixanh638/kho-tri-thuc/pull/43) | G01.4 URL/share | CAP-01, CAP-04 |
| [G01 Notion #43](https://github.com/cavoixanh638/kho-tri-thuc/pull/43) | G01.5 Editor | EDIT-01, EDIT-02, EDIT-03, EDIT-04, EDIT-05, EDIT-06, EDIT-12 |
| [G01 Notion #43](https://github.com/cavoixanh638/kho-tri-thuc/pull/43) | G01.6 AI review | AI-01, AI-02, AI-12 |
| [G02 Keep #42](https://github.com/cavoixanh638/kho-tri-thuc/pull/42) | G02.1 Quick capture | CAP-01, CAP-02 |
| [G02 Keep #42](https://github.com/cavoixanh638/kho-tri-thuc/pull/42) | G02.2 Pin/color | NAV-06, CAP-06, CAP-07, CAP-08 |
| [G02 Keep #42](https://github.com/cavoixanh638/kho-tri-thuc/pull/42) | G02.3 Share | CAP-03, CAP-04, PORT-06 |
| [G02 Keep #42](https://github.com/cavoixanh638/kho-tri-thuc/pull/42) | G02.4 OCR | CAP-11, SEARCH-07 |
| [G02 Keep #42](https://github.com/cavoixanh638/kho-tri-thuc/pull/42) | G02.5 Voice | CAP-12, CAP-13 |
| [G02 Keep #42](https://github.com/cavoixanh638/kho-tri-thuc/pull/42) | G02.6 Reminders | CAP-14 |
| [G03 Lark #45](https://github.com/cavoixanh638/kho-tri-thuc/pull/45) | G03.1 Paste fields | TYPE-07, TYPE-09, CLIP-06, ORG-04, ORG-05 |
| [G03 Lark #45](https://github.com/cavoixanh638/kho-tri-thuc/pull/45) | G03.2 Smart tags | CLIP-10, ORG-01, ORG-02, ORG-06, ORG-08 |
| [G03 Lark #45](https://github.com/cavoixanh638/kho-tri-thuc/pull/45) | G03.3 Views | VIEW-01 |
| [G03 Lark #45](https://github.com/cavoixanh638/kho-tri-thuc/pull/45) | G03.4 Manual links | LINK-01, LINK-02 |
| [G03 Lark #45](https://github.com/cavoixanh638/kho-tri-thuc/pull/45) | G03.5 Source evidence | SOURCE-01 |
| [G03 Lark #45](https://github.com/cavoixanh638/kho-tri-thuc/pull/45) | G03.6 Transcript | SOURCE-04, SOURCE-05 |
| [G04 Evernote #46](https://github.com/cavoixanh638/kho-tri-thuc/pull/46) | G04.1 Clipper | CLIP-01, CLIP-02, CLIP-03, CLIP-04, CLIP-05, CLIP-07, CLIP-10 |
| [G04 Evernote #46](https://github.com/cavoixanh638/kho-tri-thuc/pull/46) | G04.2 Match→source | SOURCE-02, SOURCE-03, SOURCE-06, SEARCH-04, SEARCH-07 |
| [G04 Evernote #46](https://github.com/cavoixanh638/kho-tri-thuc/pull/46) | G04.3 AI edit | AI-01, AI-02, AI-03 |
| [G04 Evernote #46](https://github.com/cavoixanh638/kho-tri-thuc/pull/46) | G04.4 Tags view/path | VIEW-13 |
| [G04 Evernote #46](https://github.com/cavoixanh638/kho-tri-thuc/pull/46) | G04.5 Highlight/saved search | VIEW-02, SEARCH-01, SEARCH-02, SEARCH-04, SEARCH-06 |
| [G04 Evernote #46](https://github.com/cavoixanh638/kho-tri-thuc/pull/46) | G04.6 Semantic | SEARCH-03, SEARCH-05, SEARCH-08 |
| [G05 OneNote #40](https://github.com/cavoixanh638/kho-tri-thuc/pull/40) | G05.1 Timed annotation | SOURCE-02, SOURCE-03, SOURCE-05, SOURCE-09, MEET-04 |
| [G05 OneNote #40](https://github.com/cavoixanh638/kho-tri-thuc/pull/40) | G05.2 Organize preview | ORG-02, ORG-03 |
| [G05 OneNote #40](https://github.com/cavoixanh638/kho-tri-thuc/pull/40) | G05.3 Clipper | CLIP-01, CLIP-03 |
| [G05 OneNote #40](https://github.com/cavoixanh638/kho-tri-thuc/pull/40) | G05.4 Source-set | AI-04, AI-05 |
| [G05 OneNote #40](https://github.com/cavoixanh638/kho-tri-thuc/pull/40) | G05.5 Navigation/source sidepane | WS-05, WS-08, TREE-01, TREE-02, EDIT-07, SOURCE-08, SOURCE-10 |
| [G05 OneNote #40](https://github.com/cavoixanh638/kho-tri-thuc/pull/40) | G05.6 Portable package | PORT-01, PORT-02, PORT-05 |
| [G06 Apple Notes #41](https://github.com/cavoixanh638/kho-tri-thuc/pull/41) | G06.1 Quick capture | CAP-01, CAP-02, CAP-03, PORT-06 |
| [G06 Apple Notes #41](https://github.com/cavoixanh638/kho-tri-thuc/pull/41) | G06.2 Smart filters | VIEW-02, VIEW-03, NAV-04, SEARCH-02 |
| [G06 Apple Notes #41](https://github.com/cavoixanh638/kho-tri-thuc/pull/41) | G06.3 Outline/fold | EDIT-09, EDIT-10 |
| [G06 Apple Notes #41](https://github.com/cavoixanh638/kho-tri-thuc/pull/41) | G06.4 Internal link | EDIT-11, LINK-01, LINK-02 |
| [G06 Apple Notes #41](https://github.com/cavoixanh638/kho-tri-thuc/pull/41) | G06.5 Transcript seek | SOURCE-02, SOURCE-03, SOURCE-04, SOURCE-11 |
| [G06 Apple Notes #41](https://github.com/cavoixanh638/kho-tri-thuc/pull/41) | G06.6 Scan OCR | CAP-10, CAP-11, SEARCH-07 |
| [G07 Mem #38](https://github.com/cavoixanh638/kho-tri-thuc/pull/38) | G07.1 Heads Up | WS-09, LINK-04, LINK-07, LINK-08 |
| [G07 Mem #38](https://github.com/cavoixanh638/kho-tri-thuc/pull/38) | G07.2 Timeline | LINK-08, NAV-03, NAV-04 |
| [G07 Mem #38](https://github.com/cavoixanh638/kho-tri-thuc/pull/38) | G07.3 Send existing | CAP-05, CLIP-05, CLIP-09 |
| [G07 Mem #38](https://github.com/cavoixanh638/kho-tri-thuc/pull/38) | G07.4 AI diff | AI-01, AI-02, AI-03 |
| [G07 Mem #38](https://github.com/cavoixanh638/kho-tri-thuc/pull/38) | G07.5 Portable | PORT-01, PORT-02, PORT-05, PORT-08, PORT-10 |
| [G07 Mem #38](https://github.com/cavoixanh638/kho-tri-thuc/pull/38) | G07.6 Exact locator | SOURCE-02, SOURCE-03 |
| [G08 Coda #36](https://github.com/cavoixanh638/kho-tri-thuc/pull/36) | G08.1 Connected views | VIEW-01, VIEW-03, VIEW-05 |
| [G08 Coda #36](https://github.com/cavoixanh638/kho-tri-thuc/pull/36) | G08.2 Relations | TYPE-06, LINK-04, LINK-06, ORG-06 |
| [G08 Coda #36](https://github.com/cavoixanh638/kho-tri-thuc/pull/36) | G08.3 Buttons | VIEW-11, ORG-07 |
| [G08 Coda #36](https://github.com/cavoixanh638/kho-tri-thuc/pull/36) | G08.4 AI review | ORG-01, ORG-02, ORG-03, ORG-05, ORG-08 |
| [G08 Coda #36](https://github.com/cavoixanh638/kho-tri-thuc/pull/36) | G08.5 Presets | TYPE-07, TYPE-08, TYPE-09, CAP-02, ORG-04 |
| [G09 Reflect #34](https://github.com/cavoixanh638/kho-tri-thuc/pull/34) | G09.1 Daily quick note | NAV-03, NAV-04, NAV-05, CAP-01 |
| [G09 Reflect #34](https://github.com/cavoixanh638/kho-tri-thuc/pull/34) | G09.2 Wiki/backlinks | EDIT-15, LINK-01, LINK-02 |
| [G09 Reflect #34](https://github.com/cavoixanh638/kho-tri-thuc/pull/34) | G09.3 Source cards | SOURCE-01 |
| [G09 Reflect #34](https://github.com/cavoixanh638/kho-tri-thuc/pull/34) | G09.4 Ctrl+K | NAV-01, NAV-02, SEARCH-06 |
| [G09 Reflect #34](https://github.com/cavoixanh638/kho-tri-thuc/pull/34) | G09.5 Portable | PORT-01, PORT-02, PORT-03 |
| [G09 Reflect #34](https://github.com/cavoixanh638/kho-tri-thuc/pull/34) | G09.6 AI opt-in | AI-01, AI-12, PORT-10 |
| [G10 Superpowered #39](https://github.com/cavoixanh638/kho-tri-thuc/pull/39) | G10.1 Templates | TYPE-02, TYPE-03, MEET-01 |
| [G10 Superpowered #39](https://github.com/cavoixanh638/kho-tri-thuc/pull/39) | G10.2 Actions | AI-10, MEET-02 |
| [G10 Superpowered #39](https://github.com/cavoixanh638/kho-tri-thuc/pull/39) | G10.3 Timed notes | SOURCE-09, MEET-04 |
| [G10 Superpowered #39](https://github.com/cavoixanh638/kho-tri-thuc/pull/39) | G10.4 Retention | MEET-05 |
| [G10 Superpowered #39](https://github.com/cavoixanh638/kho-tri-thuc/pull/39) | G10.5 Calendar | MEET-06 |
| [G11 Gemini Notebook #44](https://github.com/cavoixanh638/kho-tri-thuc/pull/44) | G11.1 Citation | SOURCE-02, SOURCE-03, SOURCE-06, AI-06 |
| [G11 Gemini Notebook #44](https://github.com/cavoixanh638/kho-tri-thuc/pull/44) | G11.2 Source scope | AI-04, AI-05, AI-13 |
| [G11 Gemini Notebook #44](https://github.com/cavoixanh638/kho-tri-thuc/pull/44) | G11.3 Source states | SOURCE-01, SOURCE-11, SOURCE-14 |
| [G11 Gemini Notebook #44](https://github.com/cavoixanh638/kho-tri-thuc/pull/44) | G11.4 Classification | ORG-01, ORG-02, ORG-08 |
| [G11 Gemini Notebook #44](https://github.com/cavoixanh638/kho-tri-thuc/pull/44) | G11.5 FAQ/briefing | AI-07, AI-13 |
| [G12 AFFiNE #32](https://github.com/cavoixanh638/kho-tri-thuc/pull/32) | G12.1 Source cards | SOURCE-01, SOURCE-10 |
| [G12 AFFiNE #32](https://github.com/cavoixanh638/kho-tri-thuc/pull/32) | G12.2 Backlinks | LINK-02, LINK-04 |
| [G12 AFFiNE #32](https://github.com/cavoixanh638/kho-tri-thuc/pull/32) | G12.3 Views | TREE-01, VIEW-01 |
| [G12 AFFiNE #32](https://github.com/cavoixanh638/kho-tri-thuc/pull/32) | G12.4 Editor PoC | EDIT-03, EDIT-04, EDIT-05, EDIT-06, EDIT-07 |
| [G12 AFFiNE #32](https://github.com/cavoixanh638/kho-tri-thuc/pull/32) | G12.5 Canvas | VIS-01, VIS-02, VIS-04, VIS-05 |
| [G13 Capacities #37](https://github.com/cavoixanh638/kho-tri-thuc/pull/37) | G13.1 Context backlinks | LINK-04, LINK-05, LINK-06, ORG-06 |
| [G13 Capacities #37](https://github.com/cavoixanh638/kho-tri-thuc/pull/37) | G13.2 Object types | TYPE-01, TYPE-02, TYPE-04, TYPE-05, TYPE-07, TYPE-08 |
| [G13 Capacities #37](https://github.com/cavoixanh638/kho-tri-thuc/pull/37) | G13.3 Web highlights | CLIP-07, CLIP-08 |
| [G13 Capacities #37](https://github.com/cavoixanh638/kho-tri-thuc/pull/37) | G13.4 PDF highlights | CLIP-09, SOURCE-02, SOURCE-07 |
| [G13 Capacities #37](https://github.com/cavoixanh638/kho-tri-thuc/pull/37) | G13.5 Share | CAP-03, CAP-05, PORT-06 |
| [G14 Tana #33](https://github.com/cavoixanh638/kho-tri-thuc/pull/33) | G14.1 Supertags | TYPE-02, TYPE-03, TYPE-04, TYPE-05, TYPE-06, TYPE-08, TYPE-10 |
| [G14 Tana #33](https://github.com/cavoixanh638/kho-tri-thuc/pull/33) | G14.2 Saved queries | VIEW-02, SEARCH-02 |
| [G14 Tana #33](https://github.com/cavoixanh638/kho-tri-thuc/pull/33) | G14.3 Related | WS-09, LINK-04, LINK-05, LINK-06, LINK-07 |
| [G14 Tana #33](https://github.com/cavoixanh638/kho-tri-thuc/pull/33) | G14.4 Views | VIEW-01, VIEW-06, VIEW-08 |
| [G14 Tana #33](https://github.com/cavoixanh638/kho-tri-thuc/pull/33) | G14.5 AI autofill | ORG-04, ORG-05, ORG-06, AI-12 |
| [G15 Granola #31](https://github.com/cavoixanh638/kho-tri-thuc/pull/31) | G15.1 Raw/AI | EDIT-13, AI-01, AI-02, AI-03, AI-07, MEET-02 |
| [G15 Granola #31](https://github.com/cavoixanh638/kho-tri-thuc/pull/31) | G15.2 Transcript | SOURCE-04, SOURCE-12, MEET-03, MEET-04 |
| [G15 Granola #31](https://github.com/cavoixanh638/kho-tri-thuc/pull/31) | G15.3 Template | TYPE-02, AI-10, MEET-01 |
| [G15 Granola #31](https://github.com/cavoixanh638/kho-tri-thuc/pull/31) | G15.4 Granola adapter | MEET-07 |
| [G15 Granola #31](https://github.com/cavoixanh638/kho-tri-thuc/pull/31) | G15.5 Claim evidence | AI-06, AI-09, MEET-03 |
| [G16 Heptabase #35](https://github.com/cavoixanh638/kho-tri-thuc/pull/35) | G16.1 Exact citation | CLIP-08, CLIP-09, SOURCE-02, SOURCE-03, SOURCE-06, SOURCE-07, SOURCE-08, SOURCE-09 |
| [G16 Heptabase #35](https://github.com/cavoixanh638/kho-tri-thuc/pull/35) | G16.2 Related | WS-09, LINK-04, LINK-05, LINK-06, LINK-07, SOURCE-10 |
| [G16 Heptabase #35](https://github.com/cavoixanh638/kho-tri-thuc/pull/35) | G16.3 Tag/table | TYPE-10, VIEW-01, VIEW-05 |
| [G16 Heptabase #35](https://github.com/cavoixanh638/kho-tri-thuc/pull/35) | G16.4 Inbox | CAP-01, CAP-06, CAP-07, ORG-03 |
| [G16 Heptabase #35](https://github.com/cavoixanh638/kho-tri-thuc/pull/35) | G16.5 AI insights | AI-01, AI-02, AI-06, AI-09, AI-12 |
| [G17 Obsidian #30](https://github.com/cavoixanh638/kho-tri-thuc/pull/30) | G17.1 Live Preview | EDIT-01, EDIT-02, EDIT-03, EDIT-04, EDIT-12 |
| [G17 Obsidian #30](https://github.com/cavoixanh638/kho-tri-thuc/pull/30) | G17.2 Backlinks | LINK-01, LINK-02, LINK-03, LINK-04, LINK-09 |
| [G17 Obsidian #30](https://github.com/cavoixanh638/kho-tri-thuc/pull/30) | G17.3 Views | VIEW-01, VIEW-02, VIEW-03, VIEW-06, VIEW-07 |
| [G17 Obsidian #30](https://github.com/cavoixanh638/kho-tri-thuc/pull/30) | G17.4 Clip | CAP-04, CLIP-01, CLIP-02, CLIP-04, CLIP-05, CLIP-06, CLIP-07 |
| [G17 Obsidian #30](https://github.com/cavoixanh638/kho-tri-thuc/pull/30) | G17.5 Vault | PORT-01, PORT-02, PORT-03, PORT-05 |
| [G17 Obsidian #30](https://github.com/cavoixanh638/kho-tri-thuc/pull/30) | G17.6 Canvas | VIS-01, VIS-05 |

**Kiểm kê:** 176 ID trong 17 nhóm, 94/94 đề xuất gốc có ánh xạ. MỘT PHẦN: 51; THIẾU: 66; CÓ MÃ: 36; HOÃN CÓ ĐIỀU KIỆN: 23. Đây là số dòng, không phải tỷ lệ hoàn thành sản phẩm. Nguồn [INDEX 17 nghiên cứu](research/notes-apps-20261120/INDEX.md), [ma trận 38 nhóm cũ](workstreams/notes-ux-20261120/G00-FEATURE-TRACEABILITY.md), [G00 #47](https://github.com/cavoixanh638/kho-tri-thuc/pull/47).

## Thứ tự triển khai và ownership

| Đợt | ID | Ranh giới / gate |
| --- | --- | --- |
| 0 | GATE, TREE-05/06/08, WS-01/02 | Sửa regression #101, test đúng SHA; không DB/API mới |
| 1A | TREE-07/09, WS-03–10, NAV, EDIT-09/10 | Workspace, route/draft, không chồng App/ItemScreen |
| 1B | EDIT | ADR so 2–3 editor, PoC lossless trước thay |
| 1C | SOURCE, CLIP | Reader/locator trước extension, provenance |
| 1D | TYPE, VIEW, LINK, CAP | Schema ADR/migration riêng, Android hoãn |
| 1E | SEARCH, ORG | Gold độc lập, câu âm, curated protection |
| 2A | AI, MEET | Source-set read-only trước AI, consent/cost, adapter Mốc Họp |
| 2B | VIS, PORT | Canvas và offline từng bước, trigger ca dùng |

Mỗi nhóm có thể chia thành PR nhỏ theo ID và file sở hữu, không gộp thay đổi lớn. Không tự merge. Ưu tiên test có chọn lọc ở mỗi checkpoint, full gate trước release.

## Nhật ký tiến độ (cập nhật mỗi PR)

| Ngày | ID | Code SHA / Tested SHA | Trạng thái / giới hạn / NEXT |
| --- | --- | --- | --- |
| 25/11/2026 | ALL | baseline a820a6d / NOT_RUN mới | Kế hoạch lập; 94/94 truy vết; bắt đầu TREE-08 và WS-02; chưa merge/deploy |
| 25/11/2026 | WS-02, TREE-07, TREE-08, GATE-01/09 | 94be069ab7753e46a65b1021482bd113b8ad1d40 / NOT_RUN | CODE checkpoint: separator resize 240–480, keyboard/pointer, reload preference (sessionStorage, CSS cap viewport), collapse/reopen cache, root tree bền qua unfiled, malformed payload retry, shortcut accessible label; test DOM thêm/sửa. Docs README và AGENTS bắt buộc ledger. Chưa xác nhận CI/browser/Windows. Rollback: revert commit frontend + docs (không migration). NEXT: chạy CI đúng HEAD; kiểm pointer thật ở 4 viewport; sau PASS tiếp TREE-06/09, WS-03, EDIT-10. |

| 25/11/2026 | WS-02, TREE-07/08, GATE-01 | 94be069 / 10dc329b | [Actions #45660847662](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/45660847662): bước frontend DOM/unit và bước browser acceptance hoàn tất SUCCESS tại lần đọc; các job tổng thể còn chạy nên chưa gọi release PASS. Đây là bằng chứng của checkpoint cũ, không phải HEAD mới. |
| 25/11/2026 | TREE-06/09, SEARCH-04 | 6daf1424ca10c55ec7d6c7e5a3ede75458836bb5 / NOT_RUN | CODE: tìm tên folder/note trong sidebar bằng /navigation giới hạn 20+20, debounce/abort/IME, không remount cây; tự cuộn mục lục tới note chính đã tải, không cuộn trang đọc, không đổi focus; highlight token khớp tiếng Việt có/không dấu, NFC/NFD, giữ nguyên text, không giả semantic. J7 thêm CDP pointer thật, keyboard, 4 viewport, search, collapse/restore. Còn giới hạn active note ngoài trang lazy đã tải, TREE-06 vẫn MỘT PHẦN; chưa xác nhận CI/Windows. NEXT: CI đúng HEAD rồi tiếp WS-03/04 và EDIT-10. Rollback revert frontend/tests, không migration. |

| 26/11/2026 | GATE-01, WS-02, TREE-06/09, SEARCH-04 | 2716e32a77ab0e8f145b70352ea37ee175a4e10f / 2056c535297d4867aa23e1e01550449289b4dc64 | [Run 45661554823](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/45661554823): frontend 344/344 PASS, P15 104/104 PASS (screen reader NOT_RUN), P08 12/13 FAIL J7 (width=356, saved=286). J8 vault, J9 synthetic 10k/1k PG restore, J6B private synthetic PASS. Windows/provider thật không được suy PASS. |
| 26/11/2026 | WS-02, EDIT-10, TREE-08 | dbd0935c0fe44e38c6b077ba817ad82d8282766c / NOT_RUN | CODE: lưu chiều rộng ngay lúc kéo/phím, không phụ thuộc passive effect; chặn DTO cấu trúc bài/danh sách folder lỗi và stale request; thu gọn heading Markdown theo cấp thực bằng native details, outline tự mở tổ tiên, nhớ preference theo note (không lưu raw/ghi DB). Thêm test nested heading, reload, raw, retry lỗi DTO và J2 Chromium. Chỉ top-level Markdown heading; chưa folding trong list/quote. NEXT: CI toàn bộ đúng SHA, sửa nếu lỗi, tiếp WS-03/04, EDT toolbar. Rollback revert frontend/test, không migration. |

| 26/11/2026 | GATE-01, EDIT-10, WS-02, TREE-08 | ce39d51be24e471f90ca97f8a743df605b189ac3 / GitHub PR merge-test SHA (xem run) | [Run 45735056944](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/45735056944): frontend 345/347 FAIL; J2/J7 browser step chạy xong nhưng gate cuối chưa xác nhận. Hai lỗi: React component inline remount khi fold; test P01 còn truy vấn nhãn/message của boundary cũ. Sửa ổn định identity và assert panel lỗi recoverable ở checkpoint sau, không hạ tiêu chí. |
| 26/11/2026 | WS-03/04/06, EDIT-10, TREE-08 | 8644e8e521fe3b316cbf22753330cd5035d9e2a4 / NOT_RUN | CODE: tab theo route một editor, chuyển/đóng/mở lại, pin, reorder drag/Alt+Arrow, tối đa 20 tab, khôi phục UUID/pin/order trong phiên theo tài khoản; /navigation/tabs chỉ trả metadata ≤20 ID owner-scoped, không title/raw ở storage; explicit logout/expiry xóa preference. Guard lưu draft đồng bộ trước chuyển tab, chặn nếu composition/save/quota lỗi. Fold components ổn định không remount. J7 thêm chuyển tab với nháp chưa gửi, không đổi raw/CaptureEvent, pin/close/reopen; unit/DB tests riêng. WS04 còn thiếu modifier mở tab mới chuyên biệt; WS06 chưa lưu split-layout (WS05 chưa làm), WS07 scroll history chưa làm. Rollback revert code + tests, không migration. NEXT: CI đúng HEAD; sửa lỗi trước split/preview và editor. |

| 26/11/2026 | GATE-01, WS-02/03/04/06, EDIT-10, TREE-08 | 4f85fe45926c71897189fd646dd50f7275294fdc / be83e8e17f9abf77f169b03c6a51b7b00074089f | [Run 45735408565](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/45735408565): **scaffold + G2 SUCCESS**. Frontend 349/349; Django 414 ca (405 PASS, 9 skipped); P08 13/13; P15 104/104; J7 tab switch draft recovery, pin/close/reopen, resize/collapse/search PASS; 10k text/1k topic/PG backup restore và J6B synthetic PDF page 2/MP4 2.5s PASS. Không suy screen reader, native Android, Drive/provider thật, dữ liệu 100GB hoặc Windows production UAT từ synthetic gate. NOT_DEPLOYED. |
| 26/11/2026 | GATE-09 | 9cc9e4fce273a8c77c2ddb1317e462ad9892592e / kiểm logic offline + CI HEAD mới chưa chạy | Thêm validator 176 ID tối thiểu, 94 đề xuất đúng PR và forward/reverse, totals/status, 6 negative fixtures; chạy trong smoke hiện có trước Compose, không thêm job/runner. Checkpoint này chỉ thêm kiểm tra/tài liệu, không đổi app đã PASS ở 4f85fe4. NEXT: kiểm CI test-only và triển khai WS05/08/09, EDIT-03/04 theo gate; không merge/deploy tự động. |

**Prompt chuyển tiếp:** Vào repo, đọc file này + AGENTS.md + CURRENT_STATE; kiểm HEAD và PR đang mở, chọn đúng ID, thực hiện code, regression, cập nhật ID + checkpoint, commit/PR, không tự merge/deploy. Giữ tất cả ánh xạ và dòng chưa làm/hoãn.
