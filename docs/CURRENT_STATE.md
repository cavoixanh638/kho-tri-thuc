# HIỆN TRẠNG THỰC TẾ — KHO TRI THỨC

**Ngày checkpoint:** 19/11/2026 (Asia/Ho_Chi_Minh).
**Nguồn kiểm chứng:** `main` tại `3d63c0f85d47a8685f60ab971d8212cd7ad30bce`, bản video `codex/kt-101-facebook` tại `e04a3211875df4308acf4290da95313cbe2f45b5`, GitHub Actions và runtime Windows thực tế. Khảo sát [QLVB_System_new](https://github.com/cavoixanh638/QLVB_System_new) chỉ là tham khảo thiết kế.
**Mục đích:** nơi duy nhất ghi **đã hoàn thành điều gì thật**. Roadmap là kế hoạch/điều kiện PASS, không là chứng cứ chạy thật.

## 1. Tình trạng tổng quát

| Hạng mục | Trạng thái đã kiểm tra | Diễn giải |
| --- | --- | --- |
| Thiết kế phạm vi/kiến trúc | **DECIDED / DOCS_ONLY** | Baseline **v4.7**: Google Drive, PostgreSQL, Django+Ninja, React+Mantine, một worker; CaptureEvent bất biến, auto-group và RelatedItem đã được đặc tả |
| Chuẩn bị bố trí repo và AI routing | **DOCS_PREPARED** | Có `REPOSITORY_LAYOUT.md`, `docs/README.md`, `CURRENT_STATE.md` và liên kết từ README/AGENTS/roadmap trong commit chuẩn bị repository này |
| Ứng dụng React/Django | **PASS (tiếp nhận và thư viện)** | Có đăng nhập, gửi URL/chữ, biên nhận, lịch sử, xem/chỉnh sửa và khôi phục Item. API upload nhận file vào staging bền vững |
| PostgreSQL/Docker Compose | **PASS (Ubuntu CI)** | PostgreSQL 18, volume riêng, migration Django và rollback/reapply migration `sessions` đã chạy |
| Kết nối Google Drive | **LIVE_VIDEO_PASS** | Reel thực do người dùng gửi đã đi qua UI tiếp nhận, worker tải và upload Drive; đọc lại toàn bộ MP4 khớp SHA-256, thumbnail có cache, một Asset/một CaptureEvent. TXT/PNG/PDF adapter smoke trước đó PASS. UI multipart với file người dùng, đổi client/project và Drive preview playback còn NOT_RUN |
| Thumbnail PDF/ảnh/video | **PASS (tích hợp KT-010)** | Renderer/caching, 8 EXIF Orientation, API riêng tư và upload hook qua test; xem mốc vận hành bên dưới |
| Video, trích chữ và FTS | **PARTIAL / TESTED** | Facebook Reel công khai đã tải MP4 và lưu Drive thật. Fetch web, parser nhẹ và hai GIN/search đã nối. YouTube/TikTok, transcript/ASR, benchmark PDF và đánh giá phân nhóm thực còn mở |
| **Nhận URL/text và giữ giờ** | **PASS (bản tích hợp)** | Session/CSRF, ACK sau transaction, retry/gửi lại, lịch sử và giao diện qua proxy đã được kiểm thử |
| ChatGPT Drive pilot / xuất tri thức / MCP | **NOT_STARTED** | Chưa có thử nghiệm trực tiếp với tài khoản/workspace |
| Backup/restore dữ liệu | **PASS (dữ liệu thử)** | Dump/manifest cùng snapshot và khôi phục vào database mới đã chạy trên Windows và Docker Compose. Drive thật/bản sao thật vẫn cần xác minh |
| Triển khai Windows/Linux/Android | **WINDOWS_PASS / ANDROID_NOT_RUN** | Native Windows phục vụ loopback cổng 8009, PostgreSQL 18 riêng, start/stop/restart đã chạy. CI Linux Compose PASS. Android/HTTPS còn NOT_RUN |
| Test/CI runtime | **PASS (164 test Windows/CI)** | Bản video/Drive tại `e04a321` đã chạy toàn suite trên PostgreSQL 18.4 và [CI #44437313933](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44437313933), migrations/build/smoke và backup/restore đều PASS |

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

Connector Drive search không thấy thư mục ứng dụng, `files.get` đúng ID trả 404 trong khi runtime vẫn đọc được. Settings xác nhận connector dùng tài khoản khác. Người dùng yêu cầu mở kết nối lại; đã mở Connect another account tới màn hình Google chọn tài khoản, chờ người dùng hoàn tất. Không lưu account ID/credential vào Git. Android được người dùng chủ động để sau, hoàn thiện Windows trước.

Các agent dừng do workspace hết credits; điều phối tiếp nhận phần đang dở.
KT-102 có 60 lượt đo và PDFium fallback, PR #20 đã CI PASS/merge/deploy Windows.
KT-108 PR #19 đã CI PASS/merge/deploy, 12 test frontend PASS.
Recovery [PR #21](https://github.com/cavoixanh638/kho-tri-thuc/pull/21) head
`9f020094a71872dc2c22cd1601f3351ccf3343d2` đã [CI #44498590620](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44498590620)
PASS, merge `fe315ceb115653fd9f03cfb03858c67071677686` theo yêu cầu tiếp tục.
Backup/restore dữ liệu thật đã PASS theo xác nhận người dùng; xem báo cáo trên main.

Lần tiếp tục: người dùng đã mở khóa Windows nhưng CUA vẫn không đọc được AX,
screenshot đen và launch báo handler chưa ready. Browser integration cũng không
có trong chat. Connector `files.get` thư mục ứng dụng vẫn lỗi. Không coi đây là
file mất hoặc tự đổi OAuth scope/chia sẻ thư mục. Tiếp tục backend/UI/test xuất
tri thức độc lập; pilot connector và native Google Docs vẫn cần kiểm thực tế.

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
**DEPLOYED/LIVE_ACCEPTANCE_PENDING**: [PR #22](https://github.com/cavoixanh638/kho-tri-thuc/pull/22)
head `b4d1a656cb6aef6be9926560b655dfd7c4690d04` đã [CI #44508674959](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44508674959)
PASS và merge. Windows đã chạy `843642e4046ac741f0aa5b5ecb1fd217dcfe11b3`:
backup riêng trước migration, storage 0003/0004, build/restart/check đều PASS;
API/bundle mới 200. [Báo cáo Windows](operations/knowledge-windows-results.json).

Lượt live export bị automatic approval review từ chối trước khi thực thi vì cần
xác nhận riêng payload và đích ChatGPT_Index. Đã tạo preview **chỉ cục bộ** 929
byte cho Reel người dùng giao (0 note/nhóm/DerivedContent), gửi xác nhận xuất một
mục sang tài khoản Drive runtime. Chưa có opt-in hoặc bản xuất Drive ở mốc này.
Runner `tools/verify_knowledge_export.py` có `--preview` không gọi Drive và
`--exercise` chỉ chạy sau xác nhận; kiểm MD/TXT/MD, full readback, unique file,
thu hồi/bật lại cùng ID và giữ CaptureEvent/Item/original. Toàn văn preview,
credential, backup và ID riêng không đưa lên Git. [Hợp đồng](operations/KNOWLEDGE_EXPORT.md).

**Việc tiếp theo:** tích hợp từng nhánh khi có mã/test/bằng chứng, giữ các cổng chưa đạt có trạng thái rõ. Chất lượng nhóm cần tập thực và người dùng đánh giá, không thay bằng fixture tự soạn. Upload Reel người dùng đã giao hoàn tất, không cần gửi lại liên kết.

**Chưa xác minh:** UI multipart với file người dùng, Drive đổi client-project, upload lớn/quota, preview playback; Docker Windows; host 24/7/HTTPS; Android; nguồn video khác và transcript; benchmark PDF 3 thư viện; chất lượng nhóm trên tập thực; ChatGPT pilot 5–10 Item. Không hỏi lại các quyết định đã chốt; chỉ nêu blocker khi bắt đầu tác vụ phụ thuộc thông tin đó.

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

- Người dùng yêu cầu hoàn thiện Windows trước; Android để sau. Connector Drive
  đang dùng tài khoản khác runtime; đã mở Connect another account tới màn hình
  chọn Google, chờ người dùng đăng nhập/cấp quyền. Chưa có pilot đọc thành công.
- Recovery mã `760be80` ở `codex/kt-008-live-recovery`: 7 test archive/Drive giả
  PASS. Người dùng đã xác nhận payload notes/URLs/hashed authentication và nơi
  lưu, sau yêu cầu của automatic approval review. Live backup/restore **PASS**:
  [báo cáo](operations/backup-live-results.json), ZIP trên Drive tải lại đúng SHA,
  restore 14 collection vào DB mới, OAuth/session rỗng. Mapping file gốc mở được,
  MP4 tải lại khớp SHA. Private Windows copy đã kiểm 12 file dưới thư mục backups.
  Không restore lên production. Dữ liệu live chưa có nhóm/note không rỗng và
  chưa kiểm client/project khác, không suy fixture thành live.
- KT-202E đã merge/deploy theo PR #22; nghiệm thu live và connector vẫn còn mở
  theo đoạn trên. Mã/checkpoint và các báo cáo khử riêng tư lưu trên GitHub.

- Mỗi lần hoàn tất task ghi **ID, SHA commit, branch/PR, test thực sự đã chạy + kết quả, điều chưa test, blocker và một bước kế tiếp**. Không tự thăng trạng thái thành PASS khi chưa có bằng chứng.
- Kiểm tra lại GitHub `main` và diff hiện hành trước mỗi lần ghi. Nếu nhiều AI làm song song, phân file/branch không chồng chéo. Không cần dựng workboard/dispatcher nếu chưa thực sự có nhiều đầu việc đồng thời.
- Không tự bổ sung lịch sử nhiều trang. Dữ liệu đo chi tiết có thể lưu dưới `evals/` khi bắt đầu đo; `CURRENT_STATE.md` giữ bản tóm tắt và liên kết bằng chứng.
- **SHA chính xác của commit hiện hành phải lấy từ GitHub ở thời điểm đọc**, không chép một SHA đã cũ thành trạng thái vĩnh viễn trong tài liệu này.
