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

**Việc tiếp theo:** tiếp tục các cổng chưa nghiệm thu của Gate B/C. Upload Reel người dùng đã giao hoàn tất, không cần gửi lại liên kết.

**Chưa xác minh:** UI multipart với file người dùng, Drive đổi client-project, upload lớn/quota, preview playback; Docker Windows; host 24/7/HTTPS; Android; nguồn video khác và transcript; benchmark PDF 3 thư viện; chất lượng nhóm trên tập thực; ChatGPT pilot 5–10 Item. Không hỏi lại các quyết định đã chốt; chỉ nêu blocker khi bắt đầu tác vụ phụ thuộc thông tin đó.

## 5. Quy tắc cập nhật trạng thái

- Mỗi lần hoàn tất task ghi **ID, SHA commit, branch/PR, test thực sự đã chạy + kết quả, điều chưa test, blocker và một bước kế tiếp**. Không tự thăng trạng thái thành PASS khi chưa có bằng chứng.
- Kiểm tra lại GitHub `main` và diff hiện hành trước mỗi lần ghi. Nếu nhiều AI làm song song, phân file/branch không chồng chéo. Không cần dựng workboard/dispatcher nếu chưa thực sự có nhiều đầu việc đồng thời.
- Không tự bổ sung lịch sử nhiều trang. Dữ liệu đo chi tiết có thể lưu dưới `evals/` khi bắt đầu đo; `CURRENT_STATE.md` giữ bản tóm tắt và liên kết bằng chứng.
- **SHA chính xác của commit hiện hành phải lấy từ GitHub ở thời điểm đọc**, không chép một SHA đã cũ thành trạng thái vĩnh viễn trong tài liệu này.
