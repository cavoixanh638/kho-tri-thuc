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

Manifest `schema_version: 1` chứa Item, CaptureEvent, Source, Topic, Project, Tag, ba loại assignment, Asset, StorageLocation, DerivedContent, RelatedItem và Job. Các ID, khóa ngoại, nguyên văn và thời điểm UTC có offset được giữ. Để tra file gốc, nối Item → Asset qua `item_id`, rồi Asset → StorageLocation qua `asset_id` và đọc `provider_file_id` của provider `google_drive`. Các payload JSON mở của Source, DerivedContent và Job chỉ có trong dump. Dữ liệu bảng OAuth Drive và phiên Django được loại khỏi gói.

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

Test dùng adapter Drive với client giả để kiểm tra mở đường dẫn của ID được khôi phục. Flag `--compose` đặt trước động từ CLI và dùng bộ công cụ trong service `db` của repo. Đường Compose, upload bản sao và mở file qua tài khoản Drive thật còn **NOT_RUN**.

Khi chuyển host cùng lúc có upload đang chờ, giữ cả volume staging hoặc hoàn tất các lượt upload trước khi chuyển. Gói dump lưu bản ghi công việc; byte chưa xác minh vẫn thuộc staging của host nguồn.
