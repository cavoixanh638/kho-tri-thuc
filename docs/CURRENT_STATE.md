# HIỆN TRẠNG THỰC TẾ — KHO TRI THỨC

**Ngày checkpoint:** 15/11/2026 (Asia/Ho_Chi_Minh).
**Nguồn kiểm chứng:** cây file GitHub nhánh `main`, bộ tài liệu v4.6 và đợt khảo sát read-only repo [QLVB_System_new](https://github.com/cavoixanh638/QLVB_System_new).
**Mục đích:** nơi duy nhất ghi **đã hoàn thành điều gì thật**. Roadmap là kế hoạch/điều kiện PASS, không là chứng cứ chạy thật.

## 1. Tình trạng tổng quát

| Hạng mục | Trạng thái đã kiểm tra | Diễn giải |
| --- | --- | --- |
| Thiết kế phạm vi/kiến trúc | **DECIDED / DOCS_ONLY** | Baseline v4.6: Drive là kho file chính, PostgreSQL, Django+Ninja, React+Mantine, một worker |
| Chuẩn bị bố trí repo và AI routing | **DOCS_PREPARED** | Có `REPOSITORY_LAYOUT.md`, `docs/README.md`, `CURRENT_STATE.md` và liên kết từ README/AGENTS/roadmap trong commit chuẩn bị repository này |
| Ứng dụng React/Django | **NOT_STARTED** | Chưa có `apps/`, API hoặc UI chạy thật |
| PostgreSQL/Docker Compose | **NOT_STARTED** | Chưa tạo database/schema/volume hay test migration |
| Kết nối Google Drive | **NOT_STARTED** | Chưa có OAuth Client/refresh token được cấu hình cho ứng dụng, chưa upload hay verify |
| Download video, trích chữ, thumbnail, FTS | **NOT_STARTED** | KT-010/102/104 mới là yêu cầu; chưa có kết quả benchmark hay index thực tế |
| ChatGPT Drive pilot / xuất tri thức / MCP | **NOT_STARTED** | Chưa có thử nghiệm trực tiếp với tài khoản/workspace |
| Backup/restore dữ liệu | **NOT_STARTED** | Chưa có PostgreSQL dump, manifest thực tế hoặc thử restore |
| Triển khai Windows/Linux/Android | **NOT_STARTED** | Chưa xác minh máy chạy, URL, HTTPS hay PWA Share Target |
| Test/CI runtime | **NOT_RUN** | **0 runtime test được ghi nhận cho Kho Tri Thức**, không suy từ việc tài liệu GitHub đã được commit |

**Không được gọi các dòng NOT_STARTED/NOT_RUN là PASS.** Tạo kế hoạch không có nghĩa đã có môi trường hoặc dữ liệu dùng thật.

## 2. Kết quả khảo sát QLVB được kế thừa ở cấp thiết kế

- Đã đọc cấu trúc `QLVB_System_new/main`: `apps/`, `packages/`, `db/migrations/`, `docs/`, `evals/`, `tests/`, `tools/` và các thư mục legacy/coordination.
- Tiếp thu **bốn lớp thông tin** (source record, source artifact, derived artifact, operational state), ID độc lập với tên hiển thị, provenance, tách tests/evals và quy tắc một nguồn tài liệu chuẩn.
- Kế thừa **nguyên tắc** an toàn Git/data, không sao chép mã nguồn hoặc schema cụ thể từ QLVB. Không sao chép Node ingestion, pgvector, legacy shims, orchestrator hay workboard nhiều tác nhân.
- Những quyết định này được quy định trong [REPOSITORY_LAYOUT.md](REPOSITORY_LAYOUT.md), **không làm thay đổi lựa chọn công nghệ v4.6**.

## 3. Checkpoint công việc

| Mã / mốc | Trạng thái | Bằng chứng cần có tiếp theo |
| --- | --- | --- |
| Chuẩn bị repository trước KT-001 | **DOCS_PREPARED** | Commit GitHub chứa tài liệu định tuyến/cấu trúc/hiện trạng và readback kiểm tra nội dung; không phải test ứng dụng |
| KT-001 — Scaffold | **NOT_STARTED** | Django/React khởi động trên môi trường thử, PostgreSQL riêng, migration + test, hướng dẫn LOCAL_SETUP dựa trên lệnh thật |
| KT-002–KT-010 — Gate A | **NOT_STARTED** | API/File/Drive/Job/thumbnail/backup/restore có test thật theo roadmap |
| KT-101–KT-109 — Gate B | **NOT_STARTED** | Link video, parser, taxonomy/search/UI Android có test/eval theo roadmap |
| KT-201–KT-204 — Gate C | **NOT_STARTED** | Pilot ChatGPT được kiểm chứng theo workspace thực tế |
| Gate D — nâng cấp | **NOT_STARTED / CONDITIONAL** | Chỉ khởi động khi có trigger từ thực tế và người dùng giao |

## 4. Việc cần làm tiếp và các thông tin còn thiếu

**Việc tiếp theo rõ ràng:** `KT-001` — tạo Django 5.2 LTS + Ninja, React/Vite/Mantine, PostgreSQL bằng Docker Compose và một worker từ cùng codebase; tạo `.env.example` không chứa secret; mở được màn hình và API mẫu; test migration/local build. Sau khi **thực sự chạy được**, bổ sung `docs/operations/LOCAL_SETUP.md` với lệnh/môi trường đã kiểm chứng.

**Chưa xác minh:** cấu hình Docker trên Windows; máy chủ 24/7; dự trữ/quota thật của Drive; OAuth; định dạng file ChatGPT app có thể đọc; quyền/media của từng nền tảng; thư viện PDF nào trích tiếng Việt tốt nhất. Không hỏi lại các quyết định đã chốt; chỉ nêu blocker khi bắt đầu tác vụ phụ thuộc thông tin đó.

## 5. Quy tắc cập nhật trạng thái

- Mỗi lần hoàn tất task ghi **ID, SHA commit, branch/PR, test thực sự đã chạy + kết quả, điều chưa test, blocker và một bước kế tiếp**. Không tự thăng trạng thái thành PASS khi chưa có bằng chứng.
- Kiểm tra lại GitHub `main` và diff hiện hành trước mỗi lần ghi. Nếu nhiều AI làm song song, phân file/branch không chồng chéo. Không cần dựng workboard/dispatcher nếu chưa thực sự có nhiều đầu việc đồng thời.
- Không tự bổ sung lịch sử nhiều trang. Dữ liệu đo chi tiết có thể lưu dưới `evals/` khi bắt đầu đo; `CURRENT_STATE.md` giữ bản tóm tắt và liên kết bằng chứng.
- **SHA chính xác của commit hiện hành phải lấy từ GitHub ở thời điểm đọc**, không chép một SHA đã cũ thành trạng thái vĩnh viễn trong tài liệu này.
