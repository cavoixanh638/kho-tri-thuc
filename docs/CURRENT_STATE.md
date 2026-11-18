# HIỆN TRẠNG THỰC TẾ — KHO TRI THỨC

**Ngày checkpoint:** 18/11/2026 (Asia/Ho_Chi_Minh).
**Nguồn kiểm chứng:** cây file GitHub nhánh `main`, bộ tài liệu v4.7, khảo sát read-only [QLVB_System_new](https://github.com/cavoixanh638/QLVB_System_new); **chỉ tài liệu được kiểm chứng, chưa có test ứng dụng**.
**Mục đích:** nơi duy nhất ghi **đã hoàn thành điều gì thật**. Roadmap là kế hoạch/điều kiện PASS, không là chứng cứ chạy thật.

## 1. Tình trạng tổng quát

| Hạng mục | Trạng thái đã kiểm tra | Diễn giải |
| --- | --- | --- |
| Thiết kế phạm vi/kiến trúc | **DECIDED / DOCS_ONLY** | Baseline **v4.7**: Google Drive, PostgreSQL, Django+Ninja, React+Mantine, một worker; CaptureEvent bất biến, auto-group và RelatedItem đã được đặc tả |
| Chuẩn bị bố trí repo và AI routing | **DOCS_PREPARED** | Có `REPOSITORY_LAYOUT.md`, `docs/README.md`, `CURRENT_STATE.md` và liên kết từ README/AGENTS/roadmap trong commit chuẩn bị repository này |
| Ứng dụng React/Django | **NOT_STARTED** | Chưa có `apps/`, API hoặc UI chạy thật |
| PostgreSQL/Docker Compose | **NOT_STARTED** | Chưa tạo database/schema/volume hay test migration |
| Kết nối Google Drive | **NOT_STARTED** | Chưa có OAuth Client/refresh token được cấu hình cho ứng dụng, chưa upload hay verify |
| Download video, trích chữ, thumbnail, FTS | **NOT_STARTED** | KT-010/102/104 mới là yêu cầu; chưa có kết quả benchmark/index/runtime thực tế |
| **Nhận URL/text, giữ giờ, tự nhóm và Item liên quan** | **DOCS_ONLY / NOT_STARTED** | Hợp đồng tại [CAPTURE_AND_ORGANIZE.md](CAPTURE_AND_ORGANIZE.md); KT-011/KT-110, N01–N17 và U19–U23 mới là **tiêu chí nghiệm thu**, không phải API/worker đã chạy |
| ChatGPT Drive pilot / xuất tri thức / MCP | **NOT_STARTED** | Chưa có thử nghiệm trực tiếp với tài khoản/workspace |
| Backup/restore dữ liệu | **NOT_STARTED** | Chưa có PostgreSQL dump, manifest thực tế hoặc thử restore |
| Triển khai Windows/Linux/Android | **NOT_STARTED** | Chưa xác minh máy chạy, URL, HTTPS hay PWA Share Target |
| Test/CI runtime | **NOT_RUN** | **0 runtime test được ghi nhận cho Kho Tri Thức**, không suy từ việc tài liệu GitHub đã được commit |

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
| KT-001 — Scaffold | **NOT_STARTED** | Django/React khởi động trên môi trường thử, PostgreSQL riêng, migration + test, hướng dẫn LOCAL_SETUP dựa trên lệnh thật |
| KT-002–KT-011 — Gate A | **NOT_STARTED** | CaptureEvent/receipt và giờ server, note chữ nguyên văn, retry/gửi lại, Drive/Job/backup/restore phải chạy/test thật |
| KT-101–KT-110 — Gate B | **NOT_STARTED** | Metadata/video/parser, auto-group thực, RelatedItem, FTS/Android và bài đánh giá phải chạy thật |
| KT-201–KT-204 — Gate C | **NOT_STARTED** | Pilot ChatGPT được kiểm chứng theo workspace thực tế |
| Gate D — nâng cấp | **NOT_STARTED / CONDITIONAL** | Chỉ khởi động khi có trigger từ thực tế và người dùng giao |

## 4. Việc cần làm tiếp và các thông tin còn thiếu

**Việc tiếp theo rõ ràng:** `KT-001` — scaffold Django 5.2 LTS + Ninja, React/Vite/Mantine, PostgreSQL Docker và một worker cùng codebase; thiết kế nền cho `KT-002/KT-011` (CaptureEvent, receipt URL/text), `.env.example` không secret, API/UI mẫu, migration/build test. **Chỉ sau khi thực sự chạy mới tạo `docs/operations/LOCAL_SETUP.md` với lệnh đã xác minh**.

**Chưa xác minh:** cấu hình Docker trên Windows; máy chủ 24/7; dự trữ/quota thật của Drive; OAuth; định dạng file ChatGPT app có thể đọc; quyền/media của từng nền tảng; thư viện PDF nào trích tiếng Việt tốt nhất. Không hỏi lại các quyết định đã chốt; chỉ nêu blocker khi bắt đầu tác vụ phụ thuộc thông tin đó.

## 5. Quy tắc cập nhật trạng thái

- Mỗi lần hoàn tất task ghi **ID, SHA commit, branch/PR, test thực sự đã chạy + kết quả, điều chưa test, blocker và một bước kế tiếp**. Không tự thăng trạng thái thành PASS khi chưa có bằng chứng.
- Kiểm tra lại GitHub `main` và diff hiện hành trước mỗi lần ghi. Nếu nhiều AI làm song song, phân file/branch không chồng chéo. Không cần dựng workboard/dispatcher nếu chưa thực sự có nhiều đầu việc đồng thời.
- Không tự bổ sung lịch sử nhiều trang. Dữ liệu đo chi tiết có thể lưu dưới `evals/` khi bắt đầu đo; `CURRENT_STATE.md` giữ bản tóm tắt và liên kết bằng chứng.
- **SHA chính xác của commit hiện hành phải lấy từ GitHub ở thời điểm đọc**, không chép một SHA đã cũ thành trạng thái vĩnh viễn trong tài liệu này.
