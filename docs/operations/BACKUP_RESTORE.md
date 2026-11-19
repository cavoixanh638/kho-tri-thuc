# Sao lưu và khôi phục PostgreSQL

Đã chạy các bước dưới đây với PostgreSQL 18.4, Python 3.13 và PowerShell trên Windows, trên cơ sở dữ liệu thử riêng với dữ liệu tổng hợp.

## Tạo gói và xác minh bản sao

Dùng Python 3.11 trở lên. Khi chạy native, đặt `psql`, `pg_dump` và `pg_restore` PostgreSQL 18 trên PATH. Đặt `PGHOST`, `PGPORT`, `PGUSER` và `PGDATABASE` cho kết nối nguồn. Dùng cơ chế xác thực libpq của môi trường. Chọn `$ktBundle` là một đường dẫn mới có thư mục cha đã tồn tại, và `$ktCopy` là một đường dẫn mới trên nơi lưu ngoài Drive.

```powershell
python tools/backup/backup.py create $ktBundle
Copy-Item -LiteralPath $ktBundle -Destination $ktCopy -Recurse
python tools/backup/backup.py verify $ktCopy
```

`create` lấy dump và JSON từ cùng một snapshot PostgreSQL. Thư mục gói được công bố sau khi đủ ba tệp `database.dump`, `manifest.json` và `SHA256SUMS`. `verify` đọc bản sao cục bộ, kiểm tra SHA-256 của cả hai tệp và định dạng manifest. Gói chứa nội dung người dùng và dump chứa dữ liệu xác thực Django đã băm. Giới hạn quyền đọc thư mục gói và lưu toàn bộ gói khi sao chép.

Manifest `schema_version: 2` chứa Item, CaptureEvent, Source, Topic, Project, Tag, ba loại assignment, Asset, StorageLocation, DerivedContent, RelatedItem, Job và KnowledgeExport. Mapping/preference/version bản xuất được giữ. Bản v1 cũ có 14 collection vẫn xác minh và restore được, không đòi bảng KnowledgeExport đã tồn tại. Các ID, khóa ngoại, nguyên văn và thời điểm UTC có offset được giữ. Để tra file gốc, nối Item → Asset qua `item_id`, rồi Asset → StorageLocation qua `asset_id` và đọc `provider_file_id` của provider `google_drive`. Các payload JSON mở của Source, DerivedContent và Job chỉ có trong dump. Dữ liệu bảng OAuth Drive và phiên Django được loại khỏi gói.

## Khôi phục vào cơ sở dữ liệu mới

Dùng gói do mình tạo và tên đích mới trong `$ktTarget`. Đặt các biến kết nối libpq cho máy đích PostgreSQL 18 trước khi chạy từ thư mục gốc repo.

```powershell
createdb --no-password --maintenance-db=postgres --template=template0 --encoding=UTF8 $ktTarget
python tools/backup/backup.py restore $ktCopy --target-db $ktTarget
```

`restore` xác minh gói, kiểm tra DB đích trống, chạy `pg_restore` trong một transaction rồi đối chiếu tất cả nhóm dữ liệu với manifest. Role thực hiện restore sở hữu các đối tượng phục hồi. Gói dump là nguồn khôi phục schema, migrations và dữ liệu. JSON dùng để đọc danh mục, tra mapping và đối chiếu.

Lệnh trả mã 1 nếu đối chiếu thất bại. Đối chiếu diễn ra sau transaction của `pg_restore`, vì vậy hãy kiểm tra lỗi và dùng một DB mới khi thử lại. Sau khi xác minh DB đích, cấu hình ứng dụng trỏ sang DB đó và đăng nhập lại. Kết nối lại Google Drive với tài khoản và OAuth client có quyền đọc các ID cũ. Gói lưu mapping của file gốc, còn nội dung file nằm ở Drive.

## Bằng chứng và giới hạn

Kết quả thực thi lần lượt là `Backup created and checksums verified.`, `Backup checksums and manifest format verified.` và `Database restored and manifest collections matched.`. Ba bài kiểm thử dưới đây cũng đã chạy với cluster thử PostgreSQL 18.4 và yêu cầu cài dependencies backend. Bộ test tự tạo và dọn các database tên ngẫu nhiên.

```powershell
$env:KT_BACKUP_TEST='1'
python -m unittest discover -s tools/backup -v
```

