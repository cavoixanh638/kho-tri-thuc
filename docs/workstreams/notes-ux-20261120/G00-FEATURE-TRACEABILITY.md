# G00 — KIỂM TOÁN CHUYỂN GIAO 17 NGHIÊN CỨU THÀNH SẢN PHẨM (LẦN BA)

**Ngày:** 20/11/2026. **Phạm vi:** 17 báo cáo G01–G17 ở PR #30–46, hai tài liệu G00 ở PR #47, code main và code tích hợp [PR #57](https://github.com/cavoixanh638/kho-tri-thuc/pull/57) HEAD `e00b3cacd02decdb852dc6e17e7b297d83acaccf` khi kiểm. **Đầu ra:** feature traceability/backlog, không phải bằng chứng đã chạy browser/Android hay “mọi ưu điểm đã áp dụng”. PR #57 vẫn OPEN/UNMERGED khi đối chiếu.

## 1. Phát hiện gốc và trách nhiệm G00

G00 đợt trước đã **rút 17 nghiên cứu (mỗi báo cáo có 5–6 ý tưởng có thể áp dụng)** thành 8 task UX (KT-114–121) mà không giữ **sổ quyết định/traceability cho từng ý tưởng**. Vì vậy số chức năng được giao không thể đại diện đầy đủ cho UX kỳ vọng. Ví dụ: mixed folder + note explorer, note→note structural parent, wiki-link autocomplete, command palette, smart collections, web clipper/quote, portable Markdown vault **đều không nằm trong KT-114–121**. Việc có `Topic.parent`, List/Table/Card/Timeline và RelatedItem **không tương đương** những khả năng này.

**Đính chính cách công bố:** 17 sản phẩm được **nghiên cứu**; không có nghĩa 17 sản phẩm được **tích hợp**, không nên phát biểu “đã học và áp dụng hết”. PR #57 có code PoC cho một số tính năng nhưng chưa merge/triển khai. G00 chịu trách nhiệm kiểm đủ feature-jou​​rney và đóng vòng chứ không để người dùng phải phát hiện từng thiếu sót.

## 2. Quy tắc nhãn trạng thái

- `MAIN`: có code trong main, có thể giới hạn phạm vi.
- `PR57`: code đã có trong PR #57, **không phải bản đang chạy**; CI green không thay end-to-end UAT.
- `PARTIAL`: có model/adapter/panel nhưng luồng sử dụng mong đợi còn thiếu.
- `GAP`: chưa thấy code/hợp đồng cho khả năng cụ thể qua các file đã rà; kết luận dựa static inspection, không phải chứng minh không có ở mọi nhánh khác.
- `CONDITIONAL/DEFER`: chỉ làm khi có bằng chứng nhu cầu/quyền/chi phí, phải ghi rõ lý do và điều kiện mở lại.
- `NOT_RUN`: chưa có bằng chứng chạy thật; không đồng nghĩa FAIL.
- Mỗi dòng chỉ ra **nguồn ứng dụng**, **chứng cứ code**, **quyết định/task**. G00 sẽ **không** đánh dấu done nếu mới có tài liệu task hoặc CI không bao phủ luồng.

## 3. Ma trận kiểm toán tính năng (đủ 17 nguồn; không lọc chỉ 8 task cũ)

