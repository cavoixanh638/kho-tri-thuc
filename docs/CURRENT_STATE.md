# HIỆN TRẠNG THỰC TẾ — KHO TRI THỨC

**Ngày checkpoint:** 18/11/2026 (Asia/Ho_Chi_Minh).
**Nguồn kiểm chứng:** baseline tài liệu trên `main` (`a223ed0`), thay đổi KT-001 trên nhánh `codex/kt-001-scaffold` và khảo sát read-only [QLVB_System_new](https://github.com/cavoixanh638/QLVB_System_new).
**Mục đích:** nơi duy nhất ghi **đã hoàn thành điều gì thật**. Roadmap là kế hoạch/điều kiện PASS, không là chứng cứ chạy thật.

## 1. Tình trạng tổng quát

| Hạng mục | Trạng thái đã kiểm tra | Diễn giải |
| --- | --- | --- |
| Thiết kế phạm vi/kiến trúc | **DECIDED / DOCS_ONLY** | Baseline **v4.7**: Google Drive, PostgreSQL, Django+Ninja, React+Mantine, một worker; CaptureEvent bất biến, auto-group và RelatedItem đã được đặc tả |
| Chuẩn bị bố trí repo và AI routing | **DOCS_PREPARED** | Có `REPOSITORY_LAYOUT.md`, `docs/README.md`, `CURRENT_STATE.md` và liên kết từ README/AGENTS/roadmap trong commit chuẩn bị repository này |
| Ứng dụng React/Django | **PASS (tiếp nhận và thư viện)** | Có đăng nhập, gửi URL/chữ, biên nhận, lịch sử, xem/chỉnh sửa và khôi phục Item. API upload nhận file vào staging bền vững |
| PostgreSQL/Docker Compose | **PASS (Ubuntu CI)** | PostgreSQL 18, volume riêng, migration Django và rollback/reapply migration `sessions` đã chạy |
| Kết nối Google Drive | **MOCK_VERIFIED (KT-003–005)** | OAuth `drive.file`, mã hóa refresh token, upload resumable và retry cùng Drive ID qua test. Cần tài khoản/OAuth thực để kiểm chứng upload và đọc lại |
| Download video, trích chữ, thumbnail, FTS | **NOT_STARTED** | KT-010/102/104 mới là yêu cầu; chưa có kết quả benchmark/index/runtime thực tế |
| **Nhận URL/text và giữ giờ** | **PASS (bản tích hợp)** | Session/CSRF, ACK sau transaction, retry/gửi lại, lịch sử và giao diện qua proxy đã được kiểm thử |
| ChatGPT Drive pilot / xuất tri thức / MCP | **NOT_STARTED** | Chưa có thử nghiệm trực tiếp với tài khoản/workspace |
| Backup/restore dữ liệu | **NOT_STARTED** | Chưa có PostgreSQL dump, manifest thực tế hoặc thử restore |
| Triển khai Windows/Linux/Android | **NOT_STARTED** | Chưa xác minh máy chạy, URL, HTTPS hay PWA Share Target |
| Test/CI runtime | **PASS (KT-001, KT-002, KT-003–005 mô phỏng)** | [GitHub Actions #44320811635](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44320811635) và smoke trên Windows với PostgreSQL tạm |

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
| KT-008–KT-010 — Vận hành, đối chiếu và thumbnail | **IN_PROGRESS** | CaptureEvent/receipt và giờ server, note chữ nguyên văn, retry/gửi lại, Drive/Job/backup/restore phải chạy/test thật |
| KT-101–KT-110 — Gate B | **NOT_STARTED** | Metadata/video/parser, auto-group thực, RelatedItem, FTS/Android và bài đánh giá phải chạy thật |
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
- Worker PostgreSQL đã thử lease, SKIP LOCKED và restart. Tệp chỉ được xác nhận sau khi Drive adapter kiểm chứng. CI chạy dữ liệu thử; sau khi có dữ liệu thật cần sao lưu trước khi rollback migration. Màn hình upload tệp, sao lưu và thumbnail đang tích hợp tiếp.

**Việc tiếp theo:** kết hợp KT-008/009/010 cho Gate A và nối KT-101/103/104/110 cho Gate B. Kiểm Drive thật khi có cấu hình OAuth và môi trường phù hợp.

**Chưa xác minh:** cấu hình Docker trên Windows; máy chủ 24/7; dự trữ/quota thật của Drive; OAuth; định dạng file ChatGPT app có thể đọc; quyền/media của từng nền tảng; thư viện PDF nào trích tiếng Việt tốt nhất. Không hỏi lại các quyết định đã chốt; chỉ nêu blocker khi bắt đầu tác vụ phụ thuộc thông tin đó.

## 5. Quy tắc cập nhật trạng thái

- Mỗi lần hoàn tất task ghi **ID, SHA commit, branch/PR, test thực sự đã chạy + kết quả, điều chưa test, blocker và một bước kế tiếp**. Không tự thăng trạng thái thành PASS khi chưa có bằng chứng.
- Kiểm tra lại GitHub `main` và diff hiện hành trước mỗi lần ghi. Nếu nhiều AI làm song song, phân file/branch không chồng chéo. Không cần dựng workboard/dispatcher nếu chưa thực sự có nhiều đầu việc đồng thời.
- Không tự bổ sung lịch sử nhiều trang. Dữ liệu đo chi tiết có thể lưu dưới `evals/` khi bắt đầu đo; `CURRENT_STATE.md` giữ bản tóm tắt và liên kết bằng chứng.
- **SHA chính xác của commit hiện hành phải lấy từ GitHub ở thời điểm đọc**, không chép một SHA đã cũ thành trạng thái vĩnh viễn trong tài liệu này.
