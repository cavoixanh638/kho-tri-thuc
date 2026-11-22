# HIỆN TRẠNG THỰC TẾ — KHO TRI THỨC

## Chú ý — GitHub snapshot mới ngày 22/11/2026 (chưa tích hợp vào main)

**Nguồn:** [bảng kiểm toán đối chiếu](operations/RELEASE_READINESS_20261122.md), kiểm trực tiếp GitHub HEAD, PR, Actions. Phần dưới đây giữ **lịch sử đã kiểm trên Windows/main**, không xóa thông tin trước đó.

- `main` HEAD lúc đối chiếu: `1f64f50147b9f92177b3e04f787a36fc673736d6`.
- `PR #79` (nhiều luồng), `PR #81` (Unified Inbox), `PR #82` (Gemini model), `PR #84` (Gemini OCR) đều **OPEN/DRAFT/UNMERGED/NOT_DEPLOYED**. Các CI Actions báo SUCCESS cho từng candidate nhưng không tương đương live PASS. HEAD chính xác tại checkpoint ở bảng audit.
- Candidate PR84 **ahead 232 / behind 26** so với `main` tại checkpoint; cần đối chiếu 26 commit và tập migration trước khi lập release candidate thực.
- **P08 browser** trong Actions #44971811417: `9 PASS / 0 FAIL / 0 BLOCKED / 4 NOT_RUN`, `status=NOT_RUN` dù step đặt continue-on-error. P15 fatal `Cannot focus .research-clipper select`; release UAT **chưa PASS**.
- **Chất lượng và vận hành chưa chốt:** P16 86 truy vấn chưa chạy PostgreSQL benchmark; P17 10k metadata fixture **không** là 10k video tải thật; YouTube/TikTok chưa có đường tải video gốc tương ứng Facebook; Gemini OCR 394 backend tests theo CI nhưng inference thật/CER/WER/provider ngân sách **NOT_RUN**.
- **NEXT:** P0-01 reconcile branch và plan; P0-02 sửa P15 và làm gate fail-closed, kiểm J3/J6B/J8/J9; P0-03 kiểm media/search/group bằng dữ liệu có phép và gold. Android **DEFERRED theo người dùng**.

Đây là checkpoint nguồn mã/CI, **không thay đổi** trạng thái đã triển khai Windows hay khẳng định PR Draft đã vận hành thật.