| ID | Năng lực người dùng phải nhìn thấy | Nguồn ý tưởng | Đối chiếu hiện trạng | Chứng cứ code/điểm giới hạn | Quyết định/task | Ghi chú quan trọng |
| --- | --- | --- | --- | --- | --- | --- |
| ORG-01 | Thư mục nhiều cấp / chuyển thư mục | G01,G03,G05,G06,G09,G12,G14,G17 | MAIN — DATA + FOLDER-ONLY UI | Topic.parent; knowledge_tree.py; KnowledgeTree.tsx | KT-122 | Không coi cây Topic là mixed explorer |
| ORG-02 | Folder + Note xen kẽ trong một cây | G05,G06,G09,G12,G14,G17 | GAP | KnowledgeTree.tsx chỉ map Topic | KT-122 | Bắt buộc có note leaf, keyboard, drag/drop |
| ORG-03 | Tạo note trong folder; primary folder và shortcut đa nhánh | G01,G03,G05,G12,G14,G17 | GAP / BACKEND PARTIAL | ItemTopic M:N và CaptureService có; UI chưa nối | KT-122 | Không nhân Item/Asset/Event |
| ORG-04 | Note cha → Note con / phân chương sách | G05,G09,G12,G14,G17 | GAP | RelatedItem canonical pair không directed structural parent | KT-123 | Tách ba quan hệ parent-folder, folder-note, note-note |
| ORG-05 | Backlink từ liên kết do người dùng tạo | G01,G03,G06,G07,G08,G09,G12,G13,G16,G17 | PR57 — PARTIAL | groups_api.py:_inline_item_links; RelatedSources.tsx | KT-124 | Đã đọc link Markdown hợp lệ, chưa đủ autocomplete wiki-link authoring |
| ORG-06 | Wiki-link [[...]] tự gợi ý, stable UUID qua đổi tên | G06,G09,G12,G17 | GAP | KnowledgeText.tsx + MarkdownEditor.tsx | KT-124 | Không dựa vào title làm định danh |
| ORG-07 | Unlinked mentions, graph contextual | G07,G09,G12,G13,G16,G17 | GAP / PARTIAL | RelatedSources.tsx có same-group/similar/backlinks; test ghi backlinks_scope inline_markdown_only | KT-124 | Ứng viên chưa liên kết phải được gắn nhãn, không tự bịa |
| ORG-08 | Saved search / smart folder / collections động | G01,G03,G06,G08,G09,G12,G14,G17 | GAP | SearchScreen.tsx filter tại URL; chưa có saved query object | KT-125 | Bộ lọc động không chuyển ItemTopic |
| ORG-09 | Một tập ID nhiều view: list/table/card/timeline | G01,G03,G06,G08,G12,G14,G16,G17 | PR57 — IMPLEMENTED CANDIDATE | LibraryViews.tsx + LibraryScreen.tsx; pagination giới hạn theo trang | KT-128 QA | Không nhầm with folder hierarchy hoặc saved views |
| ORG-10 | Kanban/calendar/đổi nhóm từ bảng | G01,G08,G13,G14,G17 | GAP/DEFER REVIEW | LibraryViews.tsx chỉ list/table/card/timeline, không editable cell | KT-125 PHASE 2 | Chỉ bổ sung nếu workflow được xác nhận; không tùy tiện drag gây mất nhóm |
| ORG-11 | Metadata chips / loại bài / properties theo kiểu supertag | G01,G03,G06,G08,G13,G14 | PR57 PARTIAL | NoteTemplateConfig/Picker dạng template Markdown, GroupEditor MultiSelect; chưa có field schema typed | KT-125 PHASE 2 | Đừng coi template là typed properties |
| ORG-12 | Người dùng duyệt đề xuất phân loại, có bằng chứng | G03,G05,G08,G11,G13,G14 | BACKEND PARTIAL, UX GAP | OrganizationService auto rules; ItemOrganization MultiSelect; chưa có review queue provenance | KT-129 | Auto chỉ khi policy đủ chắc, không xóa pinned |
| NAV-01 | Mục lục H1–H6 trong bài, anchor, fold heading | G05,G06,G09,G12,G14,G17 | GAP | KnowledgeText.tsx render Markdown nhưng chưa TOC/collapse | KT-124 | Mục lục H1 không phải Item con |
| NAV-02 | Command palette / Ctrl+K / keyboard actions | G02,G06,G09,G12,G17 | GAP | SearchScreen riêng; App.tsx chưa command palette | KT-124 | Không can thiệp IME |
| NAV-03 | Preview liên kết khi hover/sidepane, mở nguồn không mất trang | G05,G07,G09,G12,G13,G16 | GAP/PARTIAL | RelatedSources.tsx cards; ItemScreen.tsx viewer flow riêng | KT-124 PHASE 2 | Mobile dùng tap/collapsible, không cần hover |
| NAV-04 | Daily quick notes và timeline nhận nguồn khác ngày phát hành | G02,G06,G07,G09,G14 | PR57 PARTIAL | CaptureScreen draft; LibraryViews timeline saved_at; HistoryScreen events | KT-125 | Ngày ghi/nhận/đăng phải tách |
| CAP-01 | Quick capture từ Windows/Android và share target | G01,G02,G03,G05,G06,G08,G09,G13,G17 | PR57 IMPLEMENTED CANDIDATE, DEVICE NOT_RUN | CaptureScreen/sharedCapture/manifest | KT-128 QA | Không giả Android PASS |
| CAP-02 | Web Clipper: URL/article/selection/screenshot có preview | G01,G03,G04,G05,G06,G08,G09,G13,G17 | GAP / URL EXISTING | CaptureScreen nhận URL/file; source_fetch có; không selection clip UX hoàn chỉnh | KT-126 | Không cần extension ở pha 1; không lấy trang riêng tư trái phép |
| CAP-03 | Clip/trích đoạn nguồn gắn trực tiếp vào bài đang có | G03,G04,G05,G07,G09,G12,G13,G16 | PARTIAL | SourceLinks gắn URL vào Item có sẵn, chưa có selected quote/hash locator workflow | KT-126 | Giữ note gốc, provenance, không ghi đè |
| CAP-04 | Tạo note và nguồn có cấu trúc sau paste-to-fields | G03,G06,G08,G13,G14 | GAP/CONDITIONAL | CaptureScreen text/file/url; chưa có field proposal | KT-126 PHASE 2 | Chỉ đề xuất và duyệt; OCR tùy điều kiện |
| CAP-05 | Ghi âm/voice inbox/timed annotation | G02,G05,G06,G10,G15 | NOT_SELECTED / CONDITIONAL | transcript ASR hiện có; meeting recorder là dự án khác | KT-130 DEFER | Dùng adapter tới nguồn ghi họp thay vì xây recorder trùng |
| SRC-01 | Citation → PDF/audio/video chính xác | G04,G05,G06,G07,G11,G12,G13,G15,G16 | PR57 PARTIAL + LIVE GATES | SourceLocator.tsx, viewer_api.py, KnowledgeReading; PDF pageNavigationVerified=false | KT-128 + PR57 REVIEW | Không có timestamp thì không suy; authored note case chưa nối |
| SRC-02 | Highlight PDF/web chính xác và đoạn nguồn giữ version | G04,G05,G06,G11,G12,G13,G16 | GAP/BELOW-GATE | DerivedContent.source_locator có; chưa web quote anchor và PDF rect verified | KT-126 | Phân biệt locator page vs exact span |
| SRC-03 | Thẻ nguồn có trạng thái đã trích/chưa trích và provenance | G01,G03,G04,G07,G09,G11,G12,G13,G16 | PR57 PARTIAL | RelatedSources.SourceEvidence và KnowledgeReading, Item.source_fetch/content_extract | KT-128 QA | Source card không chứng minh video đã xử lý |
| SRC-04 | Source-scoped research workspace / selected notebooks | G05,G07,G11,G13,G15,G16 | GAP / CONDITIONAL | SearchService/ReadKnowledgeService có; chưa source-set workspace UX | KT-130 | Có thể làm read-only trước AI |
| SRC-05 | Câu trả lời có căn cứ / FAQ theo nhiều nguồn | G05,G11,G15,G16 | NOT_RUN / CONDITIONAL | Không có AI provider được duyệt; xuất tri thức theo Item đã có | KT-130 | AI chỉ sau quyền, nguồn và eval |
| EDT-01 | Markdown source/edit+preview/read, GFM/IME | G01,G05,G06,G09,G12,G17 | PR57 IMPLEMENTED CANDIDATE | MarkdownEditor.tsx, ItemScreen.tsx | KT-128 QA | Chưa bằng Obsidian live inline preview hoàn chỉnh |
| EDT-02 | Rich block editor / reusable block / callout | G01,G03,G05,G08,G12,G14 | GAP/DEFER | MarkdownEditor giữ Textarea; không có block object model | KT-130 | PoC so sánh lossless trước khi đầu tư |
| EDT-03 | Templates bản nháp theo loại, thủ công | G05,G10,G13,G14,G15 | PR57 PARTIAL | NoteTemplatePicker/Config; chưa có typed metadata | KT-125 PHASE 2 | Không tự nhận là full Supertag |
| AI-01 | AI preview/diff/accept/reject có version | G01,G03,G04,G05,G07,G08,G09,G11,G14,G15 | PR57 MANUAL POC, PROVIDER OFF | ItemSuggestionPanel manual_review_poc, suggestions.py | KT-128 QA | KHÔNG gọi là AI tự tạo nội dung |
| AI-02 | Semantic search/gợi ý bằng AI, kiểm chứng tiếng Việt | G04,G05,G07,G11,G13,G14 | DEFER UNTIL GOLD EVAL | SearchScreen lexical hiện có, chưa semantic provider | KT-130 | Chỉ nếu benchmark cải thiện đủ; không tự bật gửi dữ liệu |
| AI-03 | Voice meeting summary/decisions, transcript assertions | G05,G10,G11,G15 | DEFER / ADAPTER | ASR/corpus theo nguồn có; app ghi họp riêng | KT-130 | Không nhân đôi recorder; trích dẫn bắt buộc |
| PORT-01 | Portable Markdown vault có folder/frontmatter/UUID link | G01,G04,G06,G07,G09,G12,G17 | PARTIAL/GAP | KnowledgeExportPanel xuất từng item; backup DB/manifest; chưa vault roundtrip | KT-127 | Test import/export và mapping đa nhánh |
| PORT-02 | Import file Markdown/Obsidian notes với internal links | G06,G09,G12,G17 | GAP | Capture file Markdown có; chưa importer vault portable | KT-127 | Preserve IDs/mapping, dry-run conflict |
| PORT-03 | Clip/notes offline local-first, đồng bộ xung đột | G01,G02,G06,G09,G12,G17 | PARTIAL/NOT_RUN | draft CaptureScreen; backend online; không có CRDT/offline sync | KT-130 CONDITIONAL | Offline receipt không được nói đã lưu server |
| VIS-01 | Canvas/whiteboard nguồn và luận điểm | G05,G12,G16,G17 | DEFER | Không có Canvas; UX nhu cầu chưa được xác minh | KT-130 | P2/P3 chỉ sau folder+locator pass |
| VIS-02 | Knowledge map/graph toàn mạng | G07,G12,G13,G16,G17 | DEFER | RelatedItem là graph edge dạng DB nhưng UI chưa visualization | KT-130 | Không build graph DB mới |
| SYS-01 | Data safety, 10k, restore, Drive, Android | G01–G17 (cổng đánh giá chung) | PR57 TEST FIXTURE, LIVE NOT_RUN | KT-114 readiness; integration checkpoint | KT-128 | Gate vận hành độc lập với UX |

