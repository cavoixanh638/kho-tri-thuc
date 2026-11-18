# QUY CHUẨN CẤU TRÚC REPOSITORY — KHO TRI THỨC

**Trạng thái:** Đã thống nhất làm quy tắc bố trí tệp cho giai đoạn triển khai; hiện các thư mục ứng dụng trong sơ đồ bên dưới **chưa được tạo**.
**Phạm vi:** V4.7; một Django monolith, React PWA, PostgreSQL, Google Drive là kho file chính.
**Nguồn tham khảo đã đọc:** [QLVB Repository Layout](https://github.com/cavoixanh638/QLVB_System_new/blob/main/docs/REPOSITORY_LAYOUT.md), [QLVB System](https://github.com/cavoixanh638/QLVB_System_new/blob/main/docs/SYSTEM.md), [QLVB docs routing](https://github.com/cavoixanh638/QLVB_System_new/blob/main/docs/README.md). Áp dụng nguyên tắc có chọn lọc, **không di chuyển/copy mã QLVB**.

## 1. Một sự thật, một nơi có thẩm quyền

| Câu hỏi cần trả lời | Nguồn chuẩn |
| --- | --- |
| Dự án để làm gì, giới hạn của bản đầu? | [MASTER_PLAN.md](MASTER_PLAN.md) |
| Quyết định kỹ thuật, dữ liệu, API, cách nâng cấp? | [ARCHITECTURE_AND_DATA.md](ARCHITECTURE_AND_DATA.md) |
| **Gửi thông tin, giờ bất biến, tự nhóm và mục liên quan** | [CAPTURE_AND_ORGANIZE.md](CAPTURE_AND_ORGANIZE.md) |
| Công việc, phụ thuộc và tiêu chí nghiệm thu? | [ROADMAP_AND_TESTS.md](ROADMAP_AND_TESTS.md) |
| **Đã làm gì thật, đang vướng gì, test đã/chưa chạy?** | [CURRENT_STATE.md](CURRENT_STATE.md) |
| Thêm một file mới vào đâu? | **REPOSITORY_LAYOUT.md (tài liệu này)** |
| AI/Codex phải tuân thủ gì? | [AGENTS.md](../AGENTS.md) |
| Tìm đúng tài liệu nhanh? | [docs/README.md](README.md) và [README dự án](../README.md) |

Không viết lại sự thật từ nguồn khác thành nhiều phiên bản cạnh tranh. Tài liệu dẫn liên kết tới nguồn chuẩn. Phân biệt rõ **thiết kế đã chọn**, **mã đã tích hợp**, **test đã PASS**, **đã deploy**, **đã kiểm chứng sử dụng thực tế**.

## 2. Sơ đồ mục tiêu — chỉ tạo thư mục khi có file thật

~~~text
kho-tri-thuc/
├── README.md
├── AGENTS.md
├── .gitignore
├── .env.example                 # chỉ tạo cùng bộ cấu hình chạy thử KT-001
├── apps/
│   ├── web/                     # React, TypeScript, Vite, Mantine, PWA
│   └── backend/                 # một Django project + các Django app
│       ├── config/              # settings, urls, ASGI/WSGI
│       ├── catalog/             # Item, Project, Topic, Tag, RelatedItem
│       ├── storage/             # StoragePort, DriveStorage, StorageLocation
│       ├── ingestion/           # CaptureEvent, URL/ghi chú, metadata, upload
│       ├── processing/          # trích chữ, thumbnail, dữ liệu phát sinh
│       ├── search/              # SearchService, PostgreSQL FTS
│       └── jobs/                # job DB, retry, Django worker command
├── docs/
│   ├── README.md
│   ├── MASTER_PLAN.md
│   ├── ARCHITECTURE_AND_DATA.md
│   ├── ROADMAP_AND_TESTS.md
│   ├── REPOSITORY_LAYOUT.md
│   ├── CURRENT_STATE.md
│   └── operations/              # tạo LOCAL_SETUP khi chạy thật; BACKUP_RESTORE khi test thật
├── tests/                       # integration/regression/fixtures khi có test
├── evals/                       # bộ mẫu/đo chất lượng search/PDF/AI khi có
├── tools/                       # tiện ích backup, kiểm tra, phục hồi khi có
└── .github/workflows/           # CI tối thiểu khi có mã nguồn
~~~

Đây là **định hướng bố trí**, không phải khẳng định các đường dẫn đã tồn tại. Không tạo thư mục rỗng chỉ để đúng hình. Không tạo root `packages/`, `db/`, `coordination/`, `scratch/`, `misc/`, `services/` hoặc microservice mới khi chưa có nhu cầu và quyết định cụ thể.

## 3. Quy tắc đặt file theo trách nhiệm

| Loại | Đặt ở đâu | Lưu ý |
| --- | --- | --- |
| UI, trang, component, API client TypeScript | `apps/web/` | Không nhét logic nghiệp vụ vào component |
| Django models/API, xử lý một nghiệp vụ | Django app tương ứng trong `apps/backend/` | Tách module theo nghiệp vụ, không tách tiến trình mạng mặc định |
| Worker | Django management command + code `apps/backend/jobs/` | Chạy tiến trình worker riêng **từ cùng một Django codebase/image**; chưa cần `apps/worker/` |
| Migrations PostgreSQL | `apps/backend/<django_app>/migrations/` | Django migrations làm nguồn chuẩn; **không** tạo bản SQL schema cạnh tranh ở root `db/migrations/` |
| Công cụ chỉ phục vụ một Django app | Đặt cùng app đó | Không tạo `utils/` chung theo phản xạ |
| Kiểm thử unit | Gần code theo quy ước Django/TypeScript | `tests/` ở root cho regression/integration end-to-end liên ứng dụng |
| Đo chất lượng | `evals/` | Parser PDF tiếng Việt, chất lượng tìm kiếm, phân nhóm AI; khác test đúng/sai |
| Công cụ vận hành | `tools/` | Chỉ tạo khi có script hữu ích, lệnh đọc/ghi phải rõ |
| Tài liệu kỹ thuật lâu dài | `docs/` | Việc nào đã hoàn thành phải ghi ở CURRENT_STATE, không thêm lịch sử dài trong MASTER_PLAN |
| Hướng dẫn chạy/backup/restore | `docs/operations/` | Chỉ ghi lệnh đã thực thi/kiểm tra, tách các bước dự kiến chưa thử |

Chức năng dùng chung như StoragePort/SearchService nằm trong Django app của nó cho tới khi **ít nhất hai thành phần thực sự cần tái sử dụng** mới xét rút ra package thuần. `apps/` không đồng nghĩa microservice.

## 4. Dữ liệu: ranh giới quan trọng hơn tên thư mục

### 4.1. GitHub — chỉ code, cấu hình mẫu và tài liệu

Được đưa vào Git: source, migration, README, fixtures nhỏ có quyền sử dụng/đã khử thông tin riêng, unit tests, cấu hình mẫu không credential, CI. **Không đưa vào Git:** media gốc, download, database PostgreSQL, dump, refresh token OAuth, log nội dung người dùng, video/PDF thật, transcript dài, cache, file runtime, bản xuất ChatGPT, model weights hoặc backup. `.gitignore` chỉ là lớp phụ; cần kiểm tra phạm vi thay đổi trước commit.

### 4.2. Google Drive — file gốc, không phải cấu trúc phân loại nghiệp vụ

Đề xuất folder ban đầu (tạo khi kết nối Drive thành công, **không phải folder đã tồn tại**):

~~~text
Kho Tri Thuc/
├── Originals/
│   ├── Documents/
│   ├── Images/
│   └── Videos/
├── ChatGPT_Index/       # chỉ khi KT-202E được thử và chấp nhận
└── System_Backups/      # chỉ khi KT-008 có backup thành công
~~~

- Một file chỉ lưu **một bản gốc**; một Item có thể thuộc nhiều Project/Topic/Tag qua PostgreSQL. Không sao chép sang nhiều folder Drive theo lĩnh vực/dự án.
- Giữ tên file gốc hiển thị khi an toàn; khóa nghiệp vụ là UUID `item_id`/`asset_id`, vị trí là `StorageLocation.drive_file_id`; không dùng đường dẫn/tên file/URL làm ID.
- Ghi source URL, thời điểm, loại nội dung, checksum khi có và provenance. Mọi dữ liệu AI/trích xuất tạo mới theo version, không ghi đè note đã được người dùng sửa.
- Tài liệu trong `ChatGPT_Index/` chỉ là bản xuất **phát sinh** được tạo lại từ PostgreSQL, không trở thành nguồn chân lý; bản xuất stale phải được nhận diện.

### 4.3. Máy chạy ứng dụng — database và cache

- PostgreSQL sử dụng volume riêng; không vận hành database đang mở trong folder đồng bộ Drive.
- Cache thumbnail WebP/JPEG có thể regenerate, video cache tạm và file staging sử dụng volume/quota/TTL phù hợp; file gốc **chỉ xác nhận đã lưu** sau khi upload Drive và verify thành công.
- PostgreSQL dump phải được tạo nhất quán và kiểm thử restore; Drive backup không thay thế bản sao **ngoài tài khoản Drive** nếu dữ liệu quan trọng.
- Tên Docker volume/đường dẫn host do KT-001 và KT-008 chốt sau khi chạy thật; không cứng hóa đường dẫn Windows chưa kiểm chứng.

## 5. Các lớp thông tin và vòng đời Item

Nhận từ [SYSTEM.md QLVB](https://github.com/cavoixanh638/QLVB_System_new/blob/main/docs/SYSTEM.md) **nguyên tắc phân bốn lớp**, không copy schema QLVB:

1. **Source record** — CaptureEvent (mỗi lượt gửi và giờ server bất biến), Item, Source, metadata và chỉnh sửa của người dùng.
2. **Source artifact** — Asset/file gốc được liên kết qua StorageLocation trên Drive.
3. **Derived artifact** — DerivedContent, transcript, thumbnail, AI suggestion, RelatedItem có provenance/version, chỉ mục; không ghi đè curated.
4. **Operational state** — Job, stage, attempt, error, lease và mốc upload/verify/preview.

Không suy diễn `CaptureEvent đã nhận` = `video đã download` = `Drive đã verify` = `video sẵn sàng preview` = `nội dung đã được trích` = `tự phân nhóm đúng`. Giao diện/API phải diễn đạt đúng từng trạng thái; xem [CAPTURE_AND_ORGANIZE.md](CAPTURE_AND_ORGANIZE.md).

## 6. Kiểm thử, đánh giá và chứng cứ

- **tests:** khẳng định đúng/sai: Event bất biến, URL gửi lại vs retry, note chữ nguyên văn, tự gán nhóm, RelatedItem unique, job idempotent, không mất UUID/file gốc, restore mapping, API và EXIF thumbnail.
- **evals:** đo chất lượng: benchmark PDF KT-102, FTS/candidate recall tiếng Việt KT-104, precision/coverage và false auto-assignment/RelatedItem precision KT-107.
- Không commit tài liệu cá nhân làm benchmark. Ưu tiên fixture tổng hợp hoặc được phép dùng; nếu cần PDF thật để đo, lưu ở Drive/không gian QA riêng, trong Git chỉ có mô tả, ID an toàn, hash, tiêu chí và kết quả.
- PASS phải ghi **SHA đã thử**, môi trường, lệnh/test, kết quả, phần chưa chạy và giới hạn kết luận tại [CURRENT_STATE.md](CURRENT_STATE.md) hoặc PR. Không lấy kết quả từ QLVB làm bằng chứng cho Kho Tri Thức.

## 7. Tên file, di chuyển và tránh trùng lặp

- Tên path source: chữ thường, tiếng Anh ngắn theo trách nhiệm, `snake_case` khi cần; tên tài liệu chuẩn đang có (`MASTER_PLAN.md`, v.v.) được giữ nguyên.
- Không tạo các tên `final2`, `new`, `old`, `copy`, `misc`, `temp2`; không xóa/đổi tên trùng chỉ vì có hậu tố `(1)` trước khi xác định nội dung và bên đang tham chiếu.
- Khi cần chuyển vị trí: đối chiếu references/imports, thay đổi nhỏ, thêm test, verify trên nhánh và cập nhật đường dẫn tài liệu; **không** kết hợp refactor toàn repo với nâng cấp database/worker.
- Không tạo sơ đồ `REPO_MAP.md` hoặc `FEATURE_MAP.md` trước khi thật sự có code nhiều module; khi cần, chỉ làm **chỉ mục đường dẫn**, không lặp lại kiến trúc.

## 8. Khi nào cập nhật tài liệu nào?

- Ý tưởng/tuyên bố chưa kiểm chứng: đưa vào task/điểm cần đo; không nâng thành 'đã chạy'.
- Thay đổi phạm vi: `MASTER_PLAN.md`; **hành vi nhận và tự tổ chức: `CAPTURE_AND_ORGANIZE.md`**; thay đổi schema/kiến trúc: `ARCHITECTURE_AND_DATA.md`.
- Quy tắc đặt file: chính tài liệu này; thay đổi tiêu chí nghiệm thu: `ROADMAP_AND_TESTS.md`.
- **Tiến độ thực tế, commit, PASS/FAIL/NOT_RUN, blocker và next action: chỉ cập nhật `CURRENT_STATE.md`.**
- Khi KT-001 chạy được thật: viết `docs/operations/LOCAL_SETUP.md` với lệnh đã kiểm tra.
- Khi KT-008 backup/restore chạy thật: viết `docs/operations/BACKUP_RESTORE.md`, không tự tuyên bố đã có backup từ kế hoạch.

**Ranh giới áp dụng từ QLVB:** học tính rõ ràng, truy nguyên và phân vai; **không** bê cơ chế 6 worker, Node ingestion, pgvector/BGE, orchestrator, workboard khổng lồ hay đường dẫn legacy của QLVB sang Kho Tri Thức.