**Ngày checkpoint:** 20/11/2026 (Asia/Ho_Chi_Minh).
**Nguồn kiểm chứng:** Windows đã chạy candidate `8daa02bf7b8a45c41b65bfc2387d686beb27f5b8` của [PR #29](https://github.com/cavoixanh638/kho-tri-thuc/pull/29), từ main `8828663`; [CI #44566379899](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44566379899) PASS. Kết quả live/restore/connector ở phần KT-113 dưới đây. Khi tiếp tục luôn kiểm GitHub head/merge/runtime thực tế, không coi SHA trong tài liệu là bất biến. Khảo sát [QLVB_System_new](https://github.com/cavoixanh638/QLVB_System_new) chỉ là tham khảo thiết kế.
**Mục đích:** nơi duy nhất ghi **đã hoàn thành điều gì thật**. Roadmap là kế hoạch/điều kiện PASS, không là chứng cứ chạy thật.

## 1. Tình trạng tổng quát

### KT-113 — cây thư viện và text từ liên kết, Windows LIVE_PASS

Nhánh `codex/kt-113-knowledge-tree`, candidate `8daa02b`: Topic.parent có loại và
thứ tự, kiểm owner/chu trình, lọc cả nhánh và đếm bài duy nhất. Một bài thuộc
nhiều nhánh mà không sao chép nội dung. Windows có **hai kho con, 19 nhánh,
năm bài** đã xếp: bốn bài công khai trong Công nghệ và vận hành, Reel trong
Thể thao/Golf. Nhãn Sách/Bộ sách là loại bộ sưu tập, không khẳng định xuất bản.
Lệnh tổ chức chạy lại không thêm Item; note, giờ nhận, lịch sử gốc và hash MP4
khớp backup trước đổi. [Kết quả live](operations/hierarchy-live-results.json).

ReadKnowledgeService ưu tiên bài người dùng, nếu chưa có thì dùng text trích
hiện hành. Đã gắn tài liệu Django vào bài có sẵn, trích 24.257 ký tự, retry giữ
cùng Event và note không đổi. Nguồn/media nằm sau phần đọc; nút gạch chân mở
minh họa. Bộ đếm tương tác bị loại khỏi Source.metadata và tiền tố title/description,
giữ nguyên lịch sử đầu vào. Browser Windows đã kiểm đọc bài, text nguồn mở được,
nhãn Đã xếp nhóm, mở minh họa và lọc nhánh PostgreSQL đúng một bài.
[Kết quả UI](operations/hierarchy-ui-results.json).

ASR **cục bộ/offline**, faster-whisper/base/int8 + PyAV16.1.0: Reel có 11 đoạn
tiếng Anh tự động, tìm được bằng text, nhãn cần rà soát. Processor v2 giới hạn
mốc cuối 59,542 giây trong clip gốc; không tự dịch/biên tập thành kiến thức đã
kiểm chứng. Model/cache/raw transcript ngoài Git. Giới hạn 128MiB/600s, suy luận
420s; giữ text cũ khi kết quả rỗng/lỗi. Chưa đo chất lượng tiếng Việt hay nhiều
video. Bản xuất schema3 bỏ body lặp; Drive full readback SHA/version **5/5 PASS**,
cùng năm ID và file duy nhất, connector metadata/fetch **5/5 PASS** có đường dẫn
nhánh và transcript v2/cảnh báo. [Connector](operations/hierarchy-connector-results.json).

Backup manifest v3 giữ loại/thứ tự/cha-con/quan hệ. Sao lưu thật lên Drive và
bản sao Windows riêng, tải lại đúng hash, restore **15 collection** vào DB mới
ở cluster kiểm thử, không restore đè production. Cây/note/quan hệ không rỗng,
mapping MP4 đọc lại khớp hash, OAuth/session rỗng. Kiểm bổ sung restored JSON
locators v2 và metadata không còn counter PASS.
[Backup](operations/hierarchy-backup-live-results.json),
[chi tiết restore](operations/hierarchy-restored-details-results.json).
Tool nhận v1/v2; chưa thử một lượt restore v2 thật rồi migrate lên v3.

**211 backend test PASS**, FFmpeg rõ đường dẫn không skip; **19 frontend test
PASS/build PASS**, migration check/lint/diff PASS. Chín backup unit test PASS,
ba ca integration trong discovery Windows skip theo môi trường; CI đã chạy
backup/restore thật trên Compose. Các agent rà soát độc lập tree, UI, export,
ASR; root tích hợp/triển khai. [Hướng dẫn](operations/KNOWLEDGE_TREE.md).
Rollback ưu tiên revert mã UI/worker và giữ schema mở rộng; không migrate ngược
production làm mất loại/thứ tự nhánh. Backup trước đổi giữ riêng trên Windows.
Android, playback seek theo đoạn, chất lượng phân nhóm tự động trên corpus cá
nhân và ASR đa nguồn chưa nghiệm thu; không gọi toàn hệ thống DONE.

### KT-112 — văn bản là nội dung chính, Windows LIVE_PASS

Nhánh `codex/kt-112-text-first-knowledge`: nội dung `Item.note` đọc bằng Markdown
trong mục Tri thức, nguồn/media đặt sau; màn hình gửi mặc định văn bản, thư viện
có trích đoạn. Tệp `.md`/`.markdown` UTF-8 được trích vào DerivedContent để tìm.
Renderer react-markdown/remark-gfm bỏ HTML nguồn và URL ngoài HTTP(S), ảnh chỉ
mở khi bấm; 17 test frontend/build PASS. Chín test backend extraction/import
trên PostgreSQL thử PASS, gồm Unicode, CRLF, import không trùng và giữ chỉnh sửa.
Lệnh `import_knowledge_notes` có preview và `--apply`, nhập bài công khai qua
CaptureService, có opt-in export. Bốn bài thật ở `docs/knowledge/`, khác bốn
fixture giả trong pilot. [PR #28](https://github.com/cavoixanh638/kho-tri-thuc/pull/28):
candidate `0c3f6ea` đã [CI #44546796615](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44546796615)
PASS trước triển khai. Sau backup riêng được verify, Windows build/restart/check
PASS; nhập bốn bài công khai qua CaptureService, không tạo Asset giả. Chạy lại
lệnh giữ bốn Item/Event, không thêm lượt; thư viện có năm mục tại nghiệm thu.
SearchService tìm được cả bốn, Drive full readback SHA/version 4/4 PASS,
connector metadata/fetch 4/4 PASS trong ChatGPT_Index của ứng dụng.
Candidate UI `0e2c3c7` đã [CI #44548249840](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44548249840)
PASS: bỏ tiêu đề lặp và trạng thái trích nguồn không áp dụng cho bài văn bản.
Browser thật sau reload đã thấy bốn bài và Reel, đọc bảng/link/heading, mở editor
giữ đúng Markdown rồi Hủy không submit, mặc định gửi văn bản. Screenshot giữ riêng;
nghiệm thu ở viewport hiện tại, chưa thay kiểm Android hay upload `.md` qua UI.
Catalogue video, Asset/StorageLocation và CaptureEvent gốc khớp backup trước đổi.
Reel vẫn chưa có transcript/bài biên soạn; không suy nội dung lời nói.
[Báo cáo](operations/text-first-live-results.json), [hướng dẫn](operations/TEXT_KNOWLEDGE.md).

| Hạng mục | Trạng thái đã kiểm tra | Diễn giải |
| --- | --- | --- |
| Thiết kế phạm vi/kiến trúc | **DECIDED / DOCS_ONLY** | Baseline **v4.7**: Google Drive, PostgreSQL, Django+Ninja, React+Mantine, một worker; CaptureEvent bất biến, auto-group và RelatedItem đã được đặc tả |
| Chuẩn bị bố trí repo và AI routing | **DOCS_PREPARED** | Có `REPOSITORY_LAYOUT.md`, `docs/README.md`, `CURRENT_STATE.md` và liên kết từ README/AGENTS/roadmap trong commit chuẩn bị repository này |
| Ứng dụng React/Django | **PASS (tiếp nhận và thư viện)** | Có đăng nhập, gửi URL/chữ, biên nhận, lịch sử, xem/chỉnh sửa và khôi phục Item. API upload nhận file vào staging bền vững |
| Văn bản/Markdown trong kho | **LIVE_PASS (KT-112)** | Bốn bài công khai đã nhập vào thư viện chính, đọc/chỉnh Markdown và tìm theo text; media/nguồn đặt sau. Import replay không trùng, Drive/connector đọc được bốn bản xuất. Không dùng fixture riêng thay dữ liệu nhìn thấy |
| PostgreSQL/Docker Compose | **PASS (Ubuntu CI)** | PostgreSQL 18, volume riêng, migration Django và rollback/reapply migration `sessions` đã chạy |
| Kết nối Google Drive | **LIVE_VIDEO_PASS** | Reel thực do người dùng gửi đã đi qua UI tiếp nhận, worker tải và upload Drive; đọc lại toàn bộ MP4 khớp SHA-256, thumbnail có cache, một Asset/một CaptureEvent. TXT/PNG/PDF adapter smoke trước đó PASS. UI multipart với file người dùng, đổi client/project và Drive preview playback còn NOT_RUN |
| Thumbnail PDF/ảnh/video | **PASS (tích hợp KT-010)** | Renderer/caching, 8 EXIF Orientation, API riêng tư và upload hook qua test; xem mốc vận hành bên dưới |
| Video, trích chữ và FTS | **PARTIAL / TESTED** | Facebook Reel công khai đã tải MP4 và lưu Drive thật. Fetch web, parser nhẹ và hai GIN/search đã nối. YouTube/TikTok, transcript/ASR, benchmark PDF và đánh giá phân nhóm thực còn mở |
| **Nhận URL/text và giữ giờ** | **PASS (bản tích hợp)** | Session/CSRF, ACK sau transaction, retry/gửi lại, lịch sử và giao diện qua proxy đã được kiểm thử |
| ChatGPT Drive pilot / xuất tri thức / MCP | **CONTROLLED_PILOT_PASS_WITH_SEARCH_LIMITATION** | Một Reel người dùng và pilot riêng 8 Item có kiểm soát đã đọc qua connector; 9 câu hỏi đủ bằng chứng sau một fallback từ khóa. Note/Project/subtitle cập nhật cùng ID. Chưa phải corpus cá nhân, ChatGPT UI độc lập hay native Docs; chưa xây MCP |
| Backup/restore dữ liệu | **LIVE_PASS (phạm vi đã thử)** | Drive tải lại đúng hash, bản sao Windows riêng, restore DB mới đủ 15 collection gồm mapping KnowledgeExport; không restore đè production. Nhóm/note không rỗng và client-project khác còn chưa thử |
| Triển khai Windows/Linux/Android | **WINDOWS_PASS / ANDROID_NOT_RUN** | Native Windows phục vụ loopback cổng 8009, PostgreSQL 18 riêng, start/stop/restart đã chạy. CI Linux Compose PASS. Android/HTTPS còn NOT_RUN |
| Test/CI runtime | **PASS (phạm vi bản tích hợp)** | Backend 179 test: 178 PASS/1 skip PATH, riêng 11 thumbnail test chạy FFmpeg rõ đường dẫn đều PASS; frontend 14 PASS/build PASS. PR #22–25 đã CI PASS trước merge; [CI #44529471636](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44529471636). Chi tiết và giới hạn ở các mốc bên dưới |

**Không được gọi các dòng NOT_STARTED/NOT_RUN là PASS.** Tạo kế hoạch không có nghĩa đã có môi trường hoặc dữ liệu dùng thật.

## 2. Kết quả khảo sát QLVB được kế thừa ở cấp thiết kế

- Đã đọc cấu trúc `QLVB_System_new/main`: `apps/`, `packages/`, `db/migrations/`, `docs/`, `evals/`, `tests/`, `tools/` và các thư mục legacy/coordination.
- Tiếp thu **bốn lớp thông tin** (source record, source artifact, derived artifact, operational state), ID độc lập với tên hiển thị, provenance, tách tests/evals và quy tắc một nguồn tài liệu chuẩn.
- Kế thừa **nguyên tắc** an toàn Git/data, không sao chép mã nguồn hoặc schema cụ thể từ QLVB. Không sao chép Node ingestion, pgvector, legacy shims, orchestrator hay workboard nhiều tác nhân.
- Những quyết định về bố trí dữ liệu được quy định trong [REPOSITORY_LAYOUT.md](REPOSITORY_LAYOUT.md); **v4.7 bổ sung nghiệp vụ CaptureEvent và tự tổ chức**, không đổi Google Drive/PostgreSQL/Django.

## 3. Checkpoint công việc

| Mã / mốc | Trạng thái | Bằng chứng cần có tiếp theo |
| --- | --- | --- |
| Chuẩn bị repository trước KT-001 | **DOCS_PREPARED** | Commit GitHub chứa tài liệu định tuyến/cấu trúc/hiện trạng và readback kiểm tra nội dung; không phải test ứng dụng |
| KT-001 — Scaffold | **PASS (kiểm thử)** | [PR #1](https://github.com/cavoixanh638/kho-tri-thuc/pull/1), [Actions](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44320811635), [hướng dẫn chạy](operations/LOCAL_SETUP.md) |
| KT-002 — Schema | **PASS (kiểm thử)** | [PR #2](https://github.com/cavoixanh638/kho-tri-thuc/pull/2), [Actions](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44324868660) |
| KT-003–005 — Drive OAuth/lưu file | **MOCK_VERIFIED** | [PR #3](https://github.com/cavoixanh638/kho-tri-thuc/pull/3), [Actions](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44327959927), chưa thử Drive thật |
| KT-006/007/011 — UI, worker, tiếp nhận | **PASS (bản tích hợp)** | [PR #5](https://github.com/cavoixanh638/kho-tri-thuc/pull/5), [CI](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44333379367) |
| KT-008–010 — Vận hành/thumbnail | **PASS (CI và mô phỏng)** | PR #16, CI #44339513395. OAuth/Drive thật còn NOT_RUN |
| KT-101–KT-110 — Gate B | **IN_PROGRESS / PARTIAL** | [PR #17](https://github.com/cavoixanh638/kho-tri-thuc/pull/17) đã tích hợp web/parser/search/nhóm/RelatedItem/PWA. Video, benchmark PDF, đánh giá thực và Android chưa nghiệm thu |
| KT-201–KT-204 — Gate C | **NOT_STARTED** | Pilot ChatGPT được kiểm chứng theo workspace thực tế |
| Gate D — nâng cấp | **NOT_STARTED / CONDITIONAL** | Chỉ khởi động khi có trigger từ thực tế và người dùng giao |

## 4. Việc cần làm tiếp và các thông tin còn thiếu

**KT-001 đã kiểm chứng.** Nhánh `codex/kt-001-scaffold`, [PR #1](https://github.com/cavoixanh638/kho-tri-thuc/pull/1), SHA mã nguồn `5fe1def5b8feb0b04d9e6bd481b7ccab0996da75`. GitHub Actions chạy trên Ubuntu 24.04, SHA merge thử `1f3bd587b221eedc9f470f380d9a4fe1b60ba10d`. [Kết quả CI](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44320811635)

- **Ubuntu CI:** build Docker Compose và khởi động PostgreSQL 18, Django, worker và frontend. Django check/makemigrations check đều qua. Đã rollback rồi áp lại migration `sessions.0001_initial`. Hai test API (200 khi có DB và 503 khi lỗi DB) đều qua. Worker kết nối được DB. Bản build và API qua proxy frontend trả về đúng.
- **Windows:** chạy ứng dụng trên loopback với PostgreSQL 18.4 và Node.js 24.15.0 trong thư mục tạm. `pip check`, migration xuôi/ngược, 2 test, worker, Vite build, trang HTML, bundle JS và API qua proxy đều qua.
- **Chưa chạy:** Docker Desktop trên Windows, Android/PWA và tích hợp bên ngoài. Kiểm thử KT-001 dùng DB thử riêng. Rollback thay đổi bằng PR revert nếu đã merge.

### KT-002 đã kiểm chứng

- Nhánh `codex/kt-002-schema`, [PR #2](https://github.com/cavoixanh638/kho-tri-thuc/pull/2), commit mã nguồn `8c79923cae354e9d0b6d289cf81ca864fad19557`.
- [GitHub Actions #44324868660](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44324868660) PASS trên Ubuntu 24.04/PostgreSQL 18. Trên Windows/PostgreSQL 18.4, chạy migrations xuôi, rollback toàn bộ schema ứng dụng bằng `migrate catalog zero`, áp lại, `makemigrations --check` và 10 test đều qua.
- Ràng buộc đã thử gồm giờ lưu đầu tiên, nội dung/giờ Event bất biến, khóa request theo người dùng và kênh, cặp mục liên quan duy nhất, đúng trạng thái file đã xác minh và khóa Job. Luồng API tiếp nhận và Drive thực nằm ở các task kế tiếp.
- Rollback triển khai cần sao lưu trước khi đảo schema nếu đã có dữ liệu; ca CI dùng database dùng một lần.

### KT-003–005 đã kiểm thử bằng Drive mô phỏng

- [PR #3](https://github.com/cavoixanh638/kho-tri-thuc/pull/3), nhánh `codex/kt-003-005-drive`, commit mã nguồn `c51d39f3d3719a03760944145e9cf22b15c30cc6`. [GitHub Actions #44327959927](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44327959927) PASS.
- 19 test PostgreSQL 18.4 trên Windows, `makemigrations --check`, Ruff format/lint và CI trên Ubuntu 24.04. Đã thử PKCE, CSRF, `invalid_grant`, mã hóa token, kiểm checksum và tình huống upload đã ghi nhưng phản hồi mất. Chưa có OAuth consent/upload/đọc lại trên tài khoản Google thật.
- Sau khi có dữ liệu thật, sao lưu trước khi rollback migration DriveAccount. Cấu hình bí mật của runtime nằm ngoài GitHub source.

### Luồng triển khai song song

Chín đầu việc dùng mốc `c51d39f`. Chat điều phối nối router, cấu hình, worker và chạy kiểm thử tích hợp. Mỗi luồng ghi checkpoint riêng và tự kiểm phần mình.

| Hạng mục | Nhánh làm việc | Phạm vi |
| --- | --- | --- |
| KT-006 UI | `codex/kt-006-ui` | Giao diện tiếp nhận, lịch sử, thư viện và cài đặt |
| KT-006 API | `codex/kt-006-library-api` | Session, CSRF, thư viện, chi tiết và phân quyền |
| KT-007 | `codex/kt-007-worker` | Claim, lease, retry, xử lý lại sau restart |
| KT-011 | `codex/kt-011-capture` | Transaction tiếp nhận, idempotency, lịch sử |
| KT-008 | `codex/kt-008-backup` | Dump, manifest và khôi phục |
| KT-010 | `codex/kt-010-thumbnails` | Thumbnail PDF/ảnh, 8 hướng EXIF |
| KT-101 | `codex/kt-101-source-fetch` | Truy xuất nguồn an toàn, metadata và văn bản |
| KT-104 | `codex/kt-104-search` | Chỉ mục và tìm kiếm tiếng Việt |
| KT-103/110 | `codex/kt-103-110-organization` | Tự gán nhóm và lưu mục liên quan |

### KT-006/007/011 và API upload đã kiểm chứng

- [PR #5](https://github.com/cavoixanh638/kho-tri-thuc/pull/5), commit mã `f8ceec9915b239a7423041d9014c3b02ea805b50`. 52 tests PostgreSQL 18.4 trên Windows, migration check và Ruff đều PASS.
- [GitHub Actions #44333379367](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44333379367) PASS qua Docker Compose. Biên nhận sau commit, ghi chú tiếng Việt nguyên văn, retry cùng key, hai lần gửi URL cùng Item, và upload multipart thử nghiệm qua Vite proxy. Drive thật chưa kết nối; receipt upload chỉ xác nhận đã tiếp nhận vào staging.
- Worker PostgreSQL đã thử lease, SKIP LOCKED và restart. Tệp chỉ được xác nhận sau khi Drive adapter kiểm chứng. CI chạy dữ liệu thử; sau khi có dữ liệu thật cần sao lưu trước khi rollback migration. Màn hình upload tệp đã kiểm Chromium với API mô phỏng ở `0678592`. Sao lưu và thumbnail đang tích hợp.

### KT-008–010 đã kiểm chứng trong bản vận hành

- [PR #16](https://github.com/cavoixanh638/kho-tri-thuc/pull/16), SHA mã nguồn `44aec79b00756487015c961f835939bee68ed974`, [GitHub Actions #44339513395](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44339513395) PASS.
- Native Windows kiểm renderer và API bằng PostgreSQL 18.4. Lượt full suite 76 test có 1 SKIP FFmpeg, kiểm riêng thêm 18 ca OAuth/upload/khôi phục đều PASS. CI cài FFmpeg trong image, chạy suite, smoke và tạo/verify/restore bản sao vào DB mới.
- Dữ liệu gốc, timestamp và ID được giữ qua restore. Reconcile phân biệt file đã trash và thiếu quyền, làm stale nội dung dẫn xuất khi file đổi. Thumbnail có cache volume riêng, hiển thị lazy-load và helper khôi phục cache có kiểm SHA-256.
- Bản chạy Windows được người dùng chọn. Docker Desktop chưa có trên máy, đang chuẩn bị launcher native sử dụng Python/Node/PostgreSQL 18 đã có. OAuth client/consent, mở file Drive thật, đổi host/client/project và Android vật lý còn NOT_RUN.

### Bản tích hợp thư viện và native Windows

- [PR #17](https://github.com/cavoixanh638/kho-tri-thuc/pull/17), SHA mã `c9896e5b11b11bc7a4ebc845d9b8c6aabaae6060`. [CI #44344447208](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44344447208) PASS với 136 test trên PostgreSQL 18, build frontend, migration/rollback, smoke qua proxy và backup/verify/restore vào database mới.
- Có hai GIN Item/DerivedContent, tìm dấu/không dấu, ghi chú tối đa 100.000 ký tự, lọc nhóm/chưa phân loại, CRUD nhóm và quan hệ manual/pinned. Worker tổ chức lại sau chỉnh sửa; API nội dung dẫn xuất có provenance, phân trang và giới hạn preview. Retry không tạo CaptureEvent mới.
- Tại mốc PR #17, fetch web kiểm URL/redirect/IP và giới hạn tải; PDF/DOCX/XLSX/text được trích trong tiến trình có timeout. PDF dùng pypdf làm baseline tạm, chưa chốt KT-102. Tải video Facebook được bổ sung ở PR #18 bên dưới; chưa có transcript video thực.
- Đánh giá tổ chức chỉ có 40 fixture tổng hợp. Ngưỡng lexical bảo thủ đã điều chỉnh bằng tập này; chưa đo trên 30–50 Item thực do con người gán nhãn. Không suy rộng kết quả tổng hợp thành chất lượng dữ liệu cá nhân.
- PWA có manifest/icon và GET share target. Chromium fixture smoke trước đó đã kiểm các kích thước 390/768/1440; Android thiết bị thật và HTTPS còn NOT_RUN.
- Người dùng chọn máy Windows này. Bản native tại `%LOCALAPPDATA%\KhoTriThuc`, mã checkout từ GitHub; Python 3.13, Node 24, PostgreSQL 18.4 riêng ở loopback 54329, Waitress và worker ở loopback 8009. Build/migrate/check/start/stop/restart thành công, [runbook](operations/WINDOWS_SETUP.md). Sau mốc này đã tiếp nhận Reel thực theo PR #18.
- Google Cloud đã tạo app OAuth và Web client theo xác nhận của người dùng, callback loopback chính xác, scope `drive.file`, một test user. JSON đã nạp vào runtime, người dùng đăng nhập ứng dụng và xác nhận consent Google. UI Cài đặt hiển thị Đã kết nối. Không đưa email/credential/JSON lên Git.
- Cloud vẫn ở External/Testing nên refresh token Drive có hạn 7 ngày theo chính sách Google. Đã có luồng Kết nối lại; chuyển Production còn mở trước vận hành lâu dài, chưa tự công bố ứng dụng.
- Live Drive smoke từ runtime Windows PASS trên ba mẫu TXT UTF-8 tiếng Việt (85 byte), PNG (83 byte), PDF (429 byte). Dùng DriveStorage thật, refresh token mới, upload resumable, SHA-256/size/MIME, tải lại đúng byte và gọi save lần nữa giữ file ID. Mẫu đã chuyển vào Thùng rác, transaction catalog rollback. [Kết quả khử thông tin riêng](operations/drive-live-results.json), runner `tools/drive_smoke.py`. Đây là test adapter thực, chưa thay thế nghiệm thu UI/multipart/worker bằng file người dùng hoặc tải lớn/video.
- Mã/tài liệu/test lưu trên GitHub. Database, OAuth secret, staging và cache runtime nằm ngoài folder đồng bộ Drive. Rollback mã bằng PR revert; sao lưu database trước khi đảo migration trên môi trường có dữ liệu thật.

### KT-101 — Facebook Reel thật đã lưu Drive

- [PR #18](https://github.com/cavoixanh638/kho-tri-thuc/pull/18), mã được chạy trên Windows `e04a3211875df4308acf4290da95313cbe2f45b5`. 164 test PostgreSQL 18.4 trên Windows và [CI #44437313933](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44437313933) PASS, không có test skip. CI kiểm migration/rollback, build/proxy smoke và backup/restore. Lint/format các file Python thay đổi và diff check PASS.
- Người dùng gửi Reel qua UI, server nhận lúc 07:54 ngày 19/11/2026. Worker cũ lấy được metadata. Đã bổ sung downloader `yt-dlp==2026.10.26` chạy tiến trình riêng không cookie, giới hạn 120 giây/128 MiB, chỉ cho HTTPS Facebook và CDN được phép trên IP công khai. ffprobe kiểm MP4 có hình/tiếng trước khi stage fsync và enqueue upload. Lease fencing, retry và UUID Asset ổn định được kiểm thử.
- Upload nhiều chunk bộc lộ lỗi `RedirectMissingLocation`: custom httplib2 transport xử lý `308 Resume Incomplete` thành redirect. Đã tái hiện bằng test transport thật với phản hồi 200/308/200, sửa dùng `googleapiclient.http.build_http()` và kiểm lại toàn bộ suite. Chunk 1 MiB, request timeout 30 giây, một lượt upload có budget 360 giây. Chỉ log loại lỗi, không log URL/header/token.
- [Báo cáo thực đã khử thông tin riêng](operations/facebook-live-results.json) PASS, tạo bằng `tools/verify_drive_item.py` đã chạy thật. MP4 18.394.669 byte, H.264 720×1280 + AAC, ffprobe đo 59,645375 giây. SHA-256 `3fd6884f8d6fdfd6099c9378b70878c6ba7f7fceb4f4da989b2840587a1d6ca5` khớp metadata Drive và toàn bộ tệp tải lại. `source_fetch=done`, `asset_storage=verified`, cả bốn job done, thumbnail đã cache. Một Asset, một file Drive không trashed và một CaptureEvent; fingerprint đầu vào/giờ nhận đầu giữ nguyên qua các lần retry. Báo cáo không chứa URL nội dung, Drive ID, account ID hoặc token.
- Mã và báo cáo nằm trên GitHub. MP4 gốc nằm trên Drive, staging đã được dọn sau verify; runtime/config và token vẫn ngoài Git. [Runbook Windows](operations/WINDOWS_SETUP.md) có media tools được kiểm SHA-256. Chỉ thử một Reel công khai progressive; chưa xác nhận mọi Reel, video riêng tư, YouTube/TikTok, video lớn hoặc phát preview Drive.

### Đợt hoàn thiện sau PR #18 — đang thực hiện

Người dùng giao tiếp tục các phần còn lại tới khi hoàn thành hệ thống, giữ mã và kết quả trên GitHub. Baseline của đợt là `e04bfd1f6026f2fc238c03cf68d1c589dc0a47b8`. Không làm lại các phần đã PASS và không coi các cổng thiết bị/tài khoản chưa thử là hoàn tất.

| Chủ sở hữu / nhiệm vụ | Nhánh | Điều kiện bàn giao |
| --- | --- | --- |
| PDF worker — KT-102 | `codex/kt-102-pdf-evidence` | 20–30 PDF tiếng Việt thật, so ba parser, thời gian/RAM/Unicode/thứ tự đọc/locator, giấy phép và quyết định có bằng chứng |
| Recovery worker — KT-008/009 | `codex/kt-008-live-recovery` | Snapshot dữ liệu thật, backup Drive+copy độc lập, tải lại/restore vào DB mới, mở đúng file đã ánh xạ; không restore lên production |
| UI worker — KT-108 | `codex/kt-108-processing-ui` | Trạng thái worker tự cập nhật, không mất bản chỉnh sửa, polling có giới hạn/hủy; kiểm thử và build, thiết bị thật ghi riêng |
| Điều phối — KT-201/202E và tích hợp | `codex/kt-202e-knowledge-pilot` | Xuất per-item có version/opt-in/retry cùng file, pilot đọc bằng connector, tích hợp CI và cập nhật Windows |

Connector Drive ban đầu dùng tài khoản khác và không đọc được thư mục ứng dụng.
Sau khi người dùng kết nối đúng tài khoản, Settings của phiên Codex đã xác nhận
đúng Primary; connector metadata/search/fetch bản xuất Markdown thật đều PASS.
[Bằng chứng khử riêng tư](operations/drive-connector-live-results.json). Android
được người dùng chủ động để sau, hoàn thiện Windows trước.

Các agent dừng do workspace hết credits; điều phối tiếp nhận phần đang dở.
KT-102 có 60 lượt đo và PDFium fallback, PR #20 đã CI PASS/merge/deploy Windows.
KT-108 PR #19 đã CI PASS/merge/deploy, 12 test frontend PASS.
Recovery [PR #21](https://github.com/cavoixanh638/kho-tri-thuc/pull/21) head
`9f020094a71872dc2c22cd1601f3351ccf3343d2` đã [CI #44498590620](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44498590620)
PASS, merge `fe315ceb115653fd9f03cfb03858c67071677686` theo yêu cầu tiếp tục.
Backup/restore dữ liệu thật đã PASS theo xác nhận người dùng; xem báo cáo trên main.

Các lỗi CUA trước đó đã được vượt qua bằng phiên giao diện mới và quan sát ảnh.
Không thay OAuth scope/chia sẻ thư mục để sửa kết nối. Browser tích hợp hiện đã
mở ứng dụng Windows để kiểm panel cuối, đang chờ người dùng đăng nhập phiên này.

KT-202E có model KnowledgeExport, migration `storage.0003`, snapshot renderer và
6 test PostgreSQL tạm **PASS** (ghi chú/giờ bất biến, version, active/stale,
phân quyền nhóm, transcript rỗng, cắt có cảnh báo và chặn credential-like input).
`makemigrations --check` PASS. Snapshot không opt-in hoặc ghi Drive khi được đọc.
Đã bổ sung adapter TXT/Markdown, worker lease/idempotence, API opt-in/owner/CSRF,
panel từng Item và backup manifest v2 có mapping KnowledgeExport, đọc v1.
13 backend pilot test và 14 frontend JSDOM test/build PASS. Full backend 179 test:
178 PASS/1 skip FFmpeg do PATH; đã chạy lại riêng 11 thumbnail test với FFmpeg
đúng đường dẫn, tất cả PASS. Backup v2/compat v1/roundtrip 11 test PASS. Migration
0003/0004 xuôi/ngược/áp lại, check migration và lint/format module mới PASS.
**DEPLOYED/SINGLE_ITEM_LIVE_PASS**: [PR #22](https://github.com/cavoixanh638/kho-tri-thuc/pull/22)
head `b4d1a656cb6aef6be9926560b655dfd7c4690d04` đã [CI #44508674959](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44508674959)
PASS và merge. Windows đã chạy `843642e4046ac741f0aa5b5ecb1fd217dcfe11b3`:
backup riêng trước migration, storage 0003/0004, build/restart/check đều PASS;
API/bundle mới 200. [Báo cáo Windows](operations/knowledge-windows-results.json).

Sau khi người dùng xác nhận cụ thể payload/đích ChatGPT_Index, live export đã
**PASS** bằng verifier `151b4d5`: Markdown 929 byte → TXT 909 byte → Markdown,
đọc lại toàn bộ đúng SHA-256, đúng source/exported version, chỉ một file hoạt động.
Tắt/thu hồi rồi bật lại giữ cùng ID; CaptureEvent/giờ nhận và danh mục original
không đổi. Mục Reel được giữ bật Markdown sau thử. [Báo cáo](operations/knowledge-export-live-results.json).
Đây là nghiệm thu một Item người dùng giao; chưa thay pilot 5–10 Item đại diện.
Backup sau export thật cũng PASS: đủ 15 collection và **1 KnowledgeExport** giữ
nguyên mapping/version khi restore vào DB mới; file MP4 gốc đọc lại đúng hash.
[Báo cáo backup có mapping bản xuất](operations/knowledge-backup-live-results.json).
Connector hiện **đã đọc được chính file đã verify**: metadata MIME Markdown,
search đúng tên trả một kết quả, fetch có nguồn/tệp gốc/checksum/giờ nhận và cảnh
báo thiếu transcript. Đã kiểm thêm TXT đọc được qua connector, cùng file ID,
trả lại Markdown/full readback PASS; fullText bằng cụm nguồn đã biết trả đúng một
file. Chưa suy thành mọi format hoặc mọi truy vấn đều được đọc.
[PR #23](https://github.com/cavoixanh638/kho-tri-thuc/pull/23), head `8c3ab2b`,
[CI #44520958931](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44520958931)
PASS và merge `21fb7d3`; Windows source đã fast-forward tới cùng SHA, API 200.
PR #24 head `b8c128e` đã [CI #44528296946](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44528296946)
PASS và merge `d703b57`; Windows source đồng bộ và health vẫn PASS. Mã ứng dụng
không đổi sau PR #22, bản xuất cuối giữ bật Markdown. PR #25 đã CI #44529471636
PASS và merge `4b57891`, Windows source đồng bộ tới cùng SHA. Sau khi người dùng
đăng nhập, browser tích hợp đã kiểm trực quan panel và bấm Đồng bộ lại: trạng thái
chuyển Đang chờ đồng bộ rồi tự về Đã đồng bộ, giờ đồng bộ tiến lên và liên kết
Drive giữ nguyên. Markdown, tệp gốc đã xác minh và cảnh báo thiếu transcript
hiển thị đúng; bố cục ở kích thước browser hiện tại đọc được. Đây không phải
nghiệm thu Android hay ma trận viewport. [Báo cáo UI](operations/knowledge-ui-live-results.json).
Runner `tools/verify_knowledge_export.py` có `--preview` không gọi Drive và
`--exercise` đã chạy sau xác nhận; kiểm MD/TXT/MD, full readback, unique file,
thu hồi/bật lại cùng ID và giữ CaptureEvent/Item/original. Toàn văn preview,
credential, backup và ID riêng không đưa lên Git. [Hợp đồng](operations/KNOWLEDGE_EXPORT.md).

**Việc tiếp theo:** tích hợp từng nhánh khi có mã/test/bằng chứng, giữ các cổng chưa đạt có trạng thái rõ. Chất lượng nhóm cần tập thực và người dùng đánh giá, không thay bằng fixture tự soạn. Upload Reel người dùng đã giao hoàn tất, không cần gửi lại liên kết.

**Chưa xác minh:** UI multipart với file người dùng, Drive đổi client-project, upload lớn/quota, preview playback; Docker Windows; host 24/7/HTTPS; Android; nguồn video khác và transcript; chất lượng PDF toàn văn/đa nguồn; chất lượng nhóm trên tập thực; corpus cá nhân và ChatGPT consumer UI độc lập/native Docs. Không hỏi lại các quyết định đã chốt; chỉ nêu blocker khi bắt đầu tác vụ phụ thuộc thông tin đó.

### KT-201/202E/202 — pilot riêng 8 Item và 9 câu hỏi

- Người dùng giao tự chọn cách check. Dùng bốn nguồn tài liệu chính thức có HTTP
  200/anchor kiểm lại và bốn fixture tự soạn có nhãn; không thêm fixture vào
  production. Cluster PostgreSQL khác, folder Drive `KIEM THU KT202` riêng;
  nguồn production read-only, fingerprint catalogue trước/sau không đổi.
- Chuẩn bị `6aedd4b`, cập nhật `356fb2f`: 4 Markdown/4 TXT, full readback SHA và
  version 8/8 PASS, chỉ tám tệp hoạt động. Sửa note, đổi tên project trên hai Item,
  thay subtitle phiên bản, force retry, TXT/MD/TXT và thu hồi/bật lại cùng ID PASS.
  CaptureEvent/giờ nhận giữ nguyên. OAuth bind trong bộ nhớ, không chép token
  vào DB thử. [Bằng chứng Drive](operations/knowledge-pilot-live-results.json).
- Connector đọc 8/8 trước/sau, nhận đúng note/project/subtitle mới. Truy vấn đầu
  tìm đúng 8/9; câu Q5 hụt, fallback `kiểm kê` tìm đúng. Chín câu trả lời do
  nghiệm thu viết có bằng chứng trong bản fetch, locator trang/đoạn và cảnh báo
  thiếu transcript; không tính đây là benchmark mù hoặc phiên ChatGPT UI độc lập.
  [Kết quả từng câu](operations/knowledge-pilot-connector-results.json).
- Năm safety test Windows PASS và thêm vào CI; lint/format/JSON/diff check PASS.
  [Corpus, cách chạy và giới hạn](../evals/knowledge/README.md). Native Docs,
  chất lượng phân nhóm trên dữ liệu cá nhân và parser/ASR không được suy là PASS.
  Rollback: revert tools/evidence, không đổi schema hay mã ứng dụng đang phục vụ.

## 5. Quy tắc cập nhật trạng thái

### KT-108 — đã tích hợp và cập nhật Windows

- Nhánh `codex/kt-108-processing-ui`, baseline `e04bfd1`. Item/thư viện polling
  khi còn xử lý, giới hạn 10 phút, backoff và dừng sau ba lỗi; hủy request khi
  chuyển trang/unmount, dừng khi hết quyền. Item mới từ server không xóa draft.
- Windows Node 24: `npm test` **12/12 PASS**, `npm run build` **PASS**.
  Có kiểm StrictMode/share Unicode/chống gửi trùng, retry, phiên hết hạn và
  thay đổi trạng thái/tệp. JSDOM không render layout: các ca width 390/768/1440
  chỉ kiểm DOM, **không phải browser/device acceptance**.
- Agent dừng do workspace hết credits; điều phối sửa harness (fonts/RAF,
  request thật sự in-flight và hợp đồng body capture), chạy lại suite PASS.
- [PR #19](https://github.com/cavoixanh638/kho-tri-thuc/pull/19), head
  `285e9db76fa2fc77b25e0fa67fce7fbc86978cd6`, [CI #44495738623](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44495738623)
  PASS trước merge. Windows đã cập nhật main `ccc0a333c087ee1687a9d0df7de4b6326532a253`,
  npm ci/build/restart PASS; HTML, bundle mới và API 200. Không đổi schema/OAuth.
  [Bằng chứng](operations/windows-processing-results.json). Browser tương tác mới
  chưa kiểm lại; Android được người dùng để sau.

### KT-102 — mốc đo 20 PDF / ba parser

- Mã đo `ec21b59`, nhánh `codex/kt-102-pdf-evidence`, [báo cáo](../evals/pdf/README.md).
  Đã chạy 60 lượt subprocess trên Windows: cả ba parser 20/20 không lỗi/timeout,
  kiểm 42 anchor trên trang vật lý và 20 probe thứ tự đọc bằng ảnh render.
- Cả ba tìm 40/42 anchor; pypdf/PDFium đúng thứ tự 16/20, PyMuPDF 19/20.
  Đo lại cả process tree để sửa sai số RAM của Windows venv launcher. Có nguồn
  license chính thức, chưa đưa PyMuPDF vào runtime. Lint/format/diff check PASS.
- Mẫu cùng một tổ chức và nhiều trang đầu: chưa phải CER/WER/toàn văn/bảng/scan.
  Giữ pypdf đầu tiên, PDFium renderer KT-010 và fallback text khi primary lỗi/rỗng;
  encrypted không bypass, có processor/version riêng. 6 test extraction PostgreSQL
  tạm PASS, gồm PDFium thật và dữ liệu tổng hợp. Fallback đã deploy sau CI bên dưới.
  KT-102 còn nguồn khác/nghiệm thu toàn văn, không ghi toàn task DONE.
  Raw PDF/text/render ngoài Git.

- [PR #20](https://github.com/cavoixanh638/kho-tri-thuc/pull/20), head
  `c2cfe37f7e829dc5ee4b0bee90648bb6ab8760e4`, [CI #44497632923](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44497632923)
  PASS trước merge. Windows đã cập nhật `eab593d4e00f2a541c263ff2a0ede5e21acbfe6b`,
  restart/API 200/PostgreSQL running PASS. Fallback đã được triển khai.

### Cổng tài khoản và nghiệm thu còn chờ

- Người dùng yêu cầu hoàn thiện Windows trước; Android để sau. Connector đúng
  Primary đã đọc được Markdown và TXT của một Item thực; UI đồng bộ lại PASS.
  Pilot có kiểm soát 8 Item/9 câu đã chạy theo mốc trên; corpus cá nhân và native
  Docs vẫn NOT_RUN, không ghi toàn hệ thống DONE.
- Recovery mã `760be80` ở `codex/kt-008-live-recovery`: 7 test archive/Drive giả
  PASS. Người dùng đã xác nhận payload notes/URLs/hashed authentication và nơi
  lưu, sau yêu cầu của automatic approval review. Live backup/restore **PASS**:
  [báo cáo](operations/backup-live-results.json), ZIP trên Drive tải lại đúng SHA,
  restore 14 collection vào DB mới, OAuth/session rỗng. Mapping file gốc mở được,
  MP4 tải lại khớp SHA. Private Windows copy đã kiểm 12 file dưới thư mục backups.
  Không restore lên production. Dữ liệu live chưa có nhóm/note không rỗng và
  chưa kiểm client/project khác, không suy fixture thành live.
- KT-202E đã merge/deploy theo PR #22; live, connector MD/TXT và UI một Item PASS,
  pilot riêng tám Item PASS có giới hạn tìm kiếm. Mã/checkpoint/báo cáo khử riêng
  tư lưu trên GitHub. Bước tiếp theo Windows có thể kiểm multipart bằng file
  công khai/tự soạn trong môi trường riêng; corpus cá nhân cần dữ liệu được phép.
  Không tự xuất thêm nội dung kho hoặc tạo dữ liệu giả vào production.

- Mỗi lần hoàn tất task ghi **ID, SHA commit, branch/PR, test thực sự đã chạy + kết quả, điều chưa test, blocker và một bước kế tiếp**. Không tự thăng trạng thái thành PASS khi chưa có bằng chứng.
- Kiểm tra lại GitHub `main` và diff hiện hành trước mỗi lần ghi. Nếu nhiều AI làm song song, phân file/branch không chồng chéo. Không cần dựng workboard/dispatcher nếu chưa thực sự có nhiều đầu việc đồng thời.
- Không tự bổ sung lịch sử nhiều trang. Dữ liệu đo chi tiết có thể lưu dưới `evals/` khi bắt đầu đo; `CURRENT_STATE.md` giữ bản tóm tắt và liên kết bằng chứng.
- **SHA chính xác của commit hiện hành phải lấy từ GitHub ở thời điểm đọc**, không chép một SHA đã cũ thành trạng thái vĩnh viễn trong tài liệu này.

## 6. Handoff AI sau 17 nghiên cứu (20/11/2026) — CHỈ TÀI LIỆU, KHÔNG PHẢI CODE

- Trên **main**, bộ giao việc độc lập [KT-114–KT-121](workstreams/notes-ux-20261120/INDEX.md) được tạo kèm file task, tiêu chí nghiệm thu/rollback, phân quyền sở hữu và prompt ngắn. Liên kết đã thêm ở `AGENTS.md`, README, MASTER_PLAN, ARCHITECTURE_AND_DATA, CAPTURE_AND_ORGANIZE, ROADMAP_AND_TESTS và REPOSITORY_LAYOUT.
- **G01–G17:** nghiên cứu 17 ứng dụng có báo cáo ở PR #30–#46. **G00:** kiểm lại và sửa sai hai tài liệu trong [PR #47](https://github.com/cavoixanh638/kho-tri-thuc/pull/47), **chưa merge**; nội dung tổng hợp được đưa vào kế hoạch/gate và bộ giao việc. Không xem các PR nghiên cứu là code đã triển khai.
- Đính chính quan trọng: Capacities đã có audio record/transcription/summary trong gói Pro từ 11/2026 (không phải coming soon); Reflect Open có Windows/Linux experimental unsigned, Android chưa có; split Markdown editor **chưa có**; `share_target` PWA **đã có** nhưng Android thật chưa test; `DerivedContent.source_locator` có nhưng flow PDF/video jump-to-timestamp còn thiếu; không áp quan hệ `1 Source = 1 Asset`.
- **Trạng thái mới (DOCS_ONLY):** KT-114 CORE readiness, KT-115 editor, KT-116 locator, KT-117 capture Android, KT-118 multi-view, KT-119 related UI, KT-120 AI review (HOLD), KT-121 templates (HOLD) đều **IMPLEMENTATION_NOT_RUN**. **Không có test runtime mới chạy trong việc cập nhật tài liệu này; CI/Windows/Drive PASS cũ vẫn chỉ có phạm vi ghi ở các mục trước.**
- **Gate còn mở:** Drive/backup-restore/permission khác Client/Project, 10.000+ Item/hàng trăm GB, nhiều nguồn FB/TikTok/YT và Android thật; không cho UX-P0 thay thế các kiểm tra CORE. Nếu không có thiết bị/tài khoản/quyền/sandbox, ghi **NOT_RUN**, không tuyên bố không lỗi.
- **Quy trình cập nhật sau này:** AI được giao KT cụ thể tạo nhánh/PR và ghi Code SHA/Tested SHA/PASS/FAIL/NOT_RUN trong PR; G00 chỉ sửa `CURRENT_STATE.md` **sau khi kiểm chứng và tích hợp**, tránh nhiều AI ghi đè cùng file. Không tự merge PR #30–#47 khi chưa có lệnh.

## 7. Rà soát khoảng trống File Explorer / cha–con bài (20/11/2026) — CHỈ SPEC

**Đã kiểm code** trên `main` và candidate tích hợp [PR #57](https://github.com/cavoixanh638/kho-tri-thuc/pull/57), nhưng **chưa chạy thử ứng dụng thực với thay đổi KT-122/123**:

- `Topic.parent` + `knowledge_tree.py` có folder→folder, cycle/depth check; `ItemTopic` M:N có folder→note. Giao diện `KnowledgeTree.tsx` **chỉ hiển thị Topic**, không trộn các Item thành note con trong cây; `ItemOrganization.tsx` bắt người dùng mở note và chọn MultiSelect để đổi folder.
- PR #57 (OPEN/UNMERGED) có `LibraryViews` List/Table/Card/Timeline, `RelatedSources` có backlinks/gợi ý. **Không có directed Item→Item structural hierarchy**: model `RelatedItem` duy nhất theo `item_a<item_b` dùng tương quan chứ không phải cha–con; `Topic.node_kind=book/chapter` là nhãn folder, không phải nội dung cha–con.
- Giao diện PR #57 ở viewport <=1100px mặc định thu gọn cây sau nút “Mở mục lục kho tri thức”. Người dùng dễ tưởng không có folder; ngay cả khi mở cũng chưa thấy notes xen kẽ.
- Tài liệu mới: [KT-122](workstreams/notes-ux-20261120/KT-122-FOLDER-EXPLORER.md) mixed explorer và [KT-123](workstreams/notes-ux-20261120/KT-123-NOTE-HIERARCHY.md) cấu trúc note parent–child, đã bổ sung ở [INDEX](workstreams/notes-ux-20261120/INDEX.md), ROADMAP, ARCHITECTURE, MASTER_PLAN, AGENTS. **Chỉ có spec/code chưa làm: `SPEC_READY / IMPLEMENTATION_NOT_RUN`.**
- **Gate không được giả PASS:** UAT giao diện cây lẫn ghi chú, drag-drop/keyboard, note parent cycle/ownership, 10.000 Item lazy-loading, restore relations/backup, Android. Khi Codex làm, phải test đúng HEAD mới, có SHA/PASS/FAIL/NOT_RUN; PR target branch tích hợp PR #57, không tự merge. **Không thay CURRENT_STATE phần live trước đó** và không chạm dữ liệu production.

## 8. G00 kiểm toán lại 17 nghiên cứu thành trải nghiệm sản phẩm (20/11/2026) — DOCS_ONLY

- **Lỗi quản trị đã phát hiện:** 17 báo cáo có nhiều ý tưởng chi tiết nhưng G00 chưa quản lý **feature traceability**; các task KT-114–121 thiếu File Explorer mixed, Item cha/con, wiki autocomplete, command palette, saved smart collections, clip source-quote và Markdown vault portable. Người dùng phải chủ động nhắc yêu cầu folder dù Topic.parent đã có, vì UI chỉ render Topic.
- **Đã cập nhật tài liệu trên main:** [Ma trận 38 nhóm năng lực G00](workstreams/notes-ux-20261120/G00-FEATURE-TRACEABILITY.md) → [INDEX task](workstreams/notes-ux-20261120/INDEX.md) → [KT-124–KT-130](workstreams/notes-ux-20261120/INDEX.md); KT-122/123 đã có trước. MASTER_PLAN, ARCHITECTURE_AND_DATA, ROADMAP_AND_TESTS và AGENTS đồng bộ ranh giới. Không được gọi 38 nhóm đã phát hành.
- **Mã thực:** PR #57 `codex/notes-ux-integration` có candidate KT-114–121, CI reported PASS nhưng vẫn **OPEN/UNMERGED** lúc kiểm. `LibraryViews` không phải dynamic saved views; `ItemSuggestionPanel` là **manual review PoC** (provider OFF); `SourceLinks` URL không phải quoted clip; `KnowledgeExportPanel` per-item không phải full vault; `RelatedSources` có backlinks từ Markdown chứ không có full wiki authoring.
- **Task mới:** KT-122–KT-127/KT-129 = `SPEC_READY / IMPLEMENTATION_NOT_RUN`; KT-128 = `RELEASE_UAT_NOT_RUN`; KT-130 = `REGISTERED_DEFERRED`. Không thay test runtime cũ/không nâng PASS cho task mới.
- **Gate người dùng:** folder+note→note cha/con→wiki links/backlink→clip source→smart folder/search→export/import, kiểm thực tế Windows/Android và Drive khi được phép, bảo toàn Item UUID/Event/Asset/Source/notes. CI unit green **không tự chứng nhận** trải nghiệm này.
- **Tính năng hoãn có lý do:** whiteboard, OCR/voice/semantic, AI scoped research, full local-first offline sync; sổ KT-130 có nguồn Gxx và điều kiện mở lại, tránh “nghiên cứu xong rồi mất”.
- **Quy tắc:** AI được giao task mới base HEAD PR57, PR riêng target integration, G00 review/test/ghép (không đồng sửa chung file), **không merge/deploy** khi chưa có chấp thuận; Code SHA/Tested SHA/PASS/FAIL/NOT_RUN. Bản cập nhật này chỉ sửa tài liệu, không chạy bộ test runtime mới.