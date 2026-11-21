# ĐẦU MỐI GIAO AI — KHO TRI THỨC, TRUY VẾT 17 NGHIÊN CỨU THÀNH TÍNH NĂNG (20/11/2026)

**Đường dẫn chuẩn cho AI mới:** `docs/workstreams/notes-ux-20261120/INDEX.md` trên **main**. Đây là **bộ triển khai đề xuất** sau 17 nghiên cứu G01–G17 và ba lần rà soát G00; không phải 17 ứng dụng đã được tích hợp. **ĐỌC TRƯỚC:** [ma trận G00 gồm 38 nhóm năng lực](G00-FEATURE-TRACEABILITY.md), có nguồn Gxx, trạng thái code và lý do triển khai/hoãn; không được lược bỏ chỉ vì PR #57 có CI xanh. **Chỉ bắt đầu viết code khi người dùng giao đúng mã KT-xxx.**

## 1. Prompt giao một AI (một dòng)

`Vào GitHub cavoixanh638/kho-tri-thuc, đọc docs/workstreams/notes-ux-20261120/INDEX.md; thực hiện đầy đủ KT-115, tự đọc code/test, commit, push và tạo PR. Không merge.`

Đổi **KT-115** thành mã tương ứng dưới đây. Nếu được giao *“triển khai toàn bộ”*, AI phải bắt đầu từ CORE gates, lập PR riêng, làm lần lượt theo phụ thuộc, **không tự merge** và không tự chuyển bằng chứng mock thành LIVE_PASS.

## 2. Nguồn sự thật và thứ tự đọc