Test dùng adapter Drive với client giả để kiểm tra mở đường dẫn của ID được khôi phục. Flag `--compose` đặt trước động từ CLI và dùng bộ công cụ trong service `db` của repo. Đường Compose create/verify/restore đã PASS trong CI [#44339513395](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44339513395). Upload/tải lại backup Drive và mở/tải lại tệp gốc thật đã **PASS** ngày 19/11/2026, xem [báo cáo live](backup-live-results.json).

Khi chuyển host cùng lúc có upload đang chờ, giữ cả volume staging hoặc hoàn tất các lượt upload trước khi chuyển. Gói dump lưu bản ghi công việc; byte chưa xác minh vẫn thuộc staging của host nguồn.

## Kiểm chứng Drive thật và chuyển host cùng OAuth client

Đã bổ sung `tools/backup/drive_bundle.py` và runner `tools/backup/live_recovery.py`. Bản chuẩn bị đã qua kiểm thử với PostgreSQL 18.4 thử riêng và Drive mô phỏng. [Báo cáo chuẩn bị](backup-recovery-readiness.json) tách kết quả đó với thao tác dịch vụ thật còn chờ xác nhận.

Runner thực hiện tuần tự các bước sau sau khi chủ dữ liệu xác nhận xuất bản sao lên Drive.

1. Lấy snapshot chỉ đọc của database Windows đang chạy, tạo dump/manifest nhất quán và một bản sao cục bộ ngoài Drive sync.
2. Đóng gói ba tệp thành ZIP, giữ receipt chứa ID Drive trong thư mục riêng trên máy. Tạo một tệp bất biến dưới `Kho Tri Thuc/System_Backups` bằng upload resumable, giữ ID khi retry và kiểm checksum.
3. Tải ZIP từ Drive, kiểm SHA-256 và định dạng archive, phục hồi gói đã tải vào một database PostgreSQL mới có tiền tố `kt_recovery_`. Runner không dừng ứng dụng hoặc phục hồi đè lên database nguồn.
4. Đối chiếu đủ collection theo manifest (v1: 14, v2: 15), xác nhận bảng OAuth/session rỗng. Dùng credential runtime đang có chỉ để kiểm tra mapping đã khôi phục, gọi adapter mở file và đối chiếu SHA-256 toàn bộ file gốc tải lại. Thay đổi thời điểm verify trong database thử được rollback.
5. Ghi báo cáo đã khử thông tin riêng chỉ gồm số lượng, số byte, hash và kết quả. Dump, manifest, archive, ID Drive và receipt nằm ngoài Git. Gốc media trên Drive giữ nguyên.

Payload sao lưu có thể chứa ghi chú, URL, lịch sử tiếp nhận, metadata, nhóm và dữ liệu xác thực Django đã băm. OAuth token và Django session được loại. Lần chuẩn bị bị cơ chế tự duyệt quyền từ chối do thiếu xác nhận payload/nơi nhận. Sau khi người dùng xác nhận rõ ngày 19/11/2026, runner `760be80` đã chạy thật và PASS: ZIP 94.495 byte, retry cùng ID, readback SHA-256 đúng, restore đủ 14 collection vào database tạm mới, OAuth/session đều 0. Tệp MP4 gốc 18.394.669 byte cũng tải lại khớp SHA-256 từ mapping đã restore. Database production chỉ đọc.

Lượt live hiện có 1 Item/1 CaptureEvent/1 Asset/4 Job, chưa có nhóm hay note không rỗng. Bảo toàn dữ liệu nhóm/note không rỗng được kiểm bằng fixture riêng, không suy thành nghiệm thu live nội dung chưa tồn tại. Đây là cùng máy Windows và cùng OAuth client/project, chưa phải đổi client/project hoặc mất máy thật.

Lệnh dưới đây mô tả **đường chạy đã kiểm trên dữ liệu thật**. Chọn `$ktAuditRoot` là đường dẫn mới dưới `%LOCALAPPDATA%\KhoTriThuc\backups`, đặt biến `KT_BACKUP_AUDIT_PASSWORD` cho cluster thử riêng nếu cần. Các tham số mặc định của cluster thử là loopback cổng 62224 và role `kt_dev`.

```powershell
& "$env:LOCALAPPDATA\KhoTriThuc\venv\Scripts\python.exe" tools/backup/live_recovery.py `
    --runtime-config "$env:LOCALAPPDATA\KhoTriThuc\runtime\config.json" `
    --work-dir $ktAuditRoot --report $ktReport --target-db $ktTarget
```

Thư mục runtime ứng dụng đã có ACL riêng trên Windows. Đặt backup và receipt bên trong thư mục riêng đó. Bản sao cục bộ trên cùng máy giúp khôi phục khi Drive không khả dụng, nhưng chưa bảo vệ trước mất cả máy. Khi chuyển máy, OAuth refresh token không đi theo dump; phải kết nối lại cùng client/project và tài khoản được quyền đọc các ID gốc. Chưa kiểm đổi client/project hoặc phục hồi từ một máy vật lý khác.

Lượt này ban đầu tạo trong thư mục công cụ tạm ngoài Drive sync, sau đó đã sao chép
vào `%LOCALAPPDATA%\KhoTriThuc\backups\live-recovery-20261119` và kiểm SHA-256 cả
12 file. Dump/manifest/archive/receipt không đưa lên GitHub; báo cáo chỉ số lượng,
hash và trạng thái ở GitHub. Backup đã nằm trên Drive `System_Backups`.