**Tổng dòng traceability:** 38 năng lực/nhóm năng lực; đây là số dòng được kiểm kê, **không** phải số tính năng sẵn sàng dùng, không phải số ý tưởng nguyên bản trong báo cáo (một dòng gộp ý tưởng tương tự từ nhiều sản phẩm). Dòng `SYS-01` dùng quy trình chung của 17 nghiên cứu. Các liên hệ Gxx là nguồn ý tưởng, không khẳng định mỗi báo cáo có cùng tính năng native.

## 4. Rà soát theo nguồn để tránh bỏ quên một luồng

| Luồng | Điểm học nổi bật | Ít nhất một hạng mục có đầu mối triển khai | Điểm chưa khép kín |
| --- | --- | --- | --- |
| G01 Notion | Rich editing, properties, view, relation | KT-115/118/125 | Typed properties, saved views, editor block đầy đủ chưa có |
| G02 Keep | Quick capture, pin, OCR/voice/reminders tùy nhu cầu | KT-117/126/130 | Pin/màu/reminders/voice chưa chốt, Android thật chưa test |
| G03 Lark | Paste-to-fields, smart tags, wiki, multi-view | KT-126/129/118/124 | Review nhãn, proposal field cần UX/benchmark |
| G04 Evernote | Clipper selection/article, search highlight/saved search | KT-126/125/128 | Clipper + match→source chưa hoàn chỉnh |
| G05 OneNote | Notebook/subpage, audio-linked note, research pane | KT-122/123/116/130 | Note parent và contextual annotation thiếu |
| G06 Apple Notes | Quick Notes, smart folder, outline, wiki-links | KT-117/125/124 | Smart folder, outline chưa triển khai |
| G07 Mem | Related Heads Up, send-into-note, portable export | KT-119/126/127 | Contextual pin, in-note clip thiếu; không phụ thuộc Mem đóng cửa |
| G08 Coda | Connected views, action buttons, field schema | KT-118/125/129 | View ≠ saved database-like workflows |
| G09 Reflect | Markdown/wiki links, daily notes, Ctrl+K, portable | KT-115/124/125/127 | Command palette & portable vault thiếu |
| G10 Superpowered | Ghi chú họp có template và source trace | KT-121/130 | Không tích hợp vendor không cho tải mới |
| G11 Gemini Notebook | Citation grounded, source-scoped collection, FAQ | KT-116/130 | Selected source research UI chưa có, AI provider chưa duyệt |
| G12 AFFiNE | Mixed block/canvas/backlinks/tables | KT-115/122/124/130 | Không fork; canvas tùy nhu cầu |
| G13 Capacities | Types, contextual links, PDF/web highlight | KT-121/124/126 | Source quote anchor và typed fields chưa đủ; audio Pro có từ 11/2026 |
| G14 Tana | Supertag, saved query, live collection | KT-125/129 | Saved queries và metadata theo type thiếu |
| G15 Granola | Raw/AI draft, transcript evidence, meeting template | KT-120/116/130 | AI provider off; Granola không giữ original audio |
| G16 Heptabase | Highlight/source cards, adjacent related, whiteboard | KT-116/126/119/130 | PDF page/segment thực và canvas chưa đạt |
| G17 Obsidian | Folder + note explorer, wiki, backlinks, Markdown portable | KT-122/123/124/127 | Không gọi `Topic` tree là File Explorer/Obsidian-style |