1. `AGENTS.md`, `docs/CURRENT_STATE.md`, `docs/REPOSITORY_LAYOUT.md`.
2. `docs/MASTER_PLAN.md` (mục tiêu/phạm vi), `docs/CAPTURE_AND_ORGANIZE.md` (nghiệp vụ), `docs/ARCHITECTURE_AND_DATA.md` (schema/thiết kế), `docs/ROADMAP_AND_TESTS.md` (mã KT/tiêu chí nghiệm thu).
3. **Đúng một file task** trong KT-114–KT-130. **KT-122/123 phải đọc code của PR #57 `codex/notes-ux-integration`, không chỉ main** vì #57 đã ghép KT-114–121 nhưng chưa merge. Kiểm head PR/CI/test hiện hành, **không tin mô tả lịch sử “chưa có code”**.
4. **Bản tổng hợp nằm ngay trên main:** [RESEARCH_DECISIONS.md](RESEARCH_DECISIONS.md) (ma trận 17 sản phẩm, các sửa sai G00, nguồn chính thức, ánh xạ vào KT-114–121). Báo cáo chi tiết vẫn ở [PR #47 — G00 thẩm định hai lần](https://github.com/cavoixanh638/kho-tri-thuc/pull/47) và G01–G17 tại [PR #30–#46](https://github.com/cavoixanh638/kho-tri-thuc/pulls), **chưa merge**. Đọc bản tổng hợp trước; khi cần claim riêng thì mở PR nguồn theo đúng luồng.
5. Quyết định tại tài liệu này là **đề xuất ưu tiên**, không được tự suy rằng đã có lệnh cho phép cài thư viện, bật AI trả phí, thay DB/Drive hay deploy.

## 3. Hiện trạng bắt buộc tôn trọng

| Lĩnh vực | Đã có trên main/bằng chứng | Chưa được tuyên bố hoàn thành |
| --- | --- | --- |
| Nguồn gốc, Drive, dữ liệu | Django 5.2 + PostgreSQL + Google Drive; Item/Source/Asset/StorageLocation, CaptureEvent bất biến, idempotent Job; live proof một số nguồn và restore trong `CURRENT_STATE.md` | Restore đại diện 10.000 mục/hàng trăm GB, đổi Client/Project, quyền/giới hạn Google, MP4 trên mọi thiết bị |
| Văn bản | `Item.note`; `ItemScreen.tsx` có `Textarea`; `KnowledgeText.tsx` dùng react-markdown/remark-gfm; `ReadKnowledgeService` phân biệt authored và derived | **Chưa có editor Live Preview hoặc split editor**, AI không được nói đã có |
| Phân loại | `Topic.parent`, `ItemTopic` nhiều-nhiều; `OrganizationService`, `RelatedItem` với lý do và user-pinned | Giao diện backlinks đầy đủ, đa view cùng Item ID, chất lượng 10.000 mục |
| Nguồn/timestamp | `DerivedContent.source_locator` JSON và `KnowledgeReading.tsx` đang hiển thị page/section + nút mở minh họa | Chưa có flow bấm dẫn chứng → seek **đúng trang/giây** trên video gốc |
| Android capture | PWA `manifest.webmanifest` **đã có `share_target`**, `sharedCapture.ts` và `CaptureScreen.tsx` đã parse dữ liệu chia sẻ | **Android Share Target chạy trên thiết bị thật NOT_RUN**, offline ACK/queue không được giả PASS |
| Tình trạng nghiên cứu | 17/17 PR riêng chỉ sửa báo cáo; G00 PR #47 đã kiểm lại nguồn và sửa sai | Chưa chạy tài khoản demo/trả phí của 17 sản phẩm, không có benchmark nhà cung cấp |
| Kiểm thử frontend | `apps/web/package.json`: `npm test` hiện chạy **duy nhất** `tests/ui.test.mjs` | Test mới ở file khác **không tự chạy** qua `npm test` nếu chưa cập nhật runner; mọi PR phải chạy tường minh và báo rõ |

## 4. Thứ tự và phân quyền — tránh AI ghi đè nhau

| Mã task | Độ ưu tiên trong **hệ thống** | Nhánh đề nghị | Phạm vi file được sở hữu | Trạng thái tài liệu |
| --- | --- | --- | --- | --- |
| **KT-114** [Readiness & safety](KT-114-READINESS.md) | **CORE GATE, làm/đo trước phát hành** | `codex/kt-114-readiness` | `tools/readiness/*`, `evals/readiness/*`, báo cáo QA; chỉ *đọc* core services | READY_TO_ASSIGN / NOT_RUN |
| **KT-115** [Markdown Editor](KT-115-EDITOR.md) | UX-P0 (PoC cô lập) | `codex/kt-115-editor` | `apps/web/src/ItemScreen.tsx`, component editor mới, tests KT-115 | READY_TO_ASSIGN / NOT_RUN |
| **KT-116** [Locator PDF/Audio/Video](KT-116-LOCATORS.md) | UX-P0 (PoC; phải tôn trọng CORE) | `codex/kt-116-source-locators` | `KnowledgeReading.tsx`, viewer/locator adapter mới, API read/source nếu thiết yếu, tests KT-116 | READY_TO_ASSIGN / NOT_RUN |
| **KT-117** [Quick Capture/Android](KT-117-QUICK-CAPTURE.md) | **CORE Android + UX-P0** | `codex/kt-117-quick-capture` | `CaptureScreen.tsx`, `sharedCapture.ts`, manifest, tests KT-117 | READY_TO_ASSIGN / DEVICE_NOT_RUN |
| **KT-118** [Multi-view Library](KT-118-LIBRARY-VIEWS.md) | UX-P1 (sau gate dữ liệu/UX-P0) | `codex/kt-118-library-views` | `LibraryScreen.tsx`, view/filter component và tests KT-118 | READY_TO_ASSIGN / NOT_RUN |
| **KT-119** [Related/backlinks](KT-119-RELATED.md) | UX-P1 | `codex/kt-119-related` | `ItemOrganization.tsx`/related adapter, API related khi cần, tests KT-119 | READY_TO_ASSIGN / NOT_RUN |
| **KT-120** [AI suggestions/review](KT-120-AI-REVIEW.md) | UX-P1 **CONDITIONAL** | `codex/kt-120-ai-review` | isolated suggestion API/UI; model+provider **chưa chốt** | HOLD until approved |
| **KT-121** [Templates/type fields](KT-121-TEMPLATES.md) | UX-P2 **CONDITIONAL** | `codex/kt-121-templates` | template UI/config, không thay schema lõi | HOLD until approved |
| **KT-122** [Folder Explorer: thư mục + ghi chú chung một cây](KT-122-FOLDER-EXPLORER.md) | **CORE UX / HIGH — phát hiện thiếu** | `codex/kt-122-folder-explorer` (base PR #57) | `KnowledgeExplorer*`, placement API, LibraryScreen/KnowledgeTree adapt, tests KT-122 | SPEC_READY / CODE_NOT_RUN |
| **KT-123** [Note → Note cấu trúc cha–con](KT-123-NOTE-HIERARCHY.md) | **CORE UX / HIGH — phát hiện thiếu** | `codex/kt-123-note-hierarchy` (base PR #57; phụ thuộc KT-122 UI) | directed hierarchy model/service/API; note outline UI/relations; tests KT-123 | SPEC_READY / CODE_NOT_RUN |
| **KT-124** [Wiki-link, TOC, Ctrl+K](KT-124-NAVIGATION-LINKING.md) | CORE UX HIGH | `codex/kt-124-review` (base PR #57, except KT130) | Read task; code ownership/fixtures/validation in task file | SPEC_READY / NOT_RUN |
| **KT-125** [Saved smart collections, properties](KT-125-SMART-COLLECTIONS.md) | CORE UX HIGH | `codex/kt-125-review` (base PR #57, except KT130) | Read task; code ownership/fixtures/validation in task file | SPEC_READY / NOT_RUN |
| **KT-126** [Web clipper, highlight, source quote](KT-126-CLIPPER-HIGHLIGHTS.md) | CORE UX HIGH | `codex/kt-126-review` (base PR #57, except KT130) | Read task; code ownership/fixtures/validation in task file | SPEC_READY / NOT_RUN |
| **KT-127** [Markdown vault export/import](KT-127-PORTABLE-VAULT.md) | CORE DATA / UX | `codex/kt-127-review` (base PR #57, except KT130) | Read task; code ownership/fixtures/validation in task file | SPEC_READY / NOT_RUN |
| **KT-128** [End-to-end user journeys](KT-128-USER-JOURNEY-ACCEPTANCE.md) | RELEASE QA | `codex/kt-128-review` (base PR #57, except KT130) | Read task; code ownership/fixtures/validation in task file | SPEC_READY / NOT_RUN |
| **KT-129** [Organization evidence review](KT-129-ORGANIZATION-REVIEW.md) | CONDITIONAL | `codex/kt-129-review` (base PR #57, except KT130) | Read task; code ownership/fixtures/validation in task file | SPEC_READY / NOT_RUN |
| **KT-130** [Deferred features with reopening conditions](KT-130-DEFERRED-RESEARCH.md) | REGISTER ONLY | `codex/kt-130-review` (base PR #57, except KT130) | Read task; code ownership/fixtures/validation in task file | SPEC_READY / NOT_RUN |

**Lỗ hổng phát hiện ngày 20/11/2026 sau PR #57:** hệ thống **đã có Topic.parent và ItemTopic**, nhưng `KnowledgeTree` chỉ hiển thị nhánh, ghi chú vẫn ở danh sách độc lập; `RelatedItem(similar)` không phải quan hệ cha–con giữa các Item. Trên chiều rộng <=1100px, cây đang mặc định thu gọn trong nút “Mở mục lục”. **KT-118 nhiều view không đồng nghĩa KT-122 mixed explorer.** Phải thực hiện KT-122/123 trước khi báo UX folder như Obsidian hoàn thành; không sửa PR #57 hoặc merge nếu chưa có quyền. Mã của KT-122/123 viết **trên nhánh từ PR #57** để không nhân đôi patch, PR target nhánh integration; G00 nối sau khi review.

**G00 rà soát lần ba:** [Ma trận 38 nhóm năng lực](G00-FEATURE-TRACEABILITY.md) cho thấy các task KT-114–121 **không bao phủ hết 17 nghiên cứu**; cần KT-122/123/124/125/126/127 cho hành trình tri thức, KT-128 để kiểm thử UX xuyên task; KT-129 có điều kiện, KT-130 là sổ những việc được hoãn có lý do. Mỗi Codex phải đọc HEAD PR #57 còn OPEN, làm PR mới target integration và **không sửa đồng thời file chung, không merge/deploy**.

**Ngoài phạm vi / hoãn:** fork nguyên Obsidian/AFFiNE, Canvas/whiteboard lớn, graph DB, B2/R2 làm chính, Redis, bot meeting, OCR/ASR hàng loạt, dịch vụ SaaS notes làm database, MCP mới chỉ vì nghiên cứu. Không nhân đôi công cụ ghi họp độc lập.

**Xung đột:** `apps/web/tests/ui.test.mjs`, `apps/web/tests/ui-entry.tsx`, `apps/web/package.json`, `apps/web/src/api.ts`, `apps/web/src/styles.css`, `docs/CURRENT_STATE.md` là **tài sản tích hợp chung**: các luồng song song chỉ đọc hoặc mở PR riêng đề nghị thay, **không cùng sửa**. Dùng file test riêng `tests/kt115-*.test.mjs`, v.v.; nếu chưa được runner tự phát hiện, chạy `node --test tests/<tên-file>.test.mjs` và ghi rõ. Có thể dùng fixture/harness riêng. G00 xử lý những thay đổi chung khi tích hợp theo thứ tự.

## 5. Các lỗi nghiên cứu G00 đã sửa, bắt buộc không lặp

- Capacities **đã có audio record + transcription + summary cho Pro từ 11/2026** (release 71/73), nhưng không có bằng chứng AI tự hiểu toàn video/MP4. Trước đây G00 ghi sai, báo cáo G13 vốn đúng. Không dựa trên câu sai cũ.
- Reflect Open có **Windows/Linux bản build chưa ký thử nghiệm**, không có Android; bài blog khi ra mắt tháng 7 không phản ánh mọi bản cập nhật.
- Mem.ai công bố lịch đóng dịch vụ 15/01/2027; không chọn làm backend/integration.
- Superpowered không còn phát bộ cài ở trang tải; không suy từ đó rằng toàn doanh nghiệp đã đóng.
- Gemini Notebook API/MCP ở trạng thái Public Preview; Coda/Superhuman Docs có những hạng mục beta; đối chiếu GA/beta/gói và thời điểm.
- Granola không giữ audio gốc cho replay; YouTube metadata/transcript không đồng nghĩa đã phân tích video frame; không thể tuyên bố video đã lưu Drive chỉ vì URL có trong DB.
- Điểm của 17 sản phẩm là **đánh giá từ tài liệu**, không phải phép đo PoC. Các phép cộng trong báo cáo có thể khớp nhưng **không đủ để chọn đổi kiến trúc**.

## 6. Hợp đồng báo cáo bắt buộc mỗi AI

- Bắt đầu từ HEAD main và checkpoint mới nhất; phân biệt nguồn gốc, data fixture, tính năng đã có/chưa có, NOT_RUN và tác động của task.
- Chạy format/lint/test unit bị ảnh hưởng, backend PostgreSQL/migration/worker khi liên quan, `npm test` và `npm run build` khi sửa frontend; test mới phải chạy được độc lập, không dừng ở docs/plan. Nếu không có runtime hoặc thiết bị thật, ghi **NOT_RUN**, không báo PASS giả.
- Tự kiểm diff chỉ gồm file sở hữu; branch + commit + push + PR **không merge**. Đưa trong PR: **Code SHA, Tested SHA, PASS/FAIL/NOT_RUN, môi trường, lệnh, evidence, data safety, rollback, cách tích hợp**. Chưa có PR => báo rõ chưa hoàn thành GitHub.
- **Không sửa đồng thời `CURRENT_STATE.md` khi nhiều luồng chạy.** Ghi trạng thái trong PR/checkpoint task; G00 cập nhật duy nhất `CURRENT_STATE.md` sau kiểm chứng/merge. Không sửa hợp đồng chung để tự nâng trạng thái.
- Không đụng dữ liệu cá nhân, production Drive, OAuth token, billing hay deploy khi chưa có quyền rõ. Không force-push, không xóa hay ghi đè thay đổi agent khác. Không merge nghiên cứu G01–G17/G00 PR #47 trong khi triển khai.
