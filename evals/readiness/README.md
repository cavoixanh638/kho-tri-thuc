# KT-114 — cổng QA tổng hợp 10.000 Item

Harness dùng code ứng dụng hiện hành, không sửa core và không gọi Drive hay tải
nguồn mạng. Cluster duy nhất được chấp nhận là PostgreSQL QA `127.0.0.1:62224`,
role `kt_dev`, khác cluster Windows đang phục vụ người dùng. Mỗi lần chạy tạo
hai DB mới có prefix `kt_readiness_`; không tái sử dụng/xóa DB có sẵn.

## Dữ liệu và phép đo

- Seed cố định `kt114-v1`: 10.000 Item với UUID5, note Việt NFC/NFD/CRLF,
  10.000 CaptureEvent, hai kho con và cây bốn tầng. Mỗi bài có một nhánh lá,
  bài thứ `i % 10 == 0` có thêm nhánh `(i+17) % 64`: 11.000 assignment.
- 5.000 Source, 5.000 DerivedContent hiện hành + 500 bản stale có version/locator;
  100 RelatedItem có lý do/version; 100 Asset và mapping **tổng hợp/PENDING**.
  Mapping `SYNTHETIC_NOT_A_DRIVE_FILE_*` không phải ID Drive và không được mở.
- Cây đếm từng tập ID theo công thức seed độc lập. Đi hết page (100 bài/page)
  ở toàn kho, favorite và hai kho con; so tập ID, số dòng trùng và chênh lệch.
  Mốc `saved_at`/ID cố định; không suy số một trang thành toàn bộ corpus.
- Chạy OrganizationService thực giữ pinned. Hai lần gửi URL mới qua
  CaptureService tạo +2 Event, cùng Item; replay cùng key tạo +0. Không gọi
  worker/network, nên đây là kiểm ACK/database, không là ingest nguồn thật.
- Backup bằng tool hiện hành, restore DB rỗng khác. Hash **toàn bộ cột** trong
  15 collection theo ID, gồm JSON locator/metadata mà manifest không chiếu.
  Đối chiếu cả version, note, CaptureEvent, Asset và mapping; OAuth/session rỗng.
- Đọc lại bytes mẫu tổng hợp trên máy và SHA riêng. Không ghi Drive readback
  PASS từ mapping fixture. Corpus sau kiểm gửi có 10.001 Item/10.002 Event.

## Lệnh chạy

Từ repository root, dùng Python đã cài requirements backend và PostgreSQL 18
`psql`, `pg_dump`, `pg_restore` trong PATH. Mật khẩu QA lấy từ môi trường riêng:

```powershell
$env:KT_READINESS_PASSWORD = '<isolated QA password>'
$env:PATH = 'C:\Program Files\PostgreSQL\18\bin;' + $env:PATH
python -m unittest discover -s tools/readiness -p test_safety.py
python tools/readiness/run.py --work-dir '<new private directory outside Git>' --report evals/readiness/results.json
```

Bundle dump và receipt nằm ngoài Git, chỉ report tổng hợp/hash được commit.
Không dùng credentials production. Harness từ chối port khác, tên DB thường,
thư mục bundle trong repository hoặc thư mục đã tồn tại. Dùng `--cleanup` với
receipt sau khi đóng mọi kết nối thử; tool kiểm marker của **cả hai** database,
không FORCE và không đụng bản bundle:

```powershell
python tools/readiness/run.py --cleanup '<private work directory>\receipt.json'
```

## Lỗi mạng/worker và giới hạn

Suite core có các probe đã triển khai: `storage.test_drive_storage` (timeout
sau remote commit, checksum), `storage.test_reconcile` (429/retry/403/404,
PENDING không nâng VERIFIED), `storage.test_drive_transport` (lease/timeout),
`processing.test_video_jobs` và `processing.test_source_jobs` (metadata-only,
download thất bại vẫn giữ URL, version/lease), `processing.test_read_knowledge`
(thiếu transcript không suy nội dung). Kết quả chạy thật ghi checkpoint task;
transport fake là **UNIT_PASS**, không LIVE_PASS Google.

100+GB, quota/tệp Drive lớn, đổi OAuth host/client/project, nguồn FB/TikTok/YT
trực tiếp, playback Windows/Android và precision ngữ nghĩa corpus cá nhân còn
NOT_RUN trong đợt QA này. Bằng chứng live nhỏ cũ chỉ tra CURRENT_STATE, không
được cộng dồn thành benchmark 10.000 media. Có lỗi mất ID/byte/locator thì gate
FAIL và phải xử lý trước phát hành; không sửa tiêu chí để làm PASS.