## 5. Đề xuất bổ sung và quyết định không áp dụng, có lý do

### Bắt buộc hoàn thiện để đáp ứng mục tiêu cốt lõi

1. **KT-122**: Folder + Note Explorer chung cây, home vs shortcut, create/move/drag/drop.
2. **KT-123**: Item cha/con, outline trong note, không dùng RelatedItem(similar) để thay.
3. **KT-124**: Internal links/wiki autocomplete, backlinks và unlinked mentions tách loại, command palette, heading TOC, keyboard navigation.
4. **KT-125**: Smart collections/saved searches, filter/group views bền vững, properties/type templates dạng nhẹ có phân định rõ template vs schema.
5. **KT-126**: Web clipper dạng selection/article/link, “gửi vào bài đang có”, text highlight có trích dẫn/locator, preview điều gì thực sự đã trích.
6. **KT-127**: Export/Import dạng Markdown vault portable + manifest, links/relations/attachments bền vững, restore audit.
7. **KT-128**: End-to-end acceptance **từ góc người dùng** nối KT-114–127: screenshot/video thật, Windows/Android, data/source, 10k fixture; nhận diện UI ẩn do width; không coi green unit CI là trải nghiệm hoàn chỉnh.

### Có giá trị nhưng còn điều kiện, cần có trạng thái thay vì bỏ khỏi kế hoạch

- **KT-129** (gán nhóm có kiểm soát): trang triage đề xuất phân loại/field kèm evidence và accept/reject; đo precision trên bộ tiếng Việt do người kiểm chứng. Không bật AI ngoài mặc định; chủ động dùng rule engine nếu đủ.
- **KT-130** (nghiên cứu sâu / mở rộng theo trigger): notebook theo tập nguồn, fact-cited FAQ/AI, canvas-lite, board, OCR/voice/reminders, semantic retrieval, local-first multi-device. **DEFER/CONDITIONAL** vì giá/chi phí bảo trì/độ ổn định so với mục tiêu lưu/đọc/tìm 10k video. Có thể làm source-set read-only trước AI nếu được giao. Không tích hợp Mem/Superpowered làm nền tảng.

### Những quyết định “không áp dụng” hợp lý

- Không thay Django/PostgreSQL/Drive bằng sản phẩm ghi chú thương mại; giữ CaptureEvent/Asset, UUID và quyền truy xuất.
- Không import/fork SDK đóng của Notion, OneNote, Apple Notes, Granola, Heptabase; kiểm từng package AFFiNE/MPL và Reflect MIT nếu muốn tái dùng mã thật.
- Không thêm graph DB chỉ vì backlinks, không chuyển CRDT/local-first toàn hệ khi chưa có yêu cầu cộng tác offline, không tự bật OCR/ASR/AI billable hoặc Google Notebook Preview, không di chuyển file media Drive theo UI folder.
- Không sao chép UI sản phẩm nguyên xi: chỉ mượn hành vi có kiểm thử tiếng Việt/Windows/Android và giữ an toàn dữ liệu.

## 6. Definition of Done cấp sản phẩm thay vì cấp task

Mọi task chỉ `CODE_DONE` khi có code+test SHA; nhưng **UX_COMPLETE** phải có **hành trình dùng được** theo `KT-128`: tạo folder→tạo note ngay trong folder→thêm note con→wiki-link tới note khác→kiểm backlink→clip web/PDF/video làm nguồn→tìm bằng command palette→xem smart collection→export/import→khôi phục mà không trùng ID. Ở 1920/1440/768/390 px phải có minh chứng cây thấy được và điều hướng đến cùng một Item. Không có thiết bị Android/Drive thật => NOT_RUN, không tự tuyên bố hoàn tất.

**Không gọi các task mới đã hoàn thành trước khi Codex thực thi.** Mọi task mới base PR #57 đang open; sau review tích hợp cẩn thận vào PR hoặc PR nối tiếp, không force-push hay merge khi người dùng chưa cho phép. Đọc `AGENTS.md`, `CURRENT_STATE.md` và `ROADMAP_AND_TESTS.md` về an toàn dữ liệu và ranh giới.
